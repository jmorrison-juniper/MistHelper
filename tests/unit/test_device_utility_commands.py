"""Tests for DeviceUtilityCommands (Issue #210).

Covers private helpers, device type validation, confirmation flows,
API result handling, and representative public methods across all
five categories: diagnostics, show, management, clear/reset, hardware.

Uses identity-checked teardown to avoid cross-test sys.modules contamination.
"""

from __future__ import annotations

import ast
import inspect
import io
import logging
import sys
import textwrap
from unittest.mock import MagicMock, patch

import pytest

# --- Module-level mistapi stub, restored the moment the import finishes ---
# WHY: pytest imports every test module during collection but runs teardown_module only
# for a module that has a selected test. A stub left in sys.modules therefore leaks for
# the whole session and breaks mistapi's lazy subpackage import. See issue #1739.
_saved_mistapi = sys.modules.get("mistapi")
_our_mock = MagicMock()
sys.modules["mistapi"] = _our_mock
try:
    from src.device._utility_commands_action import _UtilityCommandsAction
    from src.device._utility_commands_websocket import ExportResultSpec, StreamWsSpec
    from src.device.utility_commands import DeviceUtilityCommands, UtilityCommandsDeps
finally:
    if _saved_mistapi is not None:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)

_WS_LOGGER = "src.device._utility_commands_websocket"  # WHY: caplog target for #886 print-to-logger tests
_SEL_LOGGER = "src.device._utility_commands_selection"  # WHY: caplog target for #886 print-to-logger tests
_ZTP_SECRET = "secret123"  # WHY: one literal keeps every ZTP assertion on the same value


class _FakeTerminalStdout(io.StringIO):
    """Captured stream that reports itself as a live terminal."""

    def isatty(self) -> bool:
        return True  # WHY: drive the branch that prints the ZTP credential


class _FakePipeStdout(io.StringIO):
    """Captured stream that reports itself as a pipe or a redirect."""

    def isatty(self) -> bool:
        return False  # WHY: drive the branch that withholds the ZTP credential


def setup_module() -> None:
    """Re-assert our mock in sys.modules before tests run."""
    sys.modules["mistapi"] = _our_mock


def teardown_module() -> None:
    """Restore sys.modules only if our stub is still installed."""
    if sys.modules.get("mistapi") is not _our_mock:
        return
    if _saved_mistapi is not None:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture()
def mock_deps() -> dict[str, MagicMock]:
    """Return dict of constructor dependencies as mocks."""
    return {
        "apisession": MagicMock(),
        "select_site_fn": MagicMock(return_value="site-1"),
        "select_device_fn": MagicMock(return_value="dev-1"),
        "safe_input_fn": MagicMock(return_value=""),
        "write_export_fn": MagicMock(),
        "websocket_manager_factory": MagicMock(),
    }


@pytest.fixture()
def duc(mock_deps: dict[str, MagicMock]) -> DeviceUtilityCommands:
    """Return a DeviceUtilityCommands instance with mocked deps."""
    return DeviceUtilityCommands(UtilityCommandsDeps(**mock_deps))


@pytest.fixture()
def mock_api():
    """Patch mistapi across every cluster module used by DeviceUtilityCommands."""
    with (
        patch("src.device._utility_commands_selection.mistapi") as mapi,  # WHY: primary mistapi mock
        patch("src.device._utility_commands_show.mistapi", mapi),  # WHY: keep clusters sharing one mock
        patch("src.device._utility_commands_action.mistapi", mapi),  # WHY: cover action-cluster SDK calls
        patch("src.device._utility_commands_clear.mistapi", mapi),  # WHY: cover clear-cluster SDK calls
    ):
        yield mapi


def _mock_stats_response(
    device_type: str = "switch",
    status: str = "connected",
    ports: list[dict[str, str]] | None = None,
) -> MagicMock:
    """Build a mock stats API response."""
    data: dict[str, object] = {"type": device_type, "status": status}
    if ports is not None:
        data["ports"] = ports
    resp = MagicMock()
    resp.data = data
    return resp


def _mock_api_response(
    status_code: int = 200,
    data: dict[str, object] | None = None,
) -> MagicMock:
    """Build a mock API response with status_code."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.data = data or {}
    return resp


# ===================================================================
# DEVICE_TYPE_COMPATIBILITY_MAP
# ===================================================================


class TestCompatibilityMap:
    """Verify the compatibility map is well-formed."""

    def test_map_has_all_commands(self) -> None:
        m = DeviceUtilityCommands.DEVICE_TYPE_COMPATIBILITY_MAP
        assert len(m) == 35

    def test_all_values_are_lists(self) -> None:
        for key, val in DeviceUtilityCommands.DEVICE_TYPE_COMPATIBILITY_MAP.items():
            assert isinstance(val, list), f"{key} should map to a list"

    def test_only_valid_device_types(self) -> None:
        valid = {"ap", "switch", "gateway"}
        for key, types in DeviceUtilityCommands.DEVICE_TYPE_COMPATIBILITY_MAP.items():
            assert set(types) <= valid, f"{key} has invalid types: {types}"


# ===================================================================
# _validate_device_type
# ===================================================================


class TestValidateDeviceType:
    """Tests for _validate_device_type."""

    def test_allowed_type_returns_true(self, duc: DeviceUtilityCommands) -> None:
        assert duc._validate_device_type("switch", "cable_test") is True

    def test_disallowed_type_returns_false(self, duc: DeviceUtilityCommands, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.WARNING, logger=_SEL_LOGGER)
        assert duc._validate_device_type("ap", "cable_test") is False
        assert "only available on" in caplog.text

    def test_unknown_command_returns_false(self, duc: DeviceUtilityCommands) -> None:
        assert duc._validate_device_type("switch", "nonexistent_cmd") is False


# ===================================================================
# _select_site_and_device
# ===================================================================


class TestSelectSiteAndDevice:
    """Tests for _select_site_and_device."""

    def test_returns_none_when_no_site(self, duc: DeviceUtilityCommands, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_site_fn"].return_value = None
        assert duc._select_site_and_device("traceroute") is None

    def test_returns_none_when_no_device(self, duc: DeviceUtilityCommands, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["select_device_fn"].return_value = None
        assert duc._select_site_and_device("traceroute") is None

    def test_returns_none_when_stats_fail(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_get_device_info", return_value=None):
            assert duc._select_site_and_device("traceroute") is None

    def test_returns_none_when_type_missing(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_get_device_info", return_value={"status": "connected"}):
            assert duc._select_site_and_device("traceroute") is None

    def test_returns_none_when_type_invalid(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_get_device_info", return_value={"type": "ap", "status": "connected"}):
            assert duc._select_site_and_device("cable_test") is None

    def test_returns_tuple_on_success(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(
            duc,
            "_get_device_info",
            return_value={"type": "switch", "status": "connected"},
        ):
            result = duc._select_site_and_device("cable_test")
            assert result == ("site-1", "dev-1", "switch")

    def test_warns_when_device_offline(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_SEL_LOGGER)
        with patch.object(
            duc,
            "_get_device_info",
            return_value={"type": "ap", "status": "disconnected"},
        ):
            result = duc._select_site_and_device("traceroute")
            assert result is not None
            assert "WARNING" in caplog.text


# ===================================================================
# _get_device_info
# ===================================================================


class TestGetDeviceInfo:
    """Tests for _get_device_info."""

    def test_returns_data_on_success(self, duc: DeviceUtilityCommands, mock_api: MagicMock) -> None:
        resp = _mock_stats_response("switch", "connected")
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        info = duc._get_device_info("site-1", "dev-1")
        assert info == {"type": "switch", "status": "connected"}

    def test_returns_none_on_no_data(self, duc: DeviceUtilityCommands, mock_api: MagicMock) -> None:
        resp = MagicMock(spec=[])
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        assert duc._get_device_info("site-1", "dev-1") is None

    def test_returns_none_on_exception(self, duc: DeviceUtilityCommands, mock_api: MagicMock) -> None:
        mock_api.api.v1.sites.stats.getSiteDeviceStats.side_effect = RuntimeError("boom")
        assert duc._get_device_info("site-1", "dev-1") is None


# ===================================================================
# _print_api_result
# ===================================================================


class TestPrintApiResult:
    """Tests for _print_api_result (static method)."""

    def test_success_prints_message(self, caplog: pytest.LogCaptureFixture) -> None:
        resp = _mock_api_response(200)
        with caplog.at_level(logging.INFO, logger="root"):
            result = DeviceUtilityCommands._print_api_result(resp, "OK", "FAIL")
        assert result is True
        assert "OK" in "\n".join(r.getMessage() for r in caplog.records)

    def test_failure_prints_error(self, caplog: pytest.LogCaptureFixture) -> None:
        resp = _mock_api_response(400, {"detail": "bad request"})
        with caplog.at_level(logging.ERROR, logger="root"):
            result = DeviceUtilityCommands._print_api_result(resp, "OK", "FAIL")
        assert result is False
        out = "\n".join(r.getMessage() for r in caplog.records)
        assert "FAIL" in out
        assert "400" in out
        assert "bad request" in out

    def test_failure_without_detail(self, caplog: pytest.LogCaptureFixture) -> None:
        resp = _mock_api_response(500)
        with caplog.at_level(logging.ERROR, logger="root"):
            result = DeviceUtilityCommands._print_api_result(resp, "OK", "Server Error")
        assert result is False
        assert "500" in "\n".join(r.getMessage() for r in caplog.records)


# ===================================================================
# _confirm_destructive
# ===================================================================


class TestConfirmDestructive:
    """Tests for _confirm_destructive."""

    def test_matching_keyword_returns_true(self, duc: DeviceUtilityCommands, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = "CLEAR"
        assert duc._confirm_destructive("Type CLEAR: ", "CLEAR", "test") is True

    def test_wrong_keyword_returns_false(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        mock_deps["safe_input_fn"].return_value = "nope"
        assert duc._confirm_destructive("Type CLEAR: ", "CLEAR", "test") is False
        assert "cancelled" in caplog.text

    def test_empty_input_returns_false(self, duc: DeviceUtilityCommands, mock_deps: dict[str, MagicMock]) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        assert duc._confirm_destructive("Type CLEAR: ", "CLEAR", "test") is False


# ===================================================================
# _display_and_export_result
# ===================================================================


class TestDisplayAndExportResult:
    """Tests for _display_and_export_result."""

    def test_none_result_prints_error(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        duc._display_and_export_result(
            ExportResultSpec(
                result=None,
                command_name="test_cmd",
                site_id="site-1",
                device_id="dev-1",
                api_function_name="apiFunc",
                filename="file.csv",
            )
        )
        assert "No results" in caplog.text

    def test_prints_raw_output(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_WS_LOGGER)
        result = {"raw": "output line 1\nline 2"}
        duc._display_and_export_result(
            ExportResultSpec(
                result=result,
                command_name="traceroute",
                site_id="site-1",
                device_id="dev-1",
                api_function_name="tracerouteFromDevice",
                filename="Trace.csv",
            )
        )
        out = caplog.text
        assert "output line 1" in out
        assert "TRACEROUTE RESULTS" in out
        mock_deps["write_export_fn"].assert_called_once()

    def test_exports_correct_data(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        result = {"raw": "hello"}
        duc._display_and_export_result(
            ExportResultSpec(
                result=result,
                command_name="cmd",
                site_id="s1",
                device_id="d1",
                api_function_name="apiFunc",
                filename="out.csv",
            )
        )
        call_args = mock_deps["write_export_fn"].call_args
        export_list = call_args[0][0]
        assert len(export_list) == 1
        assert export_list[0]["device_id"] == "d1"
        assert export_list[0]["site_id"] == "s1"
        assert export_list[0]["command"] == "cmd"
        assert export_list[0]["raw_output"] == "hello"


# ===================================================================
# _display_and_select_port
# ===================================================================


class TestDisplayAndSelectPort:
    """Tests for _display_and_select_port."""

    def test_numeric_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "1"
        ports = [{"port_id": "ge-0/0/0", "up": True}]
        assert duc._display_and_select_port(ports) == "ge-0/0/0"

    def test_text_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "xe-0/0/1"
        ports = [{"port_id": "ge-0/0/0", "up": True}]
        assert duc._display_and_select_port(ports) == "xe-0/0/1"

    def test_empty_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        ports = [{"port_id": "ge-0/0/0", "up": True}]
        assert duc._display_and_select_port(ports) is None

    def test_invalid_number(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "99"
        ports = [{"port_id": "ge-0/0/0", "up": True}]
        assert duc._display_and_select_port(ports) is None


# ===================================================================
# _display_and_select_ifstat
# ===================================================================


class TestDisplayAndSelectIfstat:
    """Tests for _display_and_select_ifstat."""

    def test_numeric_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "1"
        if_stat = {"ge-0/0/0": {"up": True}, "ge-0/0/1": {"up": False}}
        result = duc._display_and_select_ifstat(if_stat)
        assert result in ("ge-0/0/0", "ge-0/0/1")

    def test_strips_subinterface(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "1"
        if_stat = {"ge-0/0/0.0": {"up": True}}
        assert duc._display_and_select_ifstat(if_stat) == "ge-0/0/0"


# ===================================================================
# _manual_port_entry
# ===================================================================


class TestManualPortEntry:
    """Tests for _manual_port_entry."""

    def test_returns_typed_port(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "ge-0/0/5"
        assert duc._manual_port_entry() == "ge-0/0/5"

    def test_returns_none_on_empty(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        assert duc._manual_port_entry() is None


# ===================================================================
# _run_websocket_command
# ===================================================================


class TestRunWebsocketCommand:
    """Tests for _run_websocket_command."""

    def test_returns_none_on_connect_fail(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = False
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        result = duc._run_websocket_command("s1", "d1", MagicMock())
        assert result is None

    def test_returns_none_on_subscribe_fail(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = False
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        result = duc._run_websocket_command("s1", "d1", MagicMock())
        assert result is None
        ws_mgr.disconnect.assert_called_once()

    @patch("src.device._utility_commands_websocket.time.sleep")
    def test_success_path(
        self,
        mock_sleep: MagicMock,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        ws_mgr.wait_for_command_result.return_value = {"raw": "ok"}
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        sdk_method = MagicMock()
        resp = MagicMock()
        resp.data = {"session": "abc12345-xyz"}
        sdk_method.return_value = resp
        result = duc._run_websocket_command("s1", "d1", sdk_method, {"key": "val"})
        assert result == {"raw": "ok"}
        ws_mgr.disconnect.assert_called_once()


# ===================================================================
# _run_streaming_command
# ===================================================================


class TestRunStreamingCommand:
    """Tests for _run_streaming_command."""

    def test_returns_on_connect_fail(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = False
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        duc._run_streaming_command("s1", "d1", MagicMock())
        assert "Failed" in caplog.text


# ===================================================================
# Public methods - representative coverage per category
# ===================================================================


class TestTraceroute:
    """Tests for traceroute (diagnostic category)."""

    def test_early_return_no_selection(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.traceroute()

    def test_early_return_no_host(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "ap")):
            mock_deps["safe_input_fn"].return_value = ""
            # WHY: slice 90 migrated print()->logger.warning; assertion now reads caplog, not stdout.
            with caplog.at_level("WARNING", logger="src.device._utility_commands_show"):
                duc.traceroute()
            assert "required" in caplog.text

    def test_success_calls_ws_and_export(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["8.8.8.8", "udp"]
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "ap")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "trace done"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_export,
        ):
            duc.traceroute()
            mock_ws.assert_called_once()
            call_body = mock_ws.call_args[0][3]
            assert call_body["host"] == "8.8.8.8"
            assert call_body["protocol"] == "udp"
            mock_export.assert_called_once()


class TestShowOspfNeighbors:
    """Tests for show_ospf_neighbors (show category)."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.show_ospf_neighbors()

    def test_calls_ws_command(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "data"}) as mock_ws,
            patch.object(duc, "_display_and_export_result"),
        ):
            duc.show_ospf_neighbors()
            mock_ws.assert_called_once()


class TestLocateDevice:
    """Tests for locate_device (management category)."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.locate_device()

    def test_success_calls_api(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "10"
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.startSiteLocateDevice.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "ap")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.locate_device()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "blinking" in out.lower() or "LED" in out

    def test_clamps_duration(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "999"
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.startSiteLocateDevice.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "ap")):
            duc.locate_device()
            call_body = mock_api.api.v1.sites.devices.startSiteLocateDevice.call_args[0][3]
            assert call_body["duration"] == 120

    def test_invalid_duration_defaults_to_5(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "abc"
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.startSiteLocateDevice.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "ap")):
            duc.locate_device()
            call_body = mock_api.api.v1.sites.devices.startSiteLocateDevice.call_args[0][3]
            assert call_body["duration"] == 5


class TestUnlocateDevice:
    """Tests for unlocate_device."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.stopSiteLocateDevice.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.unlocate_device()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "stopped" in out.lower()

    def test_api_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_api.api.v1.sites.devices.stopSiteLocateDevice.side_effect = RuntimeError("fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.unlocate_device()
            assert "fail" in capsys.readouterr().out.lower()


class TestBouncePort:
    """Tests for bounce_port (management with y/N confirmation)."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.bounce_port()

    def test_blocks_management_port(
        self,
        duc: DeviceUtilityCommands,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="vme0"),
        ):
            duc.bounce_port()
            assert "cannot be bounced" in capsys.readouterr().out

    def test_cancelled_when_not_confirmed(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "n"
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
        ):
            duc.bounce_port()
            assert "cancelled" in capsys.readouterr().out.lower()


class TestClearArpCache:
    """Tests for clear_arp_cache (destructive with typed confirmation)."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.clear_arp_cache()

    def test_cancelled_without_clear_keyword(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        mock_deps["safe_input_fn"].return_value = "nope"
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_optional", return_value=""),
        ):
            duc.clear_arp_cache()
            assert "cancelled" in caplog.text.lower()

    def test_success_calls_api(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        # node="", ip="", then "CLEAR" (port_optional is patched)
        mock_deps["safe_input_fn"].side_effect = ["", "", "CLEAR"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearSiteSsrArpCache.return_value = resp
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_optional", return_value=""),
        ):
            duc.clear_arp_cache()
            mock_api.api.v1.sites.devices.clearSiteSsrArpCache.assert_called_once()


class TestPollSwitchStats:
    """Tests for poll_switch_stats (hardware category)."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.poll_switch_stats()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.pollSiteSwitchStats.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.poll_switch_stats()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "poll" in out.lower()


class TestCreateDeviceSnapshot:
    """Tests for create_device_snapshot (hardware category)."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.create_device_snapshot()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.createSiteDeviceSnapshot.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.create_device_snapshot()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "snapshot" in out.lower()

    def test_api_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_api.api.v1.sites.devices.createSiteDeviceSnapshot.side_effect = RuntimeError("snap fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.create_device_snapshot()
            assert "snap fail" in capsys.readouterr().out


class TestReprovisionDevice:
    """Tests for reprovision_device (management with y/N)."""

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "n"
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.reprovision_device()
            assert "cancelled" in capsys.readouterr().out.lower()


class TestCableTest:
    """Tests for cable_test."""

    def test_no_port_selected(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value=None),
        ):
            duc.cable_test()


class TestUploadSupportFile:
    """Tests for upload_support_file."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.upload_support_file()

    def test_success_calls_api(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["1", ""]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.uploadSiteDeviceSupportFile.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.upload_support_file()
            mock_api.api.v1.sites.devices.uploadSiteDeviceSupportFile.assert_called_once()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "upload" in out.lower() or "initiated" in out.lower()

    def test_invalid_type_defaults_full(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["abc", ""]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.uploadSiteDeviceSupportFile.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.upload_support_file()
            call_body = mock_api.api.v1.sites.devices.uploadSiteDeviceSupportFile.call_args[0][3]
            assert call_body["info"] == "full"

    def test_exception_handled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["1", ""]
        mock_api.api.v1.sites.devices.uploadSiteDeviceSupportFile.side_effect = RuntimeError("boom")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.upload_support_file()
            assert "boom" in capsys.readouterr().out


# ===================================================================
# _select_port_from_device
# ===================================================================


class TestSelectPortFromDevice:
    """Tests for _select_port_from_device."""

    def test_with_ports(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = _mock_stats_response("switch", "connected", [{"port_id": "ge-0/0/0", "up": True}])
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with patch.object(duc, "_display_and_select_port", return_value="ge-0/0/0") as mock_disp:
            result = duc._select_port_from_device("s1", "d1")
            assert result == "ge-0/0/0"
            mock_disp.assert_called_once()

    def test_with_if_stat(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"type": "switch", "status": "connected", "ports": [], "if_stat": {"ge-0/0/0": {"up": True}}}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with patch.object(duc, "_display_and_select_ifstat", return_value="ge-0/0/0") as mock_ifs:
            result = duc._select_port_from_device("s1", "d1")
            assert result == "ge-0/0/0"
            mock_ifs.assert_called_once()

    def test_no_ports_no_ifstat(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"type": "switch", "ports": [], "if_stat": {}}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with patch.object(duc, "_manual_port_entry", return_value="ge-0/0/5") as mock_man:
            result = duc._select_port_from_device("s1", "d1")
            assert result == "ge-0/0/5"
            mock_man.assert_called_once()

    def test_no_data_attr(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock(spec=[])
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with patch.object(duc, "_manual_port_entry", return_value=None):
            result = duc._select_port_from_device("s1", "d1")
            assert result is None

    def test_exception_falls_back(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        mock_api.api.v1.sites.stats.getSiteDeviceStats.side_effect = RuntimeError("fail")
        with patch.object(duc, "_manual_port_entry", return_value="ge-0/0/1") as mock_man:
            result = duc._select_port_from_device("s1", "d1")
            assert result == "ge-0/0/1"
            mock_man.assert_called_once()


# ===================================================================
# _select_port_optional
# ===================================================================


class TestSelectPortOptional:
    """Tests for _select_port_optional."""

    def test_returns_selected_port_by_number(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"ports": [{"port_id": "ge-0/0/0", "up": True}]}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        mock_deps["safe_input_fn"].return_value = "1"
        result = duc._select_port_optional("s1", "d1")
        assert result == "ge-0/0/0"

    def test_returns_empty_on_skip(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"ports": []}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        mock_deps["safe_input_fn"].return_value = ""
        result = duc._select_port_optional("s1", "d1")
        assert result == ""

    def test_returns_text_name(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"ports": []}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        mock_deps["safe_input_fn"].return_value = "xe-0/0/1"
        result = duc._select_port_optional("s1", "d1")
        assert result == "xe-0/0/1"

    def test_if_stat_fallback(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"ports": [], "if_stat": {"ge-0/0/0": {"up": True}}}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        mock_deps["safe_input_fn"].return_value = "1"
        result = duc._select_port_optional("s1", "d1")
        assert result == "ge-0/0/0"

    def test_exception_still_prompts(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_api.api.v1.sites.stats.getSiteDeviceStats.side_effect = RuntimeError("fail")
        mock_deps["safe_input_fn"].return_value = "ge-0/0/2"
        result = duc._select_port_optional("s1", "d1")
        assert result == "ge-0/0/2"


# ===================================================================
# _select_interface_from_device
# ===================================================================


class TestSelectInterfaceFromDevice:
    """Tests for _select_interface_from_device."""

    def test_with_if_stat(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"if_stat": {"ge-0/0/0": {"up": True}}, "ip_stat": {}, "ports": []}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with (
            patch.object(duc, "_print_interface_list"),
            patch.object(duc, "_get_interface_selection", return_value="ge-0/0/0"),
        ):
            result = duc._select_interface_from_device("s1", "d1")
            assert result == "ge-0/0/0"

    def test_with_ip_stat(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"if_stat": {}, "ip_stat": {"ge-0/0/1": {"ip": "10.0.0.1"}}, "ports": []}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with (
            patch.object(duc, "_print_interface_list"),
            patch.object(duc, "_get_interface_selection", return_value="ge-0/0/1"),
        ):
            result = duc._select_interface_from_device("s1", "d1")
            assert result == "ge-0/0/1"

    def test_with_ports_fallback(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"if_stat": {}, "ip_stat": {}, "ports": [{"port_id": "ge-0/0/2"}]}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with (
            patch.object(duc, "_print_interface_list"),
            patch.object(duc, "_get_interface_selection", return_value="ge-0/0/2"),
        ):
            result = duc._select_interface_from_device("s1", "d1")
            assert result == "ge-0/0/2"

    def test_no_data_falls_back_manual(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"if_stat": {}, "ip_stat": {}, "ports": []}
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with patch.object(duc, "_manual_interface_entry", return_value="wan0"):
            result = duc._select_interface_from_device("s1", "d1")
            assert result == "wan0"

    def test_no_data_attr(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock(spec=[])
        mock_api.api.v1.sites.stats.getSiteDeviceStats.return_value = resp
        with patch.object(duc, "_manual_interface_entry", return_value=None):
            result = duc._select_interface_from_device("s1", "d1")
            assert result is None

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        mock_api.api.v1.sites.stats.getSiteDeviceStats.side_effect = RuntimeError("fail")
        with patch.object(duc, "_manual_interface_entry", return_value="lo0"):
            result = duc._select_interface_from_device("s1", "d1")
            assert result == "lo0"


# ===================================================================
# _print_interface_list
# ===================================================================


class TestPrintInterfaceList:
    """Tests for _print_interface_list."""

    def test_prints_with_if_stat_ips(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_SEL_LOGGER)
        interfaces = ["ge-0/0/0"]
        if_stat = {"ge-0/0/0": {"ips": ["10.0.0.1"]}}
        duc._print_interface_list(interfaces, if_stat, {})
        assert "ge-0/0/0" in caplog.text
        assert "10.0.0.1" in caplog.text

    def test_prints_with_ip_stat(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_SEL_LOGGER)
        interfaces = ["wan0"]
        duc._print_interface_list(interfaces, {}, {"wan0": {"ip": "192.168.1.1"}})
        assert "wan0" in caplog.text
        assert "192.168.1.1" in caplog.text

    def test_prints_plain(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_SEL_LOGGER)
        interfaces = ["eth0"]
        duc._print_interface_list(interfaces, {}, {})
        assert "eth0" in caplog.text


# ===================================================================
# _get_interface_selection
# ===================================================================


class TestGetInterfaceSelection:
    """Tests for _get_interface_selection."""

    def test_numeric_valid(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "1"
        result = duc._get_interface_selection(["ge-0/0/0", "ge-0/0/1"])
        assert result == "ge-0/0/0"

    def test_numeric_invalid(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_SEL_LOGGER)
        mock_deps["safe_input_fn"].return_value = "99"
        result = duc._get_interface_selection(["ge-0/0/0"])
        assert result is None
        assert "Invalid" in caplog.text

    def test_text_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "wan0"
        result = duc._get_interface_selection(["ge-0/0/0"])
        assert result == "wan0"

    def test_empty_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        result = duc._get_interface_selection(["ge-0/0/0"])
        assert result is None


# ===================================================================
# _manual_interface_entry
# ===================================================================


class TestManualInterfaceEntry:
    """Tests for _manual_interface_entry."""

    def test_returns_typed_interface(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "wan0"
        assert duc._manual_interface_entry() == "wan0"

    def test_returns_none_on_empty(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        assert duc._manual_interface_entry() is None


# ===================================================================
# _select_network_from_device
# ===================================================================


class TestSelectNetworkFromDevice:
    """Tests for _select_network_from_device."""

    def test_auto_select_single_network(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_SEL_LOGGER)
        resp = MagicMock()
        resp.data = {"dhcpd_config": {"lan": {}}}
        mock_api.api.v1.sites.devices.getSiteDevice.return_value = resp
        result = duc._select_network_from_device("s1", "d1")
        assert result == "lan"
        assert "Auto-selecting" in caplog.text

    def test_numeric_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"dhcpd_config": {"net1": {}, "net2": {}}}
        mock_api.api.v1.sites.devices.getSiteDevice.return_value = resp
        mock_deps["safe_input_fn"].return_value = "2"
        result = duc._select_network_from_device("s1", "d1")
        assert result == "net2"

    def test_text_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"dhcpd_config": {}}
        mock_api.api.v1.sites.devices.getSiteDevice.return_value = resp
        mock_deps["safe_input_fn"].return_value = "custom_net"
        result = duc._select_network_from_device("s1", "d1")
        assert result == "custom_net"

    def test_empty_returns_empty(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"dhcpd_config": {}}
        mock_api.api.v1.sites.devices.getSiteDevice.return_value = resp
        mock_deps["safe_input_fn"].return_value = ""
        result = duc._select_network_from_device("s1", "d1")
        assert result == ""

    def test_ip_config_fallback(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        resp = MagicMock()
        resp.data = {"dhcpd_config": {}, "ip_config": {"wan": {"ip": "10.0.0.1"}}}
        mock_api.api.v1.sites.devices.getSiteDevice.return_value = resp
        mock_deps["safe_input_fn"].return_value = "1"
        result = duc._select_network_from_device("s1", "d1")
        assert result == "wan"

    def test_exception_still_prompts(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_api.api.v1.sites.devices.getSiteDevice.side_effect = RuntimeError("fail")
        mock_deps["safe_input_fn"].return_value = "mynet"
        result = duc._select_network_from_device("s1", "d1")
        assert result == "mynet"


# ===================================================================
# _execute_ws_command
# ===================================================================


class TestExecuteWsCommand:
    """Tests for _execute_ws_command."""

    def test_no_response_data(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        sdk_method = MagicMock()
        sdk_method.return_value = MagicMock(spec=[])
        ws_mgr = MagicMock()
        result = duc._execute_ws_command("s1", "d1", sdk_method, None, ws_mgr)
        assert result is None
        assert "No response data" in caplog.text

    def test_no_session_id(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        sdk_method = MagicMock()
        resp = MagicMock()
        resp.data = {}
        sdk_method.return_value = resp
        ws_mgr = MagicMock()
        result = duc._execute_ws_command("s1", "d1", sdk_method, None, ws_mgr)
        assert result is None
        assert "No session ID" in caplog.text

    def test_success_with_body(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        sdk_method = MagicMock()
        resp = MagicMock()
        resp.data = {"session": "abcdef12-3456"}
        sdk_method.return_value = resp
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = {"raw": "output"}
        result = duc._execute_ws_command("s1", "d1", sdk_method, {"key": "val"}, ws_mgr)
        assert result == {"raw": "output"}
        sdk_method.assert_called_once_with(duc._apisession, "s1", "d1", {"key": "val"})

    def test_success_without_body(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        sdk_method = MagicMock()
        resp = MagicMock()
        resp.data = {"session": "abcdef12-3456"}
        sdk_method.return_value = resp
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = {"raw": "ok"}
        result = duc._execute_ws_command("s1", "d1", sdk_method, None, ws_mgr)
        assert result == {"raw": "ok"}
        sdk_method.assert_called_once_with(duc._apisession, "s1", "d1")


# ===================================================================
# _stream_ws_output
# ===================================================================


class TestStreamWsOutput:
    """Tests for _stream_ws_output."""

    def test_no_response_data(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        sdk_method = MagicMock()
        sdk_method.return_value = MagicMock(spec=[])
        ws_mgr = MagicMock()
        duc._stream_ws_output(
            StreamWsSpec(
                site_id="s1",
                device_id="d1",
                sdk_method=sdk_method,
                body=None,
                websocket_manager=ws_mgr,
                timeout_seconds=60,
            )
        )
        assert "No response data" in caplog.text

    def test_no_session_id(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        sdk_method = MagicMock()
        resp = MagicMock()
        resp.data = {}
        sdk_method.return_value = resp
        ws_mgr = MagicMock()
        duc._stream_ws_output(
            StreamWsSpec(
                site_id="s1",
                device_id="d1",
                sdk_method=sdk_method,
                body=None,
                websocket_manager=ws_mgr,
                timeout_seconds=60,
            )
        )
        assert "No session ID" in caplog.text

    def test_success_prints_raw(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_WS_LOGGER)
        sdk_method = MagicMock()
        resp = MagicMock()
        resp.data = {"session": "abc12345-xyz"}
        sdk_method.return_value = resp
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = {"raw": "streaming output"}
        duc._stream_ws_output(
            StreamWsSpec(
                site_id="s1",
                device_id="d1",
                sdk_method=sdk_method,
                body={"port": "ge-0/0/0"},
                websocket_manager=ws_mgr,
                timeout_seconds=60,
            )
        )
        assert "streaming output" in caplog.text

    def test_success_no_raw(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_WS_LOGGER)
        sdk_method = MagicMock()
        resp = MagicMock()
        resp.data = {"session": "abc12345-xyz"}
        sdk_method.return_value = resp
        ws_mgr = MagicMock()
        ws_mgr.wait_for_command_result.return_value = {"other": "data"}
        duc._stream_ws_output(
            StreamWsSpec(
                site_id="s1",
                device_id="d1",
                sdk_method=sdk_method,
                body=None,
                websocket_manager=ws_mgr,
                timeout_seconds=60,
            )
        )
        assert "Streaming started" in caplog.text


# ===================================================================
# _run_streaming_command (additional tests)
# ===================================================================


class TestRunStreamingCommandExtended:
    """Extended tests for _run_streaming_command."""

    @patch("src.device._utility_commands_websocket.time.sleep")
    def test_subscribe_fail(
        self,
        mock_sleep: MagicMock,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING, logger=_WS_LOGGER)
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = False
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        duc._run_streaming_command("s1", "d1", MagicMock())
        assert "Failed to subscribe" in caplog.text
        ws_mgr.disconnect.assert_called_once()

    @patch("src.device._utility_commands_websocket.time.sleep")
    def test_success_path(
        self,
        mock_sleep: MagicMock,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        with patch.object(duc, "_stream_ws_output") as mock_stream:
            duc._run_streaming_command("s1", "d1", MagicMock(), {"key": "v"}, 90)
            mock_stream.assert_called_once()
        ws_mgr.disconnect.assert_called_once()

    @patch("src.device._utility_commands_websocket.time.sleep")
    def test_exception_in_stream(
        self,
        mock_sleep: MagicMock,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.ERROR, logger=_WS_LOGGER)
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        with patch.object(duc, "_stream_ws_output", side_effect=RuntimeError("oops")):
            duc._run_streaming_command("s1", "d1", MagicMock())
            assert "oops" in caplog.text
        ws_mgr.disconnect.assert_called_once()

    @patch("src.device._utility_commands_websocket.time.sleep")
    def test_keyboard_interrupt(
        self,
        mock_sleep: MagicMock,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_WS_LOGGER)
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        with patch.object(duc, "_stream_ws_output", side_effect=KeyboardInterrupt):
            duc._run_streaming_command("s1", "d1", MagicMock())
            assert "stopped" in caplog.text.lower()
        ws_mgr.disconnect.assert_called_once()


# ===================================================================
# _run_websocket_command (additional tests)
# ===================================================================


class TestRunWebsocketCommandExtended:
    """Extended tests for _run_websocket_command."""

    @patch("src.device._utility_commands_websocket.time.sleep")
    def test_exception_in_execute(
        self,
        mock_sleep: MagicMock,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.ERROR, logger=_WS_LOGGER)
        ws_mgr = MagicMock()
        ws_mgr.connect.return_value = True
        ws_mgr.subscribe_to_channel.return_value = True
        mock_deps["websocket_manager_factory"].return_value = ws_mgr
        with patch.object(duc, "_execute_ws_command", side_effect=RuntimeError("ws error")):
            result = duc._run_websocket_command("s1", "d1", MagicMock())
            assert result is None
            assert "ws error" in caplog.text
        ws_mgr.disconnect.assert_called_once()


# ===================================================================
# Show commands - success paths
# ===================================================================


class TestShowOspfInterfaces:
    """Tests for show_ospf_interfaces."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_select_port_optional", return_value=""),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_ospf_interfaces()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestShowOspfDatabase:
    """Tests for show_ospf_database."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_ospf_database()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()

    def test_with_self_originate(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["myvrf", "node0", "y"]
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result"),
        ):
            duc.show_ospf_database()
            call_body = mock_ws.call_args[0][3]
            assert call_body.get("self_originate") is True
            assert call_body["vrf"] == "myvrf"
            assert call_body["node"] == "node0"


class TestShowOspfSummary:
    """Tests for show_ospf_summary."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_ospf_summary()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestResolveDns:
    """Tests for resolve_dns."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.resolve_dns()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestMonitorTraffic:
    """Tests for monitor_traffic."""

    def test_early_return_no_port(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value=None),
        ):
            duc.monitor_traffic()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "30"
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_run_streaming_command") as mock_stream,
        ):
            duc.monitor_traffic()
            mock_stream.assert_called_once()
            call_body = mock_stream.call_args[0][3]
            assert call_body["port_id"] == "ge-0/0/0"
            assert call_body["duration"] == 30

    def test_invalid_duration(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "abc"
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_run_streaming_command") as mock_stream,
        ):
            duc.monitor_traffic()
            call_body = mock_stream.call_args[0][3]
            assert call_body["duration"] == 60


class TestRunTop:
    """Tests for run_top."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_run_streaming_command") as mock_stream,
        ):
            duc.run_top()
            mock_stream.assert_called_once()


class TestShowSession:
    """Tests for show_session."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_session()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()

    def test_with_filters(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["my_service", "sess-123", "node0"]
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result"),
        ):
            duc.show_session()
            call_body = mock_ws.call_args[0][3]
            assert call_body["service_name"] == "my_service"
            assert call_body["session_id"] == "sess-123"
            assert call_body["node"] == "node0"


class TestShowServicePath:
    """Tests for show_service_path."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_service_path()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestShowBgpSummary:
    """Tests for show_bgp_summary."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_bgp_summary()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestShowArpTable:
    """Tests for show_arp_table."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_arp_table()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestShowDhcpLeases:
    """Tests for show_dhcp_leases."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_network_from_device", return_value="lan"),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_dhcp_leases()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestShowDot1x:
    """Tests for show_dot1x."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_dot1x()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


class TestShowEvpnDatabase:
    """Tests for show_evpn_database."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.show_evpn_database()
            mock_ws.assert_called_once()
            mock_exp.assert_called_once()


# ===================================================================
# Management commands - success paths
# ===================================================================


class TestLocateDeviceExtended:
    """Extended tests for locate_device."""

    def test_exception_handled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "5"
        mock_api.api.v1.sites.devices.startSiteLocateDevice.side_effect = RuntimeError("locate boom")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "ap")):
            duc.locate_device()
            assert "locate boom" in capsys.readouterr().out


class TestBouncePortExtended:
    """Extended tests for bounce_port success path."""

    def test_success_bounces(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "y"
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
        ):
            duc.bounce_port()
            mock_ws.assert_called_once()
            call_body = mock_ws.call_args[0][3]
            assert call_body["ports"] == ["ge-0/0/0"]

    def test_no_port_selected(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value=None),
        ):
            duc.bounce_port()

    def test_timeout_result(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "y"
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_run_websocket_command", return_value=None),
        ):
            duc.bounce_port()
            assert "timed out" in capsys.readouterr().out.lower()


class TestCableTestExtended:
    """Extended tests for cable_test success path."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_run_websocket_command", return_value={"raw": "ok"}) as mock_ws,
            patch.object(duc, "_display_and_export_result") as mock_exp,
        ):
            duc.cable_test()
            mock_ws.assert_called_once()
            call_body = mock_ws.call_args[0][3]
            assert call_body["port"] == "ge-0/0/0"
            mock_exp.assert_called_once()


class TestReprovisionDeviceExtended:
    """Extended tests for reprovision_device."""

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "y"
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.reprovisionSiteOctermDevice.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.reprovision_device()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "reprovisioning" in out.lower()

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "y"
        mock_api.api.v1.sites.devices.reprovisionSiteOctermDevice.side_effect = RuntimeError("fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.reprovision_device()
            assert "fail" in capsys.readouterr().out


class TestReadoptDevice:
    """Tests for readopt_device."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.readopt_device()

    def test_not_vc_member(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        vc_resp = MagicMock()
        vc_resp.data = {"is_virtual_chassis": False}
        mock_api.api.v1.sites.devices.getSiteDeviceVirtualChassis.return_value = vc_resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.readopt_device()
            assert "not a Virtual Chassis" in capsys.readouterr().out

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        vc_resp = MagicMock()
        vc_resp.data = {"is_virtual_chassis": True}
        mock_api.api.v1.sites.devices.getSiteDeviceVirtualChassis.return_value = vc_resp
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.readoptSiteOctermDevice.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.readopt_device()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "re-adoption" in out.lower()

    def test_vc_preflight_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_api.api.v1.sites.devices.getSiteDeviceVirtualChassis.side_effect = RuntimeError("vc fail")
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.readoptSiteOctermDevice.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.INFO, logger="root"):
                duc.readopt_device()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "re-adoption" in out.lower()

    def test_readopt_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        vc_resp = MagicMock()
        vc_resp.data = {"is_virtual_chassis": True}
        mock_api.api.v1.sites.devices.getSiteDeviceVirtualChassis.return_value = vc_resp
        mock_api.api.v1.sites.devices.readoptSiteOctermDevice.side_effect = RuntimeError("readopt boom")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.readopt_device()
            assert "readopt boom" in capsys.readouterr().out


class TestGetZtpPassword:
    """Tests for get_ztp_password."""

    @staticmethod
    def _run_with_stdout(
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        stream: io.StringIO,
    ) -> str:
        """Run menu 144 against a stub stdout and return the captured text."""
        resp = MagicMock()
        resp.data = {"password": _ZTP_SECRET}
        mock_api.api.v1.sites.devices.getSiteDeviceZtpPassword.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with patch.object(sys, "stdout", stream):
                duc.get_ztp_password()
        return stream.getvalue()

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.get_ztp_password()

    def test_success_on_terminal_prints_value(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        output = self._run_with_stdout(duc, mock_api, _FakeTerminalStdout())
        assert _ZTP_SECRET in output
        assert "ZTP Password:" in output

    def test_non_terminal_withholds_value(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        output = self._run_with_stdout(duc, mock_api, _FakePipeStdout())
        assert _ZTP_SECRET not in output
        assert _ZTP_SECRET not in capsys.readouterr().out
        assert "withheld" in output
        assert "interactive terminal" in output

    def test_non_terminal_never_logs_the_value(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level(logging.DEBUG):
            self._run_with_stdout(duc, mock_api, _FakePipeStdout())
        assert _ZTP_SECRET not in caplog.text

    def test_terminal_never_logs_the_value(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level(logging.DEBUG):
            self._run_with_stdout(duc, mock_api, _FakeTerminalStdout())
        assert _ZTP_SECRET not in caplog.text

    def test_no_password_data(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resp = MagicMock(spec=[])
        mock_api.api.v1.sites.devices.getSiteDeviceZtpPassword.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.get_ztp_password()
            assert "No password" in capsys.readouterr().out

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_api.api.v1.sites.devices.getSiteDeviceZtpPassword.side_effect = RuntimeError("ztp boom")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.get_ztp_password()
            assert "ztp boom" in capsys.readouterr().out


class TestStdoutIsTerminal:
    """Tests for the stdout terminal check that guards the ZTP credential."""

    def test_true_for_a_terminal(self) -> None:
        with patch.object(sys, "stdout", _FakeTerminalStdout()):
            assert _UtilityCommandsAction._stdout_is_terminal() is True

    def test_false_for_a_pipe(self) -> None:
        with patch.object(sys, "stdout", _FakePipeStdout()):
            assert _UtilityCommandsAction._stdout_is_terminal() is False

    def test_false_when_the_stream_has_no_isatty(self) -> None:
        with patch.object(sys, "stdout", MagicMock(spec=[])):
            assert _UtilityCommandsAction._stdout_is_terminal() is False

    def test_false_when_isatty_raises(self) -> None:
        closed = MagicMock()
        closed.isatty.side_effect = ValueError("stream closed")
        with patch.object(sys, "stdout", closed):
            assert _UtilityCommandsAction._stdout_is_terminal() is False


class TestZtpCredentialMigrationRule:
    """Blocks an issue #886 print-to-logging migration of the ZTP credential.

    Issue #1735 and CodeQL alert 173 record the reason. A mechanical rewrite
    of the credential print would write a live password into
    ``data/script.log``. These tests state the rule in code, so the rule
    survives a comment removal.
    """

    @staticmethod
    def _parse(func: object) -> ast.Module:
        """Return the parsed source tree of one function."""
        return ast.parse(textwrap.dedent(inspect.getsource(func)))

    @staticmethod
    def _logging_calls(tree: ast.Module) -> list[ast.Call]:
        """Return every call whose target is an attribute of ``logging``."""
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        return [
            call
            for call in calls
            if isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "logging"
        ]

    def test_credential_print_has_no_logging_call(self) -> None:
        tree = self._parse(_UtilityCommandsAction._print_ztp_credential)
        assert self._logging_calls(tree) == []

    def test_withheld_notice_has_no_logging_call(self) -> None:
        tree = self._parse(_UtilityCommandsAction._print_ztp_withheld)
        assert self._logging_calls(tree) == []

    def test_renderer_never_passes_the_credential_to_a_log_record(self) -> None:
        tree = self._parse(_UtilityCommandsAction._render_ztp_response.__func__)
        for call in self._logging_calls(tree):
            names = {node.id for node in ast.walk(call) if isinstance(node, ast.Name)}
            assert "ztp_credential" not in names

    def test_credential_print_stays_behind_the_terminal_check(self) -> None:
        source = inspect.getsource(_UtilityCommandsAction._render_ztp_response.__func__)
        assert "_stdout_is_terminal()" in source
        assert "_print_ztp_credential(ztp_credential)" in source

    def test_credential_print_carries_the_review_record(self) -> None:
        doc = inspect.getdoc(_UtilityCommandsAction._print_ztp_credential) or ""
        assert "2026-08-22" in doc
        assert "#1735" in doc
        assert "#886" in doc


class TestGetConfigCommands:
    """Tests for get_config_commands."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.get_config_commands()

    def test_success_dict(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resp = MagicMock()
        resp.data = {"set_commands": "set interfaces ge-0/0/0"}
        mock_api.api.v1.sites.devices.getSiteDeviceConfigCmd.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.get_config_commands()
            out = capsys.readouterr().out
            assert "set interfaces" in out

    def test_success_string(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resp = MagicMock()
        resp.data = "some string config"
        mock_api.api.v1.sites.devices.getSiteDeviceConfigCmd.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.get_config_commands()
            out = capsys.readouterr().out
            assert "some string config" in out

    def test_no_data(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resp = MagicMock(spec=[])
        mock_api.api.v1.sites.devices.getSiteDeviceConfigCmd.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.get_config_commands()
            assert "No configuration" in capsys.readouterr().out

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_api.api.v1.sites.devices.getSiteDeviceConfigCmd.side_effect = RuntimeError("cmd fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.get_config_commands()
            assert "cmd fail" in capsys.readouterr().out


# ===================================================================
# Clear/Reset commands - success paths
# ===================================================================


class TestClearBgpRoutes:
    """Tests for clear_bgp_routes."""

    def test_early_return_no_selection(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.clear_bgp_routes()

    def test_no_neighbor(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            with caplog.at_level(logging.WARNING):
                duc.clear_bgp_routes()
            assert "required" in caplog.text.lower()

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["10.0.0.1", "", "", "", "nope"]
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            duc.clear_bgp_routes()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["10.0.0.1", "in", "myvrf", "node0", "CLEAR"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearSiteSsrBgpRoutes.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            duc.clear_bgp_routes()
            mock_api.api.v1.sites.devices.clearSiteSsrBgpRoutes.assert_called_once()

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["10.0.0.1", "", "", "", "CLEAR"]
        mock_api.api.v1.sites.devices.clearSiteSsrBgpRoutes.side_effect = RuntimeError("bgp fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            with caplog.at_level(logging.ERROR):
                duc.clear_bgp_routes()
            assert "bgp fail" in caplog.text


class TestClearSession:
    """Tests for clear_session."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.clear_session()

    def test_with_service_name(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["my_service", "", "", "CLEAR"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearSiteDeviceSession.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            duc.clear_session()
            mock_api.api.v1.sites.devices.clearSiteDeviceSession.assert_called_once()

    def test_with_session_ids(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "id1, id2", "", "CLEAR"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearSiteDeviceSession.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            duc.clear_session()
            call_body = mock_api.api.v1.sites.devices.clearSiteDeviceSession.call_args[0][3]
            assert call_body["session_ids"] == ["id1", "id2"]

    def test_no_ids_no_service_cancel(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "", "nope"]
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            with caplog.at_level(logging.WARNING):
                duc.clear_session()
            assert "Cancelled" in caplog.text

    def test_no_ids_no_service_confirm_all(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "", "CLEAR ALL", "", "CLEAR"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearSiteDeviceSession.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            duc.clear_session()
            mock_api.api.v1.sites.devices.clearSiteDeviceSession.assert_called_once()

    def test_exception_400(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["svc", "", "", "CLEAR"]
        error = RuntimeError("bad input")
        error.status_code = 400  # type: ignore[attr-defined]
        mock_api.api.v1.sites.devices.clearSiteDeviceSession.side_effect = error
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            with caplog.at_level(logging.ERROR, logger="root"):
                duc.clear_session()
            out = "\n".join(r.getMessage() for r in caplog.records)
            assert "400" in out or "service_name" in out


class TestClearMacTable:
    """Tests for clear_mac_table."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.clear_mac_table()

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "nope"]
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.clear_mac_table()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "CLEAR"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearSiteDeviceMacTable.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.clear_mac_table()
            mock_api.api.v1.sites.devices.clearSiteDeviceMacTable.assert_called_once()

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "CLEAR"]
        mock_api.api.v1.sites.devices.clearSiteDeviceMacTable.side_effect = RuntimeError("mac fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            with caplog.at_level(logging.ERROR):
                duc.clear_mac_table()
            assert "mac fail" in caplog.text


class TestClearBpduError:
    """Tests for clear_bpdu_error."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.clear_bpdu_error()

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_optional", return_value=""),
            patch.object(duc, "_confirm_destructive", return_value=False),
        ):
            duc.clear_bpdu_error()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearBpduErrorsFromPortsOnSwitch.return_value = resp
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_optional", return_value="ge-0/0/0"),
            patch.object(duc, "_confirm_destructive", return_value=True),
        ):
            duc.clear_bpdu_error()
            mock_api.api.v1.sites.devices.clearBpduErrorsFromPortsOnSwitch.assert_called_once()

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_api.api.v1.sites.devices.clearBpduErrorsFromPortsOnSwitch.side_effect = RuntimeError("bpdu fail")
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_optional", return_value=""),
            patch.object(duc, "_confirm_destructive", return_value=True),
        ):
            with caplog.at_level(logging.ERROR):
                duc.clear_bpdu_error()
            assert "bpdu fail" in caplog.text


class TestClearLearnedMacs:
    """Tests for clear_learned_macs."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.clear_learned_macs()

    def test_no_port(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value=None),
        ):
            with caplog.at_level(logging.WARNING):
                duc.clear_learned_macs()
            assert "required" in caplog.text.lower()

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_confirm_destructive", return_value=False),
        ):
            duc.clear_learned_macs()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearAllLearnedMacsFromPortOnSwitch.return_value = resp
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_confirm_destructive", return_value=True),
        ):
            duc.clear_learned_macs()
            call_body = mock_api.api.v1.sites.devices.clearAllLearnedMacsFromPortOnSwitch.call_args[0][3]
            assert call_body["ports"] == ["ge-0/0/0.0"]

    def test_port_with_unit(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
    ) -> None:
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearAllLearnedMacsFromPortOnSwitch.return_value = resp
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0.5"),
            patch.object(duc, "_confirm_destructive", return_value=True),
        ):
            duc.clear_learned_macs()
            call_body = mock_api.api.v1.sites.devices.clearAllLearnedMacsFromPortOnSwitch.call_args[0][3]
            assert call_body["ports"] == ["ge-0/0/0.5"]

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_api.api.v1.sites.devices.clearAllLearnedMacsFromPortOnSwitch.side_effect = RuntimeError("macs fail")
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
            patch.object(duc, "_confirm_destructive", return_value=True),
        ):
            with caplog.at_level(logging.ERROR):
                duc.clear_learned_macs()
            assert "macs fail" in caplog.text


class TestClearPolicyHitCount:
    """Tests for clear_policy_hit_count."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.clear_policy_hit_count()

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "nope"]
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            duc.clear_policy_hit_count()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["node0", "CLEAR"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.clearSiteDevicePolicyHitCount.return_value = resp
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            duc.clear_policy_hit_count()
            mock_api.api.v1.sites.devices.clearSiteDevicePolicyHitCount.assert_called_once()

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "CLEAR"]
        mock_api.api.v1.sites.devices.clearSiteDevicePolicyHitCount.side_effect = RuntimeError("policy fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")):
            with caplog.at_level(logging.ERROR):
                duc.clear_policy_hit_count()
            assert "policy fail" in caplog.text


class TestReleaseDhcpLease:
    """Tests for release_dhcp_lease."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.release_dhcp_lease()

    def test_no_port(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value=None),
        ):
            with caplog.at_level(logging.WARNING):
                duc.release_dhcp_lease()
            assert "required" in caplog.text.lower()

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "n"]
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
        ):
            duc.release_dhcp_lease()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "y"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.releaseSiteDeviceDhcpLease.return_value = resp
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
        ):
            duc.release_dhcp_lease()
            mock_api.api.v1.sites.devices.releaseSiteDeviceDhcpLease.assert_called_once()

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "y"]
        mock_api.api.v1.sites.devices.releaseSiteDeviceDhcpLease.side_effect = RuntimeError("dhcp fail")
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")),
            patch.object(duc, "_select_port_from_device", return_value="ge-0/0/0"),
        ):
            with caplog.at_level(logging.ERROR):
                duc.release_dhcp_lease()
            assert "dhcp fail" in caplog.text


class TestReleaseDhcpSsr:
    """Tests for release_dhcp_ssr."""

    def test_early_return(self, duc: DeviceUtilityCommands) -> None:
        with patch.object(duc, "_select_site_and_device", return_value=None):
            duc.release_dhcp_ssr()

    def test_no_interface(
        self,
        duc: DeviceUtilityCommands,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_select_interface_from_device", return_value=None),
        ):
            with caplog.at_level(logging.WARNING):
                duc.release_dhcp_ssr()
            assert "required" in caplog.text.lower()

    def test_cancelled(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "n"]
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_select_interface_from_device", return_value="wan0"),
        ):
            duc.release_dhcp_ssr()

    def test_success(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "y"]
        resp = _mock_api_response(200)
        mock_api.api.v1.sites.devices.releaseSiteSsrDhcpLease.return_value = resp
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_select_interface_from_device", return_value="wan0"),
        ):
            duc.release_dhcp_ssr()
            mock_api.api.v1.sites.devices.releaseSiteSsrDhcpLease.assert_called_once()

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        mock_api: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_deps["safe_input_fn"].side_effect = ["", "y"]
        mock_api.api.v1.sites.devices.releaseSiteSsrDhcpLease.side_effect = RuntimeError("ssr fail")
        with (
            patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "gateway")),
            patch.object(duc, "_select_interface_from_device", return_value="wan0"),
        ):
            with caplog.at_level(logging.ERROR):
                duc.release_dhcp_ssr()
            assert "ssr fail" in caplog.text


# ===================================================================
# Hardware commands - extended
# ===================================================================


class TestPollSwitchStatsExtended:
    """Extended tests for poll_switch_stats."""

    def test_exception(
        self,
        duc: DeviceUtilityCommands,
        mock_api: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_api.api.v1.sites.devices.pollSiteSwitchStats.side_effect = RuntimeError("poll fail")
        with patch.object(duc, "_select_site_and_device", return_value=("s1", "d1", "switch")):
            duc.poll_switch_stats()
            assert "poll fail" in capsys.readouterr().out


# ===================================================================
# _display_and_export_result - extended
# ===================================================================


class TestDisplayAndExportResultExtended:
    """Extended tests for edge cases."""

    def test_output_key_used(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger=_WS_LOGGER)
        result = {"Output": "output text"}
        duc._display_and_export_result(
            ExportResultSpec(
                result=result,
                command_name="cmd",
                site_id="s1",
                device_id="d1",
                api_function_name="apiFunc",
                filename="file.csv",
            )
        )
        assert "output text" in caplog.text


# ===================================================================
# _display_and_select_ifstat - extended
# ===================================================================


class TestDisplayAndSelectIfstatExtended:
    """Extended tests for _display_and_select_ifstat."""

    def test_empty_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = ""
        if_stat = {"ge-0/0/0": {"up": True}}
        assert duc._display_and_select_ifstat(if_stat) is None

    def test_invalid_number(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "99"
        if_stat = {"ge-0/0/0": {"up": True}}
        assert duc._display_and_select_ifstat(if_stat) is None

    def test_text_selection(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "xe-0/0/1"
        if_stat = {"ge-0/0/0": {"up": True}}
        assert duc._display_and_select_ifstat(if_stat) == "xe-0/0/1"

    def test_non_physical_keys(
        self,
        duc: DeviceUtilityCommands,
        mock_deps: dict[str, MagicMock],
    ) -> None:
        mock_deps["safe_input_fn"].return_value = "1"
        if_stat = {"lo0": {"up": True}, "irb": {"up": True}}
        result = duc._display_and_select_ifstat(if_stat)
        assert result in ("lo0", "irb")


class TestHandleClearSessionError:
    """Tests for _handle_clear_session_error."""

    def test_generic_error(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.ERROR, logger="root"):
            DeviceUtilityCommands._handle_clear_session_error(RuntimeError("generic"))
        out = "\n".join(r.getMessage() for r in caplog.records)
        assert "generic" in out

    def test_nested_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Cover the inner except branch."""

        class BadError(Exception):
            @property
            def status_code(self) -> int:
                raise ValueError("no code")

        with caplog.at_level(logging.ERROR, logger="root"):
            DeviceUtilityCommands._handle_clear_session_error(BadError("bad"))
        out = "\n".join(r.getMessage() for r in caplog.records)
        assert "bad" in out
