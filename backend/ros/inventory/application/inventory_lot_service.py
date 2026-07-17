"""Inventory lot workflow service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.inventory.persistence.models import InventoryItemModel, InventoryLotModel
from ros.inventory.persistence.repositories import InventoryItemRepository, InventoryLotRepository
from ros.shared.exceptions import ROSException


_UNSET = object()


class InventoryLotService:
	"""Coordinates inventory lot workflows."""

	def __init__(
		self,
		lot_repository: InventoryLotRepository | None = None,
		item_repository: InventoryItemRepository | None = None,
	) -> None:
		self._lot_repository = lot_repository or InventoryLotRepository()
		self._item_repository = item_repository or InventoryItemRepository()

	def create_lot(
		self,
		*,
		lot_id: str,
		inventory_item_id: str,
		lot_number: str,
		received_date: date,
		expiry_date: date | None,
		quantity: str | int | float,
		supplier_reference: str,
		notes: str,
	) -> InventoryLotModel:
		item = self._get_existing_item(inventory_item_id)
		normalized_id = self._require_text(lot_id, "Inventory lot ID is required.")
		normalized_lot_number = self._require_text(lot_number, "Lot number is required.")
		normalized_received_date = self._normalize_date(received_date, "Received date is required.")
		normalized_expiry_date = self._normalize_optional_date(expiry_date)
		normalized_quantity = self._normalize_quantity(quantity)
		normalized_supplier_reference = self._require_text(supplier_reference, "Supplier reference is required.")
		normalized_notes = self._require_text(notes, "Lot notes are required.")

		existing = self._lot_repository.get_by_lot_number(item.id, normalized_lot_number)
		if existing is not None:
			raise ROSException("Inventory lot already exists.", HTTPStatus.CONFLICT)

		model = InventoryLotModel(
			id=normalized_id,
			inventory_item_id=item.id,
			lot_number=normalized_lot_number,
			received_date=normalized_received_date,
			expiry_date=normalized_expiry_date,
			quantity=normalized_quantity,
			supplier_reference=normalized_supplier_reference,
			notes=normalized_notes,
		)
		return self._lot_repository.create(model)

	def update_lot(
		self,
		lot_id: str,
		*,
		lot_number: str | None = None,
		received_date: date | None = None,
		expiry_date: date | None | object = _UNSET,
		quantity: str | int | float | None = None,
		supplier_reference: str | None = None,
		notes: str | None = None,
	) -> InventoryLotModel:
		model = self._get_existing_lot(lot_id)
		if self._lot_repository.has_transactions(model.id):
			raise ROSException("Cannot modify lot with existing transactions.", HTTPStatus.CONFLICT)

		if lot_number is not None:
			normalized_lot_number = self._require_text(lot_number, "Lot number is required.")
			existing = self._lot_repository.get_by_lot_number(model.inventory_item_id, normalized_lot_number)
			if existing is not None and existing.id != model.id:
				raise ROSException("Inventory lot already exists.", HTTPStatus.CONFLICT)
			model.lot_number = normalized_lot_number

		if received_date is not None:
			model.received_date = self._normalize_date(received_date, "Received date is required.")

		if expiry_date is not _UNSET:
			model.expiry_date = self._normalize_optional_date(expiry_date)

		if quantity is not None:
			model.quantity = self._normalize_quantity(quantity)

		if supplier_reference is not None:
			model.supplier_reference = self._require_text(supplier_reference, "Supplier reference is required.")

		if notes is not None:
			model.notes = self._require_text(notes, "Lot notes are required.")

		return self._lot_repository.update(model)

	def delete_lot(self, lot_id: str) -> None:
		model = self._get_existing_lot(lot_id)
		if self._lot_repository.has_transactions(model.id):
			raise ROSException("Cannot delete lot with existing transactions.", HTTPStatus.CONFLICT)
		self._lot_repository.delete(model.id)

	def get_lot(self, lot_id: str) -> InventoryLotModel:
		return self._get_existing_lot(lot_id)

	def list_lots(self, inventory_item_id: str) -> list[InventoryLotModel]:
		item = self._get_existing_item(inventory_item_id)
		return self._lot_repository.get_by_item(item.id)

	def _get_existing_item(self, item_id: str) -> InventoryItemModel:
		normalized_id = self._require_text(item_id, "Inventory item ID is required.")
		item = self._item_repository.get_by_id(normalized_id)
		if item is None:
			raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)
		return item

	def _get_existing_lot(self, lot_id: str) -> InventoryLotModel:
		normalized_id = self._require_text(lot_id, "Inventory lot ID is required.")
		lot = self._lot_repository.get_by_id(normalized_id)
		if lot is None:
			raise ROSException("Inventory lot not found.", HTTPStatus.NOT_FOUND)
		return lot

	@staticmethod
	def _require_text(value: str, message: str) -> str:
		normalized = value.strip() if isinstance(value, str) else ""
		normalized = " ".join(normalized.split())
		if not normalized:
			raise ROSException(message, HTTPStatus.BAD_REQUEST)
		return normalized

	@staticmethod
	def _normalize_date(value: date, message: str) -> date:
		if not isinstance(value, date):
			raise ROSException(message, HTTPStatus.BAD_REQUEST)
		return value

	@staticmethod
	def _normalize_optional_date(value: date | None) -> date | None:
		if value is not None and not isinstance(value, date):
			raise ROSException("Expiry date must be a valid date.", HTTPStatus.BAD_REQUEST)
		return value

	@staticmethod
	def _normalize_quantity(value: str | int | float) -> Decimal:
		try:
			quantity = Decimal(str(value))
		except (InvalidOperation, ValueError, TypeError) as exc:
			raise ROSException("Lot quantity must be a valid decimal value.", HTTPStatus.BAD_REQUEST) from exc
		if not quantity.is_finite() or quantity < 0:
			raise ROSException("Lot quantity cannot be negative.", HTTPStatus.BAD_REQUEST)
		return quantity.quantize(Decimal("0.0001"))


__all__ = ["InventoryLotService"]
