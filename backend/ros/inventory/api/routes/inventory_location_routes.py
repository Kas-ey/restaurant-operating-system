"""Inventory location aggregate HTTP routes for Inventory."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import InventoryLocationService

from ..schemas import validate_create_inventory_location_payload, validate_update_inventory_location_payload
from ..serializers import inventory_location_to_dict
from . import _commit_and_respond, _require_json_body, inventory_bp


@inventory_bp.get("/locations")
@require_authenticated
@require_permission("inventory.read")
def list_locations() -> ResponseReturnValue:
    location_service = InventoryLocationService()
    models = location_service.list_locations()
    return success_response([inventory_location_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/locations/<string:location_id>")
@require_authenticated
@require_permission("inventory.read")
def get_location(location_id: str) -> ResponseReturnValue:
    location_service = InventoryLocationService()
    model = location_service.get_location(location_id)
    return success_response(inventory_location_to_dict(model), HTTPStatus.OK)


@inventory_bp.post("/locations")
@require_authenticated
@require_permission("inventory.create")
def create_location() -> ResponseReturnValue:
    location_service = InventoryLocationService()
    payload = _require_json_body()
    data = validate_create_inventory_location_payload(payload)
    model = location_service.create_location(
        location_id=data["id"],
        branch_id=data["branch_id"],
        name=data["name"],
        description=data["description"],
        location_type=data["location_type"],
    )
    return _commit_and_respond(inventory_location_to_dict(model), HTTPStatus.CREATED)


@inventory_bp.put("/locations/<string:location_id>")
@require_authenticated
@require_permission("inventory.update")
def update_location(location_id: str) -> ResponseReturnValue:
    location_service = InventoryLocationService()
    payload = _require_json_body()
    data = validate_update_inventory_location_payload(payload)
    model = location_service.update_location(
        location_id,
        branch_id=data.get("branch_id"),
        name=data.get("name"),
        description=data.get("description"),
        location_type=data.get("location_type"),
    )
    return _commit_and_respond(inventory_location_to_dict(model), HTTPStatus.OK)


@inventory_bp.delete("/locations/<string:location_id>")
@require_authenticated
@require_permission("inventory.delete")
def delete_location(location_id: str) -> ResponseReturnValue:
    location_service = InventoryLocationService()
    location_service.delete_location(location_id)
    return _commit_and_respond({"message": "Inventory location deleted."}, HTTPStatus.OK)


@inventory_bp.patch("/locations/<string:location_id>/activate")
@require_authenticated
@require_permission("inventory.update")
def activate_location(location_id: str) -> ResponseReturnValue:
    location_service = InventoryLocationService()
    model = location_service.activate_location(location_id)
    return _commit_and_respond(inventory_location_to_dict(model), HTTPStatus.OK)


@inventory_bp.patch("/locations/<string:location_id>/deactivate")
@require_authenticated
@require_permission("inventory.update")
def deactivate_location(location_id: str) -> ResponseReturnValue:
    location_service = InventoryLocationService()
    model = location_service.deactivate_location(location_id)
    return _commit_and_respond(inventory_location_to_dict(model), HTTPStatus.OK)
