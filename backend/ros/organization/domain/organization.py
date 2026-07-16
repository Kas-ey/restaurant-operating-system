"""Organization domain entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Organization:
    """Represents a legal business organization operating restaurants."""

    id: str
    name: str
    legal_name: str
    registration_number: str
    tax_number: str
    email: str
    phone: str
    is_active: bool = True

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Organization ID is required.")
        self.name = self._normalize_required(self.name, "Organization name is required.")
        self.legal_name = self._normalize_required(self.legal_name, "Organization legal name is required.")
        self.registration_number = self._normalize_required(
            self.registration_number,
            "Organization registration number is required.",
        )
        self.tax_number = self._normalize_required(self.tax_number, "Organization tax number is required.")
        self.email = self._normalize_email(self.email)
        self.phone = self._normalize_required(self.phone, "Organization phone is required.")

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def rename(self, name: str, legal_name: str) -> None:
        self.name = self._normalize_required(name, "Organization name is required.")
        self.legal_name = self._normalize_required(legal_name, "Organization legal name is required.")

    def update_contact_information(self, email: str, phone: str) -> None:
        self.email = self._normalize_email(email)
        self.phone = self._normalize_required(phone, "Organization phone is required.")

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
        return cls._normalize_required(value, "Organization email is required.").lower()
