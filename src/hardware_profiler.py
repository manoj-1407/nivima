"""
Nivima Hardware Profiler & ETA Estimator.
Analyzes machine hardware (RTX 4050/3070/CPU, VRAM, RAM) and generates exact processing ETAs.
"""

import os
import platform
import shutil
import sys
from dataclasses import dataclass


@dataclass
class HardwareProfile:
    os_name: str
    python_version: str
    cpu_cores: int
    ram_gb: float
    gpu_available: bool
    gpu_name: str
    vram_gb: float
    cuda_version: str | None
    tier: str  # 'entry_laptop_gpu', 'mid_gpu', 'high_gpu', 'cpu'
    ffmpeg_installed: bool


def detect_hardware() -> HardwareProfile:
    os_name = f"{platform.system()} {platform.release()}"
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    cpu_cores = os.cpu_count() or 4

    ram_gb = 16.0
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        pass

    gpu_available = False
    gpu_name = "CPU Only (No NVIDIA GPU)"
    vram_gb = 0.0
    cuda_version = None

    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1)
            cuda_version = torch.version.cuda
    except Exception:
        pass

    ffmpeg_installed = shutil.which("ffmpeg") is not None

    # Determine Tier
    if not gpu_available:
        tier = "cpu"
    elif vram_gb < 7.5:
        tier = "entry_laptop_gpu"  # e.g. RTX 4050 Laptop (6GB), RTX 3050 (4/6GB), RTX 2060 (6GB)
    elif vram_gb < 11.0:
        tier = "mid_gpu"           # e.g. RTX 3070 (8GB), RTX 4060 (8GB), RTX 4070 (8GB)
    else:
        tier = "high_gpu"          # e.g. RTX 3090, 4080, 4090 (12GB+)

    return HardwareProfile(
        os_name=os_name,
        python_version=python_version,
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        vram_gb=vram_gb,
        cuda_version=cuda_version,
        tier=tier,
        ffmpeg_installed=ffmpeg_installed
    )


def estimate_processing_eta(video_duration_seconds: float, target_count: int = 1) -> dict:
    """
    Calculates estimated runtime per stage and total pipeline ETA.
    """
    hw = detect_hardware()
    dur_s = video_duration_seconds

    if hw.tier in ("entry_laptop_gpu", "mid_gpu", "high_gpu"):
        # GPU Speed Multipliers
        demucs_sec = max(3.0, dur_s * 0.15)
        whisper_sec = max(2.0, dur_s * 0.08)
        translation_sec = max(1.5, dur_s * 0.04 * target_count)
        tts_sec = max(4.0, dur_s * 0.32 * target_count)
        assemble_sec = max(2.0, dur_s * 0.05 * target_count)
    else:
        # CPU Speed Multipliers (significantly slower)
        demucs_sec = max(15.0, dur_s * 1.8)
        whisper_sec = max(10.0, dur_s * 1.2)
        translation_sec = max(5.0, dur_s * 0.4 * target_count)
        tts_sec = max(20.0, dur_s * 3.5 * target_count)
        assemble_sec = max(4.0, dur_s * 0.15 * target_count)

    total_est_seconds = demucs_sec + whisper_sec + translation_sec + tts_sec + assemble_sec

    return {
        "hardware_tier": hw.tier,
        "gpu_name": hw.gpu_name,
        "vram_gb": hw.vram_gb,
        "video_duration_seconds": round(dur_s, 1),
        "target_languages_count": target_count,
        "breakdown": {
            "vocal_separation": round(demucs_sec, 1),
            "whisper_asr": round(whisper_sec, 1),
            "translation": round(translation_sec, 1),
            "voice_synthesis": round(tts_sec, 1),
            "assembly_mux": round(assemble_sec, 1),
        },
        "total_eta_seconds": round(total_est_seconds, 1),
        "speed_ratio": round(total_est_seconds / max(1.0, dur_s), 2),
        "is_faster_than_realtime": total_est_seconds < dur_s
    }


def format_hardware_report() -> str:
    hw = detect_hardware()
    lines = [
        "═" * 60,
        "  Nivima Hardware & Capability Profile",
        "═" * 60,
        f"  OS:              {hw.os_name}",
        f"  Python:          {hw.python_version}",
        f"  CPU Cores:       {hw.cpu_cores} cores • {hw.ram_gb:.1f} GB RAM",
        f"  GPU Hardware:    {hw.gpu_name}",
        f"  VRAM Available:  {hw.vram_gb:.1f} GB" if hw.gpu_available else "  VRAM Available:  0 GB (CPU Mode)",
        f"  CUDA Version:    {hw.cuda_version or 'N/A'}",
        f"  Hardware Tier:   {hw.tier.replace('_', ' ').title()}",
        f"  FFmpeg Engine:   {'✓ Detected' if hw.ffmpeg_installed else '✗ Missing on PATH'}",
        "═" * 60,
    ]

    if hw.tier == "entry_laptop_gpu":
        lines.append("  💡 Laptop Optimization: 6GB VRAM detected (RTX 4050/3060).")
        lines.append("     Auto-activating int8_float16 Whisper + sequential VRAM flushing.")
    elif hw.tier == "cpu":
        lines.append("  ⚠ WARNING: Running in CPU-only mode. GPU acceleration is inactive.")
        lines.append("     Execution will take ~7x video length. Install PyTorch with CUDA!")

    return "\n".join(lines)
