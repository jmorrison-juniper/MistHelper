"""Collect verified VPN peer scalars through bounded organization-stat pages."""

import logging
from datetime import UTC, datetime
from typing import Any, Protocol

from mistapi.api.v1.orgs.stats import searchOrgPeerPathStats

from src.interfaces.wan_performance.collection.request_admission import StatsPageCollector
from src.interfaces.wan_performance.collection.snapshot_records import PeerSnapshotMetrics
from src.interfaces.wan_performance.domain.identity import PeerPathIdentity
from src.interfaces.wan_performance.domain.measurement import SampleMeasurement

logger = logging.getLogger(__name__)


class RequestAdmission(Protocol):
    """Require shared ownership before each outgoing API request."""

    def check(self) -> None:
        """Raise when ownership or request admission is unavailable."""


class PeerQualityStats:
    """Collect one path from documented peer statistics without fake timestamps."""

    def __init__(self, session: Any, admission: RequestAdmission) -> None:
        """Use the selected portal session and its shared admission lease."""
        self.session = session
        self.admission = admission

    def collect(self, target: PeerPathIdentity) -> tuple[SampleMeasurement, ...]:
        """Search supported gateway and site filters, then match the full path locally."""
        org_id = target.gateway.site.org_id
        logger.info("Collect verified VPN peer stats for one full path identity.")
        rows, partial = StatsPageCollector(self.admission.check).collect(
            lambda cursor: searchOrgPeerPathStats(
                self.session,
                org_id,
                mac=target.gateway.gateway_id,
                site_id=target.gateway.site.site_id,
                duration="1h",
                limit=100,
                search_after=cursor,
            ),
            "VPN peer",
        )
        matches = self._matching_rows(rows, target)
        if not matches:
            raise LookupError("VPN peer stats did not return the selected full path identity.")
        if len(matches) != 1:
            raise ValueError("VPN peer stats returned duplicate full identities without a sample timestamp.")
        collected_at = datetime.now(UTC)
        sample = PeerSnapshotMetrics.sample(matches[0], org_id, collected_at, collected_at, partial)
        logger.debug("Collected one VPN peer scalar sample with partial=%s.", partial)
        return (sample,)

    @staticmethod
    def _matching_rows(rows: list[dict[str, Any]], target: PeerPathIdentity) -> list[dict[str, Any]]:
        """Keep exact local and remote path fields from the supported result set."""
        return [row for row in rows if PeerPathIdentity.from_stats_row(row, target.gateway.site.org_id) == target]
