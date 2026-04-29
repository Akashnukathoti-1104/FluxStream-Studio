from __future__ import annotations

from datetime import datetime, timezone
from .extensions import db


class Video(db.Model):
    __tablename__ = 'videos'

    id = db.Column(db.String(32), primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    original_filename = db.Column(db.String(255), nullable=False)
    source_path = db.Column(db.String(600), nullable=False)
    source_key = db.Column(db.String(600), nullable=True)
    stream_directory = db.Column(db.String(600), nullable=False)
    thumbnail_path = db.Column(db.String(600), nullable=True)
    storage_backend = db.Column(db.String(32), nullable=False, default='local')
    status = db.Column(db.String(32), nullable=False, default='processing')
    error_message = db.Column(db.Text, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def resolution(self) -> str:
        if self.width and self.height:
            return f'{self.width} x {self.height}'
        return 'Unknown'

    def duration_label(self) -> str:
        if not self.duration_seconds:
            return 'Processing'
        minutes, seconds = divmod(int(self.duration_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f'{hours:d}:{minutes:02d}:{seconds:02d}'
        return f'{minutes:d}:{seconds:02d}'

    def size_label(self) -> str:
        if not self.file_size:
            return 'Unknown'
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024 or unit == 'TB':
                return f'{size:.1f} {unit}' if unit != 'B' else f'{int(size)} B'
            size /= 1024
        return f'{size:.1f} B'
