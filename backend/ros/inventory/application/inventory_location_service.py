"""Inventory location workflow service."""

from __future__ import annotations

from http import HTTPStatus

from ros.inventory.persistence.models import InventoryLocationModel, InventoryLocationTypeEnum
from ros.inventory.persistence.repositories import InventoryLocationRepository
from ros.organization.persistence.repositories import BranchRepository
from ros.shared.exceptions import ROSException


class InventoryLocationService:
	"""Coordinates inventory location workflows."""

	def __init__(
		self,
		location_repository: InventoryLocationRepository | None = None,
		branch_repository: BranchRepository | None = None,
	) -> None:
		self._location_repository = location_repository or InventoryLocationRepository()
		self._branch_repository = branch_repository or BranchRepository()

	def create_location(
		self,
		*,
		location_id: str,
		branch_id: str,
		name: str,
		description: str,
		location_type: str,
	) -> InventoryLocationModel:
		normalized_id = self._require_text(location_id, "Inventory location ID is required.")
		normalized_branch_id = self._require_text(branch_id, "Branch ID is required.")
		normalized_name = self._require_text(name, "Inventory location name is required.")
		normalized_description = self._require_text(description, "Inventory location description is required.")
		normalized_location_type = self._normalize_location_type(location_type)

		self._ensure_branch_exists(normalized_branch_id)
		existing = self._location_repository.get_by_branch_and_name(normalized_branch_id, normalized_name)
		if existing is not None:
			raise ROSException("Inventory location already exists.", HTTPStatus.CONFLICT)

		model = InventoryLocationModel(
			id=normalized_id,
			branch_id=normalized_branch_id,
			name=normalized_name,
			description=normalized_description,
			location_type=normalized_location_type,
			is_active=True,
		)
		return self._location_repository.create(model)

	def update_location(
		self,
		location_id: str,
		*,
		branch_id: str | None = None,
		name: str | None = None,
		description: str | None = None,
		location_type: str | None = None,
	) -> InventoryLocationModel:
		model = self._get_existing_location(location_id)

		target_branch_id = model.branch_id
		if branch_id is not None:
			target_branch_id = self._require_text(branch_id, "Branch ID is required.")
			self._ensure_branch_exists(target_branch_id)
			model.branch_id = target_branch_id

		if name is not None:
			normalized_name = self._require_text(name, "Inventory location name is required.")
			existing = self._location_repository.get_by_branch_and_name(target_branch_id, normalized_name)
			if existing is not None and existing.id != model.id:
				raise ROSException("Inventory location already exists.", HTTPStatus.CONFLICT)
			model.name = normalized_name

		if description is not None:
			model.description = self._require_text(description, "Inventory location description is required.")

		if location_type is not None:
			model.location_type = self._normalize_location_type(location_type)

		return self._location_repository.update(model)

	def delete_location(self, location_id: str) -> None:
		model = self._get_existing_location(location_id)
		if self._location_repository.has_stock_levels(model.id):
			raise ROSException("Cannot delete location with stock levels.", HTTPStatus.CONFLICT)
		self._location_repository.delete(model.id)

	def activate_location(self, location_id: str) -> InventoryLocationModel:
		model = self._get_existing_location(location_id)
		model.is_active = True
		return self._location_repository.update(model)

	def deactivate_location(self, location_id: str) -> InventoryLocationModel:
		model = self._get_existing_location(location_id)
		model.is_active = False
		return self._location_repository.update(model)

	def get_location(self, location_id: str) -> InventoryLocationModel:
		return self._get_existing_location(location_id)

	def list_locations(self) -> list[InventoryLocationModel]:
		return self._location_repository.get_all()

	def _get_existing_location(self, location_id: str) -> InventoryLocationModel:
		normalized_id = self._require_text(location_id, "Inventory location ID is required.")
		model = self._location_repository.get_by_id(normalized_id)
		if model is None:
			raise ROSException("Inventory location not found.", HTTPStatus.NOT_FOUND)
		return model

	def _ensure_branch_exists(self, branch_id: str) -> None:
		if not self._branch_repository.exists(branch_id):
			raise ROSException("Branch not found.", HTTPStatus.NOT_FOUND)

	@staticmethod
	def _require_text(value: str, message: str) -> str:
		normalized = value.strip() if isinstance(value, str) else ""
		normalized = " ".join(normalized.split())
		if not normalized:
			raise ROSException(message, HTTPStatus.BAD_REQUEST)
		return normalized

	@staticmethod
	def _normalize_location_type(value: str | InventoryLocationTypeEnum) -> InventoryLocationTypeEnum:
		if isinstance(value, InventoryLocationTypeEnum):
			return value
		try:
			return InventoryLocationTypeEnum(str(value))
		except ValueError as exc:
			raise ROSException("Invalid location type.", HTTPStatus.BAD_REQUEST) from exc


__all__ = ["InventoryLocationService"]
