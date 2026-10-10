"""
Nivima Studio Voice Personas.
Curated expressive voice profiles for creators who do not want to use or clone their own voice.
Preserves natural timing, syllable durations, and emotional cadence.
"""

from dataclasses import dataclass
from enum import Enum


class PersonaGender(str, Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass(frozen=True)
class VoicePersona:
    id: str
    name: str
    gender: PersonaGender
    tone_description: str
    speaking_rate: float  # 1.0 = normal, 1.1 = brisk, 0.9 = measured
    pitch_semitones: float
    ideal_for: str
    language_native: str


STUDIO_PERSONAS: dict[str, VoicePersona] = {
    "educator_male": VoicePersona(
        id="educator_male",
        name="Aarav (The Educator)",
        gender=PersonaGender.MALE,
        tone_description="Calm, articulate, measured with zero vocal fry and clear enunciation.",
        speaking_rate=0.95,
        pitch_semitones=-1.0,
        ideal_for="Lectures, academic tutorials, deep explanations",
        language_native="hi"
    ),
    "tech_host_female": VoicePersona(
        id="tech_host_female",
        name="Ananya (The Tech Host)",
        gender=PersonaGender.FEMALE,
        tone_description="Dynamic, modern, conversational with upbeat energy.",
        speaking_rate=1.05,
        pitch_semitones=0.5,
        ideal_for="Tech reviews, coding walkthroughs, product launches",
        language_native="hi"
    ),
    "storyteller_calm": VoicePersona(
        id="storyteller_calm",
        name="Rishi (The Storyteller)",
        gender=PersonaGender.MALE,
        tone_description="Deep, resonant, rich low-end with dramatic micro-pauses.",
        speaking_rate=0.88,
        pitch_semitones=-2.5,
        ideal_for="Documentaries, history, philosophy, audiobooks",
        language_native="hi"
    ),
    "corporate_female": VoicePersona(
        id="corporate_female",
        name="Pooja (The Executive)",
        gender=PersonaGender.FEMALE,
        tone_description="Professional, polished, authoritative, corporate-neutral.",
        speaking_rate=1.0,
        pitch_semitones=0.0,
        ideal_for="Internal training, enterprise compliance, keynote presentations",
        language_native="hi"
    ),
    "telugu_presenter_male": VoicePersona(
        id="telugu_presenter_male",
        name="Kalyan (The Anchor)",
        gender=PersonaGender.MALE,
        tone_description="Native Telugu prosody, clear retroflex consonants, rhythmic pacing.",
        speaking_rate=1.02,
        pitch_semitones=-0.5,
        ideal_for="Telugu media, news reports, regional explainer videos",
        language_native="te"
    ),
    "tamil_host_female": VoicePersona(
        id="tamil_host_female",
        name="Meera (The Voice)",
        gender=PersonaGender.FEMALE,
        tone_description="Melodious, distinct Tamil alveolar and retroflex articulation.",
        speaking_rate=1.0,
        pitch_semitones=0.8,
        ideal_for="Tamil podcasts, educational content, interviews",
        language_native="ta"
    )
}


def get_persona(persona_id: str) -> VoicePersona:
    return STUDIO_PERSONAS.get(persona_id, STUDIO_PERSONAS["educator_male"])


def list_personas() -> list[dict]:
    return [
        {
            "id": p.id,
            "name": p.name,
            "gender": p.gender.value,
            "tone": p.tone_description,
            "ideal_for": p.ideal_for,
            "language": p.language_native
        }
        for p in STUDIO_PERSONAS.values()
    ]
