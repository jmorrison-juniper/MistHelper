"""Unit tests for src.device.arp_command_manager.ARPCommandManager.

Tranche 12 of initiative #878: un-omit `arp_command_manager.py` and drive it to
100% line coverage.

Why:
    ARPCommandManager owns the ARP-over-WebSocket lifecycle (REST trigger,
    stream subscription, nested JSON payload parsing, raw-text buffering,
    PrettyTable render, and dual-dataset CSV export). All I/O — HTTP,
    WebSocket, filesystem, and the live-global lookups on the ``MistHelper``
    module — is mocked here so the tests exercise pure logic without touching
    the network or disk.
"""

from __future__ import annotations

import json
import logging
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from src.dataclasses.websocket_stream_target import WebSocketStreamTarget
from src.device import arp_command_manager as arp_mod
from src.device.arp_command_manager import ARPCommandManager

# WHY: caplog must target the module logger so INFO/WARNING/ERROR records surface (issue #886).
_LOGGER_NAME = "src.device.arp_command_manager"


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake ``MistHelper`` module so lazy importlib lookups resolve here.

    Why:
        ARPCommandManager reaches ``PromptClientUtils``, ``apisession``, and
        ``FilePathUtils`` via ``importlib.import_module("MistHelper")`` at call
        time. Registering a synthetic module in ``sys.modules`` lets each test
        stub only what it needs without depending on the real MistHelper.py.
    """
    module = types.ModuleType("MistHelper")
    module.PromptClientUtils = MagicMock()
    module.apisession = types.SimpleNamespace(host=None, apitoken=None)
    module.FilePathUtils = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", module)
    return module


def _target(**overrides) -> WebSocketStreamTarget:
    """Build a WebSocketStreamTarget with defaults, overridable per test."""
    defaults = {
        "mist_host": "api-ws.mist.example",
        "mist_apitoken": "tok",
        "site_id": "site-1",
        "device_id": "dev-1",
        "session_id": "sess-1",
    }
    defaults.update(overrides)
    return WebSocketStreamTarget(**defaults)


class TestResolveArpTargetIds:
    """Cover _resolve_arp_target_ids passthrough and prompt paths."""

    def test_passthrough_when_both_ids_supplied(self, fake_mh):
        """Return the ids as-is when both are already provided."""
        result = ARPCommandManager._resolve_arp_target_ids("s1", "d1")
        assert result == ("s1", "d1")
        fake_mh.PromptClientUtils.select_site_and_device_ids.assert_not_called()

    def test_prompts_when_site_missing(self, fake_mh):
        """Delegate to PromptClientUtils when site_id is missing."""
        fake_mh.PromptClientUtils.select_site_and_device_ids.return_value = ("s2", "d2")
        result = ARPCommandManager._resolve_arp_target_ids(None, "d1")
        assert result == ("s2", "d2")
        fake_mh.PromptClientUtils.select_site_and_device_ids.assert_called_once_with(None, "d1")

    def test_prompts_when_device_missing(self, fake_mh):
        """Delegate to PromptClientUtils when device_id is missing."""
        fake_mh.PromptClientUtils.select_site_and_device_ids.return_value = ("s1", "d3")
        result = ARPCommandManager._resolve_arp_target_ids("s1", None)
        assert result == ("s1", "d3")


class TestResolveMistWsCredentials:
    """Cover session > env credential resolution paths."""

    def test_uses_session_values_when_present(self, fake_mh, monkeypatch):
        """Session host/token beat environment fallback."""
        fake_mh.apisession = types.SimpleNamespace(host="sess.host", apitoken="sess-tok")
        monkeypatch.setenv("MIST_HOST", "env.host")
        monkeypatch.setenv("MIST_APITOKEN", "env-tok")
        assert ARPCommandManager._resolve_mist_ws_credentials() == ("sess.host", "sess-tok")

    def test_falls_back_to_env_when_session_empty(self, fake_mh, monkeypatch):
        """Empty session attributes trigger environment lookup."""
        fake_mh.apisession = types.SimpleNamespace(host=None, apitoken=None)
        monkeypatch.setenv("MIST_HOST", "env.host")
        monkeypatch.setenv("MIST_APITOKEN", "env-tok")
        assert ARPCommandManager._resolve_mist_ws_credentials() == ("env.host", "env-tok")

    def test_returns_nones_when_host_missing(self, fake_mh, monkeypatch):
        """Missing host returns (None, None) regardless of token."""
        fake_mh.apisession = types.SimpleNamespace(host=None, apitoken=None)
        monkeypatch.delenv("MIST_HOST", raising=False)
        monkeypatch.setenv("MIST_APITOKEN", "env-tok")
        assert ARPCommandManager._resolve_mist_ws_credentials() == (None, None)

    def test_returns_nones_when_token_missing(self, fake_mh, monkeypatch):
        """Missing token returns (None, None) regardless of host."""
        fake_mh.apisession = types.SimpleNamespace(host=None, apitoken=None)
        monkeypatch.setenv("MIST_HOST", "env.host")
        monkeypatch.delenv("MIST_APITOKEN", raising=False)
        assert ARPCommandManager._resolve_mist_ws_credentials() == (None, None)


class TestExecute:
    """Cover the orchestrator's abort and happy paths."""

    def test_aborts_when_ids_unresolved(self, fake_mh):
        """Abort silently when target-id resolution yields empties."""
        fake_mh.PromptClientUtils.select_site_and_device_ids.return_value = (None, None)
        with patch.object(ARPCommandManager, "_trigger_command") as trigger:
            ARPCommandManager.execute()
        trigger.assert_not_called()

    def test_aborts_when_credentials_missing(self, fake_mh, monkeypatch, caplog):
        """Abort with user-facing notice when credentials cannot be resolved."""
        monkeypatch.delenv("MIST_HOST", raising=False)
        monkeypatch.delenv("MIST_APITOKEN", raising=False)
        caplog.set_level(logging.WARNING, logger=_LOGGER_NAME)
        with patch.object(ARPCommandManager, "_trigger_command") as trigger:
            ARPCommandManager.execute("s1", "d1")
        trigger.assert_not_called()
        assert any("Mist host or API token not found" in r.getMessage() for r in caplog.records)

    def test_aborts_when_trigger_returns_none(self, fake_mh, monkeypatch):
        """Skip listener when REST trigger fails to return a session id."""
        monkeypatch.setenv("MIST_HOST", "h")
        monkeypatch.setenv("MIST_APITOKEN", "t")
        with (
            patch.object(ARPCommandManager, "_trigger_command", return_value=None) as trigger,
            patch.object(ARPCommandManager, "_listen_for_output") as listen,
        ):
            ARPCommandManager.execute("s1", "d1")
        trigger.assert_called_once()
        listen.assert_not_called()

    def test_happy_path_streams_via_listener(self, fake_mh, monkeypatch):
        """Successful trigger dispatches to _listen_for_output with a target bundle."""
        monkeypatch.setenv("MIST_HOST", "api.mist.example")
        monkeypatch.setenv("MIST_APITOKEN", "tok")
        with (
            patch.object(ARPCommandManager, "_trigger_command", return_value="sess-9"),
            patch.object(ARPCommandManager, "_listen_for_output") as listen,
        ):
            ARPCommandManager.execute("s1", "d1")
        (target,), _ = listen.call_args
        assert isinstance(target, WebSocketStreamTarget)
        assert target.mist_host == "api-ws.mist.example"
        assert target.session_id == "sess-9"


class TestTriggerCommand:
    """Cover REST trigger success and failure branches."""

    def test_returns_session_id_on_200(self, caplog):
        """Extract the ``session`` field when the POST succeeds."""
        response = MagicMock(status_code=200)
        response.json.return_value = {"session": "abc"}
        caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
        with patch.object(arp_mod.requests, "post", return_value=response) as post:
            result = ARPCommandManager._trigger_command("h", "t", "s", "d")
        assert result == "abc"
        post.assert_called_once()
        assert any("ARP command triggered" in r.getMessage() for r in caplog.records)

    def test_returns_none_and_prints_body_on_failure(self, caplog):
        """Non-200 responses log the body and return None."""
        response = MagicMock(status_code=500, text="boom")
        caplog.set_level(logging.ERROR, logger=_LOGGER_NAME)
        with patch.object(arp_mod.requests, "post", return_value=response):
            result = ARPCommandManager._trigger_command("h", "t", "s", "d")
        assert result is None
        messages = [r.getMessage() for r in caplog.records]
        assert any("Failed to trigger" in m for m in messages)
        assert any("boom" in m for m in messages)


class TestBuildWsSubscribe:
    """Cover the WebSocket subscribe-payload builder."""

    def test_builds_url_headers_and_payload(self):
        """Return the wss URL, Authorization header, and subscribe topic."""
        target = _target()
        url, headers, payload = ARPCommandManager._build_ws_subscribe(target)
        assert url == "wss://api-ws.mist.example/api-ws/v1/stream"
        assert headers == ["Authorization: Token tok"]
        assert payload == {"subscribe": "/sites/site-1/devices/dev-1/cmd"}


class TestMakeWsCallbacks:
    """Cover the four WebSocket callbacks and their state mutations."""

    def test_on_message_updates_state_via_handle_message(self):
        """on_message delegates to _handle_message and updates timestamp/buffer."""
        target = _target()
        state = {"last_message_time": 0.0, "buffer": "old"}
        output_lines: list[str] = []
        with patch.object(ARPCommandManager, "_handle_message", return_value=(1234.5, "new")) as handler:
            callbacks = ARPCommandManager._make_ws_callbacks(target, state, output_lines, False, {"subscribe": "topic"})
            callbacks["on_message"](MagicMock(), "raw-frame")
        handler.assert_called_once_with("raw-frame", target.session_id, "old", output_lines, False)
        assert state == {"last_message_time": 1234.5, "buffer": "new"}

    def test_on_close_delegates_to_handle_close(self):
        """on_close forwards output_lines and debug flag to _handle_close."""
        target = _target()
        lines = ["a"]
        with patch.object(ARPCommandManager, "_handle_close") as handler:
            callbacks = ARPCommandManager._make_ws_callbacks(
                target, {"last_message_time": 0.0, "buffer": ""}, lines, True, {}
            )
            callbacks["on_close"](MagicMock(), "code", "reason")
        handler.assert_called_once_with(lines, True)

    def test_on_error_logs_error(self, caplog):
        """on_error emits an error-level log entry."""
        target = _target()
        callbacks = ARPCommandManager._make_ws_callbacks(
            target, {"last_message_time": 0.0, "buffer": ""}, [], False, {}
        )
        with caplog.at_level(logging.ERROR):
            callbacks["on_error"](MagicMock(), RuntimeError("bang"))
        assert any("WebSocket error" in r.getMessage() for r in caplog.records)

    def test_on_open_sends_subscribe_payload(self, caplog):
        """on_open sends the JSON-serialized subscribe payload on the socket."""
        target = _target()
        subscribe = {"subscribe": "/topic"}
        callbacks = ARPCommandManager._make_ws_callbacks(
            target, {"last_message_time": 0.0, "buffer": ""}, [], False, subscribe
        )
        ws = MagicMock()
        with caplog.at_level(logging.INFO):
            callbacks["on_open"](ws)
        ws.send.assert_called_once_with(json.dumps(subscribe))


class TestPollWsIdle:
    """Cover the idle-timeout polling loop's branches."""

    def test_closes_on_idle_after_output(self):
        """Break out of the loop when idle-after-output threshold is crossed."""
        ws = MagicMock()
        ws.keep_running = False
        state = {"last_message_time": 0.0, "buffer": ""}
        output_lines = ["line"]
        # time.time yields: start=100, loop_iter1=101 (elapsed 1 < 30, idle=101 > 3), close.
        with (
            patch.object(arp_mod.time, "time", side_effect=[100.0, 101.0, 101.0]),
            patch.object(arp_mod.time, "sleep"),
        ):
            ARPCommandManager._poll_ws_idle(ws, state, output_lines, timeout=30, idle_timeout=3)
        ws.close.assert_called_once()

    def test_hard_timeout_closes_when_still_running(self, caplog):
        """When the loop expires with ws.keep_running still True, close+warn."""
        ws = MagicMock()
        ws.keep_running = True
        state = {"last_message_time": 100.0, "buffer": ""}
        # First time() = start (100); second returns 200 (> timeout 30) → exit loop.
        with (
            patch.object(arp_mod.time, "time", side_effect=[100.0, 200.0]),
            patch.object(arp_mod.time, "sleep"),
            caplog.at_level(logging.WARNING),
        ):
            ARPCommandManager._poll_ws_idle(ws, state, output_lines=[], timeout=30, idle_timeout=3)
        ws.close.assert_called_once()
        assert any("Timeout waiting" in r.getMessage() for r in caplog.records)

    def test_skips_idle_close_when_no_output_yet(self):
        """Idle threshold does not fire while output_lines is empty."""
        ws = MagicMock()
        ws.keep_running = False
        # loop iter1: elapsed 1 < 30 → check idle (huge), but output empty → no close.
        # loop iter2: elapsed 999 > timeout → exit.
        with (
            patch.object(arp_mod.time, "time", side_effect=[100.0, 101.0, 101.0, 9999.0]),
            patch.object(arp_mod.time, "sleep"),
        ):
            ARPCommandManager._poll_ws_idle(ws, {"last_message_time": 0.0, "buffer": ""}, [], 30, 3)
        ws.close.assert_not_called()


class TestListenForOutput:
    """Cover the WebSocket app wiring and thread launch."""

    def test_builds_app_starts_thread_and_polls(self, fake_mh):
        """Wire the WebSocketApp with callbacks, launch a thread, and poll."""
        target = _target()
        fake_app = MagicMock()
        fake_thread = MagicMock()
        with (
            patch.object(arp_mod.websocket, "WebSocketApp", return_value=fake_app) as app_cls,
            patch.object(arp_mod.threading, "Thread", return_value=fake_thread) as thread_cls,
            patch.object(ARPCommandManager, "_poll_ws_idle") as poll,
        ):
            ARPCommandManager._listen_for_output(target, timeout=5, idle_timeout=1, debug=False)
        app_cls.assert_called_once()
        thread_cls.assert_called_once_with(target=fake_app.run_forever)
        fake_thread.start.assert_called_once()
        poll.assert_called_once()

    def test_debug_mode_enables_trace(self, fake_mh):
        """debug=True calls websocket.enableTrace before building the app."""
        target = _target()
        with (
            patch.object(arp_mod.websocket, "enableTrace") as trace,
            patch.object(arp_mod.websocket, "WebSocketApp", return_value=MagicMock()),
            patch.object(arp_mod.threading, "Thread", return_value=MagicMock()),
            patch.object(ARPCommandManager, "_poll_ws_idle"),
        ):
            ARPCommandManager._listen_for_output(target, debug=True)
        trace.assert_called_once_with(True)


class TestDrainBufferToLines:
    """Cover the newline-split buffer drainer."""

    def test_drains_complete_lines_and_returns_tail(self):
        """Complete lines are appended and the trailing partial is returned."""
        lines: list[str] = []
        remainder = ARPCommandManager._drain_buffer_to_lines("a\nbb\ncc", lines)
        assert lines == ["a", "bb"]
        assert remainder == "cc"

    def test_returns_buffer_unchanged_without_newline(self):
        """No newline means no split happens."""
        lines: list[str] = []
        remainder = ARPCommandManager._drain_buffer_to_lines("partial", lines)
        assert lines == []
        assert remainder == "partial"


class TestParseWsArpPayload:
    """Cover successful nested-JSON unwrap paths."""

    def test_parses_string_inside_string_inside_json(self):
        """Both middle and inner payloads may be JSON strings — decode both."""
        inner = {"session": "sess", "raw": "ROW\n"}
        message = json.dumps({"data": json.dumps({"data": json.dumps(inner)})})
        result = ARPCommandManager._parse_ws_arp_payload(message)
        assert result == inner

    def test_parses_when_middle_data_is_dict(self):
        """Middle data may already be a dict rather than a JSON string."""
        inner = {"session": "s", "raw": "R"}
        # Outer.data is a string that decodes to {"data": {...dict...}}.
        message = json.dumps({"data": json.dumps({"data": inner})})
        assert ARPCommandManager._parse_ws_arp_payload(message) == inner


class TestSafeParseWsArpPayload:
    """Cover JSON/key/generic error branches of the safe wrapper."""

    def test_returns_inner_on_success(self):
        """Passthrough on success."""
        inner = {"session": "s", "raw": "R"}
        message = json.dumps({"data": json.dumps({"data": inner})})
        assert ARPCommandManager._safe_parse_ws_arp_payload(message) == inner

    def test_swallows_json_decode_error(self, caplog):
        """Malformed JSON logs an error and returns None."""
        with caplog.at_level(logging.ERROR):
            assert ARPCommandManager._safe_parse_ws_arp_payload("not-json") is None
        assert any("JSON decode error" in r.getMessage() for r in caplog.records)

    def test_swallows_key_error(self, caplog):
        """KeyError from inner parsing logs a warning and returns None."""
        with (
            patch.object(ARPCommandManager, "_parse_ws_arp_payload", side_effect=KeyError("k")),
            caplog.at_level(logging.WARNING),
        ):
            assert ARPCommandManager._safe_parse_ws_arp_payload("{}") is None
        assert any("missing expected key" in r.getMessage() for r in caplog.records)

    def test_swallows_generic_exception(self, caplog):
        """Any other exception logs an error and returns None."""
        with (
            patch.object(ARPCommandManager, "_parse_ws_arp_payload", side_effect=RuntimeError("x")),
            caplog.at_level(logging.ERROR),
        ):
            assert ARPCommandManager._safe_parse_ws_arp_payload("{}") is None
        assert any("Unexpected error" in r.getMessage() for r in caplog.records)


class TestHandleMessage:
    """Cover per-frame parse+dispatch decisions."""

    def test_returns_early_on_parse_failure(self):
        """Parse failure keeps buffer + timestamp intact (via time.time stub)."""
        with (
            patch.object(ARPCommandManager, "_safe_parse_ws_arp_payload", return_value=None),
            patch.object(arp_mod.time, "time", return_value=42.0),
        ):
            ts, buf = ARPCommandManager._handle_message("frame", "s", "existing", [])
        assert (ts, buf) == (42.0, "existing")

    def test_ignores_frame_from_different_session(self):
        """Session mismatch does not append output."""
        payload = {"session": "other", "raw": "IGNORED"}
        lines: list[str] = []
        with (
            patch.object(ARPCommandManager, "_safe_parse_ws_arp_payload", return_value=payload),
            patch.object(arp_mod.time, "time", return_value=7.0),
        ):
            ts, buf = ARPCommandManager._handle_message("frame", "mine", "b", lines)
        assert (ts, buf, lines) == (7.0, "b", [])

    def test_appends_matching_session_output(self):
        """Matching session drains completed lines into output_lines."""
        payload = {"session": "mine", "raw": "row1\nrow2\npart"}
        lines: list[str] = []
        with (
            patch.object(ARPCommandManager, "_safe_parse_ws_arp_payload", return_value=payload),
            patch.object(arp_mod.time, "time", return_value=9.0),
        ):
            ts, buf = ARPCommandManager._handle_message("frame", "mine", "", lines)
        assert ts == 9.0
        assert lines == ["row1", "row2"]
        assert buf == "part"

    def test_debug_mode_logs_raw_and_size(self, caplog):
        """debug=True emits both the raw-frame trace and processed-size trace."""
        payload = {"session": "s", "raw": "x"}
        with (
            patch.object(ARPCommandManager, "_safe_parse_ws_arp_payload", return_value=payload),
            patch.object(arp_mod.time, "time", return_value=0.0),
            caplog.at_level(logging.DEBUG),
        ):
            ARPCommandManager._handle_message("raw-frame", "s", "", [], debug=True)
        messages = [r.getMessage() for r in caplog.records]
        assert any("raw message received" in m for m in messages)
        assert any("Processed WebSocket data" in m for m in messages)


class TestHandleClose:
    """Cover empty and populated close paths."""

    def test_reports_no_output_when_empty(self, caplog):
        """Empty output_lines logs at WARNING, without CSV export."""
        caplog.set_level(logging.WARNING, logger=_LOGGER_NAME)
        with (
            patch.object(ARPCommandManager, "_save_output") as save,
            patch.object(ARPCommandManager, "_export_to_csv") as export,
        ):
            ARPCommandManager._handle_close([])
        save.assert_not_called()
        export.assert_not_called()
        assert any("No ARP output received" in r.getMessage() for r in caplog.records)

    def test_processes_populated_output(self, capsys):
        """Non-empty output triggers save + export + render."""
        with (
            patch.object(ARPCommandManager, "_save_output") as save,
            patch.object(ARPCommandManager, "_export_to_csv") as export,
            patch.object(ARPCommandManager, "_render_arp_table") as render,
        ):
            ARPCommandManager._handle_close(["a", "b"], debug=True)
        save.assert_called_once()
        export.assert_called_once_with("arp_output_raw.txt")
        render.assert_called_once_with("a\nb", True)


class TestRenderArpTable:
    """Cover parse/emit dispatch and the early empty-rows return."""

    def test_returns_early_when_no_rows_parsed(self):
        """Skip table construction when parse yields no rows."""
        with (
            patch.object(ARPCommandManager, "_parse_arp_rows", return_value=([], 0)),
            patch.object(ARPCommandManager, "_emit_arp_table") as emit,
        ):
            ARPCommandManager._render_arp_table("", False)
        emit.assert_not_called()

    def test_builds_and_emits_table_for_populated_rows(self):
        """Populated rows are emitted through the table helper."""
        rows = [["a", "b"], ["c", "d"]]
        with (
            patch.object(ARPCommandManager, "_parse_arp_rows", return_value=(rows, 2)),
            patch.object(ARPCommandManager, "_emit_arp_table") as emit,
        ):
            ARPCommandManager._render_arp_table("x", True)
        emit.assert_called_once()
        _, row_count, debug = emit.call_args[0]
        assert row_count == 2 and debug is True


class TestParseArpRows:
    """Cover row splitting/padding and column-width detection."""

    def test_splits_and_pads_rows(self):
        """Tab-split rows and pad short rows to the widest row's width."""
        compiled = "a\tb\tc\nd\te\n\n"
        rows, max_cols = ARPCommandManager._parse_arp_rows(compiled)
        assert max_cols == 3
        assert rows == [["a", "b", "c"], ["d", "e", ""]]

    def test_empty_output_returns_zero_columns(self):
        """Empty compiled output yields no rows and max_cols=0."""
        rows, max_cols = ARPCommandManager._parse_arp_rows("")
        assert rows == [] and max_cols == 0


class TestPadRows:
    """Cover in-place row padding."""

    def test_pads_short_rows(self):
        """Rows shorter than max_cols receive trailing empty strings."""
        rows = [["a"], ["b", "c"]]
        ARPCommandManager._pad_rows(rows, 3)
        assert rows == [["a", "", ""], ["b", "c", ""]]

    def test_leaves_full_width_rows_unchanged(self):
        """Full-width rows are not modified."""
        rows = [["a", "b"]]
        ARPCommandManager._pad_rows(rows, 2)
        assert rows == [["a", "b"]]


class TestEmitArpTable:
    """Cover debug vs non-debug reporting."""

    def test_debug_prints_full_table(self, caplog):
        """debug=True logs the table string and its formatted contents."""
        table = MagicMock()
        table.get_string.return_value = "TABLE"
        caplog.set_level(logging.DEBUG, logger=_LOGGER_NAME)
        ARPCommandManager._emit_arp_table(table, 3, True)
        # Just verify the debug branch was taken.
        table.get_string.assert_called_once()

    def test_non_debug_reports_row_count(self, caplog):
        """debug=False emits a summary line only."""
        table = MagicMock()
        caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
        ARPCommandManager._emit_arp_table(table, 5, False)
        assert any("5 rows" in r.getMessage() for r in caplog.records)
        table.get_string.assert_not_called()


class TestSaveOutput:
    """Cover save success and exception paths."""

    def test_writes_file_when_path_resolvable(self, fake_mh, tmp_path, caplog):
        """Compiled output is written to the resolved path."""
        target_path = tmp_path / "arp_output_raw.txt"
        fake_mh.FilePathUtils.get_csv_path.return_value = str(target_path)
        with caplog.at_level(logging.INFO):
            ARPCommandManager._save_output("hello", filename="arp_output_raw.txt")
        assert target_path.read_text(encoding="utf-8") == "hello"

    def test_logs_error_when_write_fails(self, fake_mh, caplog):
        """Filesystem failure surfaces as an error log, not a raise."""
        fake_mh.FilePathUtils.get_csv_path.side_effect = OSError("nope")
        with caplog.at_level(logging.ERROR):
            ARPCommandManager._save_output("hello")
        assert any("Failed to save" in r.getMessage() for r in caplog.records)


class TestExtractArpColumns:
    """Cover column extraction from raw lines."""

    def test_strips_and_drops_empty_columns(self):
        """Tab-split then strip; drop empty tokens."""
        assert ARPCommandManager._extract_arp_columns(" a \t\t b \tc") == ["a", "b", "c"]


class TestSplitArpTextIntoDatasets:
    """Cover the Total-marker split into two datasets."""

    def test_splits_on_total_marker(self):
        """Rows before the marker go to dataset1; rows after go to dataset2."""
        raw = "a\tb\nc\td\nTotal: 2\ne\tf\ng\th"
        ds1, ds2 = ARPCommandManager._split_arp_text_into_datasets(raw)
        assert ds1 == [["a", "b"], ["c", "d"]]
        assert ds2 == [["e", "f"], ["g", "h"]]

    def test_empty_input_yields_empty_datasets(self):
        """No lines means both datasets remain empty."""
        assert ARPCommandManager._split_arp_text_into_datasets("") == ([], [])

    def test_all_rows_go_to_first_dataset_without_marker(self):
        """No Total marker keeps everything in dataset1."""
        raw = "a\tb\nc\td"
        ds1, ds2 = ARPCommandManager._split_arp_text_into_datasets(raw)
        assert ds1 == [["a", "b"], ["c", "d"]]
        assert ds2 == []


class TestWriteDatasetCsv:
    """Cover CSV write + user-facing count line."""

    def test_writes_rows_and_reports_count(self, tmp_path, caplog):
        """CSV file gets the expected rows and the logger announces the count."""
        path = tmp_path / "out.csv"
        caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
        ARPCommandManager._write_dataset_csv(str(path), [["a", "b"], ["c", "d"]])
        contents = path.read_text(encoding="utf-8").replace("\r", "")
        assert contents == "a,b\nc,d\n"
        assert any("Saved 2 rows" in r.getMessage() for r in caplog.records)


class TestExportToCsv:
    """Cover the two-CSV export orchestrator plus exception fallback."""

    def test_reads_source_and_writes_two_csvs(self, fake_mh, tmp_path, capsys):
        """Source txt drives dataset split and produces two CSV files."""
        raw = "a\tb\nTotal\nc\td"
        src = tmp_path / "arp_output_raw.txt"
        src.write_text(raw, encoding="utf-8")
        csv1 = tmp_path / "d1.csv"
        csv2 = tmp_path / "d2.csv"

        def _path_for(name):
            return {
                "arp_output_raw.txt": str(src),
                "arp_dataset1.csv": str(csv1),
                "arp_dataset2.csv": str(csv2),
            }[name]

        fake_mh.FilePathUtils.get_csv_path.side_effect = _path_for
        ARPCommandManager._export_to_csv()
        assert csv1.read_text(encoding="utf-8").replace("\r", "") == "a,b\n"
        assert csv2.read_text(encoding="utf-8").replace("\r", "") == "c,d\n"

    def test_prints_failure_on_exception(self, fake_mh, caplog):
        """Any exception during export becomes a user-facing failure log line."""
        fake_mh.FilePathUtils.get_csv_path.side_effect = RuntimeError("boom")
        caplog.set_level(logging.ERROR, logger=_LOGGER_NAME)
        ARPCommandManager._export_to_csv()
        assert any("Failed to export ARP output to CSV" in r.getMessage() for r in caplog.records)
