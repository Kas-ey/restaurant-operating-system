"""JWT token generation and validation helpers for authentication."""

from __future__ import annotations

from http import HTTPStatus
from datetime import UTC, datetime, timedelta
from typing import Any

from flask import current_app
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from ros.shared.exceptions import ROSException


def generate_access_token(user_id: str, email: str) -> str:
    """Generate a signed JWT access token for the authenticated user."""
    issued_at = datetime.now(tz=UTC)
    expires_at = issued_at + timedelta(minutes=_token_expiration_minutes())

    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    try:
        return jwt.encode(payload, _jwt_secret_key(), algorithm="HS256")
    except Exception as exc:
        raise ROSException("Failed to generate authentication token.", HTTPStatus.INTERNAL_SERVER_ERROR) from exc


def validate_access_token(token: str) -> dict[str, Any]:
    """Validate a JWT token and return its claims."""
    try:
        payload = jwt.decode(token, _jwt_secret_key(), algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise ROSException("Invalid authentication token.", HTTPStatus.UNAUTHORIZED) from exc
    except InvalidTokenError as exc:
        raise ROSException("Invalid authentication token.", HTTPStatus.UNAUTHORIZED) from exc

    for claim in ("sub", "iat", "exp"):
        if claim not in payload:
            raise ROSException("Invalid authentication token.", HTTPStatus.UNAUTHORIZED)

    return payload


def token_expires_in_seconds() -> int:
    """Return configured access-token lifetime in seconds."""
    return _token_expiration_minutes() * 60


def _token_expiration_minutes() -> int:
    value = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60)
    try:
        minutes = int(value)
    except (TypeError, ValueError) as exc:
        raise ROSException("Invalid JWT expiration configuration.", HTTPStatus.INTERNAL_SERVER_ERROR) from exc
    if minutes <= 0:
        raise ROSException("Invalid JWT expiration configuration.", HTTPStatus.INTERNAL_SERVER_ERROR)
    return minutes


def _jwt_secret_key() -> str:
    secret = str(current_app.config.get("JWT_SECRET_KEY", "")).strip()
    if not secret:
        raise ROSException("Missing JWT secret key configuration.", HTTPStatus.INTERNAL_SERVER_ERROR)
    return secret
