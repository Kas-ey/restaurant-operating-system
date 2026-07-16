"""Repository implementations for Identity persistence operations."""

from __future__ import annotations

from sqlalchemy import select

from ros.core.extensions import db

from .models import PermissionModel, RoleModel, UserModel


class UserRepository:
    """Persistence repository for user entities."""

    def get_by_id(self, user_id: str) -> UserModel | None:
        """Return a user model by identifier, or None when not found."""
        return db.session.get(UserModel, user_id)

    def get_by_email(self, email: str) -> UserModel | None:
        """Return a user model by email, or None when not found."""
        return db.session.scalar(select(UserModel).where(UserModel.email == email))

    def get_all(self) -> list[UserModel]:
        """Return all user models."""
        return db.session.scalars(select(UserModel)).all()

    def save(self, model: UserModel) -> UserModel:
        """Persist a user model and return the saved model."""
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

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

    def get_by_id(self, role_id: str) -> RoleModel | None:
        """Return a role model by identifier, or None when not found."""
        return db.session.get(RoleModel, role_id)

    def get_by_name(self, name: str) -> RoleModel | None:
        """Return a role model by name, or None when not found."""
        return db.session.scalar(select(RoleModel).where(RoleModel.name == name))

    def get_all(self) -> list[RoleModel]:
        """Return all role models."""
        return db.session.scalars(select(RoleModel)).all()

    def save(self, model: RoleModel) -> RoleModel:
        """Persist a role model and return the saved model."""
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

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

    def get_by_id(self, permission_id: str) -> PermissionModel | None:
        """Return a permission model by identifier, or None when not found."""
        return db.session.get(PermissionModel, permission_id)

    def get_by_name(self, name: str) -> PermissionModel | None:
        """Return a permission model by name, or None when not found."""
        return db.session.scalar(select(PermissionModel).where(PermissionModel.name == name))

    def get_all(self) -> list[PermissionModel]:
        """Return all permission models."""
        return db.session.scalars(select(PermissionModel)).all()

    def save(self, model: PermissionModel) -> PermissionModel:
        """Persist a permission model and return the saved model."""
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, permission_id: str) -> None:
        """Delete a permission by identifier when it exists."""
        model = db.session.get(PermissionModel, permission_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, permission_id: str) -> bool:
        """Return whether a permission exists for the provided identifier."""
        return db.session.get(PermissionModel, permission_id) is not None