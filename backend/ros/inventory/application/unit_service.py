"""Inventory unit-of-measure workflow service."""

from __future__ import annotations

from http import HTTPStatus

from ros.inventory.persistence.models import UnitOfMeasureModel
from ros.inventory.persistence.repositories import UnitRepository
from ros.shared.exceptions import ROSException


class UnitService:
	"""Coordinates inventory unit-of-measure workflows."""

	def __init__(self, unit_repository: UnitRepository | None = None) -> None:
		self._unit_repository = unit_repository or UnitRepository()

	def create_unit(
		self,
		unit_id: str,
		name: str,
		symbol: str,
		description: str,
		precision: int,
	) -> UnitOfMeasureModel:
		normalized_id = self._require_text(unit_id, "Unit ID is required.")
		normalized_name = self._normalize_name(name)
		normalized_symbol = self._normalize_symbol(symbol)
		normalized_description = self._require_text(description, "Unit description is required.")
		normalized_precision = self._normalize_precision(precision)

		if self._unit_repository.exists_by_name(normalized_name):
			raise ROSException("Unit already exists.", HTTPStatus.CONFLICT)
		if self._unit_repository.exists_by_symbol(normalized_symbol):
			raise ROSException("Unit symbol already exists.", HTTPStatus.CONFLICT)

		model = UnitOfMeasureModel(
			id=normalized_id,
			name=normalized_name,
			symbol=normalized_symbol,
			description=normalized_description,
			precision=normalized_precision,
			is_active=True,
		)
		return self._unit_repository.create(model)

	def update_unit(
		self,
		unit_id: str,
		*,
		name: str | None = None,
		symbol: str | None = None,
		description: str | None = None,
		precision: int | None = None,
	) -> UnitOfMeasureModel:
		model = self._get_existing_unit(unit_id)

		if name is not None:
			normalized_name = self._normalize_name(name)
			existing = self._unit_repository.get_by_name(normalized_name)
			if existing is not None and existing.id != model.id:
				raise ROSException("Unit already exists.", HTTPStatus.CONFLICT)
			model.name = normalized_name

		if symbol is not None:
			normalized_symbol = self._normalize_symbol(symbol)
			existing = self._unit_repository.get_by_symbol(normalized_symbol)
			if existing is not None and existing.id != model.id:
				raise ROSException("Unit symbol already exists.", HTTPStatus.CONFLICT)
			model.symbol = normalized_symbol

		if description is not None:
			model.description = self._require_text(description, "Unit description is required.")

		if precision is not None:
			model.precision = self._normalize_precision(precision)

		return self._unit_repository.update(model)

	def delete_unit(self, unit_id: str) -> None:
		model = self._get_existing_unit(unit_id)
		if self._unit_repository.has_items(model.id):
			raise ROSException("Cannot delete unit with existing inventory items.", HTTPStatus.CONFLICT)
		self._unit_repository.delete(model.id)

	def activate_unit(self, unit_id: str) -> UnitOfMeasureModel:
		model = self._get_existing_unit(unit_id)
		model.is_active = True
		return self._unit_repository.update(model)

	def deactivate_unit(self, unit_id: str) -> UnitOfMeasureModel:
		model = self._get_existing_unit(unit_id)
		model.is_active = False
		return self._unit_repository.update(model)

	def get_unit(self, unit_id: str) -> UnitOfMeasureModel:
		return self._get_existing_unit(unit_id)

	def list_units(self) -> list[UnitOfMeasureModel]:
		return self._unit_repository.get_all()

	def _get_existing_unit(self, unit_id: str) -> UnitOfMeasureModel:
		normalized_id = self._require_text(unit_id, "Unit ID is required.")
		model = self._unit_repository.get_by_id(normalized_id)
		if model is None:
			raise ROSException("Unit not found.", HTTPStatus.NOT_FOUND)
		return model

	@staticmethod
	def _require_text(value: str, message: str) -> str:
		normalized = value.strip() if isinstance(value, str) else ""
		normalized = " ".join(normalized.split())
		if not normalized:
			raise ROSException(message, HTTPStatus.BAD_REQUEST)
		return normalized

	@classmethod
	def _normalize_name(cls, value: str) -> str:
		return cls._require_text(value, "Unit name is required.")

	@classmethod
	def _normalize_symbol(cls, value: str) -> str:
		return cls._require_text(value, "Unit symbol is required.")

	@staticmethod
	def _normalize_precision(value: int) -> int:
		if not isinstance(value, int) or value < 0:
			raise ROSException("Unit precision must be zero or greater.", HTTPStatus.BAD_REQUEST)
		return value


__all__ = ["UnitService"]
