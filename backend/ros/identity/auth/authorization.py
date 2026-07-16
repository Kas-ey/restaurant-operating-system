"""Authorization helpers and decorators for RBAC permission enforcement."""

from __future__ import annotations

from functools import wraps
from http import HTTPStatus
from typing import Callable

from flask import g, request

from ros.identity.auth.authentication import AuthenticationService
from ros.identity.persistence.models import UserModel
from ros.shared.exceptions import ROSException


def resolve_user_permissions(user: UserModel) -> set[str]:
    """Resolve all permission names assigned to a user through roles."""
    cached_user_id = getattr(g, "current_user_permissions_user_id", None)
    cached_permissions = getattr(g, "current_user_permissions", None)
    if cached_user_id == user.id and isinstance(cached_permissions, set):
        return cached_permissions

    permissions: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.name)

    g.current_user_permissions_user_id = user.id
    g.current_user_permissions = permissions
    return permissions


def has_permission(user: UserModel, required_permission: str) -> bool:
    """Return whether the authenticated user has the required permission."""
    return required_permission in resolve_user_permissions(user)


def require_authenticated(func: Callable):
    """Protect an endpoint by requiring a valid authenticated user."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_service = _get_auth_service()
        token = auth_service.extract_bearer_token(request.headers.get("Authorization"))
        user = auth_service.resolve_current_user(token)
        g.current_user = user
        return func(*args, **kwargs)

    return wrapper


def require_permission(required_permission: str):
    """Protect an endpoint by requiring a specific permission."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_service = _get_auth_service()
            token = auth_service.extract_bearer_token(request.headers.get("Authorization"))
            user = auth_service.resolve_current_user(token)

            if not has_permission(user, required_permission):
                raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)

            g.current_user = user
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _get_auth_service() -> AuthenticationService:
    service = getattr(g, "auth_service", None)
    if service is None:
        service = AuthenticationService()
        g.auth_service = service
    return service
