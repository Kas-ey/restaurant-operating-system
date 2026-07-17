"""Inventory category workflow service."""

from __future__ import annotations

from http import HTTPStatus

from ros.inventory.persistence.models import InventoryCategoryModel
from ros.inventory.persistence.repositories import InventoryCategoryRepository
from ros.shared.exceptions import ROSException


class InventoryCategoryService:
	"""Coordinates inventory category workflows."""

	def __init__(self, category_repository: InventoryCategoryRepository | None = None) -> None:
		self._category_repository = category_repository or InventoryCategoryRepository()

	def create_category(self, category_id: str, name: str, description: str) -> InventoryCategoryModel:
		normalized_id = self._require_text(category_id, "Category ID is required.")
		normalized_name = self._normalize_name(name)
		normalized_description = self._require_text(description, "Category description is required.")

		if self._category_repository.exists_by_name(normalized_name):
			raise ROSException("Inventory category already exists.", HTTPStatus.CONFLICT)

		model = InventoryCategoryModel(
			id=normalized_id,
			name=normalized_name,
			description=normalized_description,
			is_active=True,
		)
		return self._category_repository.create(model)

	def update_category(
		self,
		category_id: str,
		*,
		name: str | None = None,
		description: str | None = None,
	) -> InventoryCategoryModel:
		model = self._get_existing_category(category_id)

		if name is not None:
			normalized_name = self._normalize_name(name)
			existing = self._category_repository.get_by_name(normalized_name)
			if existing is not None and existing.id != model.id:
				raise ROSException("Inventory category already exists.", HTTPStatus.CONFLICT)
			model.name = normalized_name

		if description is not None:
			model.description = self._require_text(description, "Category description is required.")

		return self._category_repository.update(model)

	def delete_category(self, category_id: str) -> None:
		model = self._get_existing_category(category_id)
		if self._category_repository.has_items(model.id):
			raise ROSException("Cannot delete category with existing inventory items.", HTTPStatus.CONFLICT)
		self._category_repository.delete(model.id)

	def activate_category(self, category_id: str) -> InventoryCategoryModel:
		model = self._get_existing_category(category_id)
		model.is_active = True
		return self._category_repository.update(model)

	def deactivate_category(self, category_id: str) -> InventoryCategoryModel:
		model = self._get_existing_category(category_id)
		model.is_active = False
		return self._category_repository.update(model)

	def get_category(self, category_id: str) -> InventoryCategoryModel:
		return self._get_existing_category(category_id)

	def list_categories(self) -> list[InventoryCategoryModel]:
		return self._category_repository.get_all()

	def _get_existing_category(self, category_id: str) -> InventoryCategoryModel:
		normalized_id = self._require_text(category_id, "Category ID is required.")
		model = self._category_repository.get_by_id(normalized_id)
		if model is None:
			raise ROSException("Inventory category not found.", HTTPStatus.NOT_FOUND)
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
		return cls._require_text(value, "Category name is required.")


__all__ = ["InventoryCategoryService"]
