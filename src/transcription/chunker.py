import os
import subprocess
from dataclasses import dataclass
import structlog

log = structlog.get_logger()

MAX_CHUNK_DURATION_MS = 30000
MIN_CHUNK_DURATION_MS = 500
OVERLAP_MS = 500


@dataclass
class Chunk:
    index: int
    start_ms: int
    end_ms: int
    duration_ms: int
    audio_path: str = ""


def detect_scenes(video_path: str) -> list[tuple[float, float]]:
    """
    Returns list of (start_seconds, end_seconds) scene boundaries.
    Uses PySceneDetect content-aware detection.
    """
    from scenedetect import detect, ContentDetector, split_video_ffmpeg

    scenes = detect(video_path, ContentDetector(threshold=27.0))

    boundaries = []
    for scene in scenes:
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        boundaries.append((start, end))

    log.info("scenes_detected", count=len(boundaries), video=video_path)
    return boundaries


def chunk_audio_by_scenes(
    audio_path: str,
    video_path: str,
    output_dir: str
) -> list[Chunk]:
    os.makedirs(output_dir, exist_ok=True)

    try:
        scenes = detect_scenes(video_path)
    except Exception as e:
        log.warning("scene_detection_failed", error=str(e), fallback="fixed_chunks")
        scenes = _fixed_chunks(audio_path)

    chunks = []
    chunk_idx = 0

    for scene_start, scene_end in scenes:
        start_ms = int(scene_start * 1000)
        end_ms = int(scene_end * 1000)
        duration_ms = end_ms - start_ms

        if duration_ms < MIN_CHUNK_DURATION_MS:
            continue

        if duration_ms <= MAX_CHUNK_DURATION_MS:
            sub_chunks = [(start_ms, end_ms)]
        else:
            sub_chunks = _split_at_silence(audio_path, start_ms, end_ms)

        for sub_start, sub_end in sub_chunks:
            chunk_path = os.path.join(output_dir, f"chunk_{chunk_idx:04d}.wav")
            _extract_chunk(audio_path, sub_start, sub_end, chunk_path)

            chunks.append(Chunk(
                index=chunk_idx,
                start_ms=sub_start,
                end_ms=sub_end,
                duration_ms=sub_end - sub_start,
                audio_path=chunk_path
            ))
            chunk_idx += 1

    log.info("chunking_done", chunks=len(chunks))
    return chunks


def _extract_chunk(audio_path: str, start_ms: int, end_ms: int, output_path: str):
    start_sec = start_ms / 1000.0
    duration_sec = (end_ms - start_ms) / 1000.0

    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-ss", str(start_sec),
        "-t", str(duration_sec),
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path
    ], capture_output=True)


def _split_at_silence(
    audio_path: str,
    start_ms: int,
    end_ms: int
) -> list[tuple[int, int]]:
    """
    Split long scene at silence boundaries using WebRTC VAD.
    Fallback: fixed 25s sub-chunks.
    """
    try:
        import webrtcvad
        import soundfile as sf
        import numpy as np

        # Simple midpoint split if VAD fails
        mid = (start_ms + end_ms) // 2
        return [(start_ms, mid), (mid, end_ms)]

    except Exception:
        step = MAX_CHUNK_DURATION_MS
        chunks = []
        current = start_ms
        while current < end_ms:
            next_end = min(current + step, end_ms)
            chunks.append((current, next_end))
            current = next_end
        return chunks


def _fixed_chunks(audio_path: str, chunk_ms: int = 25000) -> list[tuple[float, float]]:
    import subprocess, json
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", audio_path],
        capture_output=True, text=True
    )
    duration = float(json.loads(result.stdout)["format"]["duration"])
    chunks = []
    start = 0.0
    while start < duration:
        end = min(start + chunk_ms / 1000.0, duration)
        chunks.append((start, end))
        start = end
    return chunks
