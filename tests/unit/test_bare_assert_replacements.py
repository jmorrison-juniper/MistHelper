"""Tests for runtime guards that replace shipped-code assertions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.gateway.wan2_variable import GatewayWan2VariableMigrator, Wan2VariableDeps
from src.gateway.wan_probe_device_override_manager import WANProbeDeviceOverrideManager
from src.refactors.device_data_fetcher import DeviceDataFetcher, DeviceFetchConfig
from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter


@pytest.mark.parametrize(
    ("method_name", "args", "message"),
    [
        ("_find_template_sites", (), "Template must be selected before finding sites"),
        ("_show_preview", ([], False), "Template must be selected"),
        ("_print_preview_header", ([], 0), "Template must be selected"),
        ("_update_single_device", ({"device_name": "gw-1"}, True), "Template must be selected"),
        ("_initial_device_result", ({"device_name": "gw-1"},), "Template must be selected"),
        ("_generate_report", ([], True), "Template must be selected"),
    ],
)
def test_wan_probe_requires_selected_template(method_name: str, args: tuple[object, ...], message: str) -> None:
    """Template-dependent helpers raise a named error when no template is selected."""
    manager = WANProbeDeviceOverrideManager()  # Build the manager without operator input.
    method = getattr(manager, method_name)  # Select the helper that used to contain a bare assert.

    with pytest.raises(RuntimeError, match=message):  # Prove the named guard stays active under python -O.
        method(*args)  # Drive the invalid missing-template state.


def test_device_fetcher_requires_site_before_device_selection() -> None:
    """Device selection raises a named error when the site identifier is missing."""
    config = DeviceFetchConfig(MagicMock(), "out.csv", "Fetch", site_id=None)  # Build missing-site input.
    fetcher = DeviceDataFetcher(config)  # Create the fetcher without a site scope.

    with pytest.raises(RuntimeError, match="Site ID must be resolved before device ID"):  # Assert the field name.
        fetcher._resolve_device_id()  # Drive the invalid missing-site state.


@pytest.mark.parametrize("status_code", [404, 500])
def test_device_fetcher_reports_http_failure_statuses(monkeypatch: pytest.MonkeyPatch, status_code: int) -> None:
    """Device fetch returns a visible failure for HTTP error statuses."""
    monkeypatch.setattr("MistHelper.apisession", MagicMock(), raising=False)  # Avoid a live Mist session.
    response = SimpleNamespace(status_code=status_code, data={"error": "cloud"})  # Model a cloud HTTP error.
    fetch_function = MagicMock(return_value=response)  # Return the modeled cloud response.
    config = DeviceFetchConfig(fetch_function, "out.csv", "Fetch", site_id="site-1", device_id="dev-1")
    fetcher = DeviceDataFetcher(config)  # Build the fetcher with valid scope identifiers.

    result = fetcher._fetch_data()  # Drive the HTTP error path.

    assert result is False  # Prove the caller can distinguish cloud failure from an empty response.


def test_wan2_fast_mode_requires_connection_pool() -> None:
    """Fast migration raises a named error when the executor is missing."""
    deps = Wan2VariableDeps(  # Build dependencies with the fast executor deliberately absent.
        org_id="org-1",
        apisession=MagicMock(),
        site_exclude_prefix="",
        check_and_generate_csv_fn=MagicMock(),
        generate_templates_fn=MagicMock(),
        generate_sites_fn=MagicMock(),
        get_csv_path_fn=MagicMock(return_value="local.csv"),
        save_data_fn=MagicMock(),
        input_fn=MagicMock(return_value="cancel"),
        execute_fn=None,
    )
    migrator = GatewayWan2VariableMigrator(deps)  # Create the migrator with no pool executor.

    with pytest.raises(RuntimeError, match="Connection pool executor must be configured for fast mode"):
        migrator._migrate_devices_fast([])  # Drive fast mode without the executor.


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("_create_table_and_indexes", ()),
        ("_create_schema_table", ()),
        ("_create_schema_indexes", ()),
        ("_determine_insert_mode", ()),
        ("_insert_single_row", (0, {"id": "row-1"}, "INSERT", ["id"], "now")),
    ],
)
def test_sqlite_writer_cursor_methods_require_cursor(method_name: str, args: tuple[object, ...]) -> None:
    """Cursor-dependent writer helpers raise a named error when the cursor is missing."""
    writer = SQLiteDatabaseWriter.__new__(SQLiteDatabaseWriter)  # Bypass setup to model a failed connect.
    writer.cursor = None  # Set the invalid state that a missing connection would leave.
    method = getattr(writer, method_name)  # Select the helper that used to contain a bare assert.

    with pytest.raises(RuntimeError, match="Database cursor not initialized"):  # Assert the named field.
        method(*args)  # Drive the invalid missing-cursor state.


def test_sqlite_writer_commit_requires_connection() -> None:
    """Commit verification raises a named error when the connection is missing."""
    writer = SQLiteDatabaseWriter.__new__(SQLiteDatabaseWriter)  # Bypass setup to model a failed connect.
    writer.connection = None  # Set the invalid missing-connection state.
    writer.cursor = MagicMock()  # Provide a cursor so the connection guard runs first.

    with pytest.raises(RuntimeError, match="Database connection not initialized"):  # Assert the named field.
        writer._commit_and_verify(1)  # Drive commit with no connection.


def test_sqlite_writer_commit_requires_cursor() -> None:
    """Commit verification raises a named error when the cursor is missing."""
    writer = SQLiteDatabaseWriter.__new__(SQLiteDatabaseWriter)  # Bypass setup to model a failed connect.
    writer.connection = MagicMock()  # Provide a connection so the cursor guard runs second.
    writer.cursor = None  # Set the invalid missing-cursor state.

    with pytest.raises(RuntimeError, match="Database cursor not initialized"):  # Assert the named field.
        writer._commit_and_verify(1)  # Drive verification with no cursor.
