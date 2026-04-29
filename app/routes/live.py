from __future__ import annotations

import secrets

from flask import Blueprint, jsonify, request

from ..models import User

live_bp = Blueprint('live', __name__, url_prefix='/api/live')

_ACTIVE_STREAMS: dict[int, dict] = {}


@live_bp.post('/start')
def start_live():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'no creator available'}), 400

    ingest_key = secrets.token_urlsafe(24)
    stream_info = {
        'channel_id': user.id,
        'username': user.username,
        'rtmp_url': 'rtmp://live.nexstream.local/live',
        'ingest_key': ingest_key,
    }
    _ACTIVE_STREAMS[user.id] = stream_info
    return jsonify(stream_info), 201


@live_bp.post('/end')
def end_live():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'no creator available'}), 400

    _ACTIVE_STREAMS.pop(user.id, None)
    return jsonify({'message': 'live stream ended'})


@live_bp.get('/active')
def active_live():
    return jsonify(list(_ACTIVE_STREAMS.values()))
