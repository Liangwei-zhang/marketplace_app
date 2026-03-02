import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, List
from app.core.config import settings


class StorageService:
    """S3-compatible storage service (MinIO, AWS S3, etc.)"""
    
    def __init__(self):
        self.endpoint = os.getenv("S3_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("S3_SECRET_KEY", "minioadmin")
        self.bucket = os.getenv("S3_BUCKET", "marketplace")
        self.public_url = os.getenv("S3_PUBLIC_URL", f"http://{self.endpoint}/{self.bucket}")
        self.use_s3 = os.getenv("S3_ENABLED", "false").lower() == "true"
        
        if self.use_s3:
            self.client = boto3.client(
                's3',
                endpoint_url=f"http://{self.endpoint}",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            self._create_bucket_if_not_exists()
    
    def _create_bucket_if_not_exists(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)
    
    async def upload_file(self, file_data: bytes, filename: str, folder: str = "uploads") -> str:
        """Upload file and return public URL"""
        key = f"{folder}/{filename}"
        
        if self.use_s3:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                ContentType=self._get_content_type(filename)
            )
            return f"{self.public_url}/{key}"
        else:
            # Local storage fallback
            local_path = os.path.join(settings.UPLOAD_DIR, filename)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(file_data)
            return f"/uploads/{filename}"
    
    async def delete_file(self, filename: str, folder: str = "uploads") -> bool:
        """Delete file"""
        key = f"{folder}/{filename}"
        
        if self.use_s3:
            try:
                self.client.delete_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError:
                return False
        else:
            local_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.exists(local_path):
                os.remove(local_path)
                return True
            return False
    
    def _get_content_type(self, filename: str) -> str:
        ext = filename.split('.')[-1].lower()
        types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        return types.get(ext, 'application/octet-stream')


# Singleton instance
storage = StorageService()
