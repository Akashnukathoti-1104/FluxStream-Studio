from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any


def s3_is_enabled(app) -> bool:
    return bool(app.config.get('RAW_BUCKET') or app.config.get('S3_BUCKET'))


def get_s3_client(app):
    if not s3_is_enabled(app):
        return None

    try:
        import boto3
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError('boto3 is required only when S3 is enabled') from exc

    kwargs: dict[str, Any] = {}
    region = app.config.get('S3_REGION')
    if region:
        kwargs['region_name'] = region

    access_key = app.config.get('S3_ACCESS_KEY_ID')
    secret_key = app.config.get('S3_SECRET_ACCESS_KEY')
    if access_key and secret_key:
        kwargs['aws_access_key_id'] = access_key
        kwargs['aws_secret_access_key'] = secret_key

    return boto3.client('s3', **kwargs)


def generate_presigned_post(app, object_key: str, content_type: str = 'application/octet-stream', expires_in: int = 3600):
    """Return a dict with url and fields for a browser to POST directly to S3."""
    client = get_s3_client(app)
    bucket = app.config.get('RAW_BUCKET') or app.config.get('S3_BUCKET')
    if not client or not bucket:
        raise RuntimeError('S3 not configured')

    return client.generate_presigned_post(
        Bucket=bucket,
        Key=object_key,
        Fields={'Content-Type': content_type},
        Conditions=[{'Content-Type': content_type}],
        ExpiresIn=expires_in,
    )


def generate_presigned_get(app, object_key: str, expires_in: int = 3600):
    client = get_s3_client(app)
    bucket = app.config.get('CDN_BUCKET') or app.config.get('RAW_BUCKET') or app.config.get('S3_BUCKET')
    if not client or not bucket:
        raise RuntimeError('S3 not configured')
    return client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': object_key}, ExpiresIn=expires_in)


def mirror_source_to_s3(app, source_path: str, object_key: str) -> None:
    if not s3_is_enabled(app):
        return

    client = get_s3_client(app)
    content_type = mimetypes.guess_type(source_path)[0] or 'application/octet-stream'
    client.upload_file(
        source_path,
        app.config.get('RAW_BUCKET') or app.config.get('S3_BUCKET'),
        object_key,
        ExtraArgs={'ContentType': content_type},
    )


def delete_s3_object(app, object_key: str | None) -> None:
    if not s3_is_enabled(app) or not object_key:
        return

    client = get_s3_client(app)
    client.delete_object(Bucket=app.config.get('S3_BUCKET') or app.config.get('RAW_BUCKET'), Key=object_key)


def cloudfront_signed_url(app, path: str, expires: int = 3600):
    """Sign a CloudFront URL if credentials are available; otherwise fall back to S3 presigned URL.

    `path` should be the resource path relative to the CloudFront domain (no leading slash).
    """
    domain = app.config.get('CLOUDFRONT_DOMAIN')
    key_pair_id = app.config.get('CLOUDFRONT_KEY_PAIR_ID')
    private_key = app.config.get('CLOUDFRONT_PRIVATE_KEY')
    if domain and key_pair_id and private_key:
        try:
            from botocore.signers import CloudFrontSigner
            import rsa
        except Exception:
            return f'https://{domain}/{path}'

        def rsa_signer(message):
            return rsa.sign(message, rsa.PrivateKey.load_pkcs1(private_key.encode('utf-8')), 'SHA-1')

        cf_signer = CloudFrontSigner(key_pair_id, rsa_signer)
        url = f'https://{domain}/{path}'
        return cf_signer.generate_presigned_url(url, date_less_than=expires)

    # fallback to S3 presigned GET against CDN_BUCKET or RAW_BUCKET
    obj_key = path
    try:
        return generate_presigned_get(app, obj_key, expires)
    except Exception:
        return f'https://{domain}/{path}' if domain else obj_key
