"""Flask routes for recipes and recipe versions."""

from __future__ import annotations

from functools import wraps
from http import HTTPStatus
from typing import Callable

from flask import Blueprint, current_app, g, request
from flask.typing import ResponseReturnValue

from ros.core.extensions import db
from ros.http.errors import error_response
from ros.http.responses import success_response
from ros.identity.auth import require_authenticated
from ros.identity.auth.authentication import AuthenticationService
from ros.identity.auth.authorization import resolve_user_permissions
from ros.shared.exceptions import ROSException

from ..application import (
    RecipeApprovalService,
    RecipeAuditService,
    RecipeEquipmentService,
    RecipeIngredientService,
    RecipePackagingService,
    RecipeSecurityService,
    RecipeQualityService,
    RecipeService,
    RecipeStepService,
    RecipeWasteService,
    RecipeVersionService,
    RecipeYieldService,
    SecretFormulationService,
)
from .schemas import (
    validate_create_equipment_payload,
    validate_create_packaging_payload,
    validate_create_quality_payload,
    validate_create_step_payload,
    validate_create_waste_payload,
    validate_create_yield_payload,
    validate_create_ingredient_payload,
    validate_create_recipe_payload,
    validate_create_secret_formulation_payload,
    validate_create_version_payload,
    validate_secret_formulation_decrypt_payload,
    validate_review_action_payload,
    validate_update_equipment_payload,
    validate_update_packaging_payload,
    validate_update_quality_payload,
    validate_update_step_payload,
    validate_update_waste_payload,
    validate_update_yield_payload,
    validate_update_ingredient_payload,
    validate_update_recipe_payload,
    validate_update_secret_formulation_payload,
)
from .serializers import (
    equipment_to_dict,
    ingredient_to_dict,
    packaging_to_dict,
    quality_to_dict,
    recipe_to_dict,
    step_to_dict,
    secret_formulation_metadata_to_dict,
    waste_to_dict,
    version_to_dict,
    yield_to_dict,
)

recipes_bp = Blueprint("recipes", __name__, url_prefix="/api/v1/recipes")

_recipe_service = RecipeService()
_recipe_version_service = RecipeVersionService()
_recipe_ingredient_service = RecipeIngredientService()
_recipe_step_service = RecipeStepService()
_recipe_yield_service = RecipeYieldService()
_recipe_waste_service = RecipeWasteService()
_recipe_equipment_service = RecipeEquipmentService()
_recipe_packaging_service = RecipePackagingService()
_recipe_quality_service = RecipeQualityService()
_secret_formulation_service = SecretFormulationService()
_recipe_security_service = RecipeSecurityService()
_recipe_approval_service = RecipeApprovalService()
_recipe_audit_service = RecipeAuditService()


def _normalize_permission_name(value: str) -> str:
    return ".".join(value.strip().lower().split())


def _normalized_permissions_for_user(user) -> set[str]:
    return {_normalize_permission_name(permission) for permission in resolve_user_permissions(user)}


def _normalized_role_names_for_user(user) -> set[str]:
    return {_normalize_permission_name(role.name) for role in user.roles}


def _permission_aliases(required_permission: str) -> set[str]:
    return _recipe_security_service.permission_aliases(required_permission)


def _current_user_for_authorization():
    user = getattr(g, "current_user", None)
    if user is not None:
        return user

    auth_service = AuthenticationService()
    token = auth_service.extract_bearer_token(request.headers.get("Authorization"))
    user = auth_service.resolve_current_user(token)
    g.current_user = user
    return user


def _has_permission(required_permission: str, *, user=None) -> bool:
    current_user = user or _current_user_for_authorization()
    return _recipe_security_service.has_permission(
        required_permission=required_permission,
        permissions=_normalized_permissions_for_user(current_user),
        role_names=_normalized_role_names_for_user(current_user),
    )


def require_permission(required_permission: str):
    """Recipes-local permission decorator with legacy and ROS-0612 aliases."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = _current_user_for_authorization()
            if not _has_permission(required_permission, user=user):
                raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _has_classification_access(classification: str, *, user=None) -> bool:
    current_user = user or _current_user_for_authorization()
    return _recipe_security_service.has_classification_access(
        classification=classification,
        permissions=_normalized_permissions_for_user(current_user),
        role_names=_normalized_role_names_for_user(current_user),
    )


def _assert_classification_access(classification: str) -> None:
    if not _has_classification_access(classification):
        raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)


def _configure_secret_formulation_security() -> None:
    extension_security = current_app.extensions.get("recipes_secret_formulation_security", {})
    _secret_formulation_service.configure_providers(
        encryption_provider=extension_security.get("encryption_provider")
        or current_app.config.get("RECIPES_ENCRYPTION_PROVIDER"),
        decryption_provider=extension_security.get("decryption_provider")
        or current_app.config.get("RECIPES_DECRYPTION_PROVIDER"),
        key_provider=extension_security.get("key_provider") or current_app.config.get("RECIPES_KEY_PROVIDER"),
        audit_logger=extension_security.get("audit_logger") or current_app.config.get("RECIPES_AUDIT_LOGGER"),
    )


@recipes_bp.before_request
def _enforce_security_classification() -> None:
    endpoint = (request.endpoint or "").split(".")[-1]
    if endpoint in {
        "create_recipe",
        "list_recipes",
        "list_secret_formulations",
        "create_secret_formulation",
        "decrypt_secret_formulation",
    }:
        return

    view_args = request.view_args or {}
    formulation_id = view_args.get("formulation_id")
    if formulation_id is not None:
        formulation = _secret_formulation_service.get_formulation(formulation_id)
        _assert_classification_access(formulation.security_classification.value)
        return

    recipe_id = view_args.get("recipe_id")
    if recipe_id is None and "version_id" in view_args:
        version = _recipe_version_service.get_version(view_args["version_id"])
        recipe_id = version.recipe_id

    if recipe_id is None:
        return

    recipe = _recipe_service.get_recipe(recipe_id)
    _assert_classification_access(recipe.security_classification.value)


@recipes_bp.errorhandler(Exception)
def handle_recipes_exception(exc: Exception) -> ResponseReturnValue:
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


def _actor() -> str:
    user = getattr(g, "current_user", None)
    user_id = getattr(user, "id", None)
    return str(user_id) if user_id else "system"


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _assert_version_belongs_to_recipe(recipe_id: str, version_id: str) -> None:
    version = _recipe_version_service.get_version(version_id)
    if version.recipe_id != recipe_id:
        raise ROSException("Recipe version not found.", HTTPStatus.NOT_FOUND)


@recipes_bp.post("")
@require_authenticated
@require_permission("recipes.create")
def create_recipe() -> ResponseReturnValue:
    payload = _require_json_body()
    data = validate_create_recipe_payload(payload)
    _assert_classification_access(data["security_classification"])
    recipe = _recipe_service.create_recipe(
        recipe_id=data["id"],
        product_id=data["product_id"],
        code=data["code"],
        name=data["name"],
        description=data["description"],
        security_classification=data["security_classification"],
        created_by=_actor(),
    )
    return _commit_and_respond(recipe_to_dict(recipe), HTTPStatus.CREATED)


@recipes_bp.get("")
@require_authenticated
@require_permission("recipes.read")
def list_recipes() -> ResponseReturnValue:
    recipes = _recipe_service.list_recipes()
    visible = [item for item in recipes if _has_classification_access(item.security_classification.value)]
    return success_response([recipe_to_dict(item) for item in visible], HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>")
@require_authenticated
@require_permission("recipes.read")
def get_recipe(recipe_id: str) -> ResponseReturnValue:
    recipe = _recipe_service.get_recipe(recipe_id)
    return success_response(recipe_to_dict(recipe), HTTPStatus.OK)


@recipes_bp.patch("/<string:recipe_id>")
@require_authenticated
@require_permission("recipes.update")
def update_recipe(recipe_id: str) -> ResponseReturnValue:
    payload = _require_json_body()
    data = validate_update_recipe_payload(payload)
    if "security_classification" in data:
        _assert_classification_access(data["security_classification"])
    recipe = _recipe_service.update_recipe(
        recipe_id,
        name=data.get("name"),
        description=data.get("description"),
        security_classification=data.get("security_classification"),
    )
    return _commit_and_respond(recipe_to_dict(recipe), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>")
@require_authenticated
@require_permission("recipes.delete")
def delete_recipe(recipe_id: str) -> ResponseReturnValue:
    _recipe_service.delete_recipe(recipe_id)
    return _commit_and_respond({"message": "Recipe deleted."}, HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions")
@require_authenticated
@require_permission("recipes.update")
def create_version(recipe_id: str) -> ResponseReturnValue:
    payload = _require_json_body()
    data = validate_create_version_payload(payload)
    version = _recipe_version_service.create_version(
        version_id=data["id"],
        recipe_id=recipe_id,
        change_summary=data["change_summary"],
        created_by=_actor(),
        effective_date=data["effective_date"],
    )
    return _commit_and_respond(version_to_dict(version), HTTPStatus.CREATED)


@recipes_bp.get("/<string:recipe_id>/versions")
@require_authenticated
@require_permission("recipes.read")
def list_versions(recipe_id: str) -> ResponseReturnValue:
    versions = _recipe_version_service.list_versions(recipe_id)
    return success_response([version_to_dict(item) for item in versions], HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>")
@require_authenticated
@require_permission("recipes.read")
def get_version(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _ = recipe_id
    version = _recipe_version_service.get_version(version_id)
    return success_response(version_to_dict(version), HTTPStatus.OK)


@recipes_bp.patch("/<string:recipe_id>/versions/<string:version_id>/submit-review")
@require_authenticated
@require_permission("recipe.reviewer")
def submit_for_review(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _ = recipe_id
    validate_review_action_payload(_require_json_body())
    version = _recipe_approval_service.submit_for_review(version_id, requested_by=_actor(), client_ip=_client_ip())
    return _commit_and_respond(version_to_dict(version), HTTPStatus.OK)


@recipes_bp.patch("/<string:recipe_id>/versions/<string:version_id>/approve")
@require_authenticated
@require_permission("recipe.approver")
def approve_version(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _ = recipe_id
    validate_review_action_payload(_require_json_body())
    version = _recipe_approval_service.approve(version_id, approved_by=_actor(), client_ip=_client_ip())
    return _commit_and_respond(version_to_dict(version), HTTPStatus.OK)


@recipes_bp.patch("/<string:recipe_id>/versions/<string:version_id>/activate")
@require_authenticated
@require_permission("recipe.publisher")
def activate_version(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _ = recipe_id
    validate_review_action_payload(_require_json_body())
    version = _recipe_approval_service.activate(version_id, requested_by=_actor(), client_ip=_client_ip())
    return _commit_and_respond(version_to_dict(version), HTTPStatus.OK)


@recipes_bp.patch("/<string:recipe_id>/versions/<string:version_id>/archive")
@require_authenticated
@require_permission("recipes.update")
def archive_version(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _ = recipe_id
    validate_review_action_payload(_require_json_body())
    version = _recipe_approval_service.archive(version_id, requested_by=_actor(), client_ip=_client_ip())
    return _commit_and_respond(version_to_dict(version), HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/ingredients")
@require_authenticated
@require_permission("recipes.read")
def list_ingredients(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    ingredients = _recipe_ingredient_service.list_ingredients(version_id)
    return success_response([ingredient_to_dict(item) for item in ingredients], HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions/<string:version_id>/ingredients")
@require_authenticated
@require_permission("recipes.update")
def add_ingredient(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_create_ingredient_payload(payload)
    ingredient = _recipe_ingredient_service.add_ingredient(
        ingredient_id=data["id"],
        recipe_version_id=version_id,
        ingredient_type=data["ingredient_type"],
        inventory_item_id=data["inventory_item_id"],
        recipe_id=data["recipe_id"],
        secret_formulation_id=data["secret_formulation_id"],
        quantity=data["quantity"],
        unit_of_measure_id=data["unit_of_measure_id"],
        tolerance=data["tolerance"],
        display_order=data["display_order"],
        notes=data["notes"],
    )
    return _commit_and_respond(ingredient_to_dict(ingredient), HTTPStatus.CREATED)


@recipes_bp.put("/<string:recipe_id>/versions/<string:version_id>/ingredients/<string:ingredient_id>")
@require_authenticated
@require_permission("recipes.update")
def update_ingredient(recipe_id: str, version_id: str, ingredient_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_update_ingredient_payload(payload)
    ingredient = _recipe_ingredient_service.update_ingredient(
        ingredient_id,
        recipe_version_id=version_id,
        ingredient_type=data["ingredient_type"],
        inventory_item_id=data["inventory_item_id"],
        recipe_id=data["recipe_id"],
        secret_formulation_id=data["secret_formulation_id"],
        quantity=data["quantity"],
        unit_of_measure_id=data["unit_of_measure_id"],
        tolerance=data["tolerance"],
        display_order=data["display_order"],
        notes=data["notes"],
    )
    return _commit_and_respond(ingredient_to_dict(ingredient), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>/versions/<string:version_id>/ingredients/<string:ingredient_id>")
@require_authenticated
@require_permission("recipes.update")
def delete_ingredient(recipe_id: str, version_id: str, ingredient_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    _recipe_ingredient_service.remove_ingredient(ingredient_id, recipe_version_id=version_id)
    return _commit_and_respond({"message": "Ingredient deleted."}, HTTPStatus.OK)


@recipes_bp.get("/secret-formulations")
@require_authenticated
@require_permission("secret_formulations.view")
def list_secret_formulations() -> ResponseReturnValue:
    models = _secret_formulation_service.list_formulations()
    visible = [model for model in models if _has_classification_access(model.security_classification.value)]
    _recipe_audit_service.log_event(
        event_type="SECRET_FORMULATION_ACCESS",
        outcome="SUCCESS",
        requested_by=_actor(),
        client_ip=_client_ip(),
        event_metadata=f"count={len(visible)}",
    )
    return success_response([secret_formulation_metadata_to_dict(model) for model in visible], HTTPStatus.OK)


@recipes_bp.get("/secret-formulations/<string:formulation_id>")
@require_authenticated
@require_permission("secret_formulations.view")
def get_secret_formulation(formulation_id: str) -> ResponseReturnValue:
    model = _secret_formulation_service.get_formulation(formulation_id)
    _recipe_audit_service.log_event(
        event_type="SECRET_FORMULATION_ACCESS",
        outcome="SUCCESS",
        requested_by=_actor(),
        client_ip=_client_ip(),
        secret_formulation_id=model.id,
        reason="metadata_read",
    )
    return success_response(secret_formulation_metadata_to_dict(model), HTTPStatus.OK)


@recipes_bp.post("/secret-formulations")
@require_authenticated
@require_permission("secret_formulations.manage")
def create_secret_formulation() -> ResponseReturnValue:
    _configure_secret_formulation_security()
    payload = _require_json_body()
    data = validate_create_secret_formulation_payload(payload)
    _assert_classification_access(data["security_classification"])
    model = _secret_formulation_service.create_formulation(
        formulation_id=data["id"],
        code=data["code"],
        name=data["name"],
        description=data["description"],
        security_classification=data["security_classification"],
        plaintext_payload=data["payload"],
        created_by=_actor(),
        allow_manage=True,
    )
    _recipe_audit_service.log_event(
        event_type="SECRET_FORMULATION_MODIFY",
        outcome="SUCCESS",
        requested_by=_actor(),
        client_ip=_client_ip(),
        secret_formulation_id=model.id,
        reason="create",
    )
    return _commit_and_respond(secret_formulation_metadata_to_dict(model), HTTPStatus.CREATED)


@recipes_bp.put("/secret-formulations/<string:formulation_id>")
@require_authenticated
@require_permission("secret_formulations.manage")
def update_secret_formulation(formulation_id: str) -> ResponseReturnValue:
    _configure_secret_formulation_security()
    payload = _require_json_body()
    data = validate_update_secret_formulation_payload(payload)
    if "security_classification" in data:
        _assert_classification_access(data["security_classification"])
    model = _secret_formulation_service.create_new_version(
        formulation_id,
        name=data.get("name"),
        description=data.get("description"),
        security_classification=data.get("security_classification"),
        plaintext_payload=data["payload"],
        allow_manage=True,
    )
    _recipe_audit_service.log_event(
        event_type="SECRET_FORMULATION_MODIFY",
        outcome="SUCCESS",
        requested_by=_actor(),
        client_ip=_client_ip(),
        secret_formulation_id=model.id,
        reason="rotate_encrypted_payload",
    )
    return _commit_and_respond(secret_formulation_metadata_to_dict(model), HTTPStatus.OK)


@recipes_bp.patch("/secret-formulations/<string:formulation_id>/archive")
@require_authenticated
@require_permission("secret_formulations.manage")
def archive_secret_formulation(formulation_id: str) -> ResponseReturnValue:
    validate_review_action_payload(_require_json_body())
    model = _secret_formulation_service.archive(formulation_id, allow_manage=True)
    _recipe_audit_service.log_event(
        event_type="SECRET_FORMULATION_MODIFY",
        outcome="SUCCESS",
        requested_by=_actor(),
        client_ip=_client_ip(),
        secret_formulation_id=model.id,
        reason="archive",
    )
    return _commit_and_respond(secret_formulation_metadata_to_dict(model), HTTPStatus.OK)


@recipes_bp.post("/secret-formulations/<string:formulation_id>/decrypt")
@require_authenticated
def decrypt_secret_formulation(formulation_id: str) -> ResponseReturnValue:
    _configure_secret_formulation_security()
    payload = _require_json_body()
    data = validate_secret_formulation_decrypt_payload(payload)
    _assert_version_belongs_to_recipe(data["recipe_id"], data["recipe_version_id"])

    model = _secret_formulation_service.get_formulation(formulation_id)
    can_decrypt = _has_permission("secret_formulations.view") and _has_classification_access(
        model.security_classification.value
    )

    decrypted_payload = _secret_formulation_service.decrypt_formulation(
        formulation_id,
        requested_by=_actor(),
        reason=data["reason"],
        client_ip=_client_ip(),
        organization_id=data["organization_id"],
        branch_id=data["branch_id"],
        recipe_id=data["recipe_id"],
        recipe_version_id=data["recipe_version_id"],
        request_timestamp=data["request_timestamp"],
        allow_view=can_decrypt,
    )
    return success_response({"id": formulation_id, "formulation": decrypted_payload}, HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/steps")
@require_authenticated
@require_permission("recipes.read")
def list_steps(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    models = _recipe_step_service.list_steps(version_id)
    return success_response([step_to_dict(model) for model in models], HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions/<string:version_id>/steps")
@require_authenticated
@require_permission("recipes.update")
def create_step(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_create_step_payload(payload)
    model = _recipe_step_service.create_step(
        step_id=data["id"],
        recipe_version_id=version_id,
        step_number=data["step_number"],
        title=data["title"],
        description=data["description"],
        estimated_duration=data["estimated_duration"],
        temperature_min=data["temperature_min"],
        temperature_max=data["temperature_max"],
        notes=data["notes"],
    )
    return _commit_and_respond(step_to_dict(model), HTTPStatus.CREATED)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/steps/<string:step_id>")
@require_authenticated
@require_permission("recipes.read")
def get_step(recipe_id: str, version_id: str, step_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    model = _recipe_step_service.get_step(step_id, version_id)
    return success_response(step_to_dict(model), HTTPStatus.OK)


@recipes_bp.put("/<string:recipe_id>/versions/<string:version_id>/steps/<string:step_id>")
@require_authenticated
@require_permission("recipes.update")
def update_step(recipe_id: str, version_id: str, step_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_update_step_payload(payload)
    model = _recipe_step_service.update_step(
        step_id,
        version_id,
        step_number=data["step_number"],
        title=data["title"],
        description=data["description"],
        estimated_duration=data["estimated_duration"],
        temperature_min=data["temperature_min"],
        temperature_max=data["temperature_max"],
        notes=data["notes"],
    )
    return _commit_and_respond(step_to_dict(model), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>/versions/<string:version_id>/steps/<string:step_id>")
@require_authenticated
@require_permission("recipes.update")
def delete_step(recipe_id: str, version_id: str, step_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    _recipe_step_service.delete_step(step_id, version_id)
    return _commit_and_respond({"message": "Recipe step deleted."}, HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/yield")
@require_authenticated
@require_permission("recipes.read")
def get_yield(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    model = _recipe_yield_service.get_yield(version_id)
    return success_response(yield_to_dict(model), HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions/<string:version_id>/yield")
@require_authenticated
@require_permission("recipes.update")
def create_yield(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_create_yield_payload(payload)
    model = _recipe_yield_service.create_yield(
        yield_id=data["id"],
        recipe_version_id=version_id,
        expected_quantity=data["expected_quantity"],
        unit_of_measure_id=data["unit_of_measure_id"],
        expected_portions=data["expected_portions"],
        portion_weight=data["portion_weight"],
        yield_percentage=data["yield_percentage"],
        notes=data["notes"],
    )
    return _commit_and_respond(yield_to_dict(model), HTTPStatus.CREATED)


@recipes_bp.put("/<string:recipe_id>/versions/<string:version_id>/yield")
@require_authenticated
@require_permission("recipes.update")
def update_yield(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_update_yield_payload(payload)
    model = _recipe_yield_service.update_yield(
        version_id,
        expected_quantity=data["expected_quantity"],
        unit_of_measure_id=data["unit_of_measure_id"],
        expected_portions=data["expected_portions"],
        portion_weight=data["portion_weight"],
        yield_percentage=data["yield_percentage"],
        notes=data["notes"],
    )
    return _commit_and_respond(yield_to_dict(model), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>/versions/<string:version_id>/yield")
@require_authenticated
@require_permission("recipes.update")
def delete_yield(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    _recipe_yield_service.delete_yield(version_id)
    return _commit_and_respond({"message": "Recipe yield deleted."}, HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/waste")
@require_authenticated
@require_permission("recipes.read")
def list_waste(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    models = _recipe_waste_service.list_waste(version_id)
    return success_response([waste_to_dict(model) for model in models], HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions/<string:version_id>/waste")
@require_authenticated
@require_permission("recipes.update")
def create_waste(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_create_waste_payload(payload)
    model = _recipe_waste_service.create_waste(
        waste_id=data["id"],
        recipe_version_id=version_id,
        inventory_item_id=data["inventory_item_id"],
        expected_loss_quantity=data["expected_loss_quantity"],
        loss_percentage=data["loss_percentage"],
        reason=data["reason"],
        notes=data["notes"],
    )
    return _commit_and_respond(waste_to_dict(model), HTTPStatus.CREATED)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/waste/<string:waste_id>")
@require_authenticated
@require_permission("recipes.read")
def get_waste(recipe_id: str, version_id: str, waste_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    model = _recipe_waste_service.get_waste(waste_id, version_id)
    return success_response(waste_to_dict(model), HTTPStatus.OK)


@recipes_bp.put("/<string:recipe_id>/versions/<string:version_id>/waste/<string:waste_id>")
@require_authenticated
@require_permission("recipes.update")
def update_waste(recipe_id: str, version_id: str, waste_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_update_waste_payload(payload)
    model = _recipe_waste_service.update_waste(
        waste_id,
        version_id,
        inventory_item_id=data["inventory_item_id"],
        expected_loss_quantity=data["expected_loss_quantity"],
        loss_percentage=data["loss_percentage"],
        reason=data["reason"],
        notes=data["notes"],
    )
    return _commit_and_respond(waste_to_dict(model), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>/versions/<string:version_id>/waste/<string:waste_id>")
@require_authenticated
@require_permission("recipes.update")
def delete_waste(recipe_id: str, version_id: str, waste_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    _recipe_waste_service.delete_waste(waste_id, version_id)
    return _commit_and_respond({"message": "Recipe waste deleted."}, HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/equipment")
@require_authenticated
@require_permission("recipes.read")
def list_equipment(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    models = _recipe_equipment_service.list_equipment(version_id)
    return success_response([equipment_to_dict(model) for model in models], HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions/<string:version_id>/equipment")
@require_authenticated
@require_permission("recipes.update")
def create_equipment(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_create_equipment_payload(payload)
    model = _recipe_equipment_service.create_equipment(
        equipment_id=data["id"],
        recipe_version_id=version_id,
        equipment_name=data["equipment_name"],
        quantity_required=data["quantity_required"],
        mandatory=data["mandatory"],
        notes=data["notes"],
    )
    return _commit_and_respond(equipment_to_dict(model), HTTPStatus.CREATED)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/equipment/<string:equipment_id>")
@require_authenticated
@require_permission("recipes.read")
def get_equipment(recipe_id: str, version_id: str, equipment_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    model = _recipe_equipment_service.get_equipment(equipment_id, version_id)
    return success_response(equipment_to_dict(model), HTTPStatus.OK)


@recipes_bp.put("/<string:recipe_id>/versions/<string:version_id>/equipment/<string:equipment_id>")
@require_authenticated
@require_permission("recipes.update")
def update_equipment(recipe_id: str, version_id: str, equipment_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_update_equipment_payload(payload)
    model = _recipe_equipment_service.update_equipment(
        equipment_id,
        version_id,
        equipment_name=data["equipment_name"],
        quantity_required=data["quantity_required"],
        mandatory=data["mandatory"],
        notes=data["notes"],
    )
    return _commit_and_respond(equipment_to_dict(model), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>/versions/<string:version_id>/equipment/<string:equipment_id>")
@require_authenticated
@require_permission("recipes.update")
def delete_equipment(recipe_id: str, version_id: str, equipment_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    _recipe_equipment_service.delete_equipment(equipment_id, version_id)
    return _commit_and_respond({"message": "Recipe equipment deleted."}, HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/packaging")
@require_authenticated
@require_permission("recipes.read")
def list_packaging(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    models = _recipe_packaging_service.list_packaging(version_id)
    return success_response([packaging_to_dict(model) for model in models], HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions/<string:version_id>/packaging")
@require_authenticated
@require_permission("recipes.update")
def create_packaging(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_create_packaging_payload(payload)
    model = _recipe_packaging_service.create_packaging(
        packaging_id=data["id"],
        recipe_version_id=version_id,
        inventory_item_id=data["inventory_item_id"],
        quantity=data["quantity"],
        notes=data["notes"],
    )
    return _commit_and_respond(packaging_to_dict(model), HTTPStatus.CREATED)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/packaging/<string:packaging_id>")
@require_authenticated
@require_permission("recipes.read")
def get_packaging(recipe_id: str, version_id: str, packaging_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    model = _recipe_packaging_service.get_packaging(packaging_id, version_id)
    return success_response(packaging_to_dict(model), HTTPStatus.OK)


@recipes_bp.put("/<string:recipe_id>/versions/<string:version_id>/packaging/<string:packaging_id>")
@require_authenticated
@require_permission("recipes.update")
def update_packaging(recipe_id: str, version_id: str, packaging_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_update_packaging_payload(payload)
    model = _recipe_packaging_service.update_packaging(
        packaging_id,
        version_id,
        inventory_item_id=data["inventory_item_id"],
        quantity=data["quantity"],
        notes=data["notes"],
    )
    return _commit_and_respond(packaging_to_dict(model), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>/versions/<string:version_id>/packaging/<string:packaging_id>")
@require_authenticated
@require_permission("recipes.update")
def delete_packaging(recipe_id: str, version_id: str, packaging_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    _recipe_packaging_service.delete_packaging(packaging_id, version_id)
    return _commit_and_respond({"message": "Recipe packaging deleted."}, HTTPStatus.OK)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/quality-standards")
@require_authenticated
@require_permission("recipes.read")
def list_quality_standards(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    models = _recipe_quality_service.list_quality_standards(version_id)
    return success_response([quality_to_dict(model) for model in models], HTTPStatus.OK)


@recipes_bp.post("/<string:recipe_id>/versions/<string:version_id>/quality-standards")
@require_authenticated
@require_permission("recipes.update")
def create_quality_standard(recipe_id: str, version_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_create_quality_payload(payload)
    model = _recipe_quality_service.create_quality_standard(
        quality_id=data["id"],
        recipe_version_id=version_id,
        metric=data["metric"],
        minimum_value=data["minimum_value"],
        maximum_value=data["maximum_value"],
        target_value=data["target_value"],
        unit=data["unit"],
        notes=data["notes"],
    )
    return _commit_and_respond(quality_to_dict(model), HTTPStatus.CREATED)


@recipes_bp.get("/<string:recipe_id>/versions/<string:version_id>/quality-standards/<string:quality_id>")
@require_authenticated
@require_permission("recipes.read")
def get_quality_standard(recipe_id: str, version_id: str, quality_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    model = _recipe_quality_service.get_quality_standard(quality_id, version_id)
    return success_response(quality_to_dict(model), HTTPStatus.OK)


@recipes_bp.put("/<string:recipe_id>/versions/<string:version_id>/quality-standards/<string:quality_id>")
@require_authenticated
@require_permission("recipes.update")
def update_quality_standard(recipe_id: str, version_id: str, quality_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    payload = _require_json_body()
    data = validate_update_quality_payload(payload)
    model = _recipe_quality_service.update_quality_standard(
        quality_id,
        version_id,
        metric=data["metric"],
        minimum_value=data["minimum_value"],
        maximum_value=data["maximum_value"],
        target_value=data["target_value"],
        unit=data["unit"],
        notes=data["notes"],
    )
    return _commit_and_respond(quality_to_dict(model), HTTPStatus.OK)


@recipes_bp.delete("/<string:recipe_id>/versions/<string:version_id>/quality-standards/<string:quality_id>")
@require_authenticated
@require_permission("recipes.update")
def delete_quality_standard(recipe_id: str, version_id: str, quality_id: str) -> ResponseReturnValue:
    _assert_version_belongs_to_recipe(recipe_id, version_id)
    _recipe_quality_service.delete_quality_standard(quality_id, version_id)
    return _commit_and_respond({"message": "Recipe quality standard deleted."}, HTTPStatus.OK)
