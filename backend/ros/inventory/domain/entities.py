"""Domain entities for the Inventory module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum

from .exceptions import (
    InventoryCategoryDomainError,
    InventoryItemDomainError,
    InventoryLocationDomainError,
    InventoryLotDomainError,
    UnitOfMeasureDomainError,
)


@dataclass(slots=True)
class InventoryCategory:
    """Business entity representing an inventory category."""

    id: str
    name: str
    description: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Inventory category ID is required.")
        self.name = self._normalize_required(self.name, "Inventory category name is required.")
        self.description = self._normalize_required(self.description, "Inventory category description is required.")
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
            raise InventoryCategoryDomainError(message)
        return normalized


@dataclass(slots=True)
class UnitOfMeasure:
    """Business entity representing an inventory unit of measure."""

    id: str
    name: str
    symbol: str
    description: str
    precision: int
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Unit ID is required.")
        self.name = self._normalize_required(self.name, "Unit name is required.")
        self.symbol = self._normalize_required(self.symbol, "Unit symbol is required.")
        self.description = self._normalize_required(self.description, "Unit description is required.")
        self.precision = self._normalize_precision(self.precision)
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
            raise UnitOfMeasureDomainError(message)
        return normalized

    @staticmethod
    def _normalize_precision(value: int) -> int:
        if not isinstance(value, int) or value < 0:
            raise UnitOfMeasureDomainError("Unit precision must be zero or greater.")
        return value


@dataclass(slots=True)
class InventoryItem:
    """Business entity representing a tracked inventory item."""

    id: str
    name: str
    sku: str
    description: str
    category_id: str
    unit_of_measure_id: str
    minimum_stock: Decimal | str | int | float
    maximum_stock: Decimal | str | int | float
    reorder_level: Decimal | str | int | float
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Inventory item ID is required.")
        self.name = self._normalize_required(self.name, "Inventory item name is required.")
        self.sku = self._normalize_required(self.sku, "Inventory item SKU is required.")
        self.description = self._normalize_required(self.description, "Inventory item description is required.")
        self.category_id = self._normalize_required(self.category_id, "Inventory category ID is required.")
        self.unit_of_measure_id = self._normalize_required(self.unit_of_measure_id, "Unit of measure ID is required.")
        self.minimum_stock = self._normalize_quantity(self.minimum_stock, "Minimum stock must be zero or greater.")
        self.maximum_stock = self._normalize_quantity(self.maximum_stock, "Maximum stock must be zero or greater.")
        self.reorder_level = self._normalize_quantity(self.reorder_level, "Reorder level must be zero or greater.")
        self._validate_thresholds()
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(tz=UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(tz=UTC)

    def _validate_thresholds(self) -> None:
        if self.minimum_stock > self.maximum_stock:
            raise InventoryItemDomainError("Minimum stock cannot exceed maximum stock.")
        if self.reorder_level > self.maximum_stock:
            raise InventoryItemDomainError("Reorder level cannot exceed maximum stock.")

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise InventoryItemDomainError(message)
        return normalized

    @staticmethod
    def _normalize_quantity(value: Decimal | str | int | float, message: str) -> Decimal:
        try:
            quantity = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise InventoryItemDomainError(message) from exc
        if not quantity.is_finite() or quantity < 0:
            raise InventoryItemDomainError(message)
        return quantity.quantize(Decimal("0.0001"))


@dataclass(slots=True)
class InventoryLot:
    """Business entity representing a physical inventory lot."""

    id: str
    inventory_item_id: str
    lot_number: str
    received_date: date
    expiry_date: date | None
    quantity: Decimal | str | int | float
    supplier_reference: str
    notes: str
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Inventory lot ID is required.")
        self.inventory_item_id = self._normalize_required(self.inventory_item_id, "Inventory item ID is required.")
        self.lot_number = self._normalize_required(self.lot_number, "Lot number is required.")
        self.received_date = self._normalize_received_date(self.received_date)
        self.expiry_date = self._normalize_optional_date(self.expiry_date)
        self.quantity = self._normalize_quantity(self.quantity)
        self.supplier_reference = self._normalize_required(self.supplier_reference, "Supplier reference is required.")
        self.notes = self._normalize_required(self.notes, "Lot notes are required.")
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise InventoryLotDomainError(message)
        return normalized

    @staticmethod
    def _normalize_received_date(value: date) -> date:
        if not isinstance(value, date):
            raise InventoryLotDomainError("Received date is required.")
        return value

    @staticmethod
    def _normalize_optional_date(value: date | None) -> date | None:
        if value is not None and not isinstance(value, date):
            raise InventoryLotDomainError("Expiry date must be a valid date.")
        return value

    @staticmethod
    def _normalize_quantity(value: Decimal | str | int | float) -> Decimal:
        try:
            quantity = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise InventoryLotDomainError("Lot quantity must be a valid decimal value.") from exc
        if not quantity.is_finite() or quantity < 0:
            raise InventoryLotDomainError("Lot quantity cannot be negative.")
        return quantity.quantize(Decimal("0.0001"))


class InventoryLocationType(str, Enum):
    """Supported inventory location types."""

    STORE = "STORE"
    FREEZER = "FREEZER"
    COLD_ROOM = "COLD_ROOM"
    KITCHEN = "KITCHEN"
    BAR = "BAR"
    DISPATCH = "DISPATCH"
    OTHER = "OTHER"


@dataclass(slots=True)
class InventoryLocation:
    """Business entity representing a physical inventory location."""

    id: str
    branch_id: str
    name: str
    description: str
    location_type: InventoryLocationType
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Inventory location ID is required.")
        self.branch_id = self._normalize_required(self.branch_id, "Branch ID is required.")
        self.name = self._normalize_required(self.name, "Inventory location name is required.")
        self.description = self._normalize_required(self.description, "Inventory location description is required.")
        self.location_type = self._normalize_location_type(self.location_type)
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
            raise InventoryLocationDomainError(message)
        return normalized

    @staticmethod
    def _normalize_location_type(value: InventoryLocationType | str) -> InventoryLocationType:
        if isinstance(value, InventoryLocationType):
            return value
        try:
            return InventoryLocationType(str(value))
        except ValueError as exc:
            raise InventoryLocationDomainError("Invalid inventory location type.") from exc
