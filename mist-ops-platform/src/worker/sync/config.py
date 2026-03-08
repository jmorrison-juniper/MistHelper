"""Config snapshot sync — fetch device/site config and store revisions (T039).

``ConfigSyncService`` computes a SHA-256 content hash for each fetched
configuration. A new ``ConfigRevision`` is created only when the hash
differs from the latest stored revision (dedup via unique constraint).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.shared.config.constants import EntityType
from src.shared.mist.endpoints import MistEndpointService
from src.shared.models.config import ConfigRevision
from src.shared.models.inventory import Device, Site

logger = logging.getLogger(__name__)


class ConfigSyncService:
    """Capture configuration snapshots from Mist and store revisions."""

    def __init__(
        self,
        db: Session,
        mist: MistEndpointService,
        org_id: str,
    ) -> None:
        self._db = db
        self._mist = mist
        self._org_id = org_id

    # -- public entry point ----------------------------------------------

    def sync_device_configs(self) -> int:
        """Sync config for all devices in the org; return count stored."""
        devices = self._load_devices()
        stored = 0
        for device in devices:
            if self._capture_device_config(device):
                stored += 1
        self._db.commit()
        return stored

    def sync_site_configs(self) -> int:
        """Sync site settings for all sites; return count stored."""
        sites = self._load_sites()
        stored = 0
        for site in sites:
            if self._capture_site_config(site):
                stored += 1
        self._db.commit()
        return stored

    # -- capture helpers (max 25 lines) ----------------------------------

    def _capture_device_config(self, device: Device) -> bool:
        """Fetch and store device config if changed."""
        result = self._mist.read_entity(
            entity_type="device",
            ids={
                "site_id": str(device.site_id),
                "device_id": str(device.device_id),
            },
        )
        config_data = result.data if isinstance(result.data, dict) else {}
        return self._store_revision(
            entity_type=EntityType.DEVICE.value,
            entity_id=device.device_id,
            content=config_data,
        )

    def _capture_site_config(self, site: Site) -> bool:
        """Fetch and store site setting config if changed."""
        result = self._mist.read_entity(
            entity_type="site_setting",
            ids={"site_id": str(site.site_id)},
        )
        config_data = result.data if isinstance(result.data, dict) else {}
        return self._store_revision(
            entity_type=EntityType.SITE.value,
            entity_id=site.site_id,
            content=config_data,
        )

    # -- revision storage ------------------------------------------------

    def _store_revision(
        self,
        entity_type: str,
        entity_id: UUID,
        content: dict[str, Any],
    ) -> bool:
        """Store a new revision if the content hash is new."""
        content_hash = self._hash_content(content)
        stmt = pg_insert(ConfigRevision).values(
            org_id=UUID(self._org_id),
            entity_type=entity_type,
            entity_id=entity_id,
            config_payload=content,
            content_hash=content_hash,
            captured_at=datetime.now(UTC),
        )
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_revision_dedup"
        )
        result = self._db.execute(stmt)
        return result.rowcount > 0

    # -- helpers ---------------------------------------------------------

    def _load_devices(self) -> list[Device]:
        """Load all devices for the current org."""
        stmt = select(Device).where(Device.org_id == UUID(self._org_id))
        return list(self._db.execute(stmt).scalars().all())

    def _load_sites(self) -> list[Site]:
        """Load all sites for the current org."""
        stmt = select(Site).where(Site.org_id == UUID(self._org_id))
        return list(self._db.execute(stmt).scalars().all())

    @staticmethod
    def _hash_content(content: dict[str, Any]) -> str:
        """SHA-256 hash of deterministically serialised JSON."""
        canonical = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
