"""Shared service utilities for the Organization application layer."""

from __future__ import annotations

from http import HTTPStatus

from ros.shared.exceptions import ROSException


class BaseService:
    """Provides common input validation and normalization helpers."""

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @classmethod
    def _normalize_name(cls, value: str, message: str) -> str:
        return cls._require_text(value, message)

    @classmethod
    def _normalize_description(cls, value: str, message: str) -> str:
        return cls._require_text(value, message)

    @classmethod
    def _normalize_email(cls, value: str, message: str) -> str:
        return cls._require_text(value, message).lower()

    @classmethod
    def _normalize_phone(cls, value: str, message: str) -> str:
        return cls._require_text(value, message)

    @classmethod
    def _normalize_code(cls, value: str, message: str) -> str:
        return cls._require_text(value, message)
