"""Tests for video watermarking."""
import os
import tempfile

from src.ingestion.watermarker import apply_watermark


def test_watermark_fallback_when_dummy_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_vid = os.path.join(tmpdir, "in.mp4")
        output_vid = os.path.join(tmpdir, "out.mp4")
        with open(input_vid, "wb") as f:
            f.write(b"dummy_video_stream")

        res = apply_watermark(input_vid, output_vid)
        assert os.path.exists(res)
        assert os.path.getsize(res) > 0
