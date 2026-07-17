"""Modifier group aggregate application service workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.products.persistence.models import ModifierGroupModel, ModifierSelectionTypeEnum, ProductModel
from ros.products.persistence.repositories import ModifierGroupRepository, ProductRepository
from ros.shared.exceptions import ROSException


class ModifierGroupService:
    """Coordinates modifier group workflows."""

    def __init__(
        self,
        group_repository: ModifierGroupRepository | None = None,
        product_repository: ProductRepository | None = None,
    ) -> None:
        self._group_repository = group_repository or ModifierGroupRepository()
        self._product_repository = product_repository or ProductRepository()

    def create_group(
        self,
        *,
        group_id: str,
        product_id: str,
        name: str,
        description: str,
        selection_type: str,
        minimum_required: int,
        maximum_allowed: int,
        display_order: int,
        is_required: bool,
    ) -> ModifierGroupModel:
        product = self._get_active_product(product_id)
        normalized_group_id = self._require_text(group_id, "Modifier group ID is required.")
        normalized_name = self._require_text(name, "Modifier group name is required.")
        normalized_description = self._require_text(description, "Modifier group description is required.")
        normalized_selection_type = self._normalize_selection_type(selection_type)
        normalized_minimum_required = self._require_non_negative_int(
            minimum_required,
            "Minimum required must be zero or greater.",
        )
        normalized_maximum_allowed = self._require_non_negative_int(
            maximum_allowed,
            "Maximum allowed must be zero or greater.",
        )
        normalized_display_order = self._require_non_negative_int(display_order, "Display order must be zero or greater.")

        self._validate_selection_rules(
            selection_type=normalized_selection_type,
            minimum_required=normalized_minimum_required,
            maximum_allowed=normalized_maximum_allowed,
            is_required=bool(is_required),
        )

        existing = self._group_repository.get_by_name(product.id, normalized_name)
        if existing is not None:
            raise ROSException("Modifier group already exists.", HTTPStatus.CONFLICT)

        model = ModifierGroupModel(
            id=normalized_group_id,
            product_id=product.id,
            name=normalized_name,
            description=normalized_description,
            selection_type=normalized_selection_type,
            minimum_required=normalized_minimum_required,
            maximum_allowed=normalized_maximum_allowed,
            display_order=normalized_display_order,
            is_required=bool(is_required),
            is_active=True,
        )
        return self._group_repository.create(model)

    def update_group(
        self,
        group_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        selection_type: str | None = None,
        minimum_required: int | None = None,
        maximum_allowed: int | None = None,
        display_order: int | None = None,
        is_required: bool | None = None,
    ) -> ModifierGroupModel:
        model = self._get_existing_group(group_id)

        if name is not None:
            normalized_name = self._require_text(name, "Modifier group name is required.")
            existing = self._group_repository.get_by_name(model.product_id, normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Modifier group already exists.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if description is not None:
            model.description = self._require_text(description, "Modifier group description is required.")

        if selection_type is not None:
            model.selection_type = self._normalize_selection_type(selection_type)

        if minimum_required is not None:
            model.minimum_required = self._require_non_negative_int(minimum_required, "Minimum required must be zero or greater.")

        if maximum_allowed is not None:
            model.maximum_allowed = self._require_non_negative_int(maximum_allowed, "Maximum allowed must be zero or greater.")

        if display_order is not None:
            model.display_order = self._require_non_negative_int(display_order, "Display order must be zero or greater.")

        if is_required is not None:
            model.is_required = bool(is_required)

        self._validate_selection_rules(
            selection_type=model.selection_type,
            minimum_required=model.minimum_required,
            maximum_allowed=model.maximum_allowed,
            is_required=model.is_required,
        )
        return self._group_repository.update(model)

    def delete_group(self, group_id: str) -> None:
        model = self._get_existing_group(group_id)
        self._group_repository.delete(model.id)

    def activate_group(self, group_id: str) -> ModifierGroupModel:
        model = self._get_existing_group(group_id)
        model.is_active = True
        return self._group_repository.update(model)

    def deactivate_group(self, group_id: str) -> ModifierGroupModel:
        model = self._get_existing_group(group_id)
        model.is_active = False
        return self._group_repository.update(model)

    def get_group(self, group_id: str) -> ModifierGroupModel:
        return self._get_existing_group(group_id)

    def list_groups(self, product_id: str) -> list[ModifierGroupModel]:
        product = self._get_existing_product(product_id)
        return self._group_repository.get_by_product(product.id)

    def _get_existing_product(self, product_id: str) -> ProductModel:
        normalized_id = self._require_text(product_id, "Product ID is required.")
        product = self._product_repository.get_by_id(normalized_id)
        if product is None:
            raise ROSException("Product not found.", HTTPStatus.NOT_FOUND)
        return product

    def _get_active_product(self, product_id: str) -> ProductModel:
        product = self._get_existing_product(product_id)
        if not product.is_active:
            raise ROSException("Product is inactive.", HTTPStatus.CONFLICT)
        return product

    def _get_existing_group(self, group_id: str) -> ModifierGroupModel:
        normalized_id = self._require_text(group_id, "Modifier group ID is required.")
        group = self._group_repository.get_by_id(normalized_id)
        if group is None:
            raise ROSException("Modifier group not found.", HTTPStatus.NOT_FOUND)
        return group

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _require_non_negative_int(value: int, message: str) -> int:
        if not isinstance(value, int) or value < 0:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return value

    @staticmethod
    def _normalize_selection_type(value: str | ModifierSelectionTypeEnum) -> ModifierSelectionTypeEnum:
        if isinstance(value, ModifierSelectionTypeEnum):
            return value
        try:
            return ModifierSelectionTypeEnum(str(value))
        except ValueError as exc:
            raise ROSException("Invalid selection type.", HTTPStatus.BAD_REQUEST) from exc

    @staticmethod
    def _validate_selection_rules(
        *,
        selection_type: ModifierSelectionTypeEnum,
        minimum_required: int,
        maximum_allowed: int,
        is_required: bool,
    ) -> None:
        if maximum_allowed < minimum_required:
            raise ROSException("Maximum allowed must be greater than or equal to minimum required.", HTTPStatus.BAD_REQUEST)
        if is_required and minimum_required < 1:
            raise ROSException("Required modifier group must have minimum required of at least one.", HTTPStatus.BAD_REQUEST)
        if selection_type == ModifierSelectionTypeEnum.SINGLE and maximum_allowed > 1:
            raise ROSException("SINGLE selection type cannot allow more than one selection.", HTTPStatus.BAD_REQUEST)
