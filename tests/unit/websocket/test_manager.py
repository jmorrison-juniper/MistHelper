"""Unit tests for the WebSocket manager module.

Covers src/websocket/manager.py: the module-level helper functions
(_is_debug_mode, _is_debug_env_flag_set, log_ws_error, cleanup_ws_connection,
get_mist_credentials, dump_ws_debug_state, select_ws_site,
_log_credential_debug, check_mist_credentials) and the WebSocketManager class
(construction, _resolve_auth_headers, _start_websocket_thread, _await_handshake,
connect, _debug_print, _subscribe_command_channel, connect_and_subscribe,
subscribe_to_channel, _debug_log_sub, _poll_subscription_confirmed,
wait_for_subscription_confirmation, _build_result_collector,
wait_for_command_result, _on_open, _on_message, _on_error, _on_close,
disconnect).

These tests pin the WebSocket manager's observable contract (connection
lifecycle, subscription tracking, thread-safe result buffers, credential
resolution precedence, and debug/quiet log-noise gates) so future refactors of
the async reader wiring or the polling helpers cannot silently change the
public surface used by ping/ARP/service-discovery executors.
"""

from __future__ import annotations

import builtins
import importlib
import sys
import threading
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.websocket import manager as manager_mod
from src.websocket.manager import WebSocketManager

# ---------- Module import guard: raise ImportError when websocket-client missing ----------


def test_module_import_error_when_websocket_client_missing() -> None:
    """Reloading manager.py without websocket-client raises the branded ImportError.

    Why: Lines 17-22 of manager.py wrap ``import websocket`` in a try/except and
    re-raise with an actionable install hint. This exercises that guard by
    forcing the import to fail during reload and asserting the branded message.
    """
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "websocket":
            raise ImportError("no module named websocket")
        return real_import(name, *args, **kwargs)

    saved_ws = sys.modules.pop("websocket", None)
    saved_mgr = sys.modules.pop("src.websocket.manager", None)
    try:
        with patch.object(builtins, "__import__", side_effect=fake_import):
            with pytest.raises(ImportError, match="websocket-client is required"):
                importlib.import_module("src.websocket.manager")
    finally:
        if saved_ws is not None:
            sys.modules["websocket"] = saved_ws
        if saved_mgr is not None:
            sys.modules["src.websocket.manager"] = saved_mgr
        else:
            importlib.import_module("src.websocket.manager")


# ---------- Module-level helper: _is_debug_mode ----------


def test_is_debug_mode_true_for_long_flag() -> None:
    """--debug on sys.argv makes _is_debug_mode() return True."""
    with patch.object(manager_mod.sys, "argv", ["prog", "--debug"]):
        assert manager_mod._is_debug_mode() is True


def test_is_debug_mode_true_for_short_flag() -> None:
    """-d on sys.argv also makes _is_debug_mode() return True (short spelling)."""
    with patch.object(manager_mod.sys, "argv", ["prog", "-d"]):
        assert manager_mod._is_debug_mode() is True


def test_is_debug_mode_false_when_absent() -> None:
    """Absence of any debug flag returns False."""
    with patch.object(manager_mod.sys, "argv", ["prog", "other"]):
        assert manager_mod._is_debug_mode() is False


# ---------- Module-level helper: _is_debug_env_flag_set ----------


def test_is_debug_env_flag_set_true_for_recognised_values() -> None:
    """DEBUG env holding 'true', '1' or 'yes' → returns True (case-insensitive)."""
    for value in ("true", "TRUE", "1", "yes", "YES"):
        with patch.dict(manager_mod.os.environ, {"DEBUG": value}, clear=False):
            assert manager_mod._is_debug_env_flag_set() is True, value


def test_is_debug_env_flag_set_false_when_absent_or_other() -> None:
    """DEBUG unset, empty, or an unrecognised value → returns False."""
    with patch.dict(manager_mod.os.environ, {}, clear=True):
        assert manager_mod._is_debug_env_flag_set() is False
    with patch.dict(manager_mod.os.environ, {"DEBUG": "no"}, clear=True):
        assert manager_mod._is_debug_env_flag_set() is False
    with patch.dict(manager_mod.os.environ, {"DEBUG": ""}, clear=True):
        assert manager_mod._is_debug_env_flag_set() is False


# ---------- Module-level helper: log_ws_error ----------


def test_log_ws_error_prints_and_logs_without_traceback_when_not_debug(capsys) -> None:
    """log_ws_error prints an error banner and calls logging.error; no traceback when debug=False."""
    with (
        patch.object(manager_mod.logging, "error") as mock_err,
        patch.object(manager_mod.traceback, "print_exc") as mock_tb,
    ):
        manager_mod.log_ws_error("boom", debug_mode=False)
    out = capsys.readouterr().out
    assert "! boom" in out
    assert "[DEBUG] Exception details:" not in out
    mock_err.assert_called_once_with("boom")
    mock_tb.assert_not_called()


def test_log_ws_error_prints_traceback_when_debug(capsys) -> None:
    """log_ws_error with debug_mode=True dumps traceback in addition to the banner."""
    with patch.object(manager_mod.logging, "error"), patch.object(manager_mod.traceback, "print_exc") as mock_tb:
        manager_mod.log_ws_error("boom", debug_mode=True)
    out = capsys.readouterr().out
    assert "! boom" in out
    assert "[DEBUG] Exception details:" in out
    mock_tb.assert_called_once()


# ---------- Module-level helper: cleanup_ws_connection ----------


def test_cleanup_ws_connection_disconnects_manager(capsys) -> None:
    """cleanup_ws_connection calls disconnect() and prints confirmation on stdout."""
    mgr = MagicMock()
    manager_mod.cleanup_ws_connection(mgr, debug_mode=False)
    mgr.disconnect.assert_called_once()
    out = capsys.readouterr().out
    assert "-> WebSocket connection closed" in out
    assert "[DEBUG]" not in out


def test_cleanup_ws_connection_prints_debug_line_when_debug(capsys) -> None:
    """cleanup_ws_connection prints an extra [DEBUG] confirmation when debug_mode=True."""
    mgr = MagicMock()
    manager_mod.cleanup_ws_connection(mgr, debug_mode=True)
    assert "[DEBUG] WebSocket cleanup completed" in capsys.readouterr().out


def test_cleanup_ws_connection_none_manager_is_noop(capsys) -> None:
    """Passing ws_manager=None is a no-op (safe when construction failed earlier)."""
    manager_mod.cleanup_ws_connection(None, debug_mode=True)
    assert capsys.readouterr().out == ""


def test_cleanup_ws_connection_swallows_disconnect_exception() -> None:
    """Any exception raised by disconnect() is swallowed and logged as warning."""
    mgr = MagicMock()
    mgr.disconnect.side_effect = RuntimeError("nope")
    with patch.object(manager_mod.logging, "warning") as mock_warn:
        manager_mod.cleanup_ws_connection(mgr, debug_mode=False)
    mock_warn.assert_called_once()
    args = mock_warn.call_args[0]
    assert "WebSocket cleanup error" in args[0]


# ---------- Module-level helper: get_mist_credentials ----------


def test_get_mist_credentials_prefers_session_attributes() -> None:
    """When both session and env have values, session attributes win."""
    sess = MagicMock(host="sess-host", apitoken="sess-tok")
    with patch.dict(manager_mod.os.environ, {"MIST_HOST": "env-host", "MIST_APITOKEN": "env-tok"}, clear=True):
        got = manager_mod.get_mist_credentials(sess)
    assert got == ("sess-host", "sess-tok")


def test_get_mist_credentials_falls_back_to_env_when_session_missing() -> None:
    """Missing session attributes fall back to MIST_HOST / MIST_APITOKEN env vars."""
    sess = MagicMock(spec=[])  # No host/apitoken attributes.
    with patch.dict(manager_mod.os.environ, {"MIST_HOST": "env-host", "MIST_APITOKEN": "env-tok"}, clear=True):
        got = manager_mod.get_mist_credentials(sess)
    assert got == ("env-host", "env-tok")


def test_get_mist_credentials_returns_none_when_neither_source_has_value() -> None:
    """No session attrs + no env vars → returns (None, None)."""
    sess = MagicMock(spec=[])
    with patch.dict(manager_mod.os.environ, {}, clear=True):
        got = manager_mod.get_mist_credentials(sess)
    assert got == (None, None)


# ---------- Module-level helper: dump_ws_debug_state ----------


def test_dump_ws_debug_state_noop_when_debug_off(capsys) -> None:
    """dump_ws_debug_state with debug_mode=False prints nothing and does not touch state."""
    mgr = MagicMock()
    manager_mod.dump_ws_debug_state(mgr, debug_mode=False)
    assert capsys.readouterr().out == ""
    mgr.results_lock.__enter__.assert_not_called()


def test_dump_ws_debug_state_prints_state_when_debug_on(capsys) -> None:
    """dump_ws_debug_state prints connected flag, subscribed_channels, and pending session ids."""
    mgr = MagicMock()
    mgr.connected = True
    mgr.subscribed_channels = {"/a/b/cmd"}
    mgr.command_results = {"sess-1": {}, "sess-2": {}}
    mgr.results_lock = MagicMock()
    mgr.results_lock.__enter__ = MagicMock(return_value=mgr.results_lock)
    mgr.results_lock.__exit__ = MagicMock(return_value=False)
    manager_mod.dump_ws_debug_state(mgr, debug_mode=True)
    out = capsys.readouterr().out
    assert "Checking WebSocket manager state" in out
    assert "Connected = True" in out
    assert "/a/b/cmd" in out
    assert "sess-1" in out and "sess-2" in out


# ---------- Module-level helper: select_ws_site ----------


def test_select_ws_site_returns_selection(capsys) -> None:
    """A truthy select_site_fn return value is returned unchanged; no cancellation text."""
    deps = MagicMock()
    deps.select_site_fn.return_value = "site-abc"
    got = manager_mod.select_ws_site(deps, debug_mode=False)
    assert got == "site-abc"
    assert "cancelled" not in capsys.readouterr().out


def test_select_ws_site_returns_none_on_empty_and_prints_cancel(capsys) -> None:
    """Empty string return is normalised to None and a cancellation banner is printed."""
    deps = MagicMock()
    deps.select_site_fn.return_value = ""
    assert manager_mod.select_ws_site(deps, debug_mode=False) is None
    assert "No site selected. Operation cancelled." in capsys.readouterr().out


def test_select_ws_site_prints_debug_line_when_debug(capsys) -> None:
    """Selected site id is echoed as a [DEBUG] line only in debug mode."""
    deps = MagicMock()
    deps.select_site_fn.return_value = "site-xyz"
    manager_mod.select_ws_site(deps, debug_mode=True)
    assert "[DEBUG] Selected site_id = site-xyz" in capsys.readouterr().out


# ---------- Module-level helper: _log_credential_debug ----------


def test_log_credential_debug_prints_host_and_token_length(capsys) -> None:
    """Debug credential dump prints host verbatim but only the token length (never the token)."""
    manager_mod._log_credential_debug("host-name", "abcdef")
    out = capsys.readouterr().out
    assert "mist_host = host-name" in out
    assert "API token length = 6" in out
    assert "abcdef" not in out


# ---------- Module-level helper: check_mist_credentials ----------


def test_check_mist_credentials_true_when_both_present() -> None:
    """Both host and token present → returns True; ws_mgr NOT disconnected."""
    mgr = MagicMock()
    assert manager_mod.check_mist_credentials(mgr, "h", "t", debug_mode=False) is True
    mgr.disconnect.assert_not_called()


def test_check_mist_credentials_false_when_host_missing_and_disconnects(capsys) -> None:
    """Missing host → prints error, calls disconnect(), returns False."""
    mgr = MagicMock()
    assert manager_mod.check_mist_credentials(mgr, None, "t", debug_mode=False) is False
    mgr.disconnect.assert_called_once()
    assert "Mist host or API token not found" in capsys.readouterr().out


def test_check_mist_credentials_false_when_token_missing() -> None:
    """Missing token → returns False; disconnect is called on non-None manager."""
    mgr = MagicMock()
    assert manager_mod.check_mist_credentials(mgr, "h", None, debug_mode=False) is False
    mgr.disconnect.assert_called_once()


def test_check_mist_credentials_missing_with_none_manager_no_disconnect(capsys) -> None:
    """When ws_mgr is None and creds are missing, no disconnect attempt; still returns False."""
    assert manager_mod.check_mist_credentials(None, None, None, debug_mode=False) is False
    assert "Mist host or API token not found" in capsys.readouterr().out


def test_check_mist_credentials_prints_debug_when_valid_and_debug_mode(capsys) -> None:
    """Valid creds + debug_mode=True → helper prints host + token length."""
    mgr = MagicMock()
    assert manager_mod.check_mist_credentials(mgr, "host", "tok", debug_mode=True) is True
    assert "mist_host = host" in capsys.readouterr().out


# ---------- WebSocketManager.__init__ ----------


def _make_session(host: str | None = "api.mist.com", apitoken: str | None = "tok") -> MagicMock:
    """Return a mock Mist session with host/apitoken attributes for manager construction."""
    sess = MagicMock()
    sess.host = host
    sess.apitoken = apitoken
    return sess


def test_init_uses_explicit_host_when_provided() -> None:
    """Explicit mist_host arg takes precedence over session and env."""
    with patch.dict(manager_mod.os.environ, {"MIST_HOST": "env.mist.com"}, clear=True):
        m = WebSocketManager(_make_session(host="sess.mist.com"), mist_host="api.explicit.com")
    assert m.mist_host == "api.explicit.com"
    assert m.websocket_url == "wss://api-ws.explicit.com/api-ws/v1/stream"


def test_init_falls_back_to_session_host_then_env() -> None:
    """Session.host is used when explicit is None; env is only touched if both are None."""
    m1 = WebSocketManager(_make_session(host="api.sess.com"))
    assert m1.mist_host == "api.sess.com"
    sess = MagicMock(spec=[])
    with patch.dict(manager_mod.os.environ, {"MIST_HOST": "api.env.com"}, clear=True):
        m2 = WebSocketManager(sess)
    assert m2.mist_host == "api.env.com"


def test_init_defaults_to_api_mist_com_when_no_source_provides_host() -> None:
    """When explicit, session, and env all lack host, default 'api.mist.com' is used."""
    sess = MagicMock(spec=[])
    with patch.dict(manager_mod.os.environ, {}, clear=True):
        m = WebSocketManager(sess)
    assert m.mist_host == "api.mist.com"
    assert m.websocket_url == "wss://api-ws.mist.com/api-ws/v1/stream"


def test_init_state_defaults() -> None:
    """Fresh manager has connected=False, empty sets/dicts, and no thread."""
    m = WebSocketManager(_make_session())
    assert m.connected is False
    assert m.subscribed_channels == set()
    assert m.confirmed_subscriptions == set()
    assert m.command_results == {}
    assert m.websocket_thread is None
    assert m.websocket_connection is None
    assert isinstance(m.results_lock, type(threading.Lock()))


# ---------- WebSocketManager._resolve_auth_headers ----------


def test_resolve_auth_headers_returns_none_when_no_token() -> None:
    """Missing session token AND missing env → returns None + logs error."""
    sess = MagicMock(spec=[])
    with patch.dict(manager_mod.os.environ, {}, clear=True):
        m = WebSocketManager(sess, mist_host="api.mist.com")
        assert m._resolve_auth_headers() is None


def test_resolve_auth_headers_uses_session_token() -> None:
    """Session.apitoken produces the Authorization header verbatim."""
    m = WebSocketManager(_make_session(apitoken="TOK"))
    assert m._resolve_auth_headers() == ["Authorization: Token TOK"]


def test_resolve_auth_headers_falls_back_to_env_token() -> None:
    """No session.apitoken → MIST_APITOKEN env var is used."""
    sess = MagicMock(spec=["host"])
    sess.host = "api.mist.com"
    with patch.dict(manager_mod.os.environ, {"MIST_APITOKEN": "ENVTOK"}, clear=True):
        m = WebSocketManager(sess)
        assert m._resolve_auth_headers() == ["Authorization: Token ENVTOK"]


# ---------- WebSocketManager._start_websocket_thread ----------


def test_start_websocket_thread_constructs_app_and_starts_daemon() -> None:
    """_start_websocket_thread builds WebSocketApp with our callbacks and spawns a daemon thread."""
    m = WebSocketManager(_make_session())
    fake_ws = MagicMock()
    fake_thread = MagicMock()
    with (
        patch.object(manager_mod.websocket, "WebSocketApp", return_value=fake_ws) as mock_app,
        patch.object(manager_mod.threading, "Thread", return_value=fake_thread) as mock_thread,
    ):
        m._start_websocket_thread(["Authorization: Token X"])
    mock_app.assert_called_once()
    kwargs = mock_app.call_args.kwargs
    assert kwargs["on_open"] == m._on_open
    assert kwargs["on_message"] == m._on_message
    assert kwargs["on_error"] == m._on_error
    assert kwargs["on_close"] == m._on_close
    mock_thread.assert_called_once()
    thread_kwargs = mock_thread.call_args.kwargs
    assert thread_kwargs["daemon"] is True
    assert thread_kwargs["target"] == fake_ws.run_forever
    fake_thread.start.assert_called_once()
    assert m.websocket_connection is fake_ws
    assert m.websocket_thread is fake_thread


# ---------- WebSocketManager._await_handshake ----------


def test_await_handshake_returns_true_on_immediate_connect() -> None:
    """When self.connected is already True, _await_handshake returns True without sleeping."""
    m = WebSocketManager(_make_session())
    m.connected = True
    with patch.object(manager_mod.time, "sleep") as mock_sleep:
        assert m._await_handshake() is True
    mock_sleep.assert_not_called()


def test_await_handshake_returns_true_when_flag_flips_mid_poll() -> None:
    """When connected flips True mid-loop, _await_handshake returns True on next iteration."""
    m = WebSocketManager(_make_session())
    calls = {"n": 0}

    def sleep_side_effect(_secs: float) -> None:
        """Flip m.connected True after two ticks (exercises the log-mod path)."""
        calls["n"] += 1
        if calls["n"] >= 2:
            m.connected = True

    with patch.object(manager_mod.time, "sleep", side_effect=sleep_side_effect):
        assert m._await_handshake() is True
    assert calls["n"] >= 2


def test_await_handshake_returns_false_on_timeout() -> None:
    """When connected never flips True, _await_handshake exhausts polls and returns False."""
    m = WebSocketManager(_make_session())
    with patch.object(manager_mod.time, "sleep"):
        assert m._await_handshake() is False


# ---------- WebSocketManager.connect ----------


def test_connect_returns_false_when_no_auth_headers() -> None:
    """connect() returns False when _resolve_auth_headers() returns None."""
    m = WebSocketManager(_make_session())
    with patch.object(m, "_resolve_auth_headers", return_value=None):
        assert m.connect() is False


def test_connect_returns_false_on_handshake_timeout() -> None:
    """connect() returns False when _await_handshake times out; thread is still started."""
    m = WebSocketManager(_make_session())
    with (
        patch.object(m, "_resolve_auth_headers", return_value=["h"]),
        patch.object(m, "_start_websocket_thread") as mock_start,
        patch.object(m, "_await_handshake", return_value=False),
    ):
        assert m.connect() is False
    mock_start.assert_called_once_with(["h"])


def test_connect_returns_true_on_success() -> None:
    """connect() returns True on successful handshake."""
    m = WebSocketManager(_make_session())
    with (
        patch.object(m, "_resolve_auth_headers", return_value=["h"]),
        patch.object(m, "_start_websocket_thread"),
        patch.object(m, "_await_handshake", return_value=True),
    ):
        assert m.connect() is True


def test_connect_returns_false_on_exception() -> None:
    """Any exception raised during connect() is swallowed and False is returned."""
    m = WebSocketManager(_make_session())
    with patch.object(m, "_resolve_auth_headers", side_effect=RuntimeError("boom")):
        assert m.connect() is False


# ---------- WebSocketManager._debug_print ----------


def test_debug_print_prints_only_when_debug(capsys) -> None:
    """_debug_print emits a [DEBUG] line only when debug_mode is True."""
    m = WebSocketManager(_make_session())
    m._debug_print("hello", debug_mode=False)
    assert capsys.readouterr().out == ""
    m._debug_print("hello", debug_mode=True)
    assert "[DEBUG] hello" in capsys.readouterr().out


# ---------- WebSocketManager._subscribe_command_channel ----------


def test_subscribe_command_channel_success_prints_debug(capsys) -> None:
    """Successful subscribe returns True and, in debug mode, prints the channel."""
    m = WebSocketManager(_make_session())
    with patch.object(m, "subscribe_to_channel", return_value=True):
        assert m._subscribe_command_channel("s1", "d1", debug_mode=True) is True
    out = capsys.readouterr().out
    assert "/sites/s1/devices/d1/cmd" in out
    assert "[DEBUG] Subscribed to channel" in out


def test_subscribe_command_channel_failure_disconnects(capsys) -> None:
    """Failed subscribe returns False, disconnects the manager, prints error banner."""
    m = WebSocketManager(_make_session())
    with patch.object(m, "subscribe_to_channel", return_value=False), patch.object(m, "disconnect") as mock_disc:
        assert m._subscribe_command_channel("s", "d", debug_mode=False) is False
    mock_disc.assert_called_once()
    assert "Failed to subscribe to device command channel" in capsys.readouterr().out


# ---------- WebSocketManager.connect_and_subscribe ----------


def test_connect_and_subscribe_returns_false_on_connect_failure(capsys) -> None:
    """When connect() returns False, connect_and_subscribe returns False + prints error."""
    m = WebSocketManager(_make_session())
    with patch.object(m, "connect", return_value=False):
        assert m.connect_and_subscribe("s", "d", debug_mode=False) is False
    assert "Failed to establish WebSocket connection" in capsys.readouterr().out


def test_connect_and_subscribe_returns_false_when_subscribe_fails() -> None:
    """When _subscribe_command_channel returns False, overall result is False."""
    m = WebSocketManager(_make_session())
    with (
        patch.object(m, "connect", return_value=True),
        patch.object(m, "_subscribe_command_channel", return_value=False),
        patch.object(manager_mod.time, "sleep"),
    ):
        assert m.connect_and_subscribe("s", "d", debug_mode=False) is False


def test_connect_and_subscribe_success_sleeps_and_returns_true(capsys) -> None:
    """Happy path: connect + subscribe both succeed → True; time.sleep stabiliser is called."""
    m = WebSocketManager(_make_session())
    with (
        patch.object(m, "connect", return_value=True),
        patch.object(m, "_subscribe_command_channel", return_value=True),
        patch.object(manager_mod.time, "sleep") as mock_sleep,
    ):
        assert m.connect_and_subscribe("s", "d", debug_mode=True) is True
    mock_sleep.assert_called_once_with(manager_mod._WS_STABILIZE_SLEEP_SECONDS)
    assert "WebSocket connected and subscribed" in capsys.readouterr().out


# ---------- WebSocketManager.subscribe_to_channel ----------


def test_subscribe_to_channel_returns_false_when_not_connected() -> None:
    """Subscribing before handshake returns False without touching the socket."""
    m = WebSocketManager(_make_session())
    assert m.subscribe_to_channel("/x") is False


def test_subscribe_to_channel_sends_json_and_tracks_channel() -> None:
    """Connected + valid send: subscribe frame is JSON-encoded and the channel tracked."""
    m = WebSocketManager(_make_session())
    m.connected = True
    m.websocket_connection = MagicMock()
    assert m.subscribe_to_channel("/foo") is True
    m.websocket_connection.send.assert_called_once()
    sent = m.websocket_connection.send.call_args[0][0]
    assert '"subscribe": "/foo"' in sent
    assert "/foo" in m.subscribed_channels


def test_subscribe_to_channel_handles_none_connection_gracefully() -> None:
    """connected=True but websocket_connection=None → still returns True and tracks channel (mypy branch)."""
    m = WebSocketManager(_make_session())
    m.connected = True
    m.websocket_connection = None
    assert m.subscribe_to_channel("/bar") is True
    assert "/bar" in m.subscribed_channels


def test_subscribe_to_channel_returns_false_on_send_exception() -> None:
    """Exception raised during send is swallowed; helper returns False."""
    m = WebSocketManager(_make_session())
    m.connected = True
    m.websocket_connection = MagicMock()
    m.websocket_connection.send.side_effect = RuntimeError("send failed")
    assert m.subscribe_to_channel("/x") is False


# ---------- WebSocketManager._debug_log_sub ----------


def test_debug_log_sub_noop_when_debug_off(capsys) -> None:
    """_debug_log_sub emits nothing when debug_mode is False."""
    m = WebSocketManager(_make_session())
    m._debug_log_sub("Waiting", "/x", debug_mode=False)
    assert capsys.readouterr().out == ""


def test_debug_log_sub_prints_and_logs_when_debug_on(capsys) -> None:
    """_debug_log_sub prints stdout line AND calls logger.debug when debug_mode is True."""
    m = WebSocketManager(_make_session())
    with patch.object(m.logger, "debug") as mock_dbg:
        m._debug_log_sub("Waiting", "/x", debug_mode=True)
    mock_dbg.assert_called_once()
    assert "[DEBUG] Waiting: /x" in capsys.readouterr().out


# ---------- WebSocketManager._poll_subscription_confirmed ----------


def test_poll_subscription_confirmed_true_when_present() -> None:
    """Already-confirmed channel → immediate True without sleeping."""
    m = WebSocketManager(_make_session())
    m.confirmed_subscriptions.add("/ok")
    with patch.object(manager_mod.time, "sleep") as mock_sleep:
        assert m._poll_subscription_confirmed("/ok", timeout_seconds=1.0) is True
    mock_sleep.assert_not_called()


def test_poll_subscription_confirmed_true_when_added_mid_poll() -> None:
    """Channel gets added during the loop → returns True on the next iteration."""
    m = WebSocketManager(_make_session())

    def add_mid(_secs: float) -> None:
        """Populate confirmed_subscriptions during the polling sleep."""
        m.confirmed_subscriptions.add("/late")

    with patch.object(manager_mod.time, "sleep", side_effect=add_mid):
        # Return two rising time values then a large one so the loop stops after one iteration.
        with patch.object(manager_mod.time, "time", side_effect=[0.0, 0.0, 0.05, 0.10, 5.0]):
            assert m._poll_subscription_confirmed("/late", timeout_seconds=1.0) is True


def test_poll_subscription_confirmed_false_on_timeout() -> None:
    """Timeout without confirmation returns False."""
    m = WebSocketManager(_make_session())
    with (
        patch.object(manager_mod.time, "sleep"),
        patch.object(manager_mod.time, "time", side_effect=[0.0, 0.0, 2.0, 2.0]),
    ):
        assert m._poll_subscription_confirmed("/never", timeout_seconds=1.0) is False


# ---------- WebSocketManager.wait_for_subscription_confirmation ----------


def test_wait_for_subscription_confirmation_success() -> None:
    """Successful poll returns True."""
    m = WebSocketManager(_make_session())
    with patch.object(m, "_poll_subscription_confirmed", return_value=True):
        assert m.wait_for_subscription_confirmation("/ok") is True


def test_wait_for_subscription_confirmation_timeout_logs_warning() -> None:
    """Timeout returns False AND emits a logger.warning banner."""
    m = WebSocketManager(_make_session())
    with (
        patch.object(m, "_poll_subscription_confirmed", return_value=False),
        patch.object(m.logger, "warning") as mock_warn,
    ):
        assert m.wait_for_subscription_confirmation("/nope") is False
    mock_warn.assert_called_once()


def test_wait_for_subscription_confirmation_debug_env_flag_triggers_debug_output(capsys) -> None:
    """DEBUG env flag enables the [DEBUG] trace lines even without --debug arg."""
    m = WebSocketManager(_make_session())
    with (
        patch.object(m, "_poll_subscription_confirmed", return_value=True),
        patch.object(manager_mod, "_is_debug_env_flag_set", return_value=True),
    ):
        m.wait_for_subscription_confirmation("/dbg")
    assert "[DEBUG] Waiting for subscription confirmation for" in capsys.readouterr().out


def test_wait_for_subscription_confirmation_debug_mode_attr_triggers_debug(capsys) -> None:
    """A manager with debug_mode attribute set True prints [DEBUG] lines too."""
    m = WebSocketManager(_make_session())
    m.debug_mode = True  # type: ignore[attr-defined]
    with (
        patch.object(m, "_poll_subscription_confirmed", return_value=False),
        patch.object(manager_mod, "_is_debug_env_flag_set", return_value=False),
    ):
        m.wait_for_subscription_confirmation("/dbg2")
    out = capsys.readouterr().out
    assert "Waiting for subscription confirmation" in out
    assert "Timeout waiting for subscription confirmation" in out


# ---------- WebSocketManager._build_result_collector ----------


def test_build_result_collector_constructs_with_shared_state() -> None:
    """Result collector is built with the manager's shared buffers and debug flag."""
    m = WebSocketManager(_make_session())
    sentinel = object()
    with (
        patch.object(manager_mod, "ResultCollector", return_value=sentinel) as mock_rc,
        patch.object(manager_mod, "_is_debug_mode", return_value=True),
    ):
        got = m._build_result_collector()
    assert got is sentinel
    args = mock_rc.call_args[0]
    assert args[0] is m.command_results
    assert args[1] is m.results_lock
    assert args[2] is m.logger
    assert args[3] is True


# ---------- WebSocketManager.wait_for_command_result ----------


def test_wait_for_command_result_delegates_to_collector() -> None:
    """wait_for_command_result delegates to the ResultCollector and returns its value."""
    m = WebSocketManager(_make_session())
    fake_collector = MagicMock()
    fake_collector.collect.return_value = {"raw": "ok"}
    with patch.object(m, "_build_result_collector", return_value=fake_collector):
        got = m.wait_for_command_result("sess-1", timeout_seconds=5, activity_timeout_seconds=1)
    assert got == {"raw": "ok"}
    fake_collector.collect.assert_called_once_with("sess-1", 5, 1)


def test_wait_for_command_result_returns_none_when_collector_returns_none() -> None:
    """None from the collector is passed through unchanged (timeout contract preserved)."""
    m = WebSocketManager(_make_session())
    fake_collector = MagicMock()
    fake_collector.collect.return_value = None
    with patch.object(m, "_build_result_collector", return_value=fake_collector):
        assert m.wait_for_command_result("sess-x") is None


# ---------- WebSocketManager._on_open / _on_error / _on_close ----------


def test_on_open_sets_connected_true() -> None:
    """_on_open flips connected → True and logs debug line."""
    m = WebSocketManager(_make_session())
    m._on_open(MagicMock())
    assert m.connected is True


def test_on_error_logs_error() -> None:
    """_on_error logs both the error type and message."""
    m = WebSocketManager(_make_session())
    with patch.object(m.logger, "error") as mock_err, patch.object(m.logger, "debug"):
        m._on_error(MagicMock(), RuntimeError("boom"))
    mock_err.assert_called_once()


def test_on_close_sets_connected_false_and_logs() -> None:
    """_on_close flips connected → False and logs close-code details."""
    m = WebSocketManager(_make_session())
    m.connected = True
    with patch.object(m.logger, "info") as mock_info:
        m._on_close(MagicMock(), 1000, "normal")
    assert m.connected is False
    mock_info.assert_called_once()


# ---------- WebSocketManager._on_message ----------


def test_on_message_routes_via_message_router() -> None:
    """_on_message constructs a MessageRouter and delegates the frame to router.route()."""
    m = WebSocketManager(_make_session())
    fake_router = MagicMock()
    with (
        patch.object(manager_mod, "MessageRouter", return_value=fake_router) as mock_router_cls,
        patch.object(manager_mod, "_is_debug_mode", return_value=False),
    ):
        m._on_message(MagicMock(), "raw-frame")
    mock_router_cls.assert_called_once()
    router_args = mock_router_cls.call_args[0]
    assert router_args[0] is m.command_results
    assert router_args[1] is m.results_lock
    assert router_args[2] is m.confirmed_subscriptions
    assert router_args[3] is m.logger
    assert router_args[4] is False
    fake_router.route.assert_called_once_with("raw-frame")


# ---------- WebSocketManager.disconnect ----------


def test_disconnect_when_no_connection_still_resets_state() -> None:
    """Idempotent disconnect: no websocket_connection → still clears flags and buffers."""
    m = WebSocketManager(_make_session())
    m.connected = True
    m.subscribed_channels.add("/x")
    m.command_results["s"] = {"raw": "y"}
    m.disconnect()
    assert m.connected is False
    assert m.subscribed_channels == set()
    assert m.command_results == {}


def test_disconnect_closes_and_clears_when_connection_present() -> None:
    """When websocket_connection exists, disconnect() calls close() and clears state."""
    m = WebSocketManager(_make_session())
    m.websocket_connection = MagicMock()
    m.connected = True
    m.subscribed_channels.add("/a")
    m.command_results["s"] = {"raw": "v"}
    m.disconnect()
    m.websocket_connection.close.assert_called_once()
    assert m.connected is False
    assert m.subscribed_channels == set()
    assert m.command_results == {}


# ---------- Extra coverage: _await_handshake final-poll flag flip ----------


def test_await_handshake_flag_flip_after_last_sleep_returns_true() -> None:
    """When connected is flipped True after the final sleep, the trailing return picks it up."""
    m = WebSocketManager(_make_session())
    calls = {"n": 0}

    def sleep_side_effect(_secs: float) -> None:
        """Only flip on the final sleep (matches the fall-through return in _await_handshake)."""
        calls["n"] += 1
        if calls["n"] == manager_mod._WS_CONNECT_MAX_POLLS:
            m.connected = True

    with patch.object(manager_mod.time, "sleep", side_effect=sleep_side_effect):
        assert m._await_handshake() is True


# ---------- Extra branch coverage: check_mist_credentials both missing, ws None ----------


def test_check_mist_credentials_debug_mode_off_no_credential_dump(capsys) -> None:
    """Valid creds but debug_mode=False → no credential dump printed."""
    assert manager_mod.check_mist_credentials(MagicMock(), "h", "t", debug_mode=False) is True
    assert "mist_host" not in capsys.readouterr().out
