"""Integration tests for the real multi-case test dataset in data/test_samples.

Verifies all 6 test media files exist and can be read cleanly by the
core pipeline modules WITHOUT requiring heavy models (no GPU, no downloads).
"""

import json
import shutil
from pathlib import Path

import cv2
import pytest
import soundfile as sf

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "test_samples"
MANIFEST_PATH = DATA_DIR / "manifest.json"

_FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
requires_ffmpeg = pytest.mark.skipif(
    not _FFMPEG_AVAILABLE,
    reason="ffmpeg not on PATH — install ffmpeg to run these tests",
)


# ─── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST_PATH.exists(), f"Manifest file missing: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


# ─── Dataset Integrity ───────────────────────────────────────────────────────

def test_manifest_structure_and_files(manifest):
    """All files declared in manifest must exist and have non-zero size."""
    test_cases = manifest.get("test_cases", [])
    assert len(test_cases) >= 6, "Expected at least 6 test cases in manifest"

    for tc in test_cases:
        file_path = DATA_DIR / tc["file"]
        assert file_path.exists(), f"Test file missing: {file_path}"
        assert file_path.stat().st_size > 0, f"Test file is empty: {file_path}"

        if "audio_companion" in tc:
            companion = DATA_DIR / tc["audio_companion"]
            assert companion.exists(), f"Companion audio missing: {companion}"
            assert companion.stat().st_size > 0


def test_real_audio_samples_valid(manifest):
    """All audio files open cleanly with soundfile and have valid sample rates."""
    for tc in manifest["test_cases"]:
        audio_target = None
        if tc["type"] == "audio":
            audio_target = DATA_DIR / tc["file"]
        elif "audio_companion" in tc:
            audio_target = DATA_DIR / tc["audio_companion"]

        if audio_target and audio_target.exists():
            data, sr = sf.read(str(audio_target))
            assert sr in [8000, 16000, 22050, 44100, 48000], (
                f"Unusual sample rate {sr} in {audio_target}"
            )
            assert len(data) > 0, f"Audio signal is empty in {audio_target}"


def test_real_video_samples_valid(manifest):
    """All video files open cleanly with OpenCV and deliver at least 1 readable frame."""
    for tc in manifest["test_cases"]:
        if tc["type"] != "video":
            continue
        video_path = DATA_DIR / tc["file"]
        cap = cv2.VideoCapture(str(video_path))
        try:
            assert cap.isOpened(), f"Cannot open video: {video_path}"
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            assert fps > 0, f"Invalid fps in {video_path}"
            assert frame_count > 0, f"Zero frames in {video_path}"
            assert width >= 320 and height >= 240

            ret, frame = cap.read()
            assert ret, f"Could not read first frame of {video_path}"
            assert frame.shape == (int(height), int(width), 3)
        finally:
            cap.release()


# ─── Pipeline Module Smoke Tests (no heavy models) ──────────────────────────

def test_chunker_on_clean_lecture(tmp_path):
    """chunk_audio_by_scenes produces >= 1 chunk from the clean lecture sample."""
    from src.transcription.chunker import _fixed_chunks
    audio_path = DATA_DIR / "hindi_lecture_optics.wav"
    # _fixed_chunks is the direct, no-ffmpeg fallback — always works
    chunks = _fixed_chunks(str(audio_path), chunk_ms=5000)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    for start, end in chunks:
        assert end > start


def test_chunker_on_short_clip(tmp_path):
    """3-second audio yields exactly 1 fixed chunk (< 5s chunk_ms)."""
    from src.transcription.chunker import _fixed_chunks
    audio_path = DATA_DIR / "short_clip_3sec.wav"
    chunks = _fixed_chunks(str(audio_path), chunk_ms=5000)
    assert len(chunks) == 1
    start, end = chunks[0]
    assert abs((end - start) - 3.0) < 0.5


def test_fast_speech_tempo_adjuster(tmp_path):
    """audio_adjuster stretches the fast speech sample without errors."""
    from src.alignment.audio_adjuster import adjust_segment_timing
    src = DATA_DIR / "fast_speech_mismatch.wav"
    out = str(tmp_path / "stretched.wav")
    # Source is 3s, target 3.2s → mild stretch within tolerance
    result_path, info = adjust_segment_timing(str(src), 3200, out)
    assert Path(result_path).exists()
    assert not info["flagged"]  # 3.2/3.0 = 1.067x is within tolerance


def test_fast_speech_extreme_flag(tmp_path):
    """Extreme mismatch (3s audio forced to 7s) is flagged by audio_adjuster."""
    from src.alignment.audio_adjuster import adjust_segment_timing
    src = DATA_DIR / "fast_speech_mismatch.wav"
    out = str(tmp_path / "extreme.wav")
    _result, info = adjust_segment_timing(str(src), 7000, out)
    assert info["flagged"], "Expected flagged=True for 2.3x stretch ratio"


@requires_ffmpeg
def test_validator_on_clean_lecture():
    """VideoValidator accepts the clean lecture sample."""
    from src.ingestion.validator import validate_and_extract_metadata
    video_path = DATA_DIR / "hindi_lecture_optics.mp4"
    meta = validate_and_extract_metadata(str(video_path))
    assert meta.has_audio
    assert abs(meta.duration_seconds - 8.0) < 2.0
    assert meta.fps > 0


# ─── Phoneme / Viseme Correctness ────────────────────────────────────────────

def test_retroflex_phoneme_viseme_mapping(manifest):
    """TC-04 retroflex phonemes all map to 'retroflex' viseme with cheek_raiser > 0."""
    from src.translation.phoneme_map import get_blend_weights, get_viseme

    tc_retroflex = next(
        (tc for tc in manifest["test_cases"] if tc["id"] == "TC-04-RETROFLEX-PHONEMES"),
        None,
    )
    assert tc_retroflex is not None, "TC-04 missing from manifest"

    # Manifest stores IPA, phoneme_map uses ASCII romanisation
    ipa_to_ascii = {
        "ʈ": "tt",   # retroflex stop
        "ɖ": "dd",   # retroflex voiced stop
        "ɳ": "nn",   # retroflex nasal
        "ɻ": "zh",   # Tamil retroflex approximant (ழ)
        "ɭ": "ll",   # Tamil retroflex lateral (ள)
    }

    for ipa, ascii_ph in ipa_to_ascii.items():
        viseme = get_viseme(ascii_ph)
        assert viseme == "retroflex", (
            f"Phoneme '{ascii_ph}' (IPA: {ipa}) should map to 'retroflex', got '{viseme}'"
        )
        # get_blend_weights takes a VISEME (not a phoneme)
        weights = get_blend_weights(viseme)
        assert isinstance(weights, dict) and len(weights) > 0
        assert "cheek_raiser" in weights, (
            "Retroflex viseme should have cheek_raiser blendshape weight"
        )
        assert weights["cheek_raiser"] > 0, (
            "cheek_raiser should be > 0 for retroflex (tongue-curl creates cheek tension)"
        )


def test_scene_classifier_on_profile_video():
    """Profile face video should not be classified as FRONTAL_CLEAR."""
    from src.scene.classifier import Decision, classify_face
    from src.scene.face_analyzer import analyze_frame
    video_path = DATA_DIR / "profile_face_pose.mp4"
    cap = cv2.VideoCapture(str(video_path))
    ret, frame = cap.read()
    cap.release()
    assert ret, "Could not read frame from profile_face_pose.mp4"

    # The test video is a solid-colour frame (no real face), so it should come
    # back NO_FACE or LOW_RES — which is correct: not falsely "frontal".
    analysis = analyze_frame(frame)
    result = classify_face(analysis)
    assert result.decision != Decision.FRONTAL_CLEAR, (
        "Solid-colour test frame incorrectly classified as FRONTAL_CLEAR"
    )
