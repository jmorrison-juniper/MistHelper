"""Tests for UTC timestamps in the run persistence layer."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.interfaces.portals.upgrade_portal.persistence.runs import UpgradeRunsService


class CollectionDouble:
    """Implement the Arango collection methods that the service owns."""

    def __init__(self) -> None:
        """Start with an empty document collection."""
        self.documents: dict[str, dict[str, Any]] = {}

    def insert(self, document: dict[str, Any]) -> dict[str, Any]:
        """Store one document under its natural key."""
        self.documents[document["_key"]] = dict(document)
        return dict(document)

    def get(self, key: str) -> dict[str, Any] | None:
        """Read one document by its natural key."""
        document = self.documents.get(key)
        return dict(document) if document is not None else None

    def update(self, document: dict[str, Any]) -> dict[str, Any]:
        """Apply one Arango-style partial document update."""
        self.documents[document["_key"]].update(document)
        return dict(self.documents[document["_key"]])


class RunDatabaseDouble:
    """Expose the explicit collection interface without a production store."""

    def __init__(self) -> None:
        """Create one isolated upgrade_runs collection."""
        self.upgrade_runs = CollectionDouble()

    def collection(self, name: str) -> CollectionDouble:
        """Return the collection named by the service."""
        assert name == "upgrade_runs"
        return self.upgrade_runs


def test_create_run_writes_aware_utc_timestamps() -> None:
    """A created run stores aware UTC creation and update times."""
    database = RunDatabaseDouble()  # WHY: capture the database document.
    service = UpgradeRunsService(db_router=object(), document_store=database)

    run_id = service.create_run("user-1", "org-1", "site-1", ["device-1"])  # WHY: write one run document.

    record = database.collection("upgrade_runs").get(run_id)
    assert record is not None
    created_at = datetime.fromisoformat(record["created_at"])  # WHY: parse the stored creation time.
    updated_at = datetime.fromisoformat(record["updated_at"])  # WHY: parse the stored update time.
    assert run_id == record["run_id"]  # WHY: prove the assertion reads the written document.
    assert created_at.utcoffset() == timedelta(0)  # WHY: creation time must be explicit UTC.
    assert updated_at.utcoffset() == timedelta(0)  # WHY: update time must be explicit UTC.
    assert record["created_at"] == record["updated_at"]  # WHY: a new run uses one timestamp for both fields.


def test_update_run_writes_aware_utc_timestamp() -> None:
    """An updated run stores an aware UTC update time."""
    database = RunDatabaseDouble()  # WHY: capture the database document.
    service = UpgradeRunsService(db_router=object(), document_store=database)
    database.collection("upgrade_runs").insert({"_key": "run-1", "run_id": "run-1", "status": "in_progress"})

    result = service.update_run("run-1", {"status": "completed"})  # WHY: write one update document.

    record = database.collection("upgrade_runs").get("run-1")
    assert record is not None
    updated_at = datetime.fromisoformat(record["updated_at"])  # WHY: parse the stored update time.
    assert result is True  # WHY: prove the update path succeeded.
    assert updated_at.utcoffset() == timedelta(0)  # WHY: update time must be explicit UTC.
    assert record["status"] == "completed"  # WHY: preserve caller fields with the timestamp.
