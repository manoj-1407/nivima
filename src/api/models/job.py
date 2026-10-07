
from pydantic import BaseModel, field_validator

SUPPORTED_LANGUAGES = {
    "hi",  # Hindi
    "te",  # Telugu
    "ta",  # Tamil
    "kn",  # Kannada
    "ml",  # Malayalam
    "bn",  # Bengali
    "mr",  # Marathi
    "gu",  # Gujarati
    "or",  # Odia
    "pa",  # Punjabi
    "as",  # Assamese
    "ur",  # Urdu
    "en",  # English
}

VALID_TIERS = {"speed", "quality", "balanced"}
MAX_TARGET_LANGUAGES = 8


class JobSubmitRequest(BaseModel):
    source_language: str
    target_languages: list[str]
    processing_tier: str = "speed"
    voice_clone_id: str | None = None

    @field_validator("source_language")
    @classmethod
    def validate_source_language(cls, v: str) -> str:
        lang = v.strip().lower()
        if lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: '{v}'. Supported: {sorted(SUPPORTED_LANGUAGES)}")
        return lang

    @field_validator("target_languages")
    @classmethod
    def validate_target_languages(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Target languages list cannot be empty.")

        # Deduplicate preserving order
        deduped = []
        seen = set()
        for item in v:
            lang = item.strip().lower()
            if lang not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Unsupported target language: '{item}'. Supported: {sorted(SUPPORTED_LANGUAGES)}")
            if lang not in seen:
                seen.add(lang)
                deduped.append(lang)

        if len(deduped) > MAX_TARGET_LANGUAGES:
            raise ValueError(
                f"Too many target languages: {len(deduped)}. Maximum allowed per job is {MAX_TARGET_LANGUAGES}."
            )
        return deduped

    @field_validator("processing_tier")
    @classmethod
    def validate_processing_tier(cls, v: str) -> str:
        tier = v.strip().lower()
        if tier not in VALID_TIERS:
            raise ValueError(f"Invalid processing tier: '{v}'. Must be one of: {sorted(VALID_TIERS)}")
        return tier


class VoiceCloneRequest(BaseModel):
    display_name: str
    consent_acknowledged: bool

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        name = v.strip()
        if not name:
            raise ValueError("display_name cannot be empty.")
        return name

    @field_validator("consent_acknowledged")
    @classmethod
    def validate_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Consent must be explicitly acknowledged to register a voice clone.")
        return v
