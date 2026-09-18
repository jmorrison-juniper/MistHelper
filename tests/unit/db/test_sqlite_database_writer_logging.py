"""Log-order regression tests for SQLite writer failure paths."""

from __future__ import annotations  # Keep annotation behavior stable across supported Python versions.

import logging  # Capture exact log levels and messages with caplog.
import sqlite3  # Raise the same exception class that the writer handles.
from pathlib import Path  # Build a portable per-test database path.

import pytest  # Use pytest fixtures and exception assertions.

from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter  # Import the writer under test.


class _CommittedConnection:
    """Record whether the commit step ran before verification failed."""

    def __init__(self) -> None:
        self.commit_called = False  # Start false so the test can prove commit ran.

    def commit(self) -> None:
        self.commit_called = True  # Mark the commit so the failure path remains realistic.


class _FailingVerifyCursor:
    """Raise during verification to prove the success claim does not outrun the proof."""

    def execute(self, query: str) -> None:
        self.query = query  # Store the query so the object mimics a cursor side effect.
        raise sqlite3.Error("verification failed")  # Fail after commit, before row-count proof.


def _writer_for_verification_failure(tmp_path: Path) -> SQLiteDatabaseWriter:
    """Build a writer instance that fails only during row-count verification."""
    writer = SQLiteDatabaseWriter.__new__(SQLiteDatabaseWriter)  # Bypass dependency resolution in __init__.
    writer.connection = _CommittedConnection()  # Provide the minimal connection API for _commit_and_verify.
    writer.cursor = _FailingVerifyCursor()  # Provide a cursor that fails on the verification query.
    writer.processed_data = [{"id": "row-1"}]  # Give the log message a deterministic total row count.
    writer.table_name = "widgets"  # Use a safe table name so SQL sanitizing does not change it.
    writer.strategy = {"type": "natural_pk"}  # Match the strategy field that the log line reads.
    writer.timestamp = "2026-09-18T08:48:51+00:00"  # Pin the timestamp for exact log assertions.
    writer._database_path = lambda: str(tmp_path / "mist_data.db")  # Return a portable path for the log line.
    return writer  # Hand the prepared writer to the test.


def test_commit_and_verify_does_not_log_success_when_verification_fails(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """A verification failure must not leave a misleading write-success claim."""
    writer = _writer_for_verification_failure(tmp_path)  # Create a writer with a failing verification cursor.
    caplog.set_level(logging.DEBUG, logger="src.refactors.sqlite_database_writer")  # Capture module logs only.
    database_path = str(tmp_path / "mist_data.db")  # Compute the expected database path once for exact matches.
    intent_message = (  # Build the exact before-action message that must remain in the log.
        f"Committing 1/1 rows to table widgets in database {database_path} "
        "using natural_pk strategy at 2026-09-18T08:48:51+00:00"
    )
    verify_message = "Verifying row count for table widgets at 2026-09-18T08:48:51+00:00"  # Exact verify intent.
    success_message = (  # Build the exact success claim that must not appear after a verification failure.
        f"Successfully wrote 1/1 rows to table widgets in database {database_path} "
        "using natural_pk strategy at 2026-09-18T08:48:51+00:00"
    )

    with pytest.raises(sqlite3.Error, match="verification failed"):  # The proof step fails after commit.
        writer._commit_and_verify(1)  # Run the failure path under caplog.

    assert writer.connection.commit_called is True  # Prove the failure occurred after the commit action.
    assert ("INFO", intent_message) in _level_messages(caplog.records)  # Require the before-action log.
    assert ("INFO", verify_message) in _level_messages(caplog.records)  # Require the verification intent log.
    assert ("DEBUG", success_message) not in _level_messages(caplog.records)  # Reject an unproved success claim.


def _level_messages(records: list[logging.LogRecord]) -> list[tuple[str, str]]:
    """Return level/message pairs so tests can assert exact log evidence."""
    return [(record.levelname, record.getMessage()) for record in records]  # Preserve order for diagnostics.
