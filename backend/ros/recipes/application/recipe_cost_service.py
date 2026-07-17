"""Recipe cost calculation service (computed only, never persisted)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from http import HTTPStatus
from typing import Protocol

from ros.shared.exceptions import ROSException

from ..persistence.models import RecipeIngredientTypeEnum
from ..persistence.repositories import RecipeIngredientRepository, RecipeVersionRepository, SecretFormulationRepository


class InventoryCostProvider(Protocol):
    """Provides current inventory item costs from an external source."""

    def get_inventory_item_unit_cost(self, inventory_item_id: str) -> Decimal:
        """Return current unit cost for an inventory item."""


class SecretFormulationQuantityCostProvider(Protocol):
    """Provides cost for secret formulation quantity without exposing composition."""

    def get_secret_formulation_unit_cost(self, secret_formulation_id: str) -> Decimal:
        """Return effective unit cost for a secret formulation."""


@dataclass(slots=True)
class RecipeCostBreakdown:
    """Calculated recipe cost breakdown."""

    recipe_version_id: str
    total_cost: Decimal


class RecipeCostService:
    """Calculates recipe costs without persisting cost history."""

    def __init__(
        self,
        *,
        version_repository: RecipeVersionRepository | None = None,
        ingredient_repository: RecipeIngredientRepository | None = None,
        secret_formulation_repository: SecretFormulationRepository | None = None,
        inventory_cost_provider: InventoryCostProvider | None = None,
        secret_formulation_cost_provider: SecretFormulationQuantityCostProvider | None = None,
    ) -> None:
        self._version_repository = version_repository or RecipeVersionRepository()
        self._ingredient_repository = ingredient_repository or RecipeIngredientRepository()
        self._secret_formulation_repository = secret_formulation_repository or SecretFormulationRepository()
        self._inventory_cost_provider = inventory_cost_provider
        self._secret_formulation_cost_provider = secret_formulation_cost_provider

    def calculate_recipe_version_cost(self, recipe_version_id: str) -> RecipeCostBreakdown:
        total = self._calculate_version_cost(recipe_version_id.strip(), visited_versions=set())
        return RecipeCostBreakdown(recipe_version_id=recipe_version_id.strip(), total_cost=total)

    def _calculate_version_cost(self, recipe_version_id: str, *, visited_versions: set[str]) -> Decimal:
        if recipe_version_id in visited_versions:
            raise ROSException("Circular cost expansion detected.", HTTPStatus.CONFLICT)

        version = self._version_repository.get_by_id(recipe_version_id)
        if version is None:
            raise ROSException("Recipe version not found.", HTTPStatus.NOT_FOUND)

        visited_versions.add(recipe_version_id)
        try:
            ingredients = self._ingredient_repository.get_by_recipe_version(recipe_version_id)
            total = Decimal("0")
            for ingredient in ingredients:
                quantity = Decimal(str(ingredient.quantity))
                unit_cost = self._resolve_ingredient_unit_cost(ingredient, visited_versions=visited_versions)
                total += quantity * unit_cost
            return total
        finally:
            visited_versions.remove(recipe_version_id)

    def _resolve_ingredient_unit_cost(self, ingredient, *, visited_versions: set[str]) -> Decimal:
        ingredient_type = ingredient.ingredient_type

        if ingredient_type == RecipeIngredientTypeEnum.INVENTORY_ITEM:
            if self._inventory_cost_provider is None:
                raise ROSException("Inventory cost provider is not configured.", HTTPStatus.INTERNAL_SERVER_ERROR)
            return Decimal(str(self._inventory_cost_provider.get_inventory_item_unit_cost(ingredient.inventory_item_id)))

        if ingredient_type == RecipeIngredientTypeEnum.SECRET_FORMULATION:
            if self._secret_formulation_cost_provider is None:
                raise ROSException(
                    "Secret formulation cost provider is not configured.",
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            formulation = self._secret_formulation_repository.get_by_id(ingredient.secret_formulation_id)
            if formulation is None or not formulation.is_active:
                raise ROSException("Secret formulation reference not found.", HTTPStatus.NOT_FOUND)
            return Decimal(
                str(
                    self._secret_formulation_cost_provider.get_secret_formulation_unit_cost(
                        ingredient.secret_formulation_id
                    )
                )
            )

        sub_recipe_active_version = self._version_repository.get_active_version(ingredient.recipe_id)
        if sub_recipe_active_version is None:
            raise ROSException("Sub-recipe active version not found for cost expansion.", HTTPStatus.CONFLICT)

        sub_cost = self._calculate_version_cost(sub_recipe_active_version.id, visited_versions=visited_versions)
        sub_yield = Decimal("1")
        if sub_recipe_active_version.yield_spec is not None and sub_recipe_active_version.yield_spec.expected_quantity:
            sub_yield = Decimal(str(sub_recipe_active_version.yield_spec.expected_quantity))
            if sub_yield <= 0:
                sub_yield = Decimal("1")
        return sub_cost / sub_yield
