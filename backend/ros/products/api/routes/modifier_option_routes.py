"""Modifier option aggregate HTTP routes for Products."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.products.application import ModifierOptionService

from ..schemas import validate_create_modifier_option_payload, validate_update_modifier_option_payload
from ..serializers import modifier_option_to_dict
from . import _commit_and_respond, _require_json_body, products_bp


@products_bp.get("/modifier-groups/<string:group_id>/options")
@require_authenticated
@require_permission("products.read")
def list_modifier_options(group_id: str) -> ResponseReturnValue:
    option_service = ModifierOptionService()
    models = option_service.list_options(group_id)
    return success_response([modifier_option_to_dict(model) for model in models], HTTPStatus.OK)


@products_bp.post("/modifier-groups/<string:group_id>/options")
@require_authenticated
@require_permission("products.create")
def create_modifier_option(group_id: str) -> ResponseReturnValue:
    option_service = ModifierOptionService()
    payload = _require_json_body()
    data = validate_create_modifier_option_payload(payload)
    model = option_service.create_option(
        option_id=data["id"],
        modifier_group_id=group_id,
        name=data["name"],
        description=data["description"],
        display_order=data["display_order"],
        is_default=data["is_default"],
    )
    return _commit_and_respond(modifier_option_to_dict(model), HTTPStatus.CREATED)


@products_bp.put("/modifier-options/<string:option_id>")
@require_authenticated
@require_permission("products.update")
def update_modifier_option(option_id: str) -> ResponseReturnValue:
    option_service = ModifierOptionService()
    payload = _require_json_body()
    data = validate_update_modifier_option_payload(payload)
    model = option_service.update_option(
        option_id,
        name=data.get("name"),
        description=data.get("description"),
        display_order=data.get("display_order"),
        is_default=data.get("is_default"),
    )
    return _commit_and_respond(modifier_option_to_dict(model), HTTPStatus.OK)


@products_bp.delete("/modifier-options/<string:option_id>")
@require_authenticated
@require_permission("products.delete")
def delete_modifier_option(option_id: str) -> ResponseReturnValue:
    option_service = ModifierOptionService()
    option_service.delete_option(option_id)
    return _commit_and_respond({"message": "Modifier option deleted."}, HTTPStatus.OK)


@products_bp.patch("/modifier-options/<string:option_id>/activate")
@require_authenticated
@require_permission("products.update")
def activate_modifier_option(option_id: str) -> ResponseReturnValue:
    option_service = ModifierOptionService()
    model = option_service.activate_option(option_id)
    return _commit_and_respond(modifier_option_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/modifier-options/<string:option_id>/deactivate")
@require_authenticated
@require_permission("products.update")
def deactivate_modifier_option(option_id: str) -> ResponseReturnValue:
    option_service = ModifierOptionService()
    model = option_service.deactivate_option(option_id)
    return _commit_and_respond(modifier_option_to_dict(model), HTTPStatus.OK)
