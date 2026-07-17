"""SQLAlchemy persistence models for the Products module."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ros.core.extensions import db


class ProductCategoryModel(db.Model):
    """Persistence model for product categories."""

    __tablename__ = "product_categories"

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

    products: Mapped[list[ProductModel]] = relationship("ProductModel", back_populates="category", lazy="selectin")


class ModifierSelectionTypeEnum(str, Enum):
    """Persistence enum for modifier selection type."""

    SINGLE = "SINGLE"
    MULTIPLE = "MULTIPLE"


class ProductModel(db.Model):
    """Persistence model for products."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[str] = mapped_column(String(64), ForeignKey("product_categories.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    category: Mapped[ProductCategoryModel] = relationship("ProductCategoryModel", back_populates="products", lazy="selectin")
    variants: Mapped[list[ProductVariantModel]] = relationship("ProductVariantModel", back_populates="product", lazy="selectin")
    modifier_groups: Mapped[list[ModifierGroupModel]] = relationship("ModifierGroupModel", back_populates="product", lazy="selectin")
    prices: Mapped[list[ProductPriceModel]] = relationship("ProductPriceModel", back_populates="product", lazy="selectin")


class ProductVariantModel(db.Model):
    """Persistence model for product variants."""

    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_product_variants_product_name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    product: Mapped[ProductModel] = relationship("ProductModel", back_populates="variants", lazy="selectin")
    prices: Mapped[list[VariantPriceModel]] = relationship("VariantPriceModel", back_populates="variant", lazy="selectin")


class ModifierGroupModel(db.Model):
    """Persistence model for modifier groups."""

    __tablename__ = "modifier_groups"
    __table_args__ = (UniqueConstraint("product_id", "name", name="uq_modifier_groups_product_name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    selection_type: Mapped[ModifierSelectionTypeEnum] = mapped_column(
        SAEnum(ModifierSelectionTypeEnum, name="modifier_selection_type_enum"),
        nullable=False,
    )
    minimum_required: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    maximum_allowed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    product: Mapped[ProductModel] = relationship("ProductModel", back_populates="modifier_groups", lazy="selectin")
    options: Mapped[list[ModifierOptionModel]] = relationship("ModifierOptionModel", back_populates="modifier_group", lazy="selectin")


class ModifierOptionModel(db.Model):
    """Persistence model for modifier options."""

    __tablename__ = "modifier_options"
    __table_args__ = (UniqueConstraint("modifier_group_id", "name", name="uq_modifier_options_group_name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    modifier_group_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("modifier_groups.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    modifier_group: Mapped[ModifierGroupModel] = relationship("ModifierGroupModel", back_populates="options", lazy="selectin")


class ProductPriceModel(db.Model):
    """Persistence model for product prices."""

    __tablename__ = "product_prices"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_product_prices_amount_positive"),
        CheckConstraint("length(currency) = 3", name="ck_product_prices_currency_len"),
        CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from",
            name="ck_product_prices_effective_window",
        ),
        Index(
            "ix_product_prices_active_unique",
            "product_id",
            unique=True,
            sqlite_where=text("is_active = 1"),
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    product: Mapped[ProductModel] = relationship("ProductModel", back_populates="prices", lazy="selectin")


class VariantPriceModel(db.Model):
    """Persistence model for variant override prices."""

    __tablename__ = "variant_prices"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_variant_prices_amount_positive"),
        CheckConstraint("length(currency) = 3", name="ck_variant_prices_currency_len"),
        CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from",
            name="ck_variant_prices_effective_window",
        ),
        Index(
            "ix_variant_prices_active_unique",
            "variant_id",
            unique=True,
            sqlite_where=text("is_active = 1"),
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    variant_id: Mapped[str] = mapped_column(String(64), ForeignKey("product_variants.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    variant: Mapped[ProductVariantModel] = relationship("ProductVariantModel", back_populates="prices", lazy="selectin")
