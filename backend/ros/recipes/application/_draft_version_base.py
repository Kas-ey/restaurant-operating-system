"""Shared draft/version guards for recipe manufacturing services."""

from __future__ import annotations

from http import HTTPStatus

from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeVersionStatusEnum
from ..persistence.repositories import RecipeVersionRepository


class DraftRecipeVersionServiceBase:
    """Shared guards for workflows that only allow DRAFT modifications."""

    def __init__(
        self,
        *,
        version_repository: RecipeVersionRepository | None = None,
    ) -> None:
        self._version_repository = version_repository or RecipeVersionRepository()

    def _get_version(self, recipe_version_id: str):
        version = self._version_repository.get_by_id(recipe_version_id)
        if version is None:
            raise ROSException("Recipe version not found.", HTTPStatus.NOT_FOUND)
        return version

    def _get_draft_version(self, recipe_version_id: str):
        version = self._get_version(recipe_version_id)
        if version.status != RecipeVersionStatusEnum.DRAFT:
            raise ROSException("Recipe version must be DRAFT to modify manufacturing specifications.", HTTPStatus.CONFLICT)
        return version
