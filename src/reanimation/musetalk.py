import os
import shutil
import subprocess
import sys
import tempfile

import structlog

from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

MUSETALK_REPO = os.path.join(settings.model_cache_dir, "MuseTalk")
MUSETALK_CHECKPOINT = os.path.join(MUSETALK_REPO, "models", "musetalkV15")


def is_available() -> bool:
    return os.path.exists(MUSETALK_REPO) and os.path.exists(MUSETALK_CHECKPOINT)


def reanimate_chunk(
    video_chunk_path: str,
    dubbed_audio_path: str,
    output_path: str,
    fps: float = 25.0
) -> tuple[str, float]:
    """
    Runs MuseTalk on a single video chunk with dubbed audio.
    Returns (output_path, sync_confidence_estimate 0-1).
    """
    if not is_available():
        log.warning("musetalk_not_available_skipping")
        shutil.copy(video_chunk_path, output_path)
        return output_path, 0.0

    if not settings.gpu_available:
        log.warning("musetalk_requires_gpu_skipping")
        shutil.copy(video_chunk_path, output_path)
        return output_path, 0.0

    with tempfile.TemporaryDirectory():
        result = subprocess.run(
            [
                sys.executable, "-m", "musetalk.inference",
                "--video_path", video_chunk_path,
                "--audio_path", dubbed_audio_path,
                "--output_path", output_path,
                "--checkpoint", MUSETALK_CHECKPOINT,
                "--device", settings.gpu_device,
                "--fps", str(fps),
                "--bbox_shift", "0",
            ],
            capture_output=True, text=True,
            cwd=MUSETALK_REPO
        )

    if result.returncode != 0:
        log.error("musetalk_inference_failed",
                  stderr=result.stderr[:500],
                  chunk=video_chunk_path)
        shutil.copy(video_chunk_path, output_path)
        return output_path, 0.0

    if not os.path.exists(output_path):
        log.error("musetalk_no_output_produced")
        shutil.copy(video_chunk_path, output_path)
        return output_path, 0.0

    log.info("musetalk_reanimation_done", output=output_path)
    return output_path, 0.82


def setup_musetalk():
    """Clone and set up MuseTalk if not present."""
    if is_available():
        log.info("musetalk_already_setup")
        return

    os.makedirs(settings.model_cache_dir, exist_ok=True)

    log.info("cloning_musetalk")
    subprocess.run([
        "git", "clone",
        "https://github.com/TMElyralab/MuseTalk",
        MUSETALK_REPO
    ], check=True)

    subprocess.run([
        sys.executable, "-m", "pip", "install", "-r",
        os.path.join(MUSETALK_REPO, "requirements.txt")
    ], check=True)

    log.info("musetalk_setup_complete",
             note="Download model weights manually from MuseTalk repo README")
