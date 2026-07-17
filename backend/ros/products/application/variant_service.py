"""Product variant aggregate application service workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.products.persistence.models import ProductModel, ProductVariantModel
from ros.products.persistence.repositories import ProductRepository, ProductVariantRepository
from ros.shared.exceptions import ROSException


class ProductVariantService:
    """Coordinates product variant workflows."""

    def __init__(
        self,
        variant_repository: ProductVariantRepository | None = None,
        product_repository: ProductRepository | None = None,
    ) -> None:
        self._variant_repository = variant_repository or ProductVariantRepository()
        self._product_repository = product_repository or ProductRepository()

    def create_variant(
        self,
        *,
        variant_id: str,
        product_id: str,
        name: str,
        sku: str,
        description: str,
        display_order: int,
        is_default: bool,
    ) -> ProductVariantModel:
        product = self._get_active_product(product_id)
        normalized_variant_id = self._require_text(variant_id, "Variant ID is required.")
        normalized_name = self._require_text(name, "Variant name is required.")
        normalized_sku = self._require_text(sku, "Variant SKU is required.")
        normalized_description = self._require_text(description, "Variant description is required.")
        normalized_display_order = self._require_non_negative_int(display_order, "Variant display order must be zero or greater.")

        if self._variant_repository.exists_by_sku(normalized_sku):
            raise ROSException("Variant already exists.", HTTPStatus.CONFLICT)

        model = ProductVariantModel(
            id=normalized_variant_id,
            product_id=product.id,
            name=normalized_name,
            sku=normalized_sku,
            description=normalized_description,
            display_order=normalized_display_order,
            is_default=bool(is_default),
            is_active=True,
        )
        created = self._variant_repository.create(model)

        if created.is_default:
            self._variant_repository.set_default_variant(product.id, created.id)

        return created

    def update_variant(
        self,
        variant_id: str,
        *,
        name: str | None = None,
        sku: str | None = None,
        description: str | None = None,
        display_order: int | None = None,
        is_default: bool | None = None,
    ) -> ProductVariantModel:
        model = self._get_existing_variant(variant_id)

        if name is not None:
            model.name = self._require_text(name, "Variant name is required.")

        if sku is not None:
            normalized_sku = self._require_text(sku, "Variant SKU is required.")
            existing = self._variant_repository.get_by_id(model.id)
            if existing is None:
                raise ROSException("Variant not found.", HTTPStatus.NOT_FOUND)
            if normalized_sku != model.sku and self._variant_repository.exists_by_sku(normalized_sku):
                raise ROSException("Variant already exists.", HTTPStatus.CONFLICT)
            model.sku = normalized_sku

        if description is not None:
            model.description = self._require_text(description, "Variant description is required.")

        if display_order is not None:
            model.display_order = self._require_non_negative_int(display_order, "Variant display order must be zero or greater.")

        updated = self._variant_repository.update(model)

        if is_default is True:
            self._variant_repository.set_default_variant(updated.product_id, updated.id)
            updated.is_default = True
        elif is_default is False and updated.is_default:
            default_variant = self._variant_repository.get_default_variant(updated.product_id)
            if default_variant is not None and default_variant.id == updated.id:
                updated.is_default = False
                self._variant_repository.update(updated)

        return updated

    def set_default_variant(self, variant_id: str) -> ProductVariantModel:
        model = self._get_existing_variant(variant_id)
        self._variant_repository.set_default_variant(model.product_id, model.id)
        model.is_default = True
        return model

    def delete_variant(self, variant_id: str) -> None:
        model = self._get_existing_variant(variant_id)
        self._variant_repository.delete(model.id)

    def activate_variant(self, variant_id: str) -> ProductVariantModel:
        model = self._get_existing_variant(variant_id)
        model.is_active = True
        return self._variant_repository.update(model)

    def deactivate_variant(self, variant_id: str) -> ProductVariantModel:
        model = self._get_existing_variant(variant_id)
        model.is_active = False
        return self._variant_repository.update(model)

    def get_variant(self, variant_id: str) -> ProductVariantModel:
        return self._get_existing_variant(variant_id)

    def list_variants(self, product_id: str) -> list[ProductVariantModel]:
        product = self._get_existing_product(product_id)
        return self._variant_repository.get_by_product(product.id)

    def _get_existing_product(self, product_id: str) -> ProductModel:
        normalized_id = self._require_text(product_id, "Product ID is required.")
        product = self._product_repository.get_by_id(normalized_id)
        if product is None:
            raise ROSException("Product not found.", HTTPStatus.NOT_FOUND)
        return product

    def _get_active_product(self, product_id: str) -> ProductModel:
        product = self._get_existing_product(product_id)
        if not product.is_active:
            raise ROSException("Product is inactive.", HTTPStatus.CONFLICT)
        return product

    def _get_existing_variant(self, variant_id: str) -> ProductVariantModel:
        normalized_id = self._require_text(variant_id, "Variant ID is required.")
        variant = self._variant_repository.get_by_id(normalized_id)
        if variant is None:
            raise ROSException("Variant not found.", HTTPStatus.NOT_FOUND)
        return variant

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _require_non_negative_int(value: int, message: str) -> int:
        if not isinstance(value, int) or value < 0:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return value
