"""Inventory sync logic — orgs, sites, devices from Mist API (T029).

``InventorySyncService`` pulls the full org/site/device tree and
upserts records into PostgreSQL, recording each run in the sync ledger.
Runs inside Celery workers (synchronous context).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.shared.config.constants import EntityType
from src.shared.mist.endpoints import MistEndpointService
from src.shared.models.inventory import (
    Device,
    Organization,
    Site,
    SyncLedgerEntry,
)

if TYPE_CHECKING:  # the sync code reads ApiResult as a type only
    from src.shared.mist.endpoints import ApiResult

logger = logging.getLogger(__name__)


class MistSyncError(RuntimeError):
    """Raised when the Mist API reports a failure during a sync run."""


class InventorySyncService:
    """Synchronise Mist inventory into the local database."""

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

    def sync_full_inventory(self) -> dict[str, int]:
        """Run a complete org-tree sync and return the item counts.

        A Mist API failure raises ``MistSyncError``. The ledger then records
        the run as a failure, and the service writes no inventory row.
        """
        ledger = self._create_ledger_entry()
        try:
            counts = self._do_sync()
            self._finish_ledger(ledger, counts)
            return counts
        except Exception as exc:
            self._fail_ledger(ledger, str(exc))
            raise

    # -- individual sync routines (max 25 lines each) --------------------

    def _sync_sites(self, org_uuid: UUID) -> int:
        """Fetch and upsert sites for the org."""
        logger.info("Fetch the site list of org %s from Mist", self._org_id)  # log the start
        result = self._mist.list_all_entities(
            "org_site_list",
            ids={"org_id": self._org_id},
        )
        sites = self._read_records(result, "site")  # a failure raises and writes no row
        for site_data in sites:  # write one row for each real site
            self._upsert_site(org_uuid, site_data)
        self._db.flush()  # push the rows into the open transaction
        logger.debug("Upsert of %d site rows is complete", len(sites))  # log the result
        return len(sites)

    def _sync_devices(self, org_uuid: UUID) -> int:
        """Fetch and upsert devices for all sites in the org."""
        logger.info("Fetch the device list of org %s from Mist", self._org_id)  # log the start
        result = self._mist.list_all_entities(
            "org_inventory",
            ids={"org_id": self._org_id},
        )
        devices = self._read_records(result, "device")  # a failure raises and writes no row
        for device_data in devices:  # write one row for each real device
            self._upsert_device(org_uuid, device_data)
        self._db.flush()  # push the rows into the open transaction
        logger.debug("Upsert of %d device rows is complete", len(devices))  # log the result
        return len(devices)

    @staticmethod
    def _read_records(result: ApiResult, label: str) -> list[dict[str, Any]]:
        """Return the Mist records, or raise when the Mist call failed."""
        if not result.success:  # a failed call must never write an inventory row
            msg = f"Mist {label} list failed with status {result.status_code}: {result.error}"
            logger.error("%s", msg)  # report the failure before the raise
            raise MistSyncError(msg)  # the ledger records this run as a failure
        if not isinstance(result.data, list):  # a non-list body holds no records
            logger.warning("Mist %s list body is not a list, so read no records", label)
            return []
        return result.data  # only a successful list body reaches the upsert helpers

    # -- upsert helpers --------------------------------------------------

    def _upsert_site(self, org_uuid: UUID, data: dict[str, Any]) -> None:
        """Insert or update a single site record."""
        site_id = UUID(data["id"]) if data.get("id") else uuid4()
        stmt = pg_insert(Site).values(
            site_id=site_id,
            name=data.get("name", ""),
            org_id=org_uuid,
            address=data.get("address"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["site_id"],
            set_={"name": stmt.excluded.name, "address": stmt.excluded.address},
        )
        self._db.execute(stmt)

    def _upsert_device(self, org_uuid: UUID, data: dict[str, Any]) -> None:
        """Insert or update a single device record."""
        site_uuid = UUID(data["site_id"]) if data.get("site_id") else None
        nil_uuid = UUID("00000000-0000-0000-0000-000000000000")
        if not site_uuid or site_uuid == nil_uuid:
            return  # skip devices with no real site assignment
        device_id = UUID(data["id"]) if data.get("id") else uuid4()
        connected = data.get("connected", False)
        device_status = "connected" if connected else "disconnected"
        stmt = pg_insert(Device).values(
            device_id=device_id,
            site_id=site_uuid,
            org_id=org_uuid,
            name=data.get("name"),
            device_type=data.get("type", "ap"),
            model=data.get("model", "unknown"),
            serial=data.get("serial", ""),
            mac_address=data.get("mac"),
            firmware_version=data.get("version"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["device_id"],
            set_={
                "name": stmt.excluded.name,
                "firmware_version": stmt.excluded.firmware_version,
                "status": device_status,
            },
        )
        self._db.execute(stmt)

    # -- ledger bookkeeping ----------------------------------------------

    def _do_sync(self) -> dict[str, int]:
        """Execute the full sync pipeline; return counts."""
        org_uuid = self._db.execute(
            select(Organization.org_id).where(Organization.org_id == UUID(self._org_id))
        ).scalar()
        if not org_uuid:
            logger.warning("Org %s not found in DB -- skipping", self._org_id)
            return {"sites": 0, "devices": 0}
        sites = self._sync_sites(org_uuid)
        devices = self._sync_devices(org_uuid)
        self._db.commit()
        return {"sites": sites, "devices": devices}

    def _create_ledger_entry(self) -> SyncLedgerEntry:
        """Record the start of a sync run."""
        org_uuid = self._db.execute(
            select(Organization.org_id).where(Organization.org_id == UUID(self._org_id))
        ).scalar()
        entry = SyncLedgerEntry(
            org_id=org_uuid,
            job_type=EntityType.DEVICE.value,
            status="running",
            started_at=datetime.now(UTC),
        )
        self._db.add(entry)
        self._db.flush()
        return entry

    def _finish_ledger(
        self,
        entry: SyncLedgerEntry,
        counts: dict[str, int],
    ) -> None:
        """Mark a ledger entry as completed."""
        total = sum(counts.values())
        entry.status = "completed"
        entry.rows_affected = total
        entry.ended_at = datetime.now(UTC)
        self._db.commit()

    def _fail_ledger(self, entry: SyncLedgerEntry, error: str) -> None:
        """Mark a ledger entry as failed."""
        self._db.rollback()
        entry.status = "failed"
        entry.error_text = error[:2000]
        entry.ended_at = datetime.now(UTC)
        self._db.commit()
