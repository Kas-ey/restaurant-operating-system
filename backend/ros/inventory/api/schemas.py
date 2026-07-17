"""Request validation schemas for inventory API payloads."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.shared.exceptions import ROSException


def validate_create_inventory_category_payload(payload: dict) -> dict[str, str]:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
    }


def validate_update_inventory_category_payload(payload: dict) -> dict[str, str]:
    allowed = {"name", "description"}
    data = _validate_update_payload(payload, allowed)
    return {key: _require_string(payload, key) for key in data}


def validate_create_unit_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "symbol": _require_string(payload, "symbol"),
        "description": _require_string(payload, "description"),
        "precision": _require_non_negative_int(payload, "precision"),
    }


def validate_update_unit_payload(payload: dict) -> dict:
    allowed = {"name", "symbol", "description", "precision"}
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "symbol" in data:
        validated["symbol"] = _require_string(payload, "symbol")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "precision" in data:
        validated["precision"] = _require_non_negative_int(payload, "precision")
    return validated


def validate_create_inventory_item_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "name": _require_string(payload, "name"),
        "sku": _require_string(payload, "sku"),
        "description": _require_string(payload, "description"),
        "category_id": _require_string(payload, "category_id"),
        "unit_of_measure_id": _require_string(payload, "unit_of_measure_id"),
        "minimum_stock": _require_non_negative_decimal(payload, "minimum_stock"),
        "maximum_stock": _require_non_negative_decimal(payload, "maximum_stock"),
        "reorder_level": _require_non_negative_decimal(payload, "reorder_level"),
    }


def validate_update_inventory_item_payload(payload: dict) -> dict:
    allowed = {
        "name",
        "sku",
        "description",
        "category_id",
        "unit_of_measure_id",
        "minimum_stock",
        "maximum_stock",
        "reorder_level",
    }
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "sku" in data:
        validated["sku"] = _require_string(payload, "sku")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "category_id" in data:
        validated["category_id"] = _require_string(payload, "category_id")
    if "unit_of_measure_id" in data:
        validated["unit_of_measure_id"] = _require_string(payload, "unit_of_measure_id")
    if "minimum_stock" in data:
        validated["minimum_stock"] = _require_non_negative_decimal(payload, "minimum_stock")
    if "maximum_stock" in data:
        validated["maximum_stock"] = _require_non_negative_decimal(payload, "maximum_stock")
    if "reorder_level" in data:
        validated["reorder_level"] = _require_non_negative_decimal(payload, "reorder_level")
    return validated


def validate_create_inventory_lot_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "lot_number": _require_string(payload, "lot_number"),
        "received_date": _require_date(payload, "received_date"),
        "expiry_date": _require_optional_date(payload, "expiry_date"),
        "quantity": _require_non_negative_decimal(payload, "quantity"),
        "supplier_reference": _require_string(payload, "supplier_reference"),
        "notes": _require_string(payload, "notes"),
    }


def validate_update_inventory_lot_payload(payload: dict) -> dict:
    allowed = {
        "lot_number",
        "received_date",
        "expiry_date",
        "quantity",
        "supplier_reference",
        "notes",
    }
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "lot_number" in data:
        validated["lot_number"] = _require_string(payload, "lot_number")
    if "received_date" in data:
        validated["received_date"] = _require_date(payload, "received_date")
    if "expiry_date" in data:
        validated["expiry_date"] = _require_optional_date(payload, "expiry_date")
    if "quantity" in data:
        validated["quantity"] = _require_non_negative_decimal(payload, "quantity")
    if "supplier_reference" in data:
        validated["supplier_reference"] = _require_string(payload, "supplier_reference")
    if "notes" in data:
        validated["notes"] = _require_string(payload, "notes")
    return validated


def validate_create_inventory_location_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "branch_id": _require_string(payload, "branch_id"),
        "name": _require_string(payload, "name"),
        "description": _require_string(payload, "description"),
        "location_type": _require_string(payload, "location_type"),
    }


def validate_update_inventory_location_payload(payload: dict) -> dict:
    allowed = {"branch_id", "name", "description", "location_type"}
    data = _validate_update_payload(payload, allowed)
    validated: dict = {}
    if "branch_id" in data:
        validated["branch_id"] = _require_string(payload, "branch_id")
    if "name" in data:
        validated["name"] = _require_string(payload, "name")
    if "description" in data:
        validated["description"] = _require_string(payload, "description")
    if "location_type" in data:
        validated["location_type"] = _require_string(payload, "location_type")
    return validated


def validate_create_movement_payload(payload: dict) -> dict:
    return {
        "movement_type": _require_string(payload, "movement_type"),
        "inventory_item_id": _require_string(payload, "inventory_item_id"),
        "location_id": _require_string(payload, "location_id"),
        "quantity": _require_positive_decimal(payload, "quantity"),
        "lot_id": _require_optional_string(payload, "lot_id"),
        "reference_type": _require_string(payload, "reference_type"),
        "reference_id": _require_string(payload, "reference_id"),
        "reference_number": _require_optional_string(payload, "reference_number"),
        "performed_by": _require_string(payload, "performed_by"),
        "reason": _require_optional_string(payload, "reason"),
        "transaction_id": _require_optional_string(payload, "transaction_id"),
        "negative_policy": _require_optional_string(payload, "negative_policy"),
        "approving_manager": _require_optional_string(payload, "approving_manager"),
        "approval_reason": _require_optional_string(payload, "approval_reason"),
        "approval_timestamp": _require_optional_datetime(payload, "approval_timestamp"),
    }


def validate_create_stock_adjustment_payload(payload: dict) -> dict:
    return {
        "id": _require_string(payload, "id"),
        "inventory_item_id": _require_string(payload, "inventory_item_id"),
        "inventory_location_id": _require_string(payload, "inventory_location_id"),
        "inventory_lot_id": _require_optional_string(payload, "inventory_lot_id"),
        "actual_quantity": _require_positive_decimal(payload, "actual_quantity"),
        "adjustment_type": _require_optional_string(payload, "adjustment_type"),
        "reason": _require_string(payload, "reason"),
        "approved_by": _require_optional_string(payload, "approved_by"),
        "performed_by": _require_string(payload, "performed_by"),
        "notes": _require_optional_string(payload, "notes"),
        "negative_policy": _require_optional_string(payload, "negative_policy"),
        "approving_manager": _require_optional_string(payload, "approving_manager"),
        "approval_reason": _require_optional_string(payload, "approval_reason"),
        "approval_timestamp": _require_optional_datetime(payload, "approval_timestamp"),
    }


def validate_transaction_date_query(start_at: str | None, end_at: str | None) -> tuple[datetime | None, datetime | None]:
    parsed_start = _parse_optional_query_datetime(start_at, "start_at")
    parsed_end = _parse_optional_query_datetime(end_at, "end_at")
    if parsed_start is not None and parsed_end is not None and parsed_start > parsed_end:
        raise ROSException("Query parameter 'start_at' cannot be after 'end_at'.", HTTPStatus.BAD_REQUEST)
    return parsed_start, parsed_end


def validate_adjustment_date_query(start_at: str | None, end_at: str | None) -> tuple[datetime | None, datetime | None]:
    return validate_transaction_date_query(start_at, end_at)


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


def _require_non_negative_decimal(payload: dict, field_name: str) -> str:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ROSException(f"Field '{field_name}' must be a non-negative decimal.", HTTPStatus.BAD_REQUEST) from exc

    if not decimal_value.is_finite() or decimal_value < 0:
        raise ROSException(f"Field '{field_name}' must be a non-negative decimal.", HTTPStatus.BAD_REQUEST)

    return str(decimal_value)


def _require_positive_decimal(payload: dict, field_name: str) -> str:
    value = _require_non_negative_decimal(payload, field_name)
    if Decimal(value) <= 0:
        raise ROSException(f"Field '{field_name}' must be greater than zero.", HTTPStatus.BAD_REQUEST)
    return value


def _require_date(payload: dict, field_name: str) -> date:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ROSException(f"Field '{field_name}' is required.", HTTPStatus.BAD_REQUEST)

    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ROSException(f"Field '{field_name}' must be an ISO date.", HTTPStatus.BAD_REQUEST) from exc


def _require_optional_date(payload: dict, field_name: str) -> date | None:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)

    if field_name not in payload or payload.get(field_name) is None:
        return None

    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ROSException(f"Field '{field_name}' must be an ISO date or null.", HTTPStatus.BAD_REQUEST)

    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ROSException(f"Field '{field_name}' must be an ISO date or null.", HTTPStatus.BAD_REQUEST) from exc


def _require_optional_string(payload: dict, field_name: str) -> str | None:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    if field_name not in payload or payload.get(field_name) is None:
        return None
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ROSException(f"Field '{field_name}' must be a non-empty string or null.", HTTPStatus.BAD_REQUEST)
    return value.strip()


def _require_optional_datetime(payload: dict, field_name: str) -> datetime | None:
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    if field_name not in payload or payload.get(field_name) is None:
        return None
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ROSException(f"Field '{field_name}' must be an ISO datetime string or null.", HTTPStatus.BAD_REQUEST)
    return _parse_query_datetime(value.strip(), field_name)


def _parse_optional_query_datetime(value: str | None, field_name: str) -> datetime | None:
    if value is None or not value.strip():
        return None
    return _parse_query_datetime(value.strip(), field_name)


def _parse_query_datetime(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ROSException(f"Query parameter '{field_name}' must be an ISO datetime.", HTTPStatus.BAD_REQUEST) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed
