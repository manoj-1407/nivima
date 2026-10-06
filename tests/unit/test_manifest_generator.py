import pytest
from src.player.manifest_generator import generate_manifest, save_manifest, load_manifest
import tempfile
import os


PHONEMES = [
    {"phoneme": "n", "start_ms": 0, "end_ms": 120, "confidence": 0.9, "speaker_id": "S1"},
    {"phoneme": "aa", "start_ms": 120, "end_ms": 350, "confidence": 0.85, "speaker_id": "S1"},
    {"phoneme": "m", "start_ms": 350, "end_ms": 500, "confidence": 0.88, "speaker_id": "S1"},
    {"phoneme": "sil", "start_ms": 500, "end_ms": 700, "confidence": 1.0, "speaker_id": "S1"},
]

DECISIONS = [
    {"start_ms": 0, "end_ms": 2000, "decision": "FRONTAL_CLEAR"},
    {"start_ms": 2000, "end_ms": 4000, "decision": "PROFILE"},
]


def test_manifest_has_required_fields():
    m = generate_manifest(
        job_id="test-job",
        target_language="te",
        base_video_url="https://cdn.example.com/video.mp4",
        dubbed_audio_url="https://cdn.example.com/audio.aac",
        phoneme_timestamps=PHONEMES,
        scene_decisions=DECISIONS,
        speaker_meshes={"S1": "https://cdn.example.com/mesh.bin"},
        fps=24.0,
        total_frames=576
    )
    assert m["version"] == "1.0"
    assert m["job_id"] == "test-job"
    assert m["target_language"] == "te"
    assert "segments" in m
    assert "skipped_ranges" in m
    assert "stats" in m


def test_segments_count_matches_phonemes():
    m = generate_manifest(
        job_id="j1", target_language="te",
        base_video_url="u1", dubbed_audio_url="u2",
        phoneme_timestamps=PHONEMES,
        scene_decisions=[], speaker_meshes={}, fps=25.0, total_frames=100
    )
    assert len(m["segments"]) == len(PHONEMES)


def test_skipped_ranges_excludes_frontal():
    m = generate_manifest(
        job_id="j2", target_language="te",
        base_video_url="u1", dubbed_audio_url="u2",
        phoneme_timestamps=[],
        scene_decisions=DECISIONS,
        speaker_meshes={}, fps=25.0, total_frames=100
    )
    reasons = [r["reason"] for r in m["skipped_ranges"]]
    assert "profile" in reasons
    assert "frontal_clear" not in reasons


def test_segment_has_blend_weights():
    m = generate_manifest(
        job_id="j3", target_language="te",
        base_video_url="u1", dubbed_audio_url="u2",
        phoneme_timestamps=PHONEMES[:1],
        scene_decisions=[], speaker_meshes={}, fps=25.0, total_frames=100
    )
    seg = m["segments"][0]
    assert "blend_weights" in seg
    assert "jaw_open" in seg["blend_weights"]
    assert "viseme" in seg


def test_save_and_load_manifest():
    m = generate_manifest(
        job_id="j4", target_language="hi",
        base_video_url="u1", dubbed_audio_url="u2",
        phoneme_timestamps=PHONEMES,
        scene_decisions=DECISIONS,
        speaker_meshes={}, fps=24.0, total_frames=240
    )
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "manifest.json")
        save_manifest(m, path)
        loaded = load_manifest(path)
        assert loaded["job_id"] == "j4"
        assert len(loaded["segments"]) == len(PHONEMES)


def test_stats_coverage_pct():
    m = generate_manifest(
        job_id="j5", target_language="ta",
        base_video_url="u1", dubbed_audio_url="u2",
        phoneme_timestamps=[],
        scene_decisions=DECISIONS,
        speaker_meshes={}, fps=25.0, total_frames=100
    )
    # 1 skipped out of 2 = 50% coverage
    assert m["stats"]["coverage_pct"] == 50.0
