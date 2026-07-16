"""SQLAlchemy persistence models for the Identity & Access domain."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ros.core.extensions import db


user_roles = Table(
    "user_roles",
    db.metadata,
    Column("user_id", String(64), ForeignKey("users.id"), primary_key=True),
    Column("role_id", String(64), ForeignKey("roles.id"), primary_key=True),
)


role_permissions = Table(
    "role_permissions",
    db.metadata,
    Column("role_id", String(64), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", String(64), ForeignKey("permissions.id"), primary_key=True),
)


class UserModel(db.Model):
    """Persistence model for users."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    roles: Mapped[list[RoleModel]] = relationship(
        "RoleModel",
        secondary=user_roles,
        lazy="selectin",
    )


class RoleModel(db.Model):
    """Persistence model for roles."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    permissions: Mapped[list[PermissionModel]] = relationship(
        "PermissionModel",
        secondary=role_permissions,
        lazy="selectin",
    )


class PermissionModel(db.Model):
    """Persistence model for permissions."""

    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)