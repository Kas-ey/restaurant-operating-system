"""Application service for permission-related identity workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.identity.application.base import BaseService
from ros.identity.persistence.models import PermissionModel
from ros.identity.persistence.repositories import PermissionRepository
from ros.shared.exceptions import ROSException


class PermissionService(BaseService):
    """Coordinates permission management workflows for the identity domain."""

    def __init__(self, permission_repository: PermissionRepository | None = None) -> None:
        self._permission_repository = permission_repository or PermissionRepository()

    def create_permission(self, permission_id: str, name: str, description: str) -> PermissionModel:
        """Create and persist a new permission model."""
        normalized_id = self._require_text(permission_id, "Permission ID is required.")
        normalized_name = self._normalize_name(name)
        normalized_description = self._normalize_description(description, "Permission description is required.")

        if self._permission_repository.get_by_name(normalized_name) is not None:
            raise ROSException("Permission already exists.", HTTPStatus.CONFLICT)

        model = PermissionModel(
            id=normalized_id,
            name=normalized_name,
            description=normalized_description,
            is_active=True,
        )
        self._permission_repository.save(model)
        return model

    def update_permission(
        self,
        permission_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> PermissionModel:
        """Update mutable permission fields and persist the changes."""
        model = self._get_existing_permission(permission_id)

        if name is not None:
            normalized_name = self._normalize_name(name)
            existing = self._permission_repository.get_by_name(normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Permission already exists.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if description is not None:
            model.description = self._normalize_description(description, "Permission description is required.")

        self._permission_repository.save(model)
        return model

    def delete_permission(self, permission_id: str) -> None:
        """Delete a permission permanently by identifier."""
        model = self._get_existing_permission(permission_id)
        self._permission_repository.delete(model.id)

    def get_permission(self, permission_id: str) -> PermissionModel:
        """Return a permission by identifier."""
        return self._get_existing_permission(permission_id)

    def list_permissions(self) -> list[PermissionModel]:
        """Return all persisted permissions."""
        return self._permission_repository.get_all()

    def _get_existing_permission(self, permission_id: str) -> PermissionModel:
        normalized_id = self._require_text(permission_id, "Permission ID is required.")
        model = self._permission_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Permission not found.", HTTPStatus.NOT_FOUND)
        return model

    @classmethod
    def _normalize_name(cls, value: str) -> str:
        normalized = cls._require_text(value, "Permission name is required.")
        collapsed = " ".join(normalized.split()).lower()
        return collapsed.replace(" ", ".")
