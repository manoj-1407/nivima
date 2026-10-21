"""Unit tests for Patent Pillar 3: Hardware Playback Buffer-Aware Decoding Controller."""
from src.translation.buffer_aware_decoder import BufferAwareDecodingController


def test_syllable_duration_estimation():
    ctrl = BufferAwareDecodingController(target_language="te", target_video_duration_ms=1000.0)
    # Telugu phrase: "నమస్కారం" -> ~4 syllables -> ~540ms
    dur = ctrl.estimate_token_duration_ms("నమస్కారం")
    assert 300.0 <= dur <= 800.0


def test_temporal_logit_penalty_application():
    # Target video cut is exactly 800 ms
    ctrl = BufferAwareDecodingController(
        target_language="hi",
        target_video_duration_ms=800.0,
        penalty_scale_lambda=2.0,
        tolerance_ms=40.0,
    )

    candidates = ["हाँ", "यह बहुत ही लम्बा वाक्य है जो पूरा नहीं आ सकता"]
    raw_logits = [5.0, 5.0]

    adjusted = ctrl.modulate_logits(
        candidate_tokens=candidates,
        raw_logits=raw_logits,
        accumulated_text="नमस्ते",
    )

    # Short token "हाँ" should have higher logit than the excessively long candidate
    assert adjusted[0] > adjusted[1]
    assert ctrl.penalty_count > 0


def test_buffer_telemetry_convergence():
    ctrl = BufferAwareDecodingController(
        target_language="en",
        target_video_duration_ms=550.0,
        tolerance_ms=40.0,
    )
    # 5 syllables (e, o, o, i, e) * 110ms = 550ms -> exactly converged
    telemetry = ctrl.get_telemetry("hello world friend")
    assert telemetry.is_buffer_converged is True
    assert telemetry.buffer_phase_error_ms <= 40.0

