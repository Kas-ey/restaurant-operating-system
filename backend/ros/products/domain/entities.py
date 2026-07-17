"""Domain entities for the Products module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum

from .exceptions import (
    ModifierGroupDomainError,
    ModifierOptionDomainError,
    ProductCategoryDomainError,
    ProductDomainError,
    ProductPriceDomainError,
    ProductVariantDomainError,
    VariantPriceDomainError,
)


@dataclass(slots=True)
class ProductCategory:
    """Business entity representing a product category."""

    id: str
    name: str
    description: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Category ID is required.")
        self.name = self._normalize_required(self.name, "Category name is required.")
        self.description = self._normalize_required(self.description, "Category description is required.")
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    def rename(self, name: str) -> None:
        self.name = self._normalize_required(name, "Category name is required.")
        self.updated_at = datetime.now(tz=UTC)

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required(description, "Category description is required.")
        self.updated_at = datetime.now(tz=UTC)

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ProductCategoryDomainError(message)
        return normalized


@dataclass(slots=True)
class Product:
    """Business entity representing a sellable product."""

    id: str
    name: str
    sku: str
    description: str
    category_id: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Product ID is required.")
        self.name = self._normalize_required(self.name, "Product name is required.")
        self.sku = self._normalize_required(self.sku, "Product SKU is required.")
        self.description = self._normalize_required(self.description, "Product description is required.")
        self.category_id = self._normalize_required(self.category_id, "Product category ID is required.")
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    def rename(self, name: str) -> None:
        self.name = self._normalize_required(name, "Product name is required.")
        self.updated_at = datetime.now(tz=UTC)

    def update_sku(self, sku: str) -> None:
        self.sku = self._normalize_required(sku, "Product SKU is required.")
        self.updated_at = datetime.now(tz=UTC)

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required(description, "Product description is required.")
        self.updated_at = datetime.now(tz=UTC)

    def move_to_category(self, category_id: str) -> None:
        self.category_id = self._normalize_required(category_id, "Product category ID is required.")
        self.updated_at = datetime.now(tz=UTC)

    def assign_category(self, category_id: str) -> None:
        self.move_to_category(category_id)

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ProductDomainError(message)
        return normalized


class ModifierSelectionType(str, Enum):
    """Supported modifier selection types."""

    SINGLE = "SINGLE"
    MULTIPLE = "MULTIPLE"


@dataclass(slots=True)
class ProductVariant:
    """Business entity representing a product variant."""

    id: str
    product_id: str
    name: str
    sku: str
    description: str
    display_order: int
    is_default: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Variant ID is required.")
        self.product_id = self._normalize_required(self.product_id, "Product ID is required.")
        self.name = self._normalize_required(self.name, "Variant name is required.")
        self.sku = self._normalize_required(self.sku, "Variant SKU is required.")
        self.description = self._normalize_required(self.description, "Variant description is required.")
        self.display_order = self._normalize_display_order(self.display_order)
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    def mark_as_default(self) -> None:
        self.is_default = True
        self.updated_at = datetime.now(tz=UTC)

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ProductVariantDomainError(message)
        return normalized

    @staticmethod
    def _normalize_display_order(value: int) -> int:
        if not isinstance(value, int) or value < 0:
            raise ProductVariantDomainError("Variant display order must be zero or greater.")
        return value


@dataclass(slots=True)
class ModifierGroup:
    """Business entity representing a product modifier group."""

    id: str
    product_id: str
    name: str
    description: str
    selection_type: ModifierSelectionType
    minimum_required: int
    maximum_allowed: int
    display_order: int
    is_required: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Modifier group ID is required.")
        self.product_id = self._normalize_required(self.product_id, "Product ID is required.")
        self.name = self._normalize_required(self.name, "Modifier group name is required.")
        self.description = self._normalize_required(self.description, "Modifier group description is required.")
        self.selection_type = self._normalize_selection_type(self.selection_type)
        self.minimum_required = self._normalize_non_negative(self.minimum_required, "Minimum required must be zero or greater.")
        self.maximum_allowed = self._normalize_non_negative(self.maximum_allowed, "Maximum allowed must be zero or greater.")
        self.display_order = self._normalize_non_negative(self.display_order, "Display order must be zero or greater.")
        self.validate_selection_limits()
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    def validate_selection_limits(self) -> None:
        if self.maximum_allowed < self.minimum_required:
            raise ModifierGroupDomainError("Maximum allowed must be greater than or equal to minimum required.")
        if self.is_required and self.minimum_required < 1:
            raise ModifierGroupDomainError("Required modifier group must have minimum required of at least one.")
        if self.selection_type == ModifierSelectionType.SINGLE and self.maximum_allowed > 1:
            raise ModifierGroupDomainError("SINGLE selection type cannot allow more than one selection.")

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ModifierGroupDomainError(message)
        return normalized

    @staticmethod
    def _normalize_non_negative(value: int, message: str) -> int:
        if not isinstance(value, int) or value < 0:
            raise ModifierGroupDomainError(message)
        return value

    @staticmethod
    def _normalize_selection_type(value: ModifierSelectionType | str) -> ModifierSelectionType:
        if isinstance(value, ModifierSelectionType):
            return value
        try:
            return ModifierSelectionType(str(value))
        except ValueError as exc:
            raise ModifierGroupDomainError("Invalid modifier group selection type.") from exc


@dataclass(slots=True)
class ModifierOption:
    """Business entity representing a modifier option."""

    id: str
    modifier_group_id: str
    name: str
    description: str
    display_order: int
    is_default: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Modifier option ID is required.")
        self.modifier_group_id = self._normalize_required(self.modifier_group_id, "Modifier group ID is required.")
        self.name = self._normalize_required(self.name, "Modifier option name is required.")
        self.description = self._normalize_required(self.description, "Modifier option description is required.")
        self.display_order = self._normalize_display_order(self.display_order)
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ModifierOptionDomainError(message)
        return normalized

    @staticmethod
    def _normalize_display_order(value: int) -> int:
        if not isinstance(value, int) or value < 0:
            raise ModifierOptionDomainError("Modifier option display order must be zero or greater.")
        return value


@dataclass(slots=True)
class ProductPrice:
    """Business entity representing a product selling price."""

    id: str
    product_id: str
    amount: Decimal | str | int | float
    currency: str
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Product price ID is required.")
        self.product_id = self._normalize_required(self.product_id, "Product ID is required.")
        self.amount = self._normalize_amount(self.amount)
        self.currency = self._normalize_currency(self.currency)
        self.effective_from, self.effective_to = self._normalize_dates(self.effective_from, self.effective_to)
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ProductPriceDomainError(message)
        return normalized

    @staticmethod
    def _normalize_amount(value: Decimal | str | int | float) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ProductPriceDomainError("Price amount must be a valid number.") from exc
        if not amount.is_finite() or amount <= 0:
            raise ProductPriceDomainError("Price amount must be greater than zero.")
        return amount.quantize(Decimal("0.01"))

    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        normalized = cls._normalize_required(value, "Currency is required.").upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ProductPriceDomainError("Currency must be a 3-letter code.")
        return normalized

    @staticmethod
    def _normalize_dates(effective_from: date | None, effective_to: date | None) -> tuple[date | None, date | None]:
        if effective_from is not None and not isinstance(effective_from, date):
            raise ProductPriceDomainError("effective_from must be a valid date.")
        if effective_to is not None and not isinstance(effective_to, date):
            raise ProductPriceDomainError("effective_to must be a valid date.")
        if effective_from is not None and effective_to is not None and effective_to < effective_from:
            raise ProductPriceDomainError("effective_to cannot be earlier than effective_from.")
        return effective_from, effective_to


@dataclass(slots=True)
class VariantPrice:
    """Business entity representing a variant override price."""

    id: str
    variant_id: str
    amount: Decimal | str | int | float
    currency: str
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Variant price ID is required.")
        self.variant_id = self._normalize_required(self.variant_id, "Variant ID is required.")
        self.amount = self._normalize_amount(self.amount)
        self.currency = self._normalize_currency(self.currency)
        self.effective_from, self.effective_to = self._normalize_dates(self.effective_from, self.effective_to)
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise VariantPriceDomainError(message)
        return normalized

    @staticmethod
    def _normalize_amount(value: Decimal | str | int | float) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise VariantPriceDomainError("Price amount must be a valid number.") from exc
        if not amount.is_finite() or amount <= 0:
            raise VariantPriceDomainError("Price amount must be greater than zero.")
        return amount.quantize(Decimal("0.01"))

    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        normalized = cls._normalize_required(value, "Currency is required.").upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise VariantPriceDomainError("Currency must be a 3-letter code.")
        return normalized

    @staticmethod
    def _normalize_dates(effective_from: date | None, effective_to: date | None) -> tuple[date | None, date | None]:
        if effective_from is not None and not isinstance(effective_from, date):
            raise VariantPriceDomainError("effective_from must be a valid date.")
        if effective_to is not None and not isinstance(effective_to, date):
            raise VariantPriceDomainError("effective_to must be a valid date.")
        if effective_from is not None and effective_to is not None and effective_to < effective_from:
            raise VariantPriceDomainError("effective_to cannot be earlier than effective_from.")
        return effective_from, effective_to
