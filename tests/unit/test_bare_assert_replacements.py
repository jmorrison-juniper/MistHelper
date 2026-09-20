"""Tests for runtime guards that replace shipped-code assertions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.export import data_exporter as data_exporter_module
from src.export.data_exporter import (
    SKIP_NO_API_FUNCTION_NAME,
    SKIP_ROUTER_UNAVAILABLE,
    DataExporter,
)
from src.firmware.firmware_manager import FirmwareManager
from src.firmware.site_auto_upgrade import _resolve_configurator_kwargs
from src.gateway.wan2_variable import GatewayWan2VariableMigrator, Wan2VariableDeps
from src.gateway.wan_probe_device_override_manager import WANProbeDeviceOverrideManager
from src.refactors.device_data_fetcher import DeviceDataFetcher, DeviceFetchConfig
from src.refactors.sqlite_database_writer import SQLiteDatabaseWriter
from src.refactors.wlanradius_timer_manager import WLANRadiusTimerManager
from src.ssh.runtime.app_runner import AppRunner
from src.websocket.manager import WebSocketManager


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


def test_data_exporter_missing_polyglot_symbols_stays_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Polyglot router setup stays on the safe degraded path when imports are missing."""
    monkeypatch.setattr(data_exporter_module, "configure_db_logging", None)  # Drive the first paired guard.
    monkeypatch.setattr(data_exporter_module, "DatabaseConfig", None)  # Drive the second paired guard.
    monkeypatch.setattr(data_exporter_module, "DatabaseRouter", None)  # Drive the router guard.
    DataExporter._router = MagicMock()  # Prove the failure path clears a stale router.

    DataExporter._build_polyglot_router()  # The method catches optional-backend setup failures.

    assert DataExporter._router is None  # The exporter must remain in CSV/SQLite mode.


def test_data_exporter_missing_polyglot_probe_uses_standalone(monkeypatch: pytest.MonkeyPatch) -> None:
    """Polyglot host probing falls back to standalone mode when the probe is missing."""
    monkeypatch.setattr(DataExporter, "_standalone_probe", None)  # Reset the process cache for this check.
    monkeypatch.setattr(DataExporter, "_polyglot_db_layer_available", staticmethod(lambda: True))
    monkeypatch.setattr(data_exporter_module, "polyglot_hosts_unreachable", None)  # Remove the probe function.

    assert DataExporter._polyglot_hosts_silent() is True  # Missing probe must not attempt a network call.


def test_data_exporter_missing_router_reports_skip() -> None:
    """Polyglot write returns a skip outcome when the router is absent."""
    DataExporter._router = None  # Drive the missing-router state that a failed init leaves.

    outcome = DataExporter._perform_polyglot_write([{"id": "row-1"}], "listThing")

    assert outcome.skip_reason == SKIP_ROUTER_UNAVAILABLE  # The caller gets a named skip reason.


def test_data_exporter_route_rejects_missing_api_function(monkeypatch: pytest.MonkeyPatch) -> None:
    """Polyglot routing reports a named skip when the endpoint name is missing."""
    monkeypatch.setattr(DataExporter, "_polyglot_skip_reason", staticmethod(lambda _api: None))

    outcome = DataExporter._route_to_polyglot([{"id": "row-1"}], None)

    assert outcome.skip_reason == SKIP_NO_API_FUNCTION_NAME  # The endpoint field remains observable.


def test_ssr_bulk_upgrade_returns_error_when_prepared_data_is_missing() -> None:
    """SSR bulk upgrade returns a handled error when preparation returns no data."""
    manager = FirmwareManager.__new__(FirmwareManager)  # Bypass full initialization for this boundary test.
    manager.org_id = "org-1"  # Provide the log context read by the method.
    manager._prepare_ssr_bulk_upgrade = MagicMock(return_value=(None, None))

    result = manager._bulk_upgrade_ssr_firmware_by_site()

    assert result == {"error": "SSR bulk upgrade preparation returned no data"}


def test_ssr_prepare_returns_error_when_org_sites_are_missing() -> None:
    """SSR preparation returns a handled error when org and site data is missing."""
    manager = FirmwareManager.__new__(FirmwareManager)  # Bypass full initialization for this boundary test.
    manager._resolve_ssr_org_and_sites = MagicMock(return_value=(None, None))

    result, error = manager._prepare_ssr_bulk_upgrade(None)

    assert result is None
    assert error == {"error": "SSR bulk upgrade org and site resolution returned no data"}


def test_ssr_prepare_returns_error_when_config_version_is_missing() -> None:
    """SSR preparation returns a handled error when config and version data is missing."""
    manager = FirmwareManager.__new__(FirmwareManager)  # Bypass full initialization for this boundary test.
    manager._resolve_ssr_org_and_sites = MagicMock(return_value=(("Org", [{"id": "s1"}]), None))
    manager._resolve_ssr_config_and_version = MagicMock(return_value=(None, None))

    result, error = manager._prepare_ssr_bulk_upgrade(None)

    assert result is None
    assert error == {"error": "SSR bulk upgrade config and version resolution returned no data"}


def test_ssr_org_resolution_returns_error_when_sites_are_missing() -> None:
    """SSR org resolution returns a handled error when site data is missing."""
    manager = FirmwareManager.__new__(FirmwareManager)  # Bypass full initialization for this boundary test.
    manager._validate_org_for_ssr_upgrade = MagicMock(return_value=("Org", None))
    manager._resolve_ssr_sites_or_error = MagicMock(return_value=(None, None))

    result, error = manager._resolve_ssr_org_and_sites(None)

    assert result is None
    assert error == {"error": "SSR bulk upgrade site resolution returned no data"}


def test_site_auto_upgrade_rejects_wrong_config_type() -> None:
    """Site auto-upgrade config resolution raises a named type error for wrong input."""
    with pytest.raises(TypeError, match="config must be a SiteAutoUpgradeConfig"):
        _resolve_configurator_kwargs({"config": object()})


def test_wlanradius_requires_selected_wlan() -> None:
    """WLAN RADIUS timer updates raise a named error when no WLAN is selected."""
    manager = WLANRadiusTimerManager.__new__(WLANRadiusTimerManager)  # Bypass prompts and cache loading.
    manager.selected_wlan = None  # Drive the missing WLAN state.

    with pytest.raises(RuntimeError, match="No WLAN selected"):
        manager._get_selected_wlan()


def test_app_runner_returns_none_when_user_vanishes_after_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    """SSH app runner aborts when preflight passes but the user value is missing."""
    logger = MagicMock()  # Capture the error call without writing logs.
    context = (["host-a"], None, "password", {}, False)  # Drive the impossible missing-user state.
    monkeypatch.setattr(AppRunner, "_finalize_preflight", staticmethod(lambda *_args: True))

    result = AppRunner._preflight_and_build(SimpleNamespace(), context, logger)

    assert result is None  # The pipeline caller already treats None as an abort signal.
    logger.error.assert_called_once_with("SSH preflight passed without a user")


def test_websocket_manager_requires_mist_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """WebSocket manager raises a named error when no Mist host exists."""
    monkeypatch.setattr("src.websocket.manager.os.getenv", lambda *_args: None)  # Remove the default fallback.
    session = SimpleNamespace(host=None)  # Provide a session with no host.

    with pytest.raises(ValueError, match="mist_host must be set"):
        WebSocketManager(session)
