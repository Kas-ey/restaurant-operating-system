"""Product aggregate HTTP routes for Products."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.products.application import ProductService

from ..schemas import validate_create_product_payload, validate_update_product_payload
from ..serializers import product_to_dict
from . import _commit_and_respond, _require_json_body, products_bp


@products_bp.get("/products")
@require_authenticated
@require_permission("products.read")
def list_products() -> ResponseReturnValue:
    product_service = ProductService()
    models = product_service.list_products()
    return success_response([product_to_dict(model) for model in models], HTTPStatus.OK)


@products_bp.get("/products/<string:product_id>")
@require_authenticated
@require_permission("products.read")
def get_product(product_id: str) -> ResponseReturnValue:
    product_service = ProductService()
    model = product_service.get_product(product_id)
    return success_response(product_to_dict(model), HTTPStatus.OK)


@products_bp.post("/products")
@require_authenticated
@require_permission("products.create")
def create_product() -> ResponseReturnValue:
    product_service = ProductService()
    payload = _require_json_body()
    data = validate_create_product_payload(payload)
    model = product_service.create_product(
        product_id=data["id"],
        name=data["name"],
        sku=data["sku"],
        description=data["description"],
        category_id=data["category_id"],
    )
    return _commit_and_respond(product_to_dict(model), HTTPStatus.CREATED)


@products_bp.put("/products/<string:product_id>")
@require_authenticated
@require_permission("products.update")
def update_product(product_id: str) -> ResponseReturnValue:
    product_service = ProductService()
    payload = _require_json_body()
    data = validate_update_product_payload(payload)
    model = product_service.update_product(
        product_id,
        name=data.get("name"),
        sku=data.get("sku"),
        description=data.get("description"),
        category_id=data.get("category_id"),
    )
    return _commit_and_respond(product_to_dict(model), HTTPStatus.OK)


@products_bp.delete("/products/<string:product_id>")
@require_authenticated
@require_permission("products.delete")
def delete_product(product_id: str) -> ResponseReturnValue:
    product_service = ProductService()
    product_service.delete_product(product_id)
    return _commit_and_respond({"message": "Product deleted."}, HTTPStatus.OK)


@products_bp.patch("/products/<string:product_id>/activate")
@require_authenticated
@require_permission("products.update")
def activate_product(product_id: str) -> ResponseReturnValue:
    product_service = ProductService()
    model = product_service.activate_product(product_id)
    return _commit_and_respond(product_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/products/<string:product_id>/deactivate")
@require_authenticated
@require_permission("products.update")
def deactivate_product(product_id: str) -> ResponseReturnValue:
    product_service = ProductService()
    model = product_service.deactivate_product(product_id)
    return _commit_and_respond(product_to_dict(model), HTTPStatus.OK)
