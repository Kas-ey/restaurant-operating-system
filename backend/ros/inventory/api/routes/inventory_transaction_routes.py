"""Inventory transaction ledger read-only HTTP routes."""

from __future__ import annotations

from http import HTTPStatus

from flask import request
from flask.typing import ResponseReturnValue

from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.inventory.application import InventoryTransactionService
from ros.shared.exceptions import ROSException

from ..schemas import validate_transaction_date_query
from ..serializers import inventory_transaction_to_dict
from . import inventory_bp


@inventory_bp.get("/transactions")
@require_authenticated
@require_permission("inventory.read")
def list_transactions() -> ResponseReturnValue:
    transaction_service = InventoryTransactionService()
    models = transaction_service.list_transactions()
    return success_response([inventory_transaction_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/items/<string:item_id>/transactions")
@require_authenticated
@require_permission("inventory.read")
def list_transactions_by_item(item_id: str) -> ResponseReturnValue:
    transaction_service = InventoryTransactionService()
    models = transaction_service.list_transactions_by_item(item_id)
    return success_response([inventory_transaction_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/transactions/reference")
@require_authenticated
@require_permission("inventory.read")
def list_transactions_by_reference() -> ResponseReturnValue:
    transaction_service = InventoryTransactionService()
    reference_type = request.args.get("reference_type")
    reference_id = request.args.get("reference_id")
    if not reference_type or not reference_id:
        raise ROSException("Query params 'reference_type' and 'reference_id' are required.", HTTPStatus.BAD_REQUEST)
    models = transaction_service.list_transactions_by_reference(reference_type, reference_id)
    return success_response([inventory_transaction_to_dict(model) for model in models], HTTPStatus.OK)


@inventory_bp.get("/transactions/date-range")
@require_authenticated
@require_permission("inventory.read")
def list_transactions_by_date_range() -> ResponseReturnValue:
    transaction_service = InventoryTransactionService()
    start_at, end_at = validate_transaction_date_query(
        request.args.get("start_at"),
        request.args.get("end_at"),
    )
    models = transaction_service.list_transactions_by_date_range(start_at=start_at, end_at=end_at)
    return success_response([inventory_transaction_to_dict(model) for model in models], HTTPStatus.OK)
