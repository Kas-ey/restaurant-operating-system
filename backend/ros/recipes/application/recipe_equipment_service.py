"""Application service for recipe equipment specifications."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeEquipmentModel
from ..persistence.repositories import RecipeEquipmentRepository, RecipeVersionRepository
from ._draft_version_base import DraftRecipeVersionServiceBase


class RecipeEquipmentService(DraftRecipeVersionServiceBase):
    """Encapsulates recipe equipment requirements workflows."""

    def __init__(
        self,
        *,
        equipment_repository: RecipeEquipmentRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
    ) -> None:
        super().__init__(version_repository=version_repository)
        self._equipment_repository = equipment_repository or RecipeEquipmentRepository()

    def list_equipment(self, recipe_version_id: str) -> list[RecipeEquipmentModel]:
        self._get_version(recipe_version_id)
        return self._equipment_repository.get_by_recipe_version(recipe_version_id)

    def get_equipment(self, equipment_id: str, recipe_version_id: str) -> RecipeEquipmentModel:
        model = self._equipment_repository.get_by_id(equipment_id)
        if model is None or model.recipe_version_id != recipe_version_id:
            raise ROSException("Recipe equipment not found.", HTTPStatus.NOT_FOUND)
        return model

    def create_equipment(
        self,
        *,
        equipment_id: str,
        recipe_version_id: str,
        equipment_name: str,
        quantity_required,
        mandatory: bool,
        notes: str | None,
    ) -> RecipeEquipmentModel:
        self._get_draft_version(recipe_version_id)
        model = RecipeEquipmentModel(
            id=equipment_id.strip(),
            recipe_version_id=recipe_version_id,
            equipment_name=self._require_text(equipment_name, "equipment_name"),
            quantity_required=self._parse_positive_decimal(quantity_required, "quantity_required"),
            mandatory=bool(mandatory),
            notes=self._optional_text(notes),
        )
        return self._equipment_repository.create(model)

    def update_equipment(
        self,
        equipment_id: str,
        recipe_version_id: str,
        *,
        equipment_name: str,
        quantity_required,
        mandatory: bool,
        notes: str | None,
    ) -> RecipeEquipmentModel:
        model = self.get_equipment(equipment_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        model.equipment_name = self._require_text(equipment_name, "equipment_name")
        model.quantity_required = self._parse_positive_decimal(quantity_required, "quantity_required")
        model.mandatory = bool(mandatory)
        model.notes = self._optional_text(notes)
        return self._equipment_repository.update(model)

    def delete_equipment(self, equipment_id: str, recipe_version_id: str) -> None:
        model = self.get_equipment(equipment_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        self._equipment_repository.delete(model.id)

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
