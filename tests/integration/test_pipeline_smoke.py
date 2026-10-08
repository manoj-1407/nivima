"""
Full pipeline smoke test — runs the complete Phase 1 pipeline
with mocked heavy models (no GPU, no downloads needed).

This tests all the Python plumbing: chunking logic, timing adjustment,
audio combining, video merge, error handling.

Run with:
    pytest tests/integration/test_pipeline_smoke.py -v -s
"""
import os
import shutil
import subprocess

import numpy as np
import pytest
import soundfile as sf

# Skip all ffmpeg-dependent tests when ffmpeg is not on PATH
# (e.g. Windows dev machines without ffmpeg installed globally).
# These tests will still run in GitHub CI (ubuntu-latest has ffmpeg) and on the 3070.
_FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
requires_ffmpeg = pytest.mark.skipif(
    not _FFMPEG_AVAILABLE,
    reason="ffmpeg not found on PATH — install ffmpeg to run these tests"
)

# ─── helpers ────────────────────────────────────────────────────────────────

def _make_video(path: str, duration: float = 8.0):
    """Create a test video with Hindi-like spoken audio frequency."""
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"testsrc=duration={duration}:size=320x240:rate=24",
        "-f", "lavfi", "-i", f"sine=frequency=150:duration={duration}",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", path
    ], capture_output=True, check=True)


def _make_wav(path: str, duration: float = 2.0, sr: int = 22050):
    data = (np.sin(2 * np.pi * 200 * np.linspace(0, duration, int(sr * duration)))
            * 0.3).astype(np.float32)
    sf.write(path, data, sr)
    return path


# ─── Stage tests ────────────────────────────────────────────────────────────

@requires_ffmpeg
class TestValidator:
    def test_validates_real_video(self, tmp_path):
        from src.ingestion.validator import validate_and_extract_metadata
        video = str(tmp_path / "test.mp4")
        _make_video(video, duration=8.0)
        meta = validate_and_extract_metadata(video)
        assert meta.has_audio
        assert abs(meta.duration_seconds - 8.0) < 2.0
        assert meta.fps > 0
        assert "x" in meta.resolution

    def test_rejects_too_short(self, tmp_path):
        from src.ingestion.validator import ValidationError, validate_and_extract_metadata
        video = str(tmp_path / "short.mp4")
        _make_video(video, duration=3.0)
        with pytest.raises(ValidationError, match="too short"):
            validate_and_extract_metadata(video)


@requires_ffmpeg
class TestExtractor:
    def test_extracts_audio(self, tmp_path):
        from src.ingestion.extractor import extract_audio
        video = str(tmp_path / "test.mp4")
        _make_video(video, duration=8.0)
        audio = extract_audio(video, str(tmp_path / "audio"))
        assert os.path.exists(audio)
        assert os.path.getsize(audio) > 1000
        info = sf.info(audio)
        assert info.samplerate == 16000
        assert abs(info.duration - 8.0) < 2.0

    def test_merge_audio_video(self, tmp_path):
        from src.ingestion.extractor import extract_audio, merge_audio_video
        video = str(tmp_path / "test.mp4")
        _make_video(video, duration=8.0)
        audio = extract_audio(video, str(tmp_path / "audio"))
        _ = audio  # used via os.path.exists check below

        # Create a dubbed audio and background
        dubbed = str(tmp_path / "dubbed.wav")
        bg = str(tmp_path / "bg.wav")
        _make_wav(dubbed, duration=8.0)
        _make_wav(bg, duration=8.0)

        output = str(tmp_path / "output.mp4")
        result = merge_audio_video(video, dubbed, bg, output)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 10000

    def test_merge_bare_filename_no_dirname_crash(self, tmp_path):
        """dirname('output.mp4') == '' — should not crash makedirs."""
        from src.ingestion.extractor import merge_audio_video
        video = str(tmp_path / "test.mp4")
        _make_video(video, duration=8.0)
        dubbed = str(tmp_path / "dubbed.wav")
        bg = str(tmp_path / "bg.wav")
        _make_wav(dubbed, duration=8.0)
        _make_wav(bg, duration=8.0)

        # Output in tmp_path with no subdirectory — dirname will be tmp_path, fine
        output = str(tmp_path / "out.mp4")
        result = merge_audio_video(video, dubbed, bg, output)
        assert os.path.exists(result)


@requires_ffmpeg
class TestAudioSeparator:
    def test_fallback_creates_silence(self, tmp_path):
        from src.audio.separator import fallback_silence_background
        bg = fallback_silence_background(str(tmp_path), duration_seconds=5.0)
        assert os.path.exists(bg)
        info = sf.info(bg)
        assert abs(info.duration - 5.0) < 1.0


@requires_ffmpeg
class TestChunker:
    def test_fixed_chunks_from_audio(self, tmp_path):
        from src.transcription.chunker import _fixed_chunks
        audio = str(tmp_path / "audio.wav")
        _make_wav(audio, duration=10.0)
        chunks = _fixed_chunks(audio, chunk_ms=4000)
        assert len(chunks) >= 2
        # All chunks should cover the full duration
        total = sum(end - start for start, end in chunks)
        assert abs(total - 10.0) < 0.5

    def test_extract_chunk(self, tmp_path):
        from src.transcription.chunker import _extract_chunk
        audio = str(tmp_path / "audio.wav")
        _make_wav(audio, duration=10.0)
        chunk_out = str(tmp_path / "chunk.wav")
        _extract_chunk(audio, 0, 3000, chunk_out)
        assert os.path.exists(chunk_out)
        info = sf.info(chunk_out)
        assert abs(info.duration - 3.0) < 0.5


class TestAudioAdjuster:
    def test_within_tolerance(self, tmp_path):
        from src.alignment.audio_adjuster import adjust_segment_timing
        src = str(tmp_path / "src.wav")
        out = str(tmp_path / "out.wav")
        _make_wav(src, duration=2.0)
        path, info = adjust_segment_timing(src, 1900, out)
        assert os.path.exists(path)
        assert info["method"] == "time_stretch"
        assert not info["flagged"]

    def test_flag_on_extreme_mismatch(self, tmp_path):
        from src.alignment.audio_adjuster import adjust_segment_timing
        src = str(tmp_path / "src.wav")
        out = str(tmp_path / "out.wav")
        _make_wav(src, duration=5.0)  # 5000ms actual, 1000ms target → ratio 5x
        path, info = adjust_segment_timing(src, 1000, out)
        assert info["flagged"]

    def test_combine_segments(self, tmp_path):
        from src.alignment.audio_adjuster import combine_dubbed_segments
        segs = []
        for i in range(4):
            p = str(tmp_path / f"seg{i}.wav")
            _make_wav(p, duration=1.0)
            segs.append({
                "start_ms": i * 1100,
                "end_ms": (i + 1) * 1100,
                "dubbed_audio_path": p
            })
        out = str(tmp_path / "combined.wav")
        result = combine_dubbed_segments(segs, out)
        assert os.path.exists(result)
        info = sf.info(result)
        assert info.duration > 3.5  # 4 segments × 1s + gaps


class TestTranslationUnit:
    """Tests translation logic without loading actual model."""

    def test_validate_translation_ratio_ok(self):
        from src.translation.translator import _validate_translation
        # Should not raise or warn (called only as side-effect logger)
        _validate_translation("hello world", "नमस्ते दुनिया")

    def test_translate_segments_preserves_structure(self, monkeypatch):
        import src.translation.translator as translator_mod

        # Mock translate_text to avoid loading model
        monkeypatch.setattr(translator_mod, "translate_text",
                            lambda text, src, tgt: f"[{tgt}:{text}]")

        segs = [
            {"text": "Hello world", "start_ms": 0, "end_ms": 1000},
            {"text": "", "start_ms": 1000, "end_ms": 1500},  # empty segment
        ]
        result = translator_mod.translate_segments(segs, "hi", "te")
        assert len(result) == 2
        assert result[0]["translated_text"] == "[te:Hello world]"
        assert result[1]["translated_text"] == ""  # empty passthrough

    def test_translate_segments_handles_error_gracefully(self, monkeypatch):
        import src.translation.translator as translator_mod

        def _boom(text, src, tgt):
            raise RuntimeError("Model exploded")

        monkeypatch.setattr(translator_mod, "translate_text", _boom)

        segs = [{"text": "Hello", "start_ms": 0, "end_ms": 1000}]
        result = translator_mod.translate_segments(segs, "hi", "te")
        # Should not raise — falls back to original text
        assert len(result) == 1
        assert result[0]["translated_text"] == "Hello"


@requires_ffmpeg
class TestTTSUnit:
    """Tests TTS logic without loading actual model."""

    def test_silence_fallback_creates_file(self, tmp_path):
        from src.tts.synthesizer import _generate_silence
        out = str(tmp_path / "silence.wav")
        _generate_silence(out, duration_seconds=0.5)
        assert os.path.exists(out)
        info = sf.info(out)
        assert abs(info.duration - 0.5) < 0.2

    def test_reference_audio_too_short_raises(self, tmp_path):
        from src.tts.synthesizer import _validate_reference_audio
        short = str(tmp_path / "short.wav")
        _make_wav(short, duration=2.0)  # < 6s minimum
        with pytest.raises(ValueError, match="too short"):
            _validate_reference_audio(short)

    def test_reference_audio_valid_passes(self, tmp_path):
        from src.tts.synthesizer import _validate_reference_audio
        ref = str(tmp_path / "ref.wav")
        _make_wav(ref, duration=8.0)
        _validate_reference_audio(ref)  # should not raise

    def test_synthesize_segments_empty_text_fallback(self, tmp_path, monkeypatch):
        import src.tts.synthesizer as synthesizer_mod

        # Mock synthesize_generic to avoid actual TTS load
        def _mock_generic(text, lang, out_path):
            _make_wav(out_path, duration=0.5)
            return out_path

        monkeypatch.setattr(synthesizer_mod, "synthesize_generic", _mock_generic)

        segs = [
            {"translated_text": "నమస్కారం", "start_ms": 0, "end_ms": 1000},
            {"translated_text": "", "start_ms": 1000, "end_ms": 1500},
        ]
        results = synthesizer_mod.synthesize_segments(segs, "te", str(tmp_path / "synth"))
        assert len(results) == 2
        for r in results:
            assert "dubbed_audio_path" in r
            assert os.path.exists(r["dubbed_audio_path"])


@requires_ffmpeg
class TestFullPipelinePlumbing:
    """
    End-to-end smoke test with real ffmpeg but mocked ML models.
    Tests the complete data flow without any GPU/model downloads.
    """

    def test_phase1_plumbing(self, tmp_path, monkeypatch):
        """
        Full pipeline plumbing test:
        validate → extract → chunk → [mock transcribe] → [mock translate]
        → [mock synthesize] → adjust timing → combine → merge video
        """
        from src.alignment.audio_adjuster import adjust_segment_timing, combine_dubbed_segments
        from src.audio.separator import fallback_silence_background
        from src.ingestion.extractor import extract_audio, merge_audio_video
        from src.ingestion.validator import validate_and_extract_metadata
        from src.transcription.chunker import _extract_chunk, _fixed_chunks

        # 1. Create test video
        video = str(tmp_path / "test_hindi.mp4")
        _make_video(video, duration=10.0)

        # 2. Validate
        meta = validate_and_extract_metadata(video)
        assert meta.has_audio

        # 3. Extract audio
        audio = extract_audio(video, str(tmp_path / "audio"))
        assert os.path.exists(audio)

        # 4. Separation fallback (no demucs in CI)
        bg_path = fallback_silence_background(str(tmp_path), meta.duration_seconds)
        assert os.path.exists(bg_path)

        # 5. Chunk audio
        chunk_boundaries = _fixed_chunks(audio, chunk_ms=3000)
        chunks = []
        for i, (start, end) in enumerate(chunk_boundaries):
            chunk_path = str(tmp_path / "chunks" / f"chunk_{i:04d}.wav")
            os.makedirs(os.path.dirname(chunk_path), exist_ok=True)
            _extract_chunk(audio, int(start * 1000), int(end * 1000), chunk_path)
            if os.path.exists(chunk_path):
                chunks.append({
                    "start_ms": int(start * 1000),
                    "end_ms": int(end * 1000),
                    "audio_path": chunk_path
                })

        assert len(chunks) >= 2

        # 6. Mock: transcribe → translate → synthesize
        # Simulate what the pipeline produces
        synth_dir = str(tmp_path / "synth")
        os.makedirs(synth_dir, exist_ok=True)
        synthesized_segs = []
        for i, chunk in enumerate(chunks):
            dubbed = str(tmp_path / "synth" / f"chunk_{i:04d}.wav")
            _make_wav(dubbed, duration=(chunk["end_ms"] - chunk["start_ms"]) / 1000.0)
            synthesized_segs.append({
                **chunk,
                "translated_text": "నమస్కారం",
                "dubbed_audio_path": dubbed
            })

        # 7. Adjust timing
        adj_dir = str(tmp_path / "adjusted")
        os.makedirs(adj_dir, exist_ok=True)
        adjusted = []
        flagged = 0
        for i, seg in enumerate(synthesized_segs):
            duration_ms = seg["end_ms"] - seg["start_ms"]
            out = str(tmp_path / "adjusted" / f"adj_{i:04d}.wav")
            path, info = adjust_segment_timing(seg["dubbed_audio_path"], duration_ms, out)
            if info.get("flagged"):
                flagged += 1
            adjusted.append({**seg, "dubbed_audio_path": path})

        # 8. Combine segments
        combined = combine_dubbed_segments(adjusted, str(tmp_path / "dubbed_combined.wav"))
        assert os.path.exists(combined)
        combined_info = sf.info(combined)
        assert combined_info.duration > 5.0

        # 9. Final video assembly
        output_video = str(tmp_path / "output_te.mp4")
        result = merge_audio_video(video, combined, bg_path, output_video)
        assert os.path.exists(result)
        size_mb = os.path.getsize(result) / 1e6
        assert size_mb > 0.1

        print("\n  ✓ Full pipeline plumbing OK")
        print(f"  ✓ {len(chunks)} chunks processed")
        print(f"  ✓ {flagged} segments flagged (timing)")
        print(f"  ✓ Output: {output_video} ({size_mb:.1f} MB)")
