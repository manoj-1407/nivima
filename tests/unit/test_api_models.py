import pytest
from pydantic import ValidationError
from src.api.models.job import JobSubmitRequest, VoiceCloneRequest


def test_valid_job_request():
    req = JobSubmitRequest(
        source_language="hi",
        target_languages=["te", "ta"],
        processing_tier="speed"
    )
    assert req.source_language == "hi"
    assert set(req.target_languages) == {"te", "ta"}


def test_invalid_source_language():
    with pytest.raises(ValidationError):
        JobSubmitRequest(source_language="xx", target_languages=["te"])


def test_invalid_target_language():
    with pytest.raises(ValidationError):
        JobSubmitRequest(source_language="hi", target_languages=["xx"])


def test_too_many_target_languages():
    with pytest.raises(ValidationError):
        JobSubmitRequest(
            source_language="hi",
            target_languages=["te", "ta", "kn", "ml", "bn", "mr", "gu", "or", "pa"]
        )


def test_empty_target_languages():
    with pytest.raises(ValidationError):
        JobSubmitRequest(source_language="hi", target_languages=[])


def test_invalid_processing_tier():
    with pytest.raises(ValidationError):
        JobSubmitRequest(
            source_language="hi",
            target_languages=["te"],
            processing_tier="ultra"
        )


def test_duplicate_targets_deduplicated():
    req = JobSubmitRequest(
        source_language="hi",
        target_languages=["te", "te", "ta"]
    )
    assert len(req.target_languages) == 2


def test_voice_clone_requires_consent():
    with pytest.raises(ValidationError):
        VoiceCloneRequest(display_name="My Voice", consent_acknowledged=False)


def test_voice_clone_valid():
    req = VoiceCloneRequest(display_name="Alakh Voice", consent_acknowledged=True)
    assert req.display_name == "Alakh Voice"
