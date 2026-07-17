"""SQLAlchemy persistence models for the Inventory module."""

from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ros.core.extensions import db


class InventoryCategoryModel(db.Model):
    """Persistence model for inventory categories."""

    __tablename__ = "inventory_categories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    items: Mapped[list[InventoryItemModel]] = relationship("InventoryItemModel", back_populates="category", lazy="selectin")


class UnitOfMeasureModel(db.Model):
    """Persistence model for units of measure."""

    __tablename__ = "units_of_measure"
    __table_args__ = (CheckConstraint("precision >= 0", name="ck_units_of_measure_precision_non_negative"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    precision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    items: Mapped[list[InventoryItemModel]] = relationship("InventoryItemModel", back_populates="unit_of_measure", lazy="selectin")


class InventoryLocationTypeEnum(str, Enum):
    """Persistence enum for inventory location type."""

    STORE = "STORE"
    FREEZER = "FREEZER"
    COLD_ROOM = "COLD_ROOM"
    KITCHEN = "KITCHEN"
    BAR = "BAR"
    DISPATCH = "DISPATCH"
    OTHER = "OTHER"


class InventoryItemModel(db.Model):
    """Persistence model for inventory items."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("minimum_stock <= maximum_stock", name="ck_inventory_items_min_le_max"),
        CheckConstraint("reorder_level <= maximum_stock", name="ck_inventory_items_reorder_le_max"),
        CheckConstraint("minimum_stock >= 0", name="ck_inventory_items_min_non_negative"),
        CheckConstraint("maximum_stock >= 0", name="ck_inventory_items_max_non_negative"),
        CheckConstraint("reorder_level >= 0", name="ck_inventory_items_reorder_non_negative"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_categories.id"), nullable=False, index=True)
    unit_of_measure_id: Mapped[str] = mapped_column(String(64), ForeignKey("units_of_measure.id"), nullable=False, index=True)
    minimum_stock: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    maximum_stock: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    reorder_level: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    category: Mapped[InventoryCategoryModel] = relationship("InventoryCategoryModel", back_populates="items", lazy="selectin")
    unit_of_measure: Mapped[UnitOfMeasureModel] = relationship("UnitOfMeasureModel", back_populates="items", lazy="selectin")
    lots: Mapped[list[InventoryLotModel]] = relationship("InventoryLotModel", back_populates="inventory_item", lazy="selectin")
    stock_levels: Mapped[list[StockLevelModel]] = relationship("StockLevelModel", back_populates="inventory_item", lazy="selectin")
    transactions: Mapped[list[InventoryTransactionModel]] = relationship(
        "InventoryTransactionModel",
        back_populates="inventory_item",
        lazy="selectin",
    )


class InventoryLotModel(db.Model):
    """Persistence model for inventory lots."""

    __tablename__ = "inventory_lots"
    __table_args__ = (
        UniqueConstraint("inventory_item_id", "lot_number", name="uq_inventory_lots_item_lot_number"),
        CheckConstraint("quantity >= 0", name="ck_inventory_lots_quantity_non_negative"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inventory_item_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_items.id"), nullable=False, index=True)
    lot_number: Mapped[str] = mapped_column(String(120), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    supplier_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    inventory_item: Mapped[InventoryItemModel] = relationship("InventoryItemModel", back_populates="lots", lazy="selectin")
    transactions: Mapped[list[InventoryTransactionModel]] = relationship(
        "InventoryTransactionModel",
        back_populates="inventory_lot",
        lazy="selectin",
    )


class InventoryLocationModel(db.Model):
    """Persistence model for inventory locations."""

    __tablename__ = "inventory_locations"
    __table_args__ = (UniqueConstraint("branch_id", "name", name="uq_inventory_locations_branch_name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    branch_id: Mapped[str] = mapped_column(String(64), ForeignKey("branches.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_type: Mapped[InventoryLocationTypeEnum] = mapped_column(
        SAEnum(InventoryLocationTypeEnum, name="inventory_location_type_enum"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    stock_levels: Mapped[list[StockLevelModel]] = relationship("StockLevelModel", back_populates="location", lazy="selectin")
    transactions: Mapped[list[InventoryTransactionModel]] = relationship(
        "InventoryTransactionModel",
        back_populates="location",
        lazy="selectin",
    )


class InventoryTransactionTypeEnum(str, Enum):
    """Immutable inventory ledger transaction types."""

    RECEIVE = "RECEIVE"
    ISSUE = "ISSUE"
    CONSUMPTION = "CONSUMPTION"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    ADJUSTMENT_POSITIVE = "ADJUSTMENT_POSITIVE"
    ADJUSTMENT_NEGATIVE = "ADJUSTMENT_NEGATIVE"
    WASTE = "WASTE"
    RETURN = "RETURN"
    PRODUCTION_OUTPUT = "PRODUCTION_OUTPUT"


class InventoryNegativePolicyEnum(str, Enum):
    """Negative inventory policy used by stock movement engine."""

    STRICT = "STRICT"
    ALLOW = "ALLOW"
    MANAGER_OVERRIDE = "MANAGER_OVERRIDE"


class InventoryReferenceTypeEnum(str, Enum):
    """Cross-module reference types for inventory integration contracts."""

    GOODS_RECEIPT = "GOODS_RECEIPT"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    PRODUCTION_ORDER = "PRODUCTION_ORDER"
    SALES_ORDER = "SALES_ORDER"
    STOCK_TRANSFER = "STOCK_TRANSFER"
    STOCK_ADJUSTMENT = "STOCK_ADJUSTMENT"
    RETURN = "RETURN"
    WASTE_REPORT = "WASTE_REPORT"
    SYSTEM = "SYSTEM"


class StockAdjustmentTypeEnum(str, Enum):
    """Manual stock adjustment direction."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class StockLevelModel(db.Model):
    """Materialized stock projection by item and location."""

    __tablename__ = "stock_levels"
    __table_args__ = (
        UniqueConstraint("inventory_item_id", "location_id", name="uq_stock_levels_item_location"),
        CheckConstraint("reserved_quantity >= 0", name="ck_stock_levels_reserved_non_negative"),
        CheckConstraint("available_quantity = quantity - reserved_quantity", name="ck_stock_levels_available_formula"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inventory_item_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_items.id"), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_locations.id"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    available_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    last_transaction_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("inventory_transactions.id"),
        nullable=True,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    inventory_item: Mapped[InventoryItemModel] = relationship("InventoryItemModel", back_populates="stock_levels", lazy="selectin")
    location: Mapped[InventoryLocationModel] = relationship("InventoryLocationModel", back_populates="stock_levels", lazy="selectin")
    last_transaction: Mapped[InventoryTransactionModel | None] = relationship(
        "InventoryTransactionModel",
        foreign_keys=[last_transaction_id],
        lazy="selectin",
    )


class InventoryTransactionModel(db.Model):
    """Immutable inventory ledger record."""

    __tablename__ = "inventory_transactions"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_inventory_transactions_quantity_positive"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inventory_item_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_items.id"), nullable=False, index=True)
    inventory_lot_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("inventory_lots.id"), nullable=True, index=True)
    location_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_locations.id"), nullable=False, index=True)
    transaction_type: Mapped[InventoryTransactionTypeEnum] = mapped_column(
        SAEnum(InventoryTransactionTypeEnum, name="inventory_transaction_type_enum"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reference_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    performed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    inventory_item: Mapped[InventoryItemModel] = relationship("InventoryItemModel", back_populates="transactions", lazy="selectin")
    inventory_lot: Mapped[InventoryLotModel | None] = relationship("InventoryLotModel", back_populates="transactions", lazy="selectin")
    location: Mapped[InventoryLocationModel] = relationship("InventoryLocationModel", back_populates="transactions", lazy="selectin")
    stock_adjustments: Mapped[list[StockAdjustmentModel]] = relationship(
        "StockAdjustmentModel",
        back_populates="inventory_transaction",
        lazy="selectin",
    )


class StockAdjustmentModel(db.Model):
    """Immutable record of a manual stock count correction."""

    __tablename__ = "stock_adjustments"
    __table_args__ = (
        CheckConstraint("actual_quantity >= 0", name="ck_stock_adjustments_actual_non_negative"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    inventory_item_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_items.id"), nullable=False, index=True)
    inventory_location_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_locations.id"), nullable=False, index=True)
    inventory_lot_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("inventory_lots.id"), nullable=True, index=True)
    inventory_transaction_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("inventory_transactions.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    adjustment_type: Mapped[StockAdjustmentTypeEnum] = mapped_column(
        SAEnum(StockAdjustmentTypeEnum, name="stock_adjustment_type_enum"),
        nullable=False,
        index=True,
    )
    expected_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    variance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    performed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    inventory_item: Mapped[InventoryItemModel] = relationship("InventoryItemModel", lazy="selectin")
    inventory_location: Mapped[InventoryLocationModel] = relationship("InventoryLocationModel", lazy="selectin")
    inventory_lot: Mapped[InventoryLotModel | None] = relationship("InventoryLotModel", lazy="selectin")
    inventory_transaction: Mapped[InventoryTransactionModel] = relationship(
        "InventoryTransactionModel",
        back_populates="stock_adjustments",
        lazy="selectin",
    )
