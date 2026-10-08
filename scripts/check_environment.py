#!/usr/bin/env python3
"""
Nivima Environment Checker — run this FIRST on the 3070 machine.
It checks everything before you start the pipeline.

Usage:
    python scripts/check_environment.py
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ok(msg): print(f"  \033[92m✓\033[0m {msg}")
def warn(msg): print(f"  \033[93m⚠\033[0m {msg}")
def fail(msg): print(f"  \033[91m✗\033[0m {msg}")
def section(title): print(f"\n\033[1m{'='*55}\033[0m\n  {title}\n{'='*55}")


def check_python():
    section("Python Environment")
    v = sys.version_info
    if v.major == 3 and v.minor >= 11:
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        warn(f"Python {v.major}.{v.minor} — recommend 3.11+")


def check_ffmpeg():
    section("System Tools")
    for tool in ["ffmpeg", "ffprobe"]:
        try:
            r = subprocess.run([tool, "-version"], capture_output=True, text=True)
            version_line = r.stdout.split("\n")[0]
            ok(f"{tool}: {version_line[:60]}")
        except FileNotFoundError:
            fail(f"{tool} NOT FOUND — install: sudo apt-get install ffmpeg")


def check_gpu():
    section("GPU")
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            ok(f"CUDA available: {gpu_name} ({vram:.1f}GB VRAM)")
            ok(f"PyTorch version: {torch.__version__}")
            ok(f"CUDA version: {torch.version.cuda}")
        else:
            warn("CUDA not available — pipeline will use CPU (slower)")
    except ImportError:
        fail("PyTorch not installed — run: pip install -r requirements.txt")


def check_packages():
    section("Python Packages")
    packages = {
        "faster_whisper": "faster-whisper",
        "transformers": "transformers",
        "TTS": "TTS (Coqui)",
        "demucs": "demucs",
        "librosa": "librosa",
        "soundfile": "soundfile",
        "scenedetect": "scenedetect",
        "ffmpeg": "ffmpeg-python",
        "cv2": "opencv-python",
        "structlog": "structlog",
        "celery": "celery",
        "fastapi": "fastapi",
        "sqlalchemy": "sqlalchemy",
        "boto3": "boto3",
    }
    missing = []
    for module, display in packages.items():
        try:
            __import__(module)
            ok(display)
        except ImportError:
            fail(f"{display} — NOT INSTALLED")
            missing.append(display)

    if missing:
        print(f"\n  To install: pip install -r requirements.txt")


def check_tts_models():
    section("TTS Models (Coqui)")
    try:
        from TTS.api import TTS
        available = TTS().list_models()
        available_set = set(available)

        models_to_check = [
            ("tts_models/hi/cv/vits", "Hindi VITS"),
            ("tts_models/bn/cv/vits", "Bengali VITS"),
            ("tts_models/mr/cv/vits", "Marathi VITS"),
            ("tts_models/multilingual/multi-dataset/xtts_v2", "XTTS-v2 (multilingual)"),
        ]
        for model_id, display in models_to_check:
            if model_id in available_set:
                ok(f"{display} ({model_id})")
            else:
                warn(f"{display} — not in model zoo, will use XTTS-v2 fallback")
    except Exception as e:
        warn(f"Could not check TTS models: {e}")


def check_model_files():
    section("Downloaded Model Files")
    from src.config import get_settings
    settings = get_settings()
    cache = settings.model_cache_dir

    if not os.path.exists(cache):
        warn(f"Model cache dir does not exist yet: {cache}")
        warn("Models will be downloaded on first run (30-60 min)")
        return

    ok(f"Model cache dir: {cache}")

    # Check for faster-whisper
    whisper_dirs = [d for d in os.listdir(cache)
                    if "whisper" in d.lower() or "large-v3" in d.lower()]
    if whisper_dirs:
        ok(f"Whisper model found: {whisper_dirs[0]}")
    else:
        warn("Whisper model not found — will download on first run (~3GB)")

    # Check for IndicTrans2
    indic_dirs = [d for d in os.listdir(cache)
                  if "indictrans" in d.lower() or "ai4bharat" in d.lower()]
    if indic_dirs:
        ok(f"IndicTrans2 model found: {indic_dirs[0]}")
    else:
        warn("IndicTrans2 model not found — will download on first run (~800MB)")

    # Check MuseTalk
    musetalk_path = os.path.join(cache, "MuseTalk")
    if os.path.exists(musetalk_path):
        ok(f"MuseTalk found: {musetalk_path}")
    else:
        warn("MuseTalk not found — lip reanimation will be skipped (Phase 2)")


def check_services():
    section("Backend Services")
    import socket

    def port_open(host, port, name):
        try:
            s = socket.create_connection((host, port), timeout=1)
            s.close()
            ok(f"{name} reachable at {host}:{port}")
            return True
        except Exception:
            warn(f"{name} not reachable at {host}:{port} — needed for API server only")
            return False

    port_open("localhost", 5432, "PostgreSQL")
    port_open("localhost", 6379, "Redis")
    port_open("localhost", 9000, "MinIO/S3")
    port_open("localhost", 11434, "Ollama (llama3.1)")


def check_demo_requirements():
    section("Demo Script Requirements")
    # These are the ONLY things needed for run_phase1_demo.py
    ok("ffmpeg + ffprobe: needed ✓")
    ok("faster-whisper: downloads on first run")
    ok("IndicTrans2: downloads on first run")
    ok("TTS (XTTS-v2 fallback): downloads on first run")
    ok("demucs: downloads model on first run")
    print()
    print("  NOTE: First run will download ~5GB of models.")
    print("  Estimated download time on good connection: 15-30 min")
    print("  After that, every run is fast.")


def main():
    print("\n\033[1mNivima Environment Check\033[0m")
    print("Run this before starting the pipeline.\n")

    check_python()
    check_ffmpeg()
    check_gpu()
    check_packages()
    check_tts_models()
    check_model_files()
    check_services()
    check_demo_requirements()

    print(f"\n\033[1mDone.\033[0m Ready to run:\n")
    print("  python scripts/run_phase1_demo.py \\")
    print("    --video test_hindi.mp4 \\")
    print("    --source hi \\")
    print("    --targets te \\")
    print("    --output ./output/\n")


if __name__ == "__main__":
    main()
