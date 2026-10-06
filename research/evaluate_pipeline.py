#!/usr/bin/env python3
"""
VoxBridge Pipeline Evaluation
Measures WER, BLEU, TTS quality, and lip sync metrics.

Usage:
    python research/evaluate_pipeline.py \
        --test-dir ./data/test_set/ \
        --source hi \
        --target te \
        --output ./research/results/
"""

import argparse
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def evaluate_asr(test_dir: str, source_lang: str) -> dict:
    from src.transcription.asr import transcribe_audio

    references = []
    hypotheses = []

    audio_dir = os.path.join(test_dir, "audio")
    ref_dir = os.path.join(test_dir, "transcripts")

    if not os.path.exists(audio_dir):
        return {"wer": None, "note": "No audio test set found"}

    for fname in os.listdir(audio_dir):
        if not fname.endswith(".wav"):
            continue
        audio_path = os.path.join(audio_dir, fname)
        ref_path = os.path.join(ref_dir, fname.replace(".wav", ".txt"))

        if not os.path.exists(ref_path):
            continue

        with open(ref_path) as f:
            reference = f.read().strip()

        segments = transcribe_audio(audio_path, language=source_lang)
        hypothesis = " ".join(s.text for s in segments)

        references.append(reference)
        hypotheses.append(hypothesis)

    if not references:
        return {"wer": None, "note": "No test pairs found"}

    wer = _compute_wer(references, hypotheses)
    return {
        "wer": round(wer, 4),
        "wer_pct": round(wer * 100, 2),
        "samples": len(references),
        "target": "< 12% WER"
    }


def evaluate_translation(
    test_dir: str,
    source_lang: str,
    target_lang: str
) -> dict:
    try:
        from sacrebleu.metrics import BLEU
    except ImportError:
        return {"bleu": None, "note": "sacrebleu not installed"}

    from src.translation.translator import translate_text

    src_file = os.path.join(test_dir, f"src_{source_lang}.txt")
    ref_file = os.path.join(test_dir, f"ref_{target_lang}.txt")

    if not os.path.exists(src_file) or not os.path.exists(ref_file):
        return {"bleu": None, "note": f"Test files not found: {src_file}"}

    with open(src_file) as f:
        sources = [l.strip() for l in f if l.strip()]
    with open(ref_file) as f:
        references = [l.strip() for l in f if l.strip()]

    hypotheses = []
    for src in sources[:50]:
        hyp = translate_text(src, source_lang, target_lang)
        hypotheses.append(hyp)

    bleu = BLEU()
    result = bleu.corpus_score(hypotheses, [references[:len(hypotheses)]])

    return {
        "bleu": round(float(result.score), 2),
        "samples": len(hypotheses),
        "target": "> 28 BLEU",
        "pass": float(result.score) > 28
    }


def evaluate_lip_sync(
    orig_frames_dir: str,
    output_frames_dir: str,
    audio_path: str
) -> dict:
    from src.qc.scorer import score_chunk, score_to_dict

    if not os.path.exists(orig_frames_dir):
        return {"note": "No frames directory found"}

    score = score_chunk(orig_frames_dir, output_frames_dir, audio_path)
    d = score_to_dict(score)
    d["targets"] = {
        "syncnet": "> 7.0",
        "csim": "> 0.85",
        "psnr": "> 35 dB",
        "temporal": "< 8.0"
    }
    d["pass"] = {
        "syncnet": score.syncnet_score > 7.0,
        "csim": score.csim_score > 0.85,
        "psnr": score.psnr_non_lip > 35.0,
        "temporal": score.temporal_variance < 8.0,
    }
    return d


def _compute_wer(references: list, hypotheses: list) -> float:
    total_errors = 0
    total_words = 0

    for ref, hyp in zip(references, hypotheses):
        ref_words = ref.split()
        hyp_words = hyp.split()

        # Simple WER via edit distance
        r, h = len(ref_words), len(hyp_words)
        dp = list(range(h + 1))
        for i in range(1, r + 1):
            new_dp = [i]
            for j in range(1, h + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    new_dp.append(dp[j-1])
                else:
                    new_dp.append(1 + min(dp[j], new_dp[-1], dp[j-1]))
            dp = new_dp

        total_errors += dp[h]
        total_words += r

    return total_errors / max(total_words, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-dir", default="./data/test_set")
    parser.add_argument("--source", default="hi")
    parser.add_argument("--target", default="te")
    parser.add_argument("--output", default="./research/results")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_lang": args.source,
        "target_lang": args.target,
    }

    print(f"\n=== VoxBridge Pipeline Evaluation ===")
    print(f"Source: {args.source} | Target: {args.target}\n")

    print("[1/3] Evaluating ASR...")
    results["asr"] = evaluate_asr(args.test_dir, args.source)
    print(f"  WER: {results['asr'].get('wer_pct', 'N/A')}%")

    print("[2/3] Evaluating Translation...")
    results["translation"] = evaluate_translation(
        args.test_dir, args.source, args.target
    )
    print(f"  BLEU: {results['translation'].get('bleu', 'N/A')}")

    print("[3/3] Evaluating Lip Sync (if frames available)...")
    orig_dir = os.path.join(args.test_dir, "original_frames")
    out_dir = os.path.join(args.test_dir, "output_frames")
    audio = os.path.join(args.test_dir, "dubbed_audio.wav")
    results["lip_sync"] = evaluate_lip_sync(orig_dir, out_dir, audio)
    print(f"  SyncNet: {results['lip_sync'].get('syncnet_score', 'N/A')}")

    out_path = os.path.join(args.output, f"eval_{args.source}_{args.target}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== Results saved to {out_path} ===")

    # Summary
    print("\n--- Summary ---")
    asr_wer = results["asr"].get("wer_pct")
    bleu = results["translation"].get("bleu")
    sync = results["lip_sync"].get("syncnet_score")

    print(f"ASR WER:    {f'{asr_wer:.1f}%' if asr_wer else 'N/A'} (target: < 12%)")
    print(f"Trans BLEU: {f'{bleu:.1f}' if bleu else 'N/A'} (target: > 28)")
    print(f"SyncNet:    {f'{sync:.2f}' if sync else 'N/A'} (target: > 7.0)")


if __name__ == "__main__":
    main()
