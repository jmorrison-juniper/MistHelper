"""Prove additive natural-key migration and required durable content receipts."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from src.juniper_docs.acquire.downloader import CorpusDownloader
from src.juniper_docs.acquire.pdf_paths import PdfPathAllocator
from src.juniper_docs.harvest.state_store import HarvestStateStore, StateStoreError
from tests.unit.juniper_docs.conftest import FakeCatalogClient

if TYPE_CHECKING:
    from tests.unit.juniper_docs.canonical.conftest import SmallCorpusHarness

_LEGACY_SCHEMA = """
CREATE TABLE documents (
    root_url TEXT PRIMARY KEY, doc_type TEXT NOT NULL, stage TEXT NOT NULL,
    resolved_pdf_url TEXT, category TEXT, sub_category TEXT, is_fallback INTEGER,
    local_path TEXT, file_size INTEGER, error_reason TEXT, updated_at TEXT NOT NULL
);
CREATE TABLE pdf_candidates (root_url TEXT NOT NULL, url TEXT NOT NULL, chosen INTEGER NOT NULL, reason TEXT NOT NULL);
CREATE TABLE content_scores (
    root_url TEXT NOT NULL, signal_group TEXT NOT NULL, signal_name TEXT NOT NULL, score REAL NOT NULL
);
CREATE TABLE dropped_release_notes (root_url TEXT PRIMARY KEY, reason TEXT NOT NULL);
CREATE TABLE run_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


class LegacyState:
    """Construct original version-1 records, including committed WAL pages."""

    def __init__(self, path: Path) -> None:
        """Create the old schema without importing the new schema declaration."""
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path))
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(_LEGACY_SCHEMA)
        self.connection.executemany(
            "INSERT INTO run_meta VALUES (?, ?)",
            [("schema_version", "1"), ("discovery_complete", "1"), ("source", "all")],
        )
        self.seed()

    def seed(self) -> None:
        """Populate every old table with distinct original metadata."""
        root = "https://example.test/legacy/"
        self.connection.execute(
            "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                root,
                "html_root",
                "classified",
                root + "original.pdf",
                "uncategorized",
                "routing",
                0,
                str(self.path.parent / "old" / "original.pdf"),
                17,
                "Prior reason.",
                "2026-01-02T03:04:05+00:00",
            ),
        )
        self.connection.executemany(
            "INSERT INTO pdf_candidates VALUES (?, ?, ?, ?)",
            [(root, root + "original.pdf", 1, "chosen"), (root, root + "other.pdf", 0, "rejected")],
        )
        self.connection.execute("INSERT INTO content_scores VALUES (?, ?, ?, ?)", (root, "technology", "routing", 0.75))
        self.connection.execute(
            "INSERT INTO dropped_release_notes VALUES (?, ?)", ("https://example.test/old/", "superseded")
        )
        self.connection.commit()

    def snapshot(self) -> dict[str, list[tuple[object, ...]]]:
        """Read every original table before and after the migration."""
        names = ("documents", "pdf_candidates", "content_scores", "dropped_release_notes", "run_meta")
        return {name: self.connection.execute(f"SELECT * FROM {name} ORDER BY rowid").fetchall() for name in names}

    def close(self) -> None:
        """Release the original WAL connection."""
        self.connection.close()


class TestSchemaMigration:
    """Compare complete old values and required recovery artifacts."""

    def test_version_one_migration_preserves_all_legacy_values_and_wal(self, tmp_path: Path) -> None:
        """The backup and migration retain every natural key and old field."""
        legacy = LegacyState(tmp_path / "corpus" / "harvest_state.db")
        before = legacy.snapshot()
        with HarvestStateStore(legacy.path) as store:
            assert store.get_meta("schema_version") == "2"
            assert store.content_rows(str(legacy.path.parent.resolve())) == []
            migrated = tuple(store.document_rows()[0])
            assert migrated[:11] == before["documents"][0]
            assert migrated[11:] == (None, None)
        after = legacy.snapshot()
        for name in ("pdf_candidates", "content_scores", "dropped_release_notes"):
            assert after[name] == before[name]
        assert dict(after["run_meta"]) == {**dict(before["run_meta"]), "schema_version": "2"}
        backup = legacy.path.with_suffix(".db.bak")
        with closing(sqlite3.connect(str(backup))) as recovered:
            for name, expected in before.items():
                assert recovered.execute(f"SELECT * FROM {name} ORDER BY rowid").fetchall() == expected
            assert recovered.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        legacy.close()

    def test_repeat_open_does_not_create_another_backup(self, tmp_path: Path) -> None:
        """An unchanged version-2 store preserves rows and its single backup."""
        legacy = LegacyState(tmp_path / "harvest_state.db")
        with HarvestStateStore(legacy.path) as store:
            before = [dict(row) for row in store.document_rows()]
        with HarvestStateStore(legacy.path) as repeated:
            assert [dict(row) for row in repeated.document_rows()] == before
        assert len(list(tmp_path.glob("harvest_state.db.bak*"))) == 1
        legacy.close()

    def test_existing_backup_is_not_overwritten(self, tmp_path: Path) -> None:
        """A required migration creates a new backup without replacing an old one."""
        legacy = LegacyState(tmp_path / "harvest_state.db")
        previous = tmp_path / "harvest_state.db.bak"
        previous.write_bytes(b"Original unrelated recovery artifact.")
        with HarvestStateStore(legacy.path) as store:
            assert store.get_meta("schema_version") == "2"
        backups = list(tmp_path.glob("harvest_state.db.bak*"))
        assert len(backups) == 2
        assert previous.read_bytes() == b"Original unrelated recovery artifact."
        new_backup = next(path for path in backups if path != previous)
        with closing(sqlite3.connect(str(new_backup))) as recovered:
            assert recovered.execute("SELECT value FROM run_meta WHERE key = 'schema_version'").fetchone() == ("1",)
        legacy.close()

    @pytest.mark.parametrize("version", ["0", "3", "invalid", ""])
    def test_unknown_version_fails_before_schema_or_backup_writes(self, tmp_path: Path, version: str) -> None:
        """An unsupported version leaves the exact old values and columns intact."""
        legacy = LegacyState(tmp_path / "harvest_state.db")
        legacy.connection.execute("UPDATE run_meta SET value = ? WHERE key = 'schema_version'", (version,))
        legacy.connection.commit()
        before = legacy.snapshot()
        columns = legacy.connection.execute("PRAGMA table_info(documents)").fetchall()
        with pytest.raises(StateStoreError, match="unknown schema version"):
            HarvestStateStore(legacy.path)
        assert legacy.snapshot() == before
        assert legacy.connection.execute("PRAGMA table_info(documents)").fetchall() == columns
        assert list(tmp_path.glob("*.bak*")) == []
        legacy.close()

    def test_failed_second_alter_rolls_back_the_entire_migration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A rejected second column leaves neither new column nor a new version."""
        legacy = LegacyState(tmp_path / "harvest_state.db")
        before = legacy.snapshot()
        connection = sqlite3.connect(str(legacy.path))
        connection.row_factory = sqlite3.Row
        alterations: list[str] = []
        connection.set_authorizer(
            lambda action, _first, second, _database, _trigger: self._authorize(action, second, alterations)
        )
        monkeypatch.setattr(HarvestStateStore, "_connect", staticmethod(lambda _path: connection))
        with pytest.raises((sqlite3.DatabaseError, StateStoreError), match="authorized|initialize"):
            HarvestStateStore(legacy.path)
        assert len(alterations) == 2
        assert legacy.snapshot() == before
        assert [column[1] for column in legacy.connection.execute("PRAGMA table_info(documents)")][-1] == "updated_at"
        with closing(sqlite3.connect(str(tmp_path / "harvest_state.db.bak"))) as backup:
            assert backup.execute("SELECT value FROM run_meta WHERE key = 'schema_version'").fetchone() == ("1",)
        legacy.close()

    @staticmethod
    def _authorize(action: int, table: str | None, alterations: list[str]) -> int:
        """Reject one real SQLite DDL operation, not a mocked migration result."""
        if action == sqlite3.SQLITE_ALTER_TABLE:
            alterations.append(str(table))
            if len(alterations) == 2:
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK


class TestRequiredState:
    """Reject incomplete cache input and unverified durable associations."""

    def test_cache_uses_composite_natural_paths_and_all_identity_fields(self, tmp_path: Path) -> None:
        """A persisted cache row holds the exact real path and stat identity."""
        path = tmp_path / "document.pdf"
        payload = b"%PDF-1.4\nOriginal cache identity.\n"
        path.write_bytes(payload)
        record = (hashlib.sha256(payload).hexdigest(), PdfPathAllocator._identity(path))
        with HarvestStateStore(tmp_path / "harvest_state.db") as store:
            store.cache_content(str(tmp_path.resolve()), str(path), record)
            row = store.content_rows(str(tmp_path.resolve()))[0]
            assert tuple(row) == (str(tmp_path.resolve()), str(path.resolve()), record[0], *record[1])
            columns = store._conn.execute("PRAGMA table_info(content_cache)").fetchall()
            assert [(column["name"], column["pk"]) for column in columns if column["pk"]] == [
                ("corpus_root", 1),
                ("local_path", 2),
            ]
            assert {column["name"] for column in columns} == {
                "corpus_root",
                "local_path",
                "content_sha256",
                "file_size",
                "device",
                "inode",
                "mtime_ns",
                "ctime_ns",
            }

    def test_unregistered_url_cannot_report_a_durable_success(self, corpus: SmallCorpusHarness) -> None:
        """A stored payload without a natural source row produces a fatal state error."""
        url = "https://example.test/unregistered.pdf"
        corpus.client.payloads[url] = b"%PDF-1.4\nOriginal unregistered body.\n"
        with pytest.raises(StateStoreError, match="no recorded natural source URL"):
            corpus.downloader.download_document(url, corpus.root / "design")
        assert corpus.store.document_rows() == []
        assert corpus.client.requests == [url]
        assert corpus.payload_writes.call_count == 1
        assert (corpus.root / "design" / "unregistered.pdf").read_bytes() == corpus.client.payloads[url]

    def test_failed_cache_verification_is_not_a_success(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A real published file cannot hide a required read-back failure."""
        root, url = "https://example.test/source/", "https://example.test/verified.pdf"
        corpus.seed(root, url, "design")
        payload = b"%PDF-1.4\nOriginal verification body.\n"
        corpus.client.payloads[url] = payload
        query = corpus.store._read_committed
        with monkeypatch.context() as faults:
            faults.setattr(
                corpus.store,
                "_read_committed",
                lambda sql, parameters: [] if "FROM content_cache" in sql else query(sql, parameters),
            )
            with pytest.raises(StateStoreError, match="committed corpus cache"):
                corpus.downloader.download_document(url, corpus.root / "design")
        row = corpus.store.document_rows()[0]
        assert (row["stage"], row["local_path"], row["content_sha256"]) == ("resolved", None, None)
        assert (corpus.root / "design" / "verified.pdf").read_bytes() == payload
        assert corpus.payload_writes.call_count == 1

    def test_association_idempotency_preserves_all_source_metadata(self, corpus: SmallCorpusHarness) -> None:
        """A valid direct repeat changes no document value and makes no request."""
        root, url = "https://example.test/source/", "https://example.test/idempotent.pdf"
        corpus.seed(root, url, "design")
        corpus.client.payloads[url] = b"%PDF-1.4\nOriginal idempotent body.\n"
        result = corpus.downloader.download_document(url, corpus.root / "design")
        corpus.persist_success(root, result)
        before = [dict(row) for row in corpus.store.document_rows()]
        cached = [dict(row) for row in corpus.store.content_rows(str(corpus.root.resolve()))]
        repeated = corpus.downloader.download_document(url, corpus.root / "other")
        assert repeated == ("skipped", result[1], result[2], None)
        assert [dict(row) for row in corpus.store.document_rows()] == before
        assert [dict(row) for row in corpus.store.content_rows(str(corpus.root.resolve()))] == cached
        assert corpus.client.requests == [url]
        assert corpus.payload_writes.call_count == 1

    def test_required_write_failure_remains_fatal_and_retry_reuses_publication(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failed association leaves no completed row and no second payload write."""
        root, url = "https://example.test/source/", "https://example.test/recover.pdf"
        corpus.seed(root, url, "design")
        payload = b"%PDF-1.4\nOriginal state recovery body.\n"
        corpus.client.payloads[url] = payload
        with monkeypatch.context() as faults:
            faults.setattr(
                corpus.store, "associate_content", MagicMock(side_effect=StateStoreError("Synthetic store lock."))
            )
            with pytest.raises(StateStoreError, match="Synthetic store lock"):
                corpus.downloader.download_document(url, corpus.root / "design")
        before = corpus.store.document_rows()[0]
        assert (before["stage"], before["local_path"], before["content_sha256"]) == ("resolved", None, None)
        corpus.store.close()
        corpus.store = HarvestStateStore(corpus.root / "harvest_state.db")
        corpus.downloader = CorpusDownloader(
            corpus.client, corpus.root, PdfPathAllocator(corpus.store.owner_of_path, corpus.store)
        )
        result = corpus.downloader.download_document(url, corpus.root / "design")
        assert result == ("skipped", str(corpus.root / "design" / "recover.pdf"), len(payload), None)
        corpus.persist_success(root, result)
        assert corpus.store.stage_of(root) == "classified"
        assert corpus.payload_writes.call_count == 1
        assert corpus.client.requests == [url, url]


class TestLegacyContentAdoption:
    """Keep legacy source history while adopting only verified original bytes."""

    @pytest.mark.parametrize("valid_prefix", [True, False])
    def test_legacy_adoption_preserves_payload_and_exposes_invalid_prefixes(
        self, tmp_path: Path, valid_prefix: bool
    ) -> None:
        """A legacy digest requires a valid prefix and never removes the raw source."""
        legacy = LegacyState(tmp_path / "corpus" / "harvest_state.db")
        path = legacy.path.parent / "old" / "original.pdf"
        path.parent.mkdir()
        payload = b"%PDF-1.4\nOriginal legacy payload.\n" if valid_prefix else b"Original non-PDF raw source."
        path.write_bytes(payload)
        client = FakeCatalogClient()
        with HarvestStateStore(legacy.path) as store:
            downloader = CorpusDownloader(client, legacy.path.parent, PdfPathAllocator(store.owner_of_path, store))
            row = store.document_rows()[0]
            if valid_prefix:
                assert row["content_sha256"] == hashlib.sha256(payload).hexdigest()
                assert row["original_pdf_name"] == "original.pdf"
                assert downloader.download_document(str(row["resolved_pdf_url"]), legacy.path.parent / "other") == (
                    "skipped",
                    str(path),
                    len(payload),
                    None,
                )
                assert (row["stage"], row["sub_category"], row["is_fallback"], row["error_reason"]) == (
                    "classified",
                    "routing",
                    0,
                    "Prior reason.",
                )
            else:
                assert (row["stage"], row["content_sha256"], row["error_reason"]) == (
                    "failed",
                    None,
                    "The legacy local payload is not a PDF.",
                )
            assert path.read_bytes() == payload
            assert client.requests == []
            assert len(store.candidates_for("https://example.test/legacy/")) == 2
        legacy.close()

    def test_legacy_digest_requires_a_recorded_source(self, corpus: SmallCorpusHarness) -> None:
        """No anonymous row can receive a successful legacy digest."""
        with pytest.raises(StateStoreError, match="no recorded resolved PDF URL"):
            corpus.store.adopt_content("https://example.test/missing/", "a" * 64)
        assert corpus.store.document_rows() == []


class TestDurableGuardDecisions:
    """Test failure decisions against real SQLite rows and connections."""

    @pytest.mark.parametrize(
        ("record", "message"),
        [
            (("x", 10, 1, 1), "digest is invalid"),
            (("a" * 64, 10, 1.5, 1), "invalid field types"),
            (("a" * 64, 0, 1, 1), "identity is unreliable"),
        ],
    )
    def test_malformed_cache_input_fails_explicitly(
        self, record: tuple[str, int, int | float, int], message: str
    ) -> None:
        """Malformed fields cannot become a trusted identity through coercion."""
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(
                "SELECT ? AS content_sha256, ? AS file_size, ? AS device, ? AS inode, 1 AS mtime_ns, 1 AS ctime_ns",
                record,
            ).fetchone()
            with pytest.raises(StateStoreError, match=message):
                HarvestStateStore._content_from_row(row)
        finally:
            connection.close()

    def test_current_schema_cannot_silently_create_a_missing_cache(self, tmp_path: Path) -> None:
        """A current-version declaration with missing required input fails before repair."""
        path = tmp_path / "harvest_state.db"
        with HarvestStateStore(path):
            pass
        with closing(sqlite3.connect(str(path))) as connection:
            connection.execute("DROP TABLE content_cache")
        with pytest.raises(StateStoreError, match="incomplete or incompatible"):
            HarvestStateStore(path)
        with closing(sqlite3.connect(str(path))) as connection:
            assert connection.execute("SELECT name FROM sqlite_master WHERE name = 'content_cache'").fetchall() == []
            assert connection.execute("SELECT value FROM run_meta WHERE key = 'schema_version'").fetchone() == ("2",)

    def test_cache_scope_and_committed_alias_values_are_required(
        self, corpus: SmallCorpusHarness, tmp_path: Path
    ) -> None:
        """Wrong root, alias sets, and alias values produce distinct explicit failures."""
        root, url = "https://example.test/source/", "https://example.test/original.pdf"
        corpus.seed(root, url, "design")
        corpus.client.payloads[url] = b"%PDF original durable guard"
        result = corpus.downloader.download_document(url, corpus.root / "design")
        expected = (str(result[1]), int(result[2]), hashlib.sha256(corpus.client.payloads[url]).hexdigest())
        query = "SELECT * FROM documents WHERE root_url = ?"
        with pytest.raises(StateStoreError, match="another corpus root"):
            corpus.store.content_rows(str(tmp_path / "other"))
        with pytest.raises(StateStoreError, match="alias set differs"):
            corpus.store._verify_associations(query, (root,), {root, "missing"}, expected)
        with pytest.raises(StateStoreError, match="alias differs"):
            corpus.store._verify_associations(query, (root,), {root}, (expected[0], 999, expected[2]))
        assert corpus.store.document_rows()[0]["local_path"] == result[1]
        assert corpus.payload_writes.call_count == 1

    def test_independent_read_failure_is_fatal(
        self, corpus: SmallCorpusHarness, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unreadable independent query cannot become a verified receipt."""
        original = sqlite3.connect

        def blocked(*arguments: object, **options: object) -> sqlite3.Connection:
            connection = original(*arguments, **options)
            connection.set_authorizer(
                lambda action, _first, _second, _database, _trigger: (
                    sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ else sqlite3.SQLITE_OK
                )
            )
            return connection

        with monkeypatch.context() as faults:
            faults.setattr(sqlite3, "connect", blocked)
            with pytest.raises(StateStoreError, match="cannot be verified"):
                corpus.store._read_committed("SELECT root_url FROM documents", ())
        assert corpus.store.document_rows() == []

    def test_real_relocation_write_failure_rolls_back_every_pointer(self, corpus: SmallCorpusHarness) -> None:
        """A real SQLite write denial cannot change any canonical association."""
        root, url = "https://example.test/source/", "https://example.test/original.pdf"
        corpus.seed(root, url, "design")
        corpus.client.payloads[url] = b"%PDF original relocation guard"
        result = corpus.downloader.download_document(url, corpus.root / "design")
        source = Path(str(result[1]))
        final = source.with_name("other.pdf")
        final.write_bytes(source.read_bytes())
        before = [dict(row) for row in corpus.store.document_rows()]
        corpus.store._conn.set_authorizer(
            lambda action, _table, _column, _database, _trigger: (
                sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_UPDATE else sqlite3.SQLITE_OK
            )
        )
        try:
            with pytest.raises(StateStoreError, match="placement state transaction failed"):
                corpus.store.relocate_content(
                    str(corpus.root.resolve()), str(source), str(final), corpus.store._file_record(final)
                )
        finally:
            corpus.store._conn.set_authorizer(None)
        assert [dict(row) for row in corpus.store.document_rows()] == before
        assert source.read_bytes() == final.read_bytes() == corpus.client.payloads[url]


class TestAssociationAtomicity:
    """Prove real transaction failure and distinct URL update boundaries."""

    def test_actual_download_association_write_denial_has_no_successful_pointer(
        self, corpus: SmallCorpusHarness
    ) -> None:
        """A denied document update rolls back all natural URL associations."""
        root, url = "https://example.test/source/", "https://example.test/denied.pdf"
        corpus.seed(root, url, "design")
        payload = b"%PDF Original denied association"
        corpus.client.payloads[url] = payload
        corpus.store._conn.set_authorizer(
            lambda action, table, _column, _database, _trigger: (
                sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_UPDATE and table == "documents" else sqlite3.SQLITE_OK
            )
        )
        try:
            with pytest.raises(StateStoreError, match="content association failed"):
                corpus.downloader.download_document(url, corpus.root / "design")
        finally:
            corpus.store._conn.set_authorizer(None)
        row = corpus.store.document_rows()[0]
        assert (row["stage"], row["local_path"], row["content_sha256"]) == ("resolved", None, None)
        assert (corpus.root / "design" / "denied.pdf").read_bytes() == payload
        assert corpus.payload_writes.call_count == 1

    def test_changed_url_response_does_not_redirect_other_url_aliases(self, corpus: SmallCorpusHarness) -> None:
        """A changed response updates its URL group, not another URL's old digest."""
        roots = ("https://example.test/a/", "https://example.test/b/", "https://example.test/c/")
        urls = ("https://example.test/a/alpha.pdf", "https://example.test/b/beta.pdf")
        old, new = b"%PDF Original old response", b"%PDF Original new response"
        for root, url in zip(roots, (urls[0], urls[1], urls[0]), strict=True):
            corpus.seed(root, url, "design")
            corpus.client.payloads[url] = old
            corpus.persist_success(root, corpus.downloader.download_document(url, corpus.root / "design"))
        previous = corpus.root / "design" / "alpha.pdf"
        previous.write_bytes(b"%PDF External local corruption")
        corpus.client.payloads[urls[0]] = new
        result = corpus.downloader.download_document(urls[0], corpus.root / "design")
        final = previous.with_name(f"alpha-{PdfPathAllocator._short_hash(urls[0])}.pdf")
        assert result == ("downloaded", str(final), len(new), None)
        rows = {str(row["root_url"]): row for row in corpus.store.document_rows()}
        assert [(rows[root]["local_path"], rows[root]["content_sha256"]) for root in (roots[0], roots[2])] == [
            (str(final), hashlib.sha256(new).hexdigest())
        ] * 2
        assert (rows[roots[1]]["local_path"], rows[roots[1]]["content_sha256"]) == (
            str(previous),
            hashlib.sha256(old).hexdigest(),
        )
        assert final.read_bytes() == new
        assert previous.read_bytes() == b"%PDF External local corruption"
        assert corpus.client.requests == [*urls, urls[0]]

    def test_equivalent_path_spellings_count_once_and_conflicting_sizes_fail(self, corpus: SmallCorpusHarness) -> None:
        """The byte summary uses real path identity without hiding inconsistent metadata."""
        first, second = "https://example.test/a/", "https://example.test/b/"
        url = "https://example.test/shared.pdf"
        payload = b"%PDF Original byte summary"
        for root in (first, second):
            corpus.seed(root, url, "design")
        corpus.client.payloads[url] = payload
        corpus.downloader.download_document(url, corpus.root / "design")
        relative = str((corpus.root / "design" / "shared.pdf").relative_to(Path.cwd()))
        with corpus.store._conn:
            corpus.store._conn.execute("UPDATE documents SET local_path = ? WHERE root_url = ?", (relative, second))
        assert corpus.store.summary()["total_bytes"] == len(payload)
        with corpus.store._conn:
            corpus.store._conn.execute("UPDATE documents SET file_size = 999 WHERE root_url = ?", (second,))
        with pytest.raises(StateStoreError, match="disagree about a canonical byte count"):
            corpus.store.summary()
        with corpus.store._conn:
            corpus.store._conn.execute("UPDATE documents SET file_size = NULL WHERE root_url = ?", (second,))
        with pytest.raises(StateStoreError, match="no valid byte count"):
            corpus.store.summary()
