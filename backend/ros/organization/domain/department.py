"""Department domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Department:
    """Represents a functional department inside a branch."""

    id: str
    branch_id: str
    name: str
    description: str
    is_active: bool = True

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Department ID is required.")
        self.branch_id = self._normalize_required(self.branch_id, "Department branch ID is required.")
        self.name = self._normalize_required(self.name, "Department name is required.")
        self.description = self._normalize_required(self.description, "Department description is required.")

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def rename(self, name: str) -> None:
        self.name = self._normalize_required(name, "Department name is required.")

    def change_description(self, description: str) -> None:
        self.description = self._normalize_required(description, "Department description is required.")

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        if not isinstance(value, str):
            raise ValueError(message)
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError(message)
        return normalized
