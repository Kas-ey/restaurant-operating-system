from flask import Blueprint

from ros.http import success_response

common_bp = Blueprint("common", __name__, url_prefix="/api/v1")


@common_bp.get("/health")
def health_check():
    return success_response({"status": "healthy"}, 200)

