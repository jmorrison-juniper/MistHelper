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
import sqlite3  # The durable, single-file operational store.
from collections.abc import Sequence
from datetime import UTC, datetime  # UTC timestamps for the updated_at column.
from pathlib import Path  # Build every store path in a portable way.
from urllib.parse import urlsplit

from src.juniper_docs.acquire.pdf_paths import ContentRecord, PdfPathAllocator
from src.juniper_docs.models import ContentAnalysisResult, HarvestStage, InventoryRecord, PdfCandidate

_LOGGER = logging.getLogger(__name__)  # Module logger for the state store.

SCHEMA_VERSION = "2"
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
    updated_at        TEXT NOT NULL,
    content_sha256    TEXT,
    original_pdf_name TEXT
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
CREATE TABLE IF NOT EXISTS content_cache (
    corpus_root    TEXT NOT NULL,
    local_path     TEXT NOT NULL,
    content_sha256 TEXT NOT NULL CHECK (
        length(content_sha256) = 64 AND content_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    file_size      INTEGER NOT NULL CHECK (file_size > 0),
    device         INTEGER NOT NULL CHECK (device >= 0),
    inode          INTEGER NOT NULL CHECK (inode > 0),
    mtime_ns       INTEGER NOT NULL,
    ctime_ns       INTEGER NOT NULL,
    PRIMARY KEY (corpus_root, local_path)
);
CREATE INDEX IF NOT EXISTS content_cache_digest
    ON content_cache (corpus_root, content_sha256);
CREATE INDEX IF NOT EXISTS documents_pdf_url ON documents (resolved_pdf_url);
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
        try:
            self._initialize_schema()
        except StateStoreError:
            _LOGGER.exception("Cannot initialize the harvest state schema")
            self._conn.close()
            raise
        except (sqlite3.DatabaseError, OSError) as error:
            _LOGGER.exception("Cannot initialize the harvest state schema")
            self._conn.close()
            raise StateStoreError("Cannot initialize the harvest state schema.") from error
        _LOGGER.debug("State store ready with schema version %s", SCHEMA_VERSION)  # Result.

    def _initialize_schema(self) -> None:
        """Back up recognized legacy state and migrate through one transaction."""
        tables = {str(row[0]) for row in self._conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        version = self.get_meta("schema_version") if "run_meta" in tables else None
        if tables and version not in ("1", SCHEMA_VERSION):
            raise StateStoreError("The harvest state has an unknown schema version.")
        if version == SCHEMA_VERSION:
            self._validate_schema()
            return
        if version == "1":
            self._validate_legacy_schema(tables)
            self.backup()
        self._create_schema(version)
        self._validate_schema()
        _LOGGER.debug("Created and verified harvest schema version %s", SCHEMA_VERSION)

    def _create_schema(self, version: str | None) -> None:
        """Apply every additive declaration and the version in one transaction."""
        _LOGGER.info("Creating harvest schema version %s", SCHEMA_VERSION)
        self._conn.execute("BEGIN IMMEDIATE")
        with self._conn:
            if version == "1":
                self._conn.execute("ALTER TABLE documents ADD COLUMN content_sha256 TEXT")
                self._conn.execute("ALTER TABLE documents ADD COLUMN original_pdf_name TEXT")
            for statement in _SCHEMA.split(";"):
                if statement.strip():
                    self._conn.execute(statement)
            self._conn.execute(
                "INSERT OR REPLACE INTO run_meta (key, value) VALUES ('schema_version', ?)", (SCHEMA_VERSION,)
            )

    def _validate_legacy_schema(self, tables: set[str]) -> None:
        """Reject incompatible legacy input before backup or migration writes."""
        legacy = self._schema_columns("PRAGMA table_info(documents)")
        expected = self._document_columns()
        expected.pop("content_sha256")
        expected.pop("original_pdf_name")
        if legacy != expected or not {"pdf_candidates", "content_scores", "dropped_release_notes"}.issubset(tables):
            raise StateStoreError("The legacy harvest schema is incomplete or incompatible.")

    def _validate_schema(self) -> None:
        """Reject an incomplete current schema instead of repairing it silently."""
        documents = self._schema_columns("PRAGMA table_info(documents)")
        cache = self._schema_columns("PRAGMA table_info(content_cache)")
        if documents != self._document_columns() or cache != self._cache_columns():
            _LOGGER.error("The schema check read %d document columns and %d cache columns.", len(documents), len(cache))
            raise StateStoreError("The current harvest schema is incomplete or incompatible.")
        if self._read_committed("SELECT value FROM run_meta WHERE key = 'schema_version'", ())[0][0] != SCHEMA_VERSION:
            raise StateStoreError("The committed schema version differs from the required version.")
        _LOGGER.debug("The schema check verified %d document columns and %d cache columns.", len(documents), len(cache))

    def _schema_columns(self, statement: str) -> dict[str, tuple[str, int, int]]:
        """Read exact declarations and reject unexpected defaults."""
        rows = self._conn.execute(statement).fetchall()
        if any(row["dflt_value"] is not None for row in rows):
            raise StateStoreError("A harvest schema column has an incompatible default.")
        return {str(row["name"]): (str(row["type"]).upper(), int(row["notnull"]), int(row["pk"])) for row in rows}

    @staticmethod
    def _document_columns() -> dict[str, tuple[str, int, int]]:
        """Describe the unchanged natural key and additive nullable fields."""
        return {
            "root_url": ("TEXT", 0, 1),
            "doc_type": ("TEXT", 1, 0),
            "stage": ("TEXT", 1, 0),
            "resolved_pdf_url": ("TEXT", 0, 0),
            "category": ("TEXT", 0, 0),
            "sub_category": ("TEXT", 0, 0),
            "is_fallback": ("INTEGER", 0, 0),
            "local_path": ("TEXT", 0, 0),
            "file_size": ("INTEGER", 0, 0),
            "error_reason": ("TEXT", 0, 0),
            "updated_at": ("TEXT", 1, 0),
            "content_sha256": ("TEXT", 0, 0),
            "original_pdf_name": ("TEXT", 0, 0),
        }

    @staticmethod
    def _cache_columns() -> dict[str, tuple[str, int, int]]:
        """Describe the scoped natural path key and reliable identity fields."""
        return {
            "corpus_root": ("TEXT", 1, 1),
            "local_path": ("TEXT", 1, 2),
            "content_sha256": ("TEXT", 1, 0),
            "file_size": ("INTEGER", 1, 0),
            "device": ("INTEGER", 1, 0),
            "inode": ("INTEGER", 1, 0),
            "mtime_ns": ("INTEGER", 1, 0),
            "ctime_ns": ("INTEGER", 1, 0),
        }

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        """Return a connection with the crash-safe pragmas applied."""
        connection = sqlite3.connect(str(db_path), timeout=_LOCK_TIMEOUT_SECONDS)  # Bounded lock wait.
        connection.row_factory = sqlite3.Row  # Read each row by the column name.
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'run_meta'").fetchone():
            version = connection.execute("SELECT value FROM run_meta WHERE key = 'schema_version'").fetchone()
            if version is None or version[0] not in ("1", SCHEMA_VERSION):
                connection.close()
                raise StateStoreError("The harvest state has an unknown schema version.")
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
        backup_path = self.db_path.with_suffix(self.db_path.suffix + ".bak")
        if backup_path.exists():
            stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
            backup_path = backup_path.with_name(f"{backup_path.name}.{stamp}")
        _LOGGER.info("Backing up the state store to %s", backup_path)  # Log the intent.
        self._conn.commit()
        destination = sqlite3.connect(str(backup_path))
        try:
            self._conn.backup(destination)  # Include committed WAL pages, not only the main database file.
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise StateStoreError("The harvest state backup failed its integrity check.")
        finally:
            destination.close()
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
                "updated_at = ?, original_pdf_name = ? WHERE root_url = ?",
                (HarvestStage.RESOLVED.value, pdf_url, None, _now(), self._original_name(pdf_url), root_url),
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
            "UPDATE documents SET stage = ?, local_path = ?, file_size = ?, updated_at = ?, "
            "error_reason = NULL WHERE root_url = ?",
            (HarvestStage.DOWNLOADED.value, local_path, file_size, _now(), root_url),
        )
        rows = self._read_committed(
            "SELECT stage, local_path, file_size FROM documents WHERE root_url = ?", (root_url,)
        )
        if not rows or tuple(rows[0]) != (HarvestStage.DOWNLOADED.value, local_path, file_size):
            raise StateStoreError("The downloaded document did not match its committed state.")

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

    def content_rows(self, corpus_root: str) -> list[sqlite3.Row]:
        """Read complete cached identities for one real corpus root."""
        self._check_root(corpus_root)
        rows = self._conn.execute(
            "SELECT * FROM content_cache WHERE corpus_root = ? ORDER BY local_path", (corpus_root,)
        ).fetchall()
        _LOGGER.debug("Read %d cached corpus paths", len(rows))
        return rows

    def content_record(self, corpus_root: str, local_path: str) -> ContentRecord | None:
        """Read one current identity without scanning other corpus metadata."""
        self._check_root(corpus_root)
        row = self._conn.execute(
            "SELECT content_sha256, file_size, device, inode, mtime_ns, ctime_ns FROM content_cache "
            "WHERE corpus_root = ? AND local_path = ?",
            (corpus_root, local_path),
        ).fetchone()
        if row is None:
            return None
        return self._content_from_row(row)

    @staticmethod
    def _content_from_row(row: sqlite3.Row) -> ContentRecord:
        """Reject malformed cache input instead of coercing its identity fields."""
        digest = row["content_sha256"]
        identity = (row["file_size"], row["device"], row["inode"], row["mtime_ns"], row["ctime_ns"])
        if any(type(value) is not int for value in identity):
            raise StateStoreError("A cached corpus identity has invalid field types.")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise StateStoreError("A cached corpus digest is invalid.")
        if identity[0] <= 0 or identity[1] < 0 or identity[2] <= 0:
            raise StateStoreError("A cached corpus file identity is unreliable.")
        return digest, identity

    def paths_for_digest(self, corpus_root: str, digest: str) -> list[str]:
        """Find moved cached paths through the existing nonunique digest index."""
        self._check_root(corpus_root)
        rows = self._conn.execute(
            "SELECT local_path FROM content_cache WHERE corpus_root = ? AND content_sha256 = ? ORDER BY local_path",
            (corpus_root, digest),
        ).fetchall()
        return [str(row[0]) for row in rows]

    def associations_for_url(self, pdf_url: str) -> list[sqlite3.Row]:
        """Read current natural URL pointers after another path consumer moves a file."""
        return self._conn.execute(
            "SELECT local_path, content_sha256 FROM documents "
            "WHERE resolved_pdf_url = ? AND local_path IS NOT NULL ORDER BY root_url",
            (pdf_url,),
        ).fetchall()

    def cache_content(self, corpus_root: str, local_path: str, record: ContentRecord) -> None:
        """Persist a verified file identity with an independent read-back."""
        _LOGGER.info("Recording 1 verified corpus file")
        self._check_root(corpus_root)
        self._run(self._cache_sql(), self._cache_values(corpus_root, local_path, record))
        self._verify_content(corpus_root, local_path, record)
        _LOGGER.debug("Recorded and verified 1 corpus file")

    def forget_content(self, corpus_root: str, local_path: str) -> None:
        """Discard stale cache metadata without deleting any payload."""
        _LOGGER.info("Removing stale metadata for 1 corpus path")
        self._run("DELETE FROM content_cache WHERE corpus_root = ? AND local_path = ?", (corpus_root, local_path))
        _LOGGER.debug("Removed stale metadata for 1 corpus path")

    def adopt_content(self, root_url: str, digest: str) -> None:
        """Adopt validated legacy bytes without changing their prior history."""
        _LOGGER.info("Recording a validated legacy document digest")
        source = self._conn.execute("SELECT resolved_pdf_url FROM documents WHERE root_url = ?", (root_url,)).fetchone()
        if source is None or source[0] is None:
            raise StateStoreError("A legacy payload has no recorded resolved PDF URL.")
        self._run(
            "UPDATE documents SET content_sha256 = ?, original_pdf_name = COALESCE(original_pdf_name, ?) "
            "WHERE root_url = ? AND content_sha256 IS NULL",
            (digest, self._original_name(str(source[0])), root_url),
        )
        rows = self._read_committed("SELECT content_sha256 FROM documents WHERE root_url = ?", (root_url,))
        if not rows or rows[0][0] != digest:
            raise StateStoreError("The legacy document digest did not match its committed state.")
        _LOGGER.debug("Recorded and verified 1 legacy document digest")

    def associate_content(
        self, corpus_root: str, local_path: str, pdf_url: str, record: ContentRecord
    ) -> list[sqlite3.Row]:
        """Bind natural URL rows and repair every alias of the verified digest."""
        _LOGGER.info("Associating verified content with corpus URL records")
        self._check_root(corpus_root)
        query = "SELECT * FROM documents WHERE resolved_pdf_url = ? OR content_sha256 = ? ORDER BY root_url"
        parameters = (pdf_url, record[0])
        roots = {str(row["root_url"]) for row in self._conn.execute(query, parameters)}
        if not roots:
            raise StateStoreError("A corpus download has no recorded natural source URL.")
        self._commit_association(corpus_root, local_path, parameters, record)
        rows = self._verify_associations(query, parameters, roots, (local_path, record[1][0], record[0]))
        self._verify_content(corpus_root, local_path, record)
        _LOGGER.debug("Associated and verified %d natural URL records", len(rows))
        return rows

    def _commit_association(
        self, corpus_root: str, local_path: str, parameters: tuple[str, str], record: ContentRecord
    ) -> None:
        """Commit cache identity and all selected natural URL pointers together."""
        try:
            with self._conn:
                self._conn.execute(self._cache_sql(), self._cache_values(corpus_root, local_path, record))
                self._conn.execute(
                    "UPDATE documents SET local_path = ?, file_size = ?, content_sha256 = ?, updated_at = ? "
                    "WHERE (resolved_pdf_url = ? OR content_sha256 = ?) "
                    "AND (local_path IS NOT ? OR file_size IS NOT ? OR content_sha256 IS NOT ?)",
                    (local_path, record[1][0], record[0], _now(), *parameters, local_path, record[1][0], record[0]),
                )
        except sqlite3.DatabaseError as error:
            _LOGGER.exception("Cannot commit the corpus content association")
            raise StateStoreError("The corpus content association failed.") from error

    def relocate_content(self, corpus_root: str, source: str, final: str, record: ContentRecord) -> None:
        """Update every path alias and its cache after one physical move."""
        _LOGGER.info("Recording a canonical corpus placement")
        roots = {
            str(row[0])
            for row in self._conn.execute("SELECT root_url FROM documents WHERE local_path IN (?, ?)", (source, final))
        }
        try:
            with self._conn:
                self._relocate_rows(corpus_root, source, final, record)
        except sqlite3.DatabaseError as error:
            _LOGGER.exception("Cannot commit the corpus placement")
            raise StateStoreError("The corpus placement state transaction failed.") from error
        query = "SELECT * FROM documents WHERE local_path = ? ORDER BY root_url"
        self._verify_associations(query, (final,), roots, (final, record[1][0], record[0]))
        self._verify_content(corpus_root, final, record)
        _LOGGER.debug("Recorded placement for %d natural URL records", len(roots))

    def reclassify_document(self, root_url: str, result: ContentAnalysisResult, source: str, final: str) -> None:
        """Commit the intended label and every affected physical path together."""
        _LOGGER.info("Recording a corpus reclassification")
        record = self._file_record(Path(final))
        with self._conn:
            self._relocate_rows(str(self.db_path.parent.resolve()), source, final, record)
            self._conn.execute(
                "UPDATE documents SET sub_category = ?, is_fallback = ?, updated_at = ? WHERE root_url = ?",
                (result.sub_category, int(result.is_fallback), _now(), root_url),
            )
            self._conn.execute("DELETE FROM content_scores WHERE root_url = ?", (root_url,))
            rows = [(root_url, *key.split(":", 1), score) for key, score in result.scores.items()]
            self._conn.executemany(
                "INSERT INTO content_scores (root_url, signal_group, signal_name, score) VALUES (?, ?, ?, ?)", rows
            )
        reading = self._read_committed(
            "SELECT sub_category, is_fallback, local_path FROM documents WHERE root_url = ?", (root_url,)
        )
        if not reading or tuple(reading[0]) != (result.sub_category, int(result.is_fallback), final):
            raise StateStoreError("The reclassification did not match its committed state.")
        _LOGGER.debug("Recorded and verified 1 corpus reclassification")

    def path_is_shared(self, local_path: str) -> bool:
        """Return whether several source rows depend on one canonical path."""
        row = self._conn.execute("SELECT COUNT(*) FROM documents WHERE local_path = ?", (local_path,)).fetchone()
        return int(row[0]) > 1

    def placement_is_recorded(self, local_path: str) -> bool:
        """Distinguish a committed placement from a failed transaction before rollback."""
        row = self._conn.execute("SELECT COUNT(*) FROM documents WHERE local_path = ?", (local_path,)).fetchone()
        return int(row[0]) > 0

    def require_recovery(self, root_url: str) -> None:
        """Reprocess a final document whose expected payload is no longer valid."""
        _LOGGER.warning("A completed corpus document needs payload recovery")
        self._run(
            "UPDATE documents SET stage = ?, error_reason = ?, updated_at = ? WHERE root_url = ?",
            (HarvestStage.RESOLVED.value, "The canonical payload needs recovery.", _now(), root_url),
        )

    def _relocate_rows(self, corpus_root: str, source: str, final: str, record: ContentRecord) -> None:
        """Apply path metadata inside the caller's state transaction."""
        self._check_root(corpus_root)
        expected = {
            str(row[0])
            for row in self._conn.execute(
                "SELECT DISTINCT content_sha256 FROM documents WHERE local_path = ? AND content_sha256 IS NOT NULL",
                (source,),
            )
        }
        if expected and expected != {record[0]}:
            raise StateStoreError("The moved payload differs from its recorded content identity.")
        self._conn.execute(self._cache_sql(), self._cache_values(corpus_root, final, record))
        self._conn.execute(
            "UPDATE documents SET local_path = ?, file_size = ?, content_sha256 = ?, updated_at = ? "
            "WHERE local_path = ? AND (local_path IS NOT ? OR file_size IS NOT ? OR content_sha256 IS NOT ?)",
            (final, record[1][0], record[0], _now(), source, final, record[1][0], record[0]),
        )
        if Path(source).resolve() != Path(final).resolve():
            self._conn.execute(
                "DELETE FROM content_cache WHERE corpus_root = ? AND local_path = ?",
                (corpus_root, str(Path(source).resolve())),
            )

    def _file_record(self, path: Path) -> ContentRecord:
        """Use a verified identity or stream this one moved file."""
        identity = PdfPathAllocator._identity(path)
        cached = self._conn.execute(
            "SELECT content_sha256, file_size, device, inode, mtime_ns, ctime_ns FROM content_cache "
            "WHERE corpus_root = ? AND local_path = ?",
            (str(self.db_path.parent.resolve()), str(path.resolve())),
        ).fetchone()
        if cached is not None:
            record = self._content_from_row(cached)
            if record[1] == identity:
                return record
        digest = PdfPathAllocator._digest_file(path)
        if PdfPathAllocator._identity(path) != identity:
            raise StateStoreError("The moved corpus file changed during validation.")
        return digest, identity

    def _verify_associations(
        self,
        query: str,
        parameters: tuple[object, ...],
        roots: set[str],
        expected: tuple[str, int, str],
    ) -> list[sqlite3.Row]:
        """Compare the exact committed aliases through a fresh connection."""
        rows = self._read_committed(query, parameters)
        found = {str(row["root_url"]) for row in rows}
        if found != roots:
            raise StateStoreError("The committed corpus alias set differs from the expected source URLs.")
        for row in rows:
            if (
                str(row["root_url"]) in roots
                and (row["local_path"], row["file_size"], row["content_sha256"]) != expected
            ):
                raise StateStoreError("A committed corpus alias differs from its verified payload.")
        return rows

    def _verify_content(self, corpus_root: str, local_path: str, record: ContentRecord) -> None:
        """Compare all persisted identity fields through a fresh connection."""
        rows = self._read_committed(
            "SELECT content_sha256, file_size, device, inode, mtime_ns, ctime_ns FROM content_cache "
            "WHERE corpus_root = ? AND local_path = ?",
            (corpus_root, str(Path(local_path).resolve())),
        )
        if not rows or tuple(rows[0]) != (record[0], *record[1]):
            raise StateStoreError("The committed corpus cache differs from its verified file identity.")

    def _read_committed(self, query: str, parameters: Sequence[object]) -> list[sqlite3.Row]:
        """Read independent durable state, including committed WAL records."""
        connection = sqlite3.connect(f"{self.db_path.resolve().as_uri()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            return connection.execute(query, parameters).fetchall()
        except sqlite3.DatabaseError as error:
            _LOGGER.exception("Cannot verify committed harvest state")
            raise StateStoreError("The committed harvest state cannot be verified.") from error
        finally:
            connection.close()

    def _check_root(self, corpus_root: str) -> None:
        """Keep the cache scoped to the real directory of this state store."""
        if Path(corpus_root).resolve() != self.db_path.parent.resolve():
            raise StateStoreError("The content cache belongs to another corpus root.")

    @staticmethod
    def _cache_values(corpus_root: str, local_path: str, record: ContentRecord) -> tuple[object, ...]:
        """Serialize the natural path key and complete stat identity."""
        path = Path(local_path).resolve()
        if not path.is_relative_to(Path(corpus_root)):
            raise StateStoreError("The content cache path is outside its corpus root.")
        return corpus_root, str(path), record[0], *record[1]

    @staticmethod
    def _cache_sql() -> str:
        """Return a fixed upsert for the existing operational store."""
        return (
            "INSERT INTO content_cache "
            "(corpus_root, local_path, content_sha256, file_size, device, inode, mtime_ns, ctime_ns) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(corpus_root, local_path) DO UPDATE SET "
            "content_sha256 = excluded.content_sha256, file_size = excluded.file_size, "
            "device = excluded.device, inode = excluded.inode, "
            "mtime_ns = excluded.mtime_ns, ctime_ns = excluded.ctime_ns"
        )

    @staticmethod
    def _original_name(pdf_url: str) -> str:
        """Keep the original URL basename, not a canonical collision name."""
        return urlsplit(pdf_url).path.rsplit("/", 1)[-1]

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
        """Count each recorded physical path once instead of once per alias."""
        rows = self._conn.execute("SELECT local_path, file_size FROM documents WHERE local_path IS NOT NULL")
        sizes: dict[Path, int] = {}
        for row in rows:
            path = Path(str(row["local_path"])).resolve()
            size = row["file_size"]
            if type(size) is not int or size <= 0:
                raise StateStoreError("A recorded canonical path has no valid byte count.")
            if path in sizes and sizes[path] != size:
                raise StateStoreError("Source aliases disagree about a canonical byte count.")
            sizes[path] = size
        return sum(sizes.values())

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
