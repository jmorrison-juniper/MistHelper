"""Wave 12 P2 coverage for src/refactors/sqlite_database_writer.py (initiative #1018).

Covers the SQLiteDatabaseWriter full write() pipeline including happy-path
inserts, validation branches, directory creation errors, sqlite3.Error path,
unexpected-exception path, rollback/close resilience, and both natural_pk
(INSERT OR REPLACE) and auto-increment (INSERT with pre-clear) modes.

All MistHelper-owned dependencies (`DatabaseSchemaUtils`, `DataProcessingUtils`,
`DATABASE_PATH`) are patched at the module level so no real MistHelper state is
mutated and no filesystem I/O occurs beyond the per-test tmp_path fixture.
"""

from __future__ import annotations  # PEP 604 unions across Python 3.10-3.13 test runs

import sqlite3  # WHY: sqlite3.Error type used for raising into except-branch tests
from pathlib import Path  # WHY: tmp_path fixture returns pathlib.Path objects
from types import SimpleNamespace  # WHY: build stand-in namespace matching writer._deps shape
from typing import Any, cast  # WHY: cast() lets tests pass wrong-type inputs without # type: ignore
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) for collaborators

import pytest  # WHY: monkeypatch, caplog, tmp_path fixtures

from src.refactors import sqlite_database_writer as swr_mod  # WHY: module handle for monkeypatching
from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter  # WHY: SUT direct import

# ---------------------------------------------------------------------------
# Fixture: install stub deps so no MistHelper.py import cost per test
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_deps(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> SimpleNamespace:
    """Patch _resolve_runtime_dependencies to return an all-MagicMock deps bundle.

    Each collaborator is a MagicMock so tests can override behaviour per-test
    without touching real MistHelper attributes. DATABASE_PATH is set to a
    per-test tmp file so `_ensure_database_directory` and `_connect_to_database`
    can operate on a fresh SQLite file without disturbing production data.
    """
    db_file = tmp_path / "sub" / "mist_data.db"  # Nested path forces mkdir branch
    misthelper_ns = SimpleNamespace(DATABASE_PATH=str(db_file))  # Namespace so writer sees .DATABASE_PATH
    schema_utils = MagicMock(name="DatabaseSchemaUtils")  # Stub schema utils collaborator
    processing_utils = MagicMock(name="DataProcessingUtils")  # Stub processing utils collaborator
    processing_utils.escape_multiline.side_effect = lambda x: x  # Pass-through by default
    processing_utils.get_unique_keys.side_effect = lambda rows: sorted(  # Deterministic key set
        {key for row in rows for key in row}
    )
    schema_utils.determine_api_function_name_from_context.return_value = "listInferredFn"  # Fallback name
    schema_utils.get_endpoint_strategy.return_value = {  # Default natural_pk strategy
        "type": "natural_pk",
        "description": "primary key on id column",
    }
    schema_utils.build_create_table_sql.side_effect = lambda tbl, fields, strat: (  # Real DDL
        f"CREATE TABLE IF NOT EXISTS {tbl} ("
        + ", ".join(f"{col} TEXT" for col in [*fields, "misthelper_created_time", "misthelper_updated_time"])
        + ")"
    )
    schema_utils.build_indexes_sql.side_effect = lambda tbl, fields, strat: []  # No extra indexes by default
    deps = SimpleNamespace(
        DatabaseSchemaUtils=schema_utils,
        DataProcessingUtils=processing_utils,
        misthelper_module=misthelper_ns,
    )
    monkeypatch.setattr(swr_mod, "_resolve_runtime_dependencies", lambda: deps)  # Divert deps resolution
    return deps  # Tests can adjust individual mock behaviour via the returned namespace


# ---------------------------------------------------------------------------
# _resolve_runtime_dependencies
# ---------------------------------------------------------------------------


def test_resolve_runtime_dependencies_calls_import_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """The runtime resolver must go through importlib.import_module('MistHelper')."""
    fake_module = SimpleNamespace(  # Fake MistHelper module with only the attrs we need
        DatabaseSchemaUtils="schema-sentinel",
        DataProcessingUtils="processing-sentinel",
    )
    import_calls: list[str] = []  # Track what import_module was asked to load

    def fake_import(name: str) -> object:  # Stand-in for importlib.import_module
        import_calls.append(name)  # Record the requested module name
        return fake_module  # Return the sentinel-bearing namespace

    import importlib as _importlib  # Local import to satisfy mypy strict re: explicit re-export

    monkeypatch.setattr(_importlib, "import_module", fake_import)  # Divert late import
    ns = swr_mod._resolve_runtime_dependencies()  # Invoke the resolver directly

    assert import_calls == ["MistHelper"]  # Only MistHelper should be imported
    assert ns.DatabaseSchemaUtils == "schema-sentinel"  # Value plumbed through to namespace
    assert ns.DataProcessingUtils == "processing-sentinel"  # Value plumbed through to namespace
    assert ns.misthelper_module is fake_module  # Full module handle retained for later lookups


# ---------------------------------------------------------------------------
# Input validation branches
# ---------------------------------------------------------------------------


def test_write_returns_false_when_data_is_empty(stub_deps: SimpleNamespace) -> None:
    """Empty list must short-circuit before any DB access."""
    writer = SQLiteDatabaseWriter([], "t", "listFoo")  # Empty rows list
    assert writer.write() is False  # Guard trips inside _validate_data


def test_write_returns_false_when_data_is_none(stub_deps: SimpleNamespace) -> None:
    """None data must short-circuit before any DB access."""
    writer = SQLiteDatabaseWriter(cast(list[dict[str, Any]], None), "t", "listFoo")  # cast to bypass type-check
    assert writer.write() is False  # Guard trips inside _validate_data (falsy branch)


def test_write_returns_false_when_data_is_not_list(stub_deps: SimpleNamespace) -> None:
    """Wrong-type data (not a list) must be rejected."""
    writer = SQLiteDatabaseWriter(cast(list[dict[str, Any]], {"row": 1}), "t", "listFoo")  # cast: dict, not list
    assert writer.write() is False  # Falls into isinstance check inside _validate_data


def test_write_returns_false_when_table_name_empty(stub_deps: SimpleNamespace) -> None:
    """Empty table name must fail validation."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "", "listFoo")  # Empty table name
    assert writer.write() is False  # Falls into _validate_table_name empty branch


def test_write_returns_false_when_table_name_wrong_type(stub_deps: SimpleNamespace) -> None:
    """Non-string table name must fail validation."""
    writer = SQLiteDatabaseWriter([{"a": 1}], cast(str, 12345), "listFoo")  # cast bypasses strict param typing
    assert writer.write() is False  # Falls into _validate_table_name type-check branch


# ---------------------------------------------------------------------------
# _resolve_api_function_name inference
# ---------------------------------------------------------------------------


def test_write_infers_api_function_name_when_none(stub_deps: SimpleNamespace) -> None:
    """When api_function_name is None, the schema utility's inference is called."""
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "T", None)  # api_fn omitted so inference runs
    assert writer.write() is True  # Full pipeline should succeed with inferred name
    stub_deps.DatabaseSchemaUtils.determine_api_function_name_from_context.assert_called_once()
    assert writer.api_function_name == "listInferredFn"  # Value assigned from mock return


def test_write_uses_provided_api_function_name_verbatim(stub_deps: SimpleNamespace) -> None:
    """When api_function_name is provided, inference is NOT called."""
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "T", "listMyFn")  # api_fn provided
    assert writer.write() is True  # Happy path
    stub_deps.DatabaseSchemaUtils.determine_api_function_name_from_context.assert_not_called()


# ---------------------------------------------------------------------------
# _ensure_database_directory branches
# ---------------------------------------------------------------------------


def test_ensure_database_directory_creates_missing_parent(stub_deps: SimpleNamespace, tmp_path: Path) -> None:
    """When the DB parent directory doesn't exist yet, it must be created."""
    assert not (tmp_path / "sub").exists()  # Precondition - parent absent
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "T", "listX")
    assert writer.write() is True  # Full write should succeed
    assert (tmp_path / "sub").exists()  # Postcondition - parent directory now present


def test_ensure_database_directory_returns_false_on_oserror(
    stub_deps: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OSError during mkdir must abort the write and return False."""
    original_mkdir = Path.mkdir  # Retain reference in case tests are order-sensitive

    def fail_mkdir(self: Path, *args: object, **kwargs: object) -> None:  # Simulate permissions failure
        raise OSError("permission denied")  # Raise the exception path expects

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)  # Divert Path.mkdir to always fail
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "T", "listX")
    assert writer.write() is False  # OSError path returns False
    monkeypatch.setattr(Path, "mkdir", original_mkdir)  # Restore for other tests


# ---------------------------------------------------------------------------
# _process_data branch
# ---------------------------------------------------------------------------


def test_write_returns_false_when_process_data_raises(stub_deps: SimpleNamespace) -> None:
    """Any exception from escape_multiline aborts the write."""
    stub_deps.DataProcessingUtils.escape_multiline.side_effect = RuntimeError("boom")  # Explode processing
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "T", "listX")
    assert writer.write() is False  # _process_data exception branch returns False


# ---------------------------------------------------------------------------
# _determine_fields_and_strategy branches
# ---------------------------------------------------------------------------


def test_write_returns_false_when_no_fields(stub_deps: SimpleNamespace) -> None:
    """Empty field set (no keys) must abort the write."""
    stub_deps.DataProcessingUtils.get_unique_keys.side_effect = lambda rows: []  # Force zero fields
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "T", "listX")
    assert writer.write() is False  # No-fields branch returns False


def test_write_returns_false_when_strategy_lookup_raises(stub_deps: SimpleNamespace) -> None:
    """Any exception from get_endpoint_strategy aborts the write."""
    stub_deps.DatabaseSchemaUtils.get_endpoint_strategy.side_effect = RuntimeError("strategy-error")
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "T", "listX")
    assert writer.write() is False  # Strategy-exception branch returns False


# ---------------------------------------------------------------------------
# _execute_database_operations branches
# ---------------------------------------------------------------------------


def test_write_happy_path_inserts_rows_and_returns_true(
    stub_deps: SimpleNamespace,
    tmp_path: Path,
) -> None:
    """Full happy-path write must persist rows and return True."""
    writer = SQLiteDatabaseWriter(
        [{"id": "row-1", "name": "A"}, {"id": "row-2", "name": "B"}],
        "widgets",
        "listWidgets",
    )
    assert writer.write() is True  # Pipeline should succeed
    db_path = writer._database_path()  # Query the persisted rows back to verify insert count
    with sqlite3.connect(db_path) as conn:  # Open DB and confirm the inserted rows
        cursor = conn.cursor()
        row_count = cursor.execute("SELECT COUNT(*) FROM widgets").fetchone()[0]
    assert row_count == 2  # Both rows must be persisted


def test_write_uses_insert_mode_for_auto_increment_strategy(
    stub_deps: SimpleNamespace,
) -> None:
    """Auto-increment strategy must use DELETE + INSERT (not INSERT OR REPLACE)."""
    stub_deps.DatabaseSchemaUtils.get_endpoint_strategy.return_value = {  # Force auto-increment mode
        "type": "auto_increment",
        "description": "no natural key, using auto-increment id",
    }
    writer = SQLiteDatabaseWriter([{"a": 1}, {"a": 2}], "widgets2", "listWidgets2")
    assert writer.write() is True  # Pipeline should succeed
    db_path = writer._database_path()  # Verify row count post-insert (DELETE + INSERT clears first)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        row_count = cursor.execute("SELECT COUNT(*) FROM widgets2").fetchone()[0]
    assert row_count == 2  # Both rows inserted after the DELETE clear


def test_write_handles_sqlite_error_and_returns_false(
    stub_deps: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """sqlite3.Error during connect must be caught and return False."""

    def raise_sqlite_error(*args: object, **kwargs: object) -> None:  # Force connect() to fail
        raise sqlite3.Error("simulated driver error")  # Land in sqlite3.Error except-branch

    monkeypatch.setattr(sqlite3, "connect", raise_sqlite_error)  # Divert connect
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "widgets3", "listWidgets3")
    assert writer.write() is False  # sqlite3.Error branch returns False


def test_write_handles_unexpected_error_and_returns_false(
    stub_deps: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-SQLite exception during table creation must be caught and return False."""
    stub_deps.DatabaseSchemaUtils.build_create_table_sql.side_effect = RuntimeError("ddl-error")  # Explode DDL
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "widgets4", "listWidgets4")
    assert writer.write() is False  # Unexpected-error branch returns False


def test_write_creates_indexes_when_strategy_provides_them(
    stub_deps: SimpleNamespace,
) -> None:
    """Indexes returned by build_indexes_sql must be executed against the DB."""
    stub_deps.DatabaseSchemaUtils.build_indexes_sql.side_effect = lambda tbl, fields, strat: [
        f"CREATE INDEX IF NOT EXISTS idx_{tbl}_id ON {tbl}(id)"  # Real, executable index DDL
    ]
    writer = SQLiteDatabaseWriter([{"id": "row-1"}], "widgets5", "listWidgets5")
    assert writer.write() is True  # Full pipeline including index creation must succeed
    with sqlite3.connect(writer._database_path()) as conn:  # Verify the index is present
        cursor = conn.cursor()
        idx_names = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()]
    assert "idx_widgets5_id" in idx_names  # Requested index must exist post-write


# ---------------------------------------------------------------------------
# _prepare_row_values / _get_safe_table_name / _prepare_safe_fields
# ---------------------------------------------------------------------------


def test_get_safe_table_name_replaces_unsafe_chars(stub_deps: SimpleNamespace) -> None:
    """Non-alphanumeric characters in the table name must be replaced by underscores."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "my-weird$table", "listX")
    assert writer._get_safe_table_name() == "my_weird_table"  # Dashes/dollars sanitised to underscores


def test_get_safe_table_name_prefixes_leading_digit(stub_deps: SimpleNamespace) -> None:
    """Table names starting with a digit must be prefixed to make them valid SQL identifiers."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "9widgets", "listX")
    assert writer._get_safe_table_name() == "table_9widgets"  # Leading digit gets the safe-prefix


def test_prepare_row_values_stringifies_and_replaces_none(stub_deps: SimpleNamespace) -> None:
    """None values must become empty strings; other values must be stringified."""
    writer = SQLiteDatabaseWriter([{"a": 1, "b": None, "c": True}], "t", "listX")
    writer.fields = ["a", "b", "c"]  # Simulate post-determination field list
    values = writer._prepare_row_values({"a": 1, "b": None, "c": True}, "2024-01-01T00:00:00")
    assert values[:3] == ["1", "", "True"]  # None -> "", 1 -> "1", True -> "True"
    assert values[3] == "2024-01-01T00:00:00"  # First timestamp column
    assert values[4] == "2024-01-01T00:00:00"  # Second timestamp column


def test_prepare_safe_fields_appends_audit_columns(stub_deps: SimpleNamespace) -> None:
    """Safe fields must include the two audit columns appended at the end."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    writer.fields = ["a-b", "c"]  # Unsafe char in first field for sanitiser check
    safe = writer._prepare_safe_fields()
    assert safe == ["a_b", "c", "misthelper_created_time", "misthelper_updated_time"]  # Sanitised + audit


# ---------------------------------------------------------------------------
# _rollback_transaction / _close_connection resilience
# ---------------------------------------------------------------------------


def test_rollback_swallows_rollback_exception(stub_deps: SimpleNamespace) -> None:
    """Rollback failures must NOT propagate - they must be logged and swallowed."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    fake_conn = MagicMock(spec=sqlite3.Connection)  # Stand-in connection with rollback
    fake_conn.rollback.side_effect = RuntimeError("rollback-failed")  # Simulate rollback failure
    writer.connection = fake_conn  # Attach the failing connection
    writer._rollback_transaction()  # Must NOT raise
    fake_conn.rollback.assert_called_once()  # Rollback was attempted


def test_rollback_no_op_when_no_connection(stub_deps: SimpleNamespace) -> None:
    """_rollback_transaction with connection=None must be a silent no-op."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    writer.connection = None  # No connection was ever opened
    writer._rollback_transaction()  # Must return without raising


def test_close_connection_swallows_close_exception(stub_deps: SimpleNamespace) -> None:
    """Failures during close() must NOT propagate."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    fake_conn = MagicMock(spec=sqlite3.Connection)  # Stand-in connection
    fake_conn.close.side_effect = RuntimeError("close-failed")  # Simulate close failure
    writer.connection = fake_conn
    writer._close_connection()  # Must NOT raise
    fake_conn.close.assert_called_once()  # Close was attempted


def test_close_connection_no_op_when_no_connection(stub_deps: SimpleNamespace) -> None:
    """_close_connection with connection=None must be a silent no-op."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    writer.connection = None  # No connection was ever opened
    writer._close_connection()  # Must return without raising


# ---------------------------------------------------------------------------
# _database_path resolves DATABASE_PATH at call-time (monkeypatch friendly)
# ---------------------------------------------------------------------------


def test_database_path_resolved_at_call_time(stub_deps: SimpleNamespace, tmp_path: Path) -> None:
    """The DATABASE_PATH must be read from the module namespace at call-time so tests can patch it."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    initial = writer._database_path()  # Read initial value
    stub_deps.misthelper_module.DATABASE_PATH = str(tmp_path / "another.db")  # Mutate after construction
    later = writer._database_path()  # Re-read
    assert initial != later  # Value picked up dynamically, not cached at construction
    assert later.endswith("another.db")  # Post-mutation value returned


# ---------------------------------------------------------------------------
# _log_sample_insert / _log_row_failure - direct exercise for coverage
# ---------------------------------------------------------------------------


def test_log_sample_insert_only_logs_first_three_rows(
    stub_deps: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Only the first three rows (indices 0-2) get sample-logged."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    with caplog.at_level("DEBUG"):  # Capture debug traces
        writer._log_sample_insert(0, "INSERT")  # First row - should log
        writer._log_sample_insert(2, "INSERT")  # Third row - should log
        writer._log_sample_insert(3, "INSERT")  # Fourth row - should NOT log
        writer._log_sample_insert(100, "INSERT")  # Large index - should NOT log
    matching = [rec for rec in caplog.records if "Row" in rec.getMessage() and "inserted into" in rec.getMessage()]
    assert len(matching) == 2  # Only two of the four calls should have emitted a debug row-inserted line


def test_log_row_failure_emits_error_with_index(
    stub_deps: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Per-row failure logs must include the row index."""
    writer = SQLiteDatabaseWriter([{"a": 1}], "t", "listX")
    with caplog.at_level("ERROR"):  # Capture error records only
        writer._log_row_failure(7, RuntimeError("bad-row"))
    combined = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "Failed to insert row 7" in combined  # Row index and prefix present
    assert "bad-row" in combined  # Error message included in the log line
