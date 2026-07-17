"""Serialization helpers for recipes API responses."""

from __future__ import annotations

from ros.recipes.persistence.models import (
    RecipeEquipmentModel,
    RecipeIngredientModel,
    RecipeModel,
    RecipePackagingModel,
    RecipeQualityModel,
    RecipeStepModel,
    RecipeVersionModel,
    RecipeWasteModel,
    RecipeYieldModel,
    SecretFormulationModel,
)


def recipe_to_dict(model: RecipeModel) -> dict:
    security = model.security_classification.value if hasattr(model.security_classification, "value") else str(model.security_classification)
    return {
        "id": model.id,
        "product_id": model.product_id,
        "code": model.code,
        "name": model.name,
        "description": model.description,
        "is_active": model.is_active,
        "security_classification": security,
        "current_version_id": model.current_version_id,
        "created_by": model.created_by,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def version_to_dict(model: RecipeVersionModel) -> dict:
    status = model.status.value if hasattr(model.status, "value") else str(model.status)
    return {
        "id": model.id,
        "recipe_id": model.recipe_id,
        "version_number": model.version_number,
        "status": status,
        "change_summary": model.change_summary,
        "effective_date": model.effective_date.isoformat() if model.effective_date else None,
        "approved_by": model.approved_by,
        "approved_at": model.approved_at.isoformat() if model.approved_at else None,
        "created_by": model.created_by,
        "created_at": model.created_at.isoformat() if model.created_at else None,
    }


def ingredient_to_dict(model: RecipeIngredientModel) -> dict:
    ingredient_type = model.ingredient_type.value if hasattr(model.ingredient_type, "value") else str(model.ingredient_type)
    return {
        "id": model.id,
        "recipe_version_id": model.recipe_version_id,
        "ingredient_type": ingredient_type,
        "inventory_item_id": model.inventory_item_id,
        "recipe_id": model.recipe_id,
        "secret_formulation_id": model.secret_formulation_id,
        "quantity": str(model.quantity),
        "unit_of_measure_id": model.unit_of_measure_id,
        "tolerance": str(model.tolerance),
        "display_order": model.display_order,
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def secret_formulation_metadata_to_dict(model: SecretFormulationModel) -> dict:
    security = model.security_classification.value if hasattr(model.security_classification, "value") else str(model.security_classification)
    return {
        "id": model.id,
        "code": model.code,
        "name": model.name,
        "description": model.description,
        "security_classification": security,
        "is_active": model.is_active,
        "created_by": model.created_by,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def step_to_dict(model: RecipeStepModel) -> dict:
    return {
        "id": model.id,
        "recipe_version_id": model.recipe_version_id,
        "step_number": model.step_number,
        "title": model.title,
        "description": model.description,
        "estimated_duration": model.estimated_duration,
        "temperature_min": str(model.temperature_min) if model.temperature_min is not None else None,
        "temperature_max": str(model.temperature_max) if model.temperature_max is not None else None,
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def yield_to_dict(model: RecipeYieldModel) -> dict:
    return {
        "id": model.id,
        "recipe_version_id": model.recipe_version_id,
        "expected_quantity": str(model.expected_quantity),
        "unit_of_measure_id": model.unit_of_measure_id,
        "expected_portions": model.expected_portions,
        "portion_weight": str(model.portion_weight),
        "yield_percentage": str(model.yield_percentage),
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def waste_to_dict(model: RecipeWasteModel) -> dict:
    return {
        "id": model.id,
        "recipe_version_id": model.recipe_version_id,
        "inventory_item_id": model.inventory_item_id,
        "expected_loss_quantity": str(model.expected_loss_quantity),
        "loss_percentage": str(model.loss_percentage),
        "reason": model.reason,
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def equipment_to_dict(model: RecipeEquipmentModel) -> dict:
    return {
        "id": model.id,
        "recipe_version_id": model.recipe_version_id,
        "equipment_name": model.equipment_name,
        "quantity_required": str(model.quantity_required),
        "mandatory": model.mandatory,
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def packaging_to_dict(model: RecipePackagingModel) -> dict:
    return {
        "id": model.id,
        "recipe_version_id": model.recipe_version_id,
        "inventory_item_id": model.inventory_item_id,
        "quantity": str(model.quantity),
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


def quality_to_dict(model: RecipeQualityModel) -> dict:
    return {
        "id": model.id,
        "recipe_version_id": model.recipe_version_id,
        "metric": model.metric,
        "minimum_value": str(model.minimum_value) if model.minimum_value is not None else None,
        "maximum_value": str(model.maximum_value) if model.maximum_value is not None else None,
        "target_value": str(model.target_value) if model.target_value is not None else None,
        "unit": model.unit,
        "notes": model.notes,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }
