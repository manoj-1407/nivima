from celery import Celery

from src.config import get_settings

settings = get_settings()

app = Celery(
    "nivima",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.worker.tasks.pipeline", "src.worker.tasks.notify"]
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "src.worker.tasks.pipeline.*": {"queue": "default"},
        "src.worker.tasks.notify.*": {"queue": "notify"},
    },
    task_soft_time_limit=7200,
    task_time_limit=10800,
    result_expires=86400,
)
