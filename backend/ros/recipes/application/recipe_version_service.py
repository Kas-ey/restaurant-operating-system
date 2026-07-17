"""Application service for recipe version lifecycle workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus

from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeVersionModel, RecipeVersionStatusEnum
from ..persistence.repositories import RecipeRepository, RecipeVersionRepository


class RecipeVersionService:
    """Encapsulates recipe version creation and lifecycle transitions."""

    def __init__(
        self,
        *,
        recipe_repository: RecipeRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
    ) -> None:
        self._recipe_repository = recipe_repository or RecipeRepository()
        self._version_repository = version_repository or RecipeVersionRepository()

    def create_version(
        self,
        *,
        version_id: str,
        recipe_id: str,
        change_summary: str,
        created_by: str,
        effective_date,
    ) -> RecipeVersionModel:
        recipe = self._get_recipe(recipe_id)
        latest = self._version_repository.get_latest_version(recipe.id)
        if latest is not None and latest.status != RecipeVersionStatusEnum.ARCHIVED:
            raise ROSException("Latest recipe version must be archived before creating a new version.", HTTPStatus.CONFLICT)

        next_number = 1 if latest is None else latest.version_number + 1
        model = RecipeVersionModel(
            id=version_id.strip(),
            recipe_id=recipe.id,
            version_number=next_number,
            status=RecipeVersionStatusEnum.DRAFT,
            change_summary=change_summary.strip(),
            effective_date=effective_date,
            created_by=created_by.strip(),
        )
        return self._version_repository.create(model)

    def get_version(self, version_id: str) -> RecipeVersionModel:
        version = self._version_repository.get_by_id(version_id)
        if version is None:
            raise ROSException("Recipe version not found.", HTTPStatus.NOT_FOUND)
        return version

    def list_versions(self, recipe_id: str) -> list[RecipeVersionModel]:
        self._get_recipe(recipe_id)
        return self._version_repository.get_by_recipe(recipe_id)

    def submit_for_review(self, version_id: str, *, allow_review: bool) -> RecipeVersionModel:
        if not allow_review:
            raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)
        version = self.get_version(version_id)
        self._assert_transition(version, RecipeVersionStatusEnum.UNDER_REVIEW)
        return self._version_repository.mark_under_review(version)

    def approve(self, version_id: str, approved_by: str, *, allow_approve: bool) -> RecipeVersionModel:
        if not allow_approve:
            raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)
        version = self.get_version(version_id)
        self._assert_transition(version, RecipeVersionStatusEnum.APPROVED)
        return self._version_repository.mark_approved(
            version,
            approved_by=approved_by.strip(),
            approved_at=datetime.now(tz=UTC),
        )

    def activate(self, version_id: str, *, allow_publish: bool) -> RecipeVersionModel:
        if not allow_publish:
            raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)
        version = self.get_version(version_id)
        self._assert_transition(version, RecipeVersionStatusEnum.ACTIVE)
        recipe = self._get_recipe(version.recipe_id)
        return self._version_repository.activate(recipe, version)

    def archive(self, version_id: str) -> RecipeVersionModel:
        version = self.get_version(version_id)
        self._assert_transition(version, RecipeVersionStatusEnum.ARCHIVED)
        return self._version_repository.mark_archived(version)

    @staticmethod
    def _assert_transition(version: RecipeVersionModel, target: RecipeVersionStatusEnum) -> None:
        valid = {
            RecipeVersionStatusEnum.DRAFT: {RecipeVersionStatusEnum.UNDER_REVIEW},
            RecipeVersionStatusEnum.UNDER_REVIEW: {RecipeVersionStatusEnum.APPROVED},
            RecipeVersionStatusEnum.APPROVED: {RecipeVersionStatusEnum.ACTIVE},
            RecipeVersionStatusEnum.ACTIVE: {RecipeVersionStatusEnum.ARCHIVED},
            RecipeVersionStatusEnum.ARCHIVED: set(),
        }
        allowed_targets = valid.get(version.status, set())
        if target not in allowed_targets:
            raise ROSException(
                f"Invalid status transition from {version.status.value} to {target.value}.",
                HTTPStatus.CONFLICT,
            )

    def _get_recipe(self, recipe_id: str):
        recipe = self._recipe_repository.get_by_id(recipe_id)
        if recipe is None:
            raise ROSException("Recipe not found.", HTTPStatus.NOT_FOUND)
        return recipe
