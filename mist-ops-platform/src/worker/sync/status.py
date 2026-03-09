"""Device status sync — port states, client count, health metrics (T040).

``StatusSyncService`` fetches device stats from Mist and stores
periodic snapshots in ``device_status_snapshots``.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.mist.endpoints import MistEndpointService
from src.shared.models.config import DeviceStatusSnapshot
from src.shared.models.inventory import Device

logger = logging.getLogger(__name__)


class StatusSyncService:
    """Capture device health/status snapshots from Mist."""

    def __init__(
        self,
        db: Session,
        mist: MistEndpointService,
        org_id: str,
    ) -> None:
        self._db = db
        self._mist = mist
        self._org_id = org_id

    def sync_device_status(self) -> int:
        """Pull status for all org devices; return snapshot count."""
        devices = self._load_devices()
        count = 0
        for device in devices:
            self._capture_status(device)
            count += 1
        self._db.commit()
        return count

    def _capture_status(self, device: Device) -> None:
        """Fetch and store one device status snapshot."""
        result = self._mist.read_entity(
            "device_stats",
            ids={
                "site_id": str(device.site_id),
                "device_id": str(device.device_id),
            },
        )
        data = result.data if isinstance(result.data, dict) else {}
        snapshot = DeviceStatusSnapshot(
            device_id=device.device_id,
            org_id=self._org_id,
            status=data.get("status", "unknown"),
            client_count=data.get("num_clients", 0),
            health_metrics=data,
            captured_at=datetime.now(UTC),
        )
        self._db.add(snapshot)

    def _load_devices(self) -> list[Device]:
        """Load all devices for the current org."""
        stmt = select(Device).where(Device.org_id == UUID(self._org_id))
        return list(self._db.execute(stmt).scalars().all())
