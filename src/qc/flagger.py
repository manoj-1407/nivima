import uuid

import structlog
from sqlalchemy.orm import Session

from src.qc.scorer import QCScore
from src.storage.db import QCQueue

log = structlog.get_logger()


def flag_chunk_if_needed(
    db: Session,
    job_id: str,
    chunk_id: str,
    target_language: str,
    score: QCScore,
    original_frame_path: str | None = None,
    reanimated_frame_path: str | None = None
) -> bool:
    if score.overall_pass:
        return False

    for flag_reason in score.flags:
        entry = QCQueue(
            id=uuid.uuid4(),
            job_id=job_id,
            chunk_id=chunk_id,
            target_language=target_language,
            flag_reason=flag_reason,
            flag_details={
                "syncnet": score.syncnet_score,
                "csim": score.csim_score,
                "psnr": score.psnr_non_lip,
                "temporal": score.temporal_variance,
                "frames_reverted": score.frames_reverted,
            },
            original_frame_path=original_frame_path,
            reanimated_frame_path=reanimated_frame_path,
        )
        db.add(entry)

    db.commit()
    log.warning("chunk_flagged",
                job_id=str(job_id),
                chunk_id=str(chunk_id),
                lang=target_language,
                flags=score.flags)
    return True


def get_job_qc_summary(db: Session, job_id: str) -> dict:

    flags = db.query(QCQueue).filter(QCQueue.job_id == job_id).all()
    pending = [f for f in flags if f.reviewed_at is None]
    reviewed = [f for f in flags if f.reviewed_at is not None]

    return {
        "total_flags": len(flags),
        "pending_review": len(pending),
        "reviewed": len(reviewed),
        "flagged_scenes": [
            {
                "id": str(f.id),
                "chunk_id": str(f.chunk_id),
                "target_language": f.target_language,
                "flag_reason": f.flag_reason,
                "flag_details": f.flag_details,
                "original_frame_path": f.original_frame_path,
                "reanimated_frame_path": f.reanimated_frame_path,
                "flagged_at": f.flagged_at.isoformat(),
                "status": "pending" if f.reviewed_at is None else f.reviewer_decision
            }
            for f in flags
        ]
    }
