"""Products API route registrations and shared route utilities."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, request
from flask.typing import ResponseReturnValue

from ros.core.extensions import db
from ros.http.errors import error_response
from ros.http.responses import success_response
from ros.shared.exceptions import ROSException


products_bp = Blueprint("products", __name__, url_prefix="/api/v1")


@products_bp.errorhandler(Exception)
def handle_products_exception(exc: Exception) -> ResponseReturnValue:
    db.session.rollback()
    if isinstance(exc, ROSException):
        return error_response(exc.message, exc.status_code)
    return error_response("Internal server error.", HTTPStatus.INTERNAL_SERVER_ERROR)


def _require_json_body() -> dict:
    payload = request.get_json(silent=True)
    if payload is None:
        raise ROSException("Request body must be valid JSON.", HTTPStatus.BAD_REQUEST)
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    return payload


def _commit_and_respond(data, status_code: HTTPStatus) -> ResponseReturnValue:
    db.session.commit()
    return success_response(data, status_code)


# Import route modules for blueprint registration side effects.
from . import category_routes, modifier_group_routes, modifier_option_routes, pricing_routes, product_routes, variant_routes


__all__ = ["products_bp"]
