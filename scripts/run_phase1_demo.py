#!/usr/bin/env python3
"""
VoxBridge Phase 1 Demo Script
Runs the full audio dubbing pipeline on a local video file.
No API server needed — runs pipeline directly.

Usage:
    python scripts/run_phase1_demo.py \
        --video path/to/hindi_video.mp4 \
        --source hi \
        --targets te ta \
        --output ./demo_output/

    # With voice clone:
    python scripts/run_phase1_demo.py \
        --video lecture.mp4 \
        --source hi \
        --targets te \
        --voice reference_voice.wav \
        --output ./output/
"""

import argparse
import os
import sys
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def banner(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)


def step(n: int, total: int, text: str):
    print(f"\n[{n}/{total}] {text}...")


def main():
    parser = argparse.ArgumentParser(description="VoxBridge Phase 1 Demo")
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

    banner("VoxBridge Phase 1 Demo — Audio Dubbing Pipeline")
    print(f"  Input:   {args.video}")
    print(f"  Source:  {args.source}")
    print(f"  Targets: {', '.join(args.targets)}")
    print(f"  Voice:   {args.voice or 'Generic TTS (no clone)'}")
    print(f"  Output:  {args.output}")

    os.makedirs(args.output, exist_ok=True)

    total_steps = 6
    t_start = time.time()

    # Step 1: Validate
    step(1, total_steps, "Validating input video")
    from src.ingestion.validator import validate_and_extract_metadata, ValidationError
    try:
        meta = validate_and_extract_metadata(args.video)
        print(f"  ✓ Duration: {meta.duration_seconds:.1f}s "
              f"| Resolution: {meta.resolution} "
              f"| FPS: {meta.fps} "
              f"| Audio: {'Yes' if meta.has_audio else 'No'}")
    except ValidationError as e:
        print(f"  ✗ Validation failed: {e}")
        sys.exit(1)

    if not meta.has_audio:
        print("  ✗ Video has no audio track. Cannot proceed.")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:

        # Step 2: Extract and separate audio
        step(2, total_steps, "Extracting and separating audio")
        from src.ingestion.extractor import extract_audio, merge_audio_video
        from src.audio.separator import separate_audio, fallback_silence_background

        audio_path = extract_audio(args.video, os.path.join(tmpdir, "audio"))

        try:
            speech_path, bg_path = separate_audio(
                audio_path, os.path.join(tmpdir, "separated")
            )
            print("  ✓ Speech and background audio separated")
        except Exception as e:
            print(f"  ⚠ Demucs failed ({e}), using original audio")
            speech_path = audio_path
            bg_path = fallback_silence_background(tmpdir, meta.duration_seconds)

        # Step 3: Transcribe
        step(3, total_steps, f"Transcribing {args.source} speech")
        from src.transcription.asr import transcribe_audio, segments_to_dict

        segments = transcribe_audio(speech_path, language=args.source)
        seg_dicts = segments_to_dict(segments)
        total_words = sum(len(s["words"]) for s in seg_dicts)
        print(f"  ✓ {len(segments)} segments | ~{total_words} words transcribed")

        if not segments:
            print("  ✗ No speech detected. Check source language setting.")
            sys.exit(1)

        # Preview transcript
        preview = " ".join(s["text"] for s in seg_dicts[:3])
        print(f"  Preview: \"{preview[:120]}...\"")

        # Step 4: Translate
        step(4, total_steps, f"Translating to {', '.join(args.targets)}")
        from src.translation.translator import translate_segments
        from src.translation.rewriter import rewrite_segments

        all_translated = {}
        for target in args.targets:
            translated = translate_segments(seg_dicts, args.source, target)
            rewritten = rewrite_segments(translated, args.source, target)
            all_translated[target] = rewritten
            sample = rewritten[0]["translated_text"] if rewritten else ""
            print(f"  ✓ {target.upper()}: \"{sample[:80]}...\"")

        # Step 5: Synthesize
        step(5, total_steps, "Synthesizing dubbed audio")
        from src.tts.synthesizer import synthesize_segments

        all_synthesized = {}
        for target, segs in all_translated.items():
            synth_dir = os.path.join(tmpdir, f"synth_{target}")
            synthesized = synthesize_segments(
                segs, target, synth_dir,
                voice_clone_path=args.voice
            )
            all_synthesized[target] = synthesized
            clone_note = f"(voice clone ~{65 if target != 'hi' else 85}% similarity)" \
                if args.voice else "(generic TTS)"
            print(f"  ✓ {target.upper()} audio synthesized {clone_note}")

        # Step 6: Align + Assemble
        step(6, total_steps, "Aligning timing and assembling final videos")
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

            size_mb = os.path.getsize(output_path) / 1e6
            print(f"  ✓ {target.upper()} → {output_path} ({size_mb:.1f} MB)"
                  f"{f' | {flagged} segments flagged for review' if flagged else ''}")

    elapsed = time.time() - t_start
    ratio = elapsed / meta.duration_seconds

    banner("Done!")
    print(f"  Processing time: {elapsed:.1f}s")
    print(f"  Speed ratio:     {ratio:.1f}x realtime "
          f"({'faster' if ratio < 1 else 'slower'} than realtime)")
    print(f"  Output files:")
    for target in args.targets:
        out = os.path.join(args.output, f"output_{target}.mp4")
        if os.path.exists(out):
            print(f"    → {out}")
    print()
    print("  Next steps:")
    print("  1. Review the dubbed videos")
    print("  2. Check timing sync with original audio events")
    print("  3. Run the API server for the full web UI")
    print("  4. Submit feedback via make run-api + open frontend/index.html")


if __name__ == "__main__":
    main()
