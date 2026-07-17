"""Category aggregate HTTP routes for Products."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.products.application import ProductCategoryService

from ..schemas import validate_create_category_payload, validate_update_category_payload
from ..serializers import category_to_dict
from . import _commit_and_respond, _require_json_body, products_bp


@products_bp.get("/categories")
@require_authenticated
@require_permission("categories.read")
def list_categories() -> ResponseReturnValue:
    category_service = ProductCategoryService()
    models = category_service.list_categories()
    return success_response([category_to_dict(model) for model in models], HTTPStatus.OK)


@products_bp.get("/categories/<string:category_id>")
@require_authenticated
@require_permission("categories.read")
def get_category(category_id: str) -> ResponseReturnValue:
    category_service = ProductCategoryService()
    model = category_service.get_category(category_id)
    return success_response(category_to_dict(model), HTTPStatus.OK)


@products_bp.post("/categories")
@require_authenticated
@require_permission("categories.create")
def create_category() -> ResponseReturnValue:
    category_service = ProductCategoryService()
    payload = _require_json_body()
    data = validate_create_category_payload(payload)
    model = category_service.create_category(
        category_id=data["id"],
        name=data["name"],
        description=data["description"],
    )
    return _commit_and_respond(category_to_dict(model), HTTPStatus.CREATED)


@products_bp.put("/categories/<string:category_id>")
@require_authenticated
@require_permission("categories.update")
def update_category(category_id: str) -> ResponseReturnValue:
    category_service = ProductCategoryService()
    payload = _require_json_body()
    data = validate_update_category_payload(payload)
    model = category_service.update_category(
        category_id,
        name=data.get("name"),
        description=data.get("description"),
    )
    return _commit_and_respond(category_to_dict(model), HTTPStatus.OK)


@products_bp.delete("/categories/<string:category_id>")
@require_authenticated
@require_permission("categories.delete")
def delete_category(category_id: str) -> ResponseReturnValue:
    category_service = ProductCategoryService()
    category_service.delete_category(category_id)
    return _commit_and_respond({"message": "Category deleted."}, HTTPStatus.OK)


@products_bp.patch("/categories/<string:category_id>/activate")
@require_authenticated
@require_permission("categories.update")
def activate_category(category_id: str) -> ResponseReturnValue:
    category_service = ProductCategoryService()
    model = category_service.activate_category(category_id)
    return _commit_and_respond(category_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/categories/<string:category_id>/deactivate")
@require_authenticated
@require_permission("categories.update")
def deactivate_category(category_id: str) -> ResponseReturnValue:
    category_service = ProductCategoryService()
    model = category_service.deactivate_category(category_id)
    return _commit_and_respond(category_to_dict(model), HTTPStatus.OK)
