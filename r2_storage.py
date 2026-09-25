"""
KameraPh Cloud Storage: Cloudflare R2 Zero-Egress Engine
---------------------------------------------------------
Handles high-volume graduation photo batches using S3-compatible APIs.
Enables:
  1. Direct presigned multipart uploads from client browsers (bypassing app servers).
  2. Presigned temporary download links for student photo packages.
  3. ZERO data-transfer / egress charges on downloads.
"""

import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional


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
            endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version="s3v4")
            )
        else:
            self.s3_client = None

    def generate_presigned_upload_url(self, file_key: str, content_type: str = "image/jpeg", expires_in: int = 3600) -> Dict[str, Any]:
        """
        Generates a direct pre-signed PUT URL for browser uploads to Cloudflare R2.
        Bypasses web server memory during high-volume pictorial spikes.
        """
        if not self.is_configured:
            # Fallback for local development
            return {
                "upload_url": f"/api/storage/upload?key={file_key}",
                "file_key": file_key,
                "storage": "local_streaming",
                "expires_in": expires_in
            }

        try:
            url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_key,
                    "ContentType": content_type
                },
                ExpiresIn=expires_in
            )
            return {
                "upload_url": url,
                "file_key": file_key,
                "storage": "cloudflare_r2",
                "expires_in": expires_in
            }
        except ClientError as e:
            return {"error": str(e), "storage": "error"}

    def generate_presigned_download_url(self, file_key: str, expires_in: int = 86400) -> str:
        """
        Generates a temporary pre-signed GET URL for clients to stream high-res photos
        directly from Cloudflare R2 with zero egress transfer cost.
        """
        if not self.is_configured:
            return f"/api/storage/download?key={file_key}"

        try:
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=expires_in
            )
        except ClientError:
            return f"/api/storage/download?key={file_key}"


storage = R2StorageEngine()
