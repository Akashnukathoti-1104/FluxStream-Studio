from __future__ import annotations

import uuid
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, render_template, request, current_app
from sqlalchemy import desc, or_

from ..extensions import db
from ..models import Comment, Like, Subscription, User, Video, WatchHistory

videos_bp = Blueprint('videos', __name__)

_UPLOAD_JOBS: dict[str, dict] = {}


def _serialize_video(video: Video) -> dict:
    return {
        'id': video.id,
        'title': video.title,
        'description': video.description,
        'tags': video.tags.split(',') if video.tags else [],
        'category': video.category,
        'status': video.status,
        'view_count': video.view_count,
        'like_count': video.like_count,
        'hls_playlist_url': video.hls_playlist_url,
        'thumbnail_url': video.ai_thumbnail_url or video.thumbnail_url,
        'duration_seconds': video.duration_seconds,
        'is_live': video.is_live,
        'created_at': video.created_at.isoformat(),
    }


@videos_bp.get('/')
def root_dashboard():
    videos = Video.query.order_by(desc(Video.view_count)).limit(12).all()
    stats = {
        'views': sum(v.view_count for v in videos),
        'watch_time': sum((v.duration_seconds or 0) for v in videos),
        'subscribers': User.query.filter_by(role='creator').with_entities(db.func.sum(User.subscriber_count)).scalar() or 0,
        'uploads': Video.query.count(),
    }
    return render_template('dashboard.html', videos=videos, stats=stats)


@videos_bp.get('/dashboard')
def dashboard_page():
    return root_dashboard()


@videos_bp.get('/healthz')
def healthz():
    return jsonify({'status': 'ok'})


@videos_bp.get('/videos')
def videos_page():
    category = request.args.get('category', '').strip()
    sort = request.args.get('sort', 'trending').strip()

    query = Video.query
    if category:
        query = query.filter(Video.category == category)

    if sort == 'newest':
        query = query.order_by(desc(Video.created_at))
    elif sort == 'most_watched':
        query = query.order_by(desc(Video.view_count))
    else:
        query = query.order_by(desc(Video.like_count + Video.view_count))

    return render_template('videos.html', videos=query.limit(30).all(), active_category=category, active_sort=sort)


@videos_bp.get('/watch/<int:video_id>')
def watch_page(video_id: int):
    video = Video.query.get_or_404(video_id)
    related = Video.query.filter(Video.id != video.id).order_by(desc(Video.view_count)).limit(8).all()
    history = WatchHistory.query.filter_by(video_id=video_id).first()
    resume_at = int((history.watch_percent or 0) * (video.duration_seconds or 0) / 100) if history else 0
    return render_template('watch.html', video=video, related=related, resume_at=resume_at)


@videos_bp.get('/upload')
def upload_page():
    return render_template('upload.html')


@videos_bp.get('/live')
def live_page():
    return render_template('live.html')


@videos_bp.get('/api/videos')
def list_videos():
    category = request.args.get('category', '').strip()
    sort = request.args.get('sort', 'trending').strip()
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = 12

    query = Video.query
    if category:
        query = query.filter(Video.category == category)

    if sort == 'newest':
        query = query.order_by(desc(Video.created_at))
    elif sort == 'most_watched':
        query = query.order_by(desc(Video.view_count))
    else:
        query = query.order_by(desc(Video.view_count + Video.like_count))

    if q := request.args.get('q', '').strip():
        like = f'%{q}%'
        query = query.filter(or_(Video.title.ilike(like), Video.description.ilike(like), Video.tags.ilike(like)))

    items = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'items': [_serialize_video(v) for v in items.items], 'page': page, 'pages': items.pages})


@videos_bp.get('/api/videos/<int:video_id>')
def get_video(video_id: int):
    return jsonify(_serialize_video(Video.query.get_or_404(video_id)))


@videos_bp.post('/api/videos/upload')
def upload_video():
    data = request.get_json(silent=True) or {}
    user = User.query.first()
    if not user:
        return jsonify({'error': 'seed a user before upload'}), 400

    title = (data.get('title') or 'Untitled Stream').strip()
    description = (data.get('description') or '').strip()
    tags = ','.join(data.get('tags') or [])
    category = (data.get('category') or 'General').strip()

    video = Video(
        user_id=user.id,
        title=title,
        description=description,
        tags=tags,
        category=category,
        status='processing',
        hls_playlist_url='',
        thumbnail_url='https://picsum.photos/seed/nexstream/1280/720',
        duration_seconds=0,
        view_count=0,
        like_count=0,
        is_live=False,
    )
    db.session.add(video)
    db.session.commit()

    job_id = uuid.uuid4().hex
    _UPLOAD_JOBS[job_id] = {
        'video_id': video.id,
        'progress': 10,
        'status': 'uploading',
        'started_at': datetime.now(timezone.utc).isoformat(),
    }

    # Prepare a presigned POST for the client to upload directly to S3.
    from ..services.storage import generate_presigned_post

    # object key: <prefix>/<video_id>/<original_filename>
    filename = (data.get('original_filename') or f'{uuid.uuid4().hex}.mp4').strip()
    object_key = f"{current_app.config.get('S3_SOURCE_PREFIX','nexstream/raw')}/{video.id}/{filename}"

    try:
        presigned = generate_presigned_post(current_app, object_key, content_type='video/mp4')
    except Exception as exc:
        _UPLOAD_JOBS[job_id]['status'] = 'error'
        return jsonify({'error': f'presign failed: {exc}'}), 500

    # return the presign info and job id; client should POST file to presigned['url'] with presigned['fields']
    return jsonify({
        'job_id': job_id,
        'video_id': video.id,
        'presigned_url': presigned['url'],
        'presigned_fields': presigned['fields'],
        'object_key': object_key,
    }), 202



@videos_bp.post('/api/videos/upload/complete')
def upload_complete():
    """Called by the client after successfully uploading to S3. Triggers processing.

    Expects JSON: { job_id, object_key, file_size }
    """
    data = request.get_json(silent=True) or {}
    job_id = data.get('job_id')
    object_key = data.get('object_key')
    file_size = data.get('file_size')

    job = _UPLOAD_JOBS.get(job_id)
    if not job:
        return jsonify({'error': 'job not found'}), 404

    video = Video.query.get(job['video_id'])
    if not video:
        return jsonify({'error': 'video not found'}), 404

    # mark source and enqueue transcode
    from ..services.storage import get_s3_client
    from ..tasks.transcode import transcode_video

    video.s3_key_raw = object_key
    video.file_size_bytes = int(file_size or 0)
    video.status = 'processing'
    db.session.commit()

    # enqueue Celery job
    try:
        transcode_video.delay(video.id, object_key)
    except Exception:
        # fallback: try apply_async
        transcode_video.apply_async(args=(video.id, object_key))

    job['status'] = 'processing'
    job['progress'] = 20
    return jsonify({'message': 'processing started', 'job_id': job_id, 'video_id': video.id}), 202


@videos_bp.get('/api/videos/upload/<job_id>/status')
def upload_status_stream(job_id: str):
    def stream():
        job = _UPLOAD_JOBS.get(job_id)
        if not job:
            yield 'event: error\ndata: {"error":"job not found"}\n\n'
            return

        for progress in [20, 40, 65, 85, 100]:
            job['progress'] = progress
            job['status'] = 'processing' if progress < 100 else 'live'
            payload = f'{{"job_id":"{job_id}","progress":{progress},"status":"{job["status"]}"}}'
            yield f'data: {payload}\n\n'

        video = Video.query.get(job['video_id'])
        if video:
            video.status = 'live'
            video.hls_playlist_url = f'/stream/{video.id}/playlist.m3u8'
            video.duration_seconds = 900
            db.session.commit()

    return Response(stream(), mimetype='text/event-stream')


@videos_bp.delete('/api/videos/<int:video_id>')
def delete_video(video_id: int):
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    return jsonify({'message': 'video deleted'})


@videos_bp.patch('/api/videos/<int:video_id>')
def patch_video(video_id: int):
    video = Video.query.get_or_404(video_id)
    data = request.get_json(silent=True) or {}
    for field in ['title', 'description', 'category']:
        if field in data:
            setattr(video, field, (data.get(field) or '').strip())
    if 'tags' in data:
        tags = data.get('tags') or []
        video.tags = ','.join(tags)
    db.session.commit()
    return jsonify(_serialize_video(video))


@videos_bp.post('/api/videos/<int:video_id>/like')
def like_video(video_id: int):
    video = Video.query.get_or_404(video_id)
    user = User.query.first()
    if not user:
        return jsonify({'error': 'no user found'}), 400

    if not Like.query.filter_by(video_id=video.id, user_id=user.id).first():
        db.session.add(Like(video_id=video.id, user_id=user.id))
        video.like_count += 1
        db.session.commit()

    return jsonify({'video_id': video.id, 'like_count': video.like_count})


@videos_bp.post('/api/videos/<int:video_id>/comments')
def add_comment(video_id: int):
    data = request.get_json(silent=True) or {}
    user = User.query.first()
    if not user:
        return jsonify({'error': 'no user found'}), 400

    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'error': 'body is required'}), 400

    comment = Comment(
        video_id=video_id,
        user_id=user.id,
        body=body,
        parent_id=data.get('parent_id'),
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({'id': comment.id, 'body': comment.body, 'created_at': comment.created_at.isoformat()}), 201


@videos_bp.get('/api/videos/<int:video_id>/comments')
def get_comments(video_id: int):
    comments = Comment.query.filter_by(video_id=video_id).order_by(Comment.created_at.desc()).all()
    payload = []
    for c in comments:
        user = User.query.get(c.user_id)
        payload.append({
            'id': c.id,
            'body': c.body,
            'parent_id': c.parent_id,
            'created_at': c.created_at.isoformat(),
            'user': user.username if user else 'unknown',
        })
    return jsonify(payload)


@videos_bp.post('/api/subscribe/<int:channel_id>')
def subscribe(channel_id: int):
    user = User.query.first()
    if not user:
        return jsonify({'error': 'no user found'}), 400

    if channel_id == user.id:
        return jsonify({'error': 'cannot subscribe to yourself'}), 400

    channel = User.query.get_or_404(channel_id)
    sub = Subscription.query.filter_by(subscriber_id=user.id, channel_id=channel.id).first()
    if not sub:
        db.session.add(Subscription(subscriber_id=user.id, channel_id=channel.id, notify_on_upload=True))
        channel.subscriber_count += 1
        db.session.commit()

    return jsonify({'channel_id': channel.id, 'subscriber_count': channel.subscriber_count})
