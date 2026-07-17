"""Pricing aggregate HTTP routes for Products."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.products.application import ProductPriceService, VariantPriceService

from ..schemas import (
    validate_create_product_price_payload,
    validate_create_variant_price_payload,
    validate_update_product_price_payload,
    validate_update_variant_price_payload,
)
from ..serializers import product_price_to_dict, variant_price_to_dict
from . import _commit_and_respond, _require_json_body, products_bp


@products_bp.get("/products/<string:product_id>/prices")
@require_authenticated
@require_permission("products.read")
def list_product_prices(product_id: str) -> ResponseReturnValue:
    price_service = ProductPriceService()
    models = price_service.list_prices(product_id)
    return success_response([product_price_to_dict(model) for model in models], HTTPStatus.OK)


@products_bp.get("/products/<string:product_id>/prices/current")
@require_authenticated
@require_permission("products.read")
def get_current_product_price(product_id: str) -> ResponseReturnValue:
    price_service = ProductPriceService()
    model = price_service.get_current_price(product_id)
    return success_response(product_price_to_dict(model), HTTPStatus.OK)


@products_bp.post("/products/<string:product_id>/prices")
@require_authenticated
@require_permission("products.create")
def create_product_price(product_id: str) -> ResponseReturnValue:
    price_service = ProductPriceService()
    payload = _require_json_body()
    data = validate_create_product_price_payload(payload)
    model = price_service.create_price(
        price_id=data["id"],
        product_id=product_id,
        amount=data["amount"],
        currency=data["currency"],
        effective_from=data["effective_from"],
        effective_to=data["effective_to"],
        is_active=data["is_active"],
    )
    return _commit_and_respond(product_price_to_dict(model), HTTPStatus.CREATED)


@products_bp.put("/product-prices/<string:price_id>")
@require_authenticated
@require_permission("products.update")
def update_product_price(price_id: str) -> ResponseReturnValue:
    price_service = ProductPriceService()
    payload = _require_json_body()
    data = validate_update_product_price_payload(payload)
    model = price_service.update_price(
        price_id,
        amount=data.get("amount"),
        currency=data.get("currency"),
        effective_from=data.get("effective_from"),
        effective_to=data.get("effective_to"),
        is_active=data.get("is_active"),
    )
    return _commit_and_respond(product_price_to_dict(model), HTTPStatus.OK)


@products_bp.delete("/product-prices/<string:price_id>")
@require_authenticated
@require_permission("products.delete")
def delete_product_price(price_id: str) -> ResponseReturnValue:
    price_service = ProductPriceService()
    price_service.delete_price(price_id)
    return _commit_and_respond({"message": "Product price deleted."}, HTTPStatus.OK)


@products_bp.patch("/product-prices/<string:price_id>/activate")
@require_authenticated
@require_permission("products.update")
def activate_product_price(price_id: str) -> ResponseReturnValue:
    price_service = ProductPriceService()
    model = price_service.activate_price(price_id)
    return _commit_and_respond(product_price_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/product-prices/<string:price_id>/deactivate")
@require_authenticated
@require_permission("products.update")
def deactivate_product_price(price_id: str) -> ResponseReturnValue:
    price_service = ProductPriceService()
    model = price_service.deactivate_price(price_id)
    return _commit_and_respond(product_price_to_dict(model), HTTPStatus.OK)


@products_bp.get("/variants/<string:variant_id>/prices")
@require_authenticated
@require_permission("products.read")
def list_variant_prices(variant_id: str) -> ResponseReturnValue:
    price_service = VariantPriceService()
    models = price_service.list_prices(variant_id)
    return success_response([variant_price_to_dict(model) for model in models], HTTPStatus.OK)


@products_bp.get("/variants/<string:variant_id>/prices/current")
@require_authenticated
@require_permission("products.read")
def get_current_variant_price(variant_id: str) -> ResponseReturnValue:
    price_service = VariantPriceService()
    model = price_service.get_current_price(variant_id)
    return success_response(variant_price_to_dict(model), HTTPStatus.OK)


@products_bp.post("/variants/<string:variant_id>/prices")
@require_authenticated
@require_permission("products.create")
def create_variant_price(variant_id: str) -> ResponseReturnValue:
    price_service = VariantPriceService()
    payload = _require_json_body()
    data = validate_create_variant_price_payload(payload)
    model = price_service.create_price(
        price_id=data["id"],
        variant_id=variant_id,
        amount=data["amount"],
        currency=data["currency"],
        effective_from=data["effective_from"],
        effective_to=data["effective_to"],
        is_active=data["is_active"],
    )
    return _commit_and_respond(variant_price_to_dict(model), HTTPStatus.CREATED)


@products_bp.put("/variant-prices/<string:price_id>")
@require_authenticated
@require_permission("products.update")
def update_variant_price(price_id: str) -> ResponseReturnValue:
    price_service = VariantPriceService()
    payload = _require_json_body()
    data = validate_update_variant_price_payload(payload)
    model = price_service.update_price(
        price_id,
        amount=data.get("amount"),
        currency=data.get("currency"),
        effective_from=data.get("effective_from"),
        effective_to=data.get("effective_to"),
        is_active=data.get("is_active"),
    )
    return _commit_and_respond(variant_price_to_dict(model), HTTPStatus.OK)


@products_bp.delete("/variant-prices/<string:price_id>")
@require_authenticated
@require_permission("products.delete")
def delete_variant_price(price_id: str) -> ResponseReturnValue:
    price_service = VariantPriceService()
    price_service.delete_price(price_id)
    return _commit_and_respond({"message": "Variant price deleted."}, HTTPStatus.OK)


@products_bp.patch("/variant-prices/<string:price_id>/activate")
@require_authenticated
@require_permission("products.update")
def activate_variant_price(price_id: str) -> ResponseReturnValue:
    price_service = VariantPriceService()
    model = price_service.activate_price(price_id)
    return _commit_and_respond(variant_price_to_dict(model), HTTPStatus.OK)


@products_bp.patch("/variant-prices/<string:price_id>/deactivate")
@require_authenticated
@require_permission("products.update")
def deactivate_variant_price(price_id: str) -> ResponseReturnValue:
    price_service = VariantPriceService()
    model = price_service.deactivate_price(price_id)
    return _commit_and_respond(variant_price_to_dict(model), HTTPStatus.OK)
