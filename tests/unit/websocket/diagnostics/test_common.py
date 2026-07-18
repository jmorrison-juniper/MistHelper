"""Unit tests for the WebSocket diagnostic-command shared helpers.

Covers src/websocket/diagnostics/common.py: detect_debug_mode, post_device_command,
extract_command_session, prepare_command_credentials, and the two extra-field
printers. The helpers exist to keep the ping/ARP executors small and testable —
these tests pin the branching (debug on/off, HTTP success/failure, missing
session id, credential-validation failure) so future refactors of the executors
cannot silently change the observable contract.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from src.websocket.diagnostics import common as common_mod


def _fake_response(status: int, body: dict[str, Any] | None = None, text: str = "") -> MagicMock:
    """Build a MagicMock that mimics a requests.Response with .status_code/.json()/.text."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = body or {}
    resp.text = text or (str(body) if body else "")
    return resp


def test_detect_debug_mode_true_for_long_flag() -> None:
    """--debug on sys.argv flips detect_debug_mode() to True."""
    with patch.object(common_mod.sys, "argv", ["prog", "--debug"]):
        assert common_mod.detect_debug_mode() is True


def test_detect_debug_mode_true_for_short_flag() -> None:
    """-d on sys.argv also flips detect_debug_mode() to True (alt spelling)."""
    with patch.object(common_mod.sys, "argv", ["prog", "-d"]):
        assert common_mod.detect_debug_mode() is True


def test_detect_debug_mode_false_when_absent() -> None:
    """No debug flag on sys.argv → detect_debug_mode() returns False."""
    with patch.object(common_mod.sys, "argv", ["prog", "other"]):
        assert common_mod.detect_debug_mode() is False


def test_post_device_command_returns_response_and_calls_requests(capsys) -> None:
    """post_device_command posts JSON and returns the raw Response (debug OFF: no prints)."""
    fake = _fake_response(200, {"ok": True})
    with patch.object(common_mod.requests, "post", return_value=fake) as mock_post:
        got = common_mod.post_device_command(
            "https://x/y", {"Authorization": "Token X"}, {"a": 1}, debug_mode=False, command_label="ping"
        )
    assert got is fake
    mock_post.assert_called_once_with("https://x/y", headers={"Authorization": "Token X"}, json={"a": 1}, timeout=30)
    out = capsys.readouterr().out
    assert "[DEBUG]" not in out  # No debug prints when debug_mode=False


def test_post_device_command_prints_debug_when_enabled(capsys) -> None:
    """post_device_command with debug_mode=True prints URL, redacted headers, status, body."""
    fake = _fake_response(200, {"ok": True}, text="body-here")
    with patch.object(common_mod.requests, "post", return_value=fake):
        common_mod.post_device_command(
            "https://x/y", {"Authorization": "Token real"}, {"a": 1}, debug_mode=True, command_label="ping"
        )
    out = capsys.readouterr().out
    assert "[DEBUG] POST URL = https://x/y" in out
    assert "[REDACTED]" in out and "Token real" not in out  # Never leak the real token
    assert "HTTP Response Status = 200" in out
    assert "body-here" in out


def test_extract_command_session_success_returns_id() -> None:
    """A 200 response with a session id returns the session id verbatim; ws is NOT disconnected."""
    resp = _fake_response(200, {"session": "sess-abc"})
    ws = MagicMock()
    assert common_mod.extract_command_session(resp, ws, "ping") == "sess-abc"
    ws.disconnect.assert_not_called()


def test_extract_command_session_non_200_disconnects_and_returns_none(capsys) -> None:
    """Non-200 response disconnects the WS and returns None; failure is announced to stdout."""
    resp = _fake_response(500, text="boom")
    ws = MagicMock()
    assert common_mod.extract_command_session(resp, ws, "ping") is None
    ws.disconnect.assert_called_once()
    out = capsys.readouterr().out
    assert "Failed to issue ping command: 500" in out
    assert "boom" in out


def test_extract_command_session_missing_session_disconnects_and_returns_none(capsys) -> None:
    """200 response with no 'session' key disconnects the WS and returns None."""
    resp = _fake_response(200, {"other": "data"})
    ws = MagicMock()
    assert common_mod.extract_command_session(resp, ws, "arp") is None
    ws.disconnect.assert_called_once()
    assert "No session ID returned from arp command" in capsys.readouterr().out


def test_extract_command_session_empty_session_id_treated_as_missing(capsys) -> None:
    """Empty string session id is falsey → treated as missing (disconnect + None)."""
    resp = _fake_response(200, {"session": ""})
    ws = MagicMock()
    assert common_mod.extract_command_session(resp, ws, "arp") is None
    ws.disconnect.assert_called_once()
    assert "No session ID returned from arp command" in capsys.readouterr().out


def test_prepare_command_credentials_success_returns_tuple() -> None:
    """Valid credentials → returns (host, token); ws is NOT disconnected."""
    apisession = MagicMock()
    ws = MagicMock()
    with (
        patch.object(common_mod, "get_mist_credentials", return_value=("host.example", "tok-xyz")),
        patch.object(common_mod, "check_mist_credentials", return_value=True),
    ):
        got = common_mod.prepare_command_credentials(apisession, ws, debug_mode=False)
    assert got == ("host.example", "tok-xyz")
    ws.disconnect.assert_not_called()


def test_prepare_command_credentials_failure_returns_none() -> None:
    """check_mist_credentials returning False → helper returns None (caller aborts)."""
    apisession = MagicMock()
    ws = MagicMock()
    with (
        patch.object(common_mod, "get_mist_credentials", return_value=("h", "t")),
        patch.object(common_mod, "check_mist_credentials", return_value=False),
    ):
        assert common_mod.prepare_command_credentials(apisession, ws, debug_mode=True) is None
    # check_mist_credentials owns disconnect on failure; helper does not call it itself


def test_print_extra_result_fields_no_extras_is_noop(capsys) -> None:
    """When every key is in the excluded set, nothing is printed."""
    common_mod.print_extra_result_fields({"raw": "x", "Output": "y"}, {"raw", "Output", "session"})
    assert capsys.readouterr().out == ""


def test_print_extra_result_fields_prints_extras(capsys) -> None:
    """Extra keys with truthy values are printed after the OTHER AVAILABLE FIELDS header."""
    payload = {"raw": "x", "Output": "y", "session": "s", "extra1": "val1", "extra2": 42}
    common_mod.print_extra_result_fields(payload, {"raw", "Output", "session"})
    out = capsys.readouterr().out
    assert "OTHER AVAILABLE FIELDS: ['extra1', 'extra2']" in out
    assert "extra1: val1" in out
    assert "extra2: 42" in out


def test_print_extra_result_fields_skips_falsy_extras(capsys) -> None:
    """Extra keys with falsey values are announced in the header but not printed as lines."""
    payload = {"extra_empty": "", "extra_none": None, "extra_zero": 0, "extra_real": "kept"}
    common_mod.print_extra_result_fields(payload, set())
    out = capsys.readouterr().out
    assert "OTHER AVAILABLE FIELDS:" in out
    assert "extra_real: kept" in out
    assert "extra_empty:" not in out  # Empty string is falsey → skipped
    assert "extra_none:" not in out  # None is falsey → skipped
    assert "extra_zero:" not in out  # 0 is falsey → skipped
