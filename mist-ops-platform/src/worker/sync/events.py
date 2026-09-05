"""Event sync — audit log events from Mist for actor attribution (T041).

Pulls audit events from the Mist API and records them as
``AuditRecord`` entries for change-attribution queries.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.shared.mist.endpoints import MistEndpointService
from src.shared.models.operations import AuditRecord

logger = logging.getLogger(__name__)


class EventSyncService:
    """Ingest audit events from Mist into the local audit table."""

    def __init__(
        self,
        db: Session,
        mist: MistEndpointService,
        org_id: str,
    ) -> None:
        self._db = db
        self._mist = mist
        self._org_id = org_id

    def sync_audit_events(self) -> int:
        """Fetch recent audit logs from Mist; return count stored."""
        events = self._fetch_events()
        for event in events:
            self._store_event(event)
        self._db.commit()
        return len(events)

    def _fetch_events(self) -> list[dict[str, Any]]:
        """Call Mist audit logs API."""
        result = self._mist.list_all_entities(
            "audit_log",
            ids={"org_id": str(self._org_id)},
        )
        return result.data if isinstance(result.data, list) else []

    def _store_event(self, event: dict[str, Any]) -> None:
        """Create an AuditRecord from a Mist audit log entry."""
        record = AuditRecord(
            org_id=UUID(self._org_id),
            actor=event.get("admin_name", "unknown"),
            change_type=event.get("message", "change")[:20],
            entity_type=self._infer_entity_type(event),
            entity_id=self._extract_entity_id(event),
            old_values=event.get("before"),
            new_values=event.get("after"),
            timestamp=datetime.now(UTC),
        )
        self._db.add(record)

    @staticmethod
    def _infer_entity_type(event: dict[str, Any]) -> str:
        """Best-effort entity type from audit log metadata."""
        obj_type = event.get("obj_type", "unknown")
        return str(obj_type)[:30]

    @staticmethod
    def _extract_entity_id(event: dict[str, Any]) -> UUID:
        """Return the entity UUID of the event, or a synthetic UUID.

        ``AuditRecord.entity_id`` links the audit row back to the object that
        changed. A synthetic value breaks that link, so every fallback path
        leaves a warning that states the reason.
        """
        raw = event.get("obj_id") or event.get("id")  # WHY: Mist sends either key.
        if not raw:
            # WHY: the row still stores, so the caller needs the reason in the log.
            return EventSyncService._synthetic_entity_id("the event carries no identifier")
        try:
            return UUID(str(raw))  # WHY: the normal path keeps the real link.
        except ValueError:
            # WHY: Mist also returns MAC style object identifiers, which are not UUIDs.
            return EventSyncService._synthetic_entity_id(f"the identifier {raw!r} is not a UUID")

    @staticmethod
    def _synthetic_entity_id(reason: str) -> UUID:
        """Return a fresh UUID and record why the real identifier is missing."""
        synthetic = uuid4()  # WHY: the audit column needs a value the database accepts.
        logger.warning(  # WHY: issue #1924 requires a record on every recovery path.
            "Audit row loses its link to the entity, because %s. Identifier %s is synthetic.",
            reason,
            synthetic,
        )
        return synthetic
