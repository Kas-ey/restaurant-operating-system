"""Domain entities for the Recipes module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum

from .exceptions import RecipeDomainError, RecipeVersionDomainError


class RecipeSecurityClassification(str, Enum):
    """Security classification levels for recipes."""

    PUBLIC = "PUBLIC"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    SECRET = "SECRET"


class RecipeVersionStatus(str, Enum):
    """Recipe version lifecycle statuses."""

    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(slots=True)
class Recipe:
    """Business entity representing a manufacturing recipe."""

    id: str
    product_id: str
    code: str
    name: str
    description: str
    security_classification: RecipeSecurityClassification
    created_by: str
    current_version_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._require_text(self.id, "Recipe ID is required.")
        self.product_id = self._require_text(self.product_id, "Product ID is required.")
        self.code = self._require_text(self.code, "Recipe code is required.")
        self.name = self._require_text(self.name, "Recipe name is required.")
        self.description = self._require_text(self.description, "Recipe description is required.")
        self.security_classification = self._normalize_security_classification(self.security_classification)
        self.created_by = self._require_text(self.created_by, "Created by is required.")
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or now

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise RecipeDomainError(message)
        return normalized

    @staticmethod
    def _normalize_security_classification(
        value: RecipeSecurityClassification | str,
    ) -> RecipeSecurityClassification:
        if isinstance(value, RecipeSecurityClassification):
            return value
        try:
            return RecipeSecurityClassification(str(value))
        except ValueError as exc:
            raise RecipeDomainError("Invalid recipe security classification.") from exc


@dataclass(slots=True)
class RecipeVersion:
    """Business entity representing a versioned manufacturing recipe."""

    id: str
    recipe_id: str
    version_number: int
    status: RecipeVersionStatus
    change_summary: str
    effective_date: date | None
    created_by: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        self.id = self._require_text(self.id, "Recipe version ID is required.")
        self.recipe_id = self._require_text(self.recipe_id, "Recipe ID is required.")
        self.version_number = self._normalize_version_number(self.version_number)
        self.status = self._normalize_status(self.status)
        self.change_summary = self._require_text(self.change_summary, "Change summary is required.")
        self.created_by = self._require_text(self.created_by, "Created by is required.")
        now = datetime.now(tz=UTC)
        self.created_at = self.created_at or now

    def can_transition_to(self, target_status: RecipeVersionStatus) -> bool:
        transitions = {
            RecipeVersionStatus.DRAFT: {RecipeVersionStatus.UNDER_REVIEW},
            RecipeVersionStatus.UNDER_REVIEW: {RecipeVersionStatus.APPROVED},
            RecipeVersionStatus.APPROVED: {RecipeVersionStatus.ACTIVE},
            RecipeVersionStatus.ACTIVE: {RecipeVersionStatus.ARCHIVED},
            RecipeVersionStatus.ARCHIVED: set(),
        }
        return target_status in transitions[self.status]

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise RecipeVersionDomainError(message)
        return normalized

    @staticmethod
    def _normalize_version_number(value: int) -> int:
        if not isinstance(value, int) or value <= 0:
            raise RecipeVersionDomainError("Version number must be a positive integer.")
        return value

    @staticmethod
    def _normalize_status(value: RecipeVersionStatus | str) -> RecipeVersionStatus:
        if isinstance(value, RecipeVersionStatus):
            return value
        try:
            return RecipeVersionStatus(str(value))
        except ValueError as exc:
            raise RecipeVersionDomainError("Invalid recipe version status.") from exc
