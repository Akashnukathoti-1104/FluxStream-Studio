from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import desc

from ..models import Analytics, User, Video

studio_bp = Blueprint('studio', __name__)


@studio_bp.get('/studio')
def studio_page():
    user = User.query.first()
    videos = Video.query.order_by(desc(Video.created_at)).limit(20).all()
    earnings = sum((a.revenue_usd for a in Analytics.query.all()), 0.0)
    return render_template('studio.html', user=user, videos=videos, earnings=earnings)


@studio_bp.get('/api/studio/dashboard')
def studio_dashboard():
    videos = Video.query.all()
    total_views = sum(v.view_count for v in videos)
    total_watch_time = sum((v.duration_seconds or 0) * v.view_count for v in videos) // 60
    subscribers = sum(u.subscriber_count for u in User.query.filter(User.role.in_(['creator', 'admin'])).all())
    revenue = round((total_views / 1000.0) * 2.5, 2)
    return jsonify({
        'views': total_views,
        'watch_time_minutes': total_watch_time,
        'subscribers': subscribers,
        'revenue_usd': revenue,
    })


@studio_bp.get('/api/studio/analytics')
def studio_analytics():
    range_key = (request.args.get('range') or '7d').strip()
    days = {'7d': 7, '30d': 30, '90d': 90}.get(range_key, 7)
    video_id = request.args.get('video_id', type=int)

    start_date = date.today() - timedelta(days=days)
    query = Analytics.query.filter(Analytics.date >= start_date)
    if video_id:
        query = query.filter_by(video_id=video_id)

    rows = query.order_by(Analytics.date.asc()).all()
    return jsonify([
        {
            'date': r.date.isoformat(),
            'views': r.views,
            'watch_minutes': r.watch_minutes,
            'clicks': r.clicks,
            'ctr': r.ctr,
            'revenue_usd': r.revenue_usd,
        }
        for r in rows
    ])


@studio_bp.get('/api/studio/videos')
def studio_videos():
    page = max(int(request.args.get('page', 1) or 1), 1)
    items = Video.query.order_by(desc(Video.created_at)).paginate(page=page, per_page=20, error_out=False)
    payload = [
        {
            'id': v.id,
            'title': v.title,
            'status': v.status,
            'views': v.view_count,
            'likes': v.like_count,
            'created_at': v.created_at.isoformat(),
        }
        for v in items.items
    ]
    return jsonify({'items': payload, 'page': items.page, 'pages': items.pages})
