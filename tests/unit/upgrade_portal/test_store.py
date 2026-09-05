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

import logging
from collections.abc import Iterator, Mapping, Sequence
from types import SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.capture import store

_KEY = "cap-0001"  # WHY: One capture key serves every test in this module.
_RUN_KEY = "run-0001"  # WHY: The run that both captures of a pair belong to.
_EDGE_KEY = store.EDGE_KEY_PREFIX + _KEY  # WHY: The edge key of data-model.md section 5.


class _FakeCollection:
    """One collection of a fake document store.

    Why:
        The read-back calls ``collection(name).get(key)``. A test must own that
        one call, so the test returns a document, returns nothing, or raises.
        A unit test runs with no container and no network.

        The store also patches a capture to the verified state and imports one
        edge, so the fake answers those two calls as well. Each call may be
        made to fail, because a failed mark and a zero-row edge write are the
        two cases that the store must report and never hide.
    """

    def __init__(self) -> None:
        """Create an empty collection."""
        self.documents: dict[str, dict[str, Any]] = {}  # WHY: Holds each stored document by key.
        self.read_error: Exception | None = None  # WHY: A test sets this value to fail the read.
        self.update_error: Exception | None = None  # WHY: A test sets this value to fail the patch.
        self.bulk_accepts = True  # WHY: False repeats a bulk write that stored zero rows.
        self.bulk_error: Exception | None = None  # WHY: A test sets this value to fail the edge write.
        self.bulk_calls: list[dict[str, Any]] = []  # WHY: Records each bulk write for an assertion.

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

    def update(self, patch: Mapping[str, Any]) -> dict[str, Any]:
        """Merge a partial document into the stored document of one key.

        Why:
            The store marks a capture verified with a patch that carries the
            key, the state, and the fresh size. The driver refuses a patch for
            a key that the collection does not hold, so the fake refuses one
            too.

        Args:
            patch: The partial document. It carries ``_key``.

        Returns:
            The key of the patched document.

        Raises:
            Exception: The error that a test placed in ``update_error``.
            KeyError: When the collection holds no document under that key.
        """
        if self.update_error is not None:
            raise self.update_error
        key = str(patch["_key"])
        if key not in self.documents:
            raise KeyError(key)
        self.documents[key].update({name: value for name, value in patch.items() if name != "_key"})
        return {"_key": key}

    def import_bulk(self, documents: Sequence[Mapping[str, Any]], on_duplicate: str = "error") -> dict[str, int]:
        """Store a batch of documents by key.

        Why:
            The edge write uses the bulk import with the replace rule, which is
            the idiom of the shared writer. A test sets ``bulk_accepts`` to
            False to repeat a write that reported success and stored no row. A
            test sets ``bulk_error`` to make the driver raise, which is the
            case that must never escape the capture write.

        Args:
            documents: The documents to store.
            on_duplicate: The rule for a key that already exists.

        Returns:
            The count of created documents and the count of errors.

        Raises:
            Exception: The error that a test placed in ``bulk_error``.
        """
        self.bulk_calls.append({"documents": [dict(item) for item in documents], "on_duplicate": on_duplicate})
        if self.bulk_error is not None:
            raise self.bulk_error
        if not self.bulk_accepts:
            return {"created": 0, "errors": 0}
        for document in documents:
            self.documents[str(document["_key"])] = dict(document)
        return {"created": len(self.bulk_calls[-1]["documents"]), "errors": 0}


class _FakeAql:
    """The query seam of a fake database handle.

    Why:
        The capture list runs a count query and then a page query. The fake
        hands back one canned answer for each call in order, and it records
        every query text and every bind value. A test then proves that a
        narrowing value travels as a bind parameter and never as query text.
    """

    def __init__(self) -> None:
        """Create a query seam that answers with nothing."""
        self.calls: list[tuple[str, dict[str, Any]]] = []  # WHY: Records each query and its binds.
        self.answers: list[list[Any]] = []  # WHY: One canned answer for each call, in order.
        self.execute_error: Exception | None = None  # WHY: A test sets this value to fail the query.

    def execute(self, query: str, bind_vars: Mapping[str, Any] | None = None) -> list[Any]:
        """Return the next canned answer.

        Args:
            query: The query text.
            bind_vars: The bind values.

        Returns:
            The next canned answer, or an empty list when none is left.

        Raises:
            Exception: The error that a test placed in ``execute_error``.
        """
        self.calls.append((query, dict(bind_vars or {})))
        if self.execute_error is not None:
            raise self.execute_error
        return self.answers.pop(0) if self.answers else []


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
        self.aql = _FakeAql()  # WHY: The seam that the capture list queries run through.

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


def _linked_capture() -> dict[str, Any]:
    """Return a capture that names its run and its role.

    Why:
        The edge needs three values from the capture. One builder keeps every
        edge test on the same input, so a difference in a result comes from the
        test alone.

    Returns:
        A capture document with a run and a role.
    """
    return dict(_written_capture(), run_id=_RUN_KEY, role="pre")


def _verified_capture() -> dict[str, Any]:
    """Return a stored capture that reached the verified state.

    Why:
        Only a verified capture may join a comparison, so the load tests need a
        record that carries the word. The state field is the one field that
        separates this record from a half-written one.

    Returns:
        A capture document in the verified state.
    """
    return dict(_written_capture(), **{store.CAPTURE_STATE_FIELD: store.CaptureState.VERIFIED.value})


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


# ---------------------------------------------------------------------------
# T077: the stored size measurement
# ---------------------------------------------------------------------------


def test_measure_size_bytes_reports_zero_for_a_body_of_driver_fields() -> None:
    """A record that came back with driver fields alone measures zero.

    Why:
        The canonical text of an empty body is the two characters ``{}``. A
        plain byte count would report two bytes for a lost record and would
        pass the size rule, so the measurement calls an empty body zero.
    """
    assert store.measure_size_bytes({}) == 0
    assert store.measure_size_bytes({"_key": _KEY, "_rev": "_hZq1234"}) == 0


def test_size_rule_holds_asks_for_a_size_above_zero() -> None:
    """The size rule accepts a size above zero and refuses every other size.

    Why:
        Rule 6 of the data model asks that ``stored_size_bytes`` is greater
        than zero after a successful write. One function holds the rule, so the
        write path and this test read the same line.
    """
    assert store.size_rule_holds(1) is True
    assert store.size_rule_holds(0) is False
    assert store.size_rule_holds(-1) is False


def test_verify_write_refuses_an_empty_stored_document() -> None:
    """The read-back refuses a stored record that holds no field of its own.

    Why:
        An empty body matches an empty body, so the digest alone would call
        this write a success. The size rule is the guard that catches it.
    """
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, {}, _database_holding({"_key": _KEY}))
    assert result.verified is False
    assert result.reason == store.REASON_EMPTY_SIZE
    assert result.stored_size_bytes == 0


def test_write_capture_records_a_size_above_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """A verified capture carries a stored size above zero.

    Why:
        FR-032b asks for the stored size of every capture, and rule 6 asks that
        the number is greater than zero after a successful write.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    result = store.write_capture(_written_capture(), database)
    stored = database.fake_collection.documents[_KEY]
    assert result.verified is True
    assert store.size_rule_holds(result.stored_size_bytes) is True
    assert result.stored_size_bytes == stored["stored_size_bytes"]


def test_write_capture_records_a_size_that_matches_the_stored_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """The recorded size equals the measured size of the record that the database holds.

    Why:
        The word ``verified`` is one byte longer than the word ``writing``, so
        a size that the portal stamped before the mark would describe another
        body. A stale size makes the operator compare one number against a
        different number.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    result = store.write_capture(_written_capture(), database)
    stored = database.fake_collection.documents[_KEY]
    assert store.measure_size_bytes(stored) == stored["stored_size_bytes"]
    assert result.stored_size_bytes == store.measure_size_bytes(stored)


# ---------------------------------------------------------------------------
# T081: the capture state machine
# ---------------------------------------------------------------------------


def test_capture_state_machine_walks_the_whole_path() -> None:
    """One capture moves from pending to verified through every state between."""
    record: dict[str, Any] = {"capture_id": _KEY}
    machine = store.CaptureStateMachine()
    for wanted in (
        store.CaptureState.COLLECTING,
        store.CaptureState.ASSEMBLING,
        store.CaptureState.WRITING,
        store.CaptureState.VERIFIED,
    ):
        machine.advance(record, wanted)
    assert record[store.CAPTURE_STATE_FIELD] == store.CaptureState.VERIFIED.value


def test_capture_state_machine_refuses_an_illegal_move() -> None:
    """The machine raises for a move that the data model forbids.

    Why:
        A jump from pending to verified would let a capture that holds no
        device record and no client record join a comparison. The refusal is
        loud, because a silent skip would store a lie in one word.
    """
    record: dict[str, Any] = {"capture_id": _KEY, store.CAPTURE_STATE_FIELD: store.CaptureState.PENDING.value}
    with pytest.raises(store.CaptureTransitionError):
        store.CaptureStateMachine().advance(record, store.CaptureState.VERIFIED)
    assert record[store.CAPTURE_STATE_FIELD] == store.CaptureState.PENDING.value


def test_capture_state_machine_refuses_a_move_out_of_a_final_state() -> None:
    """The machine raises for a move away from a state that ends the lifecycle."""
    record: dict[str, Any] = {"capture_id": _KEY, store.CAPTURE_STATE_FIELD: store.CaptureState.VERIFIED.value}
    with pytest.raises(store.CaptureTransitionError):
        store.CaptureStateMachine().advance(record, store.CaptureState.COLLECTING)
    assert store.CaptureState.VERIFIED in store.CaptureStateMachine.TERMINAL


def test_capture_state_machine_refuses_a_name_outside_the_model() -> None:
    """The machine raises for a state name that the data model does not list."""
    with pytest.raises(store.CaptureTransitionError):
        store.CaptureStateMachine.coerce("done")


def test_capture_state_machine_reads_an_absent_state_as_pending() -> None:
    """A capture that names no state has not started."""
    assert store.CaptureStateMachine.read_state({}) is store.CaptureState.PENDING


def test_capture_state_machine_permits_answers_and_never_raises() -> None:
    """The question form of the table answers False and raises nothing."""
    assert store.CaptureStateMachine.permits("writing", "verified") is True
    assert store.CaptureStateMachine.permits("pending", "verified") is False
    assert store.CaptureStateMachine.permits("pending", "done") is False


def test_is_comparable_accepts_the_verified_state_alone() -> None:
    """Only a verified capture may take part in a comparison."""
    assert store.is_comparable(_verified_capture()) is True
    for name in ("pending", "collecting", "partial", "assembling", "writing", "write_failed", "failed"):
        assert store.is_comparable({store.CAPTURE_STATE_FIELD: name}) is False
    assert store.is_comparable({store.CAPTURE_STATE_FIELD: "done"}) is False


def test_write_capture_marks_a_stored_capture_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stored capture carries the verified state after a matching read-back."""
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    result = store.write_capture(_written_capture(), database)
    assert result.verified is True
    assert database.fake_collection.documents[_KEY][store.CAPTURE_STATE_FIELD] == store.CaptureState.VERIFIED.value


def test_write_capture_leaves_the_capture_unmarked_when_the_patch_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A capture that the portal could not mark stays out of every comparison.

    Why:
        The record is whole and the database holds it, so the write is not
        lost. The capture keeps the writing state, which no comparison
        accepts, and the result names the reason.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    database.fake_collection.update_error = RuntimeError("The patch failed.")
    result = store.write_capture(_written_capture(), database)
    assert result.verified is False
    assert result.reason == store.REASON_STATE_UNSET
    stored = database.fake_collection.documents[_KEY]
    assert stored[store.CAPTURE_STATE_FIELD] == store.CaptureState.WRITING.value
    assert store.is_comparable(stored) is False


def test_write_capture_refuses_a_capture_in_a_final_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """The store refuses a capture that already reached a final state."""
    database = _FakeDatabase()
    names = _install_exporter(monkeypatch, database)
    document = dict(_written_capture(), **{store.CAPTURE_STATE_FIELD: store.CaptureState.VERIFIED.value})
    result = store.write_capture(document, database)
    assert result.reason == store.REASON_BAD_STATE
    assert result.verified is False
    assert result.storage_path == store.STORAGE_NONE
    assert names == []


def test_write_capture_refuses_a_capture_in_an_early_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """The store refuses a capture that has not finished its assembly."""
    database = _FakeDatabase()
    names = _install_exporter(monkeypatch, database)
    document = dict(_written_capture(), **{store.CAPTURE_STATE_FIELD: store.CaptureState.COLLECTING.value})
    result = store.write_capture(document, database)
    assert result.reason == store.REASON_BAD_STATE
    assert names == []


# ---------------------------------------------------------------------------
# The schema version guard
# ---------------------------------------------------------------------------


def test_is_schema_version_refuses_a_boolean() -> None:
    """A boolean is not a schema version.

    Why:
        Python treats ``True`` as the integer 1, so a plain ``!= 1`` test
        accepts ``True``. ``RunRecordBuilder.validate`` in
        ``src/upgrade_portal/runtime/runs.py`` holds that defect, and this
        store must not repeat it.
    """
    assert store.is_schema_version(store.SCHEMA_VERSION) is True
    assert store.is_schema_version(True) is False
    assert store.is_schema_version(False) is False
    assert store.is_schema_version("1") is False
    assert store.is_schema_version(None) is False


def test_write_capture_refuses_a_boolean_schema_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """The store refuses a capture whose schema version is a boolean."""
    database = _FakeDatabase()
    names = _install_exporter(monkeypatch, database)
    result = store.write_capture(dict(_written_capture(), schema_version=True), database)
    assert result.reason == store.REASON_BAD_SCHEMA
    assert result.verified is False
    assert result.backup_written is False
    assert names == []
    assert database.requested_names == []


def test_verify_write_refuses_a_boolean_schema_version() -> None:
    """The read-back refuses a stored capture whose schema version turned into a boolean."""
    expected = _written_capture()
    stored = dict(expected, schema_version=True)
    result = store.verify_write(store.CAPTURE_COLLECTION, _KEY, expected, _database_holding(stored))
    assert result.verified is False
    assert result.reason == store.REASON_SCHEMA


# ---------------------------------------------------------------------------
# T079: the CaptureForRun edge
# ---------------------------------------------------------------------------


def test_build_edge_names_the_run_and_the_capture() -> None:
    """The edge carries the key of the data model and the two document handles."""
    edge = store.build_edge(_linked_capture())
    assert edge["_key"] == _EDGE_KEY
    assert edge["_from"] == store.RUN_COLLECTION + "/" + _RUN_KEY
    assert edge["_to"] == store.CAPTURE_COLLECTION + "/" + _KEY
    assert edge["role"] == "pre"


def test_write_edge_verifies_the_stored_edge() -> None:
    """The edge write reports success only after the key came back and matched."""
    database = _FakeDatabase()
    result = store.write_edge(_linked_capture(), database)
    assert result.verified is True
    assert result.key == _EDGE_KEY
    assert result.collection == store.EDGE_COLLECTION
    assert result.storage_path == store.STORAGE_DATABASE
    assert result.backup_written is False
    assert result.stored_size_bytes > 0


def test_write_edge_replaces_an_edge_that_carries_the_same_key() -> None:
    """A repeat write leaves one edge and never two."""
    database = _FakeDatabase()
    store.write_edge(_linked_capture(), database)
    store.write_edge(_linked_capture(), database)
    assert [call["on_duplicate"] for call in database.fake_collection.bulk_calls] == ["replace", "replace"]
    assert list(database.fake_collection.documents) == [_EDGE_KEY]


def test_write_edge_refuses_a_capture_that_names_no_run() -> None:
    """The store refuses an edge for a capture that names no run."""
    database = _FakeDatabase()
    result = store.write_edge(dict(_linked_capture(), run_id=""), database)
    assert result.verified is False
    assert result.reason == store.REASON_NO_KEY
    assert result.storage_path == store.STORAGE_NONE
    assert database.fake_collection.bulk_calls == []


def test_write_edge_reports_a_zero_row_write() -> None:
    """The edge write refuses a bulk import that reported success and stored no row.

    Why:
        This case is issue 1824 on the edge collection. The read-back is the
        only proof that the link arrived.
    """
    database = _FakeDatabase()
    database.fake_collection.bulk_accepts = False
    result = store.write_edge(_linked_capture(), database)
    assert result.verified is False
    assert result.reason == store.REASON_ABSENT
    assert result.stored_size_bytes == 0


def test_write_edge_rejects_a_changed_edge() -> None:
    """The edge write refuses a stored edge that points at another capture."""
    database = _FakeDatabase()
    database.fake_collection.bulk_accepts = False
    database.fake_collection.documents[_EDGE_KEY] = {
        "_key": _EDGE_KEY,
        "_from": store.RUN_COLLECTION + "/run-9999",
        "_to": store.CAPTURE_COLLECTION + "/" + _KEY,
        "role": "pre",
    }
    result = store.write_edge(_linked_capture(), database)
    assert result.verified is False
    assert result.reason == store.REASON_DIGEST


def test_write_edge_reports_an_unreachable_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """The edge write reports the database as out of reach when no handle exists."""
    monkeypatch.setattr(store, "connect_database", lambda: None)
    result = store.write_edge(_linked_capture())
    assert result.verified is False
    assert result.reason == store.REASON_NO_DATABASE


# ---------------------------------------------------------------------------
# The capture write builds the edge
# ---------------------------------------------------------------------------


def test_write_capture_links_the_capture_to_its_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """A verified capture leaves an edge that points at its run.

    Why:
        The history view walks the graph from a run to its captures. Without
        this edge the graph holds no link at all, so an operator who returns a
        month later reads an empty view.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    result = store.write_capture(_linked_capture(), database)
    edge = database.fake_collection.documents[_EDGE_KEY]
    assert result.verified is True
    assert result.collection == store.CAPTURE_COLLECTION
    assert edge["_from"] == store.RUN_COLLECTION + "/" + _RUN_KEY
    assert edge["_to"] == store.CAPTURE_COLLECTION + "/" + _KEY
    assert edge["role"] == "pre"
    assert [call["on_duplicate"] for call in database.fake_collection.bulk_calls] == ["replace"]


def test_write_capture_builds_no_edge_after_a_zero_row_write(monkeypatch: pytest.MonkeyPatch) -> None:
    """A capture that the database does not hold gets no edge.

    Why:
        An edge that points at an absent capture is worse than no edge. The
        history view would show a row that opens on nothing.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, None)
    result = store.write_capture(_linked_capture(), database)
    assert result.verified is False
    assert result.reason == store.REASON_ABSENT
    assert database.fake_collection.bulk_calls == []
    assert _EDGE_KEY not in database.fake_collection.documents


def test_write_capture_builds_no_edge_when_the_mark_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """A capture that the portal could not mark verified gets no edge.

    Why:
        The database holds the record, but no comparison accepts it. The edge
        waits for the full proof and never for the first read-back alone.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    database.fake_collection.update_error = RuntimeError("The patch failed.")
    result = store.write_capture(_linked_capture(), database)
    assert result.verified is False
    assert result.reason == store.REASON_STATE_UNSET
    assert database.fake_collection.bulk_calls == []
    assert _EDGE_KEY not in database.fake_collection.documents


def test_write_capture_keeps_its_result_when_the_edge_write_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed edge write changes no field of the capture result and raises nothing.

    Why:
        The link is a best effort. The capture names its run, so the portal
        rebuilds a lost edge later. A driver error on the edge must never turn
        a stored capture into a reported failure.
    """
    healthy = _FakeDatabase()
    _install_exporter(monkeypatch, healthy)
    linked = store.write_capture(_linked_capture(), healthy)
    broken = _FakeDatabase()
    _install_exporter(monkeypatch, broken)
    broken.fake_collection.bulk_error = RuntimeError("The edge write failed.")
    unlinked = store.write_capture(_linked_capture(), broken)
    assert unlinked == linked
    assert unlinked.verified is True
    assert _EDGE_KEY in healthy.fake_collection.documents
    assert _EDGE_KEY not in broken.fake_collection.documents


def test_write_capture_keeps_its_result_when_the_edge_stores_no_row(monkeypatch: pytest.MonkeyPatch) -> None:
    """An edge write that stored no row leaves the capture result untouched.

    Why:
        This case is issue 1824 on the edge collection. The bulk import
        reported success and wrote nothing, and the capture must still read as
        verified.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    database.fake_collection.bulk_accepts = False
    result = store.write_capture(_linked_capture(), database)
    assert result.verified is True
    assert result.collection == store.CAPTURE_COLLECTION
    assert result.reason == store.REASON_VERIFIED
    assert result.storage_path == store.STORAGE_DATABASE
    assert _EDGE_KEY not in database.fake_collection.documents


def test_write_capture_builds_no_edge_for_a_capture_that_names_no_run(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A capture that names no run leaves quietly and raises no alarm.

    Why:
        Such a capture has no link to build, so the case is not a fault. A
        warning here would teach an operator to ignore the warnings that do
        report a lost link.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    with caplog.at_level(logging.DEBUG, logger=store.logger.name):
        result = store.write_capture(_written_capture(), database)
    loud = [record.levelname for record in caplog.records if record.levelno >= logging.WARNING]
    assert result.verified is True
    assert database.fake_collection.bulk_calls == []
    assert list(database.fake_collection.documents) == [_KEY]
    assert loud == []


# ---------------------------------------------------------------------------
# T078: reading captures back out
# ---------------------------------------------------------------------------


def test_list_captures_returns_the_rows_and_the_total() -> None:
    """A page carries its rows and the total number of captures behind it."""
    database = _FakeDatabase()
    rows = [{"capture_id": _KEY, "ordinal": 1}, {"capture_id": "cap-0002", "ordinal": 2}]
    database.aql.answers = [[7], rows]
    page = store.list_captures(store.CaptureQuery(site_id="site-0001", limit=2), database)
    assert page.total == 7
    assert page.limit == 2
    assert page.database_available is True
    assert [row["capture_id"] for row in page.captures] == [_KEY, "cap-0002"]


def test_list_captures_sends_every_narrowing_value_as_a_bind() -> None:
    """A narrowing value travels as a bind parameter and never as query text.

    Why:
        A site name comes from an operator. A value inside the query text would
        let that operator write the query, so every value travels as a bind and
        every name comes from a fixed tuple of the store.
    """
    database = _FakeDatabase()
    database.aql.answers = [[0], []]
    store.list_captures(store.CaptureQuery(site_id="site-0001", run_id=_RUN_KEY), database)
    count_query, count_binds = database.aql.calls[0]
    page_query, page_binds = database.aql.calls[1]
    assert count_binds == {"site_id": "site-0001", "run_id": _RUN_KEY}
    assert page_binds == {"site_id": "site-0001", "run_id": _RUN_KEY, "offset": 0, "limit": 25}
    assert "site-0001" not in count_query
    assert "site-0001" not in page_query
    assert "FILTER doc.org_id" not in page_query


def test_list_captures_reads_every_site_when_the_caller_narrows_nothing() -> None:
    """A query that names no site reads every capture and binds nothing."""
    database = _FakeDatabase()
    database.aql.answers = [[3], []]
    page = store.list_captures(store.CaptureQuery(), database)
    count_query, count_binds = database.aql.calls[0]
    assert count_binds == {}
    assert "FILTER" not in count_query
    assert page.total == 3
    assert page.limit == store.DEFAULT_LIST_LIMIT


def test_list_captures_reports_the_database_out_of_reach(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty page states that the database never answered.

    Why:
        An empty history that reads as a fact would tell the operator that the
        site holds no capture. The flag separates a silent outage from an
        empty site.
    """
    monkeypatch.setattr(store, "connect_database", lambda: None)
    page = store.list_captures(store.CaptureQuery(site_id="site-0001"))
    assert page.captures == ()
    assert page.total == 0
    assert page.database_available is False


def test_list_captures_returns_an_empty_page_when_the_query_fails() -> None:
    """A failed query returns an empty page and raises nothing."""
    database = _FakeDatabase()
    database.aql.execute_error = RuntimeError("The query failed.")
    page = store.list_captures(store.CaptureQuery(site_id="site-0001"), database)
    assert page.captures == ()
    assert page.total == 0
    assert page.database_available is True


def test_load_capture_reports_an_absent_capture() -> None:
    """The store reports the reason that the capture route answers 404 for."""
    loaded = store.load_capture(_KEY, _database_holding(None))
    assert loaded.capture is None
    assert loaded.comparable is False
    assert loaded.reason == store.REASON_CAPTURE_NOT_FOUND


def test_load_capture_returns_a_verified_capture() -> None:
    """The store hands out a verified capture and calls it comparable."""
    loaded = store.load_capture(_KEY, _database_holding(_verified_capture()))
    assert loaded.capture is not None
    assert loaded.comparable is True
    assert loaded.reason == store.REASON_VERIFIED


def test_load_capture_hands_out_an_unverified_capture_with_its_reason() -> None:
    """The store shows a half-written capture and still refuses to call it comparable.

    Why:
        An operator may need to read what a failed capture holds. The record
        travels, and the verdict travels with it.
    """
    stored = dict(_written_capture(), **{store.CAPTURE_STATE_FIELD: store.CaptureState.WRITING.value})
    loaded = store.load_capture(_KEY, _database_holding(stored))
    assert loaded.capture is not None
    assert loaded.comparable is False
    assert loaded.reason == store.REASON_CAPTURE_NOT_VERIFIED


def test_load_capture_for_comparison_withholds_an_unverified_capture() -> None:
    """A capture that never reached the verified state cannot join a comparison.

    Why:
        Section 3.8 of the data model allows a comparison of a verified capture
        alone. The rule lives at the store boundary, so the store hands out no
        document at all and a caller cannot compare a half-written capture even
        by mistake.
    """
    stored = dict(_written_capture(), **{store.CAPTURE_STATE_FIELD: store.CaptureState.WRITE_FAILED.value})
    loaded = store.load_capture_for_comparison(_KEY, _database_holding(stored))
    assert loaded.capture is None
    assert loaded.comparable is False
    assert loaded.reason == store.REASON_CAPTURE_NOT_VERIFIED


def test_load_capture_for_comparison_withholds_a_capture_that_names_no_state() -> None:
    """A capture that carries no state is not verified, so no comparison takes it."""
    loaded = store.load_capture_for_comparison(_KEY, _database_holding(_written_capture()))
    assert loaded.capture is None
    assert loaded.reason == store.REASON_CAPTURE_NOT_VERIFIED


def test_load_capture_for_comparison_returns_a_verified_capture() -> None:
    """A verified capture reaches the comparison whole."""
    loaded = store.load_capture_for_comparison(_KEY, _database_holding(_verified_capture()))
    assert loaded.capture is not None
    assert loaded.comparable is True
    assert loaded.capture["capture_id"] == _KEY


def test_load_capture_reports_an_unreachable_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """The store separates a database outage from an absent capture."""
    monkeypatch.setattr(store, "connect_database", lambda: None)
    loaded = store.load_capture(_KEY)
    assert loaded.capture is None
    assert loaded.reason == store.REASON_NO_DATABASE


def test_a_written_capture_reads_back_as_comparable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The write path and the read path agree about one capture.

    Why:
        The two halves of this store must meet. A capture that the portal wrote
        and verified is the one capture that a comparison may take, and the
        edge that names it points at the same key.
    """
    database = _FakeDatabase()
    _install_exporter(monkeypatch, database)
    written = store.write_capture(_linked_capture(), database)
    edge = store.write_edge(_linked_capture(), database)
    loaded = store.load_capture_for_comparison(_KEY, database)
    assert written.verified is True
    assert edge.verified is True
    assert loaded.comparable is True
    assert loaded.capture is not None
    assert loaded.capture["stored_size_bytes"] == written.stored_size_bytes


class TestRequestBound:
    """The document store client carries a bound on every request.

    Why:
        The driver of the store waits 60 seconds by default, and that value
        covers the connect step as well as the read step. A readiness probe
        against a host that never answers then holds one worker thread for a
        full minute, and enough probes empty the worker pool. These tests prove
        that the portal names its own shorter bound and passes it to the client.

        No test opens a socket. The fake client below records the arguments and
        returns a handle.
    """

    @staticmethod
    def _config() -> Any:
        """Return settings that name a host and leave standalone mode off.

        Returns:
            The settings record the connection helper reads.
        """
        return SimpleNamespace(
            standalone_mode=False,
            arango_host="http://127.0.0.1:8529",
            arango_database="test",
            arango_username="tester",
            arango_password="",  # nosec B106  # WHY: a fake value for a fake client, never a credential.
        )

    def test_the_client_carries_the_request_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The helper passes the portal bound to the store client.

        Why:
            Without this argument the client keeps the 60-second default of the
            driver, and the readiness probe blocks a worker for that long.

        Args:
            monkeypatch: The pytest patch helper.
        """
        seen: dict[str, Any] = {}

        def _record(**kwargs: Any) -> Any:
            """Record the client arguments and return a fake client.

            Args:
                **kwargs: The arguments the helper passed.

            Returns:
                A fake client whose ``db`` call returns a plain handle.
            """
            seen.update(kwargs)
            return SimpleNamespace(db=lambda *args, **rest: "handle")

        monkeypatch.setattr(store, "ArangoClient", _record)
        assert store._open_database(self._config()) == "handle"
        assert seen["request_timeout"] == store.REQUEST_TIMEOUT_SECONDS

    def test_the_request_bound_stays_under_the_driver_default(self) -> None:
        """The portal bound is shorter than the 60-second driver default.

        Why:
            A bound at or above the default would leave the hang in place. This
            test fails if a later change raises the number past the point where
            it still helps.
        """
        assert 0 < store.REQUEST_TIMEOUT_SECONDS < 60
