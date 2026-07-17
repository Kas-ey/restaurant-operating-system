"""Stock level projection read-only HTTP routes for Inventory."""

from __future__ import annotations

from http import HTTPStatus

from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import StockLevelService

from ..serializers import stock_level_to_dict
from . import inventory_bp


@inventory_bp.get("/stock-levels")
@require_authenticated
@require_permission("inventory.read")
def list_stock_levels() -> ResponseReturnValue:
    stock_level_service = StockLevelService()
    models = stock_level_service.list_projections()
    return success_response([stock_level_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/items/<string:item_id>/stock-levels")
@require_authenticated
@require_permission("inventory.read")
def list_stock_levels_by_item(item_id: str) -> ResponseReturnValue:
    stock_level_service = StockLevelService()
    models = stock_level_service.list_projections_by_item(item_id)
    return success_response([stock_level_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/locations/<string:location_id>/stock-levels")
@require_authenticated
@require_permission("inventory.read")
def list_stock_levels_by_location(location_id: str) -> ResponseReturnValue:
    stock_level_service = StockLevelService()
    models = stock_level_service.list_projections_by_location(location_id)
    return success_response([stock_level_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/stock-levels/<string:item_id>/<string:location_id>")
@require_authenticated
@require_permission("inventory.read")
def get_stock_level(item_id: str, location_id: str) -> ResponseReturnValue:
    stock_level_service = StockLevelService()
    model = stock_level_service.get_projection(item_id, location_id)
    return success_response(stock_level_to_dict(model), HTTPStatus.OK)
