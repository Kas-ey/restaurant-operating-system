"""Domain entity for a role in the Identity & Access business domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .permission import Permission


@dataclass(slots=True)
class Role:
    """Represents a business role within the Identity & Access domain."""

    id: str
    name: str
    description: str
    permissions: set["Permission"] = field(default_factory=set)
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate the role entity invariants after initialization."""
        self._require_non_empty(self.id, "Role ID cannot be empty.")
        self.name = self._normalize_role_name(self.name)
        self.description = self._normalize_role_description(self.description)

    def activate(self) -> None:
        """Activate the role."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the role."""
        self.is_active = False

    def rename(self, name: str) -> None:
        """Rename the role with a validated name."""
        self.name = self._normalize_role_name(name)

    def change_description(self, description: str) -> None:
        """Change the role description with a validated description."""
        self.description = self._normalize_role_description(description)

    def add_permission(self, permission: "Permission") -> None:
        """Attach a permission to the role."""
        if permission is None:
            raise ValueError("Permission cannot be None.")
        self.permissions.add(permission)

    def remove_permission(self, permission: "Permission") -> None:
        """Remove a permission from the role."""
        self.permissions.discard(permission)

    def has_permission(self, permission: "Permission") -> bool:
        """Return whether the role contains the specified permission."""
        return permission in self.permissions

    @staticmethod
    def _normalize_spaces(value: str) -> str:
        """Collapse repeated whitespace characters to a single space."""
        return " ".join(value.split())

    @classmethod
    def _normalize_role_name(cls, value: str) -> str:
        normalized_name = cls._normalize_spaces(value.strip())
        cls._require_non_empty(normalized_name, "Role name cannot be empty.")
        return normalized_name

    @classmethod
    def _normalize_role_description(cls, value: str) -> str:
        normalized_description = value.strip()
        cls._require_non_empty(normalized_description, "Role description cannot be empty.")
        return normalized_description

    @staticmethod
    def _require_non_empty(value: str, message: str) -> None:
        if not value or not value.strip():
            raise ValueError(message)
