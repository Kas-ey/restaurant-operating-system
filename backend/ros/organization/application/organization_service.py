"""Application service for organization workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.organization.application.base import BaseService
from ros.organization.persistence.models import OrganizationModel
from ros.organization.persistence.repositories import BranchRepository, OrganizationRepository
from ros.shared.exceptions import ROSException


class OrganizationService(BaseService):
    """Coordinates organization management workflows."""

    def __init__(
        self,
        organization_repository: OrganizationRepository | None = None,
        branch_repository: BranchRepository | None = None,
    ) -> None:
        self._organization_repository = organization_repository or OrganizationRepository()
        self._branch_repository = branch_repository or BranchRepository()

    def create_organization(
        self,
        organization_id: str,
        name: str,
        legal_name: str,
        registration_number: str,
        tax_number: str,
        email: str,
        phone: str,
    ) -> OrganizationModel:
        normalized_id = self._require_text(organization_id, "Organization ID is required.")
        normalized_name = self._normalize_name(name, "Organization name is required.")
        normalized_legal_name = self._normalize_name(legal_name, "Organization legal name is required.")
        normalized_registration = self._require_text(
            registration_number,
            "Organization registration number is required.",
        )
        normalized_tax_number = self._require_text(tax_number, "Organization tax number is required.")
        normalized_email = self._normalize_email(email, "Organization email is required.")
        normalized_phone = self._normalize_phone(phone, "Organization phone is required.")

        if self._organization_repository.get_by_name(normalized_name) is not None:
            raise ROSException("Organization already exists.", HTTPStatus.CONFLICT)
        if self._organization_repository.get_by_registration_number(normalized_registration) is not None:
            raise ROSException("Organization already exists.", HTTPStatus.CONFLICT)
        if self._organization_repository.get_by_tax_number(normalized_tax_number) is not None:
            raise ROSException("Organization already exists.", HTTPStatus.CONFLICT)

        model = OrganizationModel(
            id=normalized_id,
            name=normalized_name,
            legal_name=normalized_legal_name,
            registration_number=normalized_registration,
            tax_number=normalized_tax_number,
            email=normalized_email,
            phone=normalized_phone,
            is_active=True,
        )
        return self._organization_repository.save(model)

    def update_organization(
        self,
        organization_id: str,
        *,
        name: str | None = None,
        legal_name: str | None = None,
        registration_number: str | None = None,
        tax_number: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> OrganizationModel:
        model = self._get_existing_organization(organization_id)

        if name is not None:
            normalized_name = self._normalize_name(name, "Organization name is required.")
            existing = self._organization_repository.get_by_name(normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Organization already exists.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if legal_name is not None:
            model.legal_name = self._normalize_name(legal_name, "Organization legal name is required.")

        if registration_number is not None:
            normalized_registration = self._require_text(
                registration_number,
                "Organization registration number is required.",
            )
            existing = self._organization_repository.get_by_registration_number(normalized_registration)
            if existing is not None and existing.id != model.id:
                raise ROSException("Organization already exists.", HTTPStatus.CONFLICT)
            model.registration_number = normalized_registration

        if tax_number is not None:
            normalized_tax_number = self._require_text(tax_number, "Organization tax number is required.")
            existing = self._organization_repository.get_by_tax_number(normalized_tax_number)
            if existing is not None and existing.id != model.id:
                raise ROSException("Organization already exists.", HTTPStatus.CONFLICT)
            model.tax_number = normalized_tax_number

        if email is not None:
            model.email = self._normalize_email(email, "Organization email is required.")

        if phone is not None:
            model.phone = self._normalize_phone(phone, "Organization phone is required.")

        return self._organization_repository.save(model)

    def activate_organization(self, organization_id: str) -> OrganizationModel:
        model = self._get_existing_organization(organization_id)
        model.is_active = True
        return self._organization_repository.save(model)

    def deactivate_organization(self, organization_id: str) -> OrganizationModel:
        model = self._get_existing_organization(organization_id)
        model.is_active = False
        return self._organization_repository.save(model)

    def get_organization(self, organization_id: str) -> OrganizationModel:
        return self._get_existing_organization(organization_id)

    def list_organizations(self) -> list[OrganizationModel]:
        return self._organization_repository.get_all()

    def delete_organization(self, organization_id: str) -> None:
        model = self._get_existing_organization(organization_id)
        if self._branch_repository.list_by_organization(model.id):
            raise ROSException("Cannot delete organization with existing branches.", HTTPStatus.CONFLICT)
        self._organization_repository.delete(model.id)

    def _get_existing_organization(self, organization_id: str) -> OrganizationModel:
        normalized_id = self._require_text(organization_id, "Organization ID is required.")
        model = self._organization_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Organization not found.", HTTPStatus.NOT_FOUND)
        return model
