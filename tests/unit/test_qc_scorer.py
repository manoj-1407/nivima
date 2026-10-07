import os
import tempfile

import cv2
import numpy as np

from src.qc.scorer import THRESHOLDS, compute_psnr, score_chunk, score_to_dict


def _make_frames_dir(count: int = 5, noise: float = 0.0) -> str:
    d = tempfile.mkdtemp()
    for i in range(count):
        frame = np.ones((480, 854, 3), dtype=np.uint8) * 128
        if noise > 0:
            frame = np.clip(
                frame + np.random.normal(0, noise * 255, frame.shape),
                0, 255
            ).astype(np.uint8)
        cv2.imwrite(os.path.join(d, f"{i:06d}.jpg"), frame)
    return d


def _make_wav(d: str) -> str:
    import soundfile as sf
    path = os.path.join(d, "audio.wav")
    sf.write(path, np.zeros(22050), 22050)
    return path


def test_psnr_identical_images():
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    assert compute_psnr(img, img) == float("inf")


def test_psnr_different_images():
    a = np.ones((100, 100, 3), dtype=np.uint8) * 128
    b = np.ones((100, 100, 3), dtype=np.uint8) * 200
    psnr = compute_psnr(a, b)
    assert psnr < 50.0
    assert psnr > 0.0


def test_score_chunk_missing_dirs():
    score = score_chunk("/nonexistent", "/nonexistent", "/nonexistent.wav")
    assert score.syncnet_score >= 0
    assert isinstance(score.flags, list)
    assert isinstance(score.overall_pass, bool)


def test_score_chunk_identical_frames():
    orig_dir = _make_frames_dir(5, noise=0.0)
    out_dir = _make_frames_dir(5, noise=0.0)
    with tempfile.TemporaryDirectory() as d:
        audio = _make_wav(d)
        score = score_chunk(orig_dir, out_dir, audio)
    assert score.psnr_non_lip >= THRESHOLDS["psnr_flag"]


def test_score_chunk_noisy_frames_lower_psnr():
    orig_dir = _make_frames_dir(5, noise=0.0)
    noisy_dir = _make_frames_dir(5, noise=0.3)
    with tempfile.TemporaryDirectory() as d:
        audio = _make_wav(d)
        clean_score = score_chunk(orig_dir, orig_dir, audio)
        noisy_score = score_chunk(orig_dir, noisy_dir, audio)
    assert clean_score.psnr_non_lip >= noisy_score.psnr_non_lip


def test_score_to_dict_keys():
    orig_dir = _make_frames_dir(3)
    with tempfile.TemporaryDirectory() as d:
        audio = _make_wav(d)
        score = score_chunk(orig_dir, orig_dir, audio)
    d = score_to_dict(score)
    required = ["syncnet_score", "csim_score", "psnr_non_lip",
                "temporal_variance", "frames_total", "frames_reverted",
                "overall_pass", "flags"]
    for key in required:
        assert key in d, f"Missing key: {key}"


def test_frames_reverted_tracked():
    orig_dir = _make_frames_dir(10)
    with tempfile.TemporaryDirectory() as d:
        audio = _make_wav(d)
        score = score_chunk(orig_dir, orig_dir, audio, frames_reverted=3)
    assert score.frames_reverted == 3
