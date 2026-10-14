"""Commit validated live observations before publishing a recent snapshot cache."""

import logging
from typing import Any

from src.interfaces.portals.wan_performance.collection.snapshot_client import SnapshotClient
from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords
from src.interfaces.portals.wan_performance.domain.identity import IdentityValidator
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

    def refresh(self) -> dict[str, object]:
        """Collect bounded pages only after shared WAN refresh admission succeeds."""
        logger.info("Start the bounded operator WAN refresh for organization %s.", self.org_id)
        if self.history is None:
            raise ConnectionError("History is unavailable. WAN refresh requires the selected durable store.")
        lease = self.store.acquire(self.org_id)
        snapshot = SnapshotClient(self.session, lease).collect(self.org_id)
        records = SnapshotRecords.build(snapshot)
        lease.check()
        self.history.upsert(records)
        lease.check()
        self.store.publish(self.org_id, snapshot)
        logger.debug("Finished the bounded WAN refresh with %d history records.", len(records))
        return snapshot
