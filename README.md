# NexStream 2.0

NexStream 2.0 is an AI-powered video streaming platform scaffold built with Flask, SQLAlchemy, Celery, Redis, FFmpeg-oriented task flows, and modular API blueprints.

## Stack

- Backend: Flask, Flask-Login, Flask-SocketIO, SQLAlchemy
- Jobs: Celery + Redis
- Video pipeline: FFmpeg task stubs for multi-quality/HLS workflow
- Storage: AWS S3/CloudFront ready configuration
- AI hooks: Whisper and AI thumbnail task stubs
- DB: SQLite (default) and PostgreSQL-ready via `DATABASE_URL`
- Frontend: Vanilla JS, Chart.js, HLS.js, cinematic dark UI

## Project Layout

- `app/__init__.py`: Flask factory and blueprint registration
- `app/models.py`: User/Video/Playlist/Comment/Like/Subscription/WatchHistory/Analytics
- `app/routes/auth.py`: register/login/google callback placeholders
- `app/routes/videos.py`: dashboard, watch/upload pages, video APIs, comments, likes, subscribe
- `app/routes/studio.py`: studio page and analytics APIs
- `app/routes/stream.py`: HLS stream endpoints (placeholder routing)
- `app/routes/live.py`: live stream API start/end/active
- `app/tasks/`: Celery task stubs for transcode, AI, and analytics
- `seed.py`: seeds creator + 6 sample videos + analytics rows
- `docker-compose.yml`: web + worker + redis + nginx-rtmp

## Key Endpoints

- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/google/callback`
- Videos: `/api/videos`, `/api/videos/<id>`, `/api/videos/upload`, `/api/videos/upload/<job_id>/status`
- Studio: `/api/studio/dashboard`, `/api/studio/analytics`, `/api/studio/videos`
- Social: `/api/videos/<id>/like`, `/api/videos/<id>/comments`, `/api/subscribe/<channel_id>`
- Live: `/api/live/start`, `/api/live/end`, `/api/live/active`
- Health: `/healthz`

## Local Run

1. Create/activate virtualenv.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Seed sample data:

```bash
python seed.py
```

4. Run Flask app:

```bash
python run.py
```

5. Open:

- Dashboard: `http://127.0.0.1:5000/`
- Studio: `http://127.0.0.1:5000/studio`
- Upload: `http://127.0.0.1:5000/upload`

## Render

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
- Health Check Path: `/healthz`
- Persistent Disk Mount: `/opt/render/project/src/instance`

## Notes

This is a production-style scaffold. The heavy AI and FFmpeg/S3/CloudFront flows are wired as task placeholders so you can swap in real credentials and worker infra without restructuring the app.
