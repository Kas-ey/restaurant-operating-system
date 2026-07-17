"""Application service for recipe ingredient workflows."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

from ros.inventory.persistence.repositories import InventoryItemRepository, UnitRepository
from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeIngredientModel, RecipeIngredientTypeEnum, RecipeVersionStatusEnum
from ..persistence.repositories import (
    RecipeIngredientRepository,
    RecipeRepository,
    RecipeVersionRepository,
    SecretFormulationRepository,
)


class RecipeIngredientService:
    """Encapsulates recipe ingredient business validation and workflows."""

    def __init__(
        self,
        *,
        ingredient_repository: RecipeIngredientRepository | None = None,
        version_repository: RecipeVersionRepository | None = None,
        recipe_repository: RecipeRepository | None = None,
        secret_formulation_repository: SecretFormulationRepository | None = None,
        inventory_item_repository: InventoryItemRepository | None = None,
        unit_repository: UnitRepository | None = None,
        max_sub_recipe_depth: int = 5,
    ) -> None:
        self._ingredient_repository = ingredient_repository or RecipeIngredientRepository()
        self._version_repository = version_repository or RecipeVersionRepository()
        self._recipe_repository = recipe_repository or RecipeRepository()
        self._secret_formulation_repository = secret_formulation_repository or SecretFormulationRepository()
        self._inventory_item_repository = inventory_item_repository or InventoryItemRepository()
        self._unit_repository = unit_repository or UnitRepository()
        self._max_sub_recipe_depth = max_sub_recipe_depth

    def list_ingredients(self, recipe_version_id: str) -> list[RecipeIngredientModel]:
        self._get_version(recipe_version_id)
        return self._ingredient_repository.get_by_recipe_version(recipe_version_id)

    def add_ingredient(
        self,
        *,
        ingredient_id: str,
        recipe_version_id: str,
        ingredient_type: str,
        inventory_item_id: str | None,
        recipe_id: str | None,
        secret_formulation_id: str | None,
        quantity,
        unit_of_measure_id: str,
        tolerance,
        display_order: int,
        notes: str | None,
    ) -> RecipeIngredientModel:
        version = self._get_draft_version(recipe_version_id)
        normalized_type = self._parse_ingredient_type(ingredient_type)
        refs = self._normalize_references(inventory_item_id, recipe_id, secret_formulation_id)
        self._validate_single_reference(normalized_type, refs)
        self._validate_unit(unit_of_measure_id)

        quantity_value = self._parse_positive_decimal(quantity, "quantity")
        tolerance_value = self._parse_non_negative_decimal(tolerance, "tolerance")
        if not isinstance(display_order, int) or display_order < 0:
            raise ROSException("Display order must be a non-negative integer.", HTTPStatus.BAD_REQUEST)

        self._validate_reference_integrity(version.recipe_id, normalized_type, refs)

        model = RecipeIngredientModel(
            id=ingredient_id.strip(),
            recipe_version_id=recipe_version_id,
            ingredient_type=normalized_type,
            inventory_item_id=refs["inventory_item_id"],
            recipe_id=refs["recipe_id"],
            secret_formulation_id=refs["secret_formulation_id"],
            quantity=quantity_value,
            unit_of_measure_id=unit_of_measure_id.strip(),
            tolerance=tolerance_value,
            display_order=display_order,
            notes=notes.strip() if isinstance(notes, str) and notes.strip() else None,
        )
        return self._ingredient_repository.create(model)

    def update_ingredient(
        self,
        ingredient_id: str,
        *,
        recipe_version_id: str,
        ingredient_type: str,
        inventory_item_id: str | None,
        recipe_id: str | None,
        secret_formulation_id: str | None,
        quantity,
        unit_of_measure_id: str,
        tolerance,
        display_order: int,
        notes: str | None,
    ) -> RecipeIngredientModel:
        ingredient = self._get_ingredient(ingredient_id)
        if ingredient.recipe_version_id != recipe_version_id:
            raise ROSException("Recipe ingredient not found.", HTTPStatus.NOT_FOUND)
        version = self._get_draft_version(ingredient.recipe_version_id)

        normalized_type = self._parse_ingredient_type(ingredient_type)
        refs = self._normalize_references(inventory_item_id, recipe_id, secret_formulation_id)
        self._validate_single_reference(normalized_type, refs)
        self._validate_unit(unit_of_measure_id)

        quantity_value = self._parse_positive_decimal(quantity, "quantity")
        tolerance_value = self._parse_non_negative_decimal(tolerance, "tolerance")
        if not isinstance(display_order, int) or display_order < 0:
            raise ROSException("Display order must be a non-negative integer.", HTTPStatus.BAD_REQUEST)

        self._validate_reference_integrity(version.recipe_id, normalized_type, refs)

        ingredient.ingredient_type = normalized_type
        ingredient.inventory_item_id = refs["inventory_item_id"]
        ingredient.recipe_id = refs["recipe_id"]
        ingredient.secret_formulation_id = refs["secret_formulation_id"]
        ingredient.quantity = quantity_value
        ingredient.unit_of_measure_id = unit_of_measure_id.strip()
        ingredient.tolerance = tolerance_value
        ingredient.display_order = display_order
        ingredient.notes = notes.strip() if isinstance(notes, str) and notes.strip() else None
        return self._ingredient_repository.update(ingredient)

    def remove_ingredient(self, ingredient_id: str, *, recipe_version_id: str) -> None:
        ingredient = self._get_ingredient(ingredient_id)
        if ingredient.recipe_version_id != recipe_version_id:
            raise ROSException("Recipe ingredient not found.", HTTPStatus.NOT_FOUND)
        self._get_draft_version(ingredient.recipe_version_id)
        self._ingredient_repository.delete(ingredient_id)

    def _validate_reference_integrity(self, owner_recipe_id: str, ingredient_type: RecipeIngredientTypeEnum, refs: dict[str, str | None]) -> None:
        if ingredient_type == RecipeIngredientTypeEnum.INVENTORY_ITEM:
            item = self._inventory_item_repository.get_by_id(refs["inventory_item_id"] or "")
            if item is None:
                raise ROSException("Inventory item reference not found.", HTTPStatus.NOT_FOUND)
            if not item.is_active:
                raise ROSException("Inactive inventory items cannot be referenced.", HTTPStatus.CONFLICT)
            return

        if ingredient_type == RecipeIngredientTypeEnum.SECRET_FORMULATION:
            formulation = self._secret_formulation_repository.get_by_id(refs["secret_formulation_id"] or "")
            if formulation is None:
                raise ROSException("Secret formulation reference not found.", HTTPStatus.NOT_FOUND)
            if not formulation.is_active:
                raise ROSException("Inactive secret formulations cannot be referenced.", HTTPStatus.CONFLICT)
            return

        sub_recipe_id = refs["recipe_id"] or ""
        sub_recipe = self._recipe_repository.get_by_id(sub_recipe_id)
        if sub_recipe is None:
            raise ROSException("Sub-recipe reference not found.", HTTPStatus.NOT_FOUND)
        if not sub_recipe.is_active:
            raise ROSException("Inactive recipes cannot be referenced.", HTTPStatus.CONFLICT)

        sub_recipe_active_version = self._version_repository.get_active_version(sub_recipe.id)
        if sub_recipe_active_version is None:
            raise ROSException("Only recipes with an ACTIVE version may be referenced.", HTTPStatus.CONFLICT)

        self._assert_no_circular_reference(owner_recipe_id=owner_recipe_id, target_recipe_id=sub_recipe.id)

    def _assert_no_circular_reference(self, *, owner_recipe_id: str, target_recipe_id: str) -> None:
        if owner_recipe_id == target_recipe_id:
            raise ROSException("Circular sub-recipe reference detected.", HTTPStatus.CONFLICT)
        self._walk_sub_recipe_tree(owner_recipe_id, target_recipe_id, depth=1, visited={target_recipe_id})

    def _walk_sub_recipe_tree(self, owner_recipe_id: str, current_recipe_id: str, *, depth: int, visited: set[str]) -> None:
        if depth > self._max_sub_recipe_depth:
            raise ROSException("Sub-recipe recursion depth exceeded.", HTTPStatus.CONFLICT)

        active_version = self._version_repository.get_active_version(current_recipe_id)
        if active_version is None:
            return

        ingredients = self._ingredient_repository.get_by_recipe_version(active_version.id)
        for ingredient in ingredients:
            if ingredient.ingredient_type != RecipeIngredientTypeEnum.SUB_RECIPE or not ingredient.recipe_id:
                continue
            if ingredient.recipe_id == owner_recipe_id:
                raise ROSException("Circular sub-recipe reference detected.", HTTPStatus.CONFLICT)
            if ingredient.recipe_id in visited:
                continue
            visited.add(ingredient.recipe_id)
            self._walk_sub_recipe_tree(owner_recipe_id, ingredient.recipe_id, depth=depth + 1, visited=visited)

    def _validate_unit(self, unit_of_measure_id: str) -> None:
        unit = self._unit_repository.get_by_id(unit_of_measure_id.strip())
        if unit is None:
            raise ROSException("Unit of measure not found.", HTTPStatus.NOT_FOUND)
        if not unit.is_active:
            raise ROSException("Inactive units of measure cannot be referenced.", HTTPStatus.CONFLICT)

    def _get_version(self, recipe_version_id: str):
        version = self._version_repository.get_by_id(recipe_version_id)
        if version is None:
            raise ROSException("Recipe version not found.", HTTPStatus.NOT_FOUND)
        return version

    def _get_draft_version(self, recipe_version_id: str):
        version = self._get_version(recipe_version_id)
        if version.status != RecipeVersionStatusEnum.DRAFT:
            raise ROSException("Ingredients can only be modified for DRAFT recipe versions.", HTTPStatus.CONFLICT)
        return version

    def _get_ingredient(self, ingredient_id: str) -> RecipeIngredientModel:
        ingredient = self._ingredient_repository.get_by_id(ingredient_id)
        if ingredient is None:
            raise ROSException("Recipe ingredient not found.", HTTPStatus.NOT_FOUND)
        return ingredient

    @staticmethod
    def _normalize_references(
        inventory_item_id: str | None,
        recipe_id: str | None,
        secret_formulation_id: str | None,
    ) -> dict[str, str | None]:
        return {
            "inventory_item_id": inventory_item_id.strip() if isinstance(inventory_item_id, str) and inventory_item_id.strip() else None,
            "recipe_id": recipe_id.strip() if isinstance(recipe_id, str) and recipe_id.strip() else None,
            "secret_formulation_id": (
                secret_formulation_id.strip()
                if isinstance(secret_formulation_id, str) and secret_formulation_id.strip()
                else None
            ),
        }

    @staticmethod
    def _parse_ingredient_type(value: str) -> RecipeIngredientTypeEnum:
        try:
            return RecipeIngredientTypeEnum(value.strip().upper())
        except ValueError as exc:
            raise ROSException("Invalid ingredient type.", HTTPStatus.BAD_REQUEST) from exc

    @staticmethod
    def _validate_single_reference(ingredient_type: RecipeIngredientTypeEnum, refs: dict[str, str | None]) -> None:
        populated = [name for name, value in refs.items() if value]
        if len(populated) != 1:
            raise ROSException("Exactly one ingredient reference must be provided.", HTTPStatus.BAD_REQUEST)

        type_to_field = {
            RecipeIngredientTypeEnum.INVENTORY_ITEM: "inventory_item_id",
            RecipeIngredientTypeEnum.SUB_RECIPE: "recipe_id",
            RecipeIngredientTypeEnum.SECRET_FORMULATION: "secret_formulation_id",
        }
        expected_field = type_to_field[ingredient_type]
        if populated[0] != expected_field:
            raise ROSException("Ingredient type does not match the provided reference.", HTTPStatus.BAD_REQUEST)

    @staticmethod
    def _parse_positive_decimal(value, field_name: str) -> Decimal:
        decimal_value = RecipeIngredientService._to_decimal(value, field_name)
        if decimal_value <= 0:
            raise ROSException(f"Field '{field_name}' must be greater than zero.", HTTPStatus.BAD_REQUEST)
        return decimal_value

    @staticmethod
    def _parse_non_negative_decimal(value, field_name: str) -> Decimal:
        decimal_value = RecipeIngredientService._to_decimal(value, field_name)
        if decimal_value < 0:
            raise ROSException(f"Field '{field_name}' cannot be negative.", HTTPStatus.BAD_REQUEST)
        return decimal_value

    @staticmethod
    def _to_decimal(value, field_name: str) -> Decimal:
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError) as exc:
            raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST) from exc
        if not parsed.is_finite():
            raise ROSException(f"Field '{field_name}' must be a decimal number.", HTTPStatus.BAD_REQUEST)
        return parsed
