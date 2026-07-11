from flask import Flask

from app.core.config import config
from app.core.extensions import db, migrate


def _load_configuration(app: Flask, config_name: str | None = None) -> type:
    selected_config = config.get(config_name or "development", config["development"])
    app.config.from_object(selected_config)
    return selected_config


def _validate_configuration(config_class: type) -> None:
    config_class.validate()


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    selected_config = _load_configuration(app, config_name)
    _validate_configuration(selected_config)
    _init_extensions(app)
    return app
