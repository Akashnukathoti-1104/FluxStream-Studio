#!/usr/bin/env python3
"""Download small sample videos and optionally seed them into the app.

Run from the project root: `python scripts/fetch_samples.py`.
Set environment variables for S3 if you want the script to upload raw files and trigger processing.
"""
import urllib.request
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models import User, Video
from app.services.storage import s3_is_enabled, mirror_source_to_s3


SAMPLES = [
    ('big_buck_bunny_720p_10s.mp4', 'https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4'),
    ('small.mp4', 'https://sample-videos.com/video123/mp4/240/big_buck_bunny_240p_1mb.mp4'),
]


def main():
    app = create_app()
    app.app_context().push()

    inst = Path(app.config['UPLOAD_FOLDER'])
    inst.mkdir(parents=True, exist_ok=True)

    user = User.query.first()
    if not user:
        user = User(username='sample', email='sample@example.com', password_hash='')
        db.session.add(user)
        db.session.commit()

    for name, url in SAMPLES:
        dest = inst / name
        print('Downloading', url)
        urllib.request.urlretrieve(url, dest)
        print('Saved to', dest)

        video = Video(
            user_id=user.id,
            title=name,
            description='Sample video',
            status='uploading',
            thumbnail_url='https://picsum.photos/seed/sample/1280/720',
        )
        db.session.add(video)
        db.session.commit()

        # mirror to S3 if enabled
        if s3_is_enabled(app):
            key = f"{app.config.get('S3_SOURCE_PREFIX')}/{video.id}/{name}"
            mirror_source_to_s3(app, str(dest), key)
            video.s3_key_raw = key
            video.status = 'processing'
            db.session.commit()
            print('Mirrored to S3 as', key)
        else:
            video.s3_key_raw = str(dest)
            video.status = 'processing'
            db.session.commit()

        print('Created Video', video.id)

    print('Done.')


if __name__ == '__main__':
    main()
