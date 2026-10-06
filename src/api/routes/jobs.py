import os
import uuid
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
import structlog

from src.storage.db import get_db, Job, JobStatus, User
from src.storage.s3 import upload_file, generate_presigned_url
from src.api.models.job import JobSubmitRequest
from src.api.middleware.auth import get_current_user
from src.ingestion.validator import validate_and_extract_metadata, ValidationError
from src.worker.tasks.pipeline import process_job

log = structlog.get_logger()
router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

TIER_LIMITS = {
    "free": 10,
    "creator": 120,
    "professional": 600,
    "enterprise": 999999
}


@router.post("", status_code=202)
async def submit_job(
    video: UploadFile = File(...),
    source_language: str = Form(...),
    target_languages: str = Form(...),
    processing_tier: str = Form("speed"),
    voice_clone_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import json
    targets = json.loads(target_languages) if target_languages.startswith("[") \
        else target_languages.split(",")

    try:
        req = JobSubmitRequest(
            source_language=source_language,
            target_languages=targets,
            processing_tier=processing_tier,
            voice_clone_id=voice_clone_id
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        content = await video.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        metadata = validate_and_extract_metadata(tmp_path)
    except ValidationError as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=400, detail=str(e))

    duration_minutes = metadata.duration_seconds / 60
    limit = TIER_LIMITS.get(current_user.tier, 10)
    used = current_user.minutes_processed_this_month or 0

    if used + duration_minutes > limit:
        os.unlink(tmp_path)
        raise HTTPException(
            status_code=402,
            detail=f"Minute limit exceeded. Used: {used:.1f}/{limit} min. "
                   f"Video is {duration_minutes:.1f} min."
        )

    job_id = uuid.uuid4()
    s3_key = f"uploads/{job_id}/source{os.path.splitext(video.filename or '.mp4')[1]}"
    upload_file(tmp_path, s3_key, content_type=video.content_type or "video/mp4")
    os.unlink(tmp_path)

    job = Job(
        id=job_id,
        user_id=current_user.id,
        status=JobStatus.queued,
        source_language=req.source_language,
        target_languages=req.target_languages,
        processing_tier=req.processing_tier,
        voice_clone_id=req.voice_clone_id,
        source_file_path=s3_key,
        source_duration_seconds=int(metadata.duration_seconds),
        source_resolution=metadata.resolution,
        source_fps=str(metadata.fps),
        output_paths={}
    )
    db.add(job)

    # Update user usage
    current_user.minutes_processed_this_month = (
        (current_user.minutes_processed_this_month or 0) + int(duration_minutes)
    )
    db.commit()

    process_job.delay(str(job_id))
    log.info("job_submitted", job_id=str(job_id), user=str(current_user.id))

    return {
        "job_id": str(job_id),
        "status": "queued",
        "source_duration_minutes": round(duration_minutes, 2),
        "target_languages": req.target_languages,
        "domain_detection": "enabled",
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("")
def list_jobs(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    status: str = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Job).filter(Job.user_id == current_user.id)

    if status:
        try:
            query = query.filter(Job.status == JobStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    total = query.count()
    jobs = query.order_by(desc(Job.created_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "jobs": [_job_to_dict(j) for j in jobs]
    }


@router.get("/{job_id}")
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(
        Job.id == job_id, Job.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_dict(job)


@router.delete("/{job_id}", status_code=204)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(
        Job.id == job_id, Job.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job.status.value}"
        )
    job.status = JobStatus.cancelled
    db.commit()


def _job_to_dict(job: Job) -> dict:
    outputs = {}
    for lang, s3_key in (job.output_paths or {}).items():
        outputs[lang] = {
            "download_url": generate_presigned_url(s3_key),
            "expires_in_hours": 168
        }
    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "progress_pct": job.progress_pct,
        "current_stage": job.current_stage,
        "source_language": job.source_language,
        "target_languages": job.target_languages,
        "processing_tier": job.processing_tier,
        "source_duration_seconds": job.source_duration_seconds,
        "source_resolution": job.source_resolution,
        "chunks_total": job.chunks_total,
        "chunks_completed": job.chunks_completed,
        "outputs": outputs,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message
    }
