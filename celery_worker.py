from app import create_app
from app.tasks import create_celery_app

flask_app = create_app()
celery = create_celery_app(flask_app)

# Import tasks so Celery discovers them.
from app.tasks import ai, analytics, transcode  # noqa: E402,F401
