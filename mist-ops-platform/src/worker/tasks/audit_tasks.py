"""Audit Celery tasks — export and compliance pack generation (T072).

Tasks:
  - export_audit_records: async CSV/JSON export of filtered records
  - generate_compliance_pack: build compliance evidence package
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.shared.config.settings import get_settings
from src.shared.models.governance import ComplianceAuditPack
from src.shared.models.operations import AuditRecord
from src.worker.celeryconfig import app

logger = logging.getLogger(__name__)


@app.task(name="src.worker.tasks.audit_tasks.export_audit_records")
def export_audit_records(
    org_id: str,
    export_format: str,
    filters: dict,
) -> dict:
    """Export filtered audit records to CSV or JSON.

    Returns metadata about the generated export including
    record count and serialized content for storage.
    """
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        records = _query_filtered(db, org_id, filters)
        content = _serialize(records, export_format)

    engine.dispose()
    return {
        "status": "completed",
        "record_count": len(records),
        "format": export_format,
        "content_length": len(content),
    }


@app.task(name="src.worker.tasks.audit_tasks.generate_compliance_pack")
def generate_compliance_pack(
    org_id: str,
    framework: str,
    date_start: str,
    date_end: str,
    export_format: str,
    generated_by: str,
) -> dict:
    """Generate a compliance audit evidence package.

    Queries all audit records in the date range, builds a
    summary, and persists a ComplianceAuditPack record.
    """
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        records = _query_date_range(
            db, org_id,
            datetime.fromisoformat(date_start),
            datetime.fromisoformat(date_end),
        )
        summary = _build_pack_summary(records, framework)
        pack = ComplianceAuditPack(
            org_id=UUID(org_id),
            framework=framework,
            date_range_start=datetime.fromisoformat(date_start),
            date_range_end=datetime.fromisoformat(date_end),
            included_records=summary,
            export_format=export_format,
            generated_by=generated_by,
        )
        db.add(pack)
        db.commit()
        pack_id = str(pack.pack_id)

    engine.dispose()
    return {
        "pack_id": pack_id,
        "status": "completed",
        "framework": framework,
        "record_count": len(records),
    }


# -- Helpers ---


def _query_filtered(
    db: Session, org_id: str, filters: dict,
) -> list[AuditRecord]:
    """Apply filters to audit record query."""
    stmt = (
        select(AuditRecord)
        .where(AuditRecord.org_id == UUID(org_id))
        .order_by(AuditRecord.timestamp.desc())
    )
    entity_type = filters.get("entity_type")
    if entity_type:
        stmt = stmt.where(AuditRecord.entity_type == entity_type)

    actor = filters.get("actor")
    if actor:
        stmt = stmt.where(AuditRecord.actor == actor)

    stmt = stmt.limit(10000)
    return list(db.execute(stmt).scalars().all())


def _query_date_range(
    db: Session,
    org_id: str,
    start: datetime,
    end: datetime,
) -> list[AuditRecord]:
    """Query records within a date range."""
    stmt = (
        select(AuditRecord)
        .where(
            AuditRecord.org_id == UUID(org_id),
            AuditRecord.timestamp >= start,
            AuditRecord.timestamp <= end,
        )
        .order_by(AuditRecord.timestamp.asc())
        .limit(50000)
    )
    return list(db.execute(stmt).scalars().all())


def _serialize(
    records: list[AuditRecord], fmt: str,
) -> str:
    """Serialize records to the requested format."""
    if fmt == "csv":
        return _to_csv(records)
    return _to_json(records)


def _to_csv(records: list[AuditRecord]) -> str:
    """Convert records to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "record_id", "timestamp", "actor", "entity_type",
        "entity_id", "change_type",
    ])
    for record in records:
        writer.writerow([
            record.record_id,
            record.timestamp.isoformat(),
            record.actor,
            record.entity_type,
            str(record.entity_id),
            record.change_type,
        ])
    return output.getvalue()


def _to_json(records: list[AuditRecord]) -> str:
    """Convert records to JSON string."""
    items = [
        {
            "record_id": r.record_id,
            "timestamp": r.timestamp.isoformat(),
            "actor": r.actor,
            "entity_type": r.entity_type,
            "entity_id": str(r.entity_id),
            "change_type": r.change_type,
        }
        for r in records
    ]
    return json.dumps(items, indent=2)


def _build_pack_summary(
    records: list[AuditRecord], framework: str,
) -> dict:
    """Build summary metadata for a compliance pack."""
    by_type: dict[str, int] = {}
    for record in records:
        by_type[record.change_type] = (
            by_type.get(record.change_type, 0) + 1
        )
    return {
        "framework": framework,
        "total_records": len(records),
        "changes_by_type": by_type,
    }


# ===================================================================
# Retention policy task (T098)
# ===================================================================

_RETENTION_DAYS = {
    "config_revisions": 365,
    "device_status_snapshots": 90,
    "audit_records": 730,
    "drift_alerts": 180,
    "webhook_envelopes": 30,
}


@app.task(name="src.worker.tasks.audit_tasks.run_retention_cleanup")
def run_retention_cleanup() -> dict:
    """Nightly cleanup of expired records per data-model.md retention."""
    from sqlalchemy import text

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    results: dict[str, int] = {}
    with Session(engine) as db:
        for table, days in _RETENTION_DAYS.items():
            results[table] = _purge_table(db, table, days)
        db.commit()

    engine.dispose()
    logger.info("Retention cleanup complete: %s", results)
    return results


def _purge_table(db: Session, table: str, days: int) -> int:
    """Delete rows older than retention period."""
    from sqlalchemy import text

    ts_col = _timestamp_column(table)
    sql = text(
        f"DELETE FROM {table} "
        f"WHERE {ts_col} < NOW() - INTERVAL ':days days'"
    )
    result = db.execute(sql, {"days": days})
    return result.rowcount


def _timestamp_column(table: str) -> str:
    """Map table to its timestamp column for retention."""
    mapping = {
        "config_revisions": "captured_at",
        "device_status_snapshots": "captured_at",
        "audit_records": "timestamp",
        "drift_alerts": "detected_at",
        "webhook_envelopes": "received_at",
    }
    return mapping.get(table, "created_at")
