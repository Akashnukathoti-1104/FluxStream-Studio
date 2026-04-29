from __future__ import annotations

import tempfile
from pathlib import Path

import requests

from . import create_celery_app
from .. import create_app
from ..extensions import db
from ..models import Video
from ..services.storage import cloudfront_signed_url, get_s3_client

flask_app = create_app()
celery = create_celery_app(flask_app)


@celery.task(name='tasks.generate_ai_thumbnail')
def generate_ai_thumbnail(video_id: int):
    video = Video.query.get(video_id)
    if not video:
        return {'error': 'video not found'}

    video.ai_thumbnail_url = f'https://picsum.photos/seed/ai-{video_id}/1280/720'
    db.session.commit()
    return {'video_id': video.id, 'ai_thumbnail_url': video.ai_thumbnail_url}


@celery.task(name='tasks.generate_subtitles')
def generate_subtitles(video_id: int):
    video = Video.query.get(video_id)
    if not video:
        return {'error': 'video not found'}
    # Try OpenAI Whisper API if key is configured, otherwise leave placeholder
    api_key = flask_app.config.get('OPENAI_API_KEY') or None
    client = get_s3_client(flask_app)
    processed_prefix = flask_app.config.get('S3_PROCESSED_PREFIX', 'nexstream/processed')
    raw_bucket = flask_app.config.get('RAW_BUCKET') or flask_app.config.get('S3_BUCKET')
    destination_bucket = flask_app.config.get('CDN_BUCKET') or raw_bucket

    try:
        local = Path(tempfile.mktemp(suffix='.mp4'))
        if client and video.s3_key_raw and raw_bucket:
            # download raw source
            client.download_file(raw_bucket, video.s3_key_raw, str(local))
        else:
            # fall back to local path
            local = Path(video.s3_key_raw)

        transcript = ''
        if api_key and local.exists():
            url = 'https://api.openai.com/v1/audio/transcriptions'
            with open(local, 'rb') as fh:
                files = {'file': fh}
                data = {'model': 'whisper-1'}
                r = requests.post(url, headers={'Authorization': f'Bearer {api_key}'}, files=files, data=data, timeout=120)
                if r.status_code == 200:
                    j = r.json()
                    transcript = j.get('text', '')

        if not transcript:
            transcript = 'Transcription not available.'

        # write simple VTT (single cue)
        vtt = f"WEBVTT\n\n00:00:00.000 --> 00:10:00.000\n{transcript}\n"
        tmp_vtt = Path(tempfile.mktemp(suffix='.vtt'))
        tmp_vtt.write_text(vtt, encoding='utf-8')

        # upload to processed bucket
        s3_key = f"{processed_prefix}/{video.id}/subtitles.vtt"
        if client and destination_bucket:
            client.upload_file(str(tmp_vtt), destination_bucket, s3_key)
            video.subtitle_url = cloudfront_signed_url(flask_app, s3_key)
        else:
            # link to local instance file
            inst_sub = Path(flask_app.config['SUBTITLE_FOLDER']) / f"{video.id}.vtt"
            inst_sub.parent.mkdir(parents=True, exist_ok=True)
            tmp_vtt.replace(inst_sub)
            video.subtitle_url = f"/subtitles/{video.id}.vtt"

        db.session.commit()
        return {'video_id': video.id, 'subtitle_url': video.subtitle_url}
    finally:
        try:
            if 'local' in locals() and isinstance(local, Path) and local.exists():
                local.unlink()
        except Exception:
            pass
