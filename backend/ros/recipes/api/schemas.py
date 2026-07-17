"""Request validation schemas for recipes API payloads."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.shared.exceptions import ROSException


def validate_create_recipe_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "product_id": _require_string(payload, "product_id"),
        "code": _require_string(payload, "code").upper(),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
        "security_classification": _require_string(payload, "security_classification").upper(),
    }


def validate_update_recipe_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "description", "security_classification"}
    data = _validate_update_payload(payload, allowed)
    validated: dict[str, str] = {}
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "security_classification" in data:
        validated["security_classification"] = _require_string(payload, "security_classification").upper()
    return validated


def validate_create_version_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "change_summary": _require_string(payload, "change_summary"),
        "effective_date": _require_optional_date(payload, "effective_date"),
    }


def validate_review_action_payload(payload: dict) -> dict[str, str]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    return {}


def validate_create_ingredient_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "ingredient_type": _require_string(payload, "ingredient_type").upper(),
        "inventory_item_id": _require_optional_string(payload, "inventory_item_id"),
        "recipe_id": _require_optional_string(payload, "recipe_id"),
        "secret_formulation_id": _require_optional_string(payload, "secret_formulation_id"),
        "quantity": _require_decimal(payload, "quantity"),
        "unit_of_measure_id": _require_string(payload, "unit_of_measure_id"),
        "tolerance": _require_decimal(payload, "tolerance", allow_negative=False, default=Decimal("0")),
        "display_order": _require_non_negative_int(payload, "display_order"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_update_ingredient_payload(payload: dict) -> dict:
    allowed = {
        "ingredient_type",
        "inventory_item_id",
        "recipe_id",
        "secret_formulation_id",
        "quantity",
        "unit_of_measure_id",
        "tolerance",
        "display_order",
        "notes",
    }
    _validate_update_payload(payload, allowed)
    # Update uses complete replacement to preserve the single-reference invariant.
    return validate_create_ingredient_payload(payload)


def validate_create_secret_formulation_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "code": _require_string(payload, "code").upper(),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
        "security_classification": _require_string(payload, "security_classification").upper(),
        "payload": _require_string(payload, "payload"),
    }


def validate_update_secret_formulation_payload(payload: dict) -> dict:
    allowed = {"name", "description", "security_classification", "payload"}
    data = _validate_update_payload(payload, allowed)
    if "payload" not in data:
        raise ROSException("Field 'payload' is required.", HTTPStatus.BAD_REQUEST)

    validated: dict[str, str] = {"payload": _require_string(payload, "payload")}
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "security_classification" in data:
        validated["security_classification"] = _require_string(payload, "security_classification").upper()
    return validated


def validate_secret_formulation_decrypt_payload(payload: dict) -> dict:
    return {
        "reason": _require_string(payload, "reason"),
        "request_timestamp": _require_datetime(payload, "request_timestamp"),
        "organization_id": _require_string(payload, "organization_id"),
        "branch_id": _require_string(payload, "branch_id"),
        "recipe_id": _require_string(payload, "recipe_id"),
        "recipe_version_id": _require_string(payload, "recipe_version_id"),
    }


def validate_create_step_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "step_number": _require_positive_int(payload, "step_number"),
        "title": _require_string(payload, "title"),
        "description": _require_string(payload, "description"),
        "estimated_duration": _require_non_negative_int(payload, "estimated_duration"),
        "temperature_min": _require_optional_decimal(payload, "temperature_min"),
        "temperature_max": _require_optional_decimal(payload, "temperature_max"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_update_step_payload(payload: dict) -> dict:
    allowed = {"step_number", "title", "description", "estimated_duration", "temperature_min", "temperature_max", "notes"}
    _validate_update_payload(payload, allowed)
    return {
        "step_number": _require_positive_int(payload, "step_number"),
        "title": _require_string(payload, "title"),
        "description": _require_string(payload, "description"),
        "estimated_duration": _require_non_negative_int(payload, "estimated_duration"),
        "temperature_min": _require_optional_decimal(payload, "temperature_min"),
        "temperature_max": _require_optional_decimal(payload, "temperature_max"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_create_yield_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "expected_quantity": _require_decimal(payload, "expected_quantity"),
        "unit_of_measure_id": _require_string(payload, "unit_of_measure_id"),
        "expected_portions": _require_positive_int(payload, "expected_portions"),
        "portion_weight": _require_decimal(payload, "portion_weight"),
        "yield_percentage": _require_percentage(payload, "yield_percentage"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_update_yield_payload(payload: dict) -> dict:
    allowed = {"expected_quantity", "unit_of_measure_id", "expected_portions", "portion_weight", "yield_percentage", "notes"}
    _validate_update_payload(payload, allowed)
    return {
        "expected_quantity": _require_decimal(payload, "expected_quantity"),
        "unit_of_measure_id": _require_string(payload, "unit_of_measure_id"),
        "expected_portions": _require_positive_int(payload, "expected_portions"),
        "portion_weight": _require_decimal(payload, "portion_weight"),
        "yield_percentage": _require_percentage(payload, "yield_percentage"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_create_waste_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "inventory_item_id": _require_string(payload, "inventory_item_id"),
        "expected_loss_quantity": _require_decimal(payload, "expected_loss_quantity"),
        "loss_percentage": _require_percentage(payload, "loss_percentage"),
        "reason": _require_string(payload, "reason"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_update_waste_payload(payload: dict) -> dict:
    allowed = {"inventory_item_id", "expected_loss_quantity", "loss_percentage", "reason", "notes"}
    _validate_update_payload(payload, allowed)
    return {
        "inventory_item_id": _require_string(payload, "inventory_item_id"),
        "expected_loss_quantity": _require_decimal(payload, "expected_loss_quantity"),
        "loss_percentage": _require_percentage(payload, "loss_percentage"),
        "reason": _require_string(payload, "reason"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_create_equipment_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "equipment_name": _require_string(payload, "equipment_name"),
        "quantity_required": _require_decimal(payload, "quantity_required"),
        "mandatory": _require_bool(payload, "mandatory", default=True),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_update_equipment_payload(payload: dict) -> dict:
    allowed = {"equipment_name", "quantity_required", "mandatory", "notes"}
    _validate_update_payload(payload, allowed)
    return {
        "equipment_name": _require_string(payload, "equipment_name"),
        "quantity_required": _require_decimal(payload, "quantity_required"),
        "mandatory": _require_bool(payload, "mandatory", default=True),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_create_packaging_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "inventory_item_id": _require_string(payload, "inventory_item_id"),
        "quantity": _require_decimal(payload, "quantity"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_update_packaging_payload(payload: dict) -> dict:
    allowed = {"inventory_item_id", "quantity", "notes"}
    _validate_update_payload(payload, allowed)
    return {
        "inventory_item_id": _require_string(payload, "inventory_item_id"),
        "quantity": _require_decimal(payload, "quantity"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_create_quality_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "metric": _require_string(payload, "metric"),
        "minimum_value": _require_optional_decimal(payload, "minimum_value"),
        "maximum_value": _require_optional_decimal(payload, "maximum_value"),
        "target_value": _require_optional_decimal(payload, "target_value"),
        "unit": _require_optional_string(payload, "unit"),
        "notes": _require_optional_string(payload, "notes"),
    }


def validate_update_quality_payload(payload: dict) -> dict:
    allowed = {"metric", "minimum_value", "maximum_value", "target_value", "unit", "notes"}
    _validate_update_payload(payload, allowed)
    return {
        "metric": _require_string(payload, "metric"),
        "minimum_value": _require_optional_decimal(payload, "minimum_value"),
        "maximum_value": _require_optional_decimal(payload, "maximum_value"),
        "target_value": _require_optional_decimal(payload, "target_value"),
        "unit": _require_optional_string(payload, "unit"),
        "notes": _require_optional_string(payload, "notes"),
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


def _require_optional_string(payload: dict, field_name: str) -> str | None:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ROSException(f"Field '{field_name}' must be a string.", HTTPStatus.BAD_REQUEST)
    normalized = value.strip()
    return normalized or None


def _require_decimal(
    payload: dict,
    field_name: str,
    *,
    allow_negative: bool = False,
    default: Decimal | None = None,
) -> Decimal:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    if field_name not in payload:
        if default is not None:
            return default
        raise ROSException(f"Field '{field_name}' is required.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc

    if not parsed.is_finite():
        raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST)
    if parsed == 0 and field_name == "quantity":
        raise ROSException("Field 'quantity' must be greater than zero.", HTTPStatus.BAD_REQUEST)
    if parsed < 0 and not allow_negative:
        raise ROSException(f"Field '{field_name}' cannot be negative.", HTTPStatus.BAD_REQUEST)
    return parsed


def _require_non_negative_int(payload: dict, field_name: str) -> int:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    value = payload.get(field_name)
    if not isinstance(value, int) or value < 0:
        raise ROSException(f"Field '{field_name}' must be a non-negative integer.", HTTPStatus.BAD_REQUEST)
    return value


def _require_positive_int(payload: dict, field_name: str) -> int:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    value = payload.get(field_name)
    if not isinstance(value, int) or value <= 0:
        raise ROSException(f"Field '{field_name}' must be a positive integer.", HTTPStatus.BAD_REQUEST)
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


def _require_percentage(payload: dict, field_name: str) -> Decimal:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc

    if not parsed.is_finite() or parsed < 0 or parsed > 100:
        raise ROSException(f"Field '{field_name}' must be between 0 and 100.", HTTPStatus.BAD_REQUEST)
    return parsed


def _require_optional_decimal(payload: dict, field_name: str) -> Decimal | None:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    if field_name not in payload or payload.get(field_name) is None:
        return None

    value = payload.get(field_name)
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc

    if not parsed.is_finite():
        raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST)
    return parsed


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


def _require_datetime(payload: dict, field_name: str) -> datetime:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ROSException(f"Field '{field_name}' is required.", HTTPStatus.BAD_REQUEST)

    raw_value = value.strip()
    try:
        if raw_value.endswith("Z"):
            raw_value = f"{raw_value[:-1]}+00:00"
        parsed = datetime.fromisoformat(raw_value)
    except ValueError as exc:
        raise ROSException(f"Field '{field_name}' must be an ISO datetime string.", HTTPStatus.BAD_REQUEST) from exc

    if parsed.tzinfo is None:
        raise ROSException(f"Field '{field_name}' must include timezone information.", HTTPStatus.BAD_REQUEST)
    return parsed
