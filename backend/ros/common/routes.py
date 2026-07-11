from flask import Blueprint, jsonify

common_bp = Blueprint("common", __name__)


@common_bp.get("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200
