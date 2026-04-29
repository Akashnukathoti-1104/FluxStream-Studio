from __future__ import annotations

from datetime import date

from . import create_celery_app
from .. import create_app
from ..extensions import db
from ..models import Analytics, Video

flask_app = create_app()
celery = create_celery_app(flask_app)


@celery.task(name='tasks.update_analytics')
def update_analytics(video_id: int, event_type: str, user_id: int | None = None):
    video = Video.query.get(video_id)
    if not video:
        return {'error': 'video not found'}

    row = Analytics.query.filter_by(video_id=video_id, date=date.today()).first()
    if not row:
        row = Analytics(video_id=video_id, date=date.today())
        db.session.add(row)

    if event_type == 'view':
        row.views += 1
        row.watch_minutes += max((video.duration_seconds or 0) // 60, 1)
    if event_type == 'click':
        row.clicks += 1

    row.ctr = (row.clicks / row.views) if row.views else 0.0
    row.revenue_usd = round((row.views / 1000.0) * 2.5, 2)
    db.session.commit()
    return {'video_id': video_id, 'event_type': event_type}
