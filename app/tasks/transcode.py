from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

from . import create_celery_app
from .. import create_app
from ..extensions import db, socketio
from ..models import Video
from ..services.storage import get_s3_client, cloudfront_signed_url

flask_app = create_app()
celery = create_celery_app(flask_app)


@celery.task(name='tasks.transcode_video')
def transcode_video(video_id: int, s3_key_raw: str):
    video = Video.query.get(video_id)
    if not video:
        return {'error': 'video not found'}

    client = get_s3_client(flask_app)
    bucket = flask_app.config.get('RAW_BUCKET') or flask_app.config.get('S3_BUCKET')
    processed_prefix = flask_app.config.get('S3_PROCESSED_PREFIX', 'nexstream/processed')

    workdir = Path(tempfile.mkdtemp(prefix=f'nexstream_{video_id}_'))
    try:
        local_raw = workdir / 'source'
        # download raw from S3
        if client and bucket and s3_key_raw:
            client.download_file(bucket, s3_key_raw, str(local_raw))
        else:
            # if not on S3, assume local path
            local_raw = Path(s3_key_raw)

        # transcode variants and HLS
        variants = [
            {'name': '360p', 'height': 360, 'bandwidth': 800000},
            {'name': '720p', 'height': 720, 'bandwidth': 2500000},
            {'name': '1080p', 'height': 1080, 'bandwidth': 5000000},
        ]

        master_lines = ['#EXTM3U', '#EXT-X-VERSION:3']

        for v in variants:
            out_dir = workdir / v['name']
            out_dir.mkdir(parents=True, exist_ok=True)
            variant_playlist = out_dir / 'index.m3u8'
            # build hls for this variant
            ff_cmd = [
                'ffmpeg', '-y', '-i', str(local_raw),
                '-vf', f"scale=-2:{v['height']}",
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                '-b:v', str(int(v['bandwidth']/1000)) + 'k',
                '-hls_time', '6', '-hls_playlist_type', 'vod',
                '-hls_segment_filename', str(out_dir / 'seg_%03d.ts'),
                str(variant_playlist)
            ]
            subprocess.run(ff_cmd, check=True)

            # upload variant files to S3
            # upload playlist and segments
            s3_base = f"{processed_prefix}/{video.id}/{v['name']}"
            uploaded_playlist_key = f"{s3_base}/index.m3u8"
            client_bucket = flask_app.config.get('CDN_BUCKET') or flask_app.config.get('RAW_BUCKET') or flask_app.config.get('S3_BUCKET')
            for f in out_dir.iterdir():
                if f.is_file():
                    client.upload_file(str(f), client_bucket, f"{s3_base}/{f.name}")

            # add entry to master playlist
            master_lines.append(f'#EXT-X-STREAM-INF:BANDWIDTH={v["bandwidth"]},RESOLUTION=1920x{v["height"]}')
            master_lines.append(f'{v["name"]}/index.m3u8')

            # set model fields for mp4/variant (point to playlist for HLS)
            if v['name'] == '720p':
                video.s3_key_720p = f"{s3_base}/index.m3u8"
            if v['name'] == '1080p':
                video.s3_key_1080p = f"{s3_base}/index.m3u8"
            if v['name'] == '360p':
                video.s3_key_4k = video.s3_key_4k or ''

        # write master playlist
        master = workdir / 'master.m3u8'
        master.write_text('\n'.join(master_lines), encoding='utf-8')
        master_s3_key = f"{processed_prefix}/{video.id}/master.m3u8"
        client.upload_file(str(master), client_bucket, master_s3_key)

        # set HLS URL using CloudFront-signed helper if available
        video.hls_playlist_url = cloudfront_signed_url(flask_app, master_s3_key)
        video.status = 'live'
        db.session.commit()

        socketio.emit('video.processing.complete', {'video_id': video.id, 'status': video.status})
        return {'video_id': video.id, 'status': video.status}
    except subprocess.CalledProcessError as exc:
        video.status = 'error'
        video.error_message = str(exc)
        db.session.commit()
        socketio.emit('video.processing.failed', {'video_id': video.id, 'error': str(exc)})
        raise
    finally:
        try:
            shutil.rmtree(workdir)
        except Exception:
            pass
