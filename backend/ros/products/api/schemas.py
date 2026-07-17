"""Request validation schemas for products API payloads."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.shared.exceptions import ROSException


def validate_create_category_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
    }


def validate_update_category_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "description"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_product_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "sku": _require_string(payload, "sku"),
        "description": _require_string(payload, "description"),
        "category_id": _require_string(payload, "category_id"),
    }


def validate_update_product_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "sku", "description", "category_id"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_variant_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "sku": _require_string(payload, "sku"),
        "description": _require_string(payload, "description"),
        "display_order": _require_non_negative_int(payload, "display_order"),
        "is_default": _require_bool(payload, "is_default", default=False),
    }


def validate_update_variant_payload(payload: dict) -> dict:
    allowed = {"name", "sku", "description", "display_order", "is_default"}
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "sku" in data:
        validated["sku"] = _require_string(payload, "sku")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "display_order" in data:
        validated["display_order"] = _require_non_negative_int(payload, "display_order")
    if "is_default" in data:
        validated["is_default"] = _require_bool(payload, "is_default")
    return validated


def validate_create_modifier_group_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
        "selection_type": _require_string(payload, "selection_type"),
        "minimum_required": _require_non_negative_int(payload, "minimum_required"),
        "maximum_allowed": _require_non_negative_int(payload, "maximum_allowed"),
        "display_order": _require_non_negative_int(payload, "display_order"),
        "is_required": _require_bool(payload, "is_required", default=False),
    }


def validate_update_modifier_group_payload(payload: dict) -> dict:
    allowed = {
        "name",
        "description",
        "selection_type",
        "minimum_required",
        "maximum_allowed",
        "display_order",
        "is_required",
    }
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "selection_type" in data:
        validated["selection_type"] = _require_string(payload, "selection_type")
    if "minimum_required" in data:
        validated["minimum_required"] = _require_non_negative_int(payload, "minimum_required")
    if "maximum_allowed" in data:
        validated["maximum_allowed"] = _require_non_negative_int(payload, "maximum_allowed")
    if "display_order" in data:
        validated["display_order"] = _require_non_negative_int(payload, "display_order")
    if "is_required" in data:
        validated["is_required"] = _require_bool(payload, "is_required")
    return validated


def validate_create_modifier_option_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
        "display_order": _require_non_negative_int(payload, "display_order"),
        "is_default": _require_bool(payload, "is_default", default=False),
    }


def validate_update_modifier_option_payload(payload: dict) -> dict:
    allowed = {"name", "description", "display_order", "is_default"}
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "display_order" in data:
        validated["display_order"] = _require_non_negative_int(payload, "display_order")
    if "is_default" in data:
        validated["is_default"] = _require_bool(payload, "is_default")
    return validated


def validate_create_product_price_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "amount": _require_positive_number(payload, "amount"),
        "currency": _require_currency(payload, "currency"),
        "effective_from": _require_optional_date(payload, "effective_from"),
        "effective_to": _require_optional_date(payload, "effective_to"),
        "is_active": _require_bool(payload, "is_active", default=True),
    }


def validate_update_product_price_payload(payload: dict) -> dict:
    allowed = {"amount", "currency", "effective_from", "effective_to", "is_active"}
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "amount" in data:
        validated["amount"] = _require_positive_number(payload, "amount")
    if "currency" in data:
        validated["currency"] = _require_currency(payload, "currency")
    if "effective_from" in data:
        validated["effective_from"] = _require_optional_date(payload, "effective_from")
    if "effective_to" in data:
        validated["effective_to"] = _require_optional_date(payload, "effective_to")
    if "is_active" in data:
        validated["is_active"] = _require_bool(payload, "is_active")
    return validated


def validate_create_variant_price_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "amount": _require_positive_number(payload, "amount"),
        "currency": _require_currency(payload, "currency"),
        "effective_from": _require_optional_date(payload, "effective_from"),
        "effective_to": _require_optional_date(payload, "effective_to"),
        "is_active": _require_bool(payload, "is_active", default=True),
    }


def validate_update_variant_price_payload(payload: dict) -> dict:
    allowed = {"amount", "currency", "effective_from", "effective_to", "is_active"}
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "amount" in data:
        validated["amount"] = _require_positive_number(payload, "amount")
    if "currency" in data:
        validated["currency"] = _require_currency(payload, "currency")
    if "effective_from" in data:
        validated["effective_from"] = _require_optional_date(payload, "effective_from")
    if "effective_to" in data:
        validated["effective_to"] = _require_optional_date(payload, "effective_to")
    if "is_active" in data:
        validated["is_active"] = _require_bool(payload, "is_active")
    return validated


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


def _require_non_negative_int(payload: dict, field_name: str) -> int:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    if not isinstance(value, int) or value < 0:
        raise ROSException(f"Field '{field_name}' must be a non-negative integer.", HTTPStatus.BAD_REQUEST)
    return value


def _require_bool(payload: dict, field_name: str, default: bool | None = None) -> bool:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    if field_name not in payload:
        if default is None:
            raise ROSException(f"Field '{field_name}' is required.", HTTPStatus.BAD_REQUEST)
        return default

    value = payload.get(field_name)
    if not isinstance(value, bool):
        raise ROSException(f"Field '{field_name}' must be a boolean.", HTTPStatus.BAD_REQUEST)
    return value


def _require_positive_number(payload: dict, field_name: str) -> str:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    if not isinstance(value, (int, float, str)):
        raise ROSException(f"Field '{field_name}' must be a positive number.", HTTPStatus.BAD_REQUEST)

    text_value = str(value).strip()
    if not text_value:
        raise ROSException(f"Field '{field_name}' must be a positive number.", HTTPStatus.BAD_REQUEST)

    try:
        numeric_value = Decimal(text_value)
    except (InvalidOperation, ValueError) as exc:
        raise ROSException(f"Field '{field_name}' must be a positive number.", HTTPStatus.BAD_REQUEST) from exc

    if not numeric_value.is_finite():
        raise ROSException(f"Field '{field_name}' must be a positive number.", HTTPStatus.BAD_REQUEST)

    if numeric_value <= 0:
        raise ROSException(f"Field '{field_name}' must be greater than zero.", HTTPStatus.BAD_REQUEST)
    return text_value


def _require_currency(payload: dict, field_name: str) -> str:
    value = _require_string(payload, field_name).upper()
    if len(value) != 3 or not value.isalpha():
        raise ROSException(f"Field '{field_name}' must be a 3-letter currency code.", HTTPStatus.BAD_REQUEST)
    return value


def _require_optional_date(payload: dict, field_name: str) -> date | None:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    if field_name not in payload or payload.get(field_name) is None:
        return None

    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ROSException(f"Field '{field_name}' must be an ISO date string.", HTTPStatus.BAD_REQUEST)
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ROSException(f"Field '{field_name}' must be an ISO date string.", HTTPStatus.BAD_REQUEST) from exc
