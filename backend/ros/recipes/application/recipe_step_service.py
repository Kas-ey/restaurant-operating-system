"""Application service for recipe manufacturing steps."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.core.extensions import db
from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeStepModel
from ..persistence.repositories import RecipeStepRepository, RecipeVersionRepository
from ._draft_version_base import DraftRecipeVersionServiceBase


class RecipeStepService(DraftRecipeVersionServiceBase):
    """Encapsulates recipe step workflows."""

    def __init__(
        self,
        *,
        step_repository: RecipeStepRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
    ) -> None:
        super().__init__(version_repository=version_repository)
        self._step_repository = step_repository or RecipeStepRepository()

    def list_steps(self, recipe_version_id: str) -> list[RecipeStepModel]:
        self._get_version(recipe_version_id)
        return self._step_repository.get_by_recipe_version(recipe_version_id)

    def get_step(self, step_id: str, recipe_version_id: str) -> RecipeStepModel:
        step = self._step_repository.get_by_id(step_id)
        if step is None or step.recipe_version_id != recipe_version_id:
            raise ROSException("Recipe step not found.", HTTPStatus.NOT_FOUND)
        return step

    def create_step(
        self,
        *,
        step_id: str,
        recipe_version_id: str,
        step_number: int,
        title: str,
        description: str,
        estimated_duration,
        temperature_min,
        temperature_max,
        notes: str | None,
    ) -> RecipeStepModel:
        self._get_draft_version(recipe_version_id)
        steps = self._step_repository.get_by_recipe_version(recipe_version_id)
        expected_step_number = len(steps) + 1
        if step_number != expected_step_number:
            raise ROSException("Step numbers must be sequential.", HTTPStatus.CONFLICT)

        duration_value = self._parse_non_negative_int(estimated_duration, "estimated_duration")
        temperature_min_value = self._parse_optional_decimal(temperature_min, "temperature_min")
        temperature_max_value = self._parse_optional_decimal(temperature_max, "temperature_max")
        self._validate_temperature_range(temperature_min_value, temperature_max_value)

        model = RecipeStepModel(
            id=step_id.strip(),
            recipe_version_id=recipe_version_id,
            step_number=step_number,
            title=self._require_text(title, "title"),
            description=self._require_text(description, "description"),
            estimated_duration=duration_value,
            temperature_min=temperature_min_value,
            temperature_max=temperature_max_value,
            notes=self._optional_text(notes),
        )
        return self._step_repository.create(model)

    def update_step(
        self,
        step_id: str,
        recipe_version_id: str,
        *,
        step_number: int,
        title: str,
        description: str,
        estimated_duration,
        temperature_min,
        temperature_max,
        notes: str | None,
    ) -> RecipeStepModel:
        step = self.get_step(step_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        if step.step_number != step_number:
            raise ROSException("Step numbers must remain sequential.", HTTPStatus.CONFLICT)

        duration_value = self._parse_non_negative_int(estimated_duration, "estimated_duration")
        temperature_min_value = self._parse_optional_decimal(temperature_min, "temperature_min")
        temperature_max_value = self._parse_optional_decimal(temperature_max, "temperature_max")
        self._validate_temperature_range(temperature_min_value, temperature_max_value)

        step.title = self._require_text(title, "title")
        step.description = self._require_text(description, "description")
        step.estimated_duration = duration_value
        step.temperature_min = temperature_min_value
        step.temperature_max = temperature_max_value
        step.notes = self._optional_text(notes)
        return self._step_repository.update(step)

    def delete_step(self, step_id: str, recipe_version_id: str) -> None:
        self.get_step(step_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        self._step_repository.delete(step_id)
        self._renumber_steps(recipe_version_id)

    def _renumber_steps(self, recipe_version_id: str) -> None:
        steps = self._step_repository.get_by_recipe_version(recipe_version_id)
        for index, step in enumerate(steps, start=1):
            step.step_number = index
        db.session.flush()

    @staticmethod
    def _validate_temperature_range(temperature_min: Decimal | None, temperature_max: Decimal | None) -> None:
        if temperature_min is not None and temperature_max is not None and temperature_max <= temperature_min:
            raise ROSException("Temperature max must be greater than temperature min.", HTTPStatus.BAD_REQUEST)

    @staticmethod
    def _parse_non_negative_int(value, field_name: str) -> int:
        if not isinstance(value, int) or value < 0:
            raise ROSException(f"Field '{field_name}' must be a non-negative integer.", HTTPStatus.BAD_REQUEST)
        return value

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
