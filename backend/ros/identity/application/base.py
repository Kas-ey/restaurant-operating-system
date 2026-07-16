"""Shared service utilities for the identity application layer."""

from __future__ import annotations

from http import HTTPStatus

from ros.shared.exceptions import ROSException


class BaseService:
    """Provides common input normalization and validation helpers."""

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @classmethod
    def _normalize_spaces(cls, value: str, message: str) -> str:
        normalized = cls._require_text(value, message)
        return " ".join(normalized.split())

    @classmethod
    def _normalize_description(cls, value: str, message: str) -> str:
        return cls._normalize_spaces(value, message)
