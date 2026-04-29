from flask import Flask
from dotenv import load_dotenv
from pathlib import Path

from .config import Config
from .extensions import db, login_manager, socketio
from .models import User
from .routes.auth import auth_bp
from .routes.live import live_bp
from .routes.stream import stream_bp
from .routes.studio import studio_bp
from .routes.videos import videos_bp


def create_app(config_object: type[Config] | None = None) -> Flask:
    load_dotenv()
    base_dir = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(base_dir / 'templates'),
        static_folder=str(base_dir / 'static'),
    )
    app.config.from_object(config_object or Config)

    base_instance = Path(app.instance_path)
    base_instance.mkdir(parents=True, exist_ok=True)
    app.config.setdefault('UPLOAD_FOLDER', str(base_instance / 'uploads'))
    app.config.setdefault('STREAM_FOLDER', str(base_instance / 'streams'))
    app.config.setdefault('THUMBNAIL_FOLDER', str(base_instance / 'thumbnails'))
    app.config.setdefault('SUBTITLE_FOLDER', str(base_instance / 'subtitles'))

    for folder_key in ('UPLOAD_FOLDER', 'STREAM_FOLDER', 'THUMBNAIL_FOLDER', 'SUBTITLE_FOLDER'):
        Path(app.config[folder_key]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(studio_bp)
    app.register_blueprint(stream_bp)
    app.register_blueprint(live_bp)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    with app.app_context():
        from . import models
        db.create_all()

    return app
