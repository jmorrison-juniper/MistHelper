"""Incident-change correlation logic (T071).

Identifies temporal and scope-based correlations between
network incidents (alarms, SLE degradations) and recent
config changes. SC-016 requires <2min processing.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.models.governance import IncidentChangeCorrelation
from src.shared.models.operations import AuditRecord

logger = logging.getLogger(__name__)

# Temporal window — correlate changes within 30 minutes before incident
CORRELATION_WINDOW = timedelta(minutes=30)
MIN_CONFIDENCE_THRESHOLD = 0.3


class CorrelationEngine:
    """Find correlations between incidents and config changes.

    Uses temporal proximity and entity-scope matching to
    assign confidence scores to potential correlations.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def correlate_incident(
        self,
        org_id: UUID,
        incident_type: str,
        incident_id: str,
        incident_at: datetime,
        affected_entity_ids: list[UUID],
    ) -> list[IncidentChangeCorrelation]:
        """Find changes that may have caused an incident."""
        window_start = incident_at - CORRELATION_WINDOW
        candidates = await self._find_candidates(
            org_id, window_start, incident_at, affected_entity_ids,
        )

        correlations: list[IncidentChangeCorrelation] = []
        for record in candidates:
            score = _compute_confidence(record, incident_at)
            if score < MIN_CONFIDENCE_THRESHOLD:
                continue

            method = _detection_method(record, affected_entity_ids)
            correlation = IncidentChangeCorrelation(
                org_id=org_id,
                incident_type=incident_type,
                incident_id=incident_id,
                incident_at=incident_at,
                change_revision_id=record.revision_id,
                change_job_id=record.job_id,
                confidence_score=round(score, 3),
                detection_method=method,
                detected_at=datetime.now(UTC),
            )
            self._db.add(correlation)
            correlations.append(correlation)

        if correlations:
            await self._db.flush()
        return correlations

    async def _find_candidates(
        self,
        org_id: UUID,
        window_start: datetime,
        window_end: datetime,
        entity_ids: list[UUID],
    ) -> list[AuditRecord]:
        """Query audit records in the correlation window."""
        stmt = (
            select(AuditRecord)
            .where(
                AuditRecord.org_id == org_id,
                AuditRecord.timestamp >= window_start,
                AuditRecord.timestamp <= window_end,
            )
            .order_by(AuditRecord.timestamp.desc())
            .limit(100)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())


def _compute_confidence(
    record: AuditRecord, incident_at: datetime,
) -> float:
    """Score 0-1 based on temporal proximity."""
    delta = abs((incident_at - record.timestamp).total_seconds())
    max_seconds = CORRELATION_WINDOW.total_seconds()

    if delta == 0:
        return 1.0
    proximity = 1.0 - (delta / max_seconds)
    return max(proximity, 0.0) * 0.85 + 0.15


def _detection_method(
    record: AuditRecord, affected_ids: list[UUID],
) -> str:
    """Classify the detection approach used."""
    if record.entity_id in affected_ids:
        return "scope_and_temporal"
    return "temporal"
