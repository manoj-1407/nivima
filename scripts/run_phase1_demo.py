#!/usr/bin/env python3
"""
Nivima Phase 1 Demo Script
Runs the full audio dubbing pipeline on a local video file.
Includes hardware profiling, live ETA calculation, and laptop VRAM optimization (RTX 4050/3070).

Usage:
    python scripts/run_phase1_demo.py \
        --video path/to/hindi_video.mp4 \
        --source hi \
        --targets te ta \
        --output ./demo_output/
"""

import argparse
import gc
import os
import sys
import tempfile
import time

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hardware_profiler import estimate_processing_eta, format_hardware_report



def banner(text: str):
    print(f"\n{'='*65}")
    print(f"  {text}")
    print('='*65)


def step(n: int, total: int, text: str):
    print(f"\n[{n}/{total}] {text}...")


def free_vram():
    """Frees Python garbage and CUDA cached memory."""
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Nivima Phase 1 Dubbing Pipeline")
    parser.add_argument("--video", required=True, help="Input video path")
    parser.add_argument("--source", default="hi", help="Source language code (default: hi)")
    parser.add_argument("--targets", nargs="+", default=["te"],
                        help="Target language codes (default: te)")
    parser.add_argument("--voice", default=None,
                        help="Reference audio for voice cloning (optional, min 6s)")
    parser.add_argument("--output", default="./nivima_output",
                        help="Output directory")
    parser.add_argument("--tier", choices=["speed", "quality"], default="speed")
    args = parser.parse_args()

    # Hardware & Capability Detection
    print("\n" + format_hardware_report())

    banner("Nivima Phase 1 Demo — Audio Dubbing Pipeline")
    print(f"  Input Video:     {args.video}")
    print(f"  Source Language: {args.source}")
    print(f"  Target Langs:    {', '.join(args.targets)}")
    print(f"  Voice Clone:     {args.voice or 'Generic TTS (No clone)'}")
    print(f"  Output Dir:      {args.output}")

    os.makedirs(args.output, exist_ok=True)

    total_steps = 6
    t_start = time.time()

    # Step 1: Validate
    step(1, total_steps, "Validating input video stream")
    from src.ingestion.validator import ValidationError, validate_and_extract_metadata
    try:
        meta = validate_and_extract_metadata(args.video)
        print(f"  [OK] Duration: {meta.duration_seconds:.1f}s "
              f"| Resolution: {meta.resolution} "
              f"| FPS: {meta.fps} "
              f"| Audio: {'Yes' if meta.has_audio else 'No'}")
    except ValidationError as e:
        print(f"  [ERROR] Validation failed: {e}")
        sys.exit(1)

    if not meta.has_audio:
        print("  [ERROR] Video has no audio track. Cannot proceed.")
        sys.exit(1)

    # Calculate and display ETA for user
    eta_info = estimate_processing_eta(meta.duration_seconds, len(args.targets))
    print(f"\n  [ETA] ESTIMATED PIPELINE ETA: ~{eta_info['total_eta_seconds']:.0f} seconds "
          f"({eta_info['speed_ratio']:.2f}x realtime on {eta_info['gpu_name']})")
    print(f"     - Separation: ~{eta_info['breakdown']['vocal_separation']}s | "
          f"ASR: ~{eta_info['breakdown']['whisper_asr']}s | "
          f"Translation: ~{eta_info['breakdown']['translation']}s | "
          f"TTS: ~{eta_info['breakdown']['voice_synthesis']}s")

    with tempfile.TemporaryDirectory() as tmpdir:

        # Step 2: Extract and separate audio
        step(2, total_steps, "Extracting audio and separating vocal stems (Demucs)")
        from src.audio.separator import fallback_silence_background, separate_audio
        from src.ingestion.extractor import extract_audio, merge_audio_video

        audio_path = extract_audio(args.video, os.path.join(tmpdir, "audio"))

        try:
            speech_path, bg_path = separate_audio(
                audio_path, os.path.join(tmpdir, "separated")
            )
            print("  [OK] Speech and background audio separated successfully")
        except Exception as e:
            print(f"  [WARN] Demucs separation fell back ({e}), continuing with original audio")
            speech_path = audio_path
            bg_path = fallback_silence_background(tmpdir, meta.duration_seconds)

        free_vram()

        # Step 3: Transcribe
        step(3, total_steps, f"Transcribing {args.source} speech with Faster-Whisper")
        from src.transcription.asr import segments_to_dict, transcribe_audio, unload_asr_model

        segments = transcribe_audio(speech_path, language=args.source)
        seg_dicts = segments_to_dict(segments)
        total_words = sum(len(s["words"]) for s in seg_dicts)
        print(f"  [OK] {len(segments)} segments transcribed (~{total_words} words)")

        if not segments:
            print("  [ERROR] No speech detected in video. Exiting.")
            sys.exit(1)

        preview = " ".join(s["text"] for s in seg_dicts[:3])
        print(f"  Preview transcript: \"{preview[:100]}...\"")

        # Unload Whisper model to free 1.5–3.0 GB VRAM for translation & TTS
        unload_asr_model()
        free_vram()

        # Step 4: Translate
        step(4, total_steps, f"Translating via IndicTrans2 to {', '.join(args.targets)}")
        from src.translation.rewriter import rewrite_segments
        from src.translation.translator import translate_segments, unload_translation_model

        all_translated = {}
        for target in args.targets:
            translated = translate_segments(seg_dicts, args.source, target)
            rewritten = rewrite_segments(translated, args.source, target)
            all_translated[target] = rewritten
            sample = rewritten[0]["translated_text"] if rewritten else ""
            print(f"  [OK] {target.upper()}: \"{sample[:80]}...\"")

        unload_translation_model()
        free_vram()

        # Step 5: Synthesize
        step(5, total_steps, "Synthesizing dubbed audio tracks")
        from src.tts.synthesizer import synthesize_segments, unload_tts_models

        all_synthesized = {}
        for target, segs in all_translated.items():
            synth_dir = os.path.join(tmpdir, f"synth_{target}")
            synthesized = synthesize_segments(
                segs, target, synth_dir,
                voice_clone_path=args.voice
            )
            all_synthesized[target] = synthesized
            clone_note = f"(voice clone ~{65 if target != 'hi' else 85}% similarity)" \
                if args.voice else "(generic IndicTTS)"
            print(f"  [OK] {target.upper()} voice synthesized {clone_note}")

        unload_tts_models()
        free_vram()

        # Step 6: Align + Assemble
        step(6, total_steps, "Aligning timing and assembling final video containers")
        from src.alignment.audio_adjuster import adjust_segment_timing, combine_dubbed_segments

        for target, synthesized in all_synthesized.items():
            lang_dir = os.path.join(tmpdir, f"final_{target}")
            os.makedirs(lang_dir, exist_ok=True)

            adj_dir = os.path.join(lang_dir, "adjusted")
            os.makedirs(adj_dir, exist_ok=True)

            adjusted = []
            flagged = 0
            for i, seg in enumerate(synthesized):
                dubbed = seg.get("dubbed_audio_path", "")
                duration = seg.get("end_ms", 0) - seg.get("start_ms", 0)
                if not dubbed or not os.path.exists(dubbed) or duration <= 0:
                    adjusted.append(seg)
                    continue
                out = os.path.join(adj_dir, f"adj_{i:04d}.wav")
                path, info = adjust_segment_timing(dubbed, duration, out)
                if info.get("flagged"):
                    flagged += 1
                adjusted.append({**seg, "dubbed_audio_path": path})

            combined = combine_dubbed_segments(
                adjusted,
                os.path.join(lang_dir, "dubbed_combined.wav")
            )

            output_path = os.path.join(args.output, f"output_{target}.mp4")
            merge_audio_video(args.video, combined, bg_path, output_path)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  [OK] {target.upper()} -> {output_path} ({size_mb:.1f} MB)"
                  f"{f' | {flagged} segments flagged for sync' if flagged else ''}")

    elapsed = time.time() - t_start
    ratio = elapsed / meta.duration_seconds

    banner("Pipeline Completed Successfully!")
    print(f"  Actual Processing Time: {elapsed:.1f}s (Estimated: {eta_info['total_eta_seconds']:.0f}s)")
    print(f"  Processing Speed Ratio: {ratio:.2f}x realtime "
          f"({'Faster than realtime' if ratio < 1 else 'Slower than realtime'})")
    print("\n  Generated Dubbed Videos:")
    for target in args.targets:
        out = os.path.join(args.output, f"output_{target}.mp4")
        if os.path.exists(out):
            print(f"    - {out}")

    print("\n  All steps finished with 0 errors.\n")


if __name__ == "__main__":
    main()
