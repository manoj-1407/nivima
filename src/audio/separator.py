import os
import shutil
import subprocess
import sys

import structlog

from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# mdx_extra_q: fast, lower memory footprint
# htdemucs: high quality
CPU_MODEL = "mdx_extra_q"
GPU_MODEL = "htdemucs"


def separate_audio(audio_path: str, output_dir: str) -> tuple[str, str]:
    """
    Returns (speech_path, background_path)
    speech_path:     vocals only (the speaker's voice)
    background_path: everything else (music, SFX, ambient)
    """
    os.makedirs(output_dir, exist_ok=True)

    model = GPU_MODEL if settings.gpu_available else CPU_MODEL
    log.info("demucs_separation_start", model=model, audio=audio_path)

    # Use sys.executable to ensure current venv Python is used on Windows & Linux
    cmd = [
        sys.executable, "-m", "demucs",
        "--model", model,
        "--two-stems", "vocals",
        "--out", output_dir,
        audio_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.warning("demucs_gpu_failed_trying_cpu", stderr=result.stderr[:300])
            # If GPU run failed (e.g. OOM or driver issue), retry on CPU
            if model != CPU_MODEL:
                cmd[4] = CPU_MODEL
                cmd.extend(["-d", "cpu"])
                result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Demucs separation failed: {result.stderr[:500]}")
    except Exception as e:
        log.error("demucs_execution_error", error=str(e))
        raise

    # Locate vocals.wav and no_vocals.wav recursively in output_dir
    vocals_src = None
    background_src = None

    for root, _, files in os.walk(output_dir):
        if "vocals.wav" in files:
            vocals_src = os.path.join(root, "vocals.wav")
        if "no_vocals.wav" in files:
            background_src = os.path.join(root, "no_vocals.wav")

    speech_dst = os.path.join(output_dir, "speech.wav")
    background_dst = os.path.join(output_dir, "background.wav")

    if vocals_src and background_src and os.path.exists(vocals_src) and os.path.exists(background_src):
        shutil.move(vocals_src, speech_dst)
        shutil.move(background_src, background_dst)
    else:
        # Emergency copy of original if demucs didn't produce expected files
        shutil.copy(audio_path, speech_dst)
        fallback_silence_background(output_dir, 5.0)

    # Clean up intermediate model folders
    for item in os.listdir(output_dir):
        p = os.path.join(output_dir, item)
        if os.path.isdir(p) and item not in ("speech.wav", "background.wav"):
            shutil.rmtree(p, ignore_errors=True)

    log.info("demucs_separation_done", speech=speech_dst, background=background_dst)
    return speech_dst, background_dst


def fallback_silence_background(output_dir: str, duration_seconds: float) -> str:
    """
    If separation fails, generate a silent background track.
    Used as emergency fallback only.
    """
    background_path = os.path.join(output_dir, "background.wav")
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i",
        f"anullsrc=r=16000:cl=mono:d={duration_seconds}",
        "-y", background_path
    ], capture_output=True)
    log.warning("using_silent_background_fallback")
    return background_path
