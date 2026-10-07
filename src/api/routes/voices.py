import os
import tempfile
import uuid
from datetime import UTC, datetime

import soundfile as sf
import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.storage.db import User, VoiceClone, get_db
from src.storage.s3 import upload_file

log = structlog.get_logger()
router = APIRouter(prefix="/api/v1/voices", tags=["voices"])

MIN_DURATION_SECONDS = 6.0
MAX_DURATION_SECONDS = 300.0

CLONE_LIMITS = {
    "free": 0,
    "creator": 1,
    "professional": 3,
    "enterprise": 99
}


@router.post("", status_code=201)
async def register_voice_clone(
    reference_audio: UploadFile = File(...),
    display_name: str = Form(...),
    consent_acknowledged: bool = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not consent_acknowledged:
        raise HTTPException(
            status_code=400,
            detail="Consent must be acknowledged. You confirm ownership or rights to this voice."
        )

    limit = CLONE_LIMITS.get(current_user.tier, 0)
    existing = db.query(VoiceClone).filter(
        VoiceClone.user_id == current_user.id,
        VoiceClone.is_active.is_(True)
    ).count()

    if existing >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Voice clone limit reached for your tier ({current_user.tier}). "
                   f"Limit: {limit}"
        )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        content = await reference_audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        try:
            info = sf.info(tmp_path)
            duration = info.duration
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid or unreadable audio file. Please provide a valid WAV, MP3, or FLAC audio file."
            )

        if duration < MIN_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=f"Audio too short: {duration:.1f}s. Minimum {MIN_DURATION_SECONDS}s required."
            )

        if duration > MAX_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=f"Audio too long: {duration:.1f}s. Maximum {MAX_DURATION_SECONDS}s."
            )

        clone_id = uuid.uuid4()
        s3_key = f"voices/{current_user.id}/{clone_id}/reference.wav"
        upload_file(tmp_path, s3_key, content_type="audio/wav")

        clone = VoiceClone(
            id=clone_id,
            user_id=current_user.id,
            display_name=display_name,
            reference_audio_path=s3_key,
            supported_languages=["hi"],
            consent_recorded_at=datetime.now(UTC),
            is_active=True
        )
        db.add(clone)
        db.commit()

        log.info("voice_clone_registered",
                 clone_id=str(clone_id),
                 user=str(current_user.id),
                 duration=round(duration, 1))

        return {
            "voice_id": str(clone_id),
            "display_name": display_name,
            "duration_seconds": round(duration, 1),
            "supported_languages": ["hi"],
            "quality_note": "Voice identity ~85% for Hindi. ~65% for other Indian languages.",
            "created_at": clone.consent_recorded_at.isoformat()
        }

    finally:
        os.unlink(tmp_path)


@router.get("")
def list_voice_clones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clones = db.query(VoiceClone).filter(
        VoiceClone.user_id == current_user.id,
        VoiceClone.is_active.is_(True)
    ).all()

    return [
        {
            "voice_id": str(c.id),
            "display_name": c.display_name,
            "supported_languages": c.supported_languages,
            "created_at": c.created_at.isoformat()
        }
        for c in clones
    ]


@router.delete("/{voice_id}", status_code=204)
def delete_voice_clone(
    voice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clone = db.query(VoiceClone).filter(
        VoiceClone.id == voice_id,
        VoiceClone.user_id == current_user.id
    ).first()

    if not clone:
        raise HTTPException(status_code=404, detail="Voice clone not found")

    clone.is_active = False
    db.commit()
    log.info("voice_clone_deleted", clone_id=voice_id)
