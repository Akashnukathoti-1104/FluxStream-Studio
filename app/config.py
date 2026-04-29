from __future__ import annotations

import os
import secrets
from pathlib import Path


def load_secret_key(instance_dir: Path) -> str:
    env_key = os.getenv('SECRET_KEY', '').strip()
    if env_key:
        return env_key

    secret_file = instance_dir / 'secret_key.txt'
    if secret_file.exists():
        return secret_file.read_text(encoding='utf-8').strip()

    generated_key = secrets.token_urlsafe(64)
    secret_file.write_text(generated_key, encoding='utf-8')
    return generated_key


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    SECRET_KEY = load_secret_key(INSTANCE_DIR)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "instance" / "video_platform.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(float(os.getenv('UPLOAD_LIMIT_MB', '1024')) * 1024 * 1024)
    UPLOAD_FOLDER = str(INSTANCE_DIR / 'uploads')
    STREAM_FOLDER = str(INSTANCE_DIR / 'streams')
    THUMBNAIL_FOLDER = str(INSTANCE_DIR / 'thumbnails')
    S3_BUCKET = os.getenv('S3_BUCKET', '').strip()
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID', '').strip()
    S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY', '').strip()
    S3_SOURCE_PREFIX = os.getenv('S3_SOURCE_PREFIX', 'video-platform/uploads').strip('/')
