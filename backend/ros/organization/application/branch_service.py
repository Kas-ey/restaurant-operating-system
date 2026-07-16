"""Application service for branch workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.organization.application.base import BaseService
from ros.organization.persistence.models import BranchModel
from ros.organization.persistence.repositories import (
    BranchRepository,
    DepartmentRepository,
    EmployeeRepository,
    OrganizationRepository,
)
from ros.shared.exceptions import ROSException


class BranchService(BaseService):
    """Coordinates branch management workflows."""

    def __init__(
        self,
        branch_repository: BranchRepository | None = None,
        organization_repository: OrganizationRepository | None = None,
        department_repository: DepartmentRepository | None = None,
        employee_repository: EmployeeRepository | None = None,
    ) -> None:
        self._branch_repository = branch_repository or BranchRepository()
        self._organization_repository = organization_repository or OrganizationRepository()
        self._department_repository = department_repository or DepartmentRepository()
        self._employee_repository = employee_repository or EmployeeRepository()

    def create_branch(
        self,
        branch_id: str,
        organization_id: str,
        name: str,
        code: str,
        address: str,
        city: str,
        country: str,
        phone: str,
        email: str,
    ) -> BranchModel:
        normalized_id = self._require_text(branch_id, "Branch ID is required.")
        normalized_organization_id = self._require_text(organization_id, "Organization ID is required.")
        normalized_name = self._normalize_name(name, "Branch name is required.")
        normalized_code = self._normalize_code(code, "Branch code is required.")
        normalized_address = self._require_text(address, "Branch address is required.")
        normalized_city = self._require_text(city, "Branch city is required.")
        normalized_country = self._require_text(country, "Branch country is required.")
        normalized_phone = self._normalize_phone(phone, "Branch phone is required.")
        normalized_email = self._normalize_email(email, "Branch email is required.")

        if not self._organization_repository.exists(normalized_organization_id):
            raise ROSException("Organization not found.", HTTPStatus.NOT_FOUND)

        existing = self._branch_repository.get_by_code(normalized_organization_id, normalized_code)
        if existing is not None:
            raise ROSException("Branch already exists.", HTTPStatus.CONFLICT)

        model = BranchModel(
            id=normalized_id,
            organization_id=normalized_organization_id,
            name=normalized_name,
            code=normalized_code,
            address=normalized_address,
            city=normalized_city,
            country=normalized_country,
            phone=normalized_phone,
            email=normalized_email,
            is_active=True,
        )
        return self._branch_repository.save(model)

    def update_branch(
        self,
        branch_id: str,
        *,
        name: str | None = None,
        code: str | None = None,
        address: str | None = None,
        city: str | None = None,
        country: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> BranchModel:
        model = self._get_existing_branch(branch_id)

        if name is not None:
            model.name = self._normalize_name(name, "Branch name is required.")

        if code is not None:
            normalized_code = self._normalize_code(code, "Branch code is required.")
            existing = self._branch_repository.get_by_code(model.organization_id, normalized_code)
            if existing is not None and existing.id != model.id:
                raise ROSException("Branch already exists.", HTTPStatus.CONFLICT)
            model.code = normalized_code

        if address is not None:
            model.address = self._require_text(address, "Branch address is required.")

        if city is not None:
            model.city = self._require_text(city, "Branch city is required.")

        if country is not None:
            model.country = self._require_text(country, "Branch country is required.")

        if phone is not None:
            model.phone = self._normalize_phone(phone, "Branch phone is required.")

        if email is not None:
            model.email = self._normalize_email(email, "Branch email is required.")

        return self._branch_repository.save(model)

    def activate_branch(self, branch_id: str) -> BranchModel:
        model = self._get_existing_branch(branch_id)
        model.is_active = True
        return self._branch_repository.save(model)

    def deactivate_branch(self, branch_id: str) -> BranchModel:
        model = self._get_existing_branch(branch_id)
        model.is_active = False
        return self._branch_repository.save(model)

    def get_branch(self, branch_id: str) -> BranchModel:
        return self._get_existing_branch(branch_id)

    def list_branches(self) -> list[BranchModel]:
        return self._branch_repository.get_all()

    def delete_branch(self, branch_id: str) -> None:
        model = self._get_existing_branch(branch_id)
        if self._department_repository.list_by_branch(model.id):
            raise ROSException("Cannot delete branch with existing departments.", HTTPStatus.CONFLICT)
        if self._employee_repository.list_by_branch(model.id):
            raise ROSException("Cannot delete branch with existing employees.", HTTPStatus.CONFLICT)
        self._branch_repository.delete(model.id)

    def _get_existing_branch(self, branch_id: str) -> BranchModel:
        normalized_id = self._require_text(branch_id, "Branch ID is required.")
        model = self._branch_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Branch not found.", HTTPStatus.NOT_FOUND)
        return model
