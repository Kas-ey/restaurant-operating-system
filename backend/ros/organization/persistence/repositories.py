"""Repository implementations for Organization persistence operations."""

from __future__ import annotations

from sqlalchemy import select

from ros.core.extensions import db

from .models import BranchModel, DepartmentModel, EmployeeModel, OrganizationModel, PositionModel


class OrganizationRepository:
    """Persistence repository for organizations."""

    def get_by_id(self, organization_id: str) -> OrganizationModel | None:
        return db.session.get(OrganizationModel, organization_id)

    def get_by_name(self, name: str) -> OrganizationModel | None:
        return db.session.scalar(select(OrganizationModel).where(OrganizationModel.name == name))

    def get_by_registration_number(self, registration_number: str) -> OrganizationModel | None:
        return db.session.scalar(
            select(OrganizationModel).where(OrganizationModel.registration_number == registration_number)
        )

    def get_by_tax_number(self, tax_number: str) -> OrganizationModel | None:
        return db.session.scalar(select(OrganizationModel).where(OrganizationModel.tax_number == tax_number))

    def get_all(self) -> list[OrganizationModel]:
        return db.session.scalars(select(OrganizationModel)).all()

    def save(self, model: OrganizationModel) -> OrganizationModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, organization_id: str) -> None:
        model = db.session.get(OrganizationModel, organization_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, organization_id: str) -> bool:
        return db.session.get(OrganizationModel, organization_id) is not None


class BranchRepository:
    """Persistence repository for branches."""

    def get_by_id(self, branch_id: str) -> BranchModel | None:
        return db.session.get(BranchModel, branch_id)

    def get_by_name(self, organization_id: str, name: str) -> BranchModel | None:
        return db.session.scalar(
            select(BranchModel).where(BranchModel.organization_id == organization_id, BranchModel.name == name)
        )

    def get_by_code(self, organization_id: str, code: str) -> BranchModel | None:
        return db.session.scalar(
            select(BranchModel).where(BranchModel.organization_id == organization_id, BranchModel.code == code)
        )

    def get_all(self) -> list[BranchModel]:
        return db.session.scalars(select(BranchModel)).all()

    def list_by_organization(self, organization_id: str) -> list[BranchModel]:
        return db.session.scalars(select(BranchModel).where(BranchModel.organization_id == organization_id)).all()

    def save(self, model: BranchModel) -> BranchModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, branch_id: str) -> None:
        model = db.session.get(BranchModel, branch_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, branch_id: str) -> bool:
        return db.session.get(BranchModel, branch_id) is not None


class DepartmentRepository:
    """Persistence repository for departments."""

    def get_by_id(self, department_id: str) -> DepartmentModel | None:
        return db.session.get(DepartmentModel, department_id)

    def get_by_name(self, branch_id: str, name: str) -> DepartmentModel | None:
        return db.session.scalar(
            select(DepartmentModel).where(DepartmentModel.branch_id == branch_id, DepartmentModel.name == name)
        )

    def get_all(self) -> list[DepartmentModel]:
        return db.session.scalars(select(DepartmentModel)).all()

    def list_by_branch(self, branch_id: str) -> list[DepartmentModel]:
        return db.session.scalars(select(DepartmentModel).where(DepartmentModel.branch_id == branch_id)).all()

    def save(self, model: DepartmentModel) -> DepartmentModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, department_id: str) -> None:
        model = db.session.get(DepartmentModel, department_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, department_id: str) -> bool:
        return db.session.get(DepartmentModel, department_id) is not None


class PositionRepository:
    """Persistence repository for positions."""

    def get_by_id(self, position_id: str) -> PositionModel | None:
        return db.session.get(PositionModel, position_id)

    def get_by_name(self, name: str) -> PositionModel | None:
        return db.session.scalar(select(PositionModel).where(PositionModel.name == name))

    def get_all(self) -> list[PositionModel]:
        return db.session.scalars(select(PositionModel)).all()

    def save(self, model: PositionModel) -> PositionModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, position_id: str) -> None:
        model = db.session.get(PositionModel, position_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, position_id: str) -> bool:
        return db.session.get(PositionModel, position_id) is not None


class EmployeeRepository:
    """Persistence repository for employees."""

    def get_by_id(self, employee_id: str) -> EmployeeModel | None:
        return db.session.get(EmployeeModel, employee_id)

    def get_by_employee_number(self, employee_number: str) -> EmployeeModel | None:
        return db.session.scalar(select(EmployeeModel).where(EmployeeModel.employee_number == employee_number))

    def get_by_user_id(self, user_id: str) -> EmployeeModel | None:
        return db.session.scalar(select(EmployeeModel).where(EmployeeModel.user_id == user_id))

    def get_all(self) -> list[EmployeeModel]:
        return db.session.scalars(select(EmployeeModel)).all()

    def list_by_branch(self, branch_id: str) -> list[EmployeeModel]:
        return db.session.scalars(select(EmployeeModel).where(EmployeeModel.branch_id == branch_id)).all()

    def list_by_department(self, department_id: str) -> list[EmployeeModel]:
        return db.session.scalars(select(EmployeeModel).where(EmployeeModel.department_id == department_id)).all()

    def list_by_position(self, position_id: str) -> list[EmployeeModel]:
        return db.session.scalars(select(EmployeeModel).where(EmployeeModel.position_id == position_id)).all()

    def save(self, model: EmployeeModel) -> EmployeeModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, employee_id: str) -> None:
        model = db.session.get(EmployeeModel, employee_id)
        if model is not None:
            db.session.delete(model)

    def exists(self, employee_id: str) -> bool:
        return db.session.get(EmployeeModel, employee_id) is not None
