import structlog

from src.worker.celery_app import app

log = structlog.get_logger()


@app.task(name="notify.job_complete")
def notify_job_complete(job_id: str):
    log.info("job_complete_notification", job_id=job_id)
    # TODO: WebSocket broadcast, email, webhook


@app.task(name="notify.job_failed")
def notify_job_failed(job_id: str, error: str):
    log.error("job_failed_notification", job_id=job_id, error=error)
    # TODO: WebSocket broadcast, email alert
