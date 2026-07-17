"""Serialization helpers for inventory API responses."""

from __future__ import annotations

from ros.inventory.persistence.models import (
    InventoryCategoryModel,
    InventoryItemModel,
    InventoryLocationModel,
    InventoryLotModel,
    InventoryTransactionModel,
    StockAdjustmentModel,
    StockLevelModel,
    UnitOfMeasureModel,
)


def inventory_category_to_dict(model: InventoryCategoryModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def unit_to_dict(model: UnitOfMeasureModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "symbol": model.symbol,
        "description": model.description,
        "precision": model.precision,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def inventory_item_to_dict(model: InventoryItemModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "sku": model.sku,
        "description": model.description,
        "category_id": model.category_id,
        "unit_of_measure_id": model.unit_of_measure_id,
        "minimum_stock": str(model.minimum_stock),
        "maximum_stock": str(model.maximum_stock),
        "reorder_level": str(model.reorder_level),
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def inventory_lot_to_dict(model: InventoryLotModel) -> dict:
    return {
        "id": model.id,
        "inventory_item_id": model.inventory_item_id,
        "lot_number": model.lot_number,
        "received_date": model.received_date.isoformat() if model.received_date else None,
        "expiry_date": model.expiry_date.isoformat() if model.expiry_date else None,
        "quantity": str(model.quantity),
        "supplier_reference": model.supplier_reference,
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
    }


def inventory_location_to_dict(model: InventoryLocationModel) -> dict:
    return {
        "id": model.id,
        "branch_id": model.branch_id,
        "name": model.name,
        "description": model.description,
        "location_type": model.location_type.value if model.location_type else None,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def stock_level_to_dict(model: StockLevelModel) -> dict:
    return {
        "id": model.id,
        "inventory_item_id": model.inventory_item_id,
        "location_id": model.location_id,
        "quantity": str(model.quantity),
        "reserved_quantity": str(model.reserved_quantity),
        "available_quantity": str(model.available_quantity),
        "last_transaction_id": model.last_transaction_id,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def inventory_transaction_to_dict(model: InventoryTransactionModel) -> dict:
    return {
        "id": model.id,
        "inventory_item_id": model.inventory_item_id,
        "inventory_lot_id": model.inventory_lot_id,
        "location_id": model.location_id,
        "transaction_type": model.transaction_type.value if model.transaction_type else None,
        "quantity": str(model.quantity),
        "reference_type": model.reference_type,
        "reference_id": model.reference_id,
        "reference_number": model.reference_number,
        "performed_by": model.performed_by,
        "performed_at": model.performed_at.isoformat() if model.performed_at else None,
        "notes": model.notes,
    }


def stock_adjustment_to_dict(model: StockAdjustmentModel) -> dict:
    return {
        "id": model.id,
        "inventory_item_id": model.inventory_item_id,
        "inventory_location_id": model.inventory_location_id,
        "inventory_lot_id": model.inventory_lot_id,
        "inventory_transaction_id": model.inventory_transaction_id,
        "adjustment_type": model.adjustment_type.value if model.adjustment_type else None,
        "expected_quantity": str(model.expected_quantity),
        "actual_quantity": str(model.actual_quantity),
        "variance": str(model.variance),
        "reason": model.reason,
        "approved_by": model.approved_by,
        "performed_by": model.performed_by,
        "performed_at": model.performed_at.isoformat() if model.performed_at else None,
        "notes": model.notes,
    }


def stock_movement_result_to_dict(result) -> dict:
    return {
        "transaction": inventory_transaction_to_dict(result.transaction),
        "stock_level": stock_level_to_dict(result.stock_level),
    }
