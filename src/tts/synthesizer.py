import os

import structlog

from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

INDIC_TTS_MODELS = {
    "te": "tts_models/te/cv/vits",
    "ta": "tts_models/ta/cv/vits",
    "kn": "tts_models/kn/cv/vits",
    "ml": "tts_models/ml/cv/vits",
    "hi": "tts_models/hi/cv/vits",
    "bn": "tts_models/bn/cv/vits",
    "mr": "tts_models/mr/cv/vits",
}

XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
XTTS_NATIVE = {"hi", "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh"}

MIN_REFERENCE_DURATION_SECONDS = 6.0

_tts_cache: dict = {}


def _get_tts(model_name: str):
    from TTS.api import TTS
    if model_name not in _tts_cache:
        log.info("loading_tts_model", model=model_name)
        gpu = settings.gpu_available
        _tts_cache[model_name] = TTS(model_name, gpu=gpu)
    return _tts_cache[model_name]


def synthesize_generic(text: str, language: str, output_path: str) -> str:
    model_name = INDIC_TTS_MODELS.get(language)
    if not model_name:
        raise ValueError(f"No generic TTS model for language: {language}")

    if not text.strip():
        _generate_silence(output_path, duration_seconds=0.5)
        return output_path

    tts = _get_tts(model_name)
    tts.tts_to_file(text=text, file_path=output_path)
    log.debug("tts_generic_done", lang=language, output=output_path)
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
    _validate_reference_audio(reference_audio_path)

    if not text.strip():
        _generate_silence(output_path, duration_seconds=0.5)
        return output_path, 1.0

    native = language in XTTS_NATIVE
    quality = 0.85 if native else 0.65
    xtts_lang = language if native else "hi"

    if not native:
        log.warning("xtts_non_native_language",
                    language=language,
                    using_approximation="hi",
                    quality_estimate=quality)

    tts = _get_tts(XTTS_MODEL)
    tts.tts_to_file(
        text=text,
        speaker_wav=reference_audio_path,
        language=xtts_lang,
        file_path=output_path
    )

    log.debug("tts_clone_done", lang=language, quality=quality, output=output_path)
    return output_path, quality


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

        if voice_clone_path:
            path, quality = synthesize_cloned(text, language, voice_clone_path, output_path)
            results.append({**seg, "dubbed_audio_path": path, "voice_quality_estimate": quality})
        else:
            path = synthesize_generic(text, language, output_path)
            results.append({**seg, "dubbed_audio_path": path})

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
    import subprocess
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=22050:cl=mono:d={duration_seconds}",
        output_path
    ], capture_output=True)
