"""Translators between Identity domain entities and persistence models."""

from __future__ import annotations

from ros.identity.domain import Permission, Role, User

from .models import PermissionModel, RoleModel, UserModel


class _MappedPermission(Permission):
    """Hashable permission variant used during persistence mapping."""

    __hash__ = object.__hash__


class _MappedRole(Role):
    """Hashable role variant used during persistence mapping."""

    __hash__ = object.__hash__


class PermissionMapper:
    """Maps permission entities between domain and persistence layers."""

    @staticmethod
    def to_domain(model: PermissionModel) -> Permission:
        """Convert a permission persistence model into a domain entity."""
        return _MappedPermission(
            id=model.id,
            name=model.name,
            description=model.description,
            is_active=model.is_active,
        )

    @staticmethod
    def to_model(entity: Permission) -> PermissionModel:
        """Convert a permission domain entity into a persistence model."""
        return PermissionModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            is_active=entity.is_active,
        )


class RoleMapper:
    """Maps role entities between domain and persistence layers."""

    @staticmethod
    def to_domain(model: RoleModel) -> Role:
        """Convert a role persistence model into a domain entity."""
        return _MappedRole(
            id=model.id,
            name=model.name,
            description=model.description,
            permissions={PermissionMapper.to_domain(permission) for permission in model.permissions},
            is_active=model.is_active,
        )

    @staticmethod
    def to_model(entity: Role) -> RoleModel:
        """Convert a role domain entity into a persistence model."""
        return RoleModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            permissions=[PermissionMapper.to_model(permission) for permission in entity.permissions],
            is_active=entity.is_active,
        )


class UserMapper:
    """Maps user entities between domain and persistence layers."""

    @staticmethod
    def to_domain(model: UserModel) -> User:
        """Convert a user persistence model into a domain entity."""
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            roles={RoleMapper.to_domain(role) for role in model.roles},
            is_active=model.is_active,
        )

    @staticmethod
    def to_model(entity: User) -> UserModel:
        """Convert a user domain entity into a persistence model."""
        return UserModel(
            id=entity.id,
            email=entity.email,
            full_name=entity.full_name,
            roles=[RoleMapper.to_model(role) for role in entity.roles],
            is_active=entity.is_active,
        )