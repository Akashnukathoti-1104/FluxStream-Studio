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

Production-style local run:

```bash
waitress-serve --listen=0.0.0.0:8000 wsgi:app
```

If you prefer Flask's CLI for quick development, use:

```bash
flask --app run.py --debug run
```

## Free Deployment

The repo includes deployment files for a free host like Render.

1. Push this project to GitHub.
2. Create a new Render Web Service from the repository.
3. Use the default build command: `pip install -r requirements.txt`
4. Use the start command: `waitress-serve --listen=0.0.0.0:$PORT wsgi:app`
5. Keep the service on the free plan.

If your host reads `Procfile`, it will use the same command automatically.

## Deploy

The project is already WSGI-ready through [wsgi.py](wsgi.py). Use `wsgi:app` as the entrypoint on your host.

Recommended deploy options:

1. Render or Railway: build with `pip install -r requirements.txt`, then start with `waitress-serve --listen=0.0.0.0:$PORT wsgi:app`.
2. A Linux VM or container: install Python and FFmpeg, set environment variables if you want S3, then run the same `waitress-serve` command.
3. If your host exposes a different WSGI start command, point it at `wsgi:app`.

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

## GitHub Upload Checklist

- Commit the source files in this repository.
- Keep `instance/` out of Git because it contains runtime data and generated media.
- Add your own screenshots or demo notes if your submission requires them.
