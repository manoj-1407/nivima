from dataclasses import dataclass, field
from typing import Optional
import structlog
from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

INDIC_LANGUAGES = {"hi", "te", "ta", "kn", "ml", "bn", "mr", "gu", "or", "pa", "as", "ur"}

_model_cache: dict = {}


@dataclass
class WordTimestamp:
    word: str
    start_ms: int
    end_ms: int
    confidence: float


@dataclass
class TranscriptSegment:
    text: str
    start_ms: int
    end_ms: int
    language: str
    words: list[WordTimestamp] = field(default_factory=list)
    avg_confidence: float = 0.0


def _get_model(model_size: str = "large-v3"):
    from faster_whisper import WhisperModel

    key = model_size
    if key not in _model_cache:
        device = settings.gpu_device if settings.gpu_available else "cpu"
        compute_type = "float16" if settings.gpu_available else "int8"
        log.info("loading_whisper_model", size=model_size, device=device)
        _model_cache[key] = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=settings.model_cache_dir
        )
    return _model_cache[key]


def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    chunk_offset_ms: int = 0
) -> list[TranscriptSegment]:
    model = _get_model()

    segments_iter, info = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300, "threshold": 0.5},
        beam_size=5
    )

    detected_lang = info.language
    log.info("transcription_language_detected",
             lang=detected_lang,
             confidence=round(info.language_probability, 3))

    result = []
    for seg in segments_iter:
        words = []
        if seg.words:
            for w in seg.words:
                words.append(WordTimestamp(
                    word=w.word.strip(),
                    start_ms=int(w.start * 1000) + chunk_offset_ms,
                    end_ms=int(w.end * 1000) + chunk_offset_ms,
                    confidence=round(w.probability, 3)
                ))

        avg_conf = sum(w.confidence for w in words) / len(words) if words else 0.0

        result.append(TranscriptSegment(
            text=seg.text.strip(),
            start_ms=int(seg.start * 1000) + chunk_offset_ms,
            end_ms=int(seg.end * 1000) + chunk_offset_ms,
            language=detected_lang,
            words=words,
            avg_confidence=round(avg_conf, 3)
        ))

    log.info("transcription_done",
             segments=len(result),
             language=detected_lang)

    return result


def segments_to_dict(segments: list[TranscriptSegment]) -> list[dict]:
    return [
        {
            "text": s.text,
            "start_ms": s.start_ms,
            "end_ms": s.end_ms,
            "language": s.language,
            "avg_confidence": s.avg_confidence,
            "words": [
                {
                    "word": w.word,
                    "start_ms": w.start_ms,
                    "end_ms": w.end_ms,
                    "confidence": w.confidence
                }
                for w in s.words
            ]
        }
        for s in segments
    ]
