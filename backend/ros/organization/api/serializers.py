"""Serialization helpers for organization API responses."""

from __future__ import annotations

from ros.organization.persistence.models import BranchModel, DepartmentModel, EmployeeModel, OrganizationModel, PositionModel


def organization_to_dict(model: OrganizationModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "legal_name": model.legal_name,
        "registration_number": model.registration_number,
        "tax_number": model.tax_number,
        "email": model.email,
        "phone": model.phone,
        "is_active": model.is_active,
    }


def branch_to_dict(model: BranchModel) -> dict:
    return {
        "id": model.id,
        "organization_id": model.organization_id,
        "name": model.name,
        "code": model.code,
        "address": model.address,
        "city": model.city,
        "country": model.country,
        "phone": model.phone,
        "email": model.email,
        "is_active": model.is_active,
    }


def department_to_dict(model: DepartmentModel) -> dict:
    return {
        "id": model.id,
        "branch_id": model.branch_id,
        "name": model.name,
        "description": model.description,
        "is_active": model.is_active,
    }


def position_to_dict(model: PositionModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "is_active": model.is_active,
    }


def employee_to_dict(model: EmployeeModel) -> dict:
    return {
        "id": model.id,
        "branch_id": model.branch_id,
        "department_id": model.department_id,
        "position_id": model.position_id,
        "user_id": model.user_id,
        "employee_number": model.employee_number,
        "first_name": model.first_name,
        "last_name": model.last_name,
        "phone": model.phone,
        "email": model.email,
        "hire_date": model.hire_date.isoformat(),
        "is_active": model.is_active,
    }
