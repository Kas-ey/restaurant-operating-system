"""Serialization helpers for identity API responses."""

from __future__ import annotations

from ros.identity.auth import AuthenticationResult
from ros.identity.persistence.models import PermissionModel, RoleModel, UserModel


def auth_result_to_dict(result: AuthenticationResult) -> dict[str, str | int]:
    """Serialize an authentication result object."""
    return {
        "access_token": result.access_token,
        "token_type": result.token_type,
        "expires_in": result.expires_in,
    }


def user_to_dict(model: UserModel) -> dict:
    """Serialize a user model to a JSON-compatible dictionary."""
    return {
        "id": model.id,
        "email": model.email,
        "full_name": model.full_name,
        "is_active": model.is_active,
        "roles": [{"id": role.id, "name": role.name} for role in model.roles],
    }


def role_to_dict(model: RoleModel) -> dict:
    """Serialize a role model to a JSON-compatible dictionary."""
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "is_active": model.is_active,
        "permissions": [{"id": permission.id, "name": permission.name} for permission in model.permissions],
    }


def permission_to_dict(model: PermissionModel) -> dict:
    """Serialize a permission model to a JSON-compatible dictionary."""
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "is_active": model.is_active,
    }
