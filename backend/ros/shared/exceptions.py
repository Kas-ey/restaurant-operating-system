class ConfigurationError(Exception):
    """Raised when application configuration is invalid."""


class ROSException(Exception):
    """Base exception for ROS application errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
