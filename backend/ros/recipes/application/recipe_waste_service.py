"""Application service for recipe waste specifications."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.inventory.persistence.repositories import InventoryItemRepository
from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeWasteModel
from ..persistence.repositories import RecipeVersionRepository, RecipeWasteRepository
from ._draft_version_base import DraftRecipeVersionServiceBase


class RecipeWasteService(DraftRecipeVersionServiceBase):
    """Encapsulates expected waste workflows."""

    def __init__(
        self,
        *,
        waste_repository: RecipeWasteRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
        inventory_item_repository: InventoryItemRepository | None = None,
    ) -> None:
        super().__init__(version_repository=version_repository)
        self._waste_repository = waste_repository or RecipeWasteRepository()
        self._inventory_item_repository = inventory_item_repository or InventoryItemRepository()

    def list_waste(self, recipe_version_id: str) -> list[RecipeWasteModel]:
        self._get_version(recipe_version_id)
        return self._waste_repository.get_by_recipe_version(recipe_version_id)

    def get_waste(self, waste_id: str, recipe_version_id: str) -> RecipeWasteModel:
        model = self._waste_repository.get_by_id(waste_id)
        if model is None or model.recipe_version_id != recipe_version_id:
            raise ROSException("Recipe waste not found.", HTTPStatus.NOT_FOUND)
        return model

    def create_waste(
        self,
        *,
        waste_id: str,
        recipe_version_id: str,
        inventory_item_id: str,
        expected_loss_quantity,
        loss_percentage,
        reason: str,
        notes: str | None,
    ) -> RecipeWasteModel:
        self._get_draft_version(recipe_version_id)
        item = self._inventory_item_repository.get_by_id(inventory_item_id.strip())
        if item is None:
            raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)

        model = RecipeWasteModel(
            id=waste_id.strip(),
            recipe_version_id=recipe_version_id,
            inventory_item_id=item.id,
            expected_loss_quantity=self._parse_positive_decimal(expected_loss_quantity, "expected_loss_quantity"),
            loss_percentage=self._parse_percentage(loss_percentage, "loss_percentage"),
            reason=self._require_text(reason, "reason"),
            notes=self._optional_text(notes),
        )
        return self._waste_repository.create(model)

    def update_waste(
        self,
        waste_id: str,
        recipe_version_id: str,
        *,
        inventory_item_id: str,
        expected_loss_quantity,
        loss_percentage,
        reason: str,
        notes: str | None,
    ) -> RecipeWasteModel:
        model = self.get_waste(waste_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        item = self._inventory_item_repository.get_by_id(inventory_item_id.strip())
        if item is None:
            raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)

        model.inventory_item_id = item.id
        model.expected_loss_quantity = self._parse_positive_decimal(expected_loss_quantity, "expected_loss_quantity")
        model.loss_percentage = self._parse_percentage(loss_percentage, "loss_percentage")
        model.reason = self._require_text(reason, "reason")
        model.notes = self._optional_text(notes)
        return self._waste_repository.update(model)

    def delete_waste(self, waste_id: str, recipe_version_id: str) -> None:
        model = self.get_waste(waste_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        self._waste_repository.delete(model.id)

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
    def _parse_percentage(value, field_name: str) -> Decimal:
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, AttributeError) as exc:
            raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc
        if not parsed.is_finite() or parsed < 0 or parsed > 100:
            raise ROSException(f"Field '{field_name}' must be between 0 and 100.", HTTPStatus.BAD_REQUEST)
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
