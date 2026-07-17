"""Modifier option aggregate application service workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.products.persistence.models import ModifierGroupModel, ModifierOptionModel
from ros.products.persistence.repositories import ModifierGroupRepository, ModifierOptionRepository
from ros.shared.exceptions import ROSException


class ModifierOptionService:
    """Coordinates modifier option workflows."""

    def __init__(
        self,
        option_repository: ModifierOptionRepository | None = None,
        group_repository: ModifierGroupRepository | None = None,
    ) -> None:
        self._option_repository = option_repository or ModifierOptionRepository()
        self._group_repository = group_repository or ModifierGroupRepository()

    def create_option(
        self,
        *,
        option_id: str,
        modifier_group_id: str,
        name: str,
        description: str,
        display_order: int,
        is_default: bool,
    ) -> ModifierOptionModel:
        group = self._get_active_group(modifier_group_id)
        normalized_option_id = self._require_text(option_id, "Modifier option ID is required.")
        normalized_name = self._require_text(name, "Modifier option name is required.")
        normalized_description = self._require_text(description, "Modifier option description is required.")
        normalized_display_order = self._require_non_negative_int(display_order, "Display order must be zero or greater.")

        existing = self._option_repository.get_by_name(group.id, normalized_name)
        if existing is not None:
            raise ROSException("Modifier option already exists.", HTTPStatus.CONFLICT)

        model = ModifierOptionModel(
            id=normalized_option_id,
            modifier_group_id=group.id,
            name=normalized_name,
            description=normalized_description,
            display_order=normalized_display_order,
            is_default=bool(is_default),
            is_active=True,
        )
        return self._option_repository.create(model)

    def update_option(
        self,
        option_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        display_order: int | None = None,
        is_default: bool | None = None,
    ) -> ModifierOptionModel:
        model = self._get_existing_option(option_id)

        if name is not None:
            normalized_name = self._require_text(name, "Modifier option name is required.")
            existing = self._option_repository.get_by_name(model.modifier_group_id, normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Modifier option already exists.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if description is not None:
            model.description = self._require_text(description, "Modifier option description is required.")

        if display_order is not None:
            model.display_order = self._require_non_negative_int(display_order, "Display order must be zero or greater.")

        if is_default is not None:
            model.is_default = bool(is_default)

        return self._option_repository.update(model)

    def delete_option(self, option_id: str) -> None:
        model = self._get_existing_option(option_id)
        self._option_repository.delete(model.id)

    def activate_option(self, option_id: str) -> ModifierOptionModel:
        model = self._get_existing_option(option_id)
        model.is_active = True
        return self._option_repository.update(model)

    def deactivate_option(self, option_id: str) -> ModifierOptionModel:
        model = self._get_existing_option(option_id)
        model.is_active = False
        return self._option_repository.update(model)

    def get_option(self, option_id: str) -> ModifierOptionModel:
        return self._get_existing_option(option_id)

    def list_options(self, modifier_group_id: str) -> list[ModifierOptionModel]:
        group = self._get_existing_group(modifier_group_id)
        return self._option_repository.get_by_group(group.id)

    def _get_existing_group(self, modifier_group_id: str) -> ModifierGroupModel:
        normalized_id = self._require_text(modifier_group_id, "Modifier group ID is required.")
        group = self._group_repository.get_by_id(normalized_id)
        if group is None:
            raise ROSException("Modifier group not found.", HTTPStatus.NOT_FOUND)
        return group

    def _get_active_group(self, modifier_group_id: str) -> ModifierGroupModel:
        group = self._get_existing_group(modifier_group_id)
        if not group.is_active:
            raise ROSException("Modifier group is inactive.", HTTPStatus.CONFLICT)
        return group

    def _get_existing_option(self, option_id: str) -> ModifierOptionModel:
        normalized_id = self._require_text(option_id, "Modifier option ID is required.")
        option = self._option_repository.get_by_id(normalized_id)
        if option is None:
            raise ROSException("Modifier option not found.", HTTPStatus.NOT_FOUND)
        return option

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
