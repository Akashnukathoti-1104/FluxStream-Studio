from __future__ import annotations

import mimetypes
from pathlib import Path


def s3_is_enabled(app) -> bool:
    return bool(app.config.get('S3_BUCKET'))


def get_s3_client(app):
    if not s3_is_enabled(app):
        return None

    try:
        import boto3
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError('boto3 is required only when S3 is enabled') from exc

    kwargs = {
        'region_name': app.config.get('S3_REGION') or None,
    }
    access_key = app.config.get('S3_ACCESS_KEY_ID')
    secret_key = app.config.get('S3_SECRET_ACCESS_KEY')
    if access_key and secret_key:
        kwargs['aws_access_key_id'] = access_key
        kwargs['aws_secret_access_key'] = secret_key

    return boto3.client('s3', **kwargs)


def mirror_source_to_s3(app, source_path: str, object_key: str) -> None:
    if not s3_is_enabled(app):
        return

    client = get_s3_client(app)
    content_type = mimetypes.guess_type(source_path)[0] or 'application/octet-stream'
    client.upload_file(
        source_path,
        app.config['S3_BUCKET'],
        object_key,
        ExtraArgs={'ContentType': content_type},
    )


def delete_s3_object(app, object_key: str | None) -> None:
    if not s3_is_enabled(app) or not object_key:
        return

    client = get_s3_client(app)
    client.delete_object(Bucket=app.config['S3_BUCKET'], Key=object_key)
