"""
ClaimIQ — Storage Service
Local filesystem (dev) → Cloudflare R2 (prod).
Switch via STORAGE_BACKEND env var.
"""
import uuid
import logging
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _safe_filename(original: str) -> str:
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4()}{ext}"


async def save_file(file_bytes: bytes, original_filename: str) -> str:
    if settings.storage_backend == "r2":
        return await _save_r2(file_bytes, original_filename)
    return await _save_local(file_bytes, original_filename)


async def _save_local(file_bytes: bytes, original_filename: str) -> str:
    upload_dir = Path(settings.storage_local_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(original_filename)
    path = upload_dir / filename
    path.write_bytes(file_bytes)
    logger.info(f"Saved file: {path}")
    return str(path)


async def _save_r2(file_bytes: bytes, original_filename: str) -> str:
    import boto3
    from botocore.config import Config

    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )
    filename = _safe_filename(original_filename)
    s3.put_object(Bucket=settings.r2_bucket_name, Key=filename, Body=file_bytes)
    url = f"{settings.r2_public_url}/{filename}"
    logger.info(f"Saved to R2: {url}")
    return url


async def load_file(file_url: str) -> bytes:
    if file_url.startswith("http"):
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(file_url)
            r.raise_for_status()
            return r.content
    return Path(file_url).read_bytes()
