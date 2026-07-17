"""Application service for recipe packaging specifications."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.inventory.persistence.repositories import InventoryItemRepository
from ros.shared.exceptions import ROSException

from ..persistence.models import RecipePackagingModel
from ..persistence.repositories import RecipePackagingRepository, RecipeVersionRepository
from ._draft_version_base import DraftRecipeVersionServiceBase


class RecipePackagingService(DraftRecipeVersionServiceBase):
    """Encapsulates recipe packaging workflows."""

    def __init__(
        self,
        *,
        packaging_repository: RecipePackagingRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
        inventory_item_repository: InventoryItemRepository | None = None,
    ) -> None:
        super().__init__(version_repository=version_repository)
        self._packaging_repository = packaging_repository or RecipePackagingRepository()
        self._inventory_item_repository = inventory_item_repository or InventoryItemRepository()

    def list_packaging(self, recipe_version_id: str) -> list[RecipePackagingModel]:
        self._get_version(recipe_version_id)
        return self._packaging_repository.get_by_recipe_version(recipe_version_id)

    def get_packaging(self, packaging_id: str, recipe_version_id: str) -> RecipePackagingModel:
        model = self._packaging_repository.get_by_id(packaging_id)
        if model is None or model.recipe_version_id != recipe_version_id:
            raise ROSException("Recipe packaging not found.", HTTPStatus.NOT_FOUND)
        return model

    def create_packaging(
        self,
        *,
        packaging_id: str,
        recipe_version_id: str,
        inventory_item_id: str,
        quantity,
        notes: str | None,
    ) -> RecipePackagingModel:
        self._get_draft_version(recipe_version_id)
        item = self._inventory_item_repository.get_by_id(inventory_item_id.strip())
        if item is None:
            raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)
        if not item.is_active:
            raise ROSException("Inactive inventory items cannot be referenced.", HTTPStatus.CONFLICT)

        model = RecipePackagingModel(
            id=packaging_id.strip(),
            recipe_version_id=recipe_version_id,
            inventory_item_id=item.id,
            quantity=self._parse_positive_decimal(quantity, "quantity"),
            notes=self._optional_text(notes),
        )
        return self._packaging_repository.create(model)

    def update_packaging(
        self,
        packaging_id: str,
        recipe_version_id: str,
        *,
        inventory_item_id: str,
        quantity,
        notes: str | None,
    ) -> RecipePackagingModel:
        model = self.get_packaging(packaging_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        item = self._inventory_item_repository.get_by_id(inventory_item_id.strip())
        if item is None:
            raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)
        if not item.is_active:
            raise ROSException("Inactive inventory items cannot be referenced.", HTTPStatus.CONFLICT)

        model.inventory_item_id = item.id
        model.quantity = self._parse_positive_decimal(quantity, "quantity")
        model.notes = self._optional_text(notes)
        return self._packaging_repository.update(model)

    def delete_packaging(self, packaging_id: str, recipe_version_id: str) -> None:
        model = self.get_packaging(packaging_id, recipe_version_id)
        self._get_draft_version(recipe_version_id)
        self._packaging_repository.delete(model.id)

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
    def _optional_text(value: str | None) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None
