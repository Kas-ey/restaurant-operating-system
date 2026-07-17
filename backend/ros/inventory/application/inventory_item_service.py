"""Inventory item workflow service."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.inventory.persistence.models import InventoryCategoryModel, InventoryItemModel, UnitOfMeasureModel
from ros.inventory.persistence.repositories import InventoryCategoryRepository, InventoryItemRepository, UnitRepository
from ros.shared.exceptions import ROSException


class InventoryItemService:
	"""Coordinates inventory item workflows."""

	def __init__(
		self,
		item_repository: InventoryItemRepository | None = None,
		category_repository: InventoryCategoryRepository | None = None,
		unit_repository: UnitRepository | None = None,
	) -> None:
		self._item_repository = item_repository or InventoryItemRepository()
		self._category_repository = category_repository or InventoryCategoryRepository()
		self._unit_repository = unit_repository or UnitRepository()

	def create_item(
		self,
		*,
		item_id: str,
		name: str,
		sku: str,
		description: str,
		category_id: str,
		unit_of_measure_id: str,
		minimum_stock: str | int | float,
		maximum_stock: str | int | float,
		reorder_level: str | int | float,
	) -> InventoryItemModel:
		normalized_id = self._require_text(item_id, "Inventory item ID is required.")
		normalized_name = self._require_text(name, "Inventory item name is required.")
		normalized_sku = self._require_text(sku, "Inventory item SKU is required.")
		normalized_description = self._require_text(description, "Inventory item description is required.")
		category = self._get_active_category(category_id)
		unit = self._get_active_unit(unit_of_measure_id)
		normalized_minimum_stock = self._normalize_quantity(minimum_stock, "Minimum stock must be zero or greater.")
		normalized_maximum_stock = self._normalize_quantity(maximum_stock, "Maximum stock must be zero or greater.")
		normalized_reorder_level = self._normalize_quantity(reorder_level, "Reorder level must be zero or greater.")
		self._validate_thresholds(
			minimum_stock=normalized_minimum_stock,
			maximum_stock=normalized_maximum_stock,
			reorder_level=normalized_reorder_level,
		)

		if self._item_repository.exists_by_sku(normalized_sku):
			raise ROSException("Inventory item already exists.", HTTPStatus.CONFLICT)

		model = InventoryItemModel(
			id=normalized_id,
			name=normalized_name,
			sku=normalized_sku,
			description=normalized_description,
			category_id=category.id,
			unit_of_measure_id=unit.id,
			minimum_stock=normalized_minimum_stock,
			maximum_stock=normalized_maximum_stock,
			reorder_level=normalized_reorder_level,
			is_active=True,
		)
		return self._item_repository.create(model)

	def update_item(
		self,
		item_id: str,
		*,
		name: str | None = None,
		sku: str | None = None,
		description: str | None = None,
		category_id: str | None = None,
		unit_of_measure_id: str | None = None,
		minimum_stock: str | int | float | None = None,
		maximum_stock: str | int | float | None = None,
		reorder_level: str | int | float | None = None,
	) -> InventoryItemModel:
		model = self._get_existing_item(item_id)

		if name is not None:
			model.name = self._require_text(name, "Inventory item name is required.")

		if sku is not None:
			normalized_sku = self._require_text(sku, "Inventory item SKU is required.")
			existing = self._item_repository.get_by_sku(normalized_sku)
			if existing is not None and existing.id != model.id:
				raise ROSException("Inventory item already exists.", HTTPStatus.CONFLICT)
			model.sku = normalized_sku

		if description is not None:
			model.description = self._require_text(description, "Inventory item description is required.")

		if category_id is not None:
			category = self._get_active_category(category_id)
			model.category_id = category.id

		if unit_of_measure_id is not None:
			unit = self._get_active_unit(unit_of_measure_id)
			model.unit_of_measure_id = unit.id

		if minimum_stock is not None:
			model.minimum_stock = self._normalize_quantity(minimum_stock, "Minimum stock must be zero or greater.")

		if maximum_stock is not None:
			model.maximum_stock = self._normalize_quantity(maximum_stock, "Maximum stock must be zero or greater.")

		if reorder_level is not None:
			model.reorder_level = self._normalize_quantity(reorder_level, "Reorder level must be zero or greater.")

		self._validate_thresholds(
			minimum_stock=Decimal(str(model.minimum_stock)),
			maximum_stock=Decimal(str(model.maximum_stock)),
			reorder_level=Decimal(str(model.reorder_level)),
		)
		return self._item_repository.update(model)

	def delete_item(self, item_id: str) -> None:
		model = self._get_existing_item(item_id)
		if self._item_repository.has_transactions(model.id):
			raise ROSException("Cannot delete inventory item with existing transactions.", HTTPStatus.CONFLICT)
		self._item_repository.delete(model.id)

	def activate_item(self, item_id: str) -> InventoryItemModel:
		model = self._get_existing_item(item_id)
		model.is_active = True
		return self._item_repository.update(model)

	def deactivate_item(self, item_id: str) -> InventoryItemModel:
		model = self._get_existing_item(item_id)
		model.is_active = False
		return self._item_repository.update(model)

	def get_item(self, item_id: str) -> InventoryItemModel:
		return self._get_existing_item(item_id)

	def list_items(self) -> list[InventoryItemModel]:
		return self._item_repository.get_all()

	def _get_existing_item(self, item_id: str) -> InventoryItemModel:
		normalized_id = self._require_text(item_id, "Inventory item ID is required.")
		model = self._item_repository.get_by_id(normalized_id)
		if model is None:
			raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)
		return model

	def _get_active_category(self, category_id: str) -> InventoryCategoryModel:
		normalized_id = self._require_text(category_id, "Inventory category ID is required.")
		category = self._category_repository.get_by_id(normalized_id)
		if category is None:
			raise ROSException("Inventory category not found.", HTTPStatus.NOT_FOUND)
		if not category.is_active:
			raise ROSException("Inventory category is inactive.", HTTPStatus.CONFLICT)
		return category

	def _get_active_unit(self, unit_id: str) -> UnitOfMeasureModel:
		normalized_id = self._require_text(unit_id, "Unit of measure ID is required.")
		unit = self._unit_repository.get_by_id(normalized_id)
		if unit is None:
			raise ROSException("Unit not found.", HTTPStatus.NOT_FOUND)
		if not unit.is_active:
			raise ROSException("Unit is inactive.", HTTPStatus.CONFLICT)
		return unit

	@staticmethod
	def _validate_thresholds(*, minimum_stock: Decimal, maximum_stock: Decimal, reorder_level: Decimal) -> None:
		if minimum_stock > maximum_stock:
			raise ROSException("Minimum stock cannot exceed maximum stock.", HTTPStatus.BAD_REQUEST)
		if reorder_level > maximum_stock:
			raise ROSException("Reorder level cannot exceed maximum stock.", HTTPStatus.BAD_REQUEST)

	@staticmethod
	def _require_text(value: str, message: str) -> str:
		normalized = value.strip() if isinstance(value, str) else ""
		normalized = " ".join(normalized.split())
		if not normalized:
			raise ROSException(message, HTTPStatus.BAD_REQUEST)
		return normalized

	@staticmethod
	def _normalize_quantity(value: str | int | float, message: str) -> Decimal:
		try:
			quantity = Decimal(str(value))
		except (InvalidOperation, ValueError, TypeError) as exc:
			raise ROSException(message, HTTPStatus.BAD_REQUEST) from exc
		if not quantity.is_finite() or quantity < 0:
			raise ROSException(message, HTTPStatus.BAD_REQUEST)
		return quantity.quantize(Decimal("0.0001"))


__all__ = ["InventoryItemService"]
