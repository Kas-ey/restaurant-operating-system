"""Application service for department workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.organization.application.base import BaseService
from ros.organization.persistence.models import DepartmentModel
from ros.organization.persistence.repositories import BranchRepository, DepartmentRepository, EmployeeRepository
from ros.shared.exceptions import ROSException


class DepartmentService(BaseService):
    """Coordinates department management workflows."""

    def __init__(
        self,
        department_repository: DepartmentRepository | None = None,
        branch_repository: BranchRepository | None = None,
        employee_repository: EmployeeRepository | None = None,
    ) -> None:
        self._department_repository = department_repository or DepartmentRepository()
        self._branch_repository = branch_repository or BranchRepository()
        self._employee_repository = employee_repository or EmployeeRepository()

    def create_department(
        self,
        department_id: str,
        branch_id: str,
        name: str,
        description: str,
    ) -> DepartmentModel:
        normalized_id = self._require_text(department_id, "Department ID is required.")
        normalized_branch_id = self._require_text(branch_id, "Branch ID is required.")
        normalized_name = self._normalize_name(name, "Department name is required.")
        normalized_description = self._normalize_description(description, "Department description is required.")

        if not self._branch_repository.exists(normalized_branch_id):
            raise ROSException("Branch not found.", HTTPStatus.NOT_FOUND)

        existing = self._department_repository.get_by_name(normalized_branch_id, normalized_name)
        if existing is not None:
            raise ROSException("Department already exists.", HTTPStatus.CONFLICT)

        model = DepartmentModel(
            id=normalized_id,
            branch_id=normalized_branch_id,
            name=normalized_name,
            description=normalized_description,
            is_active=True,
        )
        return self._department_repository.save(model)

    def update_department(
        self,
        department_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> DepartmentModel:
        model = self._get_existing_department(department_id)

        if name is not None:
            normalized_name = self._normalize_name(name, "Department name is required.")
            existing = self._department_repository.get_by_name(model.branch_id, normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Department already exists.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if description is not None:
            model.description = self._normalize_description(description, "Department description is required.")

        return self._department_repository.save(model)

    def activate_department(self, department_id: str) -> DepartmentModel:
        model = self._get_existing_department(department_id)
        model.is_active = True
        return self._department_repository.save(model)

    def deactivate_department(self, department_id: str) -> DepartmentModel:
        model = self._get_existing_department(department_id)
        model.is_active = False
        return self._department_repository.save(model)

    def get_department(self, department_id: str) -> DepartmentModel:
        return self._get_existing_department(department_id)

    def list_departments(self) -> list[DepartmentModel]:
        return self._department_repository.get_all()

    def delete_department(self, department_id: str) -> None:
        model = self._get_existing_department(department_id)
        if self._employee_repository.list_by_department(model.id):
            raise ROSException("Cannot delete department with existing employees.", HTTPStatus.CONFLICT)
        self._department_repository.delete(model.id)

    def _get_existing_department(self, department_id: str) -> DepartmentModel:
        normalized_id = self._require_text(department_id, "Department ID is required.")
        model = self._department_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Department not found.", HTTPStatus.NOT_FOUND)
        return model
