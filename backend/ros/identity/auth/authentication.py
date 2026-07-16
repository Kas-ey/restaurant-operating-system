"""Authentication workflows for identity login and current-user resolution."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus

from ros.identity.auth.jwt import generate_access_token, token_expires_in_seconds, validate_access_token
from ros.identity.auth.password import verify_password
from ros.identity.persistence.models import UserModel
from ros.identity.persistence.repositories import UserRepository
from ros.shared.exceptions import ROSException


@dataclass(frozen=True)
class AuthenticationResult:
    """Structured authentication output for API serialization."""

    access_token: str
    token_type: str
    expires_in: int


class AuthenticationService:
    """Coordinates authentication workflows without HTTP concerns."""

    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self._user_repository = user_repository or UserRepository()

    def login(self, email: str, password: str) -> AuthenticationResult:
        """Authenticate credentials and return JWT token data."""
        normalized_email = self._require_text(email, "Email is required.").lower()
        normalized_password = self._require_text(password, "Password is required.")

        user = self._user_repository.get_by_email(normalized_email)
        if user is None or not verify_password(normalized_password, user.password_hash):
            raise ROSException("Invalid credentials.", HTTPStatus.UNAUTHORIZED)

        if not user.is_active:
            raise ROSException("Invalid credentials.", HTTPStatus.UNAUTHORIZED)

        return AuthenticationResult(
            access_token=generate_access_token(user.id, user.email),
            token_type="Bearer",
            expires_in=token_expires_in_seconds(),
        )

    def logout(self) -> None:
        """Perform stateless logout behavior for the current request."""
        return None

    def resolve_current_user(self, token: str) -> UserModel:
        """Resolve and return the current authenticated user from a JWT token."""
        claims = validate_access_token(token)
        user_id = claims.get("sub")
        if not isinstance(user_id, str) or not user_id.strip():
            raise ROSException("Invalid authentication token.", HTTPStatus.UNAUTHORIZED)

        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise ROSException("Invalid authentication token.", HTTPStatus.UNAUTHORIZED)

        return user

    @staticmethod
    def extract_bearer_token(authorization_header: str | None) -> str:
        """Extract a bearer token from an Authorization header."""
        if not authorization_header:
            raise ROSException("Authentication required.", HTTPStatus.UNAUTHORIZED)

        parts = authorization_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            raise ROSException("Authentication required.", HTTPStatus.UNAUTHORIZED)
        return parts[1].strip()

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized
