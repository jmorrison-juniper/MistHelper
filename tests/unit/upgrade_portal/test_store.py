"""Unit tests for the read-back verification of the upgrade capture store.

Why:
    The exporter reports success for a write that reached no database. The
    exporter skips the database outside a container
    (``src/export/data_exporter.py:134``), and the router returns a success
    envelope that carries zero written rows after a file fallback
    (``src/db/router.py:373``). That defect is issue 1824, and it stays open on
    purpose. The store works around the defect, because it reads every key back
    after a write. These tests prove that the read-back catches the false
    success, and that a driver field never raises a false alarm.

    Every test asserts on a ``REASON_`` constant, never on the message text. A
    message may change for Simplified Technical English at any time, and the
    reason code stays stable.

    No test opens a socket, a database connection, or a file. The fake handle
    and the fake exporter below hold every document in memory.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.capture import store

_KEY = "cap-0001"  # WHY: One capture key serves every test in this module.


class _FakeCollection:
    """One collection of a fake document store.

    Why:
        The read-back calls ``collection(name).get(key)``. A test must own that
        one call, so the test returns a document, returns nothing, or raises.
        A unit test runs with no container and no network.
    """

    def __init__(self) -> None:
        """Create an empty collection."""
        self.documents: dict[str, dict[str, Any]] = {}  # WHY: Holds each stored document by key.
        self.read_error: Exception | None = None  # WHY: A test sets this value to fail the read.

    def get(self, key: str) -> dict[str, Any] | None:
        """Return the stored document for one key.

        Args:
            key: The document key.

        Returns:
            The stored document, or None when the key is absent.

        Raises:
            Exception: The error that a test placed in ``read_error``.
        """
        if self.read_error is not None:
            raise self.read_error
        return self.documents.get(key)


class _FakeDatabase:
    """A fake database handle that holds one collection.

    Why:
        The store asks the handle for a collection by name. The fake records
        each name, so a test proves that a path read the database or skipped
        the database.
    """

    def __init__(self) -> None:
        """Create a handle that holds one empty collection."""
        self.fake_collection = _FakeCollection()  # WHY: Every name maps to this single store.
        self.requested_names: list[str] = []  # WHY: Records each collection that the store asked for.

    def collection(self, name: str) -> _FakeCollection:
        """Return the single fake collection.

        Args:
            name: The collection name.

        Returns:
            The fake collection.
        """
        self.requested_names.append(name)
        return self.fake_collection


@pytest.fixture(autouse=True)
def _drop_cached_handle() -> Iterator[None]:
    """Clear the cached database handle around every test.

    Why:
        The store caches one shared handle. A leaked handle makes a later test
        read a store that another test built, so each test starts and ends with
        an empty cache.

    Yields:
        None, after the cache is clear.
    """
    store.reset_connection()
    yield
    store.reset_connection()


def _written_capture() -> dict[str, Any]:
    """Return the capture document that the portal wrote.

    Why:
        Every test needs the same small document, so a difference in a result
        comes from the test and never from the input.

    Returns:
        A capture document with a business key and a schema version.
    """
    return {"capture_id": _KEY, "schema_version": store.SCHEMA_VERSION, "site_id": "site-0001", "ordinal": 1}


def _database_holding(document: dict[str, Any] | None) -> _FakeDatabase:
    """Return a fake handle that holds one document, or holds nothing.

    Why:
        The read-back has two ends. The database holds the document, or the
        database holds nothing. One builder covers both ends, so each test
        states its own case in a single line.

    Args:
        document: The document that the database holds. None leaves the
            database empty, which repeats the zero-row write of issue 1824.

    Returns:
        The fake handle.
    """
    database = _FakeDatabase()
    if document is not None:
        database.fake_collection.documents[_KEY] = document
    return database


def _install_exporter(monkeypatch: pytest.MonkeyPatch, mirror: _FakeDatabase | None) -> list[str]:
    """Replace the exporter with a stand-in that writes no file.

    Why:
        The real exporter writes a file under ``data/``, and it reports success
        even after it mirrored zero rows to the database. The stand-in repeats
        that success and mirrors only when a test asks for a mirror, so a test
        reproduces issue 1824 with no disk write.

    Args:
        monkeypatch: The pytest patch helper.
        mirror: The database that receives the mirrored document. None writes
            zero rows to the database and still reports success.

    Returns:
        The list that receives the name of each backup file.
    """
    names: list[str] = []

    def _write(rows: list[dict[str, Any]], filename: str, **options: Any) -> bool:
        """Record one backup file and mirror the payload when a database exists.

        Args:
            rows: The flat rows for the backup file. The stand-in ignores them.
            filename: The name of the backup file.
            **options: The exporter options. ``backend_options`` holds the raw
                document that the polyglot backend receives.

        Returns:
            True, because the real exporter reports success for every CSV write.
        """
        names.append(filename)
        if mirror is not None:
            payload = dict(options["backend_options"].raw_data[0])
            mirror.fake_collection.documents[str(payload["capture_id"])] = payload
        return True

    monkeypatch.setattr(store, "DataExporter", SimpleNamespace(write_with_format_selection=_write))
    return names


# ---------------------------------------------------------------------------
# verify_write: the read-back
# ---------------------------------------------------------------------------


def test_verify_write_accepts_a_matching_document() -> None:
    """The read-back verifies a document that matches the written document."""
    expected = _written_capture()
    database = _database_holding(dict(expected))
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, expected, database)
    assert result.verified is True
    assert result.reason == store.REASON_VERIFIED
    assert result.stored_size_bytes == store.measure_size_bytes(expected)
    assert database.requested_names == [store.CAPTURE_COLLECTION]


def test_verify_write_rejects_an_absent_document() -> None:
    """The read-back refuses a key that the database does not hold.

    Why:
        This case is issue 1824. The write reported success and wrote zero
        rows, so the key is absent. The read-back is the only proof.
    """
    expected = _written_capture()
    database = _database_holding(None)
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, expected, database)
    assert result.verified is False
    assert result.reason == store.REASON_ABSENT
    assert result.stored_size_bytes == 0


def test_verify_write_treats_a_failed_read_as_an_absent_document() -> None:
    """The read-back refuses a key when the database raises during the read."""
    database = _database_holding(None)
    database.fake_collection.read_error = RuntimeError("The read failed.")
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, _written_capture(), database)
    assert result.verified is False
    assert result.reason == store.REASON_ABSENT
    assert result.stored_size_bytes == 0


def test_verify_write_rejects_a_different_schema_version() -> None:
    """The read-back refuses a stored document that carries another schema version."""
    expected = _written_capture()
    stored = dict(expected, schema_version=store.SCHEMA_VERSION + 1)
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, expected, _database_holding(stored))
    assert result.verified is False
    assert result.reason == store.REASON_SCHEMA


def test_verify_write_rejects_a_changed_field() -> None:
    """The read-back refuses a stored document that holds a changed value."""
    expected = _written_capture()
    stored = dict(expected, ordinal=2)
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, expected, _database_holding(stored))
    assert result.verified is False
    assert result.reason == store.REASON_DIGEST


def test_verify_write_rejects_a_changed_digest_map() -> None:
    """The read-back refuses a stored document whose own digest differs."""
    expected = dict(_written_capture(), digests={"whole": "a" * 64})
    stored = dict(expected, digests={"whole": "b" * 64})
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, expected, _database_holding(stored))
    assert result.verified is False
    assert result.reason == store.REASON_DIGEST


def test_verify_write_reports_an_unreachable_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """The read-back reports the database as out of reach when no handle exists."""
    monkeypatch.setattr(store, "connect_database", lambda: None)
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, _written_capture())
    assert result.verified is False
    assert result.reason == store.REASON_NO_DATABASE
    assert result.stored_size_bytes == 0


def test_verify_write_ignores_the_driver_fields() -> None:
    """The read-back verifies a document that came back with driver fields.

    Why:
        The database adds ``_rev`` and ``_id`` to every stored document. A
        digest over those fields would fail every write in production.
    """
    expected = _written_capture()
    stored = dict(expected, _rev="_hZq1234", _id=store.CAPTURE_COLLECTION + "/" + _KEY)
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, expected, _database_holding(stored))
    assert result.verified is True
    assert result.reason == store.REASON_VERIFIED
    assert result.stored_size_bytes == store.measure_size_bytes(expected)


# ---------------------------------------------------------------------------
# write_capture: the store that the operator sees
# ---------------------------------------------------------------------------


def test_write_capture_names_the_database_after_a_matching_read_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """The result names the database after the key came back and matched."""
    database = _FakeDatabase()
    names = _install_exporter(monkeypatch, database)
    result = store.write_capture(_written_capture(), database)
    assert result.verified is True
    assert result.storage_path == store.STORAGE_DATABASE
    assert result.stored_size_bytes == database.fake_collection.documents[_KEY]["stored_size_bytes"]
    assert names == ["upgrade_capture_" + _KEY + ".csv"]


def test_write_capture_names_the_backup_file_after_a_zero_row_write(monkeypatch: pytest.MonkeyPatch) -> None:
    """The result names the backup file after a write that reported a false success.

    Why:
        This test is issue 1824. The exporter returns True after it wrote the
        CSV file and zero database rows. Only the read-back finds the loss.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, None)
    result = store.write_capture(_written_capture(), database)
    assert result.reason == store.REASON_ABSENT
    assert result.verified is False
    assert result.storage_path == store.STORAGE_BACKUP_FILE
    assert result.backup_written is True
    assert result.stored_size_bytes == 0


def test_write_capture_refuses_a_document_that_holds_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The store refuses a capture that carries no business key."""
    database = _FakeDatabase()
    names = _install_exporter(monkeypatch, database)
    result = store.write_capture({"site_id": "site-0001"}, database)
    assert result.reason == store.REASON_NO_KEY
    assert result.verified is False
    assert result.backup_written is False
    assert names == []
    assert database.requested_names == []


# ---------------------------------------------------------------------------
# The digest helpers that the read-back rests on
# ---------------------------------------------------------------------------


def test_canonical_json_sorts_the_keys() -> None:
    """Two documents with the same pairs in another order share one digest."""
    first = {"alpha": 1, "beta": 2, "gamma": 3}
    second = {"gamma": 3, "alpha": 1, "beta": 2}
    assert store.canonical_json(first) == store.canonical_json(second)
    assert store.document_digest(first) == store.document_digest(second)


def test_document_digest_ignores_the_driver_fields() -> None:
    """A stored copy with ``_rev`` and ``_id`` keeps the digest of the written copy."""
    written = _written_capture()
    stored = dict(written, _rev="_hZq5678", _id="upgrade_captures/" + _KEY, _key=_KEY)
    assert store.document_digest(stored) == store.document_digest(written)
    assert store.measure_size_bytes(stored) == store.measure_size_bytes(written)


def test_measure_size_bytes_counts_a_real_document() -> None:
    """The size of a capture is the byte count of its canonical form."""
    written = _written_capture()
    size = store.measure_size_bytes(written)
    assert size > 0
    assert size == len(store.canonical_json(written).encode("utf-8"))
