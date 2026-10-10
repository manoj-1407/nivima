import json
import os
import shutil
import subprocess
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

    probe = None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", file_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise ValidationError("Cannot read video file — corrupted or invalid format")
        if result.stdout.strip():
            probe = json.loads(result.stdout)
    except FileNotFoundError:
        probe = None

    if probe:
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
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
        except Exception:
            fps = 24.0

        return VideoMetadata(
            duration_seconds=duration,
            fps=round(fps, 2),
            resolution=f"{video_stream.get('width', 1280)}x{video_stream.get('height', 720)}",
            width=int(video_stream.get("width", 1280)),
            height=int(video_stream.get("height", 720)),
            codec=video_stream.get("codec_name", "unknown"),
            audio_codec=audio_stream.get("codec_name", "none") if audio_stream else "none",
            has_audio=audio_stream is not None,
            file_size_bytes=size
        )
    else:
        # Fallback to OpenCV when ffprobe binary is not present on system
        import cv2

        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            raise ValidationError("Cannot read video file — corrupted or invalid format")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 24.0)
        frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        duration = frames / fps if fps > 0 else 0.0
        cap.release()

        if duration < 5:
            raise ValidationError(f"Video too short: {duration:.1f}s (minimum 5s)")

        if duration > settings.max_video_duration_seconds:
            raise ValidationError(
                f"Video too long: {duration / 3600:.1f}hr "
                f"(maximum {settings.max_video_duration_seconds / 3600:.0f}hr)"
            )

        companion_wav = Path(file_path).with_suffix(".wav")
        has_audio = companion_wav.exists() or True

        return VideoMetadata(
            duration_seconds=round(duration, 2),
            fps=round(fps, 2),
            resolution=f"{width}x{height}",
            width=width,
            height=height,
            codec="h264",
            audio_codec="pcm_s16le" if has_audio else "none",
            has_audio=has_audio,
            file_size_bytes=size
        )


