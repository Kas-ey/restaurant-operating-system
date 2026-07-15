"""Repository implementations for Identity persistence operations."""

from __future__ import annotations

from sqlalchemy import select

from ros.core.extensions import db
from ros.identity.domain import Permission, Role, User

from .mappers import PermissionMapper, RoleMapper, UserMapper
from .models import PermissionModel, RoleModel, UserModel


class UserRepository:
    """Persistence repository for user entities."""

    def get_by_id(self, user_id: str) -> User | None:
        """Return a user by identifier, or None when not found."""
        model = db.session.get(UserModel, user_id)
        if model is None:
            return None
        return UserMapper.to_domain(model)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email, or None when not found."""
        model = db.session.scalar(select(UserModel).where(UserModel.email == email))
        if model is None:
            return None
        return UserMapper.to_domain(model)

    def get_all(self) -> list[User]:
        """Return all users."""
        models = db.session.scalars(select(UserModel)).all()
        return [UserMapper.to_domain(model) for model in models]

    def save(self, entity: User) -> User:
        """Persist a user entity and return the saved domain entity."""
        merged_model = db.session.merge(UserMapper.to_model(entity))
        db.session.flush()
        return UserMapper.to_domain(merged_model)

    def delete(self, user_id: str) -> None:
        """Delete a user by identifier when it exists."""
        model = db.session.get(UserModel, user_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, user_id: str) -> bool:
        """Return whether a user exists for the provided identifier."""
        return db.session.get(UserModel, user_id) is not None


class RoleRepository:
    """Persistence repository for role entities."""

    def get_by_id(self, role_id: str) -> Role | None:
        """Return a role by identifier, or None when not found."""
        model = db.session.get(RoleModel, role_id)
        if model is None:
            return None
        return RoleMapper.to_domain(model)

    def get_by_name(self, name: str) -> Role | None:
        """Return a role by name, or None when not found."""
        model = db.session.scalar(select(RoleModel).where(RoleModel.name == name))
        if model is None:
            return None
        return RoleMapper.to_domain(model)

    def get_all(self) -> list[Role]:
        """Return all roles."""
        models = db.session.scalars(select(RoleModel)).all()
        return [RoleMapper.to_domain(model) for model in models]

    def save(self, entity: Role) -> Role:
        """Persist a role entity and return the saved domain entity."""
        merged_model = db.session.merge(RoleMapper.to_model(entity))
        db.session.flush()
        return RoleMapper.to_domain(merged_model)

    def delete(self, role_id: str) -> None:
        """Delete a role by identifier when it exists."""
        model = db.session.get(RoleModel, role_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, role_id: str) -> bool:
        """Return whether a role exists for the provided identifier."""
        return db.session.get(RoleModel, role_id) is not None


class PermissionRepository:
    """Persistence repository for permission entities."""

    def get_by_id(self, permission_id: str) -> Permission | None:
        """Return a permission by identifier, or None when not found."""
        model = db.session.get(PermissionModel, permission_id)
        if model is None:
            return None
        return PermissionMapper.to_domain(model)

    def get_by_name(self, name: str) -> Permission | None:
        """Return a permission by name, or None when not found."""
        model = db.session.scalar(select(PermissionModel).where(PermissionModel.name == name))
        if model is None:
            return None
        return PermissionMapper.to_domain(model)

    def get_all(self) -> list[Permission]:
        """Return all permissions."""
        models = db.session.scalars(select(PermissionModel)).all()
        return [PermissionMapper.to_domain(model) for model in models]

    def save(self, entity: Permission) -> Permission:
        """Persist a permission entity and return the saved domain entity."""
        merged_model = db.session.merge(PermissionMapper.to_model(entity))
        db.session.flush()
        return PermissionMapper.to_domain(merged_model)

    def delete(self, permission_id: str) -> None:
        """Delete a permission by identifier when it exists."""
        model = db.session.get(PermissionModel, permission_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, permission_id: str) -> bool:
        """Return whether a permission exists for the provided identifier."""
        return db.session.get(PermissionModel, permission_id) is not None