"""Request validation schemas for organization API payloads."""

from __future__ import annotations

from datetime import date
from http import HTTPStatus

from ros.shared.exceptions import ROSException


def validate_create_organization_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "legal_name": _require_string(payload, "legal_name"),
        "registration_number": _require_string(payload, "registration_number"),
        "tax_number": _require_string(payload, "tax_number"),
        "email": _require_string(payload, "email"),
        "phone": _require_string(payload, "phone"),
    }


def validate_update_organization_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "legal_name", "registration_number", "tax_number", "email", "phone"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_branch_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "organization_id": _require_string(payload, "organization_id"),
        "name": _require_string(payload, "name"),
        "code": _require_string(payload, "code"),
        "address": _require_string(payload, "address"),
        "city": _require_string(payload, "city"),
        "country": _require_string(payload, "country"),
        "phone": _require_string(payload, "phone"),
        "email": _require_string(payload, "email"),
    }


def validate_update_branch_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "code", "address", "city", "country", "phone", "email"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_department_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "branch_id": _require_string(payload, "branch_id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
    }


def validate_update_department_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "description"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_position_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
    }


def validate_update_position_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "description"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_employee_payload(payload: dict) -> dict:
    data = {
        "id": _require_string(payload, "id"),
        "branch_id": _require_string(payload, "branch_id"),
        "department_id": _require_string(payload, "department_id"),
        "position_id": _require_string(payload, "position_id"),
        "employee_number": _require_string(payload, "employee_number"),
        "first_name": _require_string(payload, "first_name"),
        "last_name": _require_string(payload, "last_name"),
        "phone": _require_string(payload, "phone"),
        "email": _require_string(payload, "email"),
        "hire_date": _require_date(payload, "hire_date"),
    }

    user_id = payload.get("user_id")
    if user_id is None:
        data["user_id"] = None
    elif isinstance(user_id, str) and user_id.strip():
        data["user_id"] = user_id.strip()
    else:
        raise ROSException("Field 'user_id' must be a non-empty string when provided.", HTTPStatus.BAD_REQUEST)

    return data


def validate_update_employee_payload(payload: dict) -> dict:
    allowed = {"first_name", "last_name", "phone", "email", "hire_date"}
    data = _validate_update_payload(payload, allowed)
    result: dict = {}
    for key in data:
        if key == "hire_date":
            result[key] = _require_date(payload, key)
        else:
            result[key] = _require_string(payload, key)
    return result


def validate_assign_user_payload(payload: dict) -> dict[str, str]:
    return {"user_id": _require_string(payload, "user_id")}


def validate_transfer_branch_payload(payload: dict) -> dict[str, str]:
    return {
        "branch_id": _require_string(payload, "branch_id"),
        "department_id": _require_string(payload, "department_id"),
    }


def validate_transfer_department_payload(payload: dict) -> dict[str, str]:
    return {"department_id": _require_string(payload, "department_id")}


def validate_change_position_payload(payload: dict) -> dict[str, str]:
    return {"position_id": _require_string(payload, "position_id")}


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


def _require_date(payload: dict, field_name: str) -> date:
    value = _require_string(payload, field_name)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ROSException(f"Field '{field_name}' must be a valid ISO date.", HTTPStatus.BAD_REQUEST) from exc
