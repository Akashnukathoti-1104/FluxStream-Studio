from __future__ import annotations

from . import create_celery_app
from .. import create_app
from ..extensions import db
from ..models import Video

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

    video.subtitle_url = f'/static/subtitles/{video_id}.vtt'
    db.session.commit()
    return {'video_id': video.id, 'subtitle_url': video.subtitle_url}
