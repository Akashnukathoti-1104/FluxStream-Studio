from __future__ import annotations

from flask import Blueprint, abort, jsonify, redirect

from ..models import Video

stream_bp = Blueprint('stream', __name__, url_prefix='/stream')


@stream_bp.get('/<int:video_id>/playlist.m3u8')
def master_playlist(video_id: int):
    video = Video.query.get_or_404(video_id)
    if video.hls_playlist_url:
        return redirect(video.hls_playlist_url)
    return jsonify({'video_id': video.id, 'message': 'master playlist placeholder'}), 200


@stream_bp.get('/<int:video_id>/<quality>.m3u8')
def quality_playlist(video_id: int, quality: str):
    if quality not in {'360p', '720p', '1080p', '4k'}:
        abort(404)
    return jsonify({'video_id': video_id, 'quality': quality, 'message': 'quality playlist placeholder'}), 200


@stream_bp.get('/<int:video_id>/<segment>.ts')
def stream_segment(video_id: int, segment: str):
    return jsonify({'video_id': video_id, 'segment': segment, 'message': 'segment placeholder (serve via CloudFront in production)'}), 200
