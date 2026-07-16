"""Branch domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Branch:
    """Represents a physical operating branch of an organization."""

    id: str
    organization_id: str
    name: str
    code: str
    address: str
    city: str
    country: str
    phone: str
    email: str
    is_active: bool = True

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Branch ID is required.")
        self.organization_id = self._normalize_required(
            self.organization_id,
            "Branch organization ID is required.",
        )
        self.name = self._normalize_required(self.name, "Branch name is required.")
        self.code = self._normalize_required(self.code, "Branch code is required.")
        self.address = self._normalize_required(self.address, "Branch address is required.")
        self.city = self._normalize_required(self.city, "Branch city is required.")
        self.country = self._normalize_required(self.country, "Branch country is required.")
        self.phone = self._normalize_required(self.phone, "Branch phone is required.")
        self.email = self._normalize_email(self.email)

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def rename(self, name: str) -> None:
        self.name = self._normalize_required(name, "Branch name is required.")

    def relocate(self, address: str, city: str, country: str) -> None:
        self.address = self._normalize_required(address, "Branch address is required.")
        self.city = self._normalize_required(city, "Branch city is required.")
        self.country = self._normalize_required(country, "Branch country is required.")

    def update_contact_information(self, phone: str, email: str) -> None:
        self.phone = self._normalize_required(phone, "Branch phone is required.")
        self.email = self._normalize_email(email)

    @staticmethod
    def _normalize_required(value: str, message: str) -> str:
        if not isinstance(value, str):
            raise ValueError(message)
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError(message)
        return normalized

    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return cls._normalize_required(value, "Branch email is required.").lower()
