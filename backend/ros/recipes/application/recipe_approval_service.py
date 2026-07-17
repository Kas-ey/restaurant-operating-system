"""Centralized recipe approval and activation workflows with immutable auditing."""

from __future__ import annotations

from datetime import UTC, datetime

from ..persistence.models import RecipeVersionModel
from .recipe_audit_service import RecipeAuditService
from .recipe_version_service import RecipeVersionService


class RecipeApprovalService:
    """Coordinates review/approval/publish/archive transitions and auditing."""

    def __init__(
        self,
        *,
        version_service: RecipeVersionService | None = None,
        audit_service: RecipeAuditService | None = None,
    ) -> None:
        self._version_service = version_service or RecipeVersionService()
        self._audit_service = audit_service or RecipeAuditService()

    def submit_for_review(self, version_id: str, *, requested_by: str, client_ip: str) -> RecipeVersionModel:
        version = self._version_service.submit_for_review(version_id, allow_review=True)
        self._audit_service.log_event(
            event_type="RECIPE_SUBMIT_REVIEW",
            outcome="SUCCESS",
            requested_by=requested_by,
            client_ip=client_ip,
            recipe_id=version.recipe_id,
            recipe_version_id=version.id,
            event_timestamp=datetime.now(tz=UTC),
        )
        return version

    def approve(self, version_id: str, *, approved_by: str, client_ip: str) -> RecipeVersionModel:
        version = self._version_service.approve(version_id, approved_by=approved_by, allow_approve=True)
        self._audit_service.log_event(
            event_type="RECIPE_APPROVE",
            outcome="SUCCESS",
            requested_by=approved_by,
            client_ip=client_ip,
            recipe_id=version.recipe_id,
            recipe_version_id=version.id,
            event_timestamp=datetime.now(tz=UTC),
        )
        return version

    def activate(self, version_id: str, *, requested_by: str, client_ip: str) -> RecipeVersionModel:
        version = self._version_service.activate(version_id, allow_publish=True)
        self._audit_service.log_event(
            event_type="RECIPE_ACTIVATE",
            outcome="SUCCESS",
            requested_by=requested_by,
            client_ip=client_ip,
            recipe_id=version.recipe_id,
            recipe_version_id=version.id,
            event_timestamp=datetime.now(tz=UTC),
        )
        return version

    def archive(self, version_id: str, *, requested_by: str, client_ip: str) -> RecipeVersionModel:
        version = self._version_service.archive(version_id)
        self._audit_service.log_event(
            event_type="RECIPE_ARCHIVE",
            outcome="SUCCESS",
            requested_by=requested_by,
            client_ip=client_ip,
            recipe_id=version.recipe_id,
            recipe_version_id=version.id,
            event_timestamp=datetime.now(tz=UTC),
        )
        return version
