"""SQLAlchemy persistence models for the Recipes module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
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


class RecipeSecurityClassificationEnum(str, Enum):
    """Persistence enum for recipe security classification."""

    PUBLIC = "PUBLIC"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    SECRET = "SECRET"


class RecipeVersionStatusEnum(str, Enum):
    """Persistence enum for recipe version lifecycle."""

    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class RecipeIngredientTypeEnum(str, Enum):
    """Persistence enum for recipe ingredient reference type."""

    INVENTORY_ITEM = "INVENTORY_ITEM"
    SUB_RECIPE = "SUB_RECIPE"
    SECRET_FORMULATION = "SECRET_FORMULATION"


class RecipeModel(db.Model):
    """Persistence model for recipe aggregate root."""

    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    current_version_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=True)
    security_classification: Mapped[RecipeSecurityClassificationEnum] = mapped_column(
        SAEnum(RecipeSecurityClassificationEnum, name="recipe_security_classification_enum"),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    versions: Mapped[list[RecipeVersionModel]] = relationship(
        "RecipeVersionModel",
        back_populates="recipe",
        foreign_keys="RecipeVersionModel.recipe_id",
        lazy="selectin",
    )
    referenced_by_ingredients: Mapped[list[RecipeIngredientModel]] = relationship(
        "RecipeIngredientModel",
        back_populates="sub_recipe",
        foreign_keys="RecipeIngredientModel.recipe_id",
        lazy="selectin",
    )
    current_version: Mapped[RecipeVersionModel | None] = relationship(
        "RecipeVersionModel",
        foreign_keys=[current_version_id],
        lazy="selectin",
    )


class RecipeVersionModel(db.Model):
    """Persistence model for immutable recipe versions."""

    __tablename__ = "recipe_versions"
    __table_args__ = (
        UniqueConstraint("recipe_id", "version_number", name="uq_recipe_versions_recipe_version"),
        CheckConstraint("version_number > 0", name="ck_recipe_versions_version_positive"),
        Index(
            "ix_recipe_versions_active_unique",
            "recipe_id",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipes.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RecipeVersionStatusEnum] = mapped_column(
        SAEnum(RecipeVersionStatusEnum, name="recipe_version_status_enum"),
        nullable=False,
        index=True,
    )
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    recipe: Mapped[RecipeModel] = relationship(
        "RecipeModel",
        back_populates="versions",
        foreign_keys=[recipe_id],
        lazy="selectin",
    )
    ingredients: Mapped[list[RecipeIngredientModel]] = relationship(
        "RecipeIngredientModel",
        back_populates="recipe_version",
        foreign_keys="RecipeIngredientModel.recipe_version_id",
        lazy="selectin",
    )
    steps: Mapped[list[RecipeStepModel]] = relationship(
        "RecipeStepModel",
        back_populates="recipe_version",
        foreign_keys="RecipeStepModel.recipe_version_id",
        lazy="selectin",
    )
    yield_spec: Mapped[RecipeYieldModel | None] = relationship(
        "RecipeYieldModel",
        back_populates="recipe_version",
        foreign_keys="RecipeYieldModel.recipe_version_id",
        lazy="selectin",
        uselist=False,
    )
    waste_entries: Mapped[list[RecipeWasteModel]] = relationship(
        "RecipeWasteModel",
        back_populates="recipe_version",
        foreign_keys="RecipeWasteModel.recipe_version_id",
        lazy="selectin",
    )
    equipment_requirements: Mapped[list[RecipeEquipmentModel]] = relationship(
        "RecipeEquipmentModel",
        back_populates="recipe_version",
        foreign_keys="RecipeEquipmentModel.recipe_version_id",
        lazy="selectin",
    )
    packaging_requirements: Mapped[list[RecipePackagingModel]] = relationship(
        "RecipePackagingModel",
        back_populates="recipe_version",
        foreign_keys="RecipePackagingModel.recipe_version_id",
        lazy="selectin",
    )
    quality_standards: Mapped[list[RecipeQualityModel]] = relationship(
        "RecipeQualityModel",
        back_populates="recipe_version",
        foreign_keys="RecipeQualityModel.recipe_version_id",
        lazy="selectin",
    )


class SecretFormulationModel(db.Model):
    """Persistence model for encrypted secret formulations."""

    __tablename__ = "secret_formulations"
    __table_args__ = (
        UniqueConstraint("code", name="uq_secret_formulations_code"),
        CheckConstraint("encryption_version > 0", name="ck_secret_formulations_encryption_version_positive"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    security_classification: Mapped[RecipeSecurityClassificationEnum] = mapped_column(
        SAEnum(RecipeSecurityClassificationEnum, name="secret_formulation_security_classification_enum"),
        nullable=False,
    )
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    encryption_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    ingredients: Mapped[list[RecipeIngredientModel]] = relationship(
        "RecipeIngredientModel",
        back_populates="secret_formulation",
        foreign_keys="RecipeIngredientModel.secret_formulation_id",
        lazy="selectin",
    )


class RecipeIngredientModel(db.Model):
    """Persistence model for a single recipe version ingredient."""

    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_recipe_ingredients_quantity_positive"),
        CheckConstraint("tolerance >= 0", name="ck_recipe_ingredients_tolerance_non_negative"),
        CheckConstraint("display_order >= 0", name="ck_recipe_ingredients_display_order_non_negative"),
        CheckConstraint(
            "(" 
            "CASE WHEN inventory_item_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN recipe_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN secret_formulation_id IS NOT NULL THEN 1 ELSE 0 END"
            ") = 1",
            name="ck_recipe_ingredients_single_reference",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=False, index=True)
    ingredient_type: Mapped[RecipeIngredientTypeEnum] = mapped_column(
        SAEnum(RecipeIngredientTypeEnum, name="recipe_ingredient_type_enum"),
        nullable=False,
        index=True,
    )
    inventory_item_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("inventory_items.id"), nullable=True, index=True)
    recipe_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("recipes.id"), nullable=True, index=True)
    secret_formulation_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("secret_formulations.id"),
        nullable=True,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_of_measure_id: Mapped[str] = mapped_column(String(64), ForeignKey("units_of_measure.id"), nullable=False, index=True)
    tolerance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipe_version: Mapped[RecipeVersionModel] = relationship(
        "RecipeVersionModel",
        back_populates="ingredients",
        foreign_keys=[recipe_version_id],
        lazy="selectin",
    )
    inventory_item: Mapped[object | None] = relationship(
        "InventoryItemModel",
        foreign_keys=[inventory_item_id],
        lazy="selectin",
    )
    unit_of_measure: Mapped[object] = relationship(
        "UnitOfMeasureModel",
        foreign_keys=[unit_of_measure_id],
        lazy="selectin",
    )
    sub_recipe: Mapped[RecipeModel | None] = relationship(
        "RecipeModel",
        back_populates="referenced_by_ingredients",
        foreign_keys=[recipe_id],
        lazy="selectin",
    )
    secret_formulation: Mapped[SecretFormulationModel | None] = relationship(
        "SecretFormulationModel",
        back_populates="ingredients",
        foreign_keys=[secret_formulation_id],
        lazy="selectin",
    )


class SecretFormulationAccessAuditModel(db.Model):
    """Immutable audit log for secret formulation decryption requests."""

    __tablename__ = "secret_formulation_access_audits"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    secret_formulation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("secret_formulations.id"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recipe_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    encryption_version: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    client_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    request_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class RecipeAuditEventModel(db.Model):
    """Immutable audit log for recipe lifecycle and security events."""

    __tablename__ = "recipe_audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    branch_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    recipe_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    recipe_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    secret_formulation_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("secret_formulations.id"),
        nullable=True,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class RecipeStepModel(db.Model):
    """Persistence model for ordered recipe manufacturing steps."""

    __tablename__ = "recipe_steps"
    __table_args__ = (
        UniqueConstraint("recipe_version_id", "step_number", name="uq_recipe_steps_version_step"),
        CheckConstraint("step_number > 0", name="ck_recipe_steps_step_number_positive"),
        CheckConstraint("estimated_duration >= 0", name="ck_recipe_steps_duration_non_negative"),
        CheckConstraint(
            "temperature_max IS NULL OR temperature_min IS NULL OR temperature_max > temperature_min",
            name="ck_recipe_steps_temperature_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    temperature_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    temperature_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipe_version: Mapped[RecipeVersionModel] = relationship(
        "RecipeVersionModel",
        back_populates="steps",
        foreign_keys=[recipe_version_id],
        lazy="selectin",
    )


class RecipeYieldModel(db.Model):
    """Persistence model for expected recipe output."""

    __tablename__ = "recipe_yields"
    __table_args__ = (
        UniqueConstraint("recipe_version_id", name="uq_recipe_yields_recipe_version"),
        CheckConstraint("expected_quantity > 0", name="ck_recipe_yields_expected_quantity_positive"),
        CheckConstraint("expected_portions > 0", name="ck_recipe_yields_expected_portions_positive"),
        CheckConstraint("portion_weight > 0", name="ck_recipe_yields_portion_weight_positive"),
        CheckConstraint("yield_percentage >= 0 AND yield_percentage <= 100", name="ck_recipe_yields_percentage_range"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=False, index=True)
    expected_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_of_measure_id: Mapped[str] = mapped_column(String(64), ForeignKey("units_of_measure.id"), nullable=False, index=True)
    expected_portions: Mapped[int] = mapped_column(Integer, nullable=False)
    portion_weight: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    yield_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipe_version: Mapped[RecipeVersionModel] = relationship(
        "RecipeVersionModel",
        back_populates="yield_spec",
        foreign_keys=[recipe_version_id],
        lazy="selectin",
    )


class RecipeWasteModel(db.Model):
    """Persistence model for expected manufacturing waste."""

    __tablename__ = "recipe_wastes"
    __table_args__ = (
        CheckConstraint("expected_loss_quantity > 0", name="ck_recipe_wastes_loss_quantity_positive"),
        CheckConstraint("loss_percentage >= 0 AND loss_percentage <= 100", name="ck_recipe_wastes_percentage_range"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=False, index=True)
    inventory_item_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_items.id"), nullable=False, index=True)
    expected_loss_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    loss_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipe_version: Mapped[RecipeVersionModel] = relationship(
        "RecipeVersionModel",
        back_populates="waste_entries",
        foreign_keys=[recipe_version_id],
        lazy="selectin",
    )
    inventory_item: Mapped[InventoryItemModel] = relationship("InventoryItemModel", foreign_keys=[inventory_item_id], lazy="selectin")


class RecipeEquipmentModel(db.Model):
    """Persistence model for required manufacturing equipment."""

    __tablename__ = "recipe_equipment"
    __table_args__ = (
        UniqueConstraint("recipe_version_id", "equipment_name", name="uq_recipe_equipment_version_name"),
        CheckConstraint("quantity_required > 0", name="ck_recipe_equipment_quantity_positive"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=False, index=True)
    equipment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_required: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipe_version: Mapped[RecipeVersionModel] = relationship(
        "RecipeVersionModel",
        back_populates="equipment_requirements",
        foreign_keys=[recipe_version_id],
        lazy="selectin",
    )


class RecipePackagingModel(db.Model):
    """Persistence model for packaging requirements."""

    __tablename__ = "recipe_packaging"
    __table_args__ = (
        UniqueConstraint("recipe_version_id", "inventory_item_id", name="uq_recipe_packaging_version_item"),
        CheckConstraint("quantity > 0", name="ck_recipe_packaging_quantity_positive"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=False, index=True)
    inventory_item_id: Mapped[str] = mapped_column(String(64), ForeignKey("inventory_items.id"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipe_version: Mapped[RecipeVersionModel] = relationship(
        "RecipeVersionModel",
        back_populates="packaging_requirements",
        foreign_keys=[recipe_version_id],
        lazy="selectin",
    )
    inventory_item: Mapped[InventoryItemModel] = relationship("InventoryItemModel", foreign_keys=[inventory_item_id], lazy="selectin")


class RecipeQualityModel(db.Model):
    """Persistence model for measurable quality standards."""

    __tablename__ = "recipe_quality_standards"
    __table_args__ = (
        UniqueConstraint("recipe_version_id", "metric", name="uq_recipe_quality_version_metric"),
        CheckConstraint(
            "maximum_value IS NULL OR minimum_value IS NULL OR maximum_value >= minimum_value",
            name="ck_recipe_quality_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_version_id: Mapped[str] = mapped_column(String(64), ForeignKey("recipe_versions.id"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(255), nullable=False)
    minimum_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    maximum_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipe_version: Mapped[RecipeVersionModel] = relationship(
        "RecipeVersionModel",
        back_populates="quality_standards",
        foreign_keys=[recipe_version_id],
        lazy="selectin",
    )
