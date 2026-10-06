import os
import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from src.config import get_settings

settings = get_settings()

SUPPORTED_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


@dataclass
class VideoMetadata:
    duration_seconds: float
    fps: float
    resolution: str
    width: int
    height: int
    codec: str
    audio_codec: str
    has_audio: bool
    file_size_bytes: int


class ValidationError(Exception):
    pass


def validate_and_extract_metadata(file_path: str) -> VideoMetadata:
    path = Path(file_path)

    if not path.exists():
        raise ValidationError(f"File not found: {file_path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValidationError(f"Unsupported format: {path.suffix}. Supported: {SUPPORTED_FORMATS}")

    size = os.path.getsize(file_path)
    max_bytes = settings.max_video_size_mb * 1024 * 1024
    if size > max_bytes:
        raise ValidationError(f"File too large: {size / 1e9:.1f}GB (max {settings.max_video_size_mb / 1024:.0f}GB)")

    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", file_path],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        raise ValidationError("Cannot read video file — corrupted or invalid format")

    probe = json.loads(result.stdout)

    video_stream = next(
        (s for s in probe["streams"] if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in probe["streams"] if s["codec_type"] == "audio"), None
    )

    if not video_stream:
        raise ValidationError("No video stream found in file")

    duration = float(probe["format"].get("duration", 0))

    if duration < 5:
        raise ValidationError(f"Video too short: {duration:.1f}s (minimum 5s)")

    if duration > settings.max_video_duration_seconds:
        raise ValidationError(
            f"Video too long: {duration / 3600:.1f}hr "
            f"(maximum {settings.max_video_duration_seconds / 3600:.0f}hr)"
        )

    fps_str = video_stream.get("r_frame_rate", "24/1")
    num, den = fps_str.split("/")
    fps = float(num) / float(den)

    return VideoMetadata(
        duration_seconds=duration,
        fps=round(fps, 2),
        resolution=f"{video_stream['width']}x{video_stream['height']}",
        width=video_stream["width"],
        height=video_stream["height"],
        codec=video_stream.get("codec_name", "unknown"),
        audio_codec=audio_stream.get("codec_name", "none") if audio_stream else "none",
        has_audio=audio_stream is not None,
        file_size_bytes=size
    )
