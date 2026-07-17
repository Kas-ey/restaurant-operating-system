"""Modifier group aggregate HTTP routes for Products."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.products.application import ModifierGroupService

from ..schemas import validate_create_modifier_group_payload, validate_update_modifier_group_payload
from ..serializers import modifier_group_to_dict
from . import _commit_and_respond, _require_json_body, products_bp


@products_bp.get("/products/<string:product_id>/modifier-groups")
@require_authenticated
@require_permission("products.read")
def list_modifier_groups(product_id: str) -> ResponseReturnValue:
    group_service = ModifierGroupService()
    models = group_service.list_groups(product_id)
    return success_response([modifier_group_to_dict(model) for model in models], HTTPStatus.OK)


@products_bp.post("/products/<string:product_id>/modifier-groups")
@require_authenticated
@require_permission("products.create")
def create_modifier_group(product_id: str) -> ResponseReturnValue:
    group_service = ModifierGroupService()
    payload = _require_json_body()
    data = validate_create_modifier_group_payload(payload)
    model = group_service.create_group(
        group_id=data["id"],
        product_id=product_id,
        name=data["name"],
        description=data["description"],
        selection_type=data["selection_type"],
        minimum_required=data["minimum_required"],
        maximum_allowed=data["maximum_allowed"],
        display_order=data["display_order"],
        is_required=data["is_required"],
    )
    return _commit_and_respond(modifier_group_to_dict(model), HTTPStatus.CREATED)


@products_bp.put("/modifier-groups/<string:group_id>")
@require_authenticated
@require_permission("products.update")
def update_modifier_group(group_id: str) -> ResponseReturnValue:
    group_service = ModifierGroupService()
    payload = _require_json_body()
    data = validate_update_modifier_group_payload(payload)
    model = group_service.update_group(
        group_id,
        name=data.get("name"),
        description=data.get("description"),
        selection_type=data.get("selection_type"),
        minimum_required=data.get("minimum_required"),
        maximum_allowed=data.get("maximum_allowed"),
        display_order=data.get("display_order"),
        is_required=data.get("is_required"),
    )
    return _commit_and_respond(modifier_group_to_dict(model), HTTPStatus.OK)


@products_bp.delete("/modifier-groups/<string:group_id>")
@require_authenticated
@require_permission("products.delete")
def delete_modifier_group(group_id: str) -> ResponseReturnValue:
    group_service = ModifierGroupService()
    group_service.delete_group(group_id)
    return _commit_and_respond({"message": "Modifier group deleted."}, HTTPStatus.OK)


@products_bp.patch("/modifier-groups/<string:group_id>/activate")
@require_authenticated
@require_permission("products.update")
def activate_modifier_group(group_id: str) -> ResponseReturnValue:
    group_service = ModifierGroupService()
    model = group_service.activate_group(group_id)
    return _commit_and_respond(modifier_group_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/modifier-groups/<string:group_id>/deactivate")
@require_authenticated
@require_permission("products.update")
def deactivate_modifier_group(group_id: str) -> ResponseReturnValue:
    group_service = ModifierGroupService()
    model = group_service.deactivate_group(group_id)
    return _commit_and_respond(modifier_group_to_dict(model), HTTPStatus.OK)
