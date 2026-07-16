"""Application service for position workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.organization.application.base import BaseService
from ros.organization.persistence.models import PositionModel
from ros.organization.persistence.repositories import EmployeeRepository, PositionRepository
from ros.shared.exceptions import ROSException


class PositionService(BaseService):
    """Coordinates position management workflows."""

    def __init__(
        self,
        position_repository: PositionRepository | None = None,
        employee_repository: EmployeeRepository | None = None,
    ) -> None:
        self._position_repository = position_repository or PositionRepository()
        self._employee_repository = employee_repository or EmployeeRepository()

    def create_position(self, position_id: str, name: str, description: str) -> PositionModel:
        normalized_id = self._require_text(position_id, "Position ID is required.")
        normalized_name = self._normalize_name(name, "Position name is required.")
        normalized_description = self._normalize_description(description, "Position description is required.")

        if self._position_repository.get_by_name(normalized_name) is not None:
            raise ROSException("Position already exists.", HTTPStatus.CONFLICT)

        model = PositionModel(
            id=normalized_id,
            name=normalized_name,
            description=normalized_description,
            is_active=True,
        )
        return self._position_repository.save(model)

    def update_position(
        self,
        position_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> PositionModel:
        model = self._get_existing_position(position_id)

        if name is not None:
            normalized_name = self._normalize_name(name, "Position name is required.")
            existing = self._position_repository.get_by_name(normalized_name)
            if existing is not None and existing.id != model.id:
                raise ROSException("Position already exists.", HTTPStatus.CONFLICT)
            model.name = normalized_name

        if description is not None:
            model.description = self._normalize_description(description, "Position description is required.")

        return self._position_repository.save(model)

    def activate_position(self, position_id: str) -> PositionModel:
        model = self._get_existing_position(position_id)
        model.is_active = True
        return self._position_repository.save(model)

    def deactivate_position(self, position_id: str) -> PositionModel:
        model = self._get_existing_position(position_id)
        model.is_active = False
        return self._position_repository.save(model)

    def get_position(self, position_id: str) -> PositionModel:
        return self._get_existing_position(position_id)

    def list_positions(self) -> list[PositionModel]:
        return self._position_repository.get_all()

    def delete_position(self, position_id: str) -> None:
        model = self._get_existing_position(position_id)
        if self._employee_repository.list_by_position(model.id):
            raise ROSException("Cannot delete position assigned to employees.", HTTPStatus.CONFLICT)
        self._position_repository.delete(model.id)

    def _get_existing_position(self, position_id: str) -> PositionModel:
        normalized_id = self._require_text(position_id, "Position ID is required.")
        model = self._position_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Position not found.", HTTPStatus.NOT_FOUND)
        return model
