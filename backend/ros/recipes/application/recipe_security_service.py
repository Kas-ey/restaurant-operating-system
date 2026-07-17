"""Centralized Recipes permission and classification authorization workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.shared.exceptions import ROSException

PERMISSION_RECIPE_VIEWER = "recipe.viewer"
PERMISSION_RECIPE_EDITOR = "recipe.editor"
PERMISSION_RECIPE_REVIEWER = "recipe.reviewer"
PERMISSION_RECIPE_APPROVER = "recipe.approver"
PERMISSION_RECIPE_PUBLISHER = "recipe.publisher"
PERMISSION_SECRET_FORMULATION_VIEWER = "secret.formulation.viewer"
PERMISSION_SECRET_FORMULATION_MANAGER = "secret.formulation.manager"
PERMISSION_RECIPE_ADMINISTRATOR = "recipe.administrator"

PERMISSION_CLASSIFICATION_RESTRICTED = "recipe.classification.restricted"
PERMISSION_CLASSIFICATION_SECRET = "recipe.classification.secret"


class RecipeSecurityService:
    """Resolves Recipes-domain permissions and classification access."""

    _restricted_role_aliases = {
        "senior.operations",
        "senior_operational",
        "senior-operational",
        "operations.senior",
    }

    _secret_permission_deny_role_aliases = {
        "developer",
        "developers",
        "database.administrator",
        "database.admin",
        "dba",
        "system.administrator",
        "system.admin",
        "sysadmin",
    }

    _recipe_domain_permissions = {
        PERMISSION_RECIPE_VIEWER,
        PERMISSION_RECIPE_EDITOR,
        PERMISSION_RECIPE_REVIEWER,
        PERMISSION_RECIPE_APPROVER,
        PERMISSION_RECIPE_PUBLISHER,
        PERMISSION_RECIPE_ADMINISTRATOR,
    }

    @staticmethod
    def _normalize(value: str) -> str:
        return ".".join(value.strip().lower().split())

    def permission_aliases(self, required_permission: str) -> set[str]:
        requested = self._normalize(required_permission)
        aliases: dict[str, set[str]] = {
            PERMISSION_RECIPE_VIEWER: {PERMISSION_RECIPE_VIEWER, "recipes.read"},
            PERMISSION_RECIPE_EDITOR: {PERMISSION_RECIPE_EDITOR, "recipes.update", "recipes.create"},
            PERMISSION_RECIPE_REVIEWER: {PERMISSION_RECIPE_REVIEWER, "recipes.update"},
            PERMISSION_RECIPE_APPROVER: {PERMISSION_RECIPE_APPROVER, "recipes.approve"},
            PERMISSION_RECIPE_PUBLISHER: {PERMISSION_RECIPE_PUBLISHER, "recipes.activate"},
            PERMISSION_SECRET_FORMULATION_VIEWER: {
                PERMISSION_SECRET_FORMULATION_VIEWER,
                "secret_formulations.view",
            },
            PERMISSION_SECRET_FORMULATION_MANAGER: {
                PERMISSION_SECRET_FORMULATION_MANAGER,
                "secret_formulations.manage",
            },
            PERMISSION_RECIPE_ADMINISTRATOR: {PERMISSION_RECIPE_ADMINISTRATOR},
            "recipes.read": {
                "recipes.read",
                PERMISSION_RECIPE_VIEWER,
                PERMISSION_RECIPE_EDITOR,
                PERMISSION_RECIPE_REVIEWER,
                PERMISSION_RECIPE_APPROVER,
                PERMISSION_RECIPE_PUBLISHER,
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
            "recipes.create": {
                "recipes.create",
                PERMISSION_RECIPE_EDITOR,
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
            "recipes.update": {
                "recipes.update",
                PERMISSION_RECIPE_EDITOR,
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
            "recipes.delete": {
                "recipes.delete",
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
            "recipes.approve": {
                "recipes.approve",
                PERMISSION_RECIPE_APPROVER,
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
            "recipes.activate": {
                "recipes.activate",
                PERMISSION_RECIPE_PUBLISHER,
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
            "secret_formulations.view": {
                "secret_formulations.view",
                PERMISSION_SECRET_FORMULATION_VIEWER,
                PERMISSION_SECRET_FORMULATION_MANAGER,
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
            "secret_formulations.manage": {
                "secret_formulations.manage",
                PERMISSION_SECRET_FORMULATION_MANAGER,
                PERMISSION_RECIPE_ADMINISTRATOR,
            },
        }
        return aliases.get(requested, {requested}) | {requested}

    def has_permission(
        self,
        *,
        required_permission: str,
        permissions: set[str],
        role_names: set[str],
    ) -> bool:
        normalized_required = self._normalize(required_permission)
        normalized_permissions = {self._normalize(value) for value in permissions}
        normalized_roles = {self._normalize(value) for value in role_names}

        if normalized_required in {
            "secret_formulations.view",
            "secret_formulations.manage",
            PERMISSION_SECRET_FORMULATION_VIEWER,
            PERMISSION_SECRET_FORMULATION_MANAGER,
        } and normalized_roles & self._secret_permission_deny_role_aliases:
            return False

        return any(alias in normalized_permissions for alias in self.permission_aliases(normalized_required))

    def assert_permission(
        self,
        *,
        required_permission: str,
        permissions: set[str],
        role_names: set[str],
    ) -> None:
        if not self.has_permission(
            required_permission=required_permission,
            permissions=permissions,
            role_names=role_names,
        ):
            raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)

    def has_classification_access(self, *, classification: str, permissions: set[str], role_names: set[str]) -> bool:
        normalized = self._normalize(classification)
        normalized_permissions = {self._normalize(value) for value in permissions}
        normalized_roles = {self._normalize(value) for value in role_names}

        if normalized in {"public", "confidential"}:
            return bool(normalized_permissions & self._recipe_domain_permissions)
        if normalized == "restricted":
            return (
                PERMISSION_CLASSIFICATION_RESTRICTED in normalized_permissions
                or bool(normalized_roles & self._restricted_role_aliases)
                or PERMISSION_RECIPE_ADMINISTRATOR in normalized_permissions
            )
        if normalized == "secret":
            return (
                PERMISSION_CLASSIFICATION_SECRET in normalized_permissions
                or PERMISSION_SECRET_FORMULATION_VIEWER in normalized_permissions
                or PERMISSION_SECRET_FORMULATION_MANAGER in normalized_permissions
                or PERMISSION_RECIPE_ADMINISTRATOR in normalized_permissions
            )
        return False

    def assert_classification_access(self, *, classification: str, permissions: set[str], role_names: set[str]) -> None:
        if not self.has_classification_access(
            classification=classification,
            permissions=permissions,
            role_names=role_names,
        ):
            raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)
