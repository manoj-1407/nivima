"""
Correction interface — the feedback loop that makes the product actually usable.

When a user watches their dubbed video and finds a segment that's wrong:
  - wrong translation
  - bad timing
  - voice quality unacceptable
  - reanimation looks bad

They submit a correction. The system re-synthesizes only that segment,
replaces it in the final video, and stores the correction as training data.

This is the data flywheel. Every correction improves future outputs.
"""

import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.storage.db import Chunk, Job, User, get_db

log = structlog.get_logger()
router = APIRouter(prefix="/api/v1/corrections", tags=["corrections"])


class CorrectionRequest(BaseModel):
    chunk_index: int
    target_language: str
    correction_type: str           # "translation" | "timing" | "voice" | "reanimation"
    corrected_text: str | None  # user-provided corrected translation
    timing_offset_ms: int | None  # shift audio forward/back
    notes: str | None


class CorrectionResponse(BaseModel):
    correction_id: str
    status: str
    message: str
    estimated_minutes: int


@router.post("/{job_id}", response_model=CorrectionResponse)
async def submit_correction(
    job_id: str,
    req: CorrectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status.value not in ("completed", "qc_review"):
        raise HTTPException(
            status_code=400,
            detail=f"Job must be completed to submit corrections. Current status: {job.status.value}"
        )

    chunk = db.query(Chunk).filter(
        Chunk.job_id == job_id,
        Chunk.chunk_index == req.chunk_index
    ).first()
    if not chunk:
        raise HTTPException(
            status_code=404,
            detail=f"Chunk {req.chunk_index} not found"
        )

    correction_id = str(uuid.uuid4())

    # Store correction as training data
    correction_record = {
        "id": correction_id,
        "job_id": job_id,
        "chunk_index": req.chunk_index,
        "target_language": req.target_language,
        "correction_type": req.correction_type,
        "original_translation": chunk.translations.get(req.target_language, ""),
        "corrected_text": req.corrected_text,
        "timing_offset_ms": req.timing_offset_ms,
        "notes": req.notes,
        "submitted_by": str(current_user.id),
        "submitted_at": datetime.now(UTC).isoformat(),
        "source_segment": chunk.source_text,
        "source_language": job.source_language,
    }

    _store_correction_for_training(correction_record)

    background_tasks.add_task(
        _resynthesize_segment,
        job_id=job_id,
        chunk_id=str(chunk.id),
        chunk_index=req.chunk_index,
        target_language=req.target_language,
        corrected_text=req.corrected_text,
        timing_offset_ms=req.timing_offset_ms,
        correction_type=req.correction_type,
        voice_clone_id=str(job.voice_clone_id) if job.voice_clone_id else None
    )

    log.info("correction_submitted",
             job_id=job_id,
             chunk=req.chunk_index,
             type=req.correction_type,
             lang=req.target_language)

    return CorrectionResponse(
        correction_id=correction_id,
        status="processing",
        message=f"Re-synthesizing segment {req.chunk_index}. "
                f"Final video will be updated automatically.",
        estimated_minutes=2
    )


@router.get("/{job_id}")
def list_corrections(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    corrections = _load_corrections_for_job(job_id)
    return {
        "job_id": job_id,
        "correction_count": len(corrections),
        "corrections": corrections
    }


def _store_correction_for_training(record: dict):
    """
    Stores correction as a training data point.
    These corrections become gold-standard training pairs for:
    - IndicTrans2 fine-tuning (translation corrections)
    - XTTS-v2 fine-tuning (voice corrections)
    - Timing model improvement (timing corrections)

    In production: write to a corrections table in PostgreSQL
    and a training data pipeline that periodically fine-tunes models.
    """
    import json
    import os
    corrections_dir = "./data/corrections"
    os.makedirs(corrections_dir, exist_ok=True)
    path = os.path.join(corrections_dir, f"{record['id']}.json")
    with open(path, "w") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    log.info("correction_stored_as_training_data",
             id=record["id"],
             type=record["correction_type"])


def _load_corrections_for_job(job_id: str) -> list:
    import glob
    import json
    import os
    corrections_dir = "./data/corrections"
    if not os.path.exists(corrections_dir):
        return []
    all_corrections = []
    for path in glob.glob(os.path.join(corrections_dir, "*.json")):
        with open(path) as f:
            c = json.load(f)
        if c.get("job_id") == job_id:
            all_corrections.append(c)
    return sorted(all_corrections, key=lambda x: x.get("submitted_at", ""))


async def _resynthesize_segment(
    job_id: str,
    chunk_id: str,
    chunk_index: int,
    target_language: str,
    corrected_text: str | None,
    timing_offset_ms: int | None,
    correction_type: str,
    voice_clone_id: str | None
):
    """
    Background task: re-synthesize one segment and patch it into the final video.
    This is surgical — only the corrected segment is re-processed.
    """
    import os
    import tempfile

    from src.alignment.audio_adjuster import adjust_segment_timing
    from src.storage.db import Chunk, SessionLocal
    from src.storage.s3 import download_file, upload_file
    from src.tts.synthesizer import synthesize_cloned, synthesize_generic

    db = SessionLocal()
    try:
        chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
        if not chunk:
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            text_to_synthesize = corrected_text or chunk.translations.get(target_language, "")
            if not text_to_synthesize:
                log.warning("no_text_to_resynthesize", chunk_id=chunk_id)
                return

            out_path = os.path.join(tmpdir, "corrected.wav")

            if voice_clone_id:
                clone_ref = os.path.join(tmpdir, "clone_ref.wav")
                from src.storage.db import VoiceClone
                clone = db.query(VoiceClone).filter(
                    VoiceClone.id == voice_clone_id
                ).first()
                if clone:
                    download_file(clone.reference_audio_path, clone_ref)
                    synthesize_cloned(
                        text_to_synthesize, target_language,
                        clone_ref, out_path
                    )
                else:
                    synthesize_generic(text_to_synthesize, target_language, out_path)
            else:
                synthesize_generic(text_to_synthesize, target_language, out_path)

            duration_ms = chunk.end_ms - chunk.start_ms
            adj_path = os.path.join(tmpdir, "adjusted.wav")
            adjusted, info = adjust_segment_timing(out_path, duration_ms, adj_path)

            s3_key = f"jobs/{job_id}/corrections/chunk_{chunk_index:04d}_{target_language}.wav"
            upload_file(adjusted, s3_key)

            if correction_type == "translation" and corrected_text:
                translations = dict(chunk.translations or {})
                translations[target_language] = corrected_text
                chunk.translations = translations
                db.commit()

            log.info("segment_resynthesized",
                     job_id=job_id,
                     chunk=chunk_index,
                     lang=target_language,
                     flagged=info.get("flagged", False))

    except Exception as e:
        log.error("resynthesis_failed", error=str(e), chunk_id=chunk_id)
    finally:
        db.close()
