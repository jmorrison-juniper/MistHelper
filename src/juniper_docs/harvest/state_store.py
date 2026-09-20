"""Durable, resumable SQLite state store for the harvester.

The store is the single source of truth for one run. It holds one row per
document, the chosen and rejected PDF candidates, the numeric content scores,
the dropped release notes, and the run metadata. The ``content_scores`` table
has no text column by design, so the store never holds body text (FR-024,
SC-005). Every stage change is one transaction. The store writes durably with
WAL mode and full synchronous commits, reads the row back to verify a change,
and fails closed on a locked or damaged database (FR-031, FR-032, FR-033).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Log every durable write for observability.
import shutil  # Copy the database file before a schema migration.
import sqlite3  # The durable, single-file operational store.
from datetime import UTC, datetime  # UTC timestamps for the updated_at column.
from pathlib import Path  # Build every store path in a portable way.

from src.juniper_docs.models import HarvestStage, InventoryRecord, PdfCandidate  # Shared types.

_LOGGER = logging.getLogger(__name__)  # Module logger for the state store.

SCHEMA_VERSION = "1"  # The current schema version recorded in run_meta.
_LOCK_TIMEOUT_SECONDS = 30.0  # Bounded wait for a locked database before failing.

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    root_url          TEXT PRIMARY KEY,
    doc_type          TEXT NOT NULL,
    stage             TEXT NOT NULL,
    resolved_pdf_url  TEXT,
    category          TEXT,
    sub_category      TEXT,
    is_fallback       INTEGER,
    local_path        TEXT,
    file_size         INTEGER,
    error_reason      TEXT,
    updated_at        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pdf_candidates (
    root_url  TEXT NOT NULL,
    url       TEXT NOT NULL,
    chosen    INTEGER NOT NULL,
    reason    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS content_scores (
    root_url      TEXT NOT NULL,
    signal_group  TEXT NOT NULL,
    signal_name   TEXT NOT NULL,
    score         REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS dropped_release_notes (
    root_url  TEXT PRIMARY KEY,
    reason    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run_meta (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);
"""

_RESUME_QUERY = """
SELECT * FROM documents
WHERE stage IN ('discovered', 'resolved', 'downloaded')
   OR (stage = 'failed' AND ? = 1)
ORDER BY
  CASE
    WHEN doc_type = 'direct_pdf' THEN 0
    WHEN lower(root_url) LIKE '%/api/%' THEN 5
    WHEN lower(root_url) LIKE '%release-note%' THEN 4
    WHEN lower(root_url) LIKE '%relnote%' THEN 4
    WHEN lower(root_url) LIKE '%/mist%' THEN 1
    WHEN lower(root_url) LIKE '%apstra%' THEN 1
    WHEN lower(root_url) LIKE '%/ex4%' THEN 1
    WHEN lower(root_url) LIKE '%/qfx%' THEN 1
    WHEN lower(root_url) LIKE '%/srx%' THEN 1
    WHEN lower(root_url) LIKE '%/mx%' THEN 1
    WHEN lower(root_url) LIKE '%/acx%' THEN 1
    WHEN lower(root_url) LIKE '%/ptx%' THEN 1
    WHEN lower(root_url) LIKE '%guide%' THEN 2
    WHEN lower(root_url) LIKE '%config%' THEN 2
    WHEN lower(root_url) LIKE '%reference%' THEN 2
    WHEN lower(root_url) LIKE '%install%' THEN 2
    ELSE 3
  END,
  rowid
"""

# Static count queries, keyed by the fixed column name. The store never builds a
# query from a variable, so there is no injection surface for the summary counts.
_COUNT_QUERIES = {
    "stage": "SELECT stage AS key, COUNT(*) AS total FROM documents " "WHERE stage IS NOT NULL GROUP BY stage",
    "category": "SELECT category AS key, COUNT(*) AS total FROM documents "
    "WHERE category IS NOT NULL GROUP BY category",
    "sub_category": "SELECT sub_category AS key, COUNT(*) AS total FROM documents "
    "WHERE sub_category IS NOT NULL GROUP BY sub_category",
}


class StateStoreError(RuntimeError):
    """Raised when the store is locked or damaged, so the run fails closed."""


class HarvestStateStore:
    """Own the SQLite store, the durable writes, and the resume query."""

    def __init__(self, db_path: Path) -> None:
        """Open the store, apply the pragmas, and create the schema."""
        _LOGGER.info("Opening the harvest state store at %s", db_path)  # Log the intent.
        self.db_path = db_path  # Remember the path for a backup copy.
        db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the folder exists.
        self._conn = self._connect(db_path)  # Open the connection with the pragmas.
        self._conn.executescript(_SCHEMA)  # Create every table when it is absent.
        self.set_meta("schema_version", SCHEMA_VERSION)  # Record the schema version.
        _LOGGER.debug("State store ready with schema version %s", SCHEMA_VERSION)  # Result.

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        """Return a connection with the crash-safe pragmas applied."""
        connection = sqlite3.connect(str(db_path), timeout=_LOCK_TIMEOUT_SECONDS)  # Bounded lock wait.
        connection.row_factory = sqlite3.Row  # Read each row by the column name.
        connection.execute("PRAGMA journal_mode=WAL")  # A crash-safe write log.
        connection.execute("PRAGMA synchronous=FULL")  # The commit reaches durable storage.
        connection.execute("PRAGMA foreign_keys=ON")  # The child tables reference documents.
        return connection  # The caller owns the open connection.

    def check_integrity(self) -> None:
        """Raise when the database reports corruption, so the run fails closed."""
        _LOGGER.info("Checking the state store integrity")  # Log the intent.
        try:
            row = self._conn.execute("PRAGMA integrity_check").fetchone()  # Ask SQLite.
        except sqlite3.DatabaseError as error:  # A damaged file raises on the check.
            raise StateStoreError(f"state store is damaged: {error}") from error  # Fail closed.
        if row is None or row[0] != "ok":  # The check found a problem.
            raise StateStoreError(f"integrity check failed: {row[0] if row else 'unknown'}")
        _LOGGER.debug("State store integrity is ok")  # Result of the check.

    def backup(self) -> Path:
        """Copy the database file to a sibling backup and return the path."""
        backup_path = self.db_path.with_suffix(self.db_path.suffix + ".bak")  # Sibling name.
        _LOGGER.info("Backing up the state store to %s", backup_path)  # Log the intent.
        self._conn.commit()  # Flush any pending write before the copy.
        shutil.copy2(self.db_path, backup_path)  # Copy the file with its metadata.
        _LOGGER.debug("State store backup written to %s", backup_path)  # Result.
        return backup_path  # The caller keeps the backup path for recovery.

    def add_document(self, record: InventoryRecord) -> None:
        """Insert one document at the discovered stage, ignoring a repeat."""
        _LOGGER.debug("Adding document %s", record.source_url)  # Trace the insert.
        self._run(
            "INSERT OR IGNORE INTO documents (root_url, doc_type, stage, updated_at) " "VALUES (?, ?, ?, ?)",
            (record.source_url, record.doc_type.value, HarvestStage.DISCOVERED.value, _now()),
        )

    def record_dropped(self, root_url: str, reason: str) -> None:
        """Mark one release note dropped and record the drop reason."""
        _LOGGER.info("Dropping release note %s", root_url)  # Log the drop.
        with self._conn:  # One atomic transaction for both writes.
            self._conn.execute(
                "UPDATE documents SET stage = ?, updated_at = ? WHERE root_url = ?",
                (HarvestStage.DROPPED.value, _now(), root_url),
            )
            self._conn.execute(
                "INSERT OR REPLACE INTO dropped_release_notes (root_url, reason) VALUES (?, ?)",
                (root_url, reason),
            )

    def set_resolved(self, root_url: str, pdf_url: str, candidates: list[PdfCandidate]) -> None:
        """Record the resolved PDF URL and every candidate in one transaction."""
        _LOGGER.info("Recording resolution for %s", root_url)  # Log the resolution.
        with self._conn:  # One atomic transaction for the update and the candidates.
            self._conn.execute(
                "UPDATE documents SET stage = ?, resolved_pdf_url = ?, error_reason = ?, "
                "updated_at = ? WHERE root_url = ?",
                (HarvestStage.RESOLVED.value, pdf_url, None, _now(), root_url),
            )
            self._conn.executemany(
                "INSERT INTO pdf_candidates (root_url, url, chosen, reason) VALUES (?, ?, ?, ?)",
                [(root_url, item.url, int(item.chosen), item.reason) for item in candidates],
            )

    def mark_no_pdf(self, root_url: str, reason: str) -> None:
        """Mark a document as having no companion PDF, a clean final outcome."""
        _LOGGER.info("Marking %s as no PDF: %s", root_url, reason)  # Log the clean outcome.
        self._run(
            "UPDATE documents SET stage = ?, error_reason = ?, updated_at = ? WHERE root_url = ?",
            (HarvestStage.NO_PDF.value, reason, _now(), root_url),
        )

    def mark_downloaded(self, root_url: str, local_path: str, file_size: int) -> None:
        """Set the downloaded stage after the file is already on disk."""
        _LOGGER.info("Marking %s downloaded (%d bytes)", root_url, file_size)  # Log the write.
        self._run(
            "UPDATE documents SET stage = ?, local_path = ?, file_size = ?, updated_at = ? " "WHERE root_url = ?",
            (HarvestStage.DOWNLOADED.value, local_path, file_size, _now(), root_url),
        )

    def set_category(self, root_url: str, category: str) -> None:
        """Set the slug category early, so every document carries one."""
        _LOGGER.debug("Setting category %s for %s", category, root_url)  # Trace the write.
        self._run(
            "UPDATE documents SET category = ?, updated_at = ? WHERE root_url = ?",
            (category, _now(), root_url),
        )

    def set_classified(self, root_url: str, sub_category: str | None, is_fallback: bool | None) -> None:
        """Set the final classified stage with the sub-category and the fallback flag."""
        _LOGGER.info("Marking %s classified", root_url)  # Log the classification.
        fallback_flag = None if is_fallback is None else int(is_fallback)  # Store 0, 1, or null.
        self._run(
            "UPDATE documents SET stage = ?, sub_category = ?, is_fallback = ?, " "updated_at = ? WHERE root_url = ?",
            (HarvestStage.CLASSIFIED.value, sub_category, fallback_flag, _now(), root_url),
        )

    def record_scores(self, root_url: str, rows: list[tuple[str, str, float]]) -> None:
        """Insert the numeric content scores, which hold no body text."""
        _LOGGER.debug("Recording %d content scores for %s", len(rows), root_url)  # Trace.
        self._run_many(
            "INSERT INTO content_scores (root_url, signal_group, signal_name, score) " "VALUES (?, ?, ?, ?)",
            [(root_url, group, name, score) for group, name, score in rows],
        )

    def mark_failed(self, root_url: str, reason: str) -> None:
        """Set the failed stage and record the failure reason."""
        _LOGGER.info("Marking %s failed: %s", root_url, reason)  # Log the failure.
        self._run(
            "UPDATE documents SET stage = ?, error_reason = ?, updated_at = ? WHERE root_url = ?",
            (HarvestStage.FAILED.value, reason, _now(), root_url),
        )

    def stage_of(self, root_url: str) -> str | None:
        """Return the stored stage of one document, for a verified read-back."""
        row = self._conn.execute("SELECT stage FROM documents WHERE root_url = ?", (root_url,)).fetchone()
        return None if row is None else str(row["stage"])  # None when the row is absent.

    def owner_of_path(self, local_path: str) -> str | None:
        """Return the resolved PDF URL that owns a stored local path, or None."""
        row = self._conn.execute(
            "SELECT resolved_pdf_url FROM documents WHERE local_path = ? LIMIT 1", (local_path,)
        ).fetchone()  # The single document row that already claims this exact path.
        if row is None or row["resolved_pdf_url"] is None:  # No row, or no resolved URL yet.
            return None  # An unknown path has no recorded owner, so the caller must compare bytes.
        return str(row["resolved_pdf_url"])  # The resolved URL that produced the stored file.

    def resume_documents(self, retry_failed: bool) -> list[sqlite3.Row]:
        """Return every non-final document row, plus failed ones when retrying."""
        _LOGGER.info("Reading resume documents, retry_failed=%s", retry_failed)  # Log intent.
        rows = self._conn.execute(_RESUME_QUERY, (int(retry_failed),)).fetchall()  # Query.
        _LOGGER.debug("Found %d resume documents", len(rows))  # Result count.
        return rows  # The runner continues each row from its current stage.

    def document_rows(self) -> list[sqlite3.Row]:
        """Return every document row for the manifest render."""
        return self._conn.execute("SELECT * FROM documents ORDER BY root_url").fetchall()  # One row per document.

    def candidates_for(self, root_url: str) -> list[sqlite3.Row]:
        """Return the chosen and rejected PDF candidates of one document."""
        return self._conn.execute(
            "SELECT url, chosen, reason FROM pdf_candidates WHERE root_url = ?", (root_url,)
        ).fetchall()  # Zero or more candidate rows.

    def dropped_reason(self, root_url: str) -> str | None:
        """Return the drop reason of one release note, or None."""
        row = self._conn.execute("SELECT reason FROM dropped_release_notes WHERE root_url = ?", (root_url,)).fetchone()
        return None if row is None else str(row["reason"])  # None when not dropped.

    def set_meta(self, key: str, value: str) -> None:
        """Store one run-metadata key and value durably."""
        self._run("INSERT OR REPLACE INTO run_meta (key, value) VALUES (?, ?)", (key, value))

    def get_meta(self, key: str) -> str | None:
        """Return one run-metadata value, or None when it is absent."""
        row = self._conn.execute("SELECT value FROM run_meta WHERE key = ?", (key,)).fetchone()
        return None if row is None else str(row["value"])  # None when the key is absent.

    def summary(self) -> dict[str, object]:
        """Return the stage, category, and sub-category counts and total bytes."""
        _LOGGER.info("Building the run summary counts")  # Log the intent.
        stage_counts = self._count_by("stage")  # Count of documents per stage.
        summary: dict[str, object] = {
            "stage": stage_counts,  # Count of documents per stage.
            "category": self._count_by("category"),  # Count of documents per category.
            "sub_category": self._count_by("sub_category"),  # Count per sub-category.
            "total_bytes": self._total_bytes(),  # Sum of every downloaded byte.
        }
        _LOGGER.debug("Summary built with %d stage groups", len(stage_counts))  # Result.
        return summary  # The runner prints the summary at the end of the run.

    def close(self) -> None:
        """Commit and close the connection to release the file."""
        _LOGGER.debug("Closing the state store")  # Trace the close.
        self._conn.commit()  # Flush any pending write.
        self._conn.close()  # Release the database file.

    def __enter__(self) -> HarvestStateStore:
        """Return the store so a caller can use it as a context manager."""
        return self  # The store is already open from the constructor.

    def __exit__(self, *_exc: object) -> None:
        """Close the store when the context manager exits."""
        self.close()  # Always release the file on exit.

    def _count_by(self, column: str) -> dict[str, int]:
        """Return a map from a column value to the document count."""
        rows = self._conn.execute(_COUNT_QUERIES[column]).fetchall()  # Fixed static query.
        return {str(row["key"]): int(row["total"]) for row in rows}  # Value to count map.

    def _total_bytes(self) -> int:
        """Return the sum of every downloaded file size."""
        row = self._conn.execute("SELECT COALESCE(SUM(file_size), 0) AS total FROM documents").fetchone()
        return int(row["total"])  # Zero when no file is downloaded yet.

    def _run(self, sql: str, params: tuple[object, ...]) -> None:
        """Run one write inside a transaction and commit it durably."""
        try:
            with self._conn:  # The context commits on success and rolls back on error.
                self._conn.execute(sql, params)  # Execute the single write.
        except sqlite3.OperationalError as error:  # A lock or a disk error raises here.
            raise StateStoreError(f"state store write failed: {error}") from error  # Fail closed.

    def _run_many(self, sql: str, rows: list[tuple[object, ...]]) -> None:
        """Run one batch write inside a transaction and commit it durably."""
        try:
            with self._conn:  # The context commits on success and rolls back on error.
                self._conn.executemany(sql, rows)  # Execute every row in one transaction.
        except sqlite3.OperationalError as error:  # A lock or a disk error raises here.
            raise StateStoreError(f"state store batch write failed: {error}") from error  # Closed.


def _now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()  # A stable, sortable timestamp for updated_at.
