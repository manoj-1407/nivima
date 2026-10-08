#!/usr/bin/env python3
"""
Nivima Model Pre-downloader — cross-platform (Windows & Linux).
Downloads all required weights ahead of time so the pipeline never pauses mid-execution.

Usage:
    python scripts/download_models.py
"""

import os
import sys

MODEL_DIR = os.getenv("MODEL_CACHE_DIR", "./models")
os.makedirs(MODEL_DIR, exist_ok=True)


def log(step: int, total: int, msg: str):
    print(f"\n[{step}/{total}] {msg}...")


def main():
    print("=" * 60)
    print("  Nivima Model Downloader (Cache Dir: {})".format(MODEL_DIR))
    print("=" * 60)

    # 1. Faster-Whisper
    log(1, 5, "Downloading Faster-Whisper large-v3")
    try:
        from faster_whisper import WhisperModel
        w_dir = os.path.join(MODEL_DIR, "whisper")
        WhisperModel("large-v3", device="cpu", compute_type="int8", download_root=w_dir)
        print("  ✓ Whisper large-v3 cached successfully")
    except Exception as e:
        print(f"  ⚠ Whisper download error: {e}")

    # 2. IndicTrans2
    log(2, 5, "Downloading IndicTrans2 (200M distilled)")
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        name = "ai4bharat/indictrans2-indic-indic-dist-200M"
        t_dir = os.path.join(MODEL_DIR, "indictrans2")
        AutoTokenizer.from_pretrained(name, trust_remote_code=True, cache_dir=t_dir)
        AutoModelForSeq2SeqLM.from_pretrained(name, trust_remote_code=True, cache_dir=t_dir)
        print("  ✓ IndicTrans2 cached successfully")
    except Exception as e:
        print(f"  ⚠ IndicTrans2 download error: {e}")

    # 3. XTTS-v2
    log(3, 5, "Downloading Coqui XTTS-v2")
    try:
        from TTS.api import TTS
        TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("  ✓ XTTS-v2 cached successfully")
    except Exception as e:
        print(f"  ⚠ XTTS-v2 download error: {e}")

    # 4. IndicTTS per-language VITS
    log(4, 5, "Downloading IndicTTS per-language models")
    langs = ["hi", "bn", "mr", "ta", "te", "kn", "ml"]
    for lang in langs:
        try:
            from TTS.api import TTS
            TTS(f"tts_models/{lang}/cv/vits")
            print(f"  ✓ IndicTTS {lang}: ready")
        except Exception as e:
            print(f"  ⚠ IndicTTS {lang}: not directly available in standard repo ({e}) — XTTS-v2 will handle fallback")

    # 5. Demucs
    log(5, 5, "Downloading Demucs vocal separation models")
    try:
        import demucs.pretrained
        demucs.pretrained.get_model("htdemucs")
        print("  ✓ Demucs htdemucs ready")
    except Exception as e:
        print(f"  ⚠ Demucs download error: {e}")

    print("\n" + "=" * 60)
    print("  Pre-download check complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
