"""Domain entity for a user in the Identity & Access business domain."""

from dataclasses import dataclass


@dataclass
class User:
    """Represents a business user within the Identity & Access domain."""

    id: str
    email: str
    full_name: str
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate the user entity invariants after initialization."""
        self.email = self.email.strip().lower()
        self.full_name = self.full_name.strip()

        if not self.id or not self.id.strip():
            raise ValueError("id must not be empty")

        if not self.email:
            raise ValueError("email must not be empty")

        if not self.full_name:
            raise ValueError("full_name must not be empty")

    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False

    def rename(self, full_name: str) -> None:
        """Rename the user with a validated full name."""
        normalized_name = full_name.strip()
        if not normalized_name:
            raise ValueError("full_name must not be empty")
        self.full_name = normalized_name
