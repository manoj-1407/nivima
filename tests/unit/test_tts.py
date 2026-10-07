import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.tts.synthesizer import (
    XTTS_NATIVE,
    _validate_reference_audio,
    synthesize_cloned,
    synthesize_generic,
)


def test_unsupported_generic_language():
    with pytest.raises(ValueError, match="No generic TTS model"):
        synthesize_generic("hello", "xx", "/tmp/out.wav")


def test_reference_audio_not_found():
    with pytest.raises(FileNotFoundError):
        _validate_reference_audio("/nonexistent/audio.wav")


def test_reference_audio_too_short():
    import numpy as np
    import soundfile as sf

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        data = np.zeros(int(22050 * 2))
        sf.write(f.name, data, 22050)
        tmp = f.name

    try:
        with pytest.raises(ValueError, match="too short"):
            _validate_reference_audio(tmp)
    finally:
        os.unlink(tmp)


def test_hindi_is_native():
    assert "hi" in XTTS_NATIVE


def test_telugu_is_not_native():
    assert "te" not in XTTS_NATIVE


def test_cloned_quality_score_hindi():
    with patch("src.tts.synthesizer._get_tts") as mock_tts:
        mock_tts.return_value = MagicMock()
        mock_tts.return_value.tts_to_file = MagicMock()

        import numpy as np
        import soundfile as sf
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as ref:
            sf.write(ref.name, np.zeros(int(22050 * 8)), 22050)
            ref_path = ref.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out:
            out_path = out.name

        try:
            _, quality = synthesize_cloned("नमस्कार", "hi", ref_path, out_path)
            assert quality == 0.85
        finally:
            os.unlink(ref_path)


def test_cloned_quality_score_telugu():
    with patch("src.tts.synthesizer._get_tts") as mock_tts:
        mock_tts.return_value = MagicMock()
        mock_tts.return_value.tts_to_file = MagicMock()

        import numpy as np
        import soundfile as sf
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as ref:
            sf.write(ref.name, np.zeros(int(22050 * 8)), 22050)
            ref_path = ref.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out:
            out_path = out.name

        try:
            _, quality = synthesize_cloned("నమస్కారం", "te", ref_path, out_path)
            assert quality == 0.65
        finally:
            os.unlink(ref_path)
