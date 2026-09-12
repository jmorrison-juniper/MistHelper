"""Drift detection logic (T090).

Compares current device/site configuration against defined baselines
using DiffService. Generates DriftAlert records when changes detected.
SC-010: detection must complete within 10 minutes per org.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.models.config import Baseline, ConfigRevision, DriftAlert
from src.shared.services.diff import DiffService

logger = logging.getLogger(__name__)


class DriftScanner:
    """Scans all baselines for an org and emits DriftAlert records."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._diff = DiffService()

    def scan_org(self, org_id: UUID) -> dict:
        """Run drift scan for all baselines in an org."""
        baselines = self._load_baselines(org_id)
        alerts_created = 0
        baselines_checked = 0

        for baseline in baselines:
            baselines_checked += 1
            count = self._check_baseline(baseline)
            alerts_created += count

        return {
            "baselines_checked": baselines_checked,
            "alerts_created": alerts_created,
        }

    def _load_baselines(self, org_id: UUID) -> list[Baseline]:
        """Load all baselines for an org."""
        stmt = select(Baseline).where(Baseline.org_id == org_id)
        return list(self._db.execute(stmt).scalars().all())

    def _check_baseline(self, baseline: Baseline) -> int:
        """Compare baseline against latest revision."""
        revision = self._latest_revision(baseline)
        if revision is None:
            return 0

        diffs = self._compute_diffs(baseline, revision)
        if not diffs:
            return 0

        return self._create_alerts(baseline, revision, diffs)

    def _latest_revision(
        self,
        baseline: Baseline,
    ) -> ConfigRevision | None:
        """Find latest config revision matching baseline scope."""
        stmt = (
            select(ConfigRevision)
            .where(
                ConfigRevision.org_id == str(baseline.org_id),
                ConfigRevision.entity_type == baseline.entity_type,
                ConfigRevision.entity_id == baseline.entity_scope,
            )
            .order_by(ConfigRevision.captured_at.desc())
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def _compute_diffs(
        self,
        baseline: Baseline,
        revision: ConfigRevision,
    ) -> list[dict]:
        """Compute field-level diffs between baseline and actual."""
        result = self._diff.compute_diff(
            baseline.config_payload,
            revision.config_blob,
        )
        return result.changes if result.changes else []

    def _create_alerts(
        self,
        baseline: Baseline,
        revision: ConfigRevision,
        diffs: list[dict],
    ) -> int:
        """Create DriftAlert records for detected changes."""
        device_id = revision.entity_id
        existing = self._open_alert_exists(baseline, device_id)
        if existing:
            return 0

        alert = DriftAlert(
            org_id=baseline.org_id,
            baseline_id=baseline.baseline_id,
            device_id=device_id,
            detected_at=datetime.now(UTC),
            diff_payload={"changes": diffs},
            status="open",
        )
        self._db.add(alert)
        self._db.flush()
        logger.info(
            "Drift detected: baseline=%s device=%s changes=%d",
            baseline.baseline_id,
            device_id,
            len(diffs),
        )
        return 1

    def _open_alert_exists(
        self,
        baseline: Baseline,
        device_id: UUID,
    ) -> bool:
        """Check if an open alert already exists for this scope."""
        stmt = (
            select(DriftAlert.alert_id)
            .where(
                DriftAlert.baseline_id == baseline.baseline_id,
                DriftAlert.device_id == device_id,
                DriftAlert.status == "open",
            )
            .limit(1)
        )
        return self._db.execute(stmt).scalar_one_or_none() is not None
