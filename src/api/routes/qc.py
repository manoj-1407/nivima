from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog

from src.storage.db import get_db, QCQueue, Job, User
from src.api.middleware.auth import get_current_user
from src.qc.flagger import get_job_qc_summary

log = structlog.get_logger()
router = APIRouter(prefix="/api/v1/qc", tags=["qc"])


@router.get("/{job_id}")
def get_qc_report(
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

    return get_job_qc_summary(db, job_id)


@router.post("/{job_id}/review/{flag_id}")
def submit_review(
    job_id: str,
    flag_id: str,
    decision: str,
    notes: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if decision not in ("approve", "reject", "reprocess"):
        raise HTTPException(
            status_code=400,
            detail="decision must be: approve, reject, or reprocess"
        )

    flag = db.query(QCQueue).filter(
        QCQueue.id == flag_id,
        QCQueue.job_id == job_id
    ).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    flag.reviewed_at = datetime.now(timezone.utc)
    flag.reviewer_id = current_user.id
    flag.reviewer_decision = decision
    flag.reviewer_notes = notes
    db.commit()

    log.info("qc_review_submitted",
             flag_id=flag_id,
             decision=decision,
             reviewer=str(current_user.id))

    return {"status": "ok", "decision": decision, "flag_id": flag_id}


@router.get("/pending/all")
def get_all_pending(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    flags = (
        db.query(QCQueue)
        .join(Job, QCQueue.job_id == Job.id)
        .filter(
            Job.user_id == current_user.id,
            QCQueue.reviewed_at == None
        )
        .order_by(QCQueue.flagged_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(f.id),
            "job_id": str(f.job_id),
            "chunk_id": str(f.chunk_id),
            "target_language": f.target_language,
            "flag_reason": f.flag_reason,
            "flag_details": f.flag_details,
            "flagged_at": f.flagged_at.isoformat()
        }
        for f in flags
    ]
