from __future__ import annotations

import json
import subprocess
from pathlib import Path


class TranscodeError(RuntimeError):
    pass


def _run_command(command: list[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise TranscodeError(completed.stderr.strip() or completed.stdout.strip() or 'Transcoding failed')


def probe_media(source_path: str) -> dict:
    command = [
        'ffprobe',
        '-v', 'error',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        source_path,
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        return {'duration': None, 'width': None, 'height': None}

    payload = json.loads(completed.stdout or '{}')
    duration = None
    if payload.get('format', {}).get('duration'):
        try:
            duration = int(float(payload['format']['duration']))
        except (TypeError, ValueError):
            duration = None

    width = None
    height = None
    for stream in payload.get('streams', []):
        if stream.get('codec_type') == 'video':
            width = stream.get('width')
            height = stream.get('height')
            break

    return {'duration': duration, 'width': width, 'height': height}


def create_thumbnail(source_path: str, thumbnail_path: str) -> None:
    Path(thumbnail_path).parent.mkdir(parents=True, exist_ok=True)
    command = [
        'ffmpeg',
        '-y',
        '-ss', '00:00:01',
        '-i', source_path,
        '-frames:v', '1',
        '-vf', 'scale=1280:-2',
        thumbnail_path,
    ]
    _run_command(command)


def build_hls_package(source_path: str, output_directory: str) -> str:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / 'index.m3u8'
    segment_pattern = output / 'segment_%03d.ts'

    command = [
        'ffmpeg',
        '-y',
        '-i', source_path,
        '-map', '0:v:0',
        '-map', '0:a:0?',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '22',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ac', '2',
        '-movflags', '+faststart',
        '-vf', 'scale=w=min(1280,iw):-2',
        '-force_key_frames', 'expr:gte(t,n_forced*4)',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod',
        '-hls_flags', 'independent_segments',
        '-hls_segment_filename', str(segment_pattern),
        str(manifest_path),
    ]
    _run_command(command)
    return str(manifest_path)
