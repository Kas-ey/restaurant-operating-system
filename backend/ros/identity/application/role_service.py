"""Application service for role-related identity workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.identity.application.base import BaseService
from ros.identity.persistence.models import RoleModel
from ros.identity.persistence.repositories import PermissionRepository, RoleRepository
from ros.shared.exceptions import ROSException


class RoleService(BaseService):
    """Coordinates role management workflows for the identity domain."""

    def __init__(
        self,
        role_repository: RoleRepository | None = None,
        permission_repository: PermissionRepository | None = None,
    ) -> None:
        self._role_repository = role_repository or RoleRepository()
        self._permission_repository = permission_repository or PermissionRepository()

    def create_role(self, role_id: str, name: str, description: str) -> RoleModel:
        """Create and persist a new role model."""
        normalized_id = self._require_text(role_id, "Role ID is required.")
        normalized_name = self._normalize_name(name)
        normalized_description = self._normalize_description(description, "Role description is required.")

        if self._role_repository.get_by_name(normalized_name) is not None:
            raise ROSException("Duplicate role name.", HTTPStatus.CONFLICT)

        model = RoleModel(
            id=normalized_id,
            name=normalized_name,
            description=normalized_description,
            is_active=True,
        )
        self._role_repository.save(model)
        return model

    def update_role(self, role_id: str, *, name: str | None = None, description: str | None = None) -> RoleModel:
        """Update mutable role fields and persist the changes."""
        model = self._get_existing_role(role_id)

        if name is not None:
            normalized_name = self._normalize_name(name)
            existing = self._role_repository.get_by_name(normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Duplicate role name.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if description is not None:
            model.description = self._normalize_description(description, "Role description is required.")

        self._role_repository.save(model)
        return model

    def delete_role(self, role_id: str) -> None:
        """Delete a role permanently by identifier."""
        model = self._get_existing_role(role_id)
        self._role_repository.delete(model.id)

    def get_role(self, role_id: str) -> RoleModel:
        """Return a role by identifier."""
        return self._get_existing_role(role_id)

    def list_roles(self) -> list[RoleModel]:
        """Return all persisted roles."""
        return self._role_repository.get_all()

    def assign_permission(self, role_id: str, permission_id: str) -> RoleModel:
        """Assign a permission to a role and persist the relationship."""
        role = self._get_existing_role(role_id)
        permission = self._get_existing_permission(permission_id)

        if any(existing.id == permission.id for existing in role.permissions):
            raise ROSException("Duplicate permission assignment.", HTTPStatus.CONFLICT)

        role.permissions.append(permission)
        self._role_repository.save(role)
        return role

    def remove_permission(self, role_id: str, permission_id: str) -> RoleModel:
        """Remove a permission from a role and persist the relationship."""
        role = self._get_existing_role(role_id)
        permission = self._get_existing_permission(permission_id)

        if not any(existing.id == permission.id for existing in role.permissions):
            raise ROSException("Permission assignment not found.", HTTPStatus.NOT_FOUND)

        role.permissions = [existing for existing in role.permissions if existing.id != permission.id]
        self._role_repository.save(role)
        return role

    def _get_existing_role(self, role_id: str) -> RoleModel:
        normalized_id = self._require_text(role_id, "Role ID is required.")
        model = self._role_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Role not found.", HTTPStatus.NOT_FOUND)
        return model

    def _get_existing_permission(self, permission_id: str):
        normalized_id = self._require_text(permission_id, "Permission ID is required.")
        model = self._permission_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Permission not found.", HTTPStatus.NOT_FOUND)
        return model

    @classmethod
    def _normalize_name(cls, value: str) -> str:
        normalized = cls._require_text(value, "Role name is required.")
        return " ".join(normalized.split())
