from unittest.mock import MagicMock, patch

import pytest

from src.translation.translator import _validate_translation, translate_segments, translate_text


def test_unsupported_source_language():
    with pytest.raises(ValueError, match="Unsupported language pair"):
        translate_text("hello", "xx", "te")


def test_unsupported_target_language():
    with pytest.raises(ValueError, match="Unsupported language pair"):
        translate_text("नमस्कार", "hi", "xx")


def test_empty_text_returns_empty():
    with patch("src.translation.translator._load"):
        with patch("src.translation.translator._model"):
            with patch("src.translation.translator._tokenizer") as mock_tok:
                mock_tok.return_value = MagicMock()
                result = translate_text("", "hi", "te")
                assert result == ""


def test_validate_translation_length_ok():
    _validate_translation("hello world test sentence", "నమస్కారం ప్రపంచం పరీక్ష")


def test_validate_translation_too_short_warns(caplog):
    _validate_translation("hello world this is a very long source sentence with many words", "hi")


def test_translate_segments_preserves_metadata():
    segments = [
        {"text": "नमस्कार", "start_ms": 0, "end_ms": 1000},
        {"text": "आज हम पढ़ेंगे", "start_ms": 1000, "end_ms": 3000}
    ]

    with patch("src.translation.translator.translate_text") as mock_translate:
        mock_translate.side_effect = ["నమస్కారం", "ఈరోజు మనం చదువుతాం"]
        result = translate_segments(segments, "hi", "te")

    assert len(result) == 2
    assert result[0]["start_ms"] == 0
    assert result[0]["end_ms"] == 1000
    assert result[0]["translated_text"] == "నమస్కారం"
    assert result[0]["target_language"] == "te"
    assert result[1]["translated_text"] == "ఈరోజు మనం చదువుతాం"
