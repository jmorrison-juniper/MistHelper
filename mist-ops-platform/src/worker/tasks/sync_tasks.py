"""Full sync pipeline Celery tasks (T030 + T042).

``sync_all_inventory`` is scheduled by Beat every 5 minutes.
It iterates over all known organizations and runs the full sync
pipeline: inventory -> config -> status -> events.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.shared.config.settings import get_settings
from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.session import get_session_factory
from src.shared.models.inventory import Organization
from src.worker.celeryconfig import app
from src.worker.checks.drift import DriftScanner
from src.worker.sync.config import ConfigSyncService
from src.worker.sync.events import EventSyncService
from src.worker.sync.inventory import InventorySyncService
from src.worker.sync.status import StatusSyncService

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Engine

logger = logging.getLogger(__name__)


@contextmanager
def _sync_engine() -> Iterator[Engine]:
    """Yield a task-scoped engine and dispose it on every exit path.

    An engine owns a connection pool. A pool that no code disposes keeps
    its PostgreSQL sockets open until the database reaches
    ``max_connections``, and then every service on that database fails.
    The ``finally`` clause runs after a return and after an exception, so
    no path can skip the release.
    """
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    logger.info("Opening a task engine for the sync database")
    engine = create_engine(sync_url)  # WHY: Celery tasks run sync code, not async code.
    try:
        yield engine  # WHY: the caller runs its whole body inside this scope.
    finally:
        engine.dispose()  # WHY: this line runs on the success path and on the error path.
        logger.debug("Disposed the task engine and closed its connection pool")


@app.task(name="src.worker.tasks.sync_tasks.sync_all_inventory")
def sync_all_inventory() -> dict:
    """Sync inventory for every registered organization."""
    logger.info("Starting the inventory sync for every organization")
    with _sync_engine() as engine:  # WHY: the scope disposes the engine for us.
        with Session(engine) as db:
            org_ids = _load_org_mist_ids(db)

        results: dict[str, dict] = {}
        for mist_org_id in org_ids:
            results[mist_org_id] = _sync_single_org(engine, mist_org_id)

    logger.debug("Inventory sync finished for %d organizations", len(results))
    return results


@app.task(name="src.worker.tasks.sync_tasks.sync_org_inventory")
def sync_org_inventory(mist_org_id: str) -> dict:
    """Sync inventory for a single organization (on-demand)."""
    logger.info("Starting the inventory sync for organization %s", mist_org_id)
    with _sync_engine() as engine:  # WHY: an exception in the sync must not leak a pool.
        result = _sync_single_org(engine, mist_org_id)

    logger.debug("Inventory sync finished for organization %s", mist_org_id)
    return result


def _load_org_mist_ids(db: Session) -> list[str]:
    """Return all registered Mist org IDs."""
    rows = db.execute(select(Organization.org_id)).scalars().all()
    return [str(oid) for oid in rows]


def _sync_single_org(engine, mist_org_id: str) -> dict:  # noqa: ANN001
    """Run full sync pipeline for one org.

    Pipeline order: inventory -> config -> status -> events.
    Each stage is independent; failures are logged but do not block
    subsequent stages.
    """
    result: dict[str, object] = {}
    factory = get_session_factory()  # WHY: reuse the cached session and token factory.
    # WHY: build the org-scoped Mist SDK session.
    api_session = factory.create_session(mist_org_id)
    # WHY: enforce the org API budget on every call. Fixes #1886.
    limiter = factory.create_rate_limiter(mist_org_id)
    # WHY: wire the limiter into the shared client.
    mist = MistEndpointService(api_session, rate_limiter=limiter)

    result["inventory"] = _run_inventory_sync(engine, mist, mist_org_id)
    result["config"] = _run_config_sync(engine, mist, mist_org_id)
    result["drift"] = _run_drift_scan(engine, mist_org_id)
    result["status"] = _run_status_sync(engine, mist, mist_org_id)
    result["events"] = _run_events_sync(engine, mist, mist_org_id)
    return result


def _run_inventory_sync(engine, mist: MistEndpointService, org_id: str) -> dict:  # noqa: ANN001
    """Stage 1: Inventory (sites + devices)."""
    try:
        with Session(engine) as db:
            service = InventorySyncService(db, mist, org_id)
            return service.sync_full_inventory()
    except Exception:
        logger.exception("Inventory sync failed for %s", org_id)
        return {"error": f"inventory sync failed for {org_id}"}


def _run_config_sync(engine, mist: MistEndpointService, org_id: str) -> dict:  # noqa: ANN001
    """Stage 2: Config revisions (device + site configs)."""
    try:
        with Session(engine) as db:
            service = ConfigSyncService(db, mist, org_id)
            device_count = service.sync_device_configs()
            site_count = service.sync_site_configs()
            return {"devices": device_count, "sites": site_count}
    except Exception:
        logger.exception("Config sync failed for %s", org_id)
        return {"error": f"config sync failed for {org_id}"}


def _run_status_sync(engine, mist: MistEndpointService, org_id: str) -> dict:  # noqa: ANN001
    """Stage 3: Device status snapshots."""
    try:
        with Session(engine) as db:
            service = StatusSyncService(db, mist, org_id)
            count = service.sync_device_status()
            return {"snapshots": count}
    except Exception:
        logger.exception("Status sync failed for %s", org_id)
        return {"error": f"status sync failed for {org_id}"}


def _run_events_sync(engine, mist: MistEndpointService, org_id: str) -> dict:  # noqa: ANN001
    """Stage 4: Audit events from Mist logs."""
    try:
        with Session(engine) as db:
            service = EventSyncService(db, mist, org_id)
            count = service.sync_audit_events()
            return {"events": count}
    except Exception:
        logger.exception("Events sync failed for %s", org_id)
        return {"error": f"events sync failed for {org_id}"}


def _run_drift_scan(engine, org_id: str) -> dict:  # noqa: ANN001
    """Stage 2b: Drift detection after config sync (SC-010)."""
    try:
        with Session(engine) as db:
            from src.shared.models.inventory import Organization

            org = db.execute(
                select(Organization).where(
                    Organization.org_id == org_id,
                ),
            ).scalar_one_or_none()
            if org is None:
                return {"skipped": "org not found"}
            scanner = DriftScanner(db)
            result = scanner.scan_org(org.org_id)
            db.commit()
            return result
    except Exception:
        logger.exception("Drift scan failed for %s", org_id)
        return {"error": f"drift scan failed for {org_id}"}


# ========================================================================
# Daily automated backup (T115, FR-034, SC-018)
# ========================================================================


@app.task(name="src.worker.tasks.sync_tasks.run_daily_backup")
def run_daily_backup() -> dict:
    """Export config revisions and audit records to MinIO daily."""
    from datetime import UTC, datetime

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    tables = ("config_revisions", "audit_records", "baselines")
    counts: dict[str, int] = {}

    logger.info("Starting the daily backup at %s", timestamp)
    with _sync_engine() as engine:  # WHY: Beat runs this task daily, so a leak grows every day.
        for table_name in tables:
            counts[table_name] = _export_table_backup(engine, table_name, timestamp)

    logger.debug("Daily backup complete: %s", counts)
    return {"timestamp": timestamp, "rows": counts}


def _export_table_backup(
    engine,  # noqa: ANN001
    table_name: str,
    timestamp: str,
) -> int:
    """Export a single table to JSON lines format."""
    import json

    from sqlalchemy import text

    try:
        with Session(engine) as db:
            # `table_name` is drawn from the hardcoded tuple above (line 170),
            # never from user input. LIMIT is a literal integer.
            rows = db.execute(text(f"SELECT * FROM {table_name} LIMIT 50000"))  # nosec B608
            data = [dict(row._mapping) for row in rows]
            logger.info(
                "Backup %s: %d rows at %s",
                table_name,
                len(data),
                timestamp,
            )
            return len(data)
    except Exception:
        logger.exception("Backup failed for %s", table_name)
        return 0
