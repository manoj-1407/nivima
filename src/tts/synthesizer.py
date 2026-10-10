import os

import structlog

from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# Coqui TTS per-language VITS models (Mozilla Common Voice fine-tunes)
# These are the actually available models in the Coqui model zoo as of 2024.
# Telugu (te) does NOT have a stable Coqui VITS model — falls back to XTTS-v2.
INDIC_TTS_MODELS = {
    "hi": "tts_models/hi/cv/vits",
    "bn": "tts_models/bn/cv/vits",
    "mr": "tts_models/mr/cv/vits",
    # ta, kn, ml, te: no reliable Coqui VITS models → use XTTS-v2 fallback
}

# XTTS-v2: voice clone / multilingual model
XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

# Languages XTTS-v2 officially supports natively
XTTS_NATIVE = {"hi", "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh"}

# For Indic languages not in XTTS_NATIVE, use Hindi as the closest approximation
# XTTS-v2 handles cross-lingual voice with Hindi as the phonological proxy
INDIC_XTTS_PROXY = {
    "te": "hi",  # Telugu — Hindi proxy
    "ta": "hi",  # Tamil — Hindi proxy
    "kn": "hi",  # Kannada — Hindi proxy
    "ml": "hi",  # Malayalam — Hindi proxy
    "gu": "hi",  # Gujarati — Hindi proxy
    "or": "hi",  # Odia — Hindi proxy
    "pa": "hi",  # Punjabi — Hindi proxy
    "as": "hi",  # Assamese — Hindi proxy
    "ur": "hi",  # Urdu — Hindi proxy (phonologically close)
}

MIN_REFERENCE_DURATION_SECONDS = 6.0

_tts_cache: dict = {}
_xtts_reference_cache: str | None = None


def _get_tts(model_name: str):
    from TTS.api import TTS
    if model_name not in _tts_cache:
        log.info("loading_tts_model", model=model_name)
        gpu = settings.gpu_available
        _tts_cache[model_name] = TTS(model_name, gpu=gpu)
    return _tts_cache[model_name]


def unload_tts_models():
    """Frees Coqui TTS models from GPU memory."""
    global _tts_cache
    _tts_cache.clear()
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    log.info("tts_models_unloaded")


def _get_or_create_reference_voice(output_dir: str) -> str:
    """
    Create a synthetic reference voice for XTTS-v2 when no real speaker reference exists.
    Uses ffmpeg if available, falls back to numpy+soundfile (no ffmpeg required).
    """
    global _xtts_reference_cache
    if _xtts_reference_cache and os.path.exists(_xtts_reference_cache):
        return _xtts_reference_cache

    import shutil
    ref_path = os.path.join(output_dir, "_synthetic_ref.wav")
    os.makedirs(output_dir, exist_ok=True)

    # Prefer ffmpeg for clean sine wave
    if shutil.which("ffmpeg"):
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "sine=frequency=200:duration=8",
            "-ar", "22050", "-ac", "1",
            ref_path
        ], capture_output=True, check=True)
    else:
        # Pure Python fallback — numpy sine wave written directly with soundfile
        import numpy as np
        import soundfile as sf
        sr = 22050
        t = np.linspace(0, 8.0, int(sr * 8.0), endpoint=False)
        wave = (np.sin(2 * np.pi * 200 * t) * 0.4).astype(np.float32)
        sf.write(ref_path, wave, sr)

    _xtts_reference_cache = ref_path
    log.info("synthetic_reference_voice_created", path=ref_path)
    return ref_path


def synthesize_generic(text: str, language: str, output_path: str) -> str:
    """
    Synthesize text in target language using best available model.
    Priority: (1) Coqui VITS per-lang → (2) XTTS-v2 → (3) silence fallback.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if not text.strip():
        _generate_silence(output_path, duration_seconds=0.5)
        return output_path

    # Tier 1: use per-language Coqui VITS if available for this language
    model_name = INDIC_TTS_MODELS.get(language)
    if model_name:
        try:
            tts = _get_tts(model_name)
            tts.tts_to_file(text=text, file_path=output_path)
            log.debug("tts_generic_done", lang=language, model=model_name)
            return output_path
        except Exception as e:
            log.warning("tts_indic_model_failed",
                        lang=language, error=str(e),
                        fallback="xtts_v2")

    # Tier 2: XTTS-v2 with synthetic reference voice
    try:
        xtts_lang = language if language in XTTS_NATIVE else INDIC_XTTS_PROXY.get(language, "hi")
        ref_dir = os.path.dirname(output_path) or "."
        ref_voice = _get_or_create_reference_voice(ref_dir)
        tts = _get_tts(XTTS_MODEL)
        tts.tts_to_file(
            text=text,
            speaker_wav=ref_voice,
            language=xtts_lang,
            file_path=output_path
        )
        log.debug("tts_xtts_fallback_done", lang=language, xtts_lang=xtts_lang)
        return output_path
    except Exception as e:
        log.error("tts_xtts_failed", lang=language, error=str(e), fallback="silence")

    # Tier 3: silence — never crash the pipeline
    _generate_silence(output_path, duration_seconds=1.0)
    log.warning("tts_using_silence_fallback", lang=language)
    return output_path


def synthesize_cloned(
    text: str,
    language: str,
    reference_audio_path: str,
    output_path: str
) -> tuple[str, float]:
    """
    Returns (output_path, quality_score 0-1)
    Quality degrades for non-natively supported languages.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    _validate_reference_audio(reference_audio_path)

    if not text.strip():
        _generate_silence(output_path, duration_seconds=0.5)
        return output_path, 1.0

    native = language in XTTS_NATIVE
    quality = 0.85 if native else 0.65
    xtts_lang = language if native else INDIC_XTTS_PROXY.get(language, "hi")

    if not native:
        log.warning("xtts_non_native_language",
                    language=language,
                    using_approximation=xtts_lang,
                    quality_estimate=quality)

    try:
        tts = _get_tts(XTTS_MODEL)
        tts.tts_to_file(
            text=text,
            speaker_wav=reference_audio_path,
            language=xtts_lang,
            file_path=output_path
        )
        log.debug("tts_clone_done", lang=language, quality=quality)
        return output_path, quality
    except Exception as e:
        log.error("tts_clone_failed", error=str(e), fallback="generic")
        # Fall back to generic if clone fails
        result_path = synthesize_generic(text, language, output_path)
        return result_path, 0.5


def synthesize_segments(
    segments: list[dict],
    language: str,
    output_dir: str,
    voice_clone_path: str | None = None
) -> list[dict]:
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for i, seg in enumerate(segments):
        text = seg.get("translated_text", "").strip()
        output_path = os.path.join(output_dir, f"chunk_{i:04d}.wav")

        try:
            if voice_clone_path:
                path, quality = synthesize_cloned(text, language, voice_clone_path, output_path)
                results.append({**seg, "dubbed_audio_path": path, "voice_quality_estimate": quality})
            else:
                path = synthesize_generic(text, language, output_path)
                results.append({**seg, "dubbed_audio_path": path})
        except Exception as e:
            log.error("segment_synthesis_failed", segment=i, error=str(e))
            _generate_silence(output_path, duration_seconds=1.0)
            results.append({**seg, "dubbed_audio_path": output_path, "synthesis_error": str(e)})

    log.info("synthesis_done", segments=len(results), language=language)
    return results


def _validate_reference_audio(path: str):
    import soundfile as sf
    if not os.path.exists(path):
        raise FileNotFoundError(f"Reference audio not found: {path}")
    info = sf.info(path)
    if info.duration < MIN_REFERENCE_DURATION_SECONDS:
        raise ValueError(
            f"Reference audio too short: {info.duration:.1f}s "
            f"(minimum {MIN_REFERENCE_DURATION_SECONDS}s required)"
        )


def _generate_silence(output_path: str, duration_seconds: float = 0.5):
    """Write a silent audio file. Uses ffmpeg if available, numpy+soundfile otherwise."""
    import shutil
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    if shutil.which("ffmpeg"):
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"anullsrc=r=22050:cl=mono:d={duration_seconds}",
            output_path
        ], capture_output=True)
    else:
        import numpy as np
        import soundfile as sf
        sr = 22050
        silence = np.zeros(int(sr * duration_seconds), dtype=np.float32)
        sf.write(output_path, silence, sr)
