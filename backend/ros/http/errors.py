from flask import jsonify


def error_response(message: str, status_code: int):
    """Return a standard error payload for API responses."""
    return jsonify({"success": False, "error": {"message": message}}), status_code
