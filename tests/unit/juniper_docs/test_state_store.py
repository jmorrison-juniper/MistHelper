"""Unit tests for the durable, resumable SQLite state store.

These tests prove the privacy invariant at the schema level, the file-before-
state durable write with a verified read-back, the resume query for non-final
rows, and the fail-closed behavior on a locked or damaged database (T016).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from src.juniper_docs.harvest.state_store import HarvestStateStore, StateStoreError
from src.juniper_docs.models import DocumentType, InventoryRecord


def _store(tmp_path: Path) -> HarvestStateStore:
    """Return a fresh store rooted in the test temporary directory."""
    return HarvestStateStore(tmp_path / "harvest_state.db")  # One store per test.


def _record(url: str, slug: str) -> InventoryRecord:
    """Return an HTML-root inventory record for one URL and slug."""
    return InventoryRecord(url, slug, DocumentType.HTML_ROOT)  # Minimal test document.


def test_content_scores_table_has_no_text_column(tmp_path: Path) -> None:
    """The content_scores schema holds only the signal names and the scores."""
    store = _store(tmp_path)  # Open a fresh store with the full schema.
    columns = [row[1] for row in store._conn.execute("PRAGMA table_info(content_scores)")]
    store.close()  # Release the database file for the temp cleanup.
    assert columns == ["root_url", "signal_group", "signal_name", "score"]  # No text column.
    assert not any("text" in name.lower() for name in columns)  # The invariant holds.


def test_durable_write_then_verified_readback(tmp_path: Path) -> None:
    """A downloaded write is durable and reads back as the downloaded stage."""
    store = _store(tmp_path)  # Open a fresh store.
    store.add_document(_record("https://x/a/", "a"))  # Insert the document.
    store.mark_downloaded("https://x/a/", "data/a.pdf", 2048)  # Write the downloaded stage.
    assert store.stage_of("https://x/a/") == "downloaded"  # The verified read-back matches.
    store.close()  # Release the database file.


def test_resume_returns_only_non_final_rows(tmp_path: Path) -> None:
    """The resume query returns discovered, resolved, and downloaded rows only."""
    store = _store(tmp_path)  # Open a fresh store.
    _seed_mixed_stages(store)  # Seed one document at each stage.
    targets = {str(row["root_url"]) for row in store.resume_documents(retry_failed=False)}
    store.close()  # Release the database file.
    assert targets == {"https://x/discovered/", "https://x/resolved/", "https://x/downloaded/"}


def test_retry_failed_adds_failed_rows(tmp_path: Path) -> None:
    """A retry run also returns the failed rows, but never the final rows."""
    store = _store(tmp_path)  # Open a fresh store.
    _seed_mixed_stages(store)  # Seed one document at each stage.
    targets = {str(row["root_url"]) for row in store.resume_documents(retry_failed=True)}
    store.close()  # Release the database file.
    assert "https://x/failed/" in targets  # The failed row is retried.
    assert "https://x/classified/" not in targets  # A classified row stays final.
    assert "https://x/dropped/" not in targets  # A dropped row stays final.


def test_add_document_is_idempotent_for_resume(tmp_path: Path) -> None:
    """Re-adding a classified document never resets it, so resume skips it."""
    store = _store(tmp_path)  # Open a fresh store.
    store.add_document(_record("https://x/done/", "done"))  # Insert the document.
    store.set_classified("https://x/done/", None, None)  # Reach a final stage.
    store.add_document(_record("https://x/done/", "done"))  # A repeated discovery pass.
    assert store.stage_of("https://x/done/") == "classified"  # The final stage is intact.
    assert store.resume_documents(retry_failed=False) == []  # Nothing left to reprocess.
    store.close()  # Release the database file.


def test_check_integrity_raises_on_a_reported_problem(tmp_path: Path) -> None:
    """A non-ok integrity result makes the store fail closed."""
    store = _store(tmp_path)  # Open a fresh store.
    store._conn.close()  # Close the real connection before swapping a fake one.
    store._conn = _NotOkConnection()  # Simulate a damaged database report.
    with pytest.raises(StateStoreError):  # The store must fail closed.
        store.check_integrity()  # The non-ok result raises.


def test_write_fails_closed_on_a_locked_database(tmp_path: Path) -> None:
    """A locked database makes a write fail closed with a clear error."""
    store = _store(tmp_path)  # Open a fresh store.
    store._conn.close()  # Close the real connection before swapping a fake one.
    store._conn = _LockedConnection()  # Simulate a locked database.
    with pytest.raises(StateStoreError):  # The write must fail closed.
        store.mark_failed("https://x/a/", "boom")  # The locked write raises.


def test_batch_write_fails_closed_on_a_locked_database(tmp_path: Path) -> None:
    """A locked database makes a batch write fail closed with a clear error."""
    store = _store(tmp_path)  # Open a fresh store.
    store._conn.close()  # Close the real connection before swapping a fake one.
    store._conn = _LockedConnection()  # Simulate a locked database.
    with pytest.raises(StateStoreError):  # The batch write must fail closed.
        store.record_scores("https://x/a/", [("product_family", "srx", 1.0)])  # The batch raises.


def test_check_integrity_raises_on_a_database_error(tmp_path: Path) -> None:
    """A database error during the integrity check makes the store fail closed."""
    store = _store(tmp_path)  # Open a fresh store.
    store._conn.close()  # Close the real connection before swapping a fake one.
    store._conn = _RaisingConnection()  # Simulate a damaged database that raises.
    with pytest.raises(StateStoreError):  # The store must fail closed.
        store.check_integrity()  # The raised database error is converted.


def test_backup_copies_the_database_file(tmp_path: Path) -> None:
    """The backup copies the database to a sibling backup file."""
    store = _store(tmp_path)  # Open a fresh store.
    store.add_document(_record("https://x/a/", "a"))  # Add one document.
    backup = store.backup()  # Copy the database to the backup path.
    store.close()  # Release the database file.
    assert backup.exists()  # The backup file was written.
    assert backup.name == "harvest_state.db.bak"  # The backup sits beside the store.


def _seed_mixed_stages(store: HarvestStateStore) -> None:
    """Seed one document at each of the six stages for the resume tests."""
    store.add_document(_record("https://x/discovered/", "discovered"))  # Stays discovered.
    store.add_document(_record("https://x/resolved/", "resolved"))  # Move to resolved.
    store.set_resolved("https://x/resolved/", "https://x/resolved/r.pdf", [])  # Resolved.
    store.add_document(_record("https://x/downloaded/", "downloaded"))  # Move to downloaded.
    store.mark_downloaded("https://x/downloaded/", "data/d.pdf", 10)  # Downloaded stage.
    store.add_document(_record("https://x/classified/", "classified"))  # Move to classified.
    store.set_classified("https://x/classified/", None, None)  # Final classified.
    store.add_document(_record("https://x/failed/", "failed"))  # Move to failed.
    store.mark_failed("https://x/failed/", "timeout")  # Final failed stage.
    store.add_document(_record("https://x/dropped/", "dropped"))  # Move to dropped.
    store.record_dropped("https://x/dropped/", "superseded")  # Final dropped stage.


class _NotOkConnection:
    """A fake connection whose integrity check reports a problem."""

    def execute(self, _sql: str, *_args: Any) -> Any:
        """Return a cursor whose fetchone reports a non-ok integrity result."""
        cursor = sqlite3.connect(":memory:").cursor()  # A throwaway real cursor object.
        cursor.execute("SELECT 'malformed'")  # Load a single non-ok row into the cursor.
        return cursor  # The store reads row[0] and sees the non-ok result.


class _LockedConnection:
    """A fake connection that raises as though the database is locked."""

    def __enter__(self) -> _LockedConnection:
        """Enter the transaction context the store opens for a write."""
        return self  # The store uses the connection as a context manager.

    def __exit__(self, *_exc: object) -> bool:
        """Exit the transaction context without swallowing an exception."""
        return False  # Never suppress the raised error.

    def execute(self, _sql: str, *_args: Any) -> Any:
        """Raise the operational error the store must convert to fail-closed."""
        raise sqlite3.OperationalError("database is locked")  # The locked-write signal.

    def executemany(self, _sql: str, _rows: Any) -> Any:
        """Raise the operational error for a batch write as well."""
        raise sqlite3.OperationalError("database is locked")  # The locked batch signal.


class _RaisingConnection:
    """A fake connection whose integrity check raises a database error."""

    def execute(self, _sql: str, *_args: Any) -> Any:
        """Raise a database error to simulate a damaged database file."""
        raise sqlite3.DatabaseError("file is not a database")  # The damaged-file signal.
