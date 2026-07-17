"""Stock adjustment HTTP routes for Inventory."""

from __future__ import annotations

from http import HTTPStatus

from flask import request
from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import StockAdjustmentService
from ros.inventory.persistence.models import InventoryNegativePolicyEnum

from ..schemas import (
    validate_adjustment_date_query,
    validate_create_stock_adjustment_payload,
)
from ..serializers import stock_adjustment_to_dict
from . import _commit_and_respond, _require_json_body, inventory_bp


@inventory_bp.get("/adjustments")
@require_authenticated
@require_permission("inventory.read")
def list_adjustments() -> ResponseReturnValue:
    adjustment_service = StockAdjustmentService()
    models = adjustment_service.list_adjustments()
    return success_response([stock_adjustment_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/adjustments/<string:adjustment_id>")
@require_authenticated
@require_permission("inventory.read")
def get_adjustment(adjustment_id: str) -> ResponseReturnValue:
    adjustment_service = StockAdjustmentService()
    model = adjustment_service.get_adjustment(adjustment_id)
    return success_response(stock_adjustment_to_dict(model), HTTPStatus.OK)


@inventory_bp.post("/adjustments")
@require_authenticated
@require_permission("inventory.create")
def create_adjustment() -> ResponseReturnValue:
    adjustment_service = StockAdjustmentService()
    payload = _require_json_body()
    data = validate_create_stock_adjustment_payload(payload)
    model = adjustment_service.create_adjustment(
        adjustment_id=data["id"],
        inventory_item_id=data["inventory_item_id"],
        inventory_location_id=data["inventory_location_id"],
        inventory_lot_id=data.get("inventory_lot_id"),
        actual_quantity=data["actual_quantity"],
        adjustment_type=data.get("adjustment_type"),
        reason=data["reason"],
        approved_by=data.get("approved_by"),
        performed_by=data["performed_by"],
        notes=data.get("notes"),
        negative_policy=data.get("negative_policy") or InventoryNegativePolicyEnum.STRICT.value,
        approving_manager=data.get("approving_manager"),
        approval_reason=data.get("approval_reason"),
        approval_timestamp=data.get("approval_timestamp"),
    )
    return _commit_and_respond(stock_adjustment_to_dict(model), HTTPStatus.CREATED)


@inventory_bp.get("/items/<string:item_id>/adjustments")
@require_authenticated
@require_permission("inventory.read")
def list_adjustments_by_item(item_id: str) -> ResponseReturnValue:
    adjustment_service = StockAdjustmentService()
    models = adjustment_service.list_adjustments_by_item(item_id)
    return success_response([stock_adjustment_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/adjustments/date-range")
@require_authenticated
@require_permission("inventory.read")
def list_adjustments_by_date_range() -> ResponseReturnValue:
    adjustment_service = StockAdjustmentService()
    start_at, end_at = validate_adjustment_date_query(
        request.args.get("start_at"),
        request.args.get("end_at"),
    )
    models = adjustment_service.list_adjustments_by_date_range(start_at=start_at, end_at=end_at)
    return success_response([stock_adjustment_to_dict(model) for model in models], HTTPStatus.OK)
