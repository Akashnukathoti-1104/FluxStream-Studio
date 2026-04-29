from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, send_file, url_for)
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Video
from ..services.storage import delete_s3_object, mirror_source_to_s3, s3_is_enabled
from ..services.transcoder import TranscodeError, build_hls_package, create_thumbnail, probe_media

main_bp = Blueprint('main', __name__)
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'mkv', 'webm', 'm4v', 'avi', 'flv'}


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _safe_title(filename: str) -> str:
    name = Path(filename).stem.replace('_', ' ').replace('-', ' ').strip()
    if not name:
        return 'Untitled Video'
    return re.sub(r'\s+', ' ', name).title()


def _video_status_counts() -> dict[str, int]:
    counts = dict(db.session.query(Video.status, func.count(Video.id)).group_by(Video.status).all())
    return {
        'total': Video.query.count(),
        'ready': counts.get('ready', 0),
        'processing': counts.get('processing', 0),
        'failed': counts.get('failed', 0),
    }


def _store_video_file(video: Video, upload_file) -> tuple[str, str]:
    upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
    upload_folder.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(upload_file.filename)
    unique_name = f'{video.id}_{filename}'
    local_path = upload_folder / unique_name
    upload_file.save(str(local_path))

    file_size = local_path.stat().st_size
    object_key = None
    if s3_is_enabled(current_app):
        object_key = f"{current_app.config['S3_SOURCE_PREFIX']}/{video.id}/{unique_name}"
        mirror_source_to_s3(current_app, str(local_path), object_key)
    return str(local_path), object_key, file_size


@main_bp.route('/')
def dashboard():
    search = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')

    query = Video.query.order_by(Video.created_at.desc())
    if search:
        like = f'%{search}%'
        query = query.filter(or_(Video.title.ilike(like), Video.description.ilike(like), Video.original_filename.ilike(like)))
    if status != 'all':
        query = query.filter(Video.status == status)

    videos = query.all()
    stats = _video_status_counts()
    featured = videos[0] if videos else None
    return render_template('dashboard.html', videos=videos, stats=stats, featured=featured, search=search, status=status)


@main_bp.route('/upload', methods=['GET', 'POST'], strict_slashes=False)
def upload():
    if request.method == 'POST':
        upload_file = request.files.get('video')
        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()

        if not upload_file or upload_file.filename == '':
            flash('Choose a video file to upload.', 'error')
            return redirect(url_for('main.upload'))

        if not _allowed_file(upload_file.filename):
            flash('Unsupported file type. Use MP4, MOV, MKV, WEBM, M4V, AVI, or FLV.', 'error')
            return redirect(url_for('main.upload'))

        video = Video(
            id=uuid.uuid4().hex,
            title=title or _safe_title(upload_file.filename),
            description=description,
            original_filename=secure_filename(upload_file.filename),
            source_path='',
            source_key=None,
            stream_directory='',
            thumbnail_path=None,
            storage_backend='s3' if s3_is_enabled(current_app) else 'local',
            status='processing',
        )
        db.session.add(video)
        db.session.commit()

        try:
            source_path, source_key, file_size = _store_video_file(video, upload_file)
            video.source_path = source_path
            video.source_key = source_key
            video.file_size = file_size

            stream_directory = Path(current_app.config['STREAM_FOLDER']) / video.id
            thumbnail_path = Path(current_app.config['THUMBNAIL_FOLDER']) / f'{video.id}.jpg'

            media_info = probe_media(source_path)
            create_thumbnail(source_path, str(thumbnail_path))
            build_hls_package(source_path, str(stream_directory))

            video.stream_directory = str(stream_directory)
            video.thumbnail_path = str(thumbnail_path)
            video.duration_seconds = media_info.get('duration')
            video.width = media_info.get('width')
            video.height = media_info.get('height')
            video.status = 'ready'
            db.session.commit()
            flash(f'Video {video.title} is ready to stream.', 'success')
            return redirect(url_for('main.video_detail', video_id=video.id))
        except TranscodeError as exc:
            video.status = 'failed'
            video.error_message = str(exc)
            db.session.commit()
            flash(f'Upload saved but processing failed: {exc}', 'error')
            return redirect(url_for('main.video_detail', video_id=video.id))
        except Exception as exc:  # pragma: no cover - defensive guard for runtime failures
            video.status = 'failed'
            video.error_message = str(exc)
            db.session.commit()
            flash(f'Unexpected upload failure: {exc}', 'error')
            return redirect(url_for('main.video_detail', video_id=video.id))

    return render_template('upload.html')


@main_bp.route('/videos/<video_id>')
def video_detail(video_id: str):
    video = Video.query.get_or_404(video_id)
    stream_manifest_url = url_for('main.stream_asset', video_id=video.id, filename='index.m3u8')
    download_url = url_for('main.download_video', video_id=video.id)
    return render_template('video_detail.html', video=video, stream_manifest_url=stream_manifest_url, download_url=download_url)


@main_bp.route('/videos/<video_id>/delete', methods=['POST'])
def delete_video(video_id: str):
    video = Video.query.get_or_404(video_id)
    delete_s3_object(current_app, video.source_key)

    for path_value in [video.source_path, video.thumbnail_path]:
        if path_value and Path(path_value).exists():
            Path(path_value).unlink(missing_ok=True)

    if video.stream_directory and Path(video.stream_directory).exists():
        shutil.rmtree(video.stream_directory, ignore_errors=True)

    db.session.delete(video)
    db.session.commit()
    flash('Video removed from the dashboard.', 'success')
    return redirect(url_for('main.dashboard'))


@main_bp.route('/videos/<video_id>/download')
def download_video(video_id: str):
    video = Video.query.get_or_404(video_id)
    if not video.source_path or not Path(video.source_path).exists():
        abort(404)
    return send_file(video.source_path, as_attachment=True, download_name=video.original_filename)


@main_bp.route('/videos/<video_id>/thumbnail')
def thumbnail_video(video_id: str):
    video = Video.query.get_or_404(video_id)
    if not video.thumbnail_path or not Path(video.thumbnail_path).exists():
        abort(404)
    return send_file(video.thumbnail_path, mimetype='image/jpeg', conditional=True)


@main_bp.route('/videos/<video_id>/stream/<path:filename>')
def stream_asset(video_id: str, filename: str):
    video = Video.query.get_or_404(video_id)
    if not video.stream_directory:
        abort(404)

    asset_path = Path(video.stream_directory) / filename
    if not asset_path.exists():
        abort(404)

    mimetype = 'application/vnd.apple.mpegurl' if asset_path.suffix == '.m3u8' else None
    return send_file(asset_path, mimetype=mimetype, conditional=True)
