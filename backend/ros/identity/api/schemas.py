"""Request validation schemas for identity API payloads."""

from __future__ import annotations

from http import HTTPStatus

from ros.shared.exceptions import ROSException


def validate_create_user_payload(payload: dict) -> dict[str, str]:
    """Validate and normalize a create-user payload."""
    return {
        "id": _require_string(payload, "id"),
        "email": _require_string(payload, "email"),
        "full_name": _require_string(payload, "full_name"),
        "password": _require_string(payload, "password"),
    }


def validate_update_user_payload(payload: dict) -> dict[str, str]:
    """Validate and normalize an update-user payload."""
    allowed = {"email", "full_name", "password"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_role_payload(payload: dict) -> dict[str, str]:
    """Validate and normalize a create-role payload."""
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
    }


def validate_update_role_payload(payload: dict) -> dict[str, str]:
    """Validate and normalize an update-role payload."""
    allowed = {"name", "description"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_permission_payload(payload: dict) -> dict[str, str]:
    """Validate and normalize a create-permission payload."""
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
    }


def validate_update_permission_payload(payload: dict) -> dict[str, str]:
    """Validate and normalize an update-permission payload."""
    allowed = {"name", "description"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_login_payload(payload: dict) -> dict[str, str]:
    """Validate and normalize a login payload."""
    return {
        "email": _require_string(payload, "email"),
        "password": _require_string(payload, "password"),
    }


def _validate_update_payload(payload: dict, allowed_fields: set[str]) -> set[str]:
    if not isinstance(payload, dict) or not payload:
        raise ROSException("Request body must be a non-empty JSON object.", HTTPStatus.BAD_REQUEST)

    invalid_fields = set(payload.keys()) - allowed_fields
    if invalid_fields:
        raise ROSException("Request body contains unsupported fields.", HTTPStatus.BAD_REQUEST)
    return set(payload.keys())


def _require_string(payload: dict, field_name: str) -> str:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ROSException(f"Field '{field_name}' is required.", HTTPStatus.BAD_REQUEST)
    return value.strip()
