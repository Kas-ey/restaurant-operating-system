"""Immutable recipes audit workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ..persistence.models import RecipeAuditEventModel
from ..persistence.repositories import RecipeAuditEventRepository


class RecipeAuditService:
    """Writes immutable recipe security and lifecycle audit events."""

    def __init__(self, repository: RecipeAuditEventRepository | None = None) -> None:
        self._repository = repository or RecipeAuditEventRepository()

    def log_event(
        self,
        *,
        event_type: str,
        outcome: str,
        requested_by: str,
        event_timestamp: datetime | None = None,
        client_ip: str | None = None,
        organization_id: str | None = None,
        branch_id: str | None = None,
        recipe_id: str | None = None,
        recipe_version_id: str | None = None,
        secret_formulation_id: str | None = None,
        reason: str | None = None,
        event_metadata: str | None = None,
    ) -> RecipeAuditEventModel:
        model = RecipeAuditEventModel(
            id=str(uuid4()),
            event_type=event_type.strip().upper(),
            outcome=outcome.strip().upper(),
            requested_by=requested_by.strip(),
            client_ip=(client_ip or "").strip() or None,
            organization_id=(organization_id or "").strip() or None,
            branch_id=(branch_id or "").strip() or None,
            recipe_id=(recipe_id or "").strip() or None,
            recipe_version_id=(recipe_version_id or "").strip() or None,
            secret_formulation_id=(secret_formulation_id or "").strip() or None,
            reason=(reason or "").strip() or None,
            event_metadata=(event_metadata or "").strip() or None,
            event_timestamp=event_timestamp or datetime.now(tz=UTC),
        )
        return self._repository.create(model)
