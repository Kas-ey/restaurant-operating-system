"""Repository implementations for Inventory persistence operations."""

from __future__ import annotations

from sqlalchemy import inspect, select, text
from sqlalchemy.sql import Select

from ros.core.extensions import db

from .models import (
    InventoryCategoryModel,
    InventoryItemModel,
    InventoryLocationModel,
    InventoryReferenceTypeEnum,
    StockAdjustmentModel,
    InventoryTransactionModel,
    InventoryLocationTypeEnum,
    InventoryLotModel,
    StockLevelModel,
    UnitOfMeasureModel,
)


class InventoryCategoryRepository:
    """Persistence repository for inventory categories."""

    def create(self, model: InventoryCategoryModel) -> InventoryCategoryModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: InventoryCategoryModel) -> InventoryCategoryModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, category_id: str) -> None:
        model = db.session.get(InventoryCategoryModel, category_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, category_id: str) -> InventoryCategoryModel | None:
        return db.session.get(InventoryCategoryModel, category_id)

    def get_all(self) -> list[InventoryCategoryModel]:
        return db.session.scalars(select(InventoryCategoryModel)).all()

    def get_by_name(self, name: str) -> InventoryCategoryModel | None:
        return db.session.scalar(select(InventoryCategoryModel).where(InventoryCategoryModel.name == name))

    def exists_by_name(self, name: str) -> bool:
        return self.get_by_name(name) is not None

    def has_items(self, category_id: str) -> bool:
        inspector = inspect(db.engine)
        if not inspector.has_table("inventory_items"):
            return False
        query = text("SELECT 1 FROM inventory_items WHERE category_id = :category_id LIMIT 1")
        return db.session.execute(query, {"category_id": category_id}).scalar() is not None


class UnitRepository:
    """Persistence repository for units of measure."""

    def create(self, model: UnitOfMeasureModel) -> UnitOfMeasureModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: UnitOfMeasureModel) -> UnitOfMeasureModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, unit_id: str) -> None:
        model = db.session.get(UnitOfMeasureModel, unit_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, unit_id: str) -> UnitOfMeasureModel | None:
        return db.session.get(UnitOfMeasureModel, unit_id)

    def get_all(self) -> list[UnitOfMeasureModel]:
        return db.session.scalars(select(UnitOfMeasureModel)).all()

    def get_by_name(self, name: str) -> UnitOfMeasureModel | None:
        return db.session.scalar(select(UnitOfMeasureModel).where(UnitOfMeasureModel.name == name))

    def get_by_symbol(self, symbol: str) -> UnitOfMeasureModel | None:
        return db.session.scalar(select(UnitOfMeasureModel).where(UnitOfMeasureModel.symbol == symbol))

    def exists_by_name(self, name: str) -> bool:
        return self.get_by_name(name) is not None

    def exists_by_symbol(self, symbol: str) -> bool:
        return self.get_by_symbol(symbol) is not None

    def has_items(self, unit_id: str) -> bool:
        inspector = inspect(db.engine)
        if not inspector.has_table("inventory_items"):
            return False
        query = text("SELECT 1 FROM inventory_items WHERE unit_of_measure_id = :unit_id LIMIT 1")
        return db.session.execute(query, {"unit_id": unit_id}).scalar() is not None


class InventoryItemRepository:
    """Persistence repository for inventory items."""

    def create(self, model: InventoryItemModel) -> InventoryItemModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: InventoryItemModel) -> InventoryItemModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, item_id: str) -> None:
        model = db.session.get(InventoryItemModel, item_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, item_id: str) -> InventoryItemModel | None:
        return db.session.get(InventoryItemModel, item_id)

    def get_all(self) -> list[InventoryItemModel]:
        return db.session.scalars(select(InventoryItemModel)).all()

    def get_by_sku(self, sku: str) -> InventoryItemModel | None:
        return db.session.scalar(select(InventoryItemModel).where(InventoryItemModel.sku == sku))

    def exists_by_sku(self, sku: str) -> bool:
        return self.get_by_sku(sku) is not None

    def has_transactions(self, item_id: str) -> bool:
        inspector = inspect(db.engine)
        if not inspector.has_table("inventory_transactions"):
            return False
        query = text("SELECT 1 FROM inventory_transactions WHERE inventory_item_id = :item_id LIMIT 1")
        return db.session.execute(query, {"item_id": item_id}).scalar() is not None


class InventoryLotRepository:
    """Persistence repository for inventory lots."""

    def create(self, model: InventoryLotModel) -> InventoryLotModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: InventoryLotModel) -> InventoryLotModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, lot_id: str) -> None:
        model = db.session.get(InventoryLotModel, lot_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, lot_id: str) -> InventoryLotModel | None:
        return db.session.get(InventoryLotModel, lot_id)

    def get_by_item(self, item_id: str) -> list[InventoryLotModel]:
        return db.session.scalars(select(InventoryLotModel).where(InventoryLotModel.inventory_item_id == item_id)).all()

    def get_by_lot_number(self, inventory_item_id: str, lot_number: str) -> InventoryLotModel | None:
        return db.session.scalar(
            select(InventoryLotModel).where(
                InventoryLotModel.inventory_item_id == inventory_item_id,
                InventoryLotModel.lot_number == lot_number,
            )
        )

    def has_transactions(self, lot_id: str) -> bool:
        inspector = inspect(db.engine)
        if not inspector.has_table("inventory_transactions"):
            return False
        query = text("SELECT 1 FROM inventory_transactions WHERE inventory_lot_id = :lot_id LIMIT 1")
        return db.session.execute(query, {"lot_id": lot_id}).scalar() is not None


class InventoryLocationRepository:
    """Persistence repository for inventory locations."""

    def create(self, model: InventoryLocationModel) -> InventoryLocationModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: InventoryLocationModel) -> InventoryLocationModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, location_id: str) -> None:
        model = db.session.get(InventoryLocationModel, location_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, location_id: str) -> InventoryLocationModel | None:
        return db.session.get(InventoryLocationModel, location_id)

    def get_all(self) -> list[InventoryLocationModel]:
        return db.session.scalars(select(InventoryLocationModel)).all()

    def get_by_branch(self, branch_id: str) -> list[InventoryLocationModel]:
        return db.session.scalars(select(InventoryLocationModel).where(InventoryLocationModel.branch_id == branch_id)).all()

    def get_by_type(self, location_type: InventoryLocationTypeEnum) -> list[InventoryLocationModel]:
        return db.session.scalars(
            select(InventoryLocationModel).where(InventoryLocationModel.location_type == location_type)
        ).all()

    def get_by_branch_and_name(self, branch_id: str, name: str) -> InventoryLocationModel | None:
        return db.session.scalar(
            select(InventoryLocationModel).where(
                InventoryLocationModel.branch_id == branch_id,
                InventoryLocationModel.name == name,
            )
        )

    def has_stock_levels(self, location_id: str) -> bool:
        inspector = inspect(db.engine)
        if not inspector.has_table("stock_levels"):
            return False
        query = text("SELECT 1 FROM stock_levels WHERE location_id = :location_id LIMIT 1")
        return db.session.execute(query, {"location_id": location_id}).scalar() is not None


class StockLevelRepository:
    """Persistence repository for stock projection rows."""

    def get_by_item_and_location(self, inventory_item_id: str, location_id: str) -> StockLevelModel | None:
        return db.session.scalar(
            select(StockLevelModel).where(
                StockLevelModel.inventory_item_id == inventory_item_id,
                StockLevelModel.location_id == location_id,
            )
        )

    def create_if_missing(self, model: StockLevelModel) -> StockLevelModel:
        existing = self.get_by_item_and_location(model.inventory_item_id, model.location_id)
        if existing is not None:
            return existing
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update_projection(self, model: StockLevelModel) -> StockLevelModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def get_all(self) -> list[StockLevelModel]:
        return db.session.scalars(select(StockLevelModel)).all()

    def get_by_item(self, inventory_item_id: str) -> list[StockLevelModel]:
        return db.session.scalars(select(StockLevelModel).where(StockLevelModel.inventory_item_id == inventory_item_id)).all()

    def get_by_location(self, location_id: str) -> list[StockLevelModel]:
        return db.session.scalars(select(StockLevelModel).where(StockLevelModel.location_id == location_id)).all()


class InventoryTransactionRepository:
    """Persistence repository for immutable inventory ledger records."""

    def create(self, model: InventoryTransactionModel) -> InventoryTransactionModel:
        db.session.add(model)
        db.session.flush()
        return model

    def get_by_id(self, transaction_id: str) -> InventoryTransactionModel | None:
        return db.session.get(InventoryTransactionModel, transaction_id)

    def get_all(self) -> list[InventoryTransactionModel]:
        return db.session.scalars(select(InventoryTransactionModel).order_by(InventoryTransactionModel.performed_at.desc())).all()

    def get_by_item(self, inventory_item_id: str) -> list[InventoryTransactionModel]:
        return db.session.scalars(
            select(InventoryTransactionModel)
            .where(InventoryTransactionModel.inventory_item_id == inventory_item_id)
            .order_by(InventoryTransactionModel.performed_at.desc())
        ).all()

    def get_by_reference(
        self,
        reference_type: str | InventoryReferenceTypeEnum,
        reference_id: str,
    ) -> list[InventoryTransactionModel]:
        reference_value = reference_type.value if isinstance(reference_type, InventoryReferenceTypeEnum) else reference_type
        return db.session.scalars(
            select(InventoryTransactionModel)
            .where(
                InventoryTransactionModel.reference_type == reference_value,
                InventoryTransactionModel.reference_id == reference_id,
            )
            .order_by(InventoryTransactionModel.performed_at.desc())
        ).all()

    def get_by_date_range(self, start_at, end_at) -> list[InventoryTransactionModel]:
        query: Select = select(InventoryTransactionModel)
        if start_at is not None:
            query = query.where(InventoryTransactionModel.performed_at >= start_at)
        if end_at is not None:
            query = query.where(InventoryTransactionModel.performed_at <= end_at)
        return db.session.scalars(query.order_by(InventoryTransactionModel.performed_at.desc())).all()


class StockAdjustmentRepository:
    """Persistence repository for immutable stock adjustments."""

    def create(self, model: StockAdjustmentModel) -> StockAdjustmentModel:
        db.session.add(model)
        db.session.flush()
        return model

    def get_by_id(self, adjustment_id: str) -> StockAdjustmentModel | None:
        return db.session.get(StockAdjustmentModel, adjustment_id)

    def get_all(self) -> list[StockAdjustmentModel]:
        return db.session.scalars(select(StockAdjustmentModel).order_by(StockAdjustmentModel.performed_at.desc())).all()

    def get_by_item(self, inventory_item_id: str) -> list[StockAdjustmentModel]:
        return db.session.scalars(
            select(StockAdjustmentModel)
            .where(StockAdjustmentModel.inventory_item_id == inventory_item_id)
            .order_by(StockAdjustmentModel.performed_at.desc())
        ).all()

    def get_by_date_range(self, start_at, end_at) -> list[StockAdjustmentModel]:
        query: Select = select(StockAdjustmentModel)
        if start_at is not None:
            query = query.where(StockAdjustmentModel.performed_at >= start_at)
        if end_at is not None:
            query = query.where(StockAdjustmentModel.performed_at <= end_at)
        return db.session.scalars(query.order_by(StockAdjustmentModel.performed_at.desc())).all()
