"""Product and variant pricing application service workflows."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.products.persistence.models import ProductModel, ProductPriceModel, ProductVariantModel, VariantPriceModel
from ros.products.persistence.repositories import (
    ProductPriceRepository,
    ProductRepository,
    ProductVariantRepository,
    VariantPriceRepository,
)
from ros.shared.exceptions import ROSException


class ProductPriceService:
    """Coordinates product pricing workflows."""

    def __init__(
        self,
        price_repository: ProductPriceRepository | None = None,
        product_repository: ProductRepository | None = None,
    ) -> None:
        self._price_repository = price_repository or ProductPriceRepository()
        self._product_repository = product_repository or ProductRepository()

    def create_price(
        self,
        *,
        price_id: str,
        product_id: str,
        amount: str | int | float,
        currency: str,
        effective_from: date | None,
        effective_to: date | None,
        is_active: bool,
    ) -> ProductPriceModel:
        product = self._get_existing_product(product_id)
        normalized_id = self._require_text(price_id, "Product price ID is required.")
        normalized_amount = self._normalize_amount(amount)
        normalized_currency = self._normalize_currency(currency)
        normalized_effective_from, normalized_effective_to = self._normalize_dates(effective_from, effective_to)
        should_activate = bool(is_active)

        model = ProductPriceModel(
            id=normalized_id,
            product_id=product.id,
            amount=normalized_amount,
            currency=normalized_currency,
            effective_from=normalized_effective_from,
            effective_to=normalized_effective_to,
            is_active=False,
        )
        created = self._price_repository.create(model)

        if should_activate:
            self.activate_price(created.id)

        return created

    def update_price(
        self,
        price_id: str,
        *,
        amount: str | int | float | None = None,
        currency: str | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
        is_active: bool | None = None,
    ) -> ProductPriceModel:
        model = self._get_existing_price(price_id)

        if amount is not None:
            model.amount = self._normalize_amount(amount)

        if currency is not None:
            model.currency = self._normalize_currency(currency)

        if effective_from is not None or effective_to is not None:
            next_effective_from = effective_from if effective_from is not None else model.effective_from
            next_effective_to = effective_to if effective_to is not None else model.effective_to
            model.effective_from, model.effective_to = self._normalize_dates(next_effective_from, next_effective_to)

        updated = self._price_repository.update(model)

        if is_active is True:
            self.activate_price(updated.id)
        elif is_active is False:
            self.deactivate_price(updated.id)

        return updated

    def activate_price(self, price_id: str) -> ProductPriceModel:
        model = self._get_existing_price(price_id)
        self._ensure_not_expired(model)
        self._price_repository.deactivate_active_price(model.product_id, exclude_price_id=model.id)
        model.is_active = True
        return self._price_repository.update(model)

    def deactivate_price(self, price_id: str) -> ProductPriceModel:
        model = self._get_existing_price(price_id)
        model.is_active = False
        return self._price_repository.update(model)

    def delete_price(self, price_id: str) -> None:
        model = self._get_existing_price(price_id)
        if model.is_active:
            raise ROSException("Cannot delete an active price.", HTTPStatus.CONFLICT)
        self._price_repository.delete(model.id)

    def list_prices(self, product_id: str) -> list[ProductPriceModel]:
        product = self._get_existing_product(product_id)
        return self._price_repository.get_price_history(product.id)

    def get_current_price(self, product_id: str) -> ProductPriceModel:
        product = self._get_existing_product(product_id)
        model = self._price_repository.get_active_price(product.id)
        if model is None:
            raise ROSException("Active product price not found.", HTTPStatus.NOT_FOUND)
        return model

    def _get_existing_product(self, product_id: str) -> ProductModel:
        normalized_id = self._require_text(product_id, "Product ID is required.")
        product = self._product_repository.get_by_id(normalized_id)
        if product is None:
            raise ROSException("Product not found.", HTTPStatus.NOT_FOUND)
        return product

    def _get_existing_price(self, price_id: str) -> ProductPriceModel:
        normalized_id = self._require_text(price_id, "Product price ID is required.")
        model = self._price_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Product price not found.", HTTPStatus.NOT_FOUND)
        return model

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _normalize_amount(value: str | int | float) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ROSException("Price amount must be a valid number.", HTTPStatus.BAD_REQUEST) from exc

        if not amount.is_finite():
            raise ROSException("Price amount must be a valid number.", HTTPStatus.BAD_REQUEST)

        if amount <= 0:
            raise ROSException("Price amount must be greater than zero.", HTTPStatus.BAD_REQUEST)
        return amount.quantize(Decimal("0.01"))

    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        normalized = cls._require_text(value, "Currency is required.").upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ROSException("Currency must be a 3-letter code.", HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _normalize_dates(effective_from: date | None, effective_to: date | None) -> tuple[date | None, date | None]:
        if effective_from is not None and not isinstance(effective_from, date):
            raise ROSException("effective_from must be a valid date.", HTTPStatus.BAD_REQUEST)
        if effective_to is not None and not isinstance(effective_to, date):
            raise ROSException("effective_to must be a valid date.", HTTPStatus.BAD_REQUEST)
        if effective_from is not None and effective_to is not None and effective_to < effective_from:
            raise ROSException("effective_to cannot be earlier than effective_from.", HTTPStatus.BAD_REQUEST)
        return effective_from, effective_to

    @staticmethod
    def _ensure_not_expired(model: ProductPriceModel) -> None:
        if model.effective_to is not None and model.effective_to < date.today():
            raise ROSException("Cannot activate an expired price.", HTTPStatus.CONFLICT)


class VariantPriceService:
    """Coordinates variant override pricing workflows."""

    def __init__(
        self,
        price_repository: VariantPriceRepository | None = None,
        variant_repository: ProductVariantRepository | None = None,
    ) -> None:
        self._price_repository = price_repository or VariantPriceRepository()
        self._variant_repository = variant_repository or ProductVariantRepository()

    def create_price(
        self,
        *,
        price_id: str,
        variant_id: str,
        amount: str | int | float,
        currency: str,
        effective_from: date | None,
        effective_to: date | None,
        is_active: bool,
    ) -> VariantPriceModel:
        variant = self._get_existing_variant(variant_id)
        normalized_id = self._require_text(price_id, "Variant price ID is required.")
        normalized_amount = ProductPriceService._normalize_amount(amount)
        normalized_currency = ProductPriceService._normalize_currency(currency)
        normalized_effective_from, normalized_effective_to = ProductPriceService._normalize_dates(effective_from, effective_to)
        should_activate = bool(is_active)

        model = VariantPriceModel(
            id=normalized_id,
            variant_id=variant.id,
            amount=normalized_amount,
            currency=normalized_currency,
            effective_from=normalized_effective_from,
            effective_to=normalized_effective_to,
            is_active=False,
        )
        created = self._price_repository.create(model)

        if should_activate:
            self.activate_price(created.id)

        return created

    def update_price(
        self,
        price_id: str,
        *,
        amount: str | int | float | None = None,
        currency: str | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
        is_active: bool | None = None,
    ) -> VariantPriceModel:
        model = self._get_existing_price(price_id)

        if amount is not None:
            model.amount = ProductPriceService._normalize_amount(amount)

        if currency is not None:
            model.currency = ProductPriceService._normalize_currency(currency)

        if effective_from is not None or effective_to is not None:
            next_effective_from = effective_from if effective_from is not None else model.effective_from
            next_effective_to = effective_to if effective_to is not None else model.effective_to
            model.effective_from, model.effective_to = ProductPriceService._normalize_dates(next_effective_from, next_effective_to)

        updated = self._price_repository.update(model)

        if is_active is True:
            self.activate_price(updated.id)
        elif is_active is False:
            self.deactivate_price(updated.id)

        return updated

    def activate_price(self, price_id: str) -> VariantPriceModel:
        model = self._get_existing_price(price_id)
        if model.effective_to is not None and model.effective_to < date.today():
            raise ROSException("Cannot activate an expired price.", HTTPStatus.CONFLICT)
        self._price_repository.deactivate_active_price(model.variant_id, exclude_price_id=model.id)
        model.is_active = True
        return self._price_repository.update(model)

    def deactivate_price(self, price_id: str) -> VariantPriceModel:
        model = self._get_existing_price(price_id)
        model.is_active = False
        return self._price_repository.update(model)

    def delete_price(self, price_id: str) -> None:
        model = self._get_existing_price(price_id)
        if model.is_active:
            raise ROSException("Cannot delete an active price.", HTTPStatus.CONFLICT)
        self._price_repository.delete(model.id)

    def list_prices(self, variant_id: str) -> list[VariantPriceModel]:
        variant = self._get_existing_variant(variant_id)
        return self._price_repository.get_price_history(variant.id)

    def get_current_price(self, variant_id: str) -> VariantPriceModel:
        variant = self._get_existing_variant(variant_id)
        model = self._price_repository.get_active_price(variant.id)
        if model is None:
            raise ROSException("Active variant price not found.", HTTPStatus.NOT_FOUND)
        return model

    def _get_existing_variant(self, variant_id: str) -> ProductVariantModel:
        normalized_id = self._require_text(variant_id, "Variant ID is required.")
        variant = self._variant_repository.get_by_id(normalized_id)
        if variant is None:
            raise ROSException("Variant not found.", HTTPStatus.NOT_FOUND)
        return variant

    def _get_existing_price(self, price_id: str) -> VariantPriceModel:
        normalized_id = self._require_text(price_id, "Variant price ID is required.")
        model = self._price_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Variant price not found.", HTTPStatus.NOT_FOUND)
        return model

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized
