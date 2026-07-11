"""ROS backend package entrypoint."""

from flask import Flask

from app import create_app as create_app_impl
from ros.core.logging import configure_logging


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the ROS Flask application."""
    app = create_app_impl(config_name)
    configure_logging(app)
    return app
