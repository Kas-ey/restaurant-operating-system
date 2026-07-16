"""Employee domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class Employee:
    """Represents a staff member within the organization structure."""

    id: str
    branch_id: str
    department_id: str
    position_id: str
    user_id: str | None
    employee_number: str
    first_name: str
    last_name: str
    phone: str
    email: str
    hire_date: date
    is_active: bool = True

    def __post_init__(self) -> None:
        self.id = self._normalize_required(self.id, "Employee ID is required.")
        self.branch_id = self._normalize_required(self.branch_id, "Employee branch ID is required.")
        self.department_id = self._normalize_required(
            self.department_id,
            "Employee department ID is required.",
        )
        self.position_id = self._normalize_required(self.position_id, "Employee position ID is required.")
        self.user_id = self._normalize_optional(self.user_id)
        self.employee_number = self._normalize_required(
            self.employee_number,
            "Employee number is required.",
        )
        self.first_name = self._normalize_required(self.first_name, "Employee first name is required.")
        self.last_name = self._normalize_required(self.last_name, "Employee last name is required.")
        self.phone = self._normalize_required(self.phone, "Employee phone is required.")
        self.email = self._normalize_email(self.email)
        if not isinstance(self.hire_date, date):
            raise ValueError("Employee hire date is required.")

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def rename(self, first_name: str, last_name: str) -> None:
        self.first_name = self._normalize_required(first_name, "Employee first name is required.")
        self.last_name = self._normalize_required(last_name, "Employee last name is required.")

    def assign_user(self, user_id: str) -> None:
        self.user_id = self._normalize_required(user_id, "Employee user ID is required.")

    def remove_user(self) -> None:
        self.user_id = None

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
        return cls._normalize_required(value, "Employee email is required.").lower()

    @classmethod
    def _normalize_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = cls._normalize_required(value, "Employee user ID is required.")
        return normalized
