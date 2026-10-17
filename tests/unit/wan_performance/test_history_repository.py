"""Check WAN history against the existing SQLite file without live credentials."""

import sqlite3
from dataclasses import replace
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from arango.cursor import Cursor

from src.interfaces.portals.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS
from src.interfaces.portals.wan_performance.integration.arango_history import ArangoHistory
from src.interfaces.portals.wan_performance.integration.history_repository import HistorySelection
from src.interfaces.portals.wan_performance.integration.sqlite_history import SQLiteHistory
from src.interfaces.portals.wan_performance.presentation.offline_preview import OfflinePreviewFactory


@pytest.fixture
def history(tmp_path):
    """Use an existing isolated application database for repository checks."""
    path = tmp_path / "application.db"
    sqlite3.connect(path).close()
    return SQLiteHistory(path)


def live_record():
    """Use independent synthetic inputs labeled live only in an isolated test."""
    return replace(OfflinePreviewFactory.build().measurements[0], provenance="live")


def test_round_trip_and_idempotent_upsert(history):
    """Preserve the complete identity and replace duplicate natural keys."""
    record = live_record()
    history.upsert((record, record))
    result = history.read(record.identity, record.hour_start_utc, record.hour_start_utc + timedelta(hours=1))
    assert result == (record,)
    assert result[0].to_dict() == record.to_dict()


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
    """Accept the maximum source-compatible calendar horizon in the configured store."""
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
    database.begin_transaction.assert_called_once_with(write=["wan_performance_hours"])
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


def test_arango_connect_uses_existing_database_and_finite_timeout():
    """Use the public driver boundary without creating another application database."""
    config = MagicMock(standalone_mode=False, arango_host="http://existing.invalid", arango_database="misthelper")
    with patch("src.interfaces.portals.wan_performance.integration.arango_history.ArangoClient") as client:
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
        patch(
            "src.interfaces.portals.wan_performance.integration.history_repository.SourceDependencyResolver"
        ) as resolver,
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
        patch(
            "src.interfaces.portals.wan_performance.integration.history_repository.SourceDependencyResolver"
        ) as resolver,
        patch(
            "src.interfaces.portals.wan_performance.integration.history_repository.DatabaseConfig.from_env"
        ) as config,
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
        patch(
            "src.interfaces.portals.wan_performance.integration.history_repository.SourceDependencyResolver"
        ) as resolver,
        patch(
            "src.interfaces.portals.wan_performance.integration.history_repository.DatabaseConfig.from_env",
            return_value=MagicMock(standalone_mode=True),
        ),
        patch("src.interfaces.portals.wan_performance.integration.arango_history.ArangoClient") as client,
    ):
        resolver.OUTPUT_FORMAT = "csv"
        with pytest.raises(ConnectionError, match="CSV-only"):
            HistorySelection.open()
    client.assert_not_called()


def test_unsupported_output_format_has_no_store_fallback():
    """Reject invalid selection rather than silently choosing a durable backend."""
    with patch(
        "src.interfaces.portals.wan_performance.integration.history_repository.SourceDependencyResolver"
    ) as resolver:
        resolver.OUTPUT_FORMAT = "unsupported"
        with pytest.raises(ValueError, match="output selection"):
            HistorySelection.open()


def test_arango_reads_bind_full_identity_and_close_cursor():
    """Verify query isolation and revalidated round-trip data through public AQL."""
    from src.interfaces.portals.wan_performance.integration.record_codec import RecordCodec

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


def test_arango_history_read_binds_thirteen_month_record_limit():
    """Keep the requested record count fixed and prevent an unbounded AQL read."""
    from src.interfaces.portals.wan_performance.integration.record_codec import RecordCodec

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
