from flask import jsonify


def success_response(data, status_code: int = 200):
    """Return a standard success payload for API responses."""
    return jsonify({"success": True, "data": data}), status_code
