"""
Voice consistency across a series.

The problem:
A creator uploads 50 videos over 6 months. Each video uses voice cloning.
But the reference audio changes slightly each time — different recording conditions,
different phrases used, the creator's voice changes slightly over months.

Result: the cloned voice shifts across the series. Video 1 sounds like one person.
Video 50 sounds like someone related but noticeably different.
Subscribers notice. They complain the dubbing quality is inconsistent.

The solution:
- Build a voice embedding from ALL reference audios a creator has uploaded
- Use the centroid of these embeddings as the "canonical voice" for this creator
- Weight newer recordings higher (accounts for natural voice change over time)
- Cache the canonical voice embedding — don't recompute every video

This is novel. HeyGen, Dubverse, nobody does this.
"""

import json
import os
from dataclasses import dataclass

import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class CanonicalVoice:
    creator_id: str
    embedding: np.ndarray
    reference_count: int
    last_updated: str
    dominant_language: str
    quality_score: float


def compute_voice_embedding(audio_path: str) -> np.ndarray:
    """
    Extract speaker embedding from audio.
    Uses resemblyzer (d-vector model) for consistent speaker representation.

    Falls back to MFCC-based feature extraction if resemblyzer unavailable.
    """
    try:
        from pathlib import Path

        from resemblyzer import VoiceEncoder, preprocess_wav

        encoder = VoiceEncoder()
        wav = preprocess_wav(Path(audio_path))
        embedding = encoder.embed_utterance(wav)
        return embedding

    except ImportError:
        log.warning("resemblyzer_not_installed_using_mfcc_fallback")
        return _mfcc_embedding(audio_path)
    except Exception as e:
        log.error("embedding_failed", error=str(e))
        return np.zeros(256)


def _mfcc_embedding(audio_path: str) -> np.ndarray:
    import librosa
    y, sr = librosa.load(audio_path, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)
    features = np.concatenate([
        np.mean(mfcc, axis=1),
        np.std(mfcc, axis=1),
        np.mean(delta, axis=1),
        np.mean(delta2, axis=1),
    ])
    norm = np.linalg.norm(features)
    return features / (norm + 1e-8)


def build_canonical_voice(
    creator_id: str,
    audio_paths: list[str],
    timestamps: list[float] | None = None,
    decay_factor: float = 0.95
) -> CanonicalVoice:
    """
    Build canonical voice from multiple reference recordings.

    decay_factor: how much older recordings count relative to newer ones.
    0.95 means each previous recording counts 5% less than the one after it.
    """
    if not audio_paths:
        raise ValueError("No audio paths provided")

    embeddings = []
    for path in audio_paths:
        emb = compute_voice_embedding(path)
        embeddings.append(emb)
        log.info("embedding_computed", path=os.path.basename(path))

    # Weight by recency: most recent = highest weight
    n = len(embeddings)
    if n == 1:
        weights = np.array([1.0])
    else:
        weights = np.array([decay_factor ** (n - 1 - i) for i in range(n)])
        weights /= weights.sum()

    # Weighted centroid
    canonical = np.average(np.stack(embeddings), weights=weights, axis=0)
    norm = np.linalg.norm(canonical)
    canonical = canonical / (norm + 1e-8)

    # Quality score: average cosine similarity of all embeddings to centroid
    similarities = [
        float(np.dot(emb, canonical))
        for emb in embeddings
    ]
    quality = float(np.mean(similarities))

    import time
    result = CanonicalVoice(
        creator_id=creator_id,
        embedding=canonical,
        reference_count=n,
        last_updated=time.strftime("%Y-%m-%d %H:%M:%S"),
        dominant_language="hi",
        quality_score=round(quality, 3)
    )

    log.info("canonical_voice_built",
             creator_id=creator_id,
             references=n,
             quality=result.quality_score)

    return result


def save_canonical_voice(voice: CanonicalVoice, cache_dir: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{voice.creator_id}_canonical.npz")
    meta_path = os.path.join(cache_dir, f"{voice.creator_id}_meta.json")

    np.savez_compressed(path, embedding=voice.embedding)
    with open(meta_path, "w") as f:
        json.dump({
            "creator_id": voice.creator_id,
            "reference_count": voice.reference_count,
            "last_updated": voice.last_updated,
            "dominant_language": voice.dominant_language,
            "quality_score": voice.quality_score
        }, f, indent=2)

    log.info("canonical_voice_saved", path=path)
    return path


def load_canonical_voice(creator_id: str, cache_dir: str) -> CanonicalVoice | None:
    path = os.path.join(cache_dir, f"{creator_id}_canonical.npz")
    meta_path = os.path.join(cache_dir, f"{creator_id}_meta.json")

    if not os.path.exists(path) or not os.path.exists(meta_path):
        return None

    data = np.load(path)
    with open(meta_path) as f:
        meta = json.load(f)

    return CanonicalVoice(
        creator_id=creator_id,
        embedding=data["embedding"],
        reference_count=meta["reference_count"],
        last_updated=meta["last_updated"],
        dominant_language=meta["dominant_language"],
        quality_score=meta["quality_score"]
    )


def voice_similarity(emb_a: np.ndarray, emb_b: np.ndarray) -> float:
    """Cosine similarity between two voice embeddings. 0-1."""
    norm_a = np.linalg.norm(emb_a)
    norm_b = np.linalg.norm(emb_b)
    if norm_a < 1e-8 or norm_b < 1e-8:
        return 0.0
    return float(np.dot(emb_a, emb_b) / (norm_a * norm_b))


def check_voice_drift(
    new_audio_path: str,
    canonical: CanonicalVoice,
    threshold: float = 0.75
) -> dict:
    """
    Before using a new reference audio, check if it's consistent
    with the creator's canonical voice. If similarity < threshold,
    warn the user that this recording may cause voice inconsistency.
    """
    new_embedding = compute_voice_embedding(new_audio_path)
    similarity = voice_similarity(new_embedding, canonical.embedding)

    return {
        "similarity": round(similarity, 3),
        "consistent": similarity >= threshold,
        "warning": (
            f"This recording differs significantly from your previous voice profile "
            f"(similarity: {similarity:.0%}). Using it may cause inconsistency across "
            f"your video series. Consider using a more representative recording."
        ) if similarity < threshold else None
    }
