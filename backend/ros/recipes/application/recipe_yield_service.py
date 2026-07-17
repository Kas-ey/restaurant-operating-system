"""Application service for recipe yield specifications."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.inventory.persistence.repositories import UnitRepository
from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeYieldModel
from ..persistence.repositories import RecipeVersionRepository, RecipeYieldRepository
from ._draft_version_base import DraftRecipeVersionServiceBase


class RecipeYieldService(DraftRecipeVersionServiceBase):
    """Encapsulates expected recipe yield workflows."""

    def __init__(
        self,
        *,
        yield_repository: RecipeYieldRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
        unit_repository: UnitRepository | None = None,
    ) -> None:
        super().__init__(version_repository=version_repository)
        self._yield_repository = yield_repository or RecipeYieldRepository()
        self._unit_repository = unit_repository or UnitRepository()

    def get_yield(self, recipe_version_id: str) -> RecipeYieldModel:
        self._get_version(recipe_version_id)
        model = self._yield_repository.get_by_recipe_version(recipe_version_id)
        if model is None:
            raise ROSException("Recipe yield not found.", HTTPStatus.NOT_FOUND)
        return model

    def create_yield(
        self,
        *,
        yield_id: str,
        recipe_version_id: str,
        expected_quantity,
        unit_of_measure_id: str,
        expected_portions,
        portion_weight,
        yield_percentage,
        notes: str | None,
    ) -> RecipeYieldModel:
        self._get_draft_version(recipe_version_id)
        if self._yield_repository.get_by_recipe_version(recipe_version_id) is not None:
            raise ROSException("Recipe yield already exists for this version.", HTTPStatus.CONFLICT)

        unit = self._unit_repository.get_by_id(unit_of_measure_id.strip())
        if unit is None:
            raise ROSException("Unit of measure not found.", HTTPStatus.NOT_FOUND)

        model = RecipeYieldModel(
            id=yield_id.strip(),
            recipe_version_id=recipe_version_id,
            expected_quantity=self._parse_positive_decimal(expected_quantity, "expected_quantity"),
            unit_of_measure_id=unit.id,
            expected_portions=self._parse_positive_int(expected_portions, "expected_portions"),
            portion_weight=self._parse_positive_decimal(portion_weight, "portion_weight"),
            yield_percentage=self._parse_percentage(yield_percentage, "yield_percentage"),
            notes=self._optional_text(notes),
        )
        return self._yield_repository.create(model)

    def update_yield(
        self,
        recipe_version_id: str,
        *,
        expected_quantity,
        unit_of_measure_id: str,
        expected_portions,
        portion_weight,
        yield_percentage,
        notes: str | None,
    ) -> RecipeYieldModel:
        model = self.get_yield(recipe_version_id)
        self._get_draft_version(recipe_version_id)
        unit = self._unit_repository.get_by_id(unit_of_measure_id.strip())
        if unit is None:
            raise ROSException("Unit of measure not found.", HTTPStatus.NOT_FOUND)

        model.expected_quantity = self._parse_positive_decimal(expected_quantity, "expected_quantity")
        model.unit_of_measure_id = unit.id
        model.expected_portions = self._parse_positive_int(expected_portions, "expected_portions")
        model.portion_weight = self._parse_positive_decimal(portion_weight, "portion_weight")
        model.yield_percentage = self._parse_percentage(yield_percentage, "yield_percentage")
        model.notes = self._optional_text(notes)
        return self._yield_repository.update(model)

    def delete_yield(self, recipe_version_id: str) -> None:
        model = self.get_yield(recipe_version_id)
        self._get_draft_version(recipe_version_id)
        self._yield_repository.delete(model.id)

    @staticmethod
    def _parse_positive_decimal(value, field_name: str) -> Decimal:
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, AttributeError) as exc:
            raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc
        if not parsed.is_finite() or parsed <= 0:
            raise ROSException(f"Field '{field_name}' must be greater than zero.", HTTPStatus.BAD_REQUEST)
        return parsed

    @staticmethod
    def _parse_positive_int(value, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ROSException(f"Field '{field_name}' must be a positive integer.", HTTPStatus.BAD_REQUEST)
        return value

    @staticmethod
    def _parse_percentage(value, field_name: str) -> Decimal:
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, AttributeError) as exc:
            raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc
        if not parsed.is_finite() or parsed < 0 or parsed > 100:
            raise ROSException(f"Field '{field_name}' must be between 0 and 100.", HTTPStatus.BAD_REQUEST)
        return parsed

    @staticmethod
    def _optional_text(value: str | None) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None
