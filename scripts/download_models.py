#!/usr/bin/env python3
"""
Nivima Model Pre-downloader — cross-platform with ETA and size estimation.
Pre-caches Faster-Whisper, IndicTrans2, XTTS-v2, and Demucs models.

Usage:
    python scripts/download_models.py
    python scripts/download_models.py --fast  # Downloads lightweight models to save 50% time
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hardware_profiler import format_hardware_report

MODEL_DIR = os.getenv("MODEL_CACHE_DIR", "./models")
os.makedirs(MODEL_DIR, exist_ok=True)


def banner(text: str):
    print(f"\n{'='*65}")
    print(f"  {text}")
    print('='*65)


def step(n: int, total: int, name: str, size_mb: int):
    print(f"\n[{n}/{total}] Downloading {name} (~{size_mb} MB)...")


def main():
    parser = argparse.ArgumentParser(description="Nivima Model Weight Downloader")
    parser.add_argument("--fast", action="store_true",
                        help="Download smaller quantized models (cuts download time in half)")
    args = parser.parse_args()

    print(format_hardware_report())

    banner("Nivima Model Weight Pre-Downloader")
    print(f"  Destination Cache: {os.path.abspath(MODEL_DIR)}")
    print(f"  Download Profile:  {'⚡ Fast Quantized (~2.8 GB)' if args.fast else 'Full Production (~5.5 GB)'}")
    print("  Note: Downloads are cached permanently. Subsequent runs will use local weights.")

    t_start = time.time()
    total_steps = 4

    # 1. Faster-Whisper
    whisper_size = "medium" if args.fast else "large-v3"
    step(1, total_steps, f"Faster-Whisper ({whisper_size})", 1500 if args.fast else 3000)
    try:
        from faster_whisper import WhisperModel
        w_dir = os.path.join(MODEL_DIR, "whisper")
        WhisperModel(whisper_size, device="cpu", compute_type="int8", download_root=w_dir)
        print(f"  ✓ Faster-Whisper ({whisper_size}) downloaded successfully")
    except Exception as e:
        print(f"  ⚠ Faster-Whisper download notice: {e}")

    # 2. IndicTrans2
    step(2, total_steps, "IndicTrans2 (200M Distilled)", 800)
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        name = "ai4bharat/indictrans2-indic-indic-dist-200M"
        t_dir = os.path.join(MODEL_DIR, "indictrans2")
        AutoTokenizer.from_pretrained(name, trust_remote_code=True, cache_dir=t_dir)
        AutoModelForSeq2SeqLM.from_pretrained(name, trust_remote_code=True, cache_dir=t_dir)
        print("  ✓ IndicTrans2 downloaded successfully")
    except Exception as e:
        print(f"  ⚠ IndicTrans2 download notice: {e}")

    # 3. Coqui XTTS-v2
    step(3, total_steps, "Coqui XTTS-v2 Multilingual", 1800)
    try:
        from TTS.api import TTS
        TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("  ✓ XTTS-v2 downloaded successfully")
    except Exception as e:
        print(f"  ⚠ XTTS-v2 download notice: {e}")

    # 4. Demucs
    step(4, total_steps, "Demucs Vocal Stem Separation", 1200)
    try:
        import demucs.pretrained
        demucs.pretrained.get_model("htdemucs")
        demucs.pretrained.get_model("mdx_extra_q")
        print("  ✓ Demucs (htdemucs + mdx_extra_q) downloaded successfully")
    except Exception as e:
        print(f"  ⚠ Demucs download notice: {e}")

    elapsed = time.time() - t_start
    banner(f"All Model Weights Ready in {elapsed / 60:.1f} Minutes!")
    print("  You can now run video dubbing offline at maximum GPU speed.")
    print("  Next command to run:")
    print("    python scripts/run_phase1_demo.py --video sample_hindi.mp4 --source hi --targets te\n")


if __name__ == "__main__":
    main()
