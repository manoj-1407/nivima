
import httpx
import structlog

from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

MODEL = "llama3.1:8b"


def rewrite_for_timing(
    source_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    duration_ms: int,
    critical_phonemes: list[dict] | None = None
) -> str:
    """
    Rewrites translated_text to fit duration_ms and match critical phonemes at key timestamps.
    critical_phonemes: [{"timestamp_ms": int, "phoneme": str, "viseme": str}]
    """
    phoneme_hints = ""
    if critical_phonemes:
        hints = []
        for cp in critical_phonemes[:3]:
            hints.append(
                f"At {cp['timestamp_ms']}ms: use a word with '{cp['phoneme']}' sound "
                f"(mouth shape: {cp['viseme']})"
            )
        phoneme_hints = "\n".join(hints)

    lang_notes = _get_language_notes(target_lang)

    prompt = f"""You are a professional dubbing scriptwriter specializing in Indian languages.

TASK: Rewrite the {target_lang} translation to fit dubbing constraints.

Original ({source_lang}): {source_text}
Translation ({target_lang}): {translated_text}

CONSTRAINTS:
1. Keep the same meaning as the original
2. Must fit within {duration_ms}ms when spoken at natural pace
3. Use natural {target_lang} speech rhythm
4. {lang_notes}
{f"5. Phoneme timing hints:{chr(10)}{phoneme_hints}" if phoneme_hints else ""}

OUTPUT: Return ONLY the rewritten {target_lang} text. No explanation. No quotes."""

    try:
        response = httpx.post(
            f"{settings.ollama_url}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()
        rewritten = result["response"].strip()

        if not rewritten or len(rewritten) < 2:
            log.warning("rewriter_empty_response", returning_original=True)
            return translated_text

        log.debug("rewriter_done",
                  original=translated_text[:60],
                  rewritten=rewritten[:60])
        return rewritten

    except Exception as e:
        log.error("rewriter_failed", error=str(e), fallback="original_translation")
        return translated_text


def rewrite_segments(
    segments: list[dict],
    source_lang: str,
    target_lang: str
) -> list[dict]:
    rewritten = []
    for seg in segments:
        translated = seg.get("translated_text", "")
        source = seg.get("text", "")
        duration = seg.get("end_ms", 0) - seg.get("start_ms", 0)

        if not translated or duration < 100:
            rewritten.append(seg)
            continue

        result = rewrite_for_timing(
            source_text=source,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            duration_ms=duration
        )

        rewritten.append({**seg, "translated_text": result, "rewriter_applied": True})

    return rewritten


def _get_language_notes(lang: str) -> str:
    notes = {
        "te": "Telugu uses SOV word order. Verb comes at end of sentence.",
        "ta": "Tamil uses SOV word order. Use formal Tamil, not slang.",
        "kn": "Kannada uses SOV word order. Verb at sentence end.",
        "ml": "Malayalam uses SOV word order. Use standard Malayalam.",
        "hi": "Hindi is flexible in word order but SOV preferred.",
        "bn": "Bengali uses SOV word order.",
    }
    return notes.get(lang, "Maintain natural word order for the target language.")
