from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    app_name: str = "Nivima"
    database_url: str = "postgresql://nivima:password@localhost:5432/nivima"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "nivima-media"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "auto"

    jwt_secret: str = "nivima_default_jwt_secret_key_minimum_32_characters_for_security"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
