"""Unit tests for the PingDeviceExecutor.

Covers src/websocket/diagnostics/ping_executor.py. The executor orchestrates the
interactive ping-over-WebSocket workflow: site + device prompts, target/count
validation, WebSocket connect + subscribe, HTTP POST of the ping command,
session-id demux, WS wait for the result, and result rendering (raw block,
Other output block, extras, empty diagnostic, and timeouts).

These tests pin every branch — including debug-echo lines and
error-swallow paths — so future refactors of the executor cannot silently
change the observable operator contract.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from src.websocket.diagnostics import ping_executor as ping_mod
from src.websocket.diagnostics.ping_executor import PingDeviceExecutor


def _make_deps(
    *,
    select_site_return: Any = "site-1",
    select_device_return: Any = "dev-1",
    validate_return: bool = True,
    safe_input_returns: list[str] | None = None,
) -> SimpleNamespace:
    """Build a WebSocketCmdDeps-shaped stub for the executor under test."""
    apisession = MagicMock(name="apisession")
    select_site_fn = MagicMock(return_value=select_site_return)
    select_device_fn = MagicMock(return_value=select_device_return)
    validate_target_fn = MagicMock(return_value=validate_return)
    if safe_input_returns is None:
        safe_input_returns = ["", ""]
    safe_input_fn = MagicMock(side_effect=safe_input_returns)
    return SimpleNamespace(
        apisession=apisession,
        select_site_fn=select_site_fn,
        select_device_fn=select_device_fn,
        validate_target_fn=validate_target_fn,
        list_devices_fn=MagicMock(),
        safe_input_fn=safe_input_fn,
    )


# ---------- _emit_debug_banner ----------


def test_emit_debug_banner_off_no_prints(capsys) -> None:
    """debug_mode=False: no banner printed; root logger untouched."""
    PingDeviceExecutor._emit_debug_banner(False)
    assert "[DEBUG]" not in capsys.readouterr().out


def test_emit_debug_banner_on_prints_and_sets_level(capsys) -> None:
    """debug_mode=True: prints banner and elevates root logger to DEBUG."""
    import logging as _logging

    original_level = _logging.getLogger().level
    try:
        PingDeviceExecutor._emit_debug_banner(True)
        out = capsys.readouterr().out
        assert "[DEBUG] DEBUG MODE ENABLED" in out
        assert _logging.getLogger().level == _logging.DEBUG
    finally:
        _logging.getLogger().setLevel(original_level)


# ---------- _select_device ----------


def test_select_device_none_prints_and_returns_none(capsys) -> None:
    """No device_id returned: prints legacy phrase, returns None."""
    deps = _make_deps(select_device_return=None)
    got = PingDeviceExecutor._select_device(deps, "site-1", False)
    assert got is None
    assert "! No device selected. Operation cancelled." in capsys.readouterr().out


def test_select_device_success_debug_echoes(capsys) -> None:
    """Debug ON: prints selected id; returns id."""
    deps = _make_deps(select_device_return="dev-99")
    got = PingDeviceExecutor._select_device(deps, "site-1", True)
    assert got == "dev-99"
    assert "[DEBUG] Selected device_id = dev-99" in capsys.readouterr().out


def test_select_device_success_no_debug_no_echo(capsys) -> None:
    """Debug OFF: returns id without echoing."""
    deps = _make_deps(select_device_return="dev-42")
    got = PingDeviceExecutor._select_device(deps, "site-1", False)
    assert got == "dev-42"
    assert "[DEBUG]" not in capsys.readouterr().out


# ---------- _prompt_target_host ----------


def test_prompt_target_host_default_when_empty(capsys) -> None:
    """Empty input → default target; debug echoes default."""
    deps = _make_deps(safe_input_returns=[""])
    executor = PingDeviceExecutor()
    got = executor._prompt_target_host(deps, True)
    assert got == "8.8.8.8"
    assert "[DEBUG] Target host = 8.8.8.8" in capsys.readouterr().out


def test_prompt_target_host_valid_no_debug(capsys) -> None:
    """Non-empty valid input; debug OFF → no echo."""
    deps = _make_deps(safe_input_returns=["1.2.3.4"])
    got = PingDeviceExecutor()._prompt_target_host(deps, False)
    assert got == "1.2.3.4"
    assert "[DEBUG]" not in capsys.readouterr().out


def test_prompt_target_host_invalid_returns_none(capsys) -> None:
    """Validator rejects: prints error, returns None."""
    deps = _make_deps(safe_input_returns=["bad!"], validate_return=False)
    got = PingDeviceExecutor()._prompt_target_host(deps, False)
    assert got is None
    assert "! Invalid ping target: bad!" in capsys.readouterr().out


# ---------- _parse_ping_count ----------


def test_parse_ping_count_empty_uses_default() -> None:
    """Empty input → default (4)."""
    assert PingDeviceExecutor._parse_ping_count("") == 4


def test_parse_ping_count_non_numeric_falls_back(capsys) -> None:
    """Non-numeric → warn + default."""
    assert PingDeviceExecutor._parse_ping_count("abc") == 4
    assert "! Invalid ping count. Using default: 4" in capsys.readouterr().out


def test_parse_ping_count_below_min_falls_back(capsys) -> None:
    """Below min → warn range + default."""
    assert PingDeviceExecutor._parse_ping_count("0") == 4
    assert "must be between 1 and 100" in capsys.readouterr().out


def test_parse_ping_count_above_max_falls_back(capsys) -> None:
    """Above max → warn range + default."""
    assert PingDeviceExecutor._parse_ping_count("101") == 4
    assert "must be between 1 and 100" in capsys.readouterr().out


def test_parse_ping_count_valid_returns_int() -> None:
    """Valid int in range → returned verbatim."""
    assert PingDeviceExecutor._parse_ping_count("10") == 10


# ---------- _announce_count ----------


def test_announce_count_debug_prints(capsys) -> None:
    """Debug ON echoes count; returns count."""
    assert PingDeviceExecutor._announce_count(7, True) == 7
    assert "[DEBUG] Ping count = 7" in capsys.readouterr().out


def test_announce_count_no_debug_silent(capsys) -> None:
    """Debug OFF: silent; returns count."""
    assert PingDeviceExecutor._announce_count(5, False) == 5
    assert capsys.readouterr().out == ""


# ---------- _prompt_ping_count ----------


def test_prompt_ping_count_wraps_parse_and_announce(capsys) -> None:
    """Wraps input + parse + announce."""
    deps = _make_deps(safe_input_returns=["3"])
    got = PingDeviceExecutor()._prompt_ping_count(deps, True)
    assert got == 3
    assert "[DEBUG] Ping count = 3" in capsys.readouterr().out


# ---------- _build_ping_request ----------


def test_build_ping_request_returns_url_and_headers() -> None:
    """URL + headers pair assembled correctly."""
    url, headers = PingDeviceExecutor._build_ping_request("api.example.com", "tok-x", "site-1", "dev-2")
    assert url == "https://api.example.com/api/v1/sites/site-1/devices/dev-2/ping"
    assert headers["Authorization"] == "Token tok-x"
    assert headers["Content-Type"] == "application/json"


# ---------- _print_result_banner ----------


def test_print_result_banner_prints_lines(capsys) -> None:
    """Header/underline/label printed."""
    PingDeviceExecutor._print_result_banner()
    out = capsys.readouterr().out
    assert "PING RESULTS:" in out
    assert "=" * 60 in out


# ---------- _render_output_sections ----------


def test_render_output_sections_raw_only(capsys) -> None:
    """Only raw block rendered when other is falsy."""
    PingDeviceExecutor._render_output_sections("raw-txt", "")
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out and "raw-txt" in out
    assert "OTHER OUTPUT:" not in out


def test_render_output_sections_other_only(capsys) -> None:
    """Only other block rendered when raw is falsy."""
    PingDeviceExecutor._render_output_sections("", "oth-txt")
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" not in out
    assert "OTHER OUTPUT:" in out and "oth-txt" in out


def test_render_output_sections_duplicate_suppressed(capsys) -> None:
    """Other equal to raw suppresses duplicate rendering."""
    PingDeviceExecutor._render_output_sections("same", "same")
    out = capsys.readouterr().out
    assert out.count("same") == 1
    assert "OTHER OUTPUT:" not in out


def test_render_output_sections_both_different(capsys) -> None:
    """Both blocks rendered when non-empty and differ."""
    PingDeviceExecutor._render_output_sections("aaa", "bbb")
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out and "aaa" in out
    assert "OTHER OUTPUT:" in out and "bbb" in out


def test_render_output_sections_both_empty(capsys) -> None:
    """Both empty → nothing printed."""
    PingDeviceExecutor._render_output_sections("", "")
    assert capsys.readouterr().out == ""


# ---------- _render_empty_result ----------


def test_render_empty_result_prints_keys(capsys) -> None:
    """Empty phrasing + available keys line printed."""
    PingDeviceExecutor._render_empty_result({"a": 1, "b": 2})
    out = capsys.readouterr().out
    assert "No output data received" in out
    assert "Available result keys:" in out


# ---------- _render_ping_result ----------


def test_render_ping_result_full(capsys) -> None:
    """Renders banner + raw/other + extras + closer."""
    payload = {"raw": "r", "Output": "o", "extra1": "v"}
    PingDeviceExecutor()._render_ping_result(payload, "1.1.1.1")
    out = capsys.readouterr().out
    assert "PING RESULTS:" in out
    assert "RAW OUTPUT:" in out
    assert "OTHER OUTPUT:" in out
    assert "extra1" in out


def test_render_ping_result_empty_output_shows_diagnostic(capsys) -> None:
    """No raw/no other → empty-result diagnostic block emitted."""
    PingDeviceExecutor()._render_ping_result({"session": "s"}, "1.1.1.1")
    out = capsys.readouterr().out
    assert "No output data received" in out


# ---------- _announce_wait ----------


def test_announce_wait_no_debug(capsys) -> None:
    """Debug OFF: legacy status lines only."""
    PingDeviceExecutor._announce_wait("abcdefghXYZ", False)
    out = capsys.readouterr().out
    assert "Ping command issued (session: abcdefgh...)" in out
    assert "Waiting for ping results..." in out
    assert "[DEBUG]" not in out


def test_announce_wait_debug(capsys) -> None:
    """Debug ON: adds full-session + starting-wait lines."""
    PingDeviceExecutor._announce_wait("abcdefghXYZ", True)
    out = capsys.readouterr().out
    assert "[DEBUG] Full session ID = abcdefghXYZ" in out
    assert "[DEBUG] Starting to wait for WebSocket results..." in out


# ---------- _echo_wait_outcome ----------


def test_echo_wait_outcome_none(capsys) -> None:
    """None result: prints returned=False only (no keys line)."""
    PingDeviceExecutor._echo_wait_outcome(None)
    out = capsys.readouterr().out
    assert "wait_for_command_result returned: False" in out
    assert "Result keys" not in out


def test_echo_wait_outcome_dict(capsys) -> None:
    """Dict result: prints returned=True + keys line."""
    PingDeviceExecutor._echo_wait_outcome({"a": 1})
    out = capsys.readouterr().out
    assert "wait_for_command_result returned: True" in out
    assert "Result keys: ['a']" in out


# ---------- _connect_ws ----------


def test_connect_ws_prints_banner_and_returns_manager(capsys) -> None:
    """Prints banner lines; returns WebSocketManager built from apisession."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps,
        site_id="site-1",
        device_id="dev-1",
        target_host="8.8.8.8",
        ping_count=4,
        debug_mode=False,
    )
    sentinel_mgr = MagicMock(name="WSMgr")
    with patch.object(ping_mod, "WebSocketManager", return_value=sentinel_mgr) as ctor:
        got = PingDeviceExecutor._connect_ws(req)
    assert got is sentinel_mgr
    ctor.assert_called_once_with(deps.apisession)
    out = capsys.readouterr().out
    assert "Executing ping to 8.8.8.8 on device dev-1" in out
    assert "Ping count: 4" in out
    assert "Establishing WebSocket connection..." in out


# ---------- _announce_post ----------


def test_announce_post_debug_echoes_payload(capsys) -> None:
    """Debug ON: prints status line + payload dict."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps,
        site_id="s",
        device_id="d",
        target_host="1.1.1.1",
        ping_count=2,
        debug_mode=True,
    )
    PingDeviceExecutor._announce_post(req)
    out = capsys.readouterr().out
    assert "-> Issuing ping command..." in out
    assert "[DEBUG] Ping payload = " in out
    assert "1.1.1.1" in out


def test_announce_post_no_debug_no_echo(capsys) -> None:
    """Debug OFF: status line only; no debug echo."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps,
        site_id="s",
        device_id="d",
        target_host="1.1.1.1",
        ping_count=2,
        debug_mode=False,
    )
    PingDeviceExecutor._announce_post(req)
    out = capsys.readouterr().out
    assert "-> Issuing ping command..." in out
    assert "[DEBUG]" not in out


# ---------- _post_ping_command ----------


def test_post_ping_command_credentials_none_returns_none() -> None:
    """prepare_command_credentials → None: helper returns None."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps, site_id="s", device_id="d", target_host="1.1.1.1", ping_count=1, debug_mode=False
    )
    ws = MagicMock()
    ctx = ping_mod._PostContext(request=req, websocket_manager=ws)
    with patch.object(ping_mod, "prepare_command_credentials", return_value=None):
        assert PingDeviceExecutor()._post_ping_command(ctx) is None


def test_post_ping_command_post_none_returns_none() -> None:
    """post_device_command returning None → returns None."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps, site_id="s", device_id="d", target_host="1.1.1.1", ping_count=1, debug_mode=False
    )
    ws = MagicMock()
    ctx = ping_mod._PostContext(request=req, websocket_manager=ws)
    with (
        patch.object(ping_mod, "prepare_command_credentials", return_value=("h", "t")),
        patch.object(ping_mod, "post_device_command", return_value=None),
    ):
        assert PingDeviceExecutor()._post_ping_command(ctx) is None


def test_post_ping_command_success_returns_session_id() -> None:
    """POST 200 → extract_command_session called with response and returns id."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps, site_id="s", device_id="d", target_host="1.1.1.1", ping_count=1, debug_mode=False
    )
    ws = MagicMock()
    ctx = ping_mod._PostContext(request=req, websocket_manager=ws)
    fake_resp = MagicMock()
    with (
        patch.object(ping_mod, "prepare_command_credentials", return_value=("h", "t")),
        patch.object(ping_mod, "post_device_command", return_value=fake_resp),
        patch.object(ping_mod, "extract_command_session", return_value="sess-1") as extract,
    ):
        assert PingDeviceExecutor()._post_ping_command(ctx) == "sess-1"
    extract.assert_called_once_with(fake_resp, ws, "ping")


# ---------- _await_and_render ----------


def test_await_and_render_success(capsys) -> None:
    """Result present → render_ping_result called; no timeout dump."""
    ws = MagicMock()
    ws.wait_for_command_result.return_value = {"raw": "pong"}
    with patch.object(ping_mod, "dump_ws_debug_state") as dumper:
        PingDeviceExecutor()._await_and_render(ws, "abcdefghXYZ", "1.1.1.1", False)
    out = capsys.readouterr().out
    assert "PING RESULTS:" in out
    dumper.assert_not_called()


def test_await_and_render_timeout(capsys) -> None:
    """No result → timeout phrase + dump_ws_debug_state called."""
    ws = MagicMock()
    ws.wait_for_command_result.return_value = None
    with patch.object(ping_mod, "dump_ws_debug_state") as dumper:
        PingDeviceExecutor()._await_and_render(ws, "abcdefghXYZ", "1.1.1.1", True)
    out = capsys.readouterr().out
    assert "! Timeout waiting for ping results" in out
    assert "wait_for_command_result returned: False" in out
    dumper.assert_called_once_with(ws, True)


# ---------- _issue_ping_and_render ----------


def test_issue_ping_and_render_connect_fail_returns_manager() -> None:
    """connect_and_subscribe False → returns manager for finally cleanup."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps, site_id="s", device_id="d", target_host="1.1.1.1", ping_count=1, debug_mode=False
    )
    mgr = MagicMock()
    mgr.connect_and_subscribe.return_value = False
    with patch.object(PingDeviceExecutor, "_connect_ws", return_value=mgr):
        got = PingDeviceExecutor()._issue_ping_and_render(req)
    assert got is mgr


def test_issue_ping_and_render_post_fail_returns_manager() -> None:
    """POST returns None session → returns manager without awaiting."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps, site_id="s", device_id="d", target_host="1.1.1.1", ping_count=1, debug_mode=False
    )
    mgr = MagicMock()
    mgr.connect_and_subscribe.return_value = True
    with (
        patch.object(PingDeviceExecutor, "_connect_ws", return_value=mgr),
        patch.object(PingDeviceExecutor, "_post_ping_command", return_value=None),
    ):
        got = PingDeviceExecutor()._issue_ping_and_render(req)
    assert got is mgr


def test_issue_ping_and_render_success_calls_await() -> None:
    """Session id present → _await_and_render invoked."""
    deps = _make_deps()
    req = ping_mod._PingRequest(
        deps=deps, site_id="s", device_id="d", target_host="1.1.1.1", ping_count=1, debug_mode=False
    )
    mgr = MagicMock()
    mgr.connect_and_subscribe.return_value = True
    with (
        patch.object(PingDeviceExecutor, "_connect_ws", return_value=mgr),
        patch.object(PingDeviceExecutor, "_post_ping_command", return_value="sess-1"),
        patch.object(PingDeviceExecutor, "_await_and_render") as awaiter,
    ):
        got = PingDeviceExecutor()._issue_ping_and_render(req)
    assert got is mgr
    awaiter.assert_called_once()


# ---------- _run_workflow ----------


def test_run_workflow_no_site() -> None:
    """select_ws_site None → returns None early."""
    deps = _make_deps()
    with patch.object(ping_mod, "select_ws_site", return_value=None):
        assert PingDeviceExecutor()._run_workflow(deps, False) is None


def test_run_workflow_no_device() -> None:
    """No device_id → returns None early."""
    deps = _make_deps(select_device_return=None)
    with patch.object(ping_mod, "select_ws_site", return_value="site-1"):
        assert PingDeviceExecutor()._run_workflow(deps, False) is None


def test_run_workflow_invalid_target() -> None:
    """Invalid target host → returns None early."""
    deps = _make_deps(safe_input_returns=["bad!"], validate_return=False)
    with patch.object(ping_mod, "select_ws_site", return_value="site-1"):
        assert PingDeviceExecutor()._run_workflow(deps, False) is None


def test_run_workflow_success_returns_manager() -> None:
    """Full workflow success → returns manager from _issue_ping_and_render."""
    deps = _make_deps(safe_input_returns=["1.1.1.1", "3"])
    sentinel_mgr = MagicMock()
    with (
        patch.object(ping_mod, "select_ws_site", return_value="site-1"),
        patch.object(PingDeviceExecutor, "_issue_ping_and_render", return_value=sentinel_mgr) as iss,
    ):
        got = PingDeviceExecutor()._run_workflow(deps, False)
    assert got is sentinel_mgr
    req = iss.call_args.args[0]
    assert req.site_id == "site-1"
    assert req.target_host == "1.1.1.1"
    assert req.ping_count == 3


# ---------- execute ----------


def test_execute_success_calls_cleanup(capsys) -> None:
    """execute() success path: cleanup called with manager."""
    deps = _make_deps()
    mgr = MagicMock()
    with (
        patch.object(PingDeviceExecutor, "_run_workflow", return_value=mgr),
        patch.object(ping_mod, "cleanup_ws_connection") as cleaner,
    ):
        PingDeviceExecutor().execute(deps)
    cleaner.assert_called_once()
    assert cleaner.call_args.args[0] is mgr


def test_execute_swallows_exception_and_cleans_up(capsys) -> None:
    """Broad exception path: log_ws_error called; cleanup still runs."""
    deps = _make_deps()
    with (
        patch.object(PingDeviceExecutor, "_run_workflow", side_effect=RuntimeError("boom")),
        patch.object(ping_mod, "log_ws_error") as err_log,
        patch.object(ping_mod, "cleanup_ws_connection") as cleaner,
    ):
        PingDeviceExecutor().execute(deps)
    err_log.assert_called_once()
    cleaner.assert_called_once()


def test_execute_debug_banner_emitted(capsys) -> None:
    """Debug mode → banner + level bump happen via _emit_debug_banner."""
    deps = _make_deps()
    with (
        patch.object(ping_mod, "detect_debug_mode", return_value=True),
        patch.object(PingDeviceExecutor, "_run_workflow", return_value=None),
        patch.object(ping_mod, "cleanup_ws_connection"),
    ):
        PingDeviceExecutor().execute(deps)
    assert "[DEBUG] DEBUG MODE ENABLED" in capsys.readouterr().out
