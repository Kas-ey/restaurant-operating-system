"""Repository implementations for Products persistence operations."""

from __future__ import annotations

from sqlalchemy import select

from ros.core.extensions import db

from .models import (
    ModifierGroupModel,
    ModifierOptionModel,
    ProductCategoryModel,
    ProductModel,
    ProductPriceModel,
    ProductVariantModel,
    VariantPriceModel,
)


class ProductCategoryRepository:
    """Persistence repository for product categories."""

    def create(self, model: ProductCategoryModel) -> ProductCategoryModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def get_by_id(self, category_id: str) -> ProductCategoryModel | None:
        return db.session.get(ProductCategoryModel, category_id)

    def get_all(self) -> list[ProductCategoryModel]:
        return db.session.scalars(select(ProductCategoryModel)).all()

    def get_by_name(self, name: str) -> ProductCategoryModel | None:
        return db.session.scalar(select(ProductCategoryModel).where(ProductCategoryModel.name == name))

    def update(self, model: ProductCategoryModel) -> ProductCategoryModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, category_id: str) -> None:
        model = db.session.get(ProductCategoryModel, category_id)
        if model is not None:
            db.session.delete(model)

    def exists_by_name(self, name: str) -> bool:
        return self.get_by_name(name) is not None

    def has_products(self, category_id: str) -> bool:
        query = select(ProductModel.id).where(ProductModel.category_id == category_id).limit(1)
        return db.session.scalar(query) is not None


class ProductRepository:
    """Persistence repository for products."""

    def create(self, model: ProductModel) -> ProductModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def get_by_id(self, product_id: str) -> ProductModel | None:
        return db.session.get(ProductModel, product_id)

    def get_all(self) -> list[ProductModel]:
        return db.session.scalars(select(ProductModel)).all()

    def update(self, model: ProductModel) -> ProductModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, product_id: str) -> None:
        model = db.session.get(ProductModel, product_id)
        if model is not None:
            db.session.delete(model)

    def get_by_sku(self, sku: str) -> ProductModel | None:
        return db.session.scalar(select(ProductModel).where(ProductModel.sku == sku))

    def exists_by_sku(self, sku: str) -> bool:
        return self.get_by_sku(sku) is not None

    def get_by_category(self, category_id: str) -> list[ProductModel]:
        return db.session.scalars(select(ProductModel).where(ProductModel.category_id == category_id)).all()


class ProductVariantRepository:
    """Persistence repository for product variants."""

    def create(self, model: ProductVariantModel) -> ProductVariantModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: ProductVariantModel) -> ProductVariantModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, variant_id: str) -> None:
        model = db.session.get(ProductVariantModel, variant_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, variant_id: str) -> ProductVariantModel | None:
        return db.session.get(ProductVariantModel, variant_id)

    def get_all(self) -> list[ProductVariantModel]:
        return db.session.scalars(select(ProductVariantModel)).all()

    def get_by_product(self, product_id: str) -> list[ProductVariantModel]:
        return db.session.scalars(select(ProductVariantModel).where(ProductVariantModel.product_id == product_id)).all()

    def get_default_variant(self, product_id: str) -> ProductVariantModel | None:
        return db.session.scalar(
            select(ProductVariantModel).where(
                ProductVariantModel.product_id == product_id,
                ProductVariantModel.is_default.is_(True),
            )
        )

    def exists_by_sku(self, sku: str) -> bool:
        return db.session.scalar(select(ProductVariantModel.id).where(ProductVariantModel.sku == sku).limit(1)) is not None

    def set_default_variant(self, product_id: str, variant_id: str) -> None:
        variants = self.get_by_product(product_id)
        for variant in variants:
            variant.is_default = variant.id == variant_id
        db.session.flush()


class ModifierGroupRepository:
    """Persistence repository for modifier groups."""

    def create(self, model: ModifierGroupModel) -> ModifierGroupModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: ModifierGroupModel) -> ModifierGroupModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, group_id: str) -> None:
        model = db.session.get(ModifierGroupModel, group_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, group_id: str) -> ModifierGroupModel | None:
        return db.session.get(ModifierGroupModel, group_id)

    def get_all(self) -> list[ModifierGroupModel]:
        return db.session.scalars(select(ModifierGroupModel)).all()

    def get_by_product(self, product_id: str) -> list[ModifierGroupModel]:
        return db.session.scalars(select(ModifierGroupModel).where(ModifierGroupModel.product_id == product_id)).all()

    def get_by_name(self, product_id: str, name: str) -> ModifierGroupModel | None:
        return db.session.scalar(
            select(ModifierGroupModel).where(
                ModifierGroupModel.product_id == product_id,
                ModifierGroupModel.name == name,
            )
        )

    def activate(self, group_id: str) -> ModifierGroupModel | None:
        model = self.get_by_id(group_id)
        if model is not None:
            model.is_active = True
            db.session.flush()
        return model

    def deactivate(self, group_id: str) -> ModifierGroupModel | None:
        model = self.get_by_id(group_id)
        if model is not None:
            model.is_active = False
            db.session.flush()
        return model


class ModifierOptionRepository:
    """Persistence repository for modifier options."""

    def create(self, model: ModifierOptionModel) -> ModifierOptionModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: ModifierOptionModel) -> ModifierOptionModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, option_id: str) -> None:
        model = db.session.get(ModifierOptionModel, option_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, option_id: str) -> ModifierOptionModel | None:
        return db.session.get(ModifierOptionModel, option_id)

    def get_all(self) -> list[ModifierOptionModel]:
        return db.session.scalars(select(ModifierOptionModel)).all()

    def get_by_group(self, modifier_group_id: str) -> list[ModifierOptionModel]:
        return db.session.scalars(
            select(ModifierOptionModel).where(ModifierOptionModel.modifier_group_id == modifier_group_id)
        ).all()

    def get_by_name(self, modifier_group_id: str, name: str) -> ModifierOptionModel | None:
        return db.session.scalar(
            select(ModifierOptionModel).where(
                ModifierOptionModel.modifier_group_id == modifier_group_id,
                ModifierOptionModel.name == name,
            )
        )


class ProductPriceRepository:
    """Persistence repository for product pricing."""

    def create(self, model: ProductPriceModel) -> ProductPriceModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: ProductPriceModel) -> ProductPriceModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, price_id: str) -> None:
        model = db.session.get(ProductPriceModel, price_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, price_id: str) -> ProductPriceModel | None:
        return db.session.get(ProductPriceModel, price_id)

    def get_active_price(self, product_id: str) -> ProductPriceModel | None:
        return db.session.scalar(
            select(ProductPriceModel).where(
                ProductPriceModel.product_id == product_id,
                ProductPriceModel.is_active.is_(True),
            )
        )

    def get_price_history(self, product_id: str) -> list[ProductPriceModel]:
        return db.session.scalars(
            select(ProductPriceModel)
            .where(ProductPriceModel.product_id == product_id)
            .order_by(ProductPriceModel.created_at.desc())
        ).all()

    def activate_price(self, price_id: str) -> ProductPriceModel | None:
        model = self.get_by_id(price_id)
        if model is not None:
            model.is_active = True
            db.session.flush()
        return model

    def deactivate_price(self, price_id: str) -> ProductPriceModel | None:
        model = self.get_by_id(price_id)
        if model is not None:
            model.is_active = False
            db.session.flush()
        return model

    def deactivate_active_price(self, product_id: str, *, exclude_price_id: str | None = None) -> None:
        active = self.get_active_price(product_id)
        if active is not None and active.id != exclude_price_id:
            active.is_active = False
            db.session.flush()

    def exists(self, price_id: str) -> bool:
        return self.get_by_id(price_id) is not None


class VariantPriceRepository:
    """Persistence repository for variant pricing."""

    def create(self, model: VariantPriceModel) -> VariantPriceModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def update(self, model: VariantPriceModel) -> VariantPriceModel:
        merged_model = db.session.merge(model)
        db.session.flush()
        return merged_model

    def delete(self, price_id: str) -> None:
        model = db.session.get(VariantPriceModel, price_id)
        if model is not None:
            db.session.delete(model)

    def get_by_id(self, price_id: str) -> VariantPriceModel | None:
        return db.session.get(VariantPriceModel, price_id)

    def get_active_price(self, variant_id: str) -> VariantPriceModel | None:
        return db.session.scalar(
            select(VariantPriceModel).where(
                VariantPriceModel.variant_id == variant_id,
                VariantPriceModel.is_active.is_(True),
            )
        )

    def get_price_history(self, variant_id: str) -> list[VariantPriceModel]:
        return db.session.scalars(
            select(VariantPriceModel)
            .where(VariantPriceModel.variant_id == variant_id)
            .order_by(VariantPriceModel.created_at.desc())
        ).all()

    def activate_price(self, price_id: str) -> VariantPriceModel | None:
        model = self.get_by_id(price_id)
        if model is not None:
            model.is_active = True
            db.session.flush()
        return model

    def deactivate_price(self, price_id: str) -> VariantPriceModel | None:
        model = self.get_by_id(price_id)
        if model is not None:
            model.is_active = False
            db.session.flush()
        return model

    def deactivate_active_price(self, variant_id: str, *, exclude_price_id: str | None = None) -> None:
        active = self.get_active_price(variant_id)
        if active is not None and active.id != exclude_price_id:
            active.is_active = False
            db.session.flush()

    def exists(self, price_id: str) -> bool:
        return self.get_by_id(price_id) is not None
