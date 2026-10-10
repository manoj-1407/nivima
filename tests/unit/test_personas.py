"""Tests for studio voice personas."""
from src.tts.personas import get_persona, list_personas


def test_list_personas():
    personas = list_personas()
    assert len(personas) >= 6
    ids = [p["id"] for p in personas]
    assert "educator_male" in ids
    assert "tech_host_female" in ids
    assert "storyteller_calm" in ids
    assert "telugu_presenter_male" in ids
    assert "tamil_host_female" in ids


def test_get_persona_default():
    persona = get_persona("non_existent_id")
    assert persona.id == "educator_male"


def test_persona_attributes():
    persona = get_persona("tech_host_female")
    assert persona.gender.value == "female"
    assert persona.speaking_rate > 1.0
