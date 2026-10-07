import os
import tempfile

import numpy as np
import soundfile as sf

from src.alignment.audio_adjuster import adjust_segment_timing, combine_dubbed_segments


def _make_wav(duration_seconds: float, sr: int = 22050) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    data = np.zeros(int(sr * duration_seconds))
    sf.write(f.name, data, sr)
    return f.name


def test_passthrough_when_target_zero():
    src = _make_wav(2.0)
    out = src + "_out.wav"
    try:
        path, info = adjust_segment_timing(src, 0, out)
        assert info["method"] == "passthrough"
        assert info["flagged"] is False
    finally:
        os.unlink(src)
        if os.path.exists(out):
            os.unlink(out)


def test_time_stretch_within_tolerance():
    # 2s audio, target 1.9s — ratio 2000/1900 = 1.05 — within 1.15 threshold
    src = _make_wav(2.0)
    out = src + "_out.wav"
    try:
        path, info = adjust_segment_timing(src, 1900, out)
        assert info["method"] == "time_stretch"
        assert info["flagged"] is False
        assert os.path.exists(out)
    finally:
        os.unlink(src)
        if os.path.exists(out):
            os.unlink(out)


def test_flag_when_ratio_too_large():
    # 3s audio, target 1s — ratio 3.0 — exceeds 1.30 threshold
    src = _make_wav(3.0)
    out = src + "_out.wav"
    try:
        path, info = adjust_segment_timing(src, 1000, out)
        assert info["flagged"] is True
    finally:
        os.unlink(src)
        if os.path.exists(out):
            os.unlink(out)


def test_combine_segments_creates_output():
    segs = []
    paths = []
    for i in range(3):
        p = _make_wav(1.0)
        paths.append(p)
        segs.append({"start_ms": i * 1200, "end_ms": (i + 1) * 1200, "dubbed_audio_path": p})

    out = tempfile.mktemp(suffix=".wav")
    try:
        result = combine_dubbed_segments(segs, out)
        assert os.path.exists(result)
        info = sf.info(result)
        assert info.duration > 2.5
    finally:
        for p in paths:
            if os.path.exists(p):
                os.unlink(p)
        if os.path.exists(out):
            os.unlink(out)


def test_combine_skips_missing_audio():
    segs = [
        {"start_ms": 0, "end_ms": 1000, "dubbed_audio_path": "/nonexistent/file.wav"},
        {"start_ms": 1000, "end_ms": 2000, "dubbed_audio_path": _make_wav(1.0)}
    ]
    out = tempfile.mktemp(suffix=".wav")
    try:
        result = combine_dubbed_segments(segs, out)
        assert os.path.exists(result)
    finally:
        if os.path.exists(segs[1]["dubbed_audio_path"]):
            os.unlink(segs[1]["dubbed_audio_path"])
        if os.path.exists(out):
            os.unlink(out)
