import structlog

from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

LANGUAGE_CODES = {
    "hi": "hin_Deva",
    "te": "tel_Telu",
    "ta": "tam_Taml",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "bn": "ben_Beng",
    "mr": "mar_Deva",
    "gu": "guj_Gujr",
    "or": "ory_Orya",
    "pa": "pan_Guru",
    "as": "asm_Beng",
    "ur": "urd_Arab",
}

MODEL_NAME = "ai4bharat/indictrans2-indic-indic-dist-200M"

_model = None
_tokenizer = None


def _load():
    global _model, _tokenizer
    if _model is None:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        log.info("loading_indictrans2", model=MODEL_NAME)
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, trust_remote_code=True,
            cache_dir=settings.model_cache_dir
        )
        _model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_NAME, trust_remote_code=True,
            cache_dir=settings.model_cache_dir
        )
        if settings.gpu_available:
            _model = _model.to(settings.gpu_device)
        _model.eval()
        log.info("indictrans2_loaded")


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    src_code = LANGUAGE_CODES.get(source_lang)
    tgt_code = LANGUAGE_CODES.get(target_lang)

    if not src_code or not tgt_code:
        raise ValueError(f"Unsupported language pair: {source_lang} → {target_lang}")

    if not text.strip():
        return ""

    _load()

    import torch

    # IndicTrans2 uses forced_bos_token_id for target language — NOT tgt_lang.
    # The tgt_lang parameter is NLLB-specific and does not exist in IndicTrans2's
    # generate() method. Using it causes TypeError.
    try:
        tgt_token_id = _tokenizer.convert_tokens_to_ids(tgt_code)
    except Exception:
        # Some IndicTrans2 versions use lang_code_to_id
        tgt_token_id = _tokenizer.lang_code_to_id.get(tgt_code, None)

    # Tokenise — IndicTrans2 tokenizer accepts src_lang via its custom tokenizer
    try:
        inputs = _tokenizer(
            text,
            return_tensors="pt",
            src_lang=src_code,
            padding=True,
            truncation=True,
            max_length=512
        )
    except TypeError:
        # Fallback: some versions don't accept src_lang directly in __call__
        inputs = _tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )

    if settings.gpu_available:
        inputs = {k: v.to(settings.gpu_device) for k, v in inputs.items()}

    generate_kwargs = {
        "max_length": 512,
        "num_beams": 4,
        "length_penalty": 1.0,
        "early_stopping": True,
    }

    if tgt_token_id is not None:
        generate_kwargs["forced_bos_token_id"] = tgt_token_id

    with torch.no_grad():
        outputs = _model.generate(**inputs, **generate_kwargs)

    translation = _tokenizer.decode(outputs[0], skip_special_tokens=True)

    _validate_translation(text, translation)
    return translation


def translate_segments(
    segments: list[dict],
    source_lang: str,
    target_lang: str
) -> list[dict]:
    translated = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            translated.append({**seg, "translated_text": "", "target_language": target_lang})
            continue

        try:
            translation = translate_text(text, source_lang, target_lang)
        except Exception as e:
            log.warning("segment_translation_failed",
                        error=str(e),
                        text_preview=text[:50],
                        fallback="original_text")
            translation = text  # fallback: pass original text through

        translated.append({
            **seg,
            "translated_text": translation,
            "target_language": target_lang
        })
        log.debug("segment_translated",
                  source=text[:50], target=translation[:50])

    log.info("translation_done", segments=len(translated), target=target_lang)
    return translated


def _validate_translation(source: str, translation: str):
    src_words = len(source.split())
    tgt_words = len(translation.split())

    if src_words == 0:
        return

    ratio = tgt_words / src_words
    if ratio < 0.3 or ratio > 4.0:
        log.warning("translation_length_anomaly",
                    src_words=src_words,
                    tgt_words=tgt_words,
                    ratio=round(ratio, 2),
                    source_preview=source[:80])
