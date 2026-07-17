"""Application service for recipe quality standards."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeQualityModel
from ..persistence.repositories import RecipeQualityRepository, RecipeVersionRepository
from ._draft_version_base import DraftRecipeVersionServiceBase


class RecipeQualityService(DraftRecipeVersionServiceBase):
    """Encapsulates recipe quality standard workflows."""

    def __init__(
        self,
        *,
        quality_repository: RecipeQualityRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
    ) -> None:
        super().__init__(version_repository=version_repository)
        self._quality_repository = quality_repository or RecipeQualityRepository()

    def list_quality_standards(self, recipe_version_id: str) -> list[RecipeQualityModel]:
        self._get_version(recipe_version_id)
        return self._quality_repository.get_by_recipe_version(recipe_version_id)

    def get_quality_standard(self, quality_id: str, recipe_version_id: str) -> RecipeQualityModel:
        model = self._quality_repository.get_by_id(quality_id)
        if model is None or model.recipe_version_id != recipe_version_id:
            raise ROSException("Recipe quality standard not found.", HTTPStatus.NOT_FOUND)
        return model

    def create_quality_standard(
        self,
        *,
        quality_id: str,
        recipe_version_id: str,
        metric: str,
        minimum_value,
        maximum_value,
        target_value,
        unit: str | None,
        notes: str | None,
    ) -> RecipeQualityModel:
        self._get_draft_version(recipe_version_id)
        minimum = self._parse_optional_decimal(minimum_value, "minimum_value")
        maximum = self._parse_optional_decimal(maximum_value, "maximum_value")
        target = self._parse_optional_decimal(target_value, "target_value")
        self._validate_range(minimum, maximum)

        model = RecipeQualityModel(
            id=quality_id.strip(),
            recipe_version_id=recipe_version_id,
            metric=self._require_text(metric, "metric"),
            minimum_value=minimum,
            maximum_value=maximum,
            target_value=target,
            unit=self._optional_text(unit),
            notes=self._optional_text(notes),
        )
        return self._quality_repository.create(model)

    def update_quality_standard(
        self,
        quality_id: str,
        recipe_version_id: str,
        *,
        metric: str,
        minimum_value,
        maximum_value,
        target_value,
        unit: str | None,
        notes: str | None,
    ) -> RecipeQualityModel:
        model = self.get_quality_standard(quality_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        minimum = self._parse_optional_decimal(minimum_value, "minimum_value")
        maximum = self._parse_optional_decimal(maximum_value, "maximum_value")
        target = self._parse_optional_decimal(target_value, "target_value")
        self._validate_range(minimum, maximum)

        model.metric = self._require_text(metric, "metric")
        model.minimum_value = minimum
        model.maximum_value = maximum
        model.target_value = target
        model.unit = self._optional_text(unit)
        model.notes = self._optional_text(notes)
        return self._quality_repository.update(model)

    def delete_quality_standard(self, quality_id: str, recipe_version_id: str) -> None:
        model = self.get_quality_standard(quality_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        self._quality_repository.delete(model.id)

    @staticmethod
    def _validate_range(minimum_value: Decimal | None, maximum_value: Decimal | None) -> None:
        if minimum_value is not None and maximum_value is not None and maximum_value < minimum_value:
            raise ROSException("Maximum value must be greater than or equal to minimum value.", HTTPStatus.BAD_REQUEST)

    @staticmethod
    def _parse_optional_decimal(value, field_name: str) -> Decimal | None:
        if value is None:
            return None
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, AttributeError) as exc:
            raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc
        if not parsed.is_finite():
            raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST)
        return parsed

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        if not normalized:
            raise ROSException(f"Field '{field_name}' is required.", HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _optional_text(value: str | None) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None
