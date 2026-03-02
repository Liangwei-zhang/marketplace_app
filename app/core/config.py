from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/marketplace"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/marketplace"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif", "webp"}

    # Image compression
    COMPRESSED_MAX_WIDTH: int = 1200
    COMPRESSED_QUALITY: int = 80

    # CORS
    CORS_ORIGINS: list = ["*"]

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: int = 5  # per minute
    RATE_LIMIT_REGISTER: int = 3  # per minute

    # S3/MinIO Storage
    S3_ENABLED: bool = False
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "marketplace"
    S3_PUBLIC_URL: str = ""

    # Redis Cache
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_ITEMS: int = 300  # 5 minutes
    CACHE_TTL_USER: int = 600  # 10 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
