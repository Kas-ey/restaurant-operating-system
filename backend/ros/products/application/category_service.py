"""Product category application service workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.products.persistence.models import ProductCategoryModel
from ros.products.persistence.repositories import ProductCategoryRepository
from ros.shared.exceptions import ROSException


class ProductCategoryService:
    """Coordinates product category business workflows."""

    def __init__(self, category_repository: ProductCategoryRepository | None = None) -> None:
        self._category_repository = category_repository or ProductCategoryRepository()

    def create_category(self, category_id: str, name: str, description: str) -> ProductCategoryModel:
        normalized_id = self._require_text(category_id, "Category ID is required.")
        normalized_name = self._normalize_name(name)
        normalized_description = self._normalize_description(description)

        if self._category_repository.exists_by_name(normalized_name):
            raise ROSException("Category already exists.", HTTPStatus.CONFLICT)

        model = ProductCategoryModel(
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
    ) -> ProductCategoryModel:
        model = self._get_existing_category(category_id)

        if name is not None:
            normalized_name = self._normalize_name(name)
            existing = self._category_repository.get_by_name(normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Category already exists.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if description is not None:
            model.description = self._normalize_description(description)

        return self._category_repository.update(model)

    def delete_category(self, category_id: str) -> None:
        model = self._get_existing_category(category_id)
        if self._category_repository.has_products(model.id):
            raise ROSException("Cannot delete category with existing products.", HTTPStatus.CONFLICT)
        self._category_repository.delete(model.id)

    def activate_category(self, category_id: str) -> ProductCategoryModel:
        model = self._get_existing_category(category_id)
        model.is_active = True
        return self._category_repository.update(model)

    def deactivate_category(self, category_id: str) -> ProductCategoryModel:
        model = self._get_existing_category(category_id)
        model.is_active = False
        return self._category_repository.update(model)

    def get_category(self, category_id: str) -> ProductCategoryModel:
        return self._get_existing_category(category_id)

    def list_categories(self) -> list[ProductCategoryModel]:
        return self._category_repository.get_all()

    def _get_existing_category(self, category_id: str) -> ProductCategoryModel:
        normalized_id = self._require_text(category_id, "Category ID is required.")
        model = self._category_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Category not found.", HTTPStatus.NOT_FOUND)
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

    @classmethod
    def _normalize_description(cls, value: str) -> str:
        return cls._require_text(value, "Category description is required.")
