"""Tests for UTC timestamps in the run persistence layer."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.upgrade_portal.persistence.runs import UpgradeRunsService


class RunDatabaseDouble:
    # WHY: capture run documents without ArangoDB
    """Store run writes for timestamp assertions."""

    def __init__(self) -> None:
        # WHY: start with no written documents
        self.documents: list[dict[str, Any]] = []  # WHY: preserve each write in order.

    def write(self, collection: str, document: dict[str, Any]) -> bool:
        # WHY: implement the write seam that the service calls
        self.documents.append({"collection": collection, **document})  # WHY: keep the target collection and payload.
        return True  # WHY: model a successful database write.


def test_create_run_writes_aware_utc_timestamps() -> None:
    """A created run stores aware UTC creation and update times."""
    database = RunDatabaseDouble()  # WHY: capture the database document.
    service = UpgradeRunsService(db_router=database)  # WHY: drive the product persistence service.

    run_id = service.create_run("user-1", "org-1", "site-1", ["device-1"])  # WHY: write one run document.

    record = database.documents[0]  # WHY: read the document that crossed the database boundary.
    created_at = datetime.fromisoformat(record["created_at"])  # WHY: parse the stored creation time.
    updated_at = datetime.fromisoformat(record["updated_at"])  # WHY: parse the stored update time.
    assert run_id == record["run_id"]  # WHY: prove the assertion reads the written document.
    assert created_at.utcoffset() == timedelta(0)  # WHY: creation time must be explicit UTC.
    assert updated_at.utcoffset() == timedelta(0)  # WHY: update time must be explicit UTC.
    assert record["created_at"] == record["updated_at"]  # WHY: a new run uses one timestamp for both fields.


def test_update_run_writes_aware_utc_timestamp() -> None:
    """An updated run stores an aware UTC update time."""
    database = RunDatabaseDouble()  # WHY: capture the database document.
    service = UpgradeRunsService(db_router=database)  # WHY: drive the product persistence service.

    result = service.update_run("run-1", {"status": "completed"})  # WHY: write one update document.

    record = database.documents[0]  # WHY: read the update that crossed the database boundary.
    updated_at = datetime.fromisoformat(record["updated_at"])  # WHY: parse the stored update time.
    assert result is True  # WHY: prove the update path succeeded.
    assert updated_at.utcoffset() == timedelta(0)  # WHY: update time must be explicit UTC.
    assert record["status"] == "completed"  # WHY: preserve caller fields with the timestamp.
