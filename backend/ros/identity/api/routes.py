"""HTTP routes for identity application services."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, g, request
from flask.typing import ResponseReturnValue

from ros.core.extensions import db

from ros.http.errors import error_response
from ros.http.responses import success_response
from ros.identity.application.permission_service import PermissionService
from ros.identity.application.role_service import RoleService
from ros.identity.application.user_service import UserService
from ros.identity.auth import AuthenticationService, require_authenticated, require_permission
from ros.shared.exceptions import ROSException

from .serializers import auth_result_to_dict, permission_to_dict, role_to_dict, user_to_dict
from .schemas import (
    validate_create_permission_payload,
    validate_create_role_payload,
    validate_create_user_payload,
    validate_login_payload,
    validate_update_permission_payload,
    validate_update_role_payload,
    validate_update_user_payload,
)


identity_bp = Blueprint("identity", __name__)

_user_service = UserService()
_role_service = RoleService()
_permission_service = PermissionService()
_auth_service = AuthenticationService()


@identity_bp.post("/login")
def login() -> ResponseReturnValue:
    """Authenticate a user and issue an access token."""
    payload = _require_json_body()
    data = validate_login_payload(payload)
    result = _auth_service.login(data["email"], data["password"])
    return success_response(auth_result_to_dict(result), HTTPStatus.OK)


@identity_bp.post("/logout")
@require_authenticated
def logout() -> ResponseReturnValue:
    """Perform stateless logout for the current authenticated user."""
    _auth_service.logout()
    return success_response({"message": "Logged out."}, HTTPStatus.OK)


@identity_bp.get("/me")
@require_authenticated
def me() -> ResponseReturnValue:
    """Return the currently authenticated user's profile."""
    return success_response(user_to_dict(g.current_user), HTTPStatus.OK)


@identity_bp.post("/users")
@require_permission("users.create")
def create_user() -> ResponseReturnValue:
    """Create a new user resource."""
    payload = _require_json_body()
    data = validate_create_user_payload(payload)
    model = _user_service.create_user(
        user_id=data["id"],
        email=data["email"],
        full_name=data["full_name"],
        password=data["password"],
    )
    return _commit_and_respond(user_to_dict(model), HTTPStatus.CREATED)


@identity_bp.get("/users")
@require_permission("users.read")
def list_users() -> ResponseReturnValue:
    """List all user resources."""
    models = _user_service.list_users()
    return success_response([user_to_dict(model) for model in models], HTTPStatus.OK)


@identity_bp.get("/users/<string:user_id>")
@require_permission("users.read")
def get_user(user_id: str) -> ResponseReturnValue:
    """Retrieve a user resource by identifier."""
    model = _user_service.get_user(user_id)
    return success_response(user_to_dict(model), HTTPStatus.OK)


@identity_bp.put("/users/<string:user_id>")
@require_permission("users.update")
def update_user(user_id: str) -> ResponseReturnValue:
    """Update a user resource by identifier."""
    payload = _require_json_body()
    data = validate_update_user_payload(payload)
    model = _user_service.update_user(
        user_id,
        email=data.get("email"),
        full_name=data.get("full_name"),
        password=data.get("password"),
    )
    return _commit_and_respond(user_to_dict(model), HTTPStatus.OK)


@identity_bp.delete("/users/<string:user_id>")
@require_permission("users.delete")
def delete_user(user_id: str) -> ResponseReturnValue:
    """Delete a user resource by identifier."""
    _user_service.delete_user(user_id)
    return _commit_and_respond({"message": "User deleted."}, HTTPStatus.OK)


@identity_bp.patch("/users/<string:user_id>/activate")
@require_permission("users.activate")
def activate_user(user_id: str) -> ResponseReturnValue:
    """Activate a user resource by identifier."""
    model = _user_service.activate_user(user_id)
    return _commit_and_respond(user_to_dict(model), HTTPStatus.OK)


@identity_bp.patch("/users/<string:user_id>/deactivate")
@require_permission("users.deactivate")
def deactivate_user(user_id: str) -> ResponseReturnValue:
    """Deactivate a user resource by identifier."""
    model = _user_service.deactivate_user(user_id)
    return _commit_and_respond(user_to_dict(model), HTTPStatus.OK)


@identity_bp.post("/roles")
@require_permission("roles.create")
def create_role() -> ResponseReturnValue:
    """Create a new role resource."""
    payload = _require_json_body()
    data = validate_create_role_payload(payload)
    model = _role_service.create_role(
        role_id=data["id"],
        name=data["name"],
        description=data["description"],
    )
    return _commit_and_respond(role_to_dict(model), HTTPStatus.CREATED)


@identity_bp.get("/roles")
@require_permission("roles.read")
def list_roles() -> ResponseReturnValue:
    """List all role resources."""
    models = _role_service.list_roles()
    return success_response([role_to_dict(model) for model in models], HTTPStatus.OK)


@identity_bp.get("/roles/<string:role_id>")
@require_permission("roles.read")
def get_role(role_id: str) -> ResponseReturnValue:
    """Retrieve a role resource by identifier."""
    model = _role_service.get_role(role_id)
    return success_response(role_to_dict(model), HTTPStatus.OK)


@identity_bp.put("/roles/<string:role_id>")
@require_permission("roles.update")
def update_role(role_id: str) -> ResponseReturnValue:
    """Update a role resource by identifier."""
    payload = _require_json_body()
    data = validate_update_role_payload(payload)
    model = _role_service.update_role(
        role_id,
        name=data.get("name"),
        description=data.get("description"),
    )
    return _commit_and_respond(role_to_dict(model), HTTPStatus.OK)


@identity_bp.delete("/roles/<string:role_id>")
@require_permission("roles.delete")
def delete_role(role_id: str) -> ResponseReturnValue:
    """Delete a role resource by identifier."""
    _role_service.delete_role(role_id)
    return _commit_and_respond({"message": "Role deleted."}, HTTPStatus.OK)


@identity_bp.post("/roles/<string:role_id>/permissions/<string:permission_id>")
@require_permission("roles.permissions.assign")
def assign_permission(role_id: str, permission_id: str) -> ResponseReturnValue:
    """Assign a permission to a role."""
    model = _role_service.assign_permission(role_id, permission_id)
    return _commit_and_respond(role_to_dict(model), HTTPStatus.OK)


@identity_bp.delete("/roles/<string:role_id>/permissions/<string:permission_id>")
@require_permission("roles.permissions.remove")
def remove_permission(role_id: str, permission_id: str) -> ResponseReturnValue:
    """Remove an assigned permission from a role."""
    model = _role_service.remove_permission(role_id, permission_id)
    return _commit_and_respond(role_to_dict(model), HTTPStatus.OK)


@identity_bp.post("/permissions")
@require_permission("permissions.create")
def create_permission() -> ResponseReturnValue:
    """Create a new permission resource."""
    payload = _require_json_body()
    data = validate_create_permission_payload(payload)
    model = _permission_service.create_permission(
        permission_id=data["id"],
        name=data["name"],
        description=data["description"],
    )
    return _commit_and_respond(permission_to_dict(model), HTTPStatus.CREATED)


@identity_bp.get("/permissions")
@require_permission("permissions.read")
def list_permissions() -> ResponseReturnValue:
    """List all permission resources."""
    models = _permission_service.list_permissions()
    return success_response([permission_to_dict(model) for model in models], HTTPStatus.OK)


@identity_bp.get("/permissions/<string:permission_id>")
@require_permission("permissions.read")
def get_permission(permission_id: str) -> ResponseReturnValue:
    """Retrieve a permission resource by identifier."""
    model = _permission_service.get_permission(permission_id)
    return success_response(permission_to_dict(model), HTTPStatus.OK)


@identity_bp.put("/permissions/<string:permission_id>")
@require_permission("permissions.update")
def update_permission(permission_id: str) -> ResponseReturnValue:
    """Update a permission resource by identifier."""
    payload = _require_json_body()
    data = validate_update_permission_payload(payload)
    model = _permission_service.update_permission(
        permission_id,
        name=data.get("name"),
        description=data.get("description"),
    )
    return _commit_and_respond(permission_to_dict(model), HTTPStatus.OK)


@identity_bp.delete("/permissions/<string:permission_id>")
@require_permission("permissions.delete")
def delete_permission(permission_id: str) -> ResponseReturnValue:
    """Delete a permission resource by identifier."""
    _permission_service.delete_permission(permission_id)
    return _commit_and_respond({"message": "Permission deleted."}, HTTPStatus.OK)


@identity_bp.errorhandler(Exception)
def handle_identity_exception(exc: Exception) -> ResponseReturnValue:
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
