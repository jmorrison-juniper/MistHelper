"""Unit tests for the WebSocket MacTableCommand orchestrator.

Covers src/websocket/commands.py: the MacTableCommand class dispatches the Mist
`show_mac_table` RPC over a WebSocket. These tests pin the branching (debug
on/off, operator abort at each interactive prompt, WS connect failure, RPC
failure, timeout vs successful result) so future refactors of the workflow
cannot silently change the observable contract.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from src.websocket import commands as commands_mod
from src.websocket.commands import MacTableCommand


def _fake_response(status: int, body: dict[str, Any] | None = None, text: str = "") -> MagicMock:
    """Build a MagicMock that mimics requests.Response with .status_code/.json()/.text."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = body or {}
    resp.text = text or (str(body) if body else "")
    return resp


def _fake_deps() -> MagicMock:
    """Build a MagicMock WebSocketCmdDeps stand-in with the attributes used in commands.py."""
    deps = MagicMock()
    deps.apisession = MagicMock()
    deps.select_device_fn = MagicMock()
    return deps


# ---------- _enter_workflow ----------


def test_enter_workflow_debug_off_returns_false(capsys) -> None:
    """Without --debug/-d in argv, _enter_workflow returns False and prints no banner."""
    with patch.object(commands_mod.sys, "argv", ["prog"]):
        assert MacTableCommand._enter_workflow() is False
    assert "DEBUG MODE ENABLED" not in capsys.readouterr().out


def test_enter_workflow_debug_on_long_flag_prints_banner(capsys) -> None:
    """--debug in argv → returns True, raises log level, prints banner."""
    with patch.object(commands_mod.sys, "argv", ["prog", "--debug"]):
        assert MacTableCommand._enter_workflow() is True
    assert "DEBUG MODE ENABLED" in capsys.readouterr().out


def test_enter_workflow_debug_on_short_flag(capsys) -> None:
    """-d in argv also flips debug mode on."""
    with patch.object(commands_mod.sys, "argv", ["prog", "-d"]):
        assert MacTableCommand._enter_workflow() is True
    assert "DEBUG MODE ENABLED" in capsys.readouterr().out


# ---------- _announce_session ----------


def test_announce_session_debug_off_prints_only_progress(capsys) -> None:
    """With debug_mode=False, only the two legacy progress lines print (no full-id echo)."""
    MacTableCommand._announce_session("abcdef1234567890", debug_mode=False)
    out = capsys.readouterr().out
    assert "session: abcdef12..." in out
    assert "Waiting for MAC table results" in out
    assert "Full session ID" not in out


def test_announce_session_debug_on_prints_full_id(capsys) -> None:
    """With debug_mode=True, additional lines echo full session id and pre-wait notice."""
    MacTableCommand._announce_session("full-session-id-123", debug_mode=True)
    out = capsys.readouterr().out
    assert "Full session ID = full-session-id-123" in out
    assert "Starting to wait for WebSocket results" in out


# ---------- _resolve_targets ----------


def test_resolve_targets_site_abort_returns_none(capsys) -> None:
    """Operator cancels site selection → returns None; device picker never invoked."""
    deps = _fake_deps()
    with patch.object(commands_mod, "select_ws_site", return_value=None):
        assert MacTableCommand._resolve_targets(deps, debug_mode=False) is None
    deps.select_device_fn.assert_not_called()


def test_resolve_targets_no_device_returns_none(capsys) -> None:
    """Operator picks site but returns no switch → prints legacy warnings and returns None."""
    deps = _fake_deps()
    deps.select_device_fn.return_value = None
    with patch.object(commands_mod, "select_ws_site", return_value="site-1"):
        assert MacTableCommand._resolve_targets(deps, debug_mode=False) is None
    out = capsys.readouterr().out
    assert "No switch device selected" in out
    assert "Only switches maintain" in out


def test_resolve_targets_success_returns_tuple(capsys) -> None:
    """Both selections succeed → returns (site_id, device_id); debug OFF has no debug print."""
    deps = _fake_deps()
    deps.select_device_fn.return_value = "device-1"
    with patch.object(commands_mod, "select_ws_site", return_value="site-1"):
        got = MacTableCommand._resolve_targets(deps, debug_mode=False)
    assert got == ("site-1", "device-1")
    deps.select_device_fn.assert_called_once_with("site-1", device_type="switch")
    assert "[DEBUG] Selected device_id" not in capsys.readouterr().out


def test_resolve_targets_debug_prints_device_id(capsys) -> None:
    """debug_mode=True adds device-id debug line after successful selection."""
    deps = _fake_deps()
    deps.select_device_fn.return_value = "device-1"
    with patch.object(commands_mod, "select_ws_site", return_value="site-1"):
        MacTableCommand._resolve_targets(deps, debug_mode=True)
    assert "[DEBUG] Selected device_id = device-1" in capsys.readouterr().out


# ---------- _open_websocket ----------


def test_open_websocket_connect_failure_returns_none() -> None:
    """When connect_and_subscribe returns False, helper returns None."""
    deps = _fake_deps()
    wm = MagicMock()
    wm.connect_and_subscribe.return_value = False
    with patch.object(commands_mod, "WebSocketManager", return_value=wm):
        assert MacTableCommand._open_websocket(deps, "s", "d", debug_mode=False) is None


def test_open_websocket_connect_success_returns_manager() -> None:
    """When connect_and_subscribe returns True, helper returns the manager."""
    deps = _fake_deps()
    wm = MagicMock()
    wm.connect_and_subscribe.return_value = True
    with patch.object(commands_mod, "WebSocketManager", return_value=wm):
        got = MacTableCommand._open_websocket(deps, "s", "d", debug_mode=True)
    assert got is wm
    wm.connect_and_subscribe.assert_called_once_with("s", "d", True)


# ---------- _resolve_and_check_credentials ----------


def test_resolve_and_check_credentials_failure_returns_none() -> None:
    """check_mist_credentials False → helper returns None (validator owns error print)."""
    deps = _fake_deps()
    wm = MagicMock()
    with (
        patch.object(commands_mod, "get_mist_credentials", return_value=("h", "t")),
        patch.object(commands_mod, "check_mist_credentials", return_value=False),
    ):
        assert MacTableCommand._resolve_and_check_credentials(deps, wm, debug_mode=False) is None


def test_resolve_and_check_credentials_success_returns_tuple() -> None:
    """check_mist_credentials True → returns (host, token) tuple."""
    deps = _fake_deps()
    wm = MagicMock()
    with (
        patch.object(commands_mod, "get_mist_credentials", return_value=("host.example", "tok")),
        patch.object(commands_mod, "check_mist_credentials", return_value=True),
    ):
        got = MacTableCommand._resolve_and_check_credentials(deps, wm, debug_mode=True)
    assert got == ("host.example", "tok")


# ---------- _post_show_mac_table ----------


def test_post_show_mac_table_returns_response_debug_off(capsys) -> None:
    """Debug OFF: posts to expected URL, returns response, no debug prints for URL/headers/body."""
    fake = _fake_response(200, {"session": "s"})
    with patch.object(commands_mod.requests, "post", return_value=fake) as mock_post:
        got = MacTableCommand._post_show_mac_table("host", "tok", "site-1", "dev-1", debug_mode=False)
    assert got is fake
    args, kwargs = mock_post.call_args
    assert args[0] == "https://host/api/v1/sites/site-1/devices/dev-1/show_mac_table"
    assert kwargs["headers"]["Authorization"] == "Token tok"
    assert kwargs["json"] == {}
    assert kwargs["timeout"] == 30
    out = capsys.readouterr().out
    assert "[DEBUG] POST URL" not in out
    assert "[DEBUG] HTTP Response" not in out
    # Progress line is always printed
    assert "Issuing show MAC table command" in out


def test_post_show_mac_table_prints_debug_when_enabled(capsys) -> None:
    """Debug ON: prints payload, URL, redacted headers, HTTP status and body."""
    fake = _fake_response(200, {"session": "sess"}, text="body-here")
    with patch.object(commands_mod.requests, "post", return_value=fake):
        MacTableCommand._post_show_mac_table("h", "tok-real", "s", "d", debug_mode=True)
    out = capsys.readouterr().out
    assert "[DEBUG] MAC table payload" in out
    assert "[DEBUG] POST URL = https://h/api/v1/sites/s/devices/d/show_mac_table" in out
    assert "[REDACTED]" in out and "tok-real" not in out
    assert "HTTP Response Status = 200" in out
    assert "body-here" in out


# ---------- _extract_session_id ----------


def test_extract_session_id_non_200_disconnects_and_returns_none(capsys) -> None:
    """Non-200 response prints failure, disconnects WS, returns None."""
    wm = MagicMock()
    resp = _fake_response(500, text="boom")
    assert MacTableCommand._extract_session_id(resp, wm) is None
    wm.disconnect.assert_called_once()
    out = capsys.readouterr().out
    assert "Failed to issue show MAC table command: 500" in out
    assert "boom" in out


def test_extract_session_id_missing_session_disconnects_and_returns_none(capsys) -> None:
    """200 response without session key disconnects and returns None."""
    wm = MagicMock()
    resp = _fake_response(200, {"other": "data"})
    assert MacTableCommand._extract_session_id(resp, wm) is None
    wm.disconnect.assert_called_once()
    assert "No session ID returned" in capsys.readouterr().out


def test_extract_session_id_empty_session_disconnects_and_returns_none(capsys) -> None:
    """200 response with empty session id is treated as missing."""
    wm = MagicMock()
    resp = _fake_response(200, {"session": ""})
    assert MacTableCommand._extract_session_id(resp, wm) is None
    wm.disconnect.assert_called_once()


def test_extract_session_id_success_returns_id() -> None:
    """200 with session key returns the id; WS is NOT disconnected."""
    wm = MagicMock()
    resp = _fake_response(200, {"session": "abc-123"})
    assert MacTableCommand._extract_session_id(resp, wm) == "abc-123"
    wm.disconnect.assert_not_called()


# ---------- _trigger_rpc ----------


def test_trigger_rpc_credentials_failure_returns_none() -> None:
    """Credential validation failure → _trigger_rpc returns None early."""
    deps = _fake_deps()
    wm = MagicMock()
    with patch.object(MacTableCommand, "_resolve_and_check_credentials", return_value=None):
        assert MacTableCommand._trigger_rpc(deps, wm, "s", "d", debug_mode=False) is None


def test_trigger_rpc_success_returns_session_id() -> None:
    """Full success path: creds → POST → extract → returns session id."""
    deps = _fake_deps()
    wm = MagicMock()
    fake_resp = _fake_response(200, {"session": "sid"})
    with (
        patch.object(MacTableCommand, "_resolve_and_check_credentials", return_value=("h", "t")),
        patch.object(MacTableCommand, "_post_show_mac_table", return_value=fake_resp),
    ):
        got = MacTableCommand._trigger_rpc(deps, wm, "s", "d", debug_mode=False)
    assert got == "sid"


# ---------- _render_primary_output ----------


def test_render_primary_output_raw_only(capsys) -> None:
    """When only raw is present, RAW OUTPUT block prints, OTHER OUTPUT does not."""
    MacTableCommand._render_primary_output("mac table dump", "")
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out
    assert "mac table dump" in out
    assert "OTHER OUTPUT" not in out


def test_render_primary_output_output_distinct_prints_both(capsys) -> None:
    """When Output differs from raw, both sections print."""
    MacTableCommand._render_primary_output("raw-x", "output-y")
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out and "raw-x" in out
    assert "OTHER OUTPUT:" in out and "output-y" in out


def test_render_primary_output_output_equal_to_raw_prints_once(capsys) -> None:
    """When Output == raw, only RAW section prints (no duplicate)."""
    MacTableCommand._render_primary_output("same", "same")
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out
    assert "OTHER OUTPUT" not in out


def test_render_primary_output_both_empty_prints_nothing(capsys) -> None:
    """Empty raw and Output → no section header prints."""
    MacTableCommand._render_primary_output("", "")
    assert capsys.readouterr().out == ""


# ---------- _collect_extras ----------


def test_collect_extras_filters_transport_keys_and_falsy() -> None:
    """Transport keys and falsey values are excluded from the extras dict."""
    payload = {
        "raw": "x",
        "Output": "y",
        "session": "s",
        "extra1": "val1",
        "empty": "",
        "extra2": 42,
    }
    got = MacTableCommand._collect_extras(payload)
    assert got == {"extra1": "val1", "extra2": 42}


def test_collect_extras_returns_empty_when_nothing_to_show() -> None:
    """All entries either transport or empty → returns empty dict."""
    payload = {"raw": "x", "Output": "y", "session": "s", "empty": ""}
    assert MacTableCommand._collect_extras(payload) == {}


# ---------- _render_extra_fields ----------


def test_render_extra_fields_noop_when_empty(capsys) -> None:
    """No extras → prints nothing."""
    MacTableCommand._render_extra_fields({"raw": "x", "session": "s"})
    assert capsys.readouterr().out == ""


def test_render_extra_fields_prints_header_and_values(capsys) -> None:
    """Extras present → header + one line per extra."""
    MacTableCommand._render_extra_fields({"raw": "x", "extra1": "v1", "extra2": 42})
    out = capsys.readouterr().out
    assert "OTHER AVAILABLE FIELDS: ['extra1', 'extra2']" in out
    assert "extra1: v1" in out
    assert "extra2: 42" in out


# ---------- _render_result ----------


def test_render_result_with_raw_data(capsys) -> None:
    """With raw output, RAW OUTPUT block prints and 'No output data' does NOT appear."""
    MacTableCommand._render_result({"raw": "mac-table-dump", "extra": "x"})
    out = capsys.readouterr().out
    assert "MAC TABLE RESULTS:" in out
    assert "mac-table-dump" in out
    assert "OTHER AVAILABLE FIELDS" in out
    assert "No output data received" not in out


def test_render_result_no_raw_or_output_prints_empty_notice(capsys) -> None:
    """Without raw and Output, the 'No output data received' diagnostic prints."""
    MacTableCommand._render_result({"session": "s"})
    out = capsys.readouterr().out
    assert "No output data received" in out
    assert "Available result keys" in out


# ---------- _render_timeout ----------


def test_render_timeout_prints_banner_and_calls_dump(capsys) -> None:
    """Prints legacy timeout banner and invokes dump_ws_debug_state for verbose diagnostics."""
    wm = MagicMock()
    with patch.object(commands_mod, "dump_ws_debug_state") as mock_dump:
        MacTableCommand._render_timeout(wm, debug_mode=True)
    out = capsys.readouterr().out
    assert "Timeout waiting for MAC table results" in out
    assert "MAC tables are primarily a Layer 2" in out
    mock_dump.assert_called_once_with(wm, True)


# ---------- _await_and_display ----------


def test_await_and_display_success_calls_render_result(capsys) -> None:
    """When wait returns data, _render_result is invoked and no timeout render occurs."""
    wm = MagicMock()
    wm.wait_for_command_result.return_value = {"raw": "data"}
    with (
        patch.object(MacTableCommand, "_render_result") as mock_render,
        patch.object(MacTableCommand, "_render_timeout") as mock_timeout,
    ):
        MacTableCommand._await_and_display(wm, "sess-1", debug_mode=False)
    mock_render.assert_called_once_with({"raw": "data"})
    mock_timeout.assert_not_called()


def test_await_and_display_success_debug_prints_keys(capsys) -> None:
    """Debug ON with a result → prints DEBUG lines including result keys."""
    wm = MagicMock()
    wm.wait_for_command_result.return_value = {"raw": "data"}
    with patch.object(MacTableCommand, "_render_result"):
        MacTableCommand._await_and_display(wm, "sess-1", debug_mode=True)
    out = capsys.readouterr().out
    assert "[DEBUG] wait_for_command_result returned: True" in out
    assert "[DEBUG] Result keys:" in out


def test_await_and_display_timeout_calls_render_timeout() -> None:
    """When wait returns None, _render_timeout is invoked, _render_result is not."""
    wm = MagicMock()
    wm.wait_for_command_result.return_value = None
    with (
        patch.object(MacTableCommand, "_render_result") as mock_render,
        patch.object(MacTableCommand, "_render_timeout") as mock_timeout,
    ):
        MacTableCommand._await_and_display(wm, "sess-1", debug_mode=False)
    mock_render.assert_not_called()
    mock_timeout.assert_called_once_with(wm, False)


def test_await_and_display_timeout_debug_skips_result_keys_line(capsys) -> None:
    """Debug ON + None result → prints 'returned: False' but NOT 'Result keys' (covers 218→221)."""
    wm = MagicMock()
    wm.wait_for_command_result.return_value = None
    with patch.object(MacTableCommand, "_render_timeout"):
        MacTableCommand._await_and_display(wm, "sess-1", debug_mode=True)
    out = capsys.readouterr().out
    assert "[DEBUG] wait_for_command_result returned: False" in out
    assert "Result keys" not in out


# ---------- _run_workflow ----------


def test_run_workflow_targets_abort_returns_none() -> None:
    """Operator aborts target selection → _run_workflow returns None; no WS opened."""
    deps = _fake_deps()
    with (
        patch.object(MacTableCommand, "_resolve_targets", return_value=None),
        patch.object(MacTableCommand, "_open_websocket") as mock_open,
    ):
        assert MacTableCommand._run_workflow(deps, debug_mode=False) is None
    mock_open.assert_not_called()


def test_run_workflow_open_websocket_failure_returns_none() -> None:
    """WS connect failure → returns None; RPC helper never invoked."""
    deps = _fake_deps()
    with (
        patch.object(MacTableCommand, "_resolve_targets", return_value=("s", "d")),
        patch.object(MacTableCommand, "_open_websocket", return_value=None),
        patch.object(MacTableCommand, "_trigger_rpc") as mock_rpc,
    ):
        assert MacTableCommand._run_workflow(deps, debug_mode=False) is None
    mock_rpc.assert_not_called()


def test_run_workflow_rpc_failure_returns_manager() -> None:
    """RPC failure → helper returns the WS manager so caller can cleanup; no await/display."""
    deps = _fake_deps()
    wm = MagicMock()
    with (
        patch.object(MacTableCommand, "_resolve_targets", return_value=("s", "d")),
        patch.object(MacTableCommand, "_open_websocket", return_value=wm),
        patch.object(MacTableCommand, "_trigger_rpc", return_value=None),
        patch.object(MacTableCommand, "_await_and_display") as mock_await,
    ):
        got = MacTableCommand._run_workflow(deps, debug_mode=False)
    assert got is wm
    mock_await.assert_not_called()


def test_run_workflow_full_success_returns_manager() -> None:
    """Happy path: all helpers succeed, _await_and_display is called, manager is returned."""
    deps = _fake_deps()
    wm = MagicMock()
    with (
        patch.object(MacTableCommand, "_resolve_targets", return_value=("s", "d")),
        patch.object(MacTableCommand, "_open_websocket", return_value=wm),
        patch.object(MacTableCommand, "_trigger_rpc", return_value="sess-id"),
        patch.object(MacTableCommand, "_announce_session") as mock_announce,
        patch.object(MacTableCommand, "_await_and_display") as mock_await,
    ):
        got = MacTableCommand._run_workflow(deps, debug_mode=True)
    assert got is wm
    mock_announce.assert_called_once_with("sess-id", True)
    mock_await.assert_called_once_with(wm, "sess-id", True)


# ---------- execute ----------


def test_execute_happy_path_cleans_up() -> None:
    """execute() runs workflow and always invokes cleanup_ws_connection in finally."""
    deps = _fake_deps()
    wm = MagicMock()
    with (
        patch.object(MacTableCommand, "_enter_workflow", return_value=False),
        patch.object(MacTableCommand, "_run_workflow", return_value=wm),
        patch.object(commands_mod, "cleanup_ws_connection") as mock_cleanup,
        patch.object(commands_mod, "log_ws_error") as mock_err,
    ):
        MacTableCommand.execute(deps)
    mock_cleanup.assert_called_once_with(wm, False)
    mock_err.assert_not_called()


def test_execute_exception_logs_and_cleans_up() -> None:
    """execute() catches workflow exceptions, invokes log_ws_error, then cleans up."""
    deps = _fake_deps()
    with (
        patch.object(MacTableCommand, "_enter_workflow", return_value=True),
        patch.object(MacTableCommand, "_run_workflow", side_effect=RuntimeError("boom")),
        patch.object(commands_mod, "cleanup_ws_connection") as mock_cleanup,
        patch.object(commands_mod, "log_ws_error") as mock_err,
    ):
        MacTableCommand.execute(deps)
    # Manager is None because _run_workflow raised before returning
    mock_cleanup.assert_called_once_with(None, True)
    assert mock_err.call_count == 1
    err_msg = mock_err.call_args.args[0]
    assert "WebSocket show MAC table operation failed" in err_msg
    assert "boom" in err_msg
