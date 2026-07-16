"""Domain entity for a permission in the Identity & Access business domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Permission:
    """Represents a business permission within the Identity & Access domain."""

    id: str
    name: str
    description: str
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate the permission entity invariants after initialization."""
        self._require_non_empty(self.id, "Permission ID cannot be empty.")
        self.name = self._normalize_permission_name(self.name)
        self.description = self._normalize_permission_description(self.description)

    def activate(self) -> None:
        """Activate the permission."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the permission."""
        self.is_active = False

    def rename(self, name: str) -> None:
        """Rename the permission with a validated name."""
        self.name = self._normalize_permission_name(name)

    def change_description(self, description: str) -> None:
        """Change the permission description with a validated description."""
        self.description = self._normalize_permission_description(description)

    @staticmethod
    def _normalize_name(value: str) -> str:
        """Normalize the permission name to lowercase dot notation."""
        collapsed = " ".join(value.lower().split())
        return collapsed.replace(" ", ".")

    @classmethod
    def _normalize_permission_name(cls, value: str) -> str:
        normalized_name = cls._normalize_name(value.strip())
        cls._require_non_empty(normalized_name, "Permission name cannot be empty.")
        return normalized_name

    @classmethod
    def _normalize_permission_description(cls, value: str) -> str:
        normalized_description = value.strip()
        cls._require_non_empty(normalized_description, "Permission description cannot be empty.")
        return normalized_description

    @staticmethod
    def _require_non_empty(value: str, message: str) -> None:
        if not value or not value.strip():
            raise ValueError(message)
