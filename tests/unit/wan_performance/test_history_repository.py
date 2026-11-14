"""Check WAN history against the existing SQLite file without live credentials."""

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from arango.cursor import Cursor

from src.interfaces.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS, CalendarWindow
from src.interfaces.wan_performance.domain.measurement import MetricMeasurement, SampleMeasurement
from src.interfaces.wan_performance.integration.arango_history import ArangoArchive, ArangoHistory
from src.interfaces.wan_performance.integration.history_repository import HistorySelection
from src.interfaces.wan_performance.integration.sqlite_history import SQLiteArchive, SQLiteHistory
from src.interfaces.wan_performance.presentation.offline_preview import OfflinePreviewFactory


@pytest.fixture
def history(tmp_path):
    """Use an existing isolated application database for repository checks."""
    path = tmp_path / "application.db"
    sqlite3.connect(path).close()
    return SQLiteHistory(path)


def live_record():
    """Use independent synthetic inputs labeled live only in an isolated test."""
    return replace(OfflinePreviewFactory.build().measurements[0], provenance="live")


@pytest.fixture
def archive_payload():
    """Construct a strict synthetic archive independently of source fixtures and live history."""
    record = OfflinePreviewFactory.build().measurements[0]
    return {
        "version": 1,
        "provenance": "synthetic",
        "identity": record.identity.to_dict(),
        "window": {
            "start_utc": record.hour_start_utc.isoformat(),
            "end_utc": (record.hour_start_utc + timedelta(hours=1)).isoformat(),
            "complete": False,
        },
        "records": [record.to_dict()],
    }


@pytest.fixture
def archive_documents(archive_payload):
    """Prepare validated synthetic rows only for native append-primitive tests, not live admission."""
    import hashlib

    from src.interfaces.wan_performance.integration.record_codec import ArchiveCodec

    archive = ArchiveCodec.decode(json.dumps(archive_payload).encode())
    documents = tuple(
        {
            "_key": hashlib.sha256(json.dumps(record.natural_key).encode()).hexdigest(),
            "identity": json.dumps(record.identity.natural_key),
            "hour": record.hour_start_utc.isoformat(),
            "payload": json.dumps(record.to_dict(), sort_keys=True, allow_nan=False),
        }
        for record in archive["records"]
    )
    return archive, documents


def test_native_sqlite_archive_append_replay_conflict_and_synthetic_rejection(history, archive_documents):
    """Exercise native append semantics while proving application history still rejects synthetic payloads."""

    archive, documents = archive_documents
    with sqlite3.connect(history.path) as connection:
        connection.execute(
            "CREATE TABLE wan_performance_hours (identity TEXT, hour TEXT, payload TEXT, PRIMARY KEY(identity,hour))"
        )
    assert SQLiteArchive.append(history, documents) == 1
    assert SQLiteArchive.append(history, documents) == 0
    changed = json.loads(documents[0]["payload"])
    next(iter(changed["metrics"].values()))["value"] = 999
    with pytest.raises(ValueError, match="conflict"):
        SQLiteArchive.append(history, ({**documents[0], "payload": json.dumps(changed, sort_keys=True)},))
    with sqlite3.connect(history.path) as connection:
        assert connection.execute("SELECT payload FROM wan_performance_hours").fetchall() == [
            (documents[0]["payload"],)
        ]
    with pytest.raises(ValueError, match="live"):
        history.read(archive["identity"], *archive["window"])


def test_native_sqlite_archive_batch_constraint_failure_rolls_back_all_new_rows(history, archive_documents):
    """Prove a real SQLite failure after an insert cannot leave a partially appended archive."""
    import hashlib

    archive, documents = archive_documents
    original = archive["records"][0]
    second = replace(
        original,
        hour_start_utc=original.hour_start_utc + timedelta(hours=1),
        collected_at_utc=original.collected_at_utc + timedelta(hours=1),
        metrics={"missing": MetricMeasurement(None, "ms", missing_reason="x" * 3000)},
    )
    extra = {
        "_key": hashlib.sha256(json.dumps(second.natural_key).encode()).hexdigest(),
        "identity": json.dumps(second.identity.natural_key),
        "hour": second.hour_start_utc.isoformat(),
        "payload": json.dumps(second.to_dict(), sort_keys=True, allow_nan=False),
    }
    assert len(documents[0]["payload"]) < 2048 < len(extra["payload"])
    with sqlite3.connect(history.path) as connection:
        connection.execute(
            "CREATE TABLE wan_performance_hours (identity TEXT, hour TEXT, "
            "payload TEXT CHECK(length(payload)<2048), PRIMARY KEY(identity,hour))"
        )
    with pytest.raises(sqlite3.IntegrityError):
        SQLiteArchive.append(history, (*documents, extra))
    with sqlite3.connect(history.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM wan_performance_hours").fetchone() == (0,)


@pytest.mark.parametrize("damage", ["boolean-value", "duplicate-field"])
def test_native_sqlite_archive_rejects_invalid_stored_payload_without_replacement(history, archive_documents, damage):
    """Reject invalid stored types and duplicate fields even when permissive parsing could hide a conflict."""

    _, documents = archive_documents
    damaged = json.loads(documents[0]["payload"])
    next(iter(damaged["metrics"].values()))["value"] = True
    payload = (
        json.dumps(damaged)
        if damage == "boolean-value"
        else documents[0]["payload"].replace(
            '"provenance": "synthetic"', '"provenance": "synthetic", "provenance": "synthetic"'
        )
    )
    with sqlite3.connect(history.path) as connection:
        connection.execute(
            "CREATE TABLE wan_performance_hours (identity TEXT, hour TEXT, payload TEXT, PRIMARY KEY(identity,hour))"
        )
        connection.execute(
            "INSERT INTO wan_performance_hours VALUES (?,?,?)",
            (documents[0]["identity"], documents[0]["hour"], payload),
        )
    with pytest.raises(ValueError):
        SQLiteArchive.append(history, documents)
    with sqlite3.connect(history.path) as connection:
        assert connection.execute("SELECT payload FROM wan_performance_hours").fetchall() == [(payload,)]


def test_native_sqlite_archive_requires_existing_table_without_schema_creation(history, archive_documents):
    """Return the existing-schema prerequisite rather than create a production-like history table."""

    _, documents = archive_documents
    with sqlite3.connect(history.path):
        pass
    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        SQLiteArchive.append(history, documents)
    with sqlite3.connect(history.path) as connection:
        assert connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []


@pytest.fixture
def reviewed_live_archive():
    """Provide live-shaped bytes only to mocked admission boundaries, never a real datastore."""
    from src.interfaces.wan_performance.integration.record_codec import DeclarationCodec

    identity = {"org_id": "org-one", "site_id": "site-one", "gateway_id": "aabbccddeeff", "port_name": "ge-0/0/0"}
    body = {
        "version": 1,
        "provenance": "live",
        "identity": identity,
        "window": {"start_utc": "2024-01-01T12:00:00+00:00", "end_utc": "2024-01-01T13:00:00+00:00", "complete": False},
        "records": [
            {
                "identity": identity,
                "provenance": "live",
                "hour_start_utc": "2024-01-01T12:00:00+00:00",
                "collected_at_utc": "2024-01-01T12:34:00+00:00",
                "is_up_observation": None,
                "metrics": {"rx_bps": {"value": 40, "unit": "bit/s"}},
            }
        ],
    }
    return json.dumps(body).encode(), DeclarationCodec.identity(identity)


@pytest.mark.parametrize("state", ["missing", "wrong-bytes", "foreign-review", "bad-map", "membership", "confirmation"])
def test_live_archive_admission_refuses_untrusted_evidence_before_repository_acquisition(reviewed_live_archive, state):
    """Keep unreviewed bytes and foreign scopes away from any database connection."""
    import hashlib

    from src.interfaces.wan_performance.integration.history_repository import ArchiveImporter

    payload, identity = reviewed_live_archive
    digest = hashlib.sha256(payload).hexdigest()
    reviews = {} if state == "missing" else {identity.natural_key: frozenset({digest})}
    if state == "foreign-review":
        reviews = {("foreign", *identity.natural_key[1:]): frozenset({digest})}
    if state == "bad-map":
        reviews = {identity.natural_key: {digest}}
    provider = MagicMock()
    with pytest.raises((ValueError, TypeError)):
        ArchiveImporter(provider, reviews).apply(
            payload + b" " if state == "wrong-bytes" else payload,
            () if state == "membership" else (identity,),
            "import" if state == "confirmation" else "IMPORT",
        )
    provider.assert_not_called()


def test_live_archive_review_requires_an_available_backend(reviewed_live_archive):
    """Report an unavailable reviewed backend without creating a store or claiming an append."""
    import hashlib

    from src.interfaces.wan_performance.integration.history_repository import ArchiveImporter

    payload, identity = reviewed_live_archive
    provider = MagicMock(return_value=None)
    with pytest.raises(ConnectionError, match="available"):
        ArchiveImporter(provider, {identity.natural_key: frozenset({hashlib.sha256(payload).hexdigest()})}).apply(
            payload, (identity,), "IMPORT"
        )
    provider.assert_called_once_with()


def test_live_archive_review_admission_uses_only_a_mocked_append_boundary(reviewed_live_archive):
    """Verify exact-byte approval without persisting an invented live-shaped record."""
    import hashlib

    from src.interfaces.wan_performance.integration.history_repository import ArchiveImporter

    payload, identity = reviewed_live_archive
    repository = MagicMock(spec=SQLiteHistory)
    provider = MagicMock(return_value=repository)
    with patch.object(SQLiteArchive, "append", return_value=1) as append:
        message = ArchiveImporter(
            provider, {identity.natural_key: frozenset({hashlib.sha256(payload).hexdigest()})}
        ).apply(payload, (identity,), "IMPORT")
    assert "Appended 1 reviewed live projection" in message and "completeness remains unknown" in message
    provider.assert_called_once_with()
    assert json.loads(append.call_args.args[1][0]["payload"])["provenance"] == "live"
    repository._connect.assert_not_called()


@pytest.mark.parametrize(
    "state",
    [
        "new",
        "replay",
        "missing-receipt",
        "wrong-key",
        "commit-false",
        "cursor-count",
        "concurrent-duplicate",
        "abort-false",
        "abort-error",
        "error-receipt",
    ],
)
def test_mocked_arango_archive_acknowledgments_and_transaction_failures(archive_documents, state, caplog):
    """Require complete synchronous acknowledgments and abort uncertain or conflicting streaming transactions."""

    _, documents = archive_documents
    database = MagicMock()
    transaction = database.begin_transaction.return_value
    cursor = MagicMock(spec=Cursor)
    cursor.__iter__.return_value = iter(documents if state == "replay" else [] if state == "cursor-count" else [None])
    transaction.aql.execute.return_value = cursor
    collection = transaction.collection.return_value
    collection.insert_many.return_value = (
        []
        if state in {"missing-receipt", "abort-false", "abort-error"}
        else [{"_key": "wrong" if state == "wrong-key" else documents[0]["_key"]}]
    )
    transaction.commit_transaction.return_value = state != "commit-false"
    transaction.abort_transaction.return_value = state != "abort-false"
    if state == "error-receipt":
        collection.insert_many.return_value = [{"_key": documents[0]["_key"], "error": True}]
    if state == "abort-error":
        transaction.abort_transaction.side_effect = OSError("Synthetic abort uncertainty.")
    if state == "concurrent-duplicate":
        collection.insert_many.side_effect = ValueError("Concurrent duplicate insert.")
    if state in {"new", "replay"}:
        assert ArangoArchive.append(ArangoHistory(database), documents) == (1 if state == "new" else 0)
        transaction.commit_transaction.assert_called_once_with()
        transaction.abort_transaction.assert_not_called()
    else:
        with pytest.raises((ValueError, TypeError, ConnectionError)):
            ArangoArchive.append(ArangoHistory(database), documents)
        transaction.abort_transaction.assert_called_once_with()
        if state in {"abort-false", "abort-error"}:
            assert "rollback" in caplog.text and (
                "did not confirm" in caplog.text or "could not be confirmed" in caplog.text
            )
    cursor.close.assert_called_once_with()
    if state == "new":
        collection.insert_many.assert_called_once_with(list(documents), overwrite=False, raise_on_document_error=True)
    if state == "replay":
        collection.insert_many.assert_not_called()


@pytest.mark.parametrize("extra_byte", [0, 1])
def test_archive_codec_exact_upload_byte_bound(archive_payload, extra_byte):
    """Exercise the actual eight-MiB boundary independently of record-count validation."""
    from src.interfaces.wan_performance.integration.record_codec import ArchiveCodec

    original = json.dumps(archive_payload).encode()
    payload = original + b" " * (8 * 1024 * 1024 - len(original) + extra_byte)
    if extra_byte:
        with pytest.raises(ValueError, match="eight MiB"):
            ArchiveCodec.decode(payload)
    else:
        assert len(ArchiveCodec.decode(payload)["records"]) == 1


@pytest.mark.parametrize("extra_byte", [0, 1])
def test_declaration_codec_exact_input_byte_bound(declaration_payload, extra_byte):
    """Exercise the actual 64-KiB declaration boundary with otherwise valid input."""
    from src.interfaces.wan_performance.integration.record_codec import DeclarationCodec

    _, declaration = declaration_payload
    original = json.dumps(declaration).encode()
    payload = original + b" " * (65536 - len(original) + extra_byte)
    if extra_byte:
        with pytest.raises(ValueError, match="64 KiB"):
            DeclarationCodec.decode(payload)
    else:
        assert DeclarationCodec.decode(payload)["values"] == declaration["values"]


def test_synthetic_archive_exact_record_cap_and_append_rejection():
    """Validate 9528 independent hours below the byte cap and reject a 9529th process-state hour."""
    from src.interfaces.wan_performance.integration.history_repository import SyntheticArchiveStore
    from src.interfaces.wan_performance.integration.record_codec import ArchiveCodec

    identity = {"org_id": "o", "site_id": "s", "gateway_id": "g", "port_name": "p"}
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=397)
    records = [
        {
            "identity": identity,
            "provenance": "synthetic",
            "is_up_observation": None,
            "hour_start_utc": (start + timedelta(hours=offset)).isoformat(),
            "collected_at_utc": (start + timedelta(hours=offset)).isoformat(),
            "metrics": {"m": {"value": 1, "unit": "%"}},
        }
        for offset in range(9528)
    ]
    body = {
        "version": 1,
        "provenance": "synthetic",
        "identity": identity,
        "window": {"start_utc": start.isoformat(), "end_utc": end.isoformat(), "complete": False},
        "records": records,
    }
    payload = json.dumps(body).encode()
    archive = ArchiveCodec.decode(payload)
    assert len(archive["records"]) == 9528 and len(payload) < 8 * 1024 * 1024
    store = SyntheticArchiveStore()
    digest = store.accept(payload, (archive["identity"],), "IMPORT_SYNTHETIC")
    body["records"] = [*records, records[0]]
    assert len(json.dumps(body).encode()) < 8 * 1024 * 1024
    with pytest.raises(ValueError, match="9528"):
        ArchiveCodec.decode(json.dumps(body).encode())
    body["window"] = {
        "start_utc": end.isoformat(),
        "end_utc": (end + timedelta(hours=1)).isoformat(),
        "complete": False,
    }
    body["records"] = [{**records[0], "hour_start_utc": end.isoformat(), "collected_at_utc": end.isoformat()}]
    with pytest.raises(ValueError, match="9528"):
        store.accept(json.dumps(body).encode(), (archive["identity"],), "IMPORT_SYNTHETIC")
    assert store.export("o", digest) == payload


@pytest.mark.parametrize("extra_byte", [0, 1])
def test_synthetic_archive_exact_combined_state_byte_bound(archive_payload, extra_byte):
    """Reject one byte beyond the real combined archive and projection-state limit without eviction."""
    from src.interfaces.wan_performance.integration.history_repository import SyntheticArchiveStore
    from src.interfaces.wan_performance.integration.record_codec import ArchiveCodec

    original = json.dumps(archive_payload).encode()
    archive = ArchiveCodec.decode(original)
    row_bytes = json.dumps(archive["records"][0].to_dict(), sort_keys=True, allow_nan=False).encode()
    payload = original + b" " * (8 * 1024 * 1024 - len(original) - len(row_bytes) + extra_byte)
    store = SyntheticArchiveStore()
    if extra_byte:
        with pytest.raises(ValueError, match="eight MiB"):
            store.accept(payload, (archive["identity"],), "IMPORT_SYNTHETIC")
        assert store.entries == {}
    else:
        digest = store.accept(payload, (archive["identity"],), "IMPORT_SYNTHETIC")
        assert store.export(archive["identity"].to_dict()["org_id"], digest) == payload


def test_synthetic_archive_import_export_and_live_codec_isolation(archive_payload):
    """Retain exact archive bytes and provenance without enabling application history admission."""
    import hashlib

    from src.interfaces.wan_performance.integration.history_repository import SyntheticArchiveStore
    from src.interfaces.wan_performance.integration.record_codec import ArchiveCodec, RecordCodec

    payload = json.dumps(archive_payload).encode()
    archive = ArchiveCodec.decode(payload)
    store = SyntheticArchiveStore()
    digest = store.accept(payload, (archive["identity"],), "IMPORT_SYNTHETIC")
    assert digest == hashlib.sha256(payload).hexdigest()
    assert store.accept(payload, (archive["identity"],), "IMPORT_SYNTHETIC") == digest
    assert store.export(archive["identity"].to_dict()["org_id"], digest) == payload
    with pytest.raises(ValueError, match="synthetic"):
        RecordCodec.encode(archive["records"][0])
    with pytest.raises(ValueError, match="unavailable"):
        store.export("foreign", digest)


@pytest.mark.parametrize(
    "state",
    [
        "extra",
        "boolean-version",
        "complete",
        "missing-window",
        "duplicate",
        "foreign",
        "provenance",
        "outside",
        "raw",
        "boolean-value",
        "naive",
        "overlong",
        "too-many",
    ],
)
def test_archive_codec_rejects_invalid_records_before_storage(archive_payload, state):
    """Reject ambiguous envelope or record evidence rather than construct successful incomplete imports."""
    from src.interfaces.wan_performance.integration.record_codec import ArchiveCodec

    if state == "extra":
        archive_payload["extra"] = "Unsupported"
    if state == "boolean-version":
        archive_payload["version"] = True
    if state == "complete":
        archive_payload["window"]["complete"] = True
    if state == "missing-window":
        archive_payload["window"].pop("end_utc")
    if state == "duplicate":
        archive_payload["records"] *= 2
    if state == "foreign":
        archive_payload["records"][0]["identity"] = {**archive_payload["identity"], "org_id": "foreign"}
    if state == "provenance":
        archive_payload["records"][0]["provenance"] = "live"
    if state == "outside":
        archive_payload["window"]["start_utc"] = archive_payload["window"]["end_utc"]
    if state == "raw":
        next(iter(archive_payload["records"][0]["metrics"].values()))["raw_values"] = [1]
    if state == "boolean-value":
        next(iter(archive_payload["records"][0]["metrics"].values()))["value"] = True
    if state == "naive":
        archive_payload["records"][0]["collected_at_utc"] = "2024-01-01T12:34:00"
    if state == "overlong":
        archive_payload["window"]["end_utc"] = "2028-01-01T00:00:00+00:00"
    if state == "too-many":
        archive_payload["records"] *= 9529
    with pytest.raises((ValueError, KeyError)):
        ArchiveCodec.decode(json.dumps(archive_payload).encode())


@pytest.fixture
def declaration_payload():
    """Describe independently authored metadata only for an isolated operator-state test."""
    identity = OfflinePreviewFactory.build().measurements[0].identity
    return identity, {
        "version": 1,
        "provenance": "operator-declaration",
        "identity": identity.to_dict(),
        "effective": {"start_utc": "2024-01-01T00:00:00+00:00", "end_utc": "2024-02-01T00:00:00+00:00"},
        "values": {"capacity_bps": 1000, "region": "Synthetic test region", "role": "Declared test role"},
    }


def test_operator_declarations_replay_export_and_conflict_are_isolated(declaration_payload):
    """Export declared metadata and reject changes without modifying observed records."""
    from src.interfaces.wan_performance.integration.history_repository import OperatorDeclarations

    identity, payload = declaration_payload
    store = OperatorDeclarations()
    encoded = json.dumps(payload).encode()
    assert store.accept(encoded, (identity,), "DECLARE") == "Declaration accepted."
    assert store.accept(encoded, (identity,), "DECLARE") == "Identical declaration preserved."
    changed = {**payload, "values": {"capacity_bps": 2000}}
    with pytest.raises(ValueError, match="conflict"):
        store.accept(json.dumps(changed).encode(), (identity,), "DECLARE")
    exported = json.loads(store.export(identity.to_dict()["org_id"]))
    assert exported["declarations"] == [payload] and exported["provenance"] == "operator-declaration"
    assert json.loads(store.export("foreign"))["declarations"] == []


@pytest.mark.parametrize("value", [True, 0, -1, float("inf"), None, "1000"])
def test_operator_declarations_reject_invalid_capacity_before_state_change(declaration_payload, value):
    """Reject invalid declared numbers without substituting observed capacity."""
    from src.interfaces.wan_performance.integration.history_repository import OperatorDeclarations

    identity, payload = declaration_payload
    store = OperatorDeclarations()
    payload["values"] = {"capacity_bps": value}
    with pytest.raises(ValueError, match="capacity"):
        store.accept(json.dumps(payload).encode(), (identity,), "DECLARE")
    assert json.loads(store.export(identity.to_dict()["org_id"]))["declarations"] == []


@pytest.mark.parametrize("state", ["confirmation", "membership", "empty", "unknown", "naive", "reversed", "control"])
def test_operator_declarations_reject_unverified_input(declaration_payload, state):
    """Reject missing membership, malformed bounds, and undeclared or unsafe text."""
    from src.interfaces.wan_performance.integration.history_repository import OperatorDeclarations

    identity, payload = declaration_payload
    if state == "empty":
        payload["values"] = {}
    if state == "unknown":
        payload["extra"] = "Unsupported"
    if state == "naive":
        payload["effective"]["start_utc"] = "2024-01-01T00:00:00"
    if state == "reversed":
        payload["effective"]["end_utc"] = "2023-01-01T00:00:00+00:00"
    if state == "control":
        payload["values"] = {"region": "unsafe\ntext"}
    store = OperatorDeclarations()
    with pytest.raises(ValueError):
        store.accept(
            json.dumps(payload).encode(),
            () if state == "membership" else (identity,),
            "declare" if state == "confirmation" else "DECLARE",
        )
    assert json.loads(store.export(identity.to_dict()["org_id"]))["declarations"] == []


def test_operator_declarations_cap_preserves_identical_replay_and_rejects_append(declaration_payload):
    """Exercise the exact per-organization cap without silently replacing an existing declaration."""
    from src.interfaces.wan_performance.integration.history_repository import OperatorDeclarations

    identity, payload = declaration_payload
    store = OperatorDeclarations()
    start = datetime(2024, 1, 1, tzinfo=UTC)
    for offset in range(1000):
        payload["effective"] = {
            "start_utc": (start + timedelta(hours=offset)).isoformat(),
            "end_utc": (start + timedelta(hours=offset + 1)).isoformat(),
        }
        store.accept(json.dumps(payload).encode(), (identity,), "DECLARE")
    assert store.accept(json.dumps(payload).encode(), (identity,), "DECLARE") == "Identical declaration preserved."
    before = store.export(identity.to_dict()["org_id"])
    payload["effective"]["end_utc"] = (start + timedelta(hours=1001)).isoformat()
    with pytest.raises(ValueError, match="1000"):
        store.accept(json.dumps(payload).encode(), (identity,), "DECLARE")
    assert store.export(identity.to_dict()["org_id"]) == before
    assert len(json.loads(before)["declarations"]) == 1000


@pytest.fixture(
    params=[
        (datetime(2025, 3, 1, tzinfo=UTC), 9456, 9455),
        (datetime(2025, 1, 1, tzinfo=UTC), 9528, 9527),
        (datetime(2025, 1, 1, tzinfo=UTC), 9528, 9528),
    ]
)
def synthetic_horizon(request):
    """Generate independent synthetic hour keys, including the 397-day leap-year maximum."""
    end, expected_hours, expected_records = request.param
    start, end = CalendarWindow.thirteen_months_ending(end)
    original = OfflinePreviewFactory.build().measurements[0]
    records = tuple(
        replace(
            original,
            hour_start_utc=start + timedelta(hours=index),
            collected_at_utc=start + timedelta(hours=index, minutes=1),
            metrics={"loss": MetricMeasurement(index % 101, "%")},
            provenance="synthetic",
            is_up_observation=None,
        )
        for index in range(expected_hours)
        if expected_records == expected_hours or index != 24
    )
    return start, end, expected_hours, expected_records, records


@pytest.fixture
def synthetic_sqlite_rows(synthetic_horizon):
    """Encode synthetic payloads without invoking or changing the application codec."""
    start, end, _, _, records = synthetic_horizon
    boundaries = tuple(
        replace(records[0], hour_start_utc=hour, collected_at_utc=hour + timedelta(minutes=1))
        for hour in (start - timedelta(hours=1), end)
    )
    other = replace(records[0], identity=replace(records[0].identity, port_name="other-synthetic-port"))
    other_tenant = replace(
        records[0],
        identity=replace(
            records[0].identity,
            gateway=replace(
                records[0].identity.gateway,
                site=replace(records[0].identity.gateway.site, org_id="other-synthetic-org"),
            ),
        ),
    )
    return tuple(
        (json.dumps(record.identity.natural_key), record.hour_start_utc.isoformat(), json.dumps(record.to_dict()))
        for record in (*records, *boundaries, other, other_tenant)
    )


def test_synthetic_thirteen_month_sqlite_payload_scope_and_gaps(history, synthetic_horizon, synthetic_sqlite_rows):
    """Exercise real temporary SQLite storage without claiming application acceptance or production history."""
    start, end, expected_hours, expected_records, records = synthetic_horizon
    history.upsert(())
    statement = (
        "INSERT INTO wan_performance_hours VALUES (?, ?, ?) "
        "ON CONFLICT(identity,hour) DO UPDATE SET payload=excluded.payload"
    )
    with closing(sqlite3.connect(history.path)) as connection, connection:
        connection.executemany(statement, synthetic_sqlite_rows)
        connection.executemany(statement, synthetic_sqlite_rows)
        rows = connection.execute(
            "SELECT payload FROM wan_performance_hours WHERE identity=? AND hour>=? AND hour<? ORDER BY hour LIMIT ?",
            (json.dumps(records[0].identity.natural_key), start.isoformat(), end.isoformat(), MAX_HISTORY_RECORDS),
        ).fetchall()
        total = connection.execute("SELECT COUNT(*) FROM wan_performance_hours").fetchone()[0]
    assert (end - start).total_seconds() == expected_hours * 3600
    assert len(rows) == expected_records and total == expected_records + 4
    assert tuple(json.loads(row[0]) for row in rows) == tuple(record.to_dict() for record in records)
    with pytest.raises(ValueError, match="must contain a live"):
        history.read(records[0].identity, start, end)
    with pytest.raises(ValueError, match="synthetic"):
        history.upsert(records)


def test_synthetic_thirteen_month_mocked_arango_keeps_query_bounds_and_codec_guard(synthetic_horizon):
    """Verify mocked query scope and rejection, not actual Arango persistence or capacity."""
    start, end, expected_hours, expected_records, records = synthetic_horizon
    database, cursor = MagicMock(), MagicMock(spec=Cursor)
    cursor.__iter__.return_value = iter(json.dumps(record.to_dict()) for record in records)
    database.aql.execute.return_value = cursor
    history = ArangoHistory(database)
    with pytest.raises(ValueError, match="must contain a live"):
        history.read(records[0].identity, start, end)
    bindings = database.aql.execute.call_args.kwargs["bind_vars"]
    assert bindings == {
        "@collection": "wan_performance_hours",
        "identity": json.dumps(records[0].identity.natural_key),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "limit": MAX_HISTORY_RECORDS,
    }
    assert len(records) == expected_records and records[-1].provenance == "synthetic"
    assert (end - start).total_seconds() == expected_hours * 3600
    cursor.close.assert_called_once_with()
    with pytest.raises(ValueError, match="synthetic"):
        history.upsert(records)
    database.begin_transaction.assert_not_called()


def live_sample(record, minute_offset=0):
    """Build one deterministic poll sample from an isolated live-labeled record."""
    sampled_at = record.hour_start_utc + timedelta(minutes=minute_offset)
    return SampleMeasurement(
        record.identity,
        sampled_at,
        sampled_at,
        record.metrics,
        {"loss": 0.0},
        "poll",
        False,
        "live",
        record.is_up_observation,
    )


def test_round_trip_and_idempotent_upsert(history):
    """Preserve the complete identity and replace duplicate natural keys."""
    record = live_record()
    history.upsert((record, record))
    result = history.read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1))
    assert result == (record,)
    assert result[0].to_dict() == record.to_dict()


def test_history_round_trip_preserves_sampled_link_state(history):
    """Persist boolean state evidence so historical summaries can use it."""
    record = replace(live_record(), is_up_observation=False)
    history.upsert((record,))

    result = history.read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1))

    assert result[0].is_up_observation is False


def test_raw_samples_append_distinct_observations_within_one_hour(history):
    """Keep repeated polls distinct while the hourly projection keeps one key."""
    record = live_record()
    first, second = live_sample(record), live_sample(record, 5)

    history.upsert((first.to_hourly(), second.to_hourly()), (first, second))

    start = record.hour_start_utc
    end = start + timedelta(hours=1)
    assert history.read_samples(record.identity, start, end) == (first, second)
    hourly = history.read(record.identity, start, end)
    assert len(hourly) == 1
    assert hourly[0].collected_at_utc == second.collected_at_utc


def test_sqlite_api_sample_replay_keeps_one_original_sample(history):
    """Keep an unchanged API observation once when later polls return its timestamp."""
    record = live_record()
    first = replace(live_sample(record), timestamp_source="api")
    replay = replace(first, collected_at_utc=first.collected_at_utc + timedelta(minutes=5))

    history.upsert((), (first, replay))
    history.upsert((), (replay,))

    start = record.hour_start_utc
    end = start + timedelta(hours=1)
    assert history.read_samples(record.identity, start, end) == (first,)


def test_sqlite_rejects_changed_api_sample_without_replacing_prior_rows(history):
    """Reject changed source data at a stable sample key and roll back hourly updates."""
    record = live_record()
    first = replace(live_sample(record), timestamp_source="api")
    original_hour = first.to_hourly()
    updated_hour = replace(original_hour, collected_at_utc=original_hour.collected_at_utc + timedelta(minutes=5))
    changed = replace(
        first,
        collected_at_utc=first.collected_at_utc + timedelta(minutes=5),
        raw_fields={"loss": 1.0},
    )
    history.upsert((original_hour,), (first,))

    with pytest.raises(ValueError, match="conflicts with stored source data"):
        history.upsert((updated_hour,), (changed,))

    start = record.hour_start_utc
    end = start + timedelta(hours=1)
    assert history.read_samples(record.identity, start, end) == (first,)
    assert history.read(record.identity, start, end) == (original_hour,)


def test_half_open_query_and_identity_isolation(history):
    """Exclude another identity and the upper time boundary."""
    record = live_record()
    next_hour = replace(
        record,
        hour_start_utc=record.hour_start_utc + timedelta(hours=1),
        collected_at_utc=record.collected_at_utc + timedelta(hours=1),
    )
    other = replace(record, identity=replace(record.identity, port_name="another-port"))
    history.upsert((record, next_hour, other))
    assert history.read(record.identity, record.hour_start_utc, next_hour.hour_start_utc) == (record,)


def test_synthetic_batch_is_rejected_before_any_write(history):
    """Keep preview records out of application storage, including mixed batches."""
    record = live_record()
    with pytest.raises(ValueError, match="synthetic"):
        history.upsert((record, replace(record, provenance="synthetic")))
    assert history.read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1)) == ()


def test_synthetic_sample_is_rejected_before_any_write(history):
    """Reject synthetic samples before creating or changing history tables."""
    record = live_record()
    with pytest.raises(ValueError, match="synthetic"):
        history.upsert((), (replace(live_sample(record), provenance="synthetic"),))
    with sqlite3.connect(history.path) as connection:
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    assert tables == []


def test_missing_database_is_not_created(tmp_path):
    """Never create a second database when configured storage is absent."""
    path = tmp_path / "missing.db"
    history = SQLiteHistory(path)
    with pytest.raises(sqlite3.OperationalError):
        history.upsert((live_record(),))
    assert not path.exists()


def test_invalid_window_is_rejected(history):
    """Reject an empty query instead of returning success-shaped missing history."""
    record = live_record()
    with pytest.raises(ValueError, match="window"):
        history.read(record.identity, record.hour_start_utc, record.hour_start_utc)


def test_history_read_supports_thirteen_month_window(history):
    """Accept the maximum configured calendar horizon in the existing store."""
    record = live_record()
    history.upsert((record,))
    start = record.hour_start_utc
    end = start + timedelta(days=MAX_HISTORY_WINDOW_DAYS)
    assert history.read(record.identity, start, end) == (record,)


def test_history_read_rejects_window_above_thirteen_month_bound(history):
    """Reject requests that exceed the fixed history and record limits."""
    record = live_record()
    start = record.hour_start_utc
    end = start + timedelta(days=MAX_HISTORY_WINDOW_DAYS, seconds=1)
    with pytest.raises(ValueError, match="at most"):
        history.read(record.identity, start, end)


def test_corrupt_persisted_data_is_not_a_success(history):
    """Surface database corruption instead of displaying false missing history."""
    record = live_record()
    history.upsert((record,))
    with sqlite3.connect(history.path) as connection:
        connection.execute("UPDATE wan_performance_hours SET payload='{}'")
    with pytest.raises(ValueError, match="live"):
        history.read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1))


def test_arango_upserts_use_stable_keys_and_transaction():
    """Reuse one configured database and replace the same natural key."""
    database = MagicMock()
    history = ArangoHistory(database)
    record = live_record()
    history.upsert((record, record))
    transaction = database.begin_transaction.return_value
    database.begin_transaction.assert_called_once_with(write=["wan_performance_hours", "wan_performance_samples"])
    transaction.collection.assert_any_call("wan_performance_hours")
    documents = transaction.collection.return_value.insert.call_args_list
    assert documents[0].args[0] == documents[1].args[0]
    assert documents[0].kwargs == {"overwrite": True, "overwrite_mode": "replace"}
    transaction.commit_transaction.assert_called_once_with()


def test_arango_write_failure_aborts():
    """Rollback a partial batch and preserve the original failure."""
    database = MagicMock()
    transaction = database.begin_transaction.return_value
    transaction.collection.return_value.insert.side_effect = ConnectionError("store unavailable")
    with pytest.raises(ConnectionError, match="store unavailable"):
        ArangoHistory(database).upsert((live_record(),))
    transaction.abort_transaction.assert_called_once_with()
    transaction.commit_transaction.assert_not_called()


def test_arango_read_failure_is_explicit():
    """Do not treat unavailable configured storage as an empty query."""
    database = MagicMock()
    database.aql.execute.side_effect = ConnectionError("unavailable")
    record = live_record()
    with pytest.raises(ConnectionError, match="unavailable"):
        ArangoHistory(database).read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1))


def test_arango_appends_raw_samples_to_the_same_transaction():
    """Store different poll timestamps under distinct stable sample keys."""
    database = MagicMock()
    transaction = database.begin_transaction.return_value
    hours, samples = MagicMock(), MagicMock()
    transaction.collection.side_effect = lambda name: {
        "wan_performance_hours": hours,
        "wan_performance_samples": samples,
    }[name]
    samples.get.return_value = None
    record = live_record()
    first, second = live_sample(record), live_sample(record, 5)

    ArangoHistory(database).upsert((first.to_hourly(), second.to_hourly()), (first, second))

    assert hours.insert.call_count == 2
    assert samples.insert.call_count == 2
    assert samples.insert.call_args_list[0].args[0]["_key"] != samples.insert.call_args_list[1].args[0]["_key"]
    assert samples.insert.call_args_list[0].kwargs == {}
    transaction.commit_transaction.assert_called_once_with()


def test_arango_api_sample_replay_is_idempotent_and_rejects_changes():
    """Preserve the first Arango payload and abort changed source data."""
    from src.interfaces.wan_performance.integration.record_codec import SampleRecordCodec

    database = MagicMock()
    transaction = database.begin_transaction.return_value
    hours, samples = MagicMock(), MagicMock()
    transaction.collection.side_effect = lambda name: {
        "wan_performance_hours": hours,
        "wan_performance_samples": samples,
    }[name]
    record = live_record()
    first = replace(live_sample(record), timestamp_source="api")
    replay = replace(first, collected_at_utc=first.collected_at_utc + timedelta(minutes=5))
    changed = replace(replay, raw_fields={"loss": 1.0})
    stored_payload = SampleRecordCodec.encode(first)
    samples.get.side_effect = [None, {"payload": stored_payload}, {"payload": stored_payload}]
    history = ArangoHistory(database)

    history.upsert((), (first,))
    history.upsert((), (replay,))
    with pytest.raises(ValueError, match="conflicts with stored source data"):
        history.upsert((), (changed,))

    assert samples.insert.call_count == 1
    assert transaction.commit_transaction.call_count == 2
    transaction.abort_transaction.assert_called_once_with()


def test_arango_connect_uses_existing_database_and_finite_timeout():
    """Use the public driver boundary without creating another application database."""
    config = MagicMock(standalone_mode=False, arango_host="http://existing.invalid", arango_database="misthelper")
    with patch("src.interfaces.wan_performance.integration.arango_history.ArangoClient") as client:
        database = client.return_value.db.return_value
        database.has_collection.return_value = True
        repository = ArangoHistory.connect(config)
    assert repository.database is database
    client.assert_called_once_with(hosts=config.arango_host, request_timeout=2)
    assert client.return_value.db.call_args.args == ("misthelper",)
    database.create_collection.assert_not_called()


def test_selected_sqlite_path_does_not_open_arango(tmp_path):
    """Follow DataExporter's active primary selection without a database mirror."""
    with (
        patch("src.interfaces.wan_performance.integration.history_repository.SourceDependencyResolver") as resolver,
        patch.object(ArangoHistory, "connect") as connect,
    ):
        resolver.OUTPUT_FORMAT = "sqlite"
        resolver.DATABASE_PATH = str(tmp_path / "application.db")
        repository = HistorySelection.open()
    assert isinstance(repository, SQLiteHistory)
    assert repository.path == tmp_path / "application.db"
    connect.assert_not_called()


def test_selected_csv_uses_existing_configured_arango():
    """Use the configured application document store, never another SQLite file."""
    with (
        patch("src.interfaces.wan_performance.integration.history_repository.SourceDependencyResolver") as resolver,
        patch("src.interfaces.wan_performance.integration.history_repository.DatabaseConfig.from_env") as config,
        patch.object(ArangoHistory, "connect") as connect,
    ):
        resolver.OUTPUT_FORMAT = "csv"
        selected = HistorySelection.open()
    config.assert_called_once_with()
    connect.assert_called_once_with(config.return_value)
    assert selected is connect.return_value


def test_csv_standalone_refuses_history_without_opening_arango():
    """CSV-only output cannot appear to have durable history."""
    with (
        patch("src.interfaces.wan_performance.integration.history_repository.SourceDependencyResolver") as resolver,
        patch(
            "src.interfaces.wan_performance.integration.history_repository.DatabaseConfig.from_env",
            return_value=MagicMock(standalone_mode=True),
        ),
        patch("src.interfaces.wan_performance.integration.arango_history.ArangoClient") as client,
    ):
        resolver.OUTPUT_FORMAT = "csv"
        with pytest.raises(ConnectionError, match="CSV-only"):
            HistorySelection.open()
    client.assert_not_called()


def test_unsupported_output_format_has_no_store_fallback():
    """Reject invalid selection rather than silently choosing a durable backend."""
    with patch("src.interfaces.wan_performance.integration.history_repository.SourceDependencyResolver") as resolver:
        resolver.OUTPUT_FORMAT = "unsupported"
        with pytest.raises(ValueError, match="output selection"):
            HistorySelection.open()


def test_arango_reads_bind_full_identity_and_close_cursor():
    """Verify query isolation and revalidated round-trip data through public AQL."""
    from src.interfaces.wan_performance.integration.record_codec import RecordCodec

    record = live_record()
    cursor = MagicMock(spec=Cursor)
    cursor.__iter__.return_value = iter([RecordCodec.encode(record)])
    database = MagicMock()
    database.aql.execute.return_value = cursor
    result = ArangoHistory(database).read(
        record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1)
    )
    assert result == (record,)
    assert "FILTER record.identity == @identity" in database.aql.execute.call_args.args[0]
    assert database.aql.execute.call_args.kwargs["bind_vars"]["@collection"] == "wan_performance_hours"
    cursor.close.assert_called_once_with()


def test_arango_sample_read_binds_identity_and_sample_collection():
    """Query raw samples by full identity and half-open UTC timestamps."""
    from src.interfaces.wan_performance.integration.record_codec import SampleRecordCodec

    record = live_record()
    sample = live_sample(record)
    cursor = MagicMock(spec=Cursor)
    cursor.__iter__.return_value = iter([SampleRecordCodec.encode(sample)])
    database = MagicMock()
    database.aql.execute.return_value = cursor

    result = ArangoHistory(database).read_samples(
        record.identity,
        record.hour_start_utc,
        record.hour_start_utc + timedelta(hours=1),
    )

    assert result == (sample,)
    assert "FILTER record.identity == @identity" in database.aql.execute.call_args.args[0]
    assert database.aql.execute.call_args.kwargs["bind_vars"]["@collection"] == "wan_performance_samples"
    cursor.close.assert_called_once_with()


def test_arango_history_read_binds_thirteen_month_record_limit():
    """Keep the requested record count fixed and prevent an unbounded AQL read."""
    from src.interfaces.wan_performance.integration.record_codec import RecordCodec

    record = live_record()
    cursor = MagicMock(spec=Cursor)
    cursor.__iter__.return_value = iter([RecordCodec.encode(record)])
    database = MagicMock()
    database.aql.execute.return_value = cursor
    ArangoHistory(database).read(
        record.identity,
        record.hour_start_utc,
        record.hour_start_utc + timedelta(days=MAX_HISTORY_WINDOW_DAYS),
    )
    assert database.aql.execute.call_args.kwargs["bind_vars"]["limit"] == MAX_HISTORY_RECORDS


def test_sqlite_rolls_back_entire_failed_batch(history):
    """Prove that a second-row error cannot leave a partial update."""
    record = live_record()
    history.upsert((record,))
    with sqlite3.connect(history.path) as connection:
        connection.execute(
            "CREATE TRIGGER reject_other BEFORE INSERT ON wan_performance_hours "
            "WHEN NEW.identity LIKE '%other-port%' BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
        )
    updated = replace(record, collected_at_utc=record.collected_at_utc + timedelta(minutes=1))
    other = replace(record, identity=replace(record.identity, port_name="other-port"))
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        history.upsert((updated, other))
    assert history.read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1)) == (record,)
