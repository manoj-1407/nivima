from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    redis_url: str

    s3_endpoint: str
    s3_bucket: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str = "auto"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    ollama_url: str = "http://localhost:11434"
    model_cache_dir: str = "/models"

    max_video_size_mb: int = 2000
    max_video_duration_seconds: int = 18000

    celery_concurrency: int = 2
    gpu_available: bool = False
    gpu_device: str = "cpu"

    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
