"""HTTP routes for organization application services."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, request
from flask.typing import ResponseReturnValue

from ros.core.extensions import db
from ros.http.errors import error_response
from ros.http.responses import success_response
from ros.identity.auth import require_authenticated, require_permission
from ros.organization.application import (
    BranchService,
    DepartmentService,
    EmployeeService,
    OrganizationService,
    PositionService,
)
from ros.shared.exceptions import ROSException

from .schemas import (
    validate_assign_user_payload,
    validate_change_position_payload,
    validate_create_branch_payload,
    validate_create_department_payload,
    validate_create_employee_payload,
    validate_create_organization_payload,
    validate_create_position_payload,
    validate_transfer_branch_payload,
    validate_transfer_department_payload,
    validate_update_branch_payload,
    validate_update_department_payload,
    validate_update_employee_payload,
    validate_update_organization_payload,
    validate_update_position_payload,
)
from .serializers import (
    branch_to_dict,
    department_to_dict,
    employee_to_dict,
    organization_to_dict,
    position_to_dict,
)


organization_bp = Blueprint("organization", __name__, url_prefix="/api/v1")


@organization_bp.post("/organizations")
@require_authenticated
@require_permission("organization.create")
def create_organization() -> ResponseReturnValue:
    organization_service = OrganizationService()
    payload = _require_json_body()
    data = validate_create_organization_payload(payload)
    model = organization_service.create_organization(
        organization_id=data["id"],
        name=data["name"],
        legal_name=data["legal_name"],
        registration_number=data["registration_number"],
        tax_number=data["tax_number"],
        email=data["email"],
        phone=data["phone"],
    )
    return _commit_and_respond(organization_to_dict(model), HTTPStatus.CREATED)


@organization_bp.get("/organizations")
@require_authenticated
@require_permission("organization.read")
def list_organizations() -> ResponseReturnValue:
    organization_service = OrganizationService()
    models = organization_service.list_organizations()
    return success_response([organization_to_dict(model) for model in models], HTTPStatus.OK)


@organization_bp.get("/organizations/<string:organization_id>")
@require_authenticated
@require_permission("organization.read")
def get_organization(organization_id: str) -> ResponseReturnValue:
    organization_service = OrganizationService()
    model = organization_service.get_organization(organization_id)
    return success_response(organization_to_dict(model), HTTPStatus.OK)


@organization_bp.put("/organizations/<string:organization_id>")
@require_authenticated
@require_permission("organization.update")
def update_organization(organization_id: str) -> ResponseReturnValue:
    organization_service = OrganizationService()
    payload = _require_json_body()
    data = validate_update_organization_payload(payload)
    model = organization_service.update_organization(
        organization_id,
        name=data.get("name"),
        legal_name=data.get("legal_name"),
        registration_number=data.get("registration_number"),
        tax_number=data.get("tax_number"),
        email=data.get("email"),
        phone=data.get("phone"),
    )
    return _commit_and_respond(organization_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/organizations/<string:organization_id>/activate")
@require_authenticated
@require_permission("organization.update")
def activate_organization(organization_id: str) -> ResponseReturnValue:
    organization_service = OrganizationService()
    model = organization_service.activate_organization(organization_id)
    return _commit_and_respond(organization_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/organizations/<string:organization_id>/deactivate")
@require_authenticated
@require_permission("organization.update")
def deactivate_organization(organization_id: str) -> ResponseReturnValue:
    organization_service = OrganizationService()
    model = organization_service.deactivate_organization(organization_id)
    return _commit_and_respond(organization_to_dict(model), HTTPStatus.OK)


@organization_bp.delete("/organizations/<string:organization_id>")
@require_authenticated
@require_permission("organization.delete")
def delete_organization(organization_id: str) -> ResponseReturnValue:
    organization_service = OrganizationService()
    organization_service.delete_organization(organization_id)
    return _commit_and_respond({"message": "Organization deleted."}, HTTPStatus.OK)


@organization_bp.post("/branches")
@require_authenticated
@require_permission("branch.create")
def create_branch() -> ResponseReturnValue:
    branch_service = BranchService()
    payload = _require_json_body()
    data = validate_create_branch_payload(payload)
    model = branch_service.create_branch(
        branch_id=data["id"],
        organization_id=data["organization_id"],
        name=data["name"],
        code=data["code"],
        address=data["address"],
        city=data["city"],
        country=data["country"],
        phone=data["phone"],
        email=data["email"],
    )
    return _commit_and_respond(branch_to_dict(model), HTTPStatus.CREATED)


@organization_bp.get("/branches")
@require_authenticated
@require_permission("branch.read")
def list_branches() -> ResponseReturnValue:
    branch_service = BranchService()
    models = branch_service.list_branches()
    return success_response([branch_to_dict(model) for model in models], HTTPStatus.OK)


@organization_bp.get("/branches/<string:branch_id>")
@require_authenticated
@require_permission("branch.read")
def get_branch(branch_id: str) -> ResponseReturnValue:
    branch_service = BranchService()
    model = branch_service.get_branch(branch_id)
    return success_response(branch_to_dict(model), HTTPStatus.OK)


@organization_bp.put("/branches/<string:branch_id>")
@require_authenticated
@require_permission("branch.update")
def update_branch(branch_id: str) -> ResponseReturnValue:
    branch_service = BranchService()
    payload = _require_json_body()
    data = validate_update_branch_payload(payload)
    model = branch_service.update_branch(
        branch_id,
        name=data.get("name"),
        code=data.get("code"),
        address=data.get("address"),
        city=data.get("city"),
        country=data.get("country"),
        phone=data.get("phone"),
        email=data.get("email"),
    )
    return _commit_and_respond(branch_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/branches/<string:branch_id>/activate")
@require_authenticated
@require_permission("branch.update")
def activate_branch(branch_id: str) -> ResponseReturnValue:
    branch_service = BranchService()
    model = branch_service.activate_branch(branch_id)
    return _commit_and_respond(branch_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/branches/<string:branch_id>/deactivate")
@require_authenticated
@require_permission("branch.update")
def deactivate_branch(branch_id: str) -> ResponseReturnValue:
    branch_service = BranchService()
    model = branch_service.deactivate_branch(branch_id)
    return _commit_and_respond(branch_to_dict(model), HTTPStatus.OK)


@organization_bp.delete("/branches/<string:branch_id>")
@require_authenticated
@require_permission("branch.delete")
def delete_branch(branch_id: str) -> ResponseReturnValue:
    branch_service = BranchService()
    branch_service.delete_branch(branch_id)
    return _commit_and_respond({"message": "Branch deleted."}, HTTPStatus.OK)


@organization_bp.post("/departments")
@require_authenticated
@require_permission("department.create")
def create_department() -> ResponseReturnValue:
    department_service = DepartmentService()
    payload = _require_json_body()
    data = validate_create_department_payload(payload)
    model = department_service.create_department(
        department_id=data["id"],
        branch_id=data["branch_id"],
        name=data["name"],
        description=data["description"],
    )
    return _commit_and_respond(department_to_dict(model), HTTPStatus.CREATED)


@organization_bp.get("/departments")
@require_authenticated
@require_permission("department.read")
def list_departments() -> ResponseReturnValue:
    department_service = DepartmentService()
    models = department_service.list_departments()
    return success_response([department_to_dict(model) for model in models], HTTPStatus.OK)


@organization_bp.get("/departments/<string:department_id>")
@require_authenticated
@require_permission("department.read")
def get_department(department_id: str) -> ResponseReturnValue:
    department_service = DepartmentService()
    model = department_service.get_department(department_id)
    return success_response(department_to_dict(model), HTTPStatus.OK)


@organization_bp.put("/departments/<string:department_id>")
@require_authenticated
@require_permission("department.update")
def update_department(department_id: str) -> ResponseReturnValue:
    department_service = DepartmentService()
    payload = _require_json_body()
    data = validate_update_department_payload(payload)
    model = department_service.update_department(
        department_id,
        name=data.get("name"),
        description=data.get("description"),
    )
    return _commit_and_respond(department_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/departments/<string:department_id>/activate")
@require_authenticated
@require_permission("department.update")
def activate_department(department_id: str) -> ResponseReturnValue:
    department_service = DepartmentService()
    model = department_service.activate_department(department_id)
    return _commit_and_respond(department_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/departments/<string:department_id>/deactivate")
@require_authenticated
@require_permission("department.update")
def deactivate_department(department_id: str) -> ResponseReturnValue:
    department_service = DepartmentService()
    model = department_service.deactivate_department(department_id)
    return _commit_and_respond(department_to_dict(model), HTTPStatus.OK)


@organization_bp.delete("/departments/<string:department_id>")
@require_authenticated
@require_permission("department.delete")
def delete_department(department_id: str) -> ResponseReturnValue:
    department_service = DepartmentService()
    department_service.delete_department(department_id)
    return _commit_and_respond({"message": "Department deleted."}, HTTPStatus.OK)


@organization_bp.post("/positions")
@require_authenticated
@require_permission("position.create")
def create_position() -> ResponseReturnValue:
    position_service = PositionService()
    payload = _require_json_body()
    data = validate_create_position_payload(payload)
    model = position_service.create_position(
        position_id=data["id"],
        name=data["name"],
        description=data["description"],
    )
    return _commit_and_respond(position_to_dict(model), HTTPStatus.CREATED)


@organization_bp.get("/positions")
@require_authenticated
@require_permission("position.read")
def list_positions() -> ResponseReturnValue:
    position_service = PositionService()
    models = position_service.list_positions()
    return success_response([position_to_dict(model) for model in models], HTTPStatus.OK)


@organization_bp.get("/positions/<string:position_id>")
@require_authenticated
@require_permission("position.read")
def get_position(position_id: str) -> ResponseReturnValue:
    position_service = PositionService()
    model = position_service.get_position(position_id)
    return success_response(position_to_dict(model), HTTPStatus.OK)


@organization_bp.put("/positions/<string:position_id>")
@require_authenticated
@require_permission("position.update")
def update_position(position_id: str) -> ResponseReturnValue:
    position_service = PositionService()
    payload = _require_json_body()
    data = validate_update_position_payload(payload)
    model = position_service.update_position(
        position_id,
        name=data.get("name"),
        description=data.get("description"),
    )
    return _commit_and_respond(position_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/positions/<string:position_id>/activate")
@require_authenticated
@require_permission("position.update")
def activate_position(position_id: str) -> ResponseReturnValue:
    position_service = PositionService()
    model = position_service.activate_position(position_id)
    return _commit_and_respond(position_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/positions/<string:position_id>/deactivate")
@require_authenticated
@require_permission("position.update")
def deactivate_position(position_id: str) -> ResponseReturnValue:
    position_service = PositionService()
    model = position_service.deactivate_position(position_id)
    return _commit_and_respond(position_to_dict(model), HTTPStatus.OK)


@organization_bp.delete("/positions/<string:position_id>")
@require_authenticated
@require_permission("position.delete")
def delete_position(position_id: str) -> ResponseReturnValue:
    position_service = PositionService()
    position_service.delete_position(position_id)
    return _commit_and_respond({"message": "Position deleted."}, HTTPStatus.OK)


@organization_bp.post("/employees")
@require_authenticated
@require_permission("employee.create")
def create_employee() -> ResponseReturnValue:
    employee_service = EmployeeService()
    payload = _require_json_body()
    data = validate_create_employee_payload(payload)
    model = employee_service.create_employee(
        employee_id=data["id"],
        branch_id=data["branch_id"],
        department_id=data["department_id"],
        position_id=data["position_id"],
        user_id=data.get("user_id"),
        employee_number=data["employee_number"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
        email=data["email"],
        hire_date=data["hire_date"],
    )
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.CREATED)


@organization_bp.get("/employees")
@require_authenticated
@require_permission("employee.read")
def list_employees() -> ResponseReturnValue:
    employee_service = EmployeeService()
    models = employee_service.list_employees()
    return success_response([employee_to_dict(model) for model in models], HTTPStatus.OK)


@organization_bp.get("/employees/<string:employee_id>")
@require_authenticated
@require_permission("employee.read")
def get_employee(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    model = employee_service.get_employee(employee_id)
    return success_response(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.put("/employees/<string:employee_id>")
@require_authenticated
@require_permission("employee.update")
def update_employee(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    payload = _require_json_body()
    data = validate_update_employee_payload(payload)
    model = employee_service.update_employee(
        employee_id,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        email=data.get("email"),
        hire_date=data.get("hire_date"),
    )
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/employees/<string:employee_id>/activate")
@require_authenticated
@require_permission("employee.update")
def activate_employee(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    model = employee_service.activate_employee(employee_id)
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/employees/<string:employee_id>/deactivate")
@require_authenticated
@require_permission("employee.update")
def deactivate_employee(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    model = employee_service.deactivate_employee(employee_id)
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.delete("/employees/<string:employee_id>")
@require_authenticated
@require_permission("employee.delete")
def delete_employee(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    employee_service.delete_employee(employee_id)
    return _commit_and_respond({"message": "Employee deleted."}, HTTPStatus.OK)


@organization_bp.patch("/employees/<string:employee_id>/assign-user")
@require_authenticated
@require_permission("employee.update")
def assign_user(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    payload = _require_json_body()
    data = validate_assign_user_payload(payload)
    model = employee_service.assign_user(employee_id, data["user_id"])
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/employees/<string:employee_id>/remove-user")
@require_authenticated
@require_permission("employee.update")
def remove_user(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    model = employee_service.remove_user(employee_id)
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/employees/<string:employee_id>/transfer-branch")
@require_authenticated
@require_permission("employee.update")
def transfer_branch(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    payload = _require_json_body()
    data = validate_transfer_branch_payload(payload)
    model = employee_service.transfer_branch(employee_id, data["branch_id"], data["department_id"])
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/employees/<string:employee_id>/transfer-department")
@require_authenticated
@require_permission("employee.update")
def transfer_department(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    payload = _require_json_body()
    data = validate_transfer_department_payload(payload)
    model = employee_service.transfer_department(employee_id, data["department_id"])
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.patch("/employees/<string:employee_id>/change-position")
@require_authenticated
@require_permission("employee.update")
def change_position(employee_id: str) -> ResponseReturnValue:
    employee_service = EmployeeService()
    payload = _require_json_body()
    data = validate_change_position_payload(payload)
    model = employee_service.change_position(employee_id, data["position_id"])
    return _commit_and_respond(employee_to_dict(model), HTTPStatus.OK)


@organization_bp.errorhandler(Exception)
def handle_organization_exception(exc: Exception) -> ResponseReturnValue:
    db.session.rollback()
    if isinstance(exc, ROSException):
        return error_response(exc.message, exc.status_code)
    return error_response("Internal server error.", HTTPStatus.INTERNAL_SERVER_ERROR)


def _require_json_body() -> dict:
    payload = request.get_json(silent=True)
    if payload is None:
        raise ROSException("Request body must be valid JSON.", HTTPStatus.BAD_REQUEST)
    if not isinstance(payload, dict):
        raise ROSException("Request body must be a JSON object.", HTTPStatus.BAD_REQUEST)
    return payload


def _commit_and_respond(data, status_code: HTTPStatus) -> ResponseReturnValue:
    db.session.commit()
    return success_response(data, status_code)
