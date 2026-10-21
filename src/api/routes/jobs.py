import os
import tempfile
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.api.models.job import JobSubmitRequest
from src.ingestion.validator import ValidationError, validate_and_extract_metadata
from src.storage.db import Job, JobStatus, User, get_db
from src.storage.s3 import generate_presigned_url, upload_file
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
        # Bounded streaming write in 1MB chunks to prevent memory exhaustion
        while True:
            chunk = await video.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        metadata = validate_and_extract_metadata(tmp_path)
    except ValidationError as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=400, detail=str(e))

    # Accounting: total workload minutes = duration * number of target languages
    target_count = len(req.target_languages)
    duration_minutes = metadata.duration_seconds / 60.0
    workload_minutes = round(duration_minutes * target_count, 2)

    job_id = uuid.uuid4()
    s3_key = f"uploads/{job_id}/source{os.path.splitext(video.filename or '.mp4')[1]}"

    # Upload to storage first BEFORE acquiring database locks to avoid prolonged row contention
    try:
        upload_file(tmp_path, s3_key, content_type=video.content_type or "video/mp4")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Short atomic transaction for quota reservation and job creation
    user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    limit = TIER_LIMITS.get(user.tier, 10)
    used = float(user.minutes_processed_this_month or 0.0)

    if used + workload_minutes > limit:
        raise HTTPException(
            status_code=402,
            detail=f"Minute limit exceeded. Used: {used:.1f}/{limit} min. "
                   f"Job requires {workload_minutes:.1f} min ({target_count} target languages)."
        )

    job = Job(
        id=job_id,
        user_id=user.id,
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
    user.minutes_processed_this_month = round(used + workload_minutes, 2)
    db.commit()

    try:
        process_job.delay(str(job_id))
    except Exception as e:
        log.error("celery_dispatch_failed", job_id=str(job_id), error=str(e))
        # Revert ONLY the specific workload_minutes reserved by this job, avoiding stale aggregate overwrites
        user_revert = db.query(User).filter(User.id == current_user.id).with_for_update().first()
        if user_revert:
            curr = float(user_revert.minutes_processed_this_month or 0.0)
            user_revert.minutes_processed_this_month = max(0.0, round(curr - workload_minutes, 2))
        job_revert = db.query(Job).filter(Job.id == job_id).first()
        if job_revert:
            job_revert.status = JobStatus.failed
            job_revert.error_message = f"Job dispatch failed: {e}"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to dispatch processing job to worker queue")

    log.info("job_submitted", job_id=str(job_id), user=str(user.id), workload_minutes=workload_minutes)


    return {
        "job_id": str(job_id),
        "status": "queued",
        "source_duration_minutes": round(duration_minutes, 2),
        "target_languages": req.target_languages,
        "domain_detection": "enabled",
        "created_at": datetime.now(UTC).isoformat()
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
