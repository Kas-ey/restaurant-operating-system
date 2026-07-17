"""Category aggregate HTTP routes for Inventory."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import InventoryCategoryService

from ..schemas import validate_create_inventory_category_payload, validate_update_inventory_category_payload
from ..serializers import inventory_category_to_dict
from . import _commit_and_respond, _require_json_body, inventory_bp


@inventory_bp.get("/categories")
@require_authenticated
@require_permission("inventory.read")
def list_categories() -> ResponseReturnValue:
    category_service = InventoryCategoryService()
    models = category_service.list_categories()
    return success_response([inventory_category_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/categories/<string:category_id>")
@require_authenticated
@require_permission("inventory.read")
def get_category(category_id: str) -> ResponseReturnValue:
    category_service = InventoryCategoryService()
    model = category_service.get_category(category_id)
    return success_response(inventory_category_to_dict(model), HTTPStatus.OK)


@inventory_bp.post("/categories")
@require_authenticated
@require_permission("inventory.create")
def create_category() -> ResponseReturnValue:
    category_service = InventoryCategoryService()
    payload = _require_json_body()
    data = validate_create_inventory_category_payload(payload)
    model = category_service.create_category(
        category_id=data["id"],
        name=data["name"],
        description=data["description"],
    )
    return _commit_and_respond(inventory_category_to_dict(model), HTTPStatus.CREATED)


@inventory_bp.put("/categories/<string:category_id>")
@require_authenticated
@require_permission("inventory.update")
def update_category(category_id: str) -> ResponseReturnValue:
    category_service = InventoryCategoryService()
    payload = _require_json_body()
    data = validate_update_inventory_category_payload(payload)
    model = category_service.update_category(
        category_id,
        name=data.get("name"),
        description=data.get("description"),
    )
    return _commit_and_respond(inventory_category_to_dict(model), HTTPStatus.OK)


@inventory_bp.delete("/categories/<string:category_id>")
@require_authenticated
@require_permission("inventory.delete")
def delete_category(category_id: str) -> ResponseReturnValue:
    category_service = InventoryCategoryService()
    category_service.delete_category(category_id)
    return _commit_and_respond({"message": "Inventory category deleted."}, HTTPStatus.OK)


@inventory_bp.patch("/categories/<string:category_id>/activate")
@require_authenticated
@require_permission("inventory.update")
def activate_category(category_id: str) -> ResponseReturnValue:
    category_service = InventoryCategoryService()
    model = category_service.activate_category(category_id)
    return _commit_and_respond(inventory_category_to_dict(model), HTTPStatus.OK)


@inventory_bp.patch("/categories/<string:category_id>/deactivate")
@require_authenticated
@require_permission("inventory.update")
def deactivate_category(category_id: str) -> ResponseReturnValue:
    category_service = InventoryCategoryService()
    model = category_service.deactivate_category(category_id)
    return _commit_and_respond(inventory_category_to_dict(model), HTTPStatus.OK)
