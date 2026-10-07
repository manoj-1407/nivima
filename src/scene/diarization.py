import os
from dataclasses import dataclass

import structlog

log = structlog.get_logger()

_pipeline = None


@dataclass
class SpeakerSegment:
    speaker_id: str
    start_ms: int
    end_ms: int
    confidence: float


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from pyannote.audio import Pipeline
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            if not hf_token:
                log.warning("no_hf_token_diarization_disabled")
                return None
            _pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            log.info("diarization_pipeline_loaded")
        except Exception as e:
            log.warning("diarization_load_failed", error=str(e))
            return None
    return _pipeline


def diarize(audio_path: str) -> list[SpeakerSegment]:
    pipeline = _get_pipeline()
    if pipeline is None:
        log.warning("diarization_unavailable_single_speaker_assumed")
        return _single_speaker_fallback(audio_path)

    try:
        diarization = pipeline(audio_path)
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(SpeakerSegment(
                speaker_id=speaker,
                start_ms=int(turn.start * 1000),
                end_ms=int(turn.end * 1000),
                confidence=0.85
            ))
        log.info("diarization_done",
                 segments=len(segments),
                 speakers=len({s.speaker_id for s in segments}))
        return segments
    except Exception as e:
        log.error("diarization_failed", error=str(e))
        return _single_speaker_fallback(audio_path)


def get_active_speaker_at(
    segments: list[SpeakerSegment],
    timestamp_ms: int
) -> str | None:
    for seg in segments:
        if seg.start_ms <= timestamp_ms <= seg.end_ms:
            return seg.speaker_id
    return None


def _single_speaker_fallback(audio_path: str) -> list[SpeakerSegment]:
    import json
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", audio_path],
        capture_output=True, text=True
    )
    try:
        duration_ms = int(float(json.loads(result.stdout)["format"]["duration"]) * 1000)
    except Exception:
        duration_ms = 60000

    return [SpeakerSegment(
        speaker_id="SPEAKER_00",
        start_ms=0,
        end_ms=duration_ms,
        confidence=1.0
    )]
