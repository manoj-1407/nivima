import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.ingestion.validator import validate_and_extract_metadata, ValidationError


MOCK_PROBE_OUTPUT = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "r_frame_rate": "24/1"
        },
        {
            "codec_type": "audio",
            "codec_name": "aac"
        }
    ],
    "format": {
        "duration": "600.0",
        "size": "500000000"
    }
}


def _make_temp_video(suffix=".mp4", size_bytes=1000):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(b"0" * size_bytes)
    f.close()
    return f.name


@patch("src.ingestion.validator.subprocess.run")
def test_valid_mp4(mock_run):
    import json
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(MOCK_PROBE_OUTPUT))
    path = _make_temp_video(".mp4")
    try:
        meta = validate_and_extract_metadata(path)
        assert meta.fps == 24.0
        assert meta.resolution == "1920x1080"
        assert meta.has_audio is True
        assert meta.duration_seconds == 600.0
    finally:
        os.unlink(path)


def test_unsupported_format():
    path = _make_temp_video(".docx")
    try:
        with pytest.raises(ValidationError, match="Unsupported format"):
            validate_and_extract_metadata(path)
    finally:
        os.unlink(path)


def test_file_not_found():
    with pytest.raises(ValidationError, match="File not found"):
        validate_and_extract_metadata("/nonexistent/path/video.mp4")


@patch("src.ingestion.validator.subprocess.run")
def test_video_too_short(mock_run):
    import json
    probe = {**MOCK_PROBE_OUTPUT, "format": {"duration": "3.0"}}
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(probe))
    path = _make_temp_video(".mp4")
    try:
        with pytest.raises(ValidationError, match="too short"):
            validate_and_extract_metadata(path)
    finally:
        os.unlink(path)


@patch("src.ingestion.validator.subprocess.run")
def test_no_audio_stream(mock_run):
    import json
    probe = {
        "streams": [MOCK_PROBE_OUTPUT["streams"][0]],
        "format": MOCK_PROBE_OUTPUT["format"]
    }
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(probe))
    path = _make_temp_video(".mp4")
    try:
        meta = validate_and_extract_metadata(path)
        assert meta.has_audio is False
    finally:
        os.unlink(path)


@patch("src.ingestion.validator.subprocess.run")
def test_corrupted_file(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Invalid data")
    path = _make_temp_video(".mp4")
    try:
        with pytest.raises(ValidationError, match="Cannot read"):
            validate_and_extract_metadata(path)
    finally:
        os.unlink(path)
