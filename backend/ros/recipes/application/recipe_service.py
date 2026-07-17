"""Application service for recipe aggregate workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeModel, RecipeSecurityClassificationEnum
from ..persistence.repositories import RecipeRepository


class RecipeService:
    """Encapsulates recipe aggregate business workflows."""

    def __init__(self, repository: RecipeRepository | None = None) -> None:
        self._repository = repository or RecipeRepository()

    def create_recipe(
        self,
        *,
        recipe_id: str,
        product_id: str,
        code: str,
        name: str,
        description: str,
        security_classification: str,
        created_by: str,
    ) -> RecipeModel:
        normalized_code = code.strip().upper()
        if self._repository.exists_by_code(normalized_code):
            raise ROSException("Recipe code already exists.", HTTPStatus.CONFLICT)

        model = RecipeModel(
            id=recipe_id.strip(),
            product_id=product_id.strip(),
            code=normalized_code,
            name=name.strip(),
            description=description.strip(),
            security_classification=self._parse_security_classification(security_classification),
            created_by=created_by.strip(),
        )
        return self._repository.create(model)

    def get_recipe(self, recipe_id: str) -> RecipeModel:
        recipe = self._repository.get_by_id(recipe_id)
        if recipe is None:
            raise ROSException("Recipe not found.", HTTPStatus.NOT_FOUND)
        return recipe

    def list_recipes(self) -> list[RecipeModel]:
        return self._repository.get_all()

    def update_recipe(
        self,
        recipe_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        security_classification: str | None = None,
    ) -> RecipeModel:
        recipe = self.get_recipe(recipe_id)

        if name is not None:
            recipe.name = name.strip()
        if description is not None:
            recipe.description = description.strip()
        if security_classification is not None:
            recipe.security_classification = self._parse_security_classification(security_classification)

        return self._repository.update(recipe)

    def delete_recipe(self, recipe_id: str) -> None:
        recipe = self.get_recipe(recipe_id)
        if self._repository.has_production_references(recipe.id):
            raise ROSException("Cannot delete recipe with production references.", HTTPStatus.CONFLICT)
        self._repository.delete(recipe.id)

    @staticmethod
    def _parse_security_classification(value: str) -> RecipeSecurityClassificationEnum:
        try:
            return RecipeSecurityClassificationEnum(value.strip().upper())
        except ValueError as exc:
            raise ROSException("Invalid security classification.", HTTPStatus.BAD_REQUEST) from exc
