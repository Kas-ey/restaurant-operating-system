"""Product aggregate application service workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.products.persistence.models import ProductCategoryModel, ProductModel
from ros.products.persistence.repositories import ProductCategoryRepository, ProductRepository
from ros.shared.exceptions import ROSException


class ProductService:
    """Coordinates product business workflows."""

    def __init__(
        self,
        product_repository: ProductRepository | None = None,
        category_repository: ProductCategoryRepository | None = None,
    ) -> None:
        self._product_repository = product_repository or ProductRepository()
        self._category_repository = category_repository or ProductCategoryRepository()

    def create_product(
        self,
        product_id: str,
        name: str,
        sku: str,
        description: str,
        category_id: str,
    ) -> ProductModel:
        normalized_id = self._require_text(product_id, "Product ID is required.")
        normalized_name = self._normalize_name(name)
        normalized_sku = self._normalize_sku(sku)
        normalized_description = self._normalize_description(description)
        category = self._get_active_category(category_id)

        if self._product_repository.exists_by_sku(normalized_sku):
            raise ROSException("Product already exists.", HTTPStatus.CONFLICT)

        model = ProductModel(
            id=normalized_id,
            name=normalized_name,
            sku=normalized_sku,
            description=normalized_description,
            category_id=category.id,
            is_active=True,
        )
        return self._product_repository.create(model)

    def update_product(
        self,
        product_id: str,
        *,
        name: str | None = None,
        sku: str | None = None,
        description: str | None = None,
        category_id: str | None = None,
    ) -> ProductModel:
        model = self._get_existing_product(product_id)

        if name is not None:
            model.name = self._normalize_name(name)

        if sku is not None:
            normalized_sku = self._normalize_sku(sku)
            existing = self._product_repository.get_by_sku(normalized_sku)
            if existing is not None and existing.id != model.id:
                raise ROSException("Product already exists.", HTTPStatus.CONFLICT)
            model.sku = normalized_sku

        if description is not None:
            model.description = self._normalize_description(description)

        if category_id is not None:
            category = self._get_active_category(category_id)
            model.category_id = category.id

        return self._product_repository.update(model)

    def delete_product(self, product_id: str) -> None:
        model = self._get_existing_product(product_id)
        self._product_repository.delete(model.id)

    def activate_product(self, product_id: str) -> ProductModel:
        model = self._get_existing_product(product_id)
        model.is_active = True
        return self._product_repository.update(model)

    def deactivate_product(self, product_id: str) -> ProductModel:
        model = self._get_existing_product(product_id)
        model.is_active = False
        return self._product_repository.update(model)

    def get_product(self, product_id: str) -> ProductModel:
        return self._get_existing_product(product_id)

    def list_products(self) -> list[ProductModel]:
        return self._product_repository.get_all()

    def _get_existing_product(self, product_id: str) -> ProductModel:
        normalized_id = self._require_text(product_id, "Product ID is required.")
        model = self._product_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Product not found.", HTTPStatus.NOT_FOUND)
        return model

    def _get_active_category(self, category_id: str) -> ProductCategoryModel:
        normalized_id = self._require_text(category_id, "Category ID is required.")
        category = self._category_repository.get_by_id(normalized_id)
        if category is None:
            raise ROSException("Category not found.", HTTPStatus.NOT_FOUND)
        if not category.is_active:
            raise ROSException("Category is inactive.", HTTPStatus.CONFLICT)
        return category

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @classmethod
    def _normalize_name(cls, value: str) -> str:
        return cls._require_text(value, "Product name is required.")

    @classmethod
    def _normalize_sku(cls, value: str) -> str:
        return cls._require_text(value, "Product SKU is required.")

    @classmethod
    def _normalize_description(cls, value: str) -> str:
        return cls._require_text(value, "Product description is required.")
