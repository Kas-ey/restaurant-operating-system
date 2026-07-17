"""Repository implementations for Recipes persistence operations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import inspect, select, text

from ros.core.extensions import db

from .models import (
    RecipeEquipmentModel,
    RecipeIngredientModel,
    RecipeModel,
    RecipePackagingModel,
    RecipeQualityModel,
    RecipeStepModel,
    RecipeVersionModel,
    RecipeVersionStatusEnum,
    RecipeWasteModel,
    RecipeYieldModel,
    RecipeAuditEventModel,
    SecretFormulationAccessAuditModel,
    SecretFormulationModel,
)


class RecipeRepository:
    """Persistence repository for recipes."""

    def create(self, model: RecipeModel) -> RecipeModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipeModel) -> RecipeModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, recipe_id: str) -> None:
        model = db.session.get(RecipeModel, recipe_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, recipe_id: str) -> RecipeModel | None:
        return db.session.get(RecipeModel, recipe_id)

    def get_active_by_id(self, recipe_id: str) -> RecipeModel | None:
        return db.session.scalar(
            select(RecipeModel).where(
                RecipeModel.id == recipe_id,
                RecipeModel.is_active.is_(True),
            )
        )

    def get_all(self) -> list[RecipeModel]:
        return db.session.scalars(select(RecipeModel)).all()

    def get_by_product(self, product_id: str) -> list[RecipeModel]:
        return db.session.scalars(select(RecipeModel).where(RecipeModel.product_id == product_id)).all()

    def get_by_code(self, code: str) -> RecipeModel | None:
        return db.session.scalar(select(RecipeModel).where(RecipeModel.code == code))

    def exists_by_code(self, code: str) -> bool:
        return self.get_by_code(code) is not None

    def has_production_references(self, recipe_id: str) -> bool:
        inspector = inspect(db.engine)
        candidate_tables = ["production_orders", "production_runs", "production_batches"]
        for table_name in candidate_tables:
            if inspector.has_table(table_name):
                query = text(f"SELECT 1 FROM {table_name} WHERE recipe_id = :recipe_id LIMIT 1")
                if db.session.execute(query, {"recipe_id": recipe_id}).scalar() is not None:
                    return True
        return False


class RecipeVersionRepository:
    """Persistence repository for recipe versions."""

    def create(self, model: RecipeVersionModel) -> RecipeVersionModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def get_by_id(self, version_id: str) -> RecipeVersionModel | None:
        return db.session.get(RecipeVersionModel, version_id)

    def get_active_by_id(self, version_id: str) -> RecipeVersionModel | None:
        return db.session.scalar(
            select(RecipeVersionModel).where(
                RecipeVersionModel.id == version_id,
                RecipeVersionModel.status == RecipeVersionStatusEnum.ACTIVE,
            )
        )

    def get_by_recipe(self, recipe_id: str) -> list[RecipeVersionModel]:
        return db.session.scalars(
            select(RecipeVersionModel)
            .where(RecipeVersionModel.recipe_id == recipe_id)
            .order_by(RecipeVersionModel.version_number.desc())
        ).all()

    def get_active_version(self, recipe_id: str) -> RecipeVersionModel | None:
        return db.session.scalar(
            select(RecipeVersionModel).where(
                RecipeVersionModel.recipe_id == recipe_id,
                RecipeVersionModel.status == RecipeVersionStatusEnum.ACTIVE,
            )
        )

    def get_latest_version(self, recipe_id: str) -> RecipeVersionModel | None:
        return db.session.scalar(
            select(RecipeVersionModel)
            .where(RecipeVersionModel.recipe_id == recipe_id)
            .order_by(RecipeVersionModel.version_number.desc())
            .limit(1)
        )

    def save(self, model: RecipeVersionModel) -> RecipeVersionModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def activate(self, recipe: RecipeModel, version: RecipeVersionModel) -> RecipeVersionModel:
        currently_active = self.get_active_version(recipe.id)
        if currently_active is not None and currently_active.id != version.id:
            currently_active.status = RecipeVersionStatusEnum.ARCHIVED
        version.status = RecipeVersionStatusEnum.ACTIVE
        recipe.current_version_id = version.id
        db.session.flush()
        return version

    def mark_approved(self, model: RecipeVersionModel, approved_by: str, approved_at: datetime) -> RecipeVersionModel:
        model.status = RecipeVersionStatusEnum.APPROVED
        model.approved_by = approved_by
        model.approved_at = approved_at
        db.session.flush()
        return model

    def mark_under_review(self, model: RecipeVersionModel) -> RecipeVersionModel:
        model.status = RecipeVersionStatusEnum.UNDER_REVIEW
        db.session.flush()
        return model

    def mark_archived(self, model: RecipeVersionModel) -> RecipeVersionModel:
        model.status = RecipeVersionStatusEnum.ARCHIVED
        db.session.flush()
        return model


class RecipeIngredientRepository:
    """Persistence repository for recipe ingredients."""

    def create(self, model: RecipeIngredientModel) -> RecipeIngredientModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipeIngredientModel) -> RecipeIngredientModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, ingredient_id: str) -> None:
        model = db.session.get(RecipeIngredientModel, ingredient_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, ingredient_id: str) -> RecipeIngredientModel | None:
        return db.session.get(RecipeIngredientModel, ingredient_id)

    def get_by_recipe_version(self, recipe_version_id: str) -> list[RecipeIngredientModel]:
        return db.session.scalars(
            select(RecipeIngredientModel)
            .where(RecipeIngredientModel.recipe_version_id == recipe_version_id)
            .order_by(RecipeIngredientModel.display_order.asc(), RecipeIngredientModel.created_at.asc())
        ).all()


class SecretFormulationRepository:
    """Persistence repository for encrypted secret formulations."""

    def create(self, model: SecretFormulationModel) -> SecretFormulationModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: SecretFormulationModel) -> SecretFormulationModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def get_by_id(self, formulation_id: str) -> SecretFormulationModel | None:
        return db.session.get(SecretFormulationModel, formulation_id)

    def get_by_code(self, code: str) -> SecretFormulationModel | None:
        return db.session.scalar(select(SecretFormulationModel).where(SecretFormulationModel.code == code))

    def exists_by_code(self, code: str) -> bool:
        return self.get_by_code(code) is not None

    def get_all(self) -> list[SecretFormulationModel]:
        return db.session.scalars(select(SecretFormulationModel)).all()

    def has_ingredients_reference(self, formulation_id: str) -> bool:
        query = select(RecipeIngredientModel.id).where(RecipeIngredientModel.secret_formulation_id == formulation_id).limit(1)
        return db.session.scalar(query) is not None


class SecretFormulationAccessAuditRepository:
    """Persistence repository for immutable secret formulation audit records."""

    def create(self, model: SecretFormulationAccessAuditModel) -> SecretFormulationAccessAuditModel:
        db.session.add(model)
        db.session.flush()
        return model


class RecipeAuditEventRepository:
    """Persistence repository for immutable recipe audit events."""

    def create(self, model: RecipeAuditEventModel) -> RecipeAuditEventModel:
        db.session.add(model)
        db.session.flush()
        return model


class RecipeStepRepository:
    """Persistence repository for recipe steps."""

    def create(self, model: RecipeStepModel) -> RecipeStepModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipeStepModel) -> RecipeStepModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, step_id: str) -> None:
        model = db.session.get(RecipeStepModel, step_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, step_id: str) -> RecipeStepModel | None:
        return db.session.get(RecipeStepModel, step_id)

    def get_by_recipe_version(self, recipe_version_id: str) -> list[RecipeStepModel]:
        return db.session.scalars(
            select(RecipeStepModel)
            .where(RecipeStepModel.recipe_version_id == recipe_version_id)
            .order_by(RecipeStepModel.step_number.asc(), RecipeStepModel.created_at.asc())
        ).all()


class RecipeYieldRepository:
    """Persistence repository for recipe yield definitions."""

    def create(self, model: RecipeYieldModel) -> RecipeYieldModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipeYieldModel) -> RecipeYieldModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, yield_id: str) -> None:
        model = db.session.get(RecipeYieldModel, yield_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, yield_id: str) -> RecipeYieldModel | None:
        return db.session.get(RecipeYieldModel, yield_id)

    def get_by_recipe_version(self, recipe_version_id: str) -> RecipeYieldModel | None:
        return db.session.scalar(select(RecipeYieldModel).where(RecipeYieldModel.recipe_version_id == recipe_version_id))


class RecipeWasteRepository:
    """Persistence repository for recipe waste definitions."""

    def create(self, model: RecipeWasteModel) -> RecipeWasteModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipeWasteModel) -> RecipeWasteModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, waste_id: str) -> None:
        model = db.session.get(RecipeWasteModel, waste_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, waste_id: str) -> RecipeWasteModel | None:
        return db.session.get(RecipeWasteModel, waste_id)

    def get_by_recipe_version(self, recipe_version_id: str) -> list[RecipeWasteModel]:
        return db.session.scalars(
            select(RecipeWasteModel)
            .where(RecipeWasteModel.recipe_version_id == recipe_version_id)
            .order_by(RecipeWasteModel.created_at.asc())
        ).all()


class RecipeEquipmentRepository:
    """Persistence repository for recipe equipment requirements."""

    def create(self, model: RecipeEquipmentModel) -> RecipeEquipmentModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipeEquipmentModel) -> RecipeEquipmentModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, equipment_id: str) -> None:
        model = db.session.get(RecipeEquipmentModel, equipment_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, equipment_id: str) -> RecipeEquipmentModel | None:
        return db.session.get(RecipeEquipmentModel, equipment_id)

    def get_by_recipe_version(self, recipe_version_id: str) -> list[RecipeEquipmentModel]:
        return db.session.scalars(
            select(RecipeEquipmentModel)
            .where(RecipeEquipmentModel.recipe_version_id == recipe_version_id)
            .order_by(RecipeEquipmentModel.equipment_name.asc(), RecipeEquipmentModel.created_at.asc())
        ).all()


class RecipePackagingRepository:
    """Persistence repository for recipe packaging requirements."""

    def create(self, model: RecipePackagingModel) -> RecipePackagingModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipePackagingModel) -> RecipePackagingModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, packaging_id: str) -> None:
        model = db.session.get(RecipePackagingModel, packaging_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, packaging_id: str) -> RecipePackagingModel | None:
        return db.session.get(RecipePackagingModel, packaging_id)

    def get_by_recipe_version(self, recipe_version_id: str) -> list[RecipePackagingModel]:
        return db.session.scalars(
            select(RecipePackagingModel)
            .where(RecipePackagingModel.recipe_version_id == recipe_version_id)
            .order_by(RecipePackagingModel.created_at.asc())
        ).all()


class RecipeQualityRepository:
    """Persistence repository for recipe quality standards."""

    def create(self, model: RecipeQualityModel) -> RecipeQualityModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: RecipeQualityModel) -> RecipeQualityModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, quality_id: str) -> None:
        model = db.session.get(RecipeQualityModel, quality_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, quality_id: str) -> RecipeQualityModel | None:
        return db.session.get(RecipeQualityModel, quality_id)

    def get_by_recipe_version(self, recipe_version_id: str) -> list[RecipeQualityModel]:
        return db.session.scalars(
            select(RecipeQualityModel)
            .where(RecipeQualityModel.recipe_version_id == recipe_version_id)
            .order_by(RecipeQualityModel.metric.asc(), RecipeQualityModel.created_at.asc())
        ).all()
