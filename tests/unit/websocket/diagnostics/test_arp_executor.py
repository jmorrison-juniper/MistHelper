"""Unit tests for the ArpDeviceExecutor.

Covers src/websocket/diagnostics/arp_executor.py. The executor orchestrates the
interactive ARP-over-WebSocket workflow: site + device prompts, compat gating,
WebSocket connect + subscribe, HTTP POST of the ARP command, session-id demux,
and result rendering (raw echo, gateway JSON table, empty-result diagnostics,
and timeouts).

These tests pin every branch — including the debug-print and error-swallow
paths — so future refactors of the executor cannot silently change the
observable operator contract.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from src.websocket.diagnostics import arp_executor as arp_mod
from src.websocket.diagnostics.arp_executor import ArpDeviceExecutor


def _make_deps(
    *,
    select_site_return: Any = "site-1",
    select_device_return: Any = "dev-1",
    list_devices_return: Any = None,
    list_devices_raises: BaseException | None = None,
    safe_input_return: str = "y",
) -> SimpleNamespace:
    """Build a WebSocketCmdDeps-shaped stub for the executor under test."""
    apisession = MagicMock(name="apisession")
    select_site_fn = MagicMock(return_value=select_site_return)
    select_device_fn = MagicMock(return_value=select_device_return)
    if list_devices_raises is not None:
        list_devices_fn = MagicMock(side_effect=list_devices_raises)
    else:
        payload = SimpleNamespace(data=list_devices_return or [])
        list_devices_fn = MagicMock(return_value=payload)
    safe_input_fn = MagicMock(return_value=safe_input_return)
    return SimpleNamespace(
        apisession=apisession,
        select_site_fn=select_site_fn,
        select_device_fn=select_device_fn,
        validate_target_fn=MagicMock(),
        list_devices_fn=list_devices_fn,
        safe_input_fn=safe_input_fn,
    )


# ---------- _compute_timeout ----------


def test_compute_timeout_no_device_info_returns_default() -> None:
    """No device_info → default 30s timeout, nothing printed."""
    assert ArpDeviceExecutor._compute_timeout(None) == arp_mod._TIMEOUT_DEFAULT


def test_compute_timeout_switch_returns_45_and_prints(capsys) -> None:
    """type=switch → 45s and the legacy notice line."""
    got = ArpDeviceExecutor._compute_timeout({"type": "switch"})
    assert got == arp_mod._TIMEOUT_SWITCH
    assert "extended timeout for switch" in capsys.readouterr().out


def test_compute_timeout_gateway_returns_35_and_prints(capsys) -> None:
    """type=gateway → 35s and the legacy notice line."""
    got = ArpDeviceExecutor._compute_timeout({"type": "gateway"})
    assert got == arp_mod._TIMEOUT_GATEWAY
    assert "extended timeout for gateway" in capsys.readouterr().out


def test_compute_timeout_unknown_type_returns_default(capsys) -> None:
    """Unknown type → default timeout, no notice printed."""
    got = ArpDeviceExecutor._compute_timeout({"type": "ap"})
    assert got == arp_mod._TIMEOUT_DEFAULT
    assert capsys.readouterr().out == ""


def test_compute_timeout_missing_type_returns_default(capsys) -> None:
    """No 'type' key → default timeout, no notice printed."""
    got = ArpDeviceExecutor._compute_timeout({})
    assert got == arp_mod._TIMEOUT_DEFAULT
    assert capsys.readouterr().out == ""


# ---------- _build_arp_request ----------


def test_build_arp_request_returns_url_and_headers() -> None:
    """Assembles the device-scoped ARP URL and standard token headers."""
    url, headers = ArpDeviceExecutor._build_arp_request("host.example", "tok-xyz", "site-1", "dev-1")
    assert url == "https://host.example/api/v1/sites/site-1/devices/dev-1/arp"
    assert headers == {
        "Authorization": "Token tok-xyz",
        "Content-Type": "application/json",
    }


# ---------- _format_device_context ----------


def test_format_device_context_no_info_uses_device_id() -> None:
    """No device_info → 'device <id>' fallback string."""
    assert ArpDeviceExecutor._format_device_context(None, "d123") == "device d123"


def test_format_device_context_with_info_uses_type_and_name() -> None:
    """With device_info → '<type> <name>' payload."""
    got = ArpDeviceExecutor._format_device_context({"type": "gateway", "name": "n1"}, "d123")
    assert got == "gateway n1"


def test_format_device_context_with_partial_info_falls_back_to_id_prefix() -> None:
    """Missing name uses the first 8 chars of the device id."""
    got = ArpDeviceExecutor._format_device_context({"type": "ap"}, "abcdefghij")
    assert got == "ap abcdefgh"


# ---------- _print_result_banner ----------


def test_print_result_banner_emits_header_block(capsys) -> None:
    """Emits the legacy '=' * 60 header block above ARP output."""
    ArpDeviceExecutor._print_result_banner()
    out = capsys.readouterr().out
    assert "ARP TABLE RESULTS:" in out
    assert "=" * 60 in out


# ---------- _announce_wait ----------


def test_announce_wait_debug_off_prints_banner_only(capsys) -> None:
    """debug_mode=False prints only the two legacy banners."""
    ArpDeviceExecutor._announce_wait("sessionidlong", False)
    out = capsys.readouterr().out
    assert "ARP command issued (session: sessioni...)" in out
    assert "Waiting for ARP results..." in out
    assert "[DEBUG]" not in out


def test_announce_wait_debug_on_prints_extra_debug_lines(capsys) -> None:
    """debug_mode=True adds the two extra [DEBUG] lines."""
    ArpDeviceExecutor._announce_wait("full-session-id", True)
    out = capsys.readouterr().out
    assert "[DEBUG] Full session ID = full-session-id" in out
    assert "[DEBUG] Starting to wait for WebSocket results..." in out


# ---------- _echo_wait_outcome ----------


def test_echo_wait_outcome_none_prints_only_status(capsys) -> None:
    """None result → single '[DEBUG] wait_for_command_result returned: False' line."""
    ArpDeviceExecutor._echo_wait_outcome(None)
    out = capsys.readouterr().out
    assert "returned: False" in out
    assert "Result keys" not in out


def test_echo_wait_outcome_dict_echoes_keys(capsys) -> None:
    """Dict result → adds the '[DEBUG] Result keys: [...]' line."""
    ArpDeviceExecutor._echo_wait_outcome({"raw": "x", "Output": "y"})
    out = capsys.readouterr().out
    assert "returned: True" in out
    assert "Result keys" in out
    assert "raw" in out and "Output" in out


# ---------- _echo_device_attributes ----------


def test_echo_device_attributes_prints_type_model_name(capsys) -> None:
    """Prints a single '[DEBUG] Device type/model/name' line verbatim."""
    ArpDeviceExecutor._echo_device_attributes({"type": "gateway", "model": "SRX", "name": "gw1"}, "dev-123")
    out = capsys.readouterr().out
    assert "type: gateway" in out and "model: SRX" in out and "name: gw1" in out


def test_echo_device_attributes_uses_id_prefix_when_name_missing(capsys) -> None:
    """Missing name → falls back to 'Device <first-8-of-id>'."""
    ArpDeviceExecutor._echo_device_attributes({}, "abcdefghij")
    assert "Device abcdefgh" in capsys.readouterr().out


# ---------- _echo_raw_fallback / _echo_debug_json ----------


def test_echo_raw_fallback_prints_header_and_raw(capsys) -> None:
    """Legacy 'RAW OUTPUT:' fallback block with underline and content."""
    ArpDeviceExecutor._echo_raw_fallback("some-raw")
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out and "-" * 40 in out and "some-raw" in out


def test_echo_debug_json_prints_debug_header_and_raw(capsys) -> None:
    """Legacy '[Debug]' JSON echo block."""
    ArpDeviceExecutor._echo_debug_json("json-data")
    out = capsys.readouterr().out
    assert "RAW JSON OUTPUT (Debug)" in out and "json-data" in out


# ---------- _maybe_render_parsed ----------


def test_maybe_render_parsed_empty_parsed_is_noop(capsys) -> None:
    """Empty parsed_output prints nothing."""
    ArpDeviceExecutor._maybe_render_parsed("raw", "")
    assert capsys.readouterr().out == ""


def test_maybe_render_parsed_equal_to_raw_is_noop(capsys) -> None:
    """parsed_output equal to raw_output prints nothing."""
    ArpDeviceExecutor._maybe_render_parsed("same", "same")
    assert capsys.readouterr().out == ""


def test_maybe_render_parsed_different_prints_block(capsys) -> None:
    """Different parsed_output emits the PARSED OUTPUT section."""
    ArpDeviceExecutor._maybe_render_parsed("raw", "parsed-different")
    out = capsys.readouterr().out
    assert "PARSED OUTPUT:" in out and "parsed-different" in out


# ---------- _render_empty_result ----------


def test_render_empty_result_no_device_info_only_prints_no_output(capsys) -> None:
    """No device_info → only the legacy 'No output data received' line."""
    ArpDeviceExecutor._render_empty_result(None)
    out = capsys.readouterr().out
    assert "No output data received" in out
    assert "Troubleshooting" not in out


def test_render_empty_result_switch_prints_switch_tips(capsys) -> None:
    """type=switch → adds the switch-only troubleshooting tips block."""
    ArpDeviceExecutor._render_empty_result({"type": "switch"})
    out = capsys.readouterr().out
    assert "Troubleshooting for switches" in out
    assert "SSH-based commands" in out


def test_render_empty_result_non_switch_omits_tips(capsys) -> None:
    """Non-switch device_info → no troubleshooting tips."""
    ArpDeviceExecutor._render_empty_result({"type": "gateway"})
    out = capsys.readouterr().out
    assert "No output data received" in out
    assert "Troubleshooting" not in out


# ---------- _render_device_context ----------


def test_render_device_context_none_is_noop(capsys) -> None:
    """No device_info → nothing printed."""
    ArpDeviceExecutor._render_device_context(None)
    assert capsys.readouterr().out == ""


def test_render_device_context_switch_prints_note(capsys) -> None:
    """type=switch → 'Device: ... (SWITCH: ...)' header + note line."""
    ArpDeviceExecutor._render_device_context({"type": "switch", "model": "EX", "name": "sw1"})
    out = capsys.readouterr().out
    assert "Device: sw1 (SWITCH: EX)" in out
    assert "forwarding table" in out


def test_render_device_context_gateway_prints_note(capsys) -> None:
    """type=gateway emits its per-type note."""
    ArpDeviceExecutor._render_device_context({"type": "gateway", "model": "SRX", "name": "gw1"})
    out = capsys.readouterr().out
    assert "Device: gw1 (GATEWAY: SRX)" in out
    assert "routing information" in out


def test_render_device_context_ap_prints_note(capsys) -> None:
    """type=ap emits its per-type note."""
    ArpDeviceExecutor._render_device_context({"type": "ap", "model": "AP43", "name": "ap1"})
    out = capsys.readouterr().out
    assert "Device: ap1 (AP: AP43)" in out
    assert "client connectivity" in out


def test_render_device_context_unknown_type_omits_note(capsys) -> None:
    """Unknown type → header prints but no per-type note."""
    ArpDeviceExecutor._render_device_context({"type": "other", "model": "X", "name": "d1"})
    out = capsys.readouterr().out
    assert "Device: d1 (OTHER: X)" in out
    assert "Note:" not in out


# ---------- _render_timeout_help ----------


def test_render_timeout_help_switch_prints_switch_block(capsys) -> None:
    """type=switch prints the four legacy switch troubleshooting lines."""
    ArpDeviceExecutor._render_timeout_help({"type": "switch", "model": "EX"})
    out = capsys.readouterr().out
    assert "Switch troubleshooting (EX)" in out
    assert "SSH-based 'show arp'" in out


def test_render_timeout_help_gateway_prints_gateway_block(capsys) -> None:
    """type=gateway prints the gateway troubleshooting lines."""
    ArpDeviceExecutor._render_timeout_help({"type": "gateway", "model": "SRX"})
    out = capsys.readouterr().out
    assert "Gateway troubleshooting (SRX)" in out
    assert "different ARP command format" in out


def test_render_timeout_help_unknown_falls_to_general(capsys) -> None:
    """Unknown type falls back to the general troubleshooting block."""
    ArpDeviceExecutor._render_timeout_help({"type": "ap", "model": "AP43"})
    out = capsys.readouterr().out
    assert "General troubleshooting (ap)" in out
    assert "WebSocket support" in out


# ---------- _render_timeout ----------


def test_render_timeout_no_info_prints_only_headline(capsys, caplog) -> None:
    """No device_info → only the top headline + warning log; no per-type help."""
    with caplog.at_level(logging.WARNING):
        ArpDeviceExecutor()._render_timeout(None)
    out = capsys.readouterr().out
    assert "Timeout waiting for ARP results" in out
    assert "troubleshooting" not in out.lower()
    assert any("ARP operation timed out" in rec.message for rec in caplog.records)


def test_render_timeout_with_info_prints_help_block(capsys) -> None:
    """device_info present → per-type troubleshooting block also emitted."""
    ArpDeviceExecutor()._render_timeout({"type": "gateway", "model": "SRX"})
    out = capsys.readouterr().out
    assert "Timeout waiting for ARP results" in out
    assert "Gateway troubleshooting" in out


# ---------- _compute_column_widths ----------


def test_compute_column_widths_uses_max_of_header_and_cells() -> None:
    """Widths are max(header, cell) + 2, capped at 20."""
    columns = [{"id": "c1"}, {"id": "c2"}]
    headers = ["H1", "colwithlongheader"]
    rows = [{"c1": "1234567890", "c2": "x"}]
    widths = ArpDeviceExecutor._compute_column_widths(columns, headers, rows)
    # c1: max(len('H1'), len('1234567890')) + 2 = 12; c2: max(len(header), len('x')) + 2 = 19
    assert widths == [12, 19]


def test_compute_column_widths_caps_at_max() -> None:
    """A very wide cell is clamped to 20 (the _MAX_COLUMN_WIDTH cap)."""
    columns = [{"id": "c1"}]
    headers = ["H1"]
    rows = [{"c1": "x" * 100}]
    widths = ArpDeviceExecutor._compute_column_widths(columns, headers, rows)
    assert widths == [arp_mod._MAX_COLUMN_WIDTH]


# ---------- _print_table_header / _print_table_rows ----------


def test_print_table_header_emits_header_and_underline(capsys) -> None:
    """Header prints padded names joined by ' | ' with matching underline."""
    ArpDeviceExecutor._print_table_header(["A", "BB"], [4, 4])
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "A    | BB  "
    assert lines[1] == "-" * len(lines[0])


def test_print_table_rows_prints_padded_and_truncates_overlong(capsys) -> None:
    """Long cell values are truncated with '...' to fit the width."""
    columns = [{"id": "c1"}, {"id": "c2"}]
    rows = [{"c1": "short", "c2": "verylongvalue"}]
    widths = [10, 8]  # c2 width=8 → truncated to width-5=3 chars + '...' = 'ver...'
    ArpDeviceExecutor._print_table_rows(columns, rows, widths)
    out = capsys.readouterr().out
    assert "short" in out
    assert "ver..." in out


def test_print_table_rows_missing_column_uses_empty_string(capsys) -> None:
    """A row missing a column key renders as an empty padded cell."""
    columns = [{"id": "c1"}]
    rows = [{}]
    widths = [4]
    ArpDeviceExecutor._print_table_rows(columns, rows, widths)
    out = capsys.readouterr().out
    assert out.strip("\n") == "    "  # 4 spaces


# ---------- _render_gateway_arp_table ----------


def test_render_gateway_arp_table_no_columns_falls_back(capsys) -> None:
    """No columns → falls back to 'No column information' + raw echo."""
    ArpDeviceExecutor()._render_gateway_arp_table({"columns": [], "rows": []}, "raw-data", False)
    out = capsys.readouterr().out
    assert "No column information available" in out
    assert "RAW OUTPUT:" in out and "raw-data" in out


def test_render_gateway_arp_table_debug_on_echoes_json(capsys) -> None:
    """debug_mode=True adds the '[Debug]' JSON echo block after the table."""
    gd = {
        "columns": [{"id": "ip", "display_name": "IP"}],
        "rows": [{"ip": "10.0.0.1"}],
    }
    ArpDeviceExecutor()._render_gateway_arp_table(gd, "raw-data", True)
    out = capsys.readouterr().out
    assert "PARSED ARP TABLE:" in out
    assert "Total ARP Entries: 1" in out
    assert "RAW JSON OUTPUT (Debug)" in out


def test_render_gateway_arp_table_uses_id_when_no_display_name(capsys) -> None:
    """Columns without display_name fall back to the id."""
    gd = {"columns": [{"id": "mac"}], "rows": [{"mac": "aa:bb"}]}
    ArpDeviceExecutor()._render_gateway_arp_table(gd, "r", False)
    out = capsys.readouterr().out
    assert "mac" in out and "aa:bb" in out


def test_render_gateway_arp_table_missing_display_and_id_uses_unknown(capsys) -> None:
    """Columns with neither display_name nor id fall back to 'Unknown'."""
    gd = {"columns": [{}], "rows": []}
    ArpDeviceExecutor()._render_gateway_arp_table(gd, "r", False)
    out = capsys.readouterr().out
    assert "Unknown" in out


# ---------- _fallback_gateway_output ----------


def test_fallback_gateway_output_debug_off_no_debug_line(capsys) -> None:
    """debug_mode=False omits the '[DEBUG] Failed to parse' line."""
    err = json.JSONDecodeError("boom", "doc", 0)
    ArpDeviceExecutor()._fallback_gateway_output("raw", False, err)
    out = capsys.readouterr().out
    assert "Failed to parse gateway JSON output" in out
    assert "RAW OUTPUT:" in out
    assert "[DEBUG]" not in out


def test_fallback_gateway_output_debug_on_prints_debug_line(capsys) -> None:
    """debug_mode=True adds the '[DEBUG] Failed to parse gateway JSON: ...' line."""
    err = json.JSONDecodeError("boom", "doc", 0)
    ArpDeviceExecutor()._fallback_gateway_output("raw", True, err)
    out = capsys.readouterr().out
    assert "[DEBUG] Failed to parse gateway JSON" in out


# ---------- _render_gateway_table_or_fallback ----------


def test_render_gateway_table_or_fallback_bad_json_falls_back(capsys) -> None:
    """Non-JSON raw output triggers the JSON-parse-failure fallback path."""
    ArpDeviceExecutor()._render_gateway_table_or_fallback("not-json", False)
    out = capsys.readouterr().out
    assert "Failed to parse gateway JSON output" in out


def test_render_gateway_table_or_fallback_missing_status_falls_back(capsys) -> None:
    """JSON without status=SUCCESS → 'Gateway response format not recognized' + raw echo."""
    payload = json.dumps({"status": "FAIL", "rows": []})
    ArpDeviceExecutor()._render_gateway_table_or_fallback(payload, False)
    out = capsys.readouterr().out
    assert "Gateway response format not recognized" in out
    assert "RAW OUTPUT:" in out


def test_render_gateway_table_or_fallback_missing_rows_falls_back(capsys) -> None:
    """SUCCESS status but no 'rows' key → format-not-recognized fallback."""
    payload = json.dumps({"status": "SUCCESS", "no_rows_here": True})
    ArpDeviceExecutor()._render_gateway_table_or_fallback(payload, False)
    assert "Gateway response format not recognized" in capsys.readouterr().out


def test_render_gateway_table_or_fallback_success_renders_table(capsys) -> None:
    """SUCCESS with rows → PARSED ARP TABLE renderer runs."""
    payload = json.dumps(
        {
            "status": "SUCCESS",
            "columns": [{"id": "ip", "display_name": "IP"}],
            "rows": [{"ip": "10.0.0.1"}],
        }
    )
    ArpDeviceExecutor()._render_gateway_table_or_fallback(payload, False)
    out = capsys.readouterr().out
    assert "PARSED ARP TABLE:" in out and "10.0.0.1" in out


# ---------- _render_raw_output_block ----------


def test_render_raw_output_block_non_gateway_prints_raw(capsys) -> None:
    """Non-gateway → 'RAW OUTPUT:' block, no JSON parsing attempted."""
    ArpDeviceExecutor()._render_raw_output_block("plain-text", {"type": "ap"}, False)
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out and "plain-text" in out


def test_render_raw_output_block_no_device_info_prints_raw(capsys) -> None:
    """No device_info → 'RAW OUTPUT:' block, no JSON parsing attempted."""
    ArpDeviceExecutor()._render_raw_output_block("plain", None, False)
    assert "RAW OUTPUT:" in capsys.readouterr().out


def test_render_raw_output_block_gateway_non_json_prints_raw(capsys) -> None:
    """Gateway but raw doesn't start with '{' → 'RAW OUTPUT:' block."""
    ArpDeviceExecutor()._render_raw_output_block("plain", {"type": "gateway"}, False)
    assert "RAW OUTPUT:" in capsys.readouterr().out


def test_render_raw_output_block_gateway_json_dispatches_to_table(capsys) -> None:
    """Gateway + JSON-looking raw → dispatch to gateway table renderer."""
    payload = json.dumps({"status": "SUCCESS", "columns": [{"id": "ip"}], "rows": [{"ip": "1.1.1.1"}]})
    ArpDeviceExecutor()._render_raw_output_block(payload, {"type": "gateway"}, False)
    out = capsys.readouterr().out
    assert "PARSED ARP TABLE:" in out


# ---------- _render_output_sections ----------


def test_render_output_sections_empty_delegates_to_empty(capsys) -> None:
    """Both raw + parsed empty → _render_empty_result path."""
    ArpDeviceExecutor()._render_output_sections("", "", None, False)
    assert "No output data received" in capsys.readouterr().out


def test_render_output_sections_raw_only_prints_raw(capsys) -> None:
    """Only raw output present → 'RAW OUTPUT:' section, no PARSED block."""
    ArpDeviceExecutor()._render_output_sections("raw-x", "", {"type": "ap"}, False)
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out
    assert "PARSED OUTPUT:" not in out


def test_render_output_sections_raw_and_different_parsed_prints_both(capsys) -> None:
    """Raw + parsed differ → both sections emitted."""
    ArpDeviceExecutor()._render_output_sections("raw-x", "parsed-y", {"type": "ap"}, False)
    out = capsys.readouterr().out
    assert "RAW OUTPUT:" in out and "PARSED OUTPUT:" in out


def test_render_output_sections_parsed_only_prints_parsed(capsys) -> None:
    """Only parsed output present → PARSED section rendered (raw block skipped)."""
    ArpDeviceExecutor()._render_output_sections("", "parsed-y", None, False)
    out = capsys.readouterr().out
    assert "PARSED OUTPUT:" in out


# ---------- _render_arp_result ----------


def test_render_arp_result_prints_banner_and_context_and_body(capsys, caplog) -> None:
    """Composes banner + device-context + raw body + closer + log line."""
    with caplog.at_level(logging.INFO):
        ArpDeviceExecutor()._render_arp_result(
            {"raw": "raw-data", "Output": ""},
            {"type": "ap", "model": "AP43", "name": "ap1"},
            "dev-id",
            False,
        )
    out = capsys.readouterr().out
    assert "ARP TABLE RESULTS:" in out
    assert "Device: ap1" in out
    assert "RAW OUTPUT:" in out
    assert any("WebSocket ARP completed successfully" in r.message for r in caplog.records)


# ---------- _connect_ws ----------


def test_connect_ws_success_returns_manager(capsys) -> None:
    """connect_and_subscribe True → returns the built WebSocketManager."""
    deps = _make_deps()
    fake_ws = MagicMock()
    fake_ws.connect_and_subscribe.return_value = True
    with patch.object(arp_mod, "WebSocketManager", return_value=fake_ws) as ctor:
        got = ArpDeviceExecutor._connect_ws(deps, "site-1", "dev-1", True)
    ctor.assert_called_once_with(deps.apisession)
    fake_ws.connect_and_subscribe.assert_called_once_with("site-1", "dev-1", True)
    assert got is fake_ws
    out = capsys.readouterr().out
    assert "Executing ARP command on device dev-1" in out


def test_connect_ws_failure_still_returns_manager_for_cleanup(capsys) -> None:
    """connect_and_subscribe False → still returns the manager for finally cleanup."""
    deps = _make_deps()
    fake_ws = MagicMock()
    fake_ws.connect_and_subscribe.return_value = False
    with patch.object(arp_mod, "WebSocketManager", return_value=fake_ws):
        got = ArpDeviceExecutor._connect_ws(deps, "site-1", "dev-1", False)
    assert got is fake_ws


# ---------- _post_arp_command ----------


def test_post_arp_command_credentials_none_returns_none() -> None:
    """prepare_command_credentials returning None → helper returns None."""
    deps = _make_deps()
    ws = MagicMock()
    with patch.object(arp_mod, "prepare_command_credentials", return_value=None):
        assert ArpDeviceExecutor()._post_arp_command(deps, ws, "s", "d", False) is None


def test_post_arp_command_post_returns_none_returns_none() -> None:
    """post_device_command returning None → helper returns None (defensive path)."""
    deps = _make_deps()
    ws = MagicMock()
    with (
        patch.object(arp_mod, "prepare_command_credentials", return_value=("h", "t")),
        patch.object(arp_mod, "post_device_command", return_value=None),
    ):
        assert ArpDeviceExecutor()._post_arp_command(deps, ws, "s", "d", False) is None


def test_post_arp_command_success_returns_session_id() -> None:
    """Happy path returns the extracted session id."""
    deps = _make_deps()
    ws = MagicMock()
    fake_resp = MagicMock()
    with (
        patch.object(arp_mod, "prepare_command_credentials", return_value=("h", "t")),
        patch.object(arp_mod, "post_device_command", return_value=fake_resp) as post,
        patch.object(arp_mod, "extract_command_session", return_value="sess-1") as demux,
    ):
        got = ArpDeviceExecutor()._post_arp_command(deps, ws, "s", "d", False)
    assert got == "sess-1"
    post.assert_called_once()
    demux.assert_called_once_with(fake_resp, ws, "ARP")


# ---------- _await_and_render ----------


def test_await_and_render_success_dispatches_to_render_arp_result() -> None:
    """A truthy wait result routes to _render_arp_result."""
    ws = MagicMock()
    ws.wait_for_command_result.return_value = {"raw": "x", "Output": ""}
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(exec_obj, "_render_arp_result") as render_ok,
        patch.object(exec_obj, "_render_timeout") as render_to,
    ):
        exec_obj._await_and_render(ws, "session-1", None, "dev-1", False)
    render_ok.assert_called_once()
    render_to.assert_not_called()


def test_await_and_render_timeout_dispatches_to_render_timeout() -> None:
    """A None wait result routes to _render_timeout."""
    ws = MagicMock()
    ws.wait_for_command_result.return_value = None
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(exec_obj, "_render_arp_result") as render_ok,
        patch.object(exec_obj, "_render_timeout") as render_to,
    ):
        exec_obj._await_and_render(ws, "session-1", None, "dev-1", False)
    render_ok.assert_not_called()
    render_to.assert_called_once()


def test_await_and_render_debug_on_emits_wait_outcome(capsys) -> None:
    """debug_mode=True triggers the _echo_wait_outcome debug lines."""
    ws = MagicMock()
    ws.wait_for_command_result.return_value = None
    ArpDeviceExecutor()._await_and_render(ws, "session-1", None, "dev-1", True)
    out = capsys.readouterr().out
    assert "wait_for_command_result returned" in out


# ---------- _confirm_switch_arp ----------


def test_confirm_switch_arp_yes_returns_true(capsys) -> None:
    """User answers 'y' → returns True + no cancel line."""
    deps = _make_deps(safe_input_return="y")
    assert ArpDeviceExecutor._confirm_switch_arp(deps, "EX") is True
    assert "Operation cancelled" not in capsys.readouterr().out


def test_confirm_switch_arp_yes_uppercase_returns_true() -> None:
    """User answers 'YES' → returns True (case-insensitive)."""
    deps = _make_deps(safe_input_return="YES")
    assert ArpDeviceExecutor._confirm_switch_arp(deps, "EX") is True


def test_confirm_switch_arp_no_returns_false(capsys) -> None:
    """Any non-yes answer → False + 'Operation cancelled' line."""
    deps = _make_deps(safe_input_return="n")
    assert ArpDeviceExecutor._confirm_switch_arp(deps, "EX") is False
    assert "Operation cancelled" in capsys.readouterr().out


# ---------- _maybe_warn_and_confirm ----------


def test_maybe_warn_and_confirm_no_info_returns_true() -> None:
    """No device_info → returns True (proceed) unconditionally."""
    deps = _make_deps()
    assert ArpDeviceExecutor()._maybe_warn_and_confirm(deps, None) is True


def test_maybe_warn_and_confirm_switch_delegates_to_confirm(capsys) -> None:
    """Switch → delegates to _confirm_switch_arp; returns its bool."""
    deps = _make_deps(safe_input_return="n")
    result = ArpDeviceExecutor()._maybe_warn_and_confirm(deps, {"type": "switch", "model": "EX"})
    assert result is False


def test_maybe_warn_and_confirm_gateway_prints_note_returns_true(capsys) -> None:
    """Gateway → prints compat note, returns True."""
    deps = _make_deps()
    result = ArpDeviceExecutor()._maybe_warn_and_confirm(deps, {"type": "gateway", "model": "SRX"})
    assert result is True
    out = capsys.readouterr().out
    assert "Gateway detected" in out and "SRX" in out


def test_maybe_warn_and_confirm_ap_prints_note_returns_true(capsys) -> None:
    """AP → prints AP compat note, returns True."""
    deps = _make_deps()
    result = ArpDeviceExecutor()._maybe_warn_and_confirm(deps, {"type": "ap", "model": "AP43"})
    assert result is True
    out = capsys.readouterr().out
    assert "Access Point detected" in out and "AP43" in out


def test_maybe_warn_and_confirm_unknown_prints_generic_and_returns_true(capsys) -> None:
    """Unknown type → prints generic warning, returns True."""
    deps = _make_deps()
    result = ArpDeviceExecutor()._maybe_warn_and_confirm(deps, {"type": "weird", "model": "X"})
    assert result is True
    out = capsys.readouterr().out
    assert "Unknown device type" in out


# ---------- _lookup_device_record ----------


def test_lookup_device_record_returns_matching_entry() -> None:
    """Walks the returned list and returns the matching id entry."""
    deps = _make_deps(
        list_devices_return=[
            {"id": "other", "name": "other"},
            {"id": "dev-1", "name": "target"},
        ]
    )
    got = ArpDeviceExecutor._lookup_device_record(deps, "s", "dev-1", False)
    assert got == {"id": "dev-1", "name": "target"}


def test_lookup_device_record_no_match_returns_none() -> None:
    """No matching id in list → returns None (via next default)."""
    deps = _make_deps(list_devices_return=[{"id": "other"}])
    got = ArpDeviceExecutor._lookup_device_record(deps, "s", "missing", False)
    assert got is None


def test_lookup_device_record_exception_logs_and_returns_none(capsys, caplog) -> None:
    """API failure → warning log + legacy 'Proceeding with standard' line + None."""
    deps = _make_deps(list_devices_raises=RuntimeError("kaboom"))
    with caplog.at_level(logging.WARNING):
        got = ArpDeviceExecutor._lookup_device_record(deps, "s", "d", False)
    assert got is None
    out = capsys.readouterr().out
    assert "Proceeding with standard ARP command" in out
    assert any("Could not verify device compatibility" in r.message for r in caplog.records)


def test_lookup_device_record_exception_debug_on_prints_debug_line(capsys) -> None:
    """API failure + debug_mode=True → prints the '[DEBUG] Device check failed' line."""
    deps = _make_deps(list_devices_raises=RuntimeError("kaboom"))
    ArpDeviceExecutor._lookup_device_record(deps, "s", "d", True)
    out = capsys.readouterr().out
    assert "[DEBUG] Device check failed" in out


# ---------- _fetch_device_info ----------


def test_fetch_device_info_success_returns_record() -> None:
    """Successful lookup returns the resolved device_info dict."""
    deps = _make_deps(list_devices_return=[{"id": "d", "type": "ap"}])
    got = ArpDeviceExecutor()._fetch_device_info(deps, "s", "d", False)
    assert got == {"id": "d", "type": "ap"}


def test_fetch_device_info_debug_on_echoes_attributes(capsys) -> None:
    """debug_mode=True + present record → echoes the [DEBUG] attributes line."""
    deps = _make_deps(list_devices_return=[{"id": "d", "type": "ap", "model": "AP43", "name": "n"}])
    ArpDeviceExecutor()._fetch_device_info(deps, "s", "d", True)
    out = capsys.readouterr().out
    assert "[DEBUG] Device type: ap" in out


def test_fetch_device_info_absent_debug_on_no_echo(capsys) -> None:
    """debug_mode=True but record missing → no attributes echo line."""
    deps = _make_deps(list_devices_return=[])
    got = ArpDeviceExecutor()._fetch_device_info(deps, "s", "d", True)
    assert got is None
    out = capsys.readouterr().out
    assert "[DEBUG] Device type" not in out


# ---------- _run_workflow ----------


def test_run_workflow_no_site_returns_none() -> None:
    """select_ws_site returning None → workflow exits with None."""
    deps = _make_deps()
    with patch.object(arp_mod, "select_ws_site", return_value=None):
        assert ArpDeviceExecutor()._run_workflow(deps, False) is None


def test_run_workflow_no_device_returns_none(capsys) -> None:
    """No device selected → 'No device selected' line + None."""
    deps = _make_deps(select_device_return=None)
    with patch.object(arp_mod, "select_ws_site", return_value="site-1"):
        got = ArpDeviceExecutor()._run_workflow(deps, False)
    assert got is None
    assert "No device selected" in capsys.readouterr().out


def test_run_workflow_debug_prints_device_id(capsys) -> None:
    """debug_mode=True → '[DEBUG] Selected device_id = ...' echo."""
    deps = _make_deps()
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(arp_mod, "select_ws_site", return_value="site-1"),
        patch.object(exec_obj, "_fetch_device_info", return_value=None),
        patch.object(exec_obj, "_maybe_warn_and_confirm", return_value=False),
    ):
        exec_obj._run_workflow(deps, True)
    out = capsys.readouterr().out
    assert "[DEBUG] Selected device_id = dev-1" in out


def test_run_workflow_declined_returns_none() -> None:
    """_maybe_warn_and_confirm False → workflow returns None (skip)."""
    deps = _make_deps()
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(arp_mod, "select_ws_site", return_value="site-1"),
        patch.object(exec_obj, "_fetch_device_info", return_value=None),
        patch.object(exec_obj, "_maybe_warn_and_confirm", return_value=False),
    ):
        assert exec_obj._run_workflow(deps, False) is None


def test_run_workflow_success_delegates_to_issue_and_render() -> None:
    """Confirmed path calls _issue_arp_and_render and returns its ws manager."""
    deps = _make_deps()
    exec_obj = ArpDeviceExecutor()
    ws = MagicMock()
    with (
        patch.object(arp_mod, "select_ws_site", return_value="site-1"),
        patch.object(exec_obj, "_fetch_device_info", return_value={"type": "ap"}),
        patch.object(exec_obj, "_maybe_warn_and_confirm", return_value=True),
        patch.object(exec_obj, "_issue_arp_and_render", return_value=ws) as issue,
    ):
        got = exec_obj._run_workflow(deps, False)
    assert got is ws
    issue.assert_called_once()


# ---------- _issue_arp_and_render ----------


def test_issue_arp_and_render_connect_fail_returns_none() -> None:
    """_connect_ws returning None → returns None with no cleanup manager."""
    deps = _make_deps()
    exec_obj = ArpDeviceExecutor()
    with patch.object(exec_obj, "_connect_ws", return_value=None):
        assert exec_obj._issue_arp_and_render(deps, "s", "d", None, False) is None


def test_issue_arp_and_render_post_fail_returns_manager() -> None:
    """POST failure → returns manager for the caller to clean up."""
    deps = _make_deps()
    ws = MagicMock()
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(exec_obj, "_connect_ws", return_value=ws),
        patch.object(exec_obj, "_post_arp_command", return_value=None),
    ):
        assert exec_obj._issue_arp_and_render(deps, "s", "d", None, False) is ws


def test_issue_arp_and_render_success_calls_await(capsys) -> None:
    """Happy path: post success → _await_and_render invoked, manager returned."""
    deps = _make_deps()
    ws = MagicMock()
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(exec_obj, "_connect_ws", return_value=ws),
        patch.object(exec_obj, "_post_arp_command", return_value="sess-1"),
        patch.object(exec_obj, "_await_and_render") as await_mock,
    ):
        got = exec_obj._issue_arp_and_render(deps, "s", "d", None, False)
    assert got is ws
    await_mock.assert_called_once()


# ---------- execute ----------


def test_execute_success_cleans_up(capsys) -> None:
    """execute happy path: run workflow + cleanup called with ws manager."""
    deps = _make_deps()
    exec_obj = ArpDeviceExecutor()
    ws = MagicMock()
    with (
        patch.object(exec_obj, "_run_workflow", return_value=ws),
        patch.object(arp_mod, "cleanup_ws_connection") as cleanup,
        patch.object(arp_mod, "detect_debug_mode", return_value=False),
    ):
        exec_obj.execute(deps)
    cleanup.assert_called_once_with(ws)


def test_execute_debug_mode_prints_banner(capsys) -> None:
    """execute debug_mode=True → prints legacy '[DEBUG] Starting ARP' banner."""
    deps = _make_deps()
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(exec_obj, "_run_workflow", return_value=None),
        patch.object(arp_mod, "cleanup_ws_connection"),
        patch.object(arp_mod, "detect_debug_mode", return_value=True),
    ):
        exec_obj.execute(deps)
    out = capsys.readouterr().out
    assert "[DEBUG] Starting ARP via WebSocket operation..." in out


def test_execute_swallows_exception_and_cleans_up(caplog) -> None:
    """execute error path: exception is logged (not raised), cleanup still runs."""
    deps = _make_deps()
    exec_obj = ArpDeviceExecutor()
    with (
        patch.object(exec_obj, "_run_workflow", side_effect=RuntimeError("kaboom")),
        patch.object(arp_mod, "cleanup_ws_connection") as cleanup,
        patch.object(arp_mod, "log_ws_error") as log_err,
        patch.object(arp_mod, "detect_debug_mode", return_value=False),
    ):
        exec_obj.execute(deps)
    cleanup.assert_called_once_with(None)  # workflow never returned a ws
    log_err.assert_called_once()
    assert "kaboom" in log_err.call_args.args[0]
