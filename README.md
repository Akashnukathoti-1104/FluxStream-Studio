# FluxStream Studio

FluxStream Studio is an advanced Flask-based video platform for uploading, transcoding, streaming, and managing media libraries. It uses SQLite for metadata, FFmpeg for thumbnail generation and HLS packaging, and optional AWS S3 mirroring for source uploads.

## Features

- Upload single video files through a polished dashboard
- Automatically generate HLS segments for browser playback
- Create thumbnails and media metadata with FFmpeg and ffprobe
- Search, filter, inspect, and delete uploaded videos
- Optional AWS S3 storage for mirrored source assets
- Responsive interface with a premium dark visual design

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- FFmpeg / ffprobe
- AWS S3 via boto3
- HTML, CSS, JavaScript

## Project Structure

- `app/` Flask application package
- `templates/` Jinja templates
- `static/` UI assets
- `instance/` runtime uploads, HLS output, thumbnails, and SQLite database
- `run.py` development entry point

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file and customize it if needed:

```bash
copy .env.example .env
```

4. Install FFmpeg so `ffmpeg` and `ffprobe` are available on your PATH.
5. Start the app. The secret key is created automatically in `instance/secret_key.txt` the first time you run it if `SECRET_KEY` is not set.

## Run Locally

Windows or macOS development:

```bash
python run.py
```

If you prefer Flask's CLI for quick development, use:

```bash
flask --app run.py --debug run
```

## Runtime Notes

The app runs locally with Flask during development. For quick startup, use:

```bash
flask --app run.py --debug run
```

## Deploy On Render

This project is set up for Render's native Python runtime. Render already provides `ffmpeg` in the native runtime tools, so you can deploy without Docker.

1. Create a new Render Web Service from this repository.
2. Use the provided `render.yaml`, or enter these values manually:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
3. Keep the attached disk mounted at `/opt/render/project/src/instance`.
4. Set `SECRET_KEY` in the Render environment if you want a fixed app secret.

## AWS S3 Optional Configuration

If you want mirrored source uploads in S3, set these environment variables:

- `S3_BUCKET`
- `S3_REGION`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_SOURCE_PREFIX`

When S3 is not configured, the platform uses local disk storage and still works fully.

## Important Runtime Notes

- The app generates and stores a secret key automatically if `SECRET_KEY` is not provided.
- Keep the `instance/` folder on the server because it stores uploads, generated streams, thumbnails, the database, and the generated secret key.
- Do not commit `instance/` to Git if you want a clean repository.

## Notes

- Videos are transcoded into an HLS package stored under `instance/streams/`.
- The browser player uses HLS.js for wide compatibility.
- The SQLite database is created automatically on startup.

