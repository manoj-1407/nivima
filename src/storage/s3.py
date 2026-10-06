import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import structlog
from src.config import get_settings

log = structlog.get_logger()
settings = get_settings()

_client = None


def get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4")
        )
    return _client


def upload_file(local_path: str, s3_key: str, content_type: str = "video/mp4") -> str:
    client = get_client()
    try:
        client.upload_file(
            local_path,
            settings.s3_bucket,
            s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        log.info("s3_upload_complete", key=s3_key, size=os.path.getsize(local_path))
        return s3_key
    except ClientError as e:
        log.error("s3_upload_failed", key=s3_key, error=str(e))
        raise


def download_file(s3_key: str, local_path: str) -> str:
    client = get_client()
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        client.download_file(settings.s3_bucket, s3_key, local_path)
        log.info("s3_download_complete", key=s3_key)
        return local_path
    except ClientError as e:
        log.error("s3_download_failed", key=s3_key, error=str(e))
        raise


def generate_presigned_url(s3_key: str, expires_in: int = 604800) -> str:
    client = get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": s3_key},
        ExpiresIn=expires_in
    )


def delete_file(s3_key: str) -> None:
    client = get_client()
    try:
        client.delete_object(Bucket=settings.s3_bucket, Key=s3_key)
        log.info("s3_delete_complete", key=s3_key)
    except ClientError as e:
        log.error("s3_delete_failed", key=s3_key, error=str(e))
        raise
