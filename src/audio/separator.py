import os
import shutil
import subprocess

import structlog

from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# mdx_extra_q: 4x faster on CPU, slight quality tradeoff vs htdemucs
# htdemucs: best quality, use on GPU
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

    result = subprocess.run(
        [
            "python", "-m", "demucs",
            "--model", model,
            "--two-stems", "vocals",
            "--out", output_dir,
            audio_path
        ],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        log.error("demucs_failed", stderr=result.stderr)
        raise RuntimeError(f"Demucs separation failed: {result.stderr[:500]}")

    # Demucs output structure: output_dir/model/track_name/vocals.wav + no_vocals.wav
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
    demucs_out = os.path.join(output_dir, model, audio_name)

    vocals_src = os.path.join(demucs_out, "vocals.wav")
    background_src = os.path.join(demucs_out, "no_vocals.wav")

    speech_dst = os.path.join(output_dir, "speech.wav")
    background_dst = os.path.join(output_dir, "background.wav")

    shutil.move(vocals_src, speech_dst)
    shutil.move(background_src, background_dst)

    # Clean up demucs intermediate dirs
    shutil.rmtree(os.path.join(output_dir, model), ignore_errors=True)

    log.info("demucs_separation_done", speech=speech_dst, background=background_dst)
    return speech_dst, background_dst


def fallback_silence_background(output_dir: str, duration_seconds: float) -> str:
    """
    If separation fails, generate a silent background track.
    Used as emergency fallback only.
    """
    import subprocess
    background_path = os.path.join(output_dir, "background.wav")
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i",
        f"anullsrc=r=16000:cl=mono:d={duration_seconds}",
        "-y", background_path
    ], capture_output=True)
    log.warning("using_silent_background_fallback")
    return background_path
