"""
KameraPh Cloud Storage: Cloudflare R2 Zero-Egress Engine
---------------------------------------------------------
Handles high-volume graduation photo batches using S3-compatible APIs.
Enables:
  1. Direct presigned multipart uploads from client browsers (bypassing app servers).
  2. Presigned temporary download links for student photo packages.
  3. ZERO data-transfer / egress charges on downloads.

Security & Reliability Directives:
  - Zero Silent Failures: boto3 calls wrapped in try/except with full stack logging.
  - Strict Type Safety: Pydantic models for request/response payloads.
  - Path Isolation: Uses pathlib.Path for local fallback directory.
"""

import os
import io
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

logger = logging.getLogger("kameraph.r2_storage")

BASE_DIR = Path(__file__).resolve().parent
LOCAL_STORAGE_DIR = Path(os.getenv("LOCAL_STORAGE_DIR", BASE_DIR / "local_storage"))
LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class PresignedUploadResult(BaseModel):
    upload_url: str
    file_key: str
    storage: str
    expires_in: int
    content_type: str = "image/jpeg"


class PresignedDownloadResult(BaseModel):
    download_url: str
    file_key: str
    storage: str
    expires_in: int


class R2StorageEngine:
    def __init__(self):
        self.account_id = os.environ.get("R2_ACCOUNT_ID", "")
        self.access_key = os.environ.get("R2_ACCESS_KEY_ID", "")
        self.secret_key = os.environ.get("R2_SECRET_ACCESS_KEY", "")
        self.bucket_name = os.environ.get("R2_BUCKET_NAME", "kameraph-photos")
        self.public_domain = os.environ.get("R2_PUBLIC_DOMAIN", "http://127.0.0.1:8000/r2")
        
        self.is_configured = bool(
            self.account_id and 
            self.access_key and 
            self.secret_key and
            not self.account_id.startswith("mock_")
        )

        if self.is_configured:
            try:
                endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"
                self.s3_client = boto3.client(
                    "s3",
                    endpoint_url=endpoint,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    config=Config(signature_version="s3v4")
                )
                logger.info(f"[r2_storage] Cloudflare R2 client initialized for bucket '{self.bucket_name}'")
            except Exception as e:
                logger.error(f"[r2_storage] Failed to initialize R2 S3 client: {e}\n{traceback.format_exc()}")
                self.s3_client = None
                self.is_configured = False
        else:
            self.s3_client = None
            logger.info("[r2_storage] R2 credentials not configured. Local streaming fallback active.")

    def generate_presigned_upload_url(
        self,
        file_key: str,
        content_type: str = "image/jpeg",
        expires_in: int = 3600
    ) -> PresignedUploadResult:
        """
        Generates a direct pre-signed PUT URL for browser uploads to Cloudflare R2.
        Bypasses web server memory during high-volume pictorial spikes.
        """
        safe_key = Path(file_key).name

        if not self.is_configured or self.s3_client is None:
            # Fallback for local development
            return PresignedUploadResult(
                upload_url=f"/api/storage/upload?key={safe_key}",
                file_key=safe_key,
                storage="local_streaming",
                expires_in=expires_in,
                content_type=content_type
            )

        try:
            url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": safe_key,
                    "ContentType": content_type
                },
                ExpiresIn=expires_in
            )
            return PresignedUploadResult(
                upload_url=url,
                file_key=safe_key,
                storage="cloudflare_r2",
                expires_in=expires_in,
                content_type=content_type
            )
        except ClientError as e:
            logger.error(f"[r2_storage] ClientError generating presigned PUT URL for {safe_key}: {e}\n{traceback.format_exc()}")
            # Graceful fallback to local streaming
            return PresignedUploadResult(
                upload_url=f"/api/storage/upload?key={safe_key}",
                file_key=safe_key,
                storage="local_fallback",
                expires_in=expires_in,
                content_type=content_type
            )

    def generate_presigned_download_url(
        self,
        file_key: str,
        expires_in: int = 86400
    ) -> PresignedDownloadResult:
        """
        Generates a temporary pre-signed GET URL for clients to stream high-res photos
        directly from Cloudflare R2 with zero egress transfer cost.
        """
        safe_key = Path(file_key).name

        if not self.is_configured or self.s3_client is None:
            return PresignedDownloadResult(
                download_url=f"/api/storage/download?key={safe_key}",
                file_key=safe_key,
                storage="local_streaming",
                expires_in=expires_in
            )

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": safe_key},
                ExpiresIn=expires_in
            )
            return PresignedDownloadResult(
                download_url=url,
                file_key=safe_key,
                storage="cloudflare_r2",
                expires_in=expires_in
            )
        except ClientError as e:
            logger.error(f"[r2_storage] ClientError generating presigned GET URL for {safe_key}: {e}\n{traceback.format_exc()}")
            return PresignedDownloadResult(
                download_url=f"/api/storage/download?key={safe_key}",
                file_key=safe_key,
                storage="local_fallback",
                expires_in=expires_in
            )

    def get_object_bytes(self, file_key: str) -> bytes:
        """
        Retrieves raw object bytes from Cloudflare R2 or local storage fallback.
        """
        safe_key = Path(file_key).name

        if self.is_configured and self.s3_client is not None:
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=safe_key)
                return response["Body"].read()
            except ClientError as e:
                logger.error(f"[r2_storage] Failed to fetch {safe_key} from R2 bucket: {e}\n{traceback.format_exc()}")

        # Local storage fallback
        local_path = LOCAL_STORAGE_DIR / safe_key
        if not local_path.is_file():
            raise FileNotFoundError(f"[r2_storage] File {safe_key} not found in local or R2 storage.")

        with open(local_path, "rb") as f:
            return f.read()


storage = R2StorageEngine()


def upload_file_to_r2(local_path: str, r2_key: str) -> None:
    """
    Uploads a local file to Cloudflare R2 using the singleton storage engine.
    Used by backup_db.py for off-site backup sync.
    Falls back gracefully if R2 is not configured.
    """
    if not storage.is_configured or storage.s3_client is None:
        logger.warning(f"[r2_storage] R2 not configured — skipping upload of {r2_key}")
        return

    try:
        with open(local_path, "rb") as f:
            storage.s3_client.put_object(
                Bucket=storage.bucket_name,
                Key=r2_key,
                Body=f
            )
        logger.info(f"[r2_storage] Uploaded {local_path} → R2:{r2_key}")
    except ClientError as e:
        logger.error(f"[r2_storage] Failed to upload {local_path} to R2: {e}\n{traceback.format_exc()}")
        raise
