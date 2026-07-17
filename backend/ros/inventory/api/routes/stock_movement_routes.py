"""Inventory engine movement HTTP routes for integration contracts."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import StockMovementEngine
from ros.inventory.persistence.models import InventoryNegativePolicyEnum

from ..schemas import validate_create_movement_payload
from ..serializers import stock_movement_result_to_dict
from . import _commit_and_respond, _require_json_body, inventory_bp


@inventory_bp.post("/movements")
@require_authenticated
@require_permission("inventory.create")
def create_movement() -> ResponseReturnValue:
    movement_engine = StockMovementEngine()
    payload = _require_json_body()
    data = validate_create_movement_payload(payload)
    result = movement_engine.move_stock(
        movement_type=data["movement_type"],
        inventory_item_id=data["inventory_item_id"],
        location_id=data["location_id"],
        quantity=data["quantity"],
        lot_id=data.get("lot_id"),
        reference_type=data["reference_type"],
        reference_id=data["reference_id"],
        reference_number=data.get("reference_number"),
        performed_by=data["performed_by"],
        reason=data.get("reason"),
        transaction_id=data.get("transaction_id"),
        negative_policy=data.get("negative_policy") or InventoryNegativePolicyEnum.STRICT.value,
        approving_manager=data.get("approving_manager"),
        approval_reason=data.get("approval_reason"),
        approval_timestamp=data.get("approval_timestamp"),
    )
    return _commit_and_respond(stock_movement_result_to_dict(result), HTTPStatus.CREATED)
