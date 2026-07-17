"""Serialization helpers for products API responses."""

from __future__ import annotations

from ros.products.persistence.models import (
    ModifierGroupModel,
    ModifierOptionModel,
    ProductCategoryModel,
    ProductModel,
    ProductPriceModel,
    ProductVariantModel,
    VariantPriceModel,
)


def category_to_dict(model: ProductCategoryModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def product_to_dict(model: ProductModel) -> dict:
    category = None
    if model.category is not None:
        category = {
            "id": model.category.id,
            "name": model.category.name,
        }

    return {
        "id": model.id,
        "name": model.name,
        "sku": model.sku,
        "description": model.description,
        "category": category,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def variant_to_dict(model: ProductVariantModel) -> dict:
    return {
        "id": model.id,
        "product_id": model.product_id,
        "name": model.name,
        "sku": model.sku,
        "description": model.description,
        "display_order": model.display_order,
        "is_default": model.is_default,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def modifier_group_to_dict(model: ModifierGroupModel) -> dict:
    selection_type = model.selection_type.value if hasattr(model.selection_type, "value") else str(model.selection_type)
    return {
        "id": model.id,
        "product_id": model.product_id,
        "name": model.name,
        "description": model.description,
        "selection_type": selection_type,
        "minimum_required": model.minimum_required,
        "maximum_allowed": model.maximum_allowed,
        "display_order": model.display_order,
        "is_required": model.is_required,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def modifier_option_to_dict(model: ModifierOptionModel) -> dict:
    return {
        "id": model.id,
        "modifier_group_id": model.modifier_group_id,
        "name": model.name,
        "description": model.description,
        "display_order": model.display_order,
        "is_default": model.is_default,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def product_price_to_dict(model: ProductPriceModel) -> dict:
    return {
        "id": model.id,
        "amount": str(model.amount),
        "currency": model.currency,
        "effective_from": model.effective_from.isoformat() if model.effective_from else None,
        "effective_to": model.effective_to.isoformat() if model.effective_to else None,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def variant_price_to_dict(model: VariantPriceModel) -> dict:
    return {
        "id": model.id,
        "amount": str(model.amount),
        "currency": model.currency,
        "effective_from": model.effective_from.isoformat() if model.effective_from else None,
        "effective_to": model.effective_to.isoformat() if model.effective_to else None,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }
