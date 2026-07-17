"""Inventory item aggregate HTTP routes for Inventory."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import InventoryItemService

from ..schemas import validate_create_inventory_item_payload, validate_update_inventory_item_payload
from ..serializers import inventory_item_to_dict
from . import _commit_and_respond, _require_json_body, inventory_bp


@inventory_bp.get("/items")
@require_authenticated
@require_permission("inventory.read")
def list_items() -> ResponseReturnValue:
    item_service = InventoryItemService()
    models = item_service.list_items()
    return success_response([inventory_item_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/items/<string:item_id>")
@require_authenticated
@require_permission("inventory.read")
def get_item(item_id: str) -> ResponseReturnValue:
    item_service = InventoryItemService()
    model = item_service.get_item(item_id)
    return success_response(inventory_item_to_dict(model), HTTPStatus.OK)


@inventory_bp.post("/items")
@require_authenticated
@require_permission("inventory.create")
def create_item() -> ResponseReturnValue:
    item_service = InventoryItemService()
    payload = _require_json_body()
    data = validate_create_inventory_item_payload(payload)
    model = item_service.create_item(
        item_id=data["id"],
        name=data["name"],
        sku=data["sku"],
        description=data["description"],
        category_id=data["category_id"],
        unit_of_measure_id=data["unit_of_measure_id"],
        minimum_stock=data["minimum_stock"],
        maximum_stock=data["maximum_stock"],
        reorder_level=data["reorder_level"],
    )
    return _commit_and_respond(inventory_item_to_dict(model), HTTPStatus.CREATED)


@inventory_bp.put("/items/<string:item_id>")
@require_authenticated
@require_permission("inventory.update")
def update_item(item_id: str) -> ResponseReturnValue:
    item_service = InventoryItemService()
    payload = _require_json_body()
    data = validate_update_inventory_item_payload(payload)
    model = item_service.update_item(
        item_id,
        name=data.get("name"),
        sku=data.get("sku"),
        description=data.get("description"),
        category_id=data.get("category_id"),
        unit_of_measure_id=data.get("unit_of_measure_id"),
        minimum_stock=data.get("minimum_stock"),
        maximum_stock=data.get("maximum_stock"),
        reorder_level=data.get("reorder_level"),
    )
    return _commit_and_respond(inventory_item_to_dict(model), HTTPStatus.OK)


@inventory_bp.delete("/items/<string:item_id>")
@require_authenticated
@require_permission("inventory.delete")
def delete_item(item_id: str) -> ResponseReturnValue:
    item_service = InventoryItemService()
    item_service.delete_item(item_id)
    return _commit_and_respond({"message": "Inventory item deleted."}, HTTPStatus.OK)


@inventory_bp.patch("/items/<string:item_id>/activate")
@require_authenticated
@require_permission("inventory.update")
def activate_item(item_id: str) -> ResponseReturnValue:
    item_service = InventoryItemService()
    model = item_service.activate_item(item_id)
    return _commit_and_respond(inventory_item_to_dict(model), HTTPStatus.OK)


@inventory_bp.patch("/items/<string:item_id>/deactivate")
@require_authenticated
@require_permission("inventory.update")
def deactivate_item(item_id: str) -> ResponseReturnValue:
    item_service = InventoryItemService()
    model = item_service.deactivate_item(item_id)
    return _commit_and_respond(inventory_item_to_dict(model), HTTPStatus.OK)
