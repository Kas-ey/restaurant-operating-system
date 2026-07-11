"""ROS backend package entrypoint."""

from flask import Flask

from ros.common.routes import common_bp
from ros.core.config import config
from ros.core.extensions import db, migrate
from ros.core.logging import configure_logging
from ros.http.errors import error_response
from ros.shared.exceptions import ROSException


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
    """Create and configure the ROS Flask application."""
    app = Flask(__name__)
    selected_config = _load_configuration(app, config_name)
    _validate_configuration(selected_config)
    _init_extensions(app)
    configure_logging(app)
    app.register_blueprint(common_bp)

    @app.errorhandler(ROSException)
    def handle_ros_exception(error: ROSException):
        return error_response(error.message, error.status_code)

    return app
