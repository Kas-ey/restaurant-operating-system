"""Domain entity for a user in the Identity & Access business domain."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class User:
    """Represents a business user within the Identity & Access domain."""

    id: str
    email: str
    full_name: str
    roles: set["Role"] = field(default_factory=set)
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate the user entity invariants after initialization."""
        self._require_non_empty(self.id, "User ID cannot be empty.")
        self.email = self._normalize_email(self.email)
        self.full_name = self._normalize_full_name(self.full_name)

    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False

    def rename(self, full_name: str) -> None:
        """Rename the user with a validated full name."""
        self.full_name = self._normalize_full_name(full_name)

    def add_role(self, role: "Role") -> None:
        """Assign a role to the user."""
        if role is None:
            raise ValueError("Role cannot be None.")
        self.roles.add(role)

    def remove_role(self, role: "Role") -> None:
        """Remove a role from the user."""
        self.roles.discard(role)

    def has_role(self, role: "Role") -> bool:
        """Return whether the user has the specified role."""
        return role in self.roles

    @staticmethod
    def _normalize_spaces(value: str) -> str:
        """Collapse repeated whitespace characters to a single space."""
        return " ".join(value.split())

    @classmethod
    def _normalize_email(cls, value: str) -> str:
        normalized_email = value.strip().lower()
        cls._require_non_empty(normalized_email, "User email cannot be empty.")
        return normalized_email

    @classmethod
    def _normalize_full_name(cls, value: str) -> str:
        normalized_full_name = cls._normalize_spaces(value.strip())
        cls._require_non_empty(normalized_full_name, "User full name cannot be empty.")
        return normalized_full_name

    @staticmethod
    def _require_non_empty(value: str, message: str) -> None:
        if not value or not value.strip():
            raise ValueError(message)
