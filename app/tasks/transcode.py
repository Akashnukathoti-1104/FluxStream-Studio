from __future__ import annotations

from pathlib import Path

from . import create_celery_app
from .. import create_app
from ..extensions import db, socketio
from ..models import Video

flask_app = create_app()
celery = create_celery_app(flask_app)


@celery.task(name='tasks.transcode_video')
def transcode_video(video_id: int, s3_key_raw: str):
    video = Video.query.get(video_id)
    if not video:
        return {'error': 'video not found'}

    # Placeholder command flow. Replace with concrete ffmpeg and S3 operations in production.
    output_dir = Path(flask_app.config['STREAM_FOLDER']) / str(video_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    video.s3_key_raw = s3_key_raw
    video.status = 'live'
    video.hls_playlist_url = f'/stream/{video.id}/playlist.m3u8'
    db.session.commit()

    socketio.emit('video.processing.complete', {'video_id': video.id, 'status': video.status})
    return {'video_id': video.id, 'status': video.status}
