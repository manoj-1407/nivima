import os
import subprocess
import soundfile as sf
import librosa
import numpy as np
import structlog

log = structlog.get_logger()

MAX_STRETCH_RATIO = 1.15
MIN_STRETCH_RATIO = 0.85
FLAG_THRESHOLD_RATIO = 1.30


def adjust_segment_timing(
    dubbed_audio_path: str,
    target_duration_ms: int,
    output_path: str
) -> tuple[str, dict]:
    """
    Adjusts dubbed audio duration to match target_duration_ms.
    Returns (output_path, adjustment_info)
    adjustment_info: {method, ratio, flagged}
    """
    audio, sr = librosa.load(dubbed_audio_path, sr=None)
    actual_duration_ms = int(len(audio) / sr * 1000)

    if target_duration_ms <= 0:
        import shutil
        shutil.copy(dubbed_audio_path, output_path)
        return output_path, {"method": "passthrough", "ratio": 1.0, "flagged": False}

    ratio = actual_duration_ms / target_duration_ms

    info = {"original_ms": actual_duration_ms, "target_ms": target_duration_ms, "ratio": round(ratio, 3)}

    if MIN_STRETCH_RATIO <= ratio <= MAX_STRETCH_RATIO:
        # Within acceptable range — time stretch
        stretched = librosa.effects.time_stretch(audio, rate=ratio)
        sf.write(output_path, stretched, sr)
        info.update({"method": "time_stretch", "flagged": False})
        log.debug("audio_time_stretched", ratio=ratio, output=output_path)

    elif ratio > FLAG_THRESHOLD_RATIO or ratio < (1 / FLAG_THRESHOLD_RATIO):
        # Too different — flag for human re-recording
        import shutil
        shutil.copy(dubbed_audio_path, output_path)
        info.update({"method": "passthrough", "flagged": True,
                     "flag_reason": f"Duration ratio {ratio:.2f} exceeds threshold"})
        log.warning("audio_timing_flagged", ratio=ratio, target_ms=target_duration_ms)

    else:
        # Borderline — apply max stretch and flag
        stretch_rate = MAX_STRETCH_RATIO if ratio > 1 else (1 / MAX_STRETCH_RATIO)
        stretched = librosa.effects.time_stretch(audio, rate=stretch_rate)
        sf.write(output_path, stretched, sr)
        info.update({"method": "max_stretch_flagged", "flagged": True,
                     "flag_reason": f"Applied max stretch {stretch_rate:.2f}, still outside target"})
        log.warning("audio_max_stretch_applied", ratio=ratio)

    return output_path, info


def combine_dubbed_segments(
    segments: list[dict],
    output_path: str
) -> str:
    """
    Concatenate all dubbed audio segments into one track.
    Inserts silence for gaps between segments.
    """
    from pydub import AudioSegment

    combined = AudioSegment.empty()
    prev_end_ms = 0

    for seg in segments:
        start_ms = seg.get("start_ms", 0)
        dubbed_path = seg.get("dubbed_audio_path", "")

        if not dubbed_path or not os.path.exists(dubbed_path):
            continue

        gap_ms = max(0, start_ms - prev_end_ms)
        if gap_ms > 50:
            silence = AudioSegment.silent(duration=gap_ms)
            combined += silence

        dubbed = AudioSegment.from_wav(dubbed_path)
        combined += dubbed
        prev_end_ms = start_ms + len(dubbed)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.export(output_path, format="wav")
    log.info("segments_combined", total_ms=len(combined), output=output_path)
    return output_path
