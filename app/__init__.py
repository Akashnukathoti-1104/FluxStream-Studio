from flask import Flask
from dotenv import load_dotenv
from pathlib import Path

from .config import Config
from .extensions import db
from .routes.main import main_bp


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

    for folder_key in ('UPLOAD_FOLDER', 'STREAM_FOLDER', 'THUMBNAIL_FOLDER'):
        Path(app.config[folder_key]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(main_bp)

    with app.app_context():
        from . import models
        db.create_all()

    return app
