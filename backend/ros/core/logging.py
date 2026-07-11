import logging

from flask import Flask


def configure_logging(app: Flask) -> None:
    """Configure the Flask application logger with a single stream handler."""
    level_name = app.config.get("LOG_LEVEL", "INFO")
    if level_name is None:
        level_name = "INFO"

    if isinstance(level_name, str):
        level_name = level_name.upper()
    else:
        raise ValueError(
            f"Invalid LOG_LEVEL {level_name!r}. Expected one of: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET."
        )

    valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
    if level_name not in valid_levels:
        raise ValueError(
            f"Invalid LOG_LEVEL {level_name!r}. Expected one of: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET."
        )

    level = getattr(logging, level_name)

    existing_handler = None
    for handler in app.logger.handlers:
        if isinstance(handler, logging.StreamHandler) and getattr(handler, "_ros_logging_handler", False):
            existing_handler = handler
            break

    if existing_handler is None:
        handler = logging.StreamHandler()
        handler._ros_logging_handler = True
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

    app.logger.setLevel(level)
    app.logger.propagate = False

    app.logger.info("Logging initialized.")
