import json
import os
import structlog
from src.translation.phoneme_map import get_viseme, get_blend_weights

log = structlog.get_logger()


def generate_manifest(
    job_id: str,
    target_language: str,
    base_video_url: str,
    dubbed_audio_url: str,
    phoneme_timestamps: list[dict],
    scene_decisions: list[dict],
    speaker_meshes: dict[str, str],
    fps: float,
    total_frames: int
) -> dict:
    segments = []

    for entry in phoneme_timestamps:
        phoneme = entry.get("phoneme", "sil")
        ts_ms = entry.get("start_ms", 0)
        end_ms = entry.get("end_ms", ts_ms + 100)
        duration_ms = max(1, end_ms - ts_ms)
        speaker_id = entry.get("speaker_id", "SPEAKER_00")
        confidence = entry.get("confidence", 0.8)

        frame = int((ts_ms / 1000.0) * fps)
        duration_frames = max(1, int((duration_ms / 1000.0) * fps))

        viseme = get_viseme(phoneme)
        weights = get_blend_weights(viseme)

        segments.append({
            "frame": frame,
            "timestamp_ms": ts_ms,
            "speaker_id": speaker_id,
            "viseme": viseme,
            "intensity": round(confidence, 3),
            "duration_frames": duration_frames,
            "blend_weights": weights,
        })

    skipped_ranges = [
        {
            "start_ms": d["start_ms"],
            "end_ms": d["end_ms"],
            "reason": d["decision"].lower()
        }
        for d in scene_decisions
        if d.get("decision") not in ("FRONTAL_CLEAR", "PARTIAL_VISIBLE")
    ]

    manifest = {
        "version": "1.0",
        "job_id": job_id,
        "target_language": target_language,
        "base_video_url": base_video_url,
        "dubbed_audio_url": dubbed_audio_url,
        "fps": fps,
        "total_frames": total_frames,
        "speakers": speaker_meshes,
        "segments": segments,
        "skipped_ranges": skipped_ranges,
        "stats": {
            "total_phonemes": len(segments),
            "skipped_scene_count": len(skipped_ranges),
            "coverage_pct": round(
                100 * (1 - len(skipped_ranges) /
                       max(1, len(scene_decisions))), 1
            )
        }
    }

    log.info("manifest_generated",
             job_id=job_id,
             lang=target_language,
             segments=len(segments),
             skipped=len(skipped_ranges))

    return manifest


def save_manifest(manifest: dict, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    log.info("manifest_saved", path=output_path)
    return output_path


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
