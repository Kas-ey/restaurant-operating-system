"""Unit aggregate HTTP routes for Inventory."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import UnitService

from ..schemas import validate_create_unit_payload, validate_update_unit_payload
from ..serializers import unit_to_dict
from . import _commit_and_respond, _require_json_body, inventory_bp


@inventory_bp.get("/units")
@require_authenticated
@require_permission("inventory.read")
def list_units() -> ResponseReturnValue:
    unit_service = UnitService()
    models = unit_service.list_units()
    return success_response([unit_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/units/<string:unit_id>")
@require_authenticated
@require_permission("inventory.read")
def get_unit(unit_id: str) -> ResponseReturnValue:
    unit_service = UnitService()
    model = unit_service.get_unit(unit_id)
    return success_response(unit_to_dict(model), HTTPStatus.OK)


@inventory_bp.post("/units")
@require_authenticated
@require_permission("inventory.create")
def create_unit() -> ResponseReturnValue:
    unit_service = UnitService()
    payload = _require_json_body()
    data = validate_create_unit_payload(payload)
    model = unit_service.create_unit(
        unit_id=data["id"],
        name=data["name"],
        symbol=data["symbol"],
        description=data["description"],
        precision=data["precision"],
    )
    return _commit_and_respond(unit_to_dict(model), HTTPStatus.CREATED)


@inventory_bp.put("/units/<string:unit_id>")
@require_authenticated
@require_permission("inventory.update")
def update_unit(unit_id: str) -> ResponseReturnValue:
    unit_service = UnitService()
    payload = _require_json_body()
    data = validate_update_unit_payload(payload)
    model = unit_service.update_unit(
        unit_id,
        name=data.get("name"),
        symbol=data.get("symbol"),
        description=data.get("description"),
        precision=data.get("precision"),
    )
    return _commit_and_respond(unit_to_dict(model), HTTPStatus.OK)


@inventory_bp.delete("/units/<string:unit_id>")
@require_authenticated
@require_permission("inventory.delete")
def delete_unit(unit_id: str) -> ResponseReturnValue:
    unit_service = UnitService()
    unit_service.delete_unit(unit_id)
    return _commit_and_respond({"message": "Unit deleted."}, HTTPStatus.OK)


@inventory_bp.patch("/units/<string:unit_id>/activate")
@require_authenticated
@require_permission("inventory.update")
def activate_unit(unit_id: str) -> ResponseReturnValue:
    unit_service = UnitService()
    model = unit_service.activate_unit(unit_id)
    return _commit_and_respond(unit_to_dict(model), HTTPStatus.OK)


@inventory_bp.patch("/units/<string:unit_id>/deactivate")
@require_authenticated
@require_permission("inventory.update")
def deactivate_unit(unit_id: str) -> ResponseReturnValue:
    unit_service = UnitService()
    model = unit_service.deactivate_unit(unit_id)
    return _commit_and_respond(unit_to_dict(model), HTTPStatus.OK)
