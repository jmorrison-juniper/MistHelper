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
from src.interfaces.wan_performance.integration.arango_history import ArangoHistory
from src.interfaces.wan_performance.integration.history_repository import HistorySelection
from src.interfaces.wan_performance.integration.sqlite_history import SQLiteHistory
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
