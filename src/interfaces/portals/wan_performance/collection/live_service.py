"""Commit validated live observations before publishing a recent snapshot cache."""

import logging
from datetime import UTC, datetime
from typing import Any

from src.interfaces.portals.wan_performance.collection.snapshot_client import GatewayInsights, SnapshotClient
from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.portals.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, IdentityValidator
from src.interfaces.portals.wan_performance.integration.history_repository import HistoryRepository
from src.interfaces.portals.wan_performance.integration.refresh_store import RefreshStore

logger = logging.getLogger(__name__)


class LiveService:
    """Use existing session, configured history, and Redis without a background thread."""

    def __init__(self, session: Any, org_id: str, store: RefreshStore, history: HistoryRepository | None) -> None:
        """Accept public boundaries and the server-selected organization."""
        if session is None:
            raise ConnectionError("The portal has no configured Mist session.")
        self.session = session
        self.org_id = IdentityValidator.identifier(org_id, "org_id")
        self.store = store
        self.history = history

    def refresh(self, target: GatewayIdentity | None = None) -> dict[str, object]:
        """Collect bounded pages only after shared WAN refresh admission succeeds."""
        logger.info("Start the bounded operator WAN refresh for organization %s.", self.org_id)
        if self.history is None:
            raise ConnectionError("History is unavailable. WAN refresh requires the selected durable store.")
        if target is not None and target.site.org_id != self.org_id:
            raise ValueError("The selected gateway organization does not match the portal.")
        lease = self.store.acquire(self.org_id)
        snapshot = SnapshotClient(self.session, lease).collect(self.org_id, target)
        records = SnapshotRecords.build(snapshot)
        lease.check()
        self.history.upsert(records)
        lease.check()
        self.store.publish(self.org_id, snapshot)
        logger.debug("Finished the bounded WAN refresh with %d history records.", len(records))
        return snapshot

    def refresh_port(self, target: CircuitIdentity) -> int:
        """Persist one completed port insight hour without replacing the recent snapshot."""
        logger.info("Start selected-port history refresh for organization %s.", self.org_id)
        if self.history is None:
            raise ConnectionError("History is unavailable. Port refresh requires the selected durable store.")
        self._check_port(target)
        lease = self.store.acquire(self.org_id)
        insights = GatewayInsights(self.session, lease).collect_for_port(self.org_id, target)
        snapshot = {
            "org_id": self.org_id,
            "provenance": "live",
            "collected_at_utc": datetime.now(UTC).isoformat(),
            "ports": [],
            "peers": [],
            "insights": insights,
        }
        records = SnapshotRecords.build(snapshot)
        lease.check()
        self.history.upsert(records)
        logger.debug("Persisted %d selected-port insight records without snapshot publication.", len(records))
        return len(records)

    def _check_port(self, target: CircuitIdentity) -> None:
        """Refuse another organization or a port absent from the validated cached page."""
        if target.gateway.site.org_id != self.org_id:
            raise ValueError("The selected port organization does not match the portal.")
        cached = self.store.cached(self.org_id)
        if cached is None or target not in {record.identity for record in SnapshotRecords.build(cached)}:
            raise ValueError("The selected port is absent from the cached organization.")
