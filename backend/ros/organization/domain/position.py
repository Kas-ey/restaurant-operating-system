"""Position domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Position:
    """Represents a reusable job title in the organization."""

    id: str
    name: str
    description: str
    is_active: bool = True

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Position ID is required.")
        self.name = self._normalize_required(self.name, "Position name is required.")
        self.description = self._normalize_required(self.description, "Position description is required.")

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def rename(self, name: str) -> None:
        self.name = self._normalize_required(name, "Position name is required.")

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required(description, "Position description is required.")

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        if not isinstance(value, str):
            raise ValueError(message)
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError(message)
        return normalized
