"""Inventory lot aggregate HTTP routes for Inventory."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import InventoryLotService

from ..schemas import validate_create_inventory_lot_payload, validate_update_inventory_lot_payload
from ..serializers import inventory_lot_to_dict
from . import _commit_and_respond, _require_json_body, inventory_bp


_UNSET = object()


@inventory_bp.get("/items/<string:item_id>/lots")
@require_authenticated
@require_permission("inventory.read")
def list_lots(item_id: str) -> ResponseReturnValue:
    lot_service = InventoryLotService()
    models = lot_service.list_lots(item_id)
    return success_response([inventory_lot_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/lots/<string:lot_id>")
@require_authenticated
@require_permission("inventory.read")
def get_lot(lot_id: str) -> ResponseReturnValue:
    lot_service = InventoryLotService()
    model = lot_service.get_lot(lot_id)
    return success_response(inventory_lot_to_dict(model), HTTPStatus.OK)


@inventory_bp.post("/items/<string:item_id>/lots")
@require_authenticated
@require_permission("inventory.create")
def create_lot(item_id: str) -> ResponseReturnValue:
    lot_service = InventoryLotService()
    payload = _require_json_body()
    data = validate_create_inventory_lot_payload(payload)
    model = lot_service.create_lot(
        lot_id=data["id"],
        inventory_item_id=item_id,
        lot_number=data["lot_number"],
        received_date=data["received_date"],
        expiry_date=data.get("expiry_date"),
        quantity=data["quantity"],
        supplier_reference=data["supplier_reference"],
        notes=data["notes"],
    )
    return _commit_and_respond(inventory_lot_to_dict(model), HTTPStatus.CREATED)


@inventory_bp.put("/lots/<string:lot_id>")
@require_authenticated
@require_permission("inventory.update")
def update_lot(lot_id: str) -> ResponseReturnValue:
    lot_service = InventoryLotService()
    payload = _require_json_body()
    data = validate_update_inventory_lot_payload(payload)
    model = lot_service.update_lot(
        lot_id,
        lot_number=data.get("lot_number"),
        received_date=data.get("received_date"),
        expiry_date=data["expiry_date"] if "expiry_date" in data else _UNSET,
        quantity=data.get("quantity"),
        supplier_reference=data.get("supplier_reference"),
        notes=data.get("notes"),
    )
    return _commit_and_respond(inventory_lot_to_dict(model), HTTPStatus.OK)


@inventory_bp.delete("/lots/<string:lot_id>")
@require_authenticated
@require_permission("inventory.delete")
def delete_lot(lot_id: str) -> ResponseReturnValue:
    lot_service = InventoryLotService()
    lot_service.delete_lot(lot_id)
    return _commit_and_respond({"message": "Inventory lot deleted."}, HTTPStatus.OK)
