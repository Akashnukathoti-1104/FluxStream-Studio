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
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "instance" / "nexstream.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.getenv('JWT_SECRET', SECRET_KEY)
    JWT_ALGORITHM = 'HS256'
    MAX_CONTENT_LENGTH = int(float(os.getenv('UPLOAD_LIMIT_MB', '1024')) * 1024 * 1024)
    UPLOAD_FOLDER = str(INSTANCE_DIR / 'uploads')
    STREAM_FOLDER = str(INSTANCE_DIR / 'streams')
    THUMBNAIL_FOLDER = str(INSTANCE_DIR / 'thumbnails')
    SUBTITLE_FOLDER = str(INSTANCE_DIR / 'subtitles')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    RAW_BUCKET = os.getenv('RAW_BUCKET', 'nexstream-raw').strip()
    CDN_BUCKET = os.getenv('CDN_BUCKET', 'nexstream-cdn').strip()
    ASSETS_BUCKET = os.getenv('ASSETS_BUCKET', 'nexstream-assets').strip()
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID', '').strip()
    S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY', '').strip()
    S3_SOURCE_PREFIX = os.getenv('S3_SOURCE_PREFIX', 'nexstream/raw').strip('/')
    S3_PROCESSED_PREFIX = os.getenv('S3_PROCESSED_PREFIX', 'nexstream/processed').strip('/')
    CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', '').strip()


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
