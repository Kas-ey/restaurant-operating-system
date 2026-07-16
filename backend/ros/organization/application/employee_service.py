"""Application service for employee workflows."""

from __future__ import annotations

from datetime import date
from http import HTTPStatus

from ros.identity.persistence.repositories import UserRepository
from ros.organization.application.base import BaseService
from ros.organization.persistence.models import EmployeeModel
from ros.organization.persistence.repositories import (
    BranchRepository,
    DepartmentRepository,
    EmployeeRepository,
    PositionRepository,
)
from ros.shared.exceptions import ROSException


class EmployeeService(BaseService):
    """Coordinates employee lifecycle and assignment workflows."""

    def __init__(
        self,
        employee_repository: EmployeeRepository | None = None,
        branch_repository: BranchRepository | None = None,
        department_repository: DepartmentRepository | None = None,
        position_repository: PositionRepository | None = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        self._employee_repository = employee_repository or EmployeeRepository()
        self._branch_repository = branch_repository or BranchRepository()
        self._department_repository = department_repository or DepartmentRepository()
        self._position_repository = position_repository or PositionRepository()
        self._user_repository = user_repository or UserRepository()

    def create_employee(
        self,
        employee_id: str,
        branch_id: str,
        department_id: str,
        position_id: str,
        user_id: str | None,
        employee_number: str,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        hire_date: date,
    ) -> EmployeeModel:
        normalized_id = self._require_text(employee_id, "Employee ID is required.")
        normalized_branch_id = self._require_text(branch_id, "Branch ID is required.")
        normalized_department_id = self._require_text(department_id, "Department ID is required.")
        normalized_position_id = self._require_text(position_id, "Position ID is required.")
        normalized_employee_number = self._require_text(employee_number, "Employee number is required.")
        normalized_first_name = self._normalize_name(first_name, "Employee first name is required.")
        normalized_last_name = self._normalize_name(last_name, "Employee last name is required.")
        normalized_phone = self._normalize_phone(phone, "Employee phone is required.")
        normalized_email = self._normalize_email(email, "Employee email is required.")
        normalized_user_id = self._normalize_optional_user_id(user_id)

        self._ensure_branch_exists(normalized_branch_id)
        department = self._ensure_department_exists(normalized_department_id)
        self._ensure_position_exists(normalized_position_id)

        if department.branch_id != normalized_branch_id:
            raise ROSException("Department does not belong to branch.", HTTPStatus.CONFLICT)

        if self._employee_repository.get_by_employee_number(normalized_employee_number) is not None:
            raise ROSException("Employee already exists.", HTTPStatus.CONFLICT)

        if normalized_user_id is not None:
            self._ensure_user_available(normalized_user_id)

        if not isinstance(hire_date, date):
            raise ROSException("Employee hire date is required.", HTTPStatus.BAD_REQUEST)

        model = EmployeeModel(
            id=normalized_id,
            branch_id=normalized_branch_id,
            department_id=normalized_department_id,
            position_id=normalized_position_id,
            user_id=normalized_user_id,
            employee_number=normalized_employee_number,
            first_name=normalized_first_name,
            last_name=normalized_last_name,
            phone=normalized_phone,
            email=normalized_email,
            hire_date=hire_date,
            is_active=True,
        )
        return self._employee_repository.save(model)

    def update_employee(
        self,
        employee_id: str,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        hire_date: date | None = None,
    ) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)

        if first_name is not None:
            model.first_name = self._normalize_name(first_name, "Employee first name is required.")

        if last_name is not None:
            model.last_name = self._normalize_name(last_name, "Employee last name is required.")

        if phone is not None:
            model.phone = self._normalize_phone(phone, "Employee phone is required.")

        if email is not None:
            model.email = self._normalize_email(email, "Employee email is required.")

        if hire_date is not None:
            if not isinstance(hire_date, date):
                raise ROSException("Employee hire date is required.", HTTPStatus.BAD_REQUEST)
            model.hire_date = hire_date

        return self._employee_repository.save(model)

    def activate_employee(self, employee_id: str) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)
        model.is_active = True
        return self._employee_repository.save(model)

    def deactivate_employee(self, employee_id: str) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)
        model.is_active = False
        return self._employee_repository.save(model)

    def get_employee(self, employee_id: str) -> EmployeeModel:
        return self._get_existing_employee(employee_id)

    def list_employees(self) -> list[EmployeeModel]:
        return self._employee_repository.get_all()

    def delete_employee(self, employee_id: str) -> None:
        model = self._get_existing_employee(employee_id)
        self._employee_repository.delete(model.id)

    def assign_user(self, employee_id: str, user_id: str) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)
        normalized_user_id = self._require_text(user_id, "User ID is required.")
        self._ensure_user_available(normalized_user_id, employee_id=model.id)
        model.user_id = normalized_user_id
        return self._employee_repository.save(model)

    def remove_user(self, employee_id: str) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)
        model.user_id = None
        return self._employee_repository.save(model)

    def transfer_department(self, employee_id: str, department_id: str) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)
        normalized_department_id = self._require_text(department_id, "Department ID is required.")
        department = self._ensure_department_exists(normalized_department_id)
        if department.branch_id != model.branch_id:
            raise ROSException("Department does not belong to branch.", HTTPStatus.CONFLICT)
        model.department_id = department.id
        return self._employee_repository.save(model)

    def transfer_branch(self, employee_id: str, branch_id: str, department_id: str) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)
        normalized_branch_id = self._require_text(branch_id, "Branch ID is required.")
        normalized_department_id = self._require_text(department_id, "Department ID is required.")

        self._ensure_branch_exists(normalized_branch_id)
        department = self._ensure_department_exists(normalized_department_id)
        if department.branch_id != normalized_branch_id:
            raise ROSException("Department does not belong to branch.", HTTPStatus.CONFLICT)

        model.branch_id = normalized_branch_id
        model.department_id = normalized_department_id
        return self._employee_repository.save(model)

    def change_position(self, employee_id: str, position_id: str) -> EmployeeModel:
        model = self._get_existing_employee(employee_id)
        normalized_position_id = self._require_text(position_id, "Position ID is required.")
        self._ensure_position_exists(normalized_position_id)
        model.position_id = normalized_position_id
        return self._employee_repository.save(model)

    def _get_existing_employee(self, employee_id: str) -> EmployeeModel:
        normalized_id = self._require_text(employee_id, "Employee ID is required.")
        model = self._employee_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Employee not found.", HTTPStatus.NOT_FOUND)
        return model

    def _ensure_branch_exists(self, branch_id: str) -> None:
        if not self._branch_repository.exists(branch_id):
            raise ROSException("Branch not found.", HTTPStatus.NOT_FOUND)

    def _ensure_department_exists(self, department_id: str):
        model = self._department_repository.get_by_id(department_id)
        if model is None:
            raise ROSException("Department not found.", HTTPStatus.NOT_FOUND)
        return model

    def _ensure_position_exists(self, position_id: str) -> None:
        if not self._position_repository.exists(position_id):
            raise ROSException("Position not found.", HTTPStatus.NOT_FOUND)

    def _ensure_user_available(self, user_id: str, employee_id: str | None = None) -> None:
        if not self._user_repository.exists(user_id):
            raise ROSException("User not found.", HTTPStatus.NOT_FOUND)

        existing = self._employee_repository.get_by_user_id(user_id)
        if existing is not None and existing.id != employee_id:
            raise ROSException("User already assigned to an employee.", HTTPStatus.CONFLICT)

    def _normalize_optional_user_id(self, user_id: str | None) -> str | None:
        if user_id is None:
            return None
        return self._require_text(user_id, "User ID is required.")
