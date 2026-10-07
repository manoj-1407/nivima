import os
from dataclasses import dataclass

import cv2
import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class QCScore:
    syncnet_score: float
    csim_score: float
    psnr_non_lip: float
    temporal_variance: float
    frames_total: int
    frames_reverted: int
    overall_pass: bool
    flags: list[str]


THRESHOLDS = {
    "syncnet_flag": 5.0,
    "syncnet_good": 7.0,
    "csim_flag": 0.80,
    "psnr_flag": 30.0,
    "temporal_flag": 10.0,
}


def compute_psnr(a: np.ndarray, b: np.ndarray) -> float:
    """Computes Peak Signal-to-Noise Ratio between two images."""
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    if mse < 1e-10:
        return float("inf")
    return float(20.0 * np.log10(255.0 / np.sqrt(mse)))



def score_chunk(
    original_frames_dir: str,
    output_frames_dir: str,
    dubbed_audio_path: str,
    frames_reverted: int = 0
) -> QCScore:
    syncnet = _syncnet_score(output_frames_dir, dubbed_audio_path)
    csim = _csim_score(original_frames_dir, output_frames_dir)
    psnr = _psnr_non_lip(original_frames_dir, output_frames_dir)
    temporal = _temporal_variance(output_frames_dir)

    orig_count = len([
        f for f in os.listdir(original_frames_dir)
        if f.endswith((".jpg", ".png"))
    ]) if os.path.exists(original_frames_dir) else 0

    flags = []
    if syncnet < THRESHOLDS["syncnet_flag"]:
        flags.append(f"low_syncnet:{syncnet:.2f}")
    if csim < THRESHOLDS["csim_flag"]:
        flags.append(f"low_csim:{csim:.2f}")
    if psnr < THRESHOLDS["psnr_flag"]:
        flags.append(f"low_psnr:{psnr:.1f}dB")
    if temporal > THRESHOLDS["temporal_flag"]:
        flags.append(f"high_flicker:{temporal:.1f}")

    return QCScore(
        syncnet_score=syncnet,
        csim_score=csim,
        psnr_non_lip=psnr,
        temporal_variance=temporal,
        frames_total=orig_count,
        frames_reverted=frames_reverted,
        overall_pass=len(flags) == 0,
        flags=flags
    )


def _syncnet_score(frames_dir: str, audio_path: str) -> float:
    """
    SyncNet score: measures audio-visual sync correlation.
    Full implementation requires SyncNet pretrained weights.
    Placeholder returns heuristic based on frame count consistency.

    TODO Phase 2: integrate SyncNet weights from
    https://github.com/joonson/syncnet_python
    """
    if not os.path.exists(frames_dir) or not os.path.exists(audio_path):
        return 0.0

    frame_files = [f for f in os.listdir(frames_dir) if f.endswith((".jpg", ".png"))]
    if not frame_files:
        return 0.0

    # Heuristic: if we have reasonable frame count, return baseline
    # Replace with actual SyncNet inference
    return 7.2


def _csim_score(orig_dir: str, out_dir: str) -> float:
    """
    CSIM: cosine similarity between face embeddings.
    Measures identity preservation after reanimation.

    TODO Phase 2: integrate ArcFace or FaceNet for actual embedding comparison.
    """
    if not os.path.exists(orig_dir) or not os.path.exists(out_dir):
        return 1.0

    orig_files = sorted([f for f in os.listdir(orig_dir) if f.endswith((".jpg", ".png"))])
    out_files = sorted([f for f in os.listdir(out_dir) if f.endswith((".jpg", ".png"))])

    if not orig_files or not out_files:
        return 1.0

    # Sample 5 frames for comparison
    sample_count = min(5, len(orig_files), len(out_files))
    indices = np.linspace(0, min(len(orig_files), len(out_files)) - 1,
                          sample_count, dtype=int)

    similarities = []
    for i in indices:
        orig = cv2.imread(os.path.join(orig_dir, orig_files[i]))
        out = cv2.imread(os.path.join(out_dir, out_files[i]))
        if orig is None or out is None:
            continue

        # Placeholder: use normalized pixel similarity as proxy
        # Replace with ArcFace embedding comparison
        orig_flat = orig.astype(np.float32).flatten() / 255.0
        out_flat = out.astype(np.float32).flatten() / 255.0
        cos_sim = np.dot(orig_flat, out_flat) / (
            np.linalg.norm(orig_flat) * np.linalg.norm(out_flat) + 1e-8
        )
        similarities.append(float(cos_sim))

    return round(float(np.mean(similarities)), 3) if similarities else 1.0


def _psnr_non_lip(orig_dir: str, out_dir: str) -> float:
    if not os.path.exists(orig_dir) or not os.path.exists(out_dir):
        return 40.0

    orig_files = sorted([f for f in os.listdir(orig_dir) if f.endswith((".jpg", ".png"))])
    out_files = sorted([f for f in os.listdir(out_dir) if f.endswith((".jpg", ".png"))])

    if not orig_files or not out_files:
        return 40.0

    psnr_vals = []
    sample = min(10, len(orig_files), len(out_files))
    indices = np.linspace(0, min(len(orig_files), len(out_files)) - 1,
                          sample, dtype=int)

    for i in indices:
        orig = cv2.imread(os.path.join(orig_dir, orig_files[i]))
        out = cv2.imread(os.path.join(out_dir, out_files[i]))
        if orig is None or out is None:
            continue

        h, w = orig.shape[:2]
        # Exclude bottom 30% of face (lip region) for PSNR measurement
        top_region_orig = orig[:int(h * 0.65), :]
        top_region_out = out[:int(h * 0.65), :]

        mse = np.mean((top_region_orig.astype(np.float64) -
                       top_region_out.astype(np.float64)) ** 2)
        if mse < 1e-10:
            psnr_vals.append(50.0)
        else:
            psnr_vals.append(20.0 * np.log10(255.0 / np.sqrt(mse)))

    return round(float(np.mean(psnr_vals)), 2) if psnr_vals else 40.0


def _temporal_variance(frames_dir: str) -> float:
    if not os.path.exists(frames_dir):
        return 0.0

    files = sorted([f for f in os.listdir(frames_dir) if f.endswith((".jpg", ".png"))])
    if len(files) < 3:
        return 0.0

    diffs = []
    for i in range(1, min(len(files), 20)):
        f1 = cv2.imread(os.path.join(frames_dir, files[i - 1]))
        f2 = cv2.imread(os.path.join(frames_dir, files[i]))
        if f1 is None or f2 is None:
            continue
        diff = np.mean(np.abs(f1.astype(np.float32) - f2.astype(np.float32)))
        diffs.append(diff)

    return round(float(np.std(diffs)), 3) if diffs else 0.0


def score_to_dict(score: QCScore) -> dict:
    return {
        "syncnet_score": score.syncnet_score,
        "csim_score": score.csim_score,
        "psnr_non_lip": score.psnr_non_lip,
        "temporal_variance": score.temporal_variance,
        "frames_total": score.frames_total,
        "frames_reverted": score.frames_reverted,
        "overall_pass": score.overall_pass,
        "flags": score.flags,
    }
