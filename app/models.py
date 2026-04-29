from __future__ import annotations

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False, default='')
    avatar_url = db.Column(db.String(600), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='viewer')
    subscriber_count = db.Column(db.Integer, nullable=False, default=0)
    plan = db.Column(db.String(20), nullable=False, default='free')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash or '', password)


class Video(TimestampMixin, db.Model):
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    embed_url = db.Column(db.String(500), nullable=False, default='')
    tags = db.Column(db.String(300), nullable=False, default='')
    category = db.Column(db.String(80), nullable=False, default='General')
    s3_key_raw = db.Column(db.String(600), nullable=True)
    s3_key_720p = db.Column(db.String(600), nullable=True)
    s3_key_1080p = db.Column(db.String(600), nullable=True)
    s3_key_4k = db.Column(db.String(600), nullable=True)
    hls_playlist_url = db.Column(db.String(900), nullable=True)
    subtitle_url = db.Column(db.String(900), nullable=True)
    thumbnail_url = db.Column(db.String(900), nullable=True)
    ai_thumbnail_url = db.Column(db.String(900), nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    resolution = db.Column(db.String(40), nullable=True)
    file_size_bytes = db.Column(db.BigInteger, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='uploading')
    view_count = db.Column(db.BigInteger, nullable=False, default=0)
    like_count = db.Column(db.BigInteger, nullable=False, default=0)
    is_live = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = db.relationship('User', backref='videos')


class Playlist(TimestampMixin, db.Model):
    __tablename__ = 'playlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    thumbnail_url = db.Column(db.String(900), nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=True)


class PlaylistVideo(db.Model):
    __tablename__ = 'playlist_videos'

    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), primary_key=True)
    position = db.Column(db.Integer, nullable=False, default=0)


class Comment(TimestampMixin, db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)


class Like(db.Model):
    __tablename__ = 'likes'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    subscriber_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    notify_on_upload = db.Column(db.Boolean, nullable=False, default=True)


class WatchHistory(db.Model):
    __tablename__ = 'watch_history'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), primary_key=True)
    watch_percent = db.Column(db.Float, nullable=False, default=0.0)
    last_watched_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Analytics(db.Model):
    __tablename__ = 'analytics'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    views = db.Column(db.Integer, nullable=False, default=0)
    watch_minutes = db.Column(db.Integer, nullable=False, default=0)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    ctr = db.Column(db.Float, nullable=False, default=0.0)
    revenue_usd = db.Column(db.Float, nullable=False, default=0.0)
