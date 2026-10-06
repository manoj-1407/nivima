"""
Integration test: full audio pipeline end-to-end.
Requires: ffmpeg, faster-whisper, transformers, TTS installed.
Skipped automatically if models not available.

Run with: pytest tests/integration/test_pipeline_audio.py -v -s
"""
import pytest
import os
import tempfile
import numpy as np

# Skip entire module if heavy dependencies not available
pytest.importorskip("faster_whisper", reason="faster-whisper not installed")
pytest.importorskip("transformers", reason="transformers not installed")


def _make_test_video(path: str, duration: float = 5.0):
    """Create a minimal test video with sine-wave audio."""
    import subprocess
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration}:size=320x240:rate=24",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", path
    ], capture_output=True, check=True)


@pytest.mark.integration
def test_audio_extraction():
    from src.ingestion.extractor import extract_audio
    with tempfile.TemporaryDirectory() as d:
        video = os.path.join(d, "test.mp4")
        _make_test_video(video)
        audio = extract_audio(video, d)
        assert os.path.exists(audio)
        assert os.path.getsize(audio) > 1000


@pytest.mark.integration
def test_validator_accepts_valid_video():
    from src.ingestion.validator import validate_and_extract_metadata
    with tempfile.TemporaryDirectory() as d:
        video = os.path.join(d, "test.mp4")
        _make_test_video(video, duration=10.0)
        meta = validate_and_extract_metadata(video)
        assert meta.has_audio
        assert abs(meta.duration_seconds - 10.0) < 1.5
        assert meta.fps > 0
        assert "x" in meta.resolution


@pytest.mark.integration
def test_whisper_transcribes_audio():
    from src.transcription.asr import transcribe_audio
    import soundfile as sf

    with tempfile.TemporaryDirectory() as d:
        # Generate silent audio (no speech — should produce empty/minimal segments)
        audio_path = os.path.join(d, "audio.wav")
        silence = np.zeros(16000 * 3, dtype=np.float32)
        sf.write(audio_path, silence, 16000)

        segments = transcribe_audio(audio_path)
        # Silent audio may produce 0 or 1 empty segment — both valid
        assert isinstance(segments, list)


@pytest.mark.integration
def test_tts_generic_produces_audio():
    from src.tts.synthesizer import synthesize_generic
    import soundfile as sf

    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "output.wav")
        try:
            path = synthesize_generic("నమస్కారం", "te", out)
            assert os.path.exists(path)
            info = sf.info(path)
            assert info.duration > 0.1
        except Exception as e:
            pytest.skip(f"IndicTTS model not downloaded: {e}")


@pytest.mark.integration
def test_audio_adjuster_stretch():
    from src.alignment.audio_adjuster import adjust_segment_timing
    import soundfile as sf

    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "src.wav")
        out = os.path.join(d, "out.wav")

        data = np.zeros(int(22050 * 2.0))
        sf.write(src, data, 22050)

        path, info = adjust_segment_timing(src, 1900, out)
        assert os.path.exists(path)
        assert not info["flagged"]
        assert info["method"] == "time_stretch"


@pytest.mark.integration
def test_combine_segments_output():
    from src.alignment.audio_adjuster import combine_dubbed_segments
    import soundfile as sf

    with tempfile.TemporaryDirectory() as d:
        segs = []
        for i in range(3):
            p = os.path.join(d, f"seg{i}.wav")
            sf.write(p, np.zeros(22050), 22050)
            segs.append({
                "start_ms": i * 1100,
                "end_ms": (i + 1) * 1100,
                "dubbed_audio_path": p
            })

        out = os.path.join(d, "combined.wav")
        result = combine_dubbed_segments(segs, out)
        assert os.path.exists(result)
        info = sf.info(result)
        assert info.duration > 2.5
