"""Application service for user-related identity workflows."""

from __future__ import annotations

from http import HTTPStatus

from ros.identity.application.base import BaseService
from ros.identity.auth.password import hash_password
from ros.identity.persistence.models import UserModel
from ros.identity.persistence.repositories import UserRepository
from ros.shared.exceptions import ROSException


class UserService(BaseService):
    """Coordinates user lifecycle workflows for the identity domain."""

    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self._user_repository = user_repository or UserRepository()

    def create_user(self, user_id: str, email: str, full_name: str, password: str) -> UserModel:
        """Create and persist a new user model."""
        normalized_id = self._require_text(user_id, "User ID is required.")
        normalized_email = self._normalize_email(email)
        normalized_name = self._normalize_full_name(full_name)
        normalized_password = self._require_text(password, "Password is required.")

        if self._user_repository.get_by_email(normalized_email) is not None:
            raise ROSException("User already exists.", HTTPStatus.CONFLICT)

        model = UserModel(
            id=normalized_id,
            email=normalized_email,
            full_name=normalized_name,
            password_hash=hash_password(normalized_password),
            is_active=True,
        )
        self._user_repository.save(model)
        return model

    def update_user(
        self,
        user_id: str,
        *,
        email: str | None = None,
        full_name: str | None = None,
        password: str | None = None,
    ) -> UserModel:
        """Update mutable user fields and persist the changes."""
        model = self._get_existing_user(user_id)

        if email is not None:
            normalized_email = self._normalize_email(email)
            existing = self._user_repository.get_by_email(normalized_email)
            if existing is not None and existing.id != model.id:
                raise ROSException("User already exists.", HTTPStatus.CONFLICT)
            model.email = normalized_email

        if full_name is not None:
            model.full_name = self._normalize_full_name(full_name)

        if password is not None:
            model.password_hash = hash_password(self._require_text(password, "Password is required."))

        self._user_repository.save(model)
        return model

    def activate_user(self, user_id: str) -> UserModel:
        """Activate an existing user account."""
        model = self._get_existing_user(user_id)
        model.is_active = True
        self._user_repository.save(model)
        return model

    def deactivate_user(self, user_id: str) -> UserModel:
        """Deactivate an existing user account."""
        model = self._get_existing_user(user_id)
        model.is_active = False
        self._user_repository.save(model)
        return model

    def get_user(self, user_id: str) -> UserModel:
        """Return a user by identifier."""
        return self._get_existing_user(user_id)

    def list_users(self) -> list[UserModel]:
        """Return all persisted users."""
        return self._user_repository.get_all()

    def delete_user(self, user_id: str) -> None:
        """Delete a user permanently by identifier."""
        self._get_existing_user(user_id)
        self._user_repository.delete(user_id)

    def _get_existing_user(self, user_id: str) -> UserModel:
        normalized_id = self._require_text(user_id, "User ID is required.")
        model = self._user_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("User not found.", HTTPStatus.NOT_FOUND)
        return model

    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return cls._require_text(value, "Email is required.").lower()

    @classmethod
    def _normalize_full_name(cls, value: str) -> str:
        normalized = cls._require_text(value, "Full name is required.")
        return " ".join(normalized.split())
