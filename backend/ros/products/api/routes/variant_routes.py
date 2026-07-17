"""Variant aggregate HTTP routes for Products."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.products.application import ProductVariantService

from ..schemas import validate_create_variant_payload, validate_update_variant_payload
from ..serializers import variant_to_dict
from . import _commit_and_respond, _require_json_body, products_bp


@products_bp.get("/products/<string:product_id>/variants")
@require_authenticated
@require_permission("products.read")
def list_variants(product_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    models = variant_service.list_variants(product_id)
    return success_response([variant_to_dict(model) for model in models], HTTPStatus.OK)


@products_bp.get("/variants/<string:variant_id>")
@require_authenticated
@require_permission("products.read")
def get_variant(variant_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    model = variant_service.get_variant(variant_id)
    return success_response(variant_to_dict(model), HTTPStatus.OK)


@products_bp.post("/products/<string:product_id>/variants")
@require_authenticated
@require_permission("products.create")
def create_variant(product_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    payload = _require_json_body()
    data = validate_create_variant_payload(payload)
    model = variant_service.create_variant(
        variant_id=data["id"],
        product_id=product_id,
        name=data["name"],
        sku=data["sku"],
        description=data["description"],
        display_order=data["display_order"],
        is_default=data["is_default"],
    )
    return _commit_and_respond(variant_to_dict(model), HTTPStatus.CREATED)


@products_bp.put("/variants/<string:variant_id>")
@require_authenticated
@require_permission("products.update")
def update_variant(variant_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    payload = _require_json_body()
    data = validate_update_variant_payload(payload)
    model = variant_service.update_variant(
        variant_id,
        name=data.get("name"),
        sku=data.get("sku"),
        description=data.get("description"),
        display_order=data.get("display_order"),
        is_default=data.get("is_default"),
    )
    return _commit_and_respond(variant_to_dict(model), HTTPStatus.OK)


@products_bp.delete("/variants/<string:variant_id>")
@require_authenticated
@require_permission("products.delete")
def delete_variant(variant_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    variant_service.delete_variant(variant_id)
    return _commit_and_respond({"message": "Variant deleted."}, HTTPStatus.OK)


@products_bp.patch("/variants/<string:variant_id>/activate")
@require_authenticated
@require_permission("products.update")
def activate_variant(variant_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    model = variant_service.activate_variant(variant_id)
    return _commit_and_respond(variant_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/variants/<string:variant_id>/deactivate")
@require_authenticated
@require_permission("products.update")
def deactivate_variant(variant_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    model = variant_service.deactivate_variant(variant_id)
    return _commit_and_respond(variant_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/variants/<string:variant_id>/default")
@require_authenticated
@require_permission("products.update")
def set_default_variant(variant_id: str) -> ResponseReturnValue:
    variant_service = ProductVariantService()
    model = variant_service.set_default_variant(variant_id)
    return _commit_and_respond(variant_to_dict(model), HTTPStatus.OK)
