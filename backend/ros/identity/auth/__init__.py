"""Authentication and authorization interfaces for the identity module."""

from .authentication import AuthenticationResult, AuthenticationService
from .authorization import require_authenticated, require_permission
from .password import hash_password, verify_password

__all__ = [
    "AuthenticationResult",
    "AuthenticationService",
    "require_authenticated",
    "require_permission",
    "hash_password",
    "verify_password",
]
