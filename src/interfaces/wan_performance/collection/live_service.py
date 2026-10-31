"""Commit validated live observations before publishing a recent snapshot cache."""

import logging
from datetime import UTC, datetime
from typing import Any

from src.interfaces.wan_performance.collection.peer_insights import PeerQualityInsights
from src.interfaces.wan_performance.collection.snapshot_client import GatewayInsights, SnapshotClient
from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    IdentityValidator,
    PeerPathIdentity,
)
from src.interfaces.wan_performance.integration.history_repository import HistoryRepository
from src.interfaces.wan_performance.integration.refresh_store import RefreshStore

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
        port = self._check_port(target)
        lease = self.store.acquire(self.org_id)
        insights = GatewayInsights(self.session, lease).collect_for_port(
            self.org_id, target, port.get("speed"), port.get("up")
        )
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

    def refresh_peer(self, target: PeerPathIdentity) -> int:
        """Persist one selected peer quality hour without replacing the snapshot."""
        if self.history is None:
            raise ConnectionError("History is unavailable. Peer refresh requires the selected durable store.")
        if target.gateway.site.org_id != self.org_id:
            raise ValueError("The selected peer organization does not match the portal.")
        snapshot = self.store.cached(self.org_id)
        if snapshot is None or target not in {record.identity for record in SnapshotRecords.build(snapshot)}:
            raise ValueError("The selected peer path is absent from the cached organization.")
        lease = self.store.acquire(self.org_id)
        records = PeerQualityInsights(self.session, lease).collect(target)
        lease.check()
        self.history.upsert(records)
        logger.debug("Persisted %d selected peer quality records.", len(records))
        return len(records)

    def _check_port(self, target: CircuitIdentity) -> dict[str, object]:
        """Refuse another organization or a port absent from the validated cached page."""
        if target.gateway.site.org_id != self.org_id:
            raise ValueError("The selected port organization does not match the portal.")
        cached = self.store.cached(self.org_id)
        if cached is None:
            raise ValueError("The selected port is absent from the cached organization.")
        records = SnapshotRecords.build(cached)
        if target not in {record.identity for record in records}:
            raise ValueError("The selected port is absent from the cached organization.")
        for row in self._cached_port_rows(cached):
            if (
                row.get("org_id"),
                row.get("site_id"),
                row.get("mac"),
                row.get("port_id"),
            ) == (
                self.org_id,
                target.gateway.site.site_id,
                target.gateway.gateway_id,
                target.port_name,
            ):
                return row
        raise ValueError("The selected port has no matching cached speed and status row.")

    @staticmethod
    def _cached_port_rows(cached: dict[str, object]) -> list[dict[str, object]]:
        """Validate cached port metadata before resolving speed and current state."""
        raw_ports = cached.get("ports")
        if not isinstance(raw_ports, list):
            raise ValueError("The cached organization has no port metadata.")
        rows = []
        for raw_row in raw_ports:
            if not isinstance(raw_row, dict):
                raise ValueError("Cached port metadata must contain objects.")
            row: dict[str, object] = {}
            for key, value in raw_row.items():
                if not isinstance(key, str):
                    raise ValueError("Cached port metadata keys must be strings.")
                row[key] = value
            rows.append(row)
        return rows
