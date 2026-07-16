"""SQLAlchemy persistence models for the Organization domain."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ros.core.extensions import db


class OrganizationModel(db.Model):
    """Persistence model for organizations."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    tax_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    branches: Mapped[list[BranchModel]] = relationship("BranchModel", back_populates="organization", lazy="selectin")


class BranchModel(db.Model):
    """Persistence model for branches."""

    __tablename__ = "branches"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_branches_organization_code"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped[OrganizationModel] = relationship("OrganizationModel", back_populates="branches", lazy="selectin")
    departments: Mapped[list[DepartmentModel]] = relationship("DepartmentModel", back_populates="branch", lazy="selectin")
    employees: Mapped[list[EmployeeModel]] = relationship("EmployeeModel", back_populates="branch", lazy="selectin")


class DepartmentModel(db.Model):
    """Persistence model for departments."""

    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("branch_id", "name", name="uq_departments_branch_name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    branch_id: Mapped[str] = mapped_column(String(64), ForeignKey("branches.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    branch: Mapped[BranchModel] = relationship("BranchModel", back_populates="departments", lazy="selectin")
    employees: Mapped[list[EmployeeModel]] = relationship("EmployeeModel", back_populates="department", lazy="selectin")


class PositionModel(db.Model):
    """Persistence model for positions."""

    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    employees: Mapped[list[EmployeeModel]] = relationship("EmployeeModel", back_populates="position", lazy="selectin")


class EmployeeModel(db.Model):
    """Persistence model for employees."""

    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    branch_id: Mapped[str] = mapped_column(String(64), ForeignKey("branches.id"), nullable=False)
    department_id: Mapped[str] = mapped_column(String(64), ForeignKey("departments.id"), nullable=False)
    position_id: Mapped[str] = mapped_column(String(64), ForeignKey("positions.id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True, unique=True)
    employee_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    branch: Mapped[BranchModel] = relationship("BranchModel", back_populates="employees", lazy="selectin")
    department: Mapped[DepartmentModel] = relationship("DepartmentModel", back_populates="employees", lazy="selectin")
    position: Mapped[PositionModel] = relationship("PositionModel", back_populates="employees", lazy="selectin")
