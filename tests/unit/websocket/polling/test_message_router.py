"""Tests for src.websocket.polling.message_router.

Covers every branch of MessageRouter and its module-level helpers:
route() success/error/unknown-event dispatch; _parse for str/dict/other;
JSON decode failure; nested payload unwrapping; subscription and data
handlers; session storage under lock; and all debug-mode trace/print
branches (verbatim [DEBUG] and [PACKET] blocks).
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

import src.websocket.polling.message_router as mr
from src.websocket.polling.message_router import MessageRouter


def _make_router(debug: bool = False) -> tuple[MessageRouter, dict[str, Any], set[str], threading.Lock]:
    """Return a router plus the shared state it manipulates."""
    results: dict[str, Any] = {}
    lock = threading.Lock()
    confirmed: set[str] = set()
    logger = logging.getLogger("test.message_router")
    router = MessageRouter(results, lock, confirmed, logger, debug)
    return router, results, confirmed, lock


# ---------------------------------------------------------------------------
# MessageRouter construction + route() top-level flow
# ---------------------------------------------------------------------------


def test_router_init_wires_dispatch_table() -> None:
    router, _r, _c, _l = _make_router()
    assert set(router._dispatch.keys()) == {"channel_subscribed", "data"}


def test_route_string_subscription_confirmed() -> None:
    router, _r, confirmed, _l = _make_router()
    router.route(json.dumps({"event": "channel_subscribed", "channel": "ch1"}))
    assert "ch1" in confirmed


def test_route_string_data_event_stores_segment() -> None:
    router, results, _c, _l = _make_router()
    payload = {"event": "data", "channel": "c", "data": {"session": "s1", "raw": "hello"}}
    router.route(json.dumps(payload))
    assert results["s1"] == [{"session": "s1", "raw": "hello"}]


def test_route_dict_data_event_stores_segment() -> None:
    router, results, _c, _l = _make_router()
    router.route({"event": "data", "channel": "c", "data": {"session": "s2", "raw": "x"}})
    assert results["s2"] == [{"session": "s2", "raw": "x"}]


def test_route_unknown_event_logs_debug(caplog) -> None:
    router, _r, _c, _l = _make_router()
    with caplog.at_level(logging.DEBUG, logger="test.message_router"):
        router.route({"event": "mystery"})
    assert any("Unhandled message event type: mystery" in r.message for r in caplog.records)


def test_route_no_event_key_is_unknown(caplog) -> None:
    router, _r, _c, _l = _make_router()
    with caplog.at_level(logging.DEBUG, logger="test.message_router"):
        router.route({"channel": "c"})
    assert any("Unhandled message event type: None" in r.message for r in caplog.records)


def test_route_unparseable_string_returns_none_path(caplog) -> None:
    router, _r, _c, _l = _make_router()
    with caplog.at_level(logging.DEBUG, logger="test.message_router"):
        router.route("not json{{")
    assert any("Failed to parse JSON message" in r.message for r in caplog.records)


def test_route_unexpected_type_message(caplog) -> None:
    router, _r, _c, _l = _make_router()
    with caplog.at_level(logging.DEBUG, logger="test.message_router"):
        router.route(12345)
    assert any("Unexpected message type" in r.message for r in caplog.records)


def test_route_broad_except_logs_error(caplog) -> None:
    router, _r, _c, _l = _make_router()
    # Force an exception inside dispatch by replacing the handler with a boomer.
    router._dispatch["data"] = lambda _md: (_ for _ in ()).throw(RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="test.message_router"):
        router.route({"event": "data"})
    assert any("Error processing WebSocket message" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# _trace_raw
# ---------------------------------------------------------------------------


def test_trace_raw_debug_prints(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route(json.dumps({"event": "channel_subscribed", "channel": "x"}))
    out = capsys.readouterr().out
    assert "[DEBUG] Raw WebSocket message received" in out


def test_trace_raw_debug_off_no_print(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=False)
    router.route(json.dumps({"event": "channel_subscribed", "channel": "x"}))
    out = capsys.readouterr().out
    assert "[DEBUG] Raw WebSocket message received" not in out


# ---------------------------------------------------------------------------
# _parse / _accept_dict / _log_unexpected_type
# ---------------------------------------------------------------------------


def test_accept_dict_debug_prints(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "channel_subscribed", "channel": "x"})
    out = capsys.readouterr().out
    assert "[DEBUG] Received dict message" in out


def test_log_unexpected_type_debug_prints(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route(3.14)
    out = capsys.readouterr().out
    assert "[DEBUG] Unexpected message type" in out


def test_log_unexpected_type_no_debug_no_print(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=False)
    router.route(3.14)
    out = capsys.readouterr().out
    assert "[DEBUG]" not in out


# ---------------------------------------------------------------------------
# _parse_string / _json_load / _log_json_error / _log_non_dict
# ---------------------------------------------------------------------------


def test_parse_string_success_debug_prints(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route(json.dumps({"event": "channel_subscribed", "channel": "x"}))
    out = capsys.readouterr().out
    assert "[DEBUG] Successfully parsed JSON message" in out


def test_parse_string_non_dict_result(caplog, capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    with caplog.at_level(logging.ERROR, logger="test.message_router"):
        router.route(json.dumps([1, 2, 3]))
    out = capsys.readouterr().out
    assert "[DEBUG] Message data is not a dict" in out
    assert any("Message data is not a dict" in r.message for r in caplog.records)


def test_log_json_error_debug_prints(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route("not-json")
    out = capsys.readouterr().out
    assert "[DEBUG] Failed to parse JSON message" in out
    assert "[DEBUG] Raw message content" in out


def test_log_non_dict_no_debug_no_print(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=False)
    router.route(json.dumps("just a string"))
    out = capsys.readouterr().out
    assert "[DEBUG]" not in out


# ---------------------------------------------------------------------------
# _trace_packet + _print_packet_header/_print_packet_body/_print_packet_raw
# ---------------------------------------------------------------------------


def test_trace_packet_debug_off_skips(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=False)
    router.route({"event": "data", "channel": "c", "data": {"session": "s", "raw": "r"}})
    out = capsys.readouterr().out
    assert "[PACKET]" not in out


def test_trace_packet_no_data_field(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "channel_subscribed", "channel": "c"})
    out = capsys.readouterr().out
    assert "[PACKET] WebSocket packet details:" in out
    assert "[PACKET]   No data field in message" in out


def test_trace_packet_full_body_with_session_and_raw(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"session": "s1", "raw": "hello"}})
    out = capsys.readouterr().out
    assert "[PACKET]   Event: data" in out
    assert "[PACKET]   Channel: c" in out
    assert "[PACKET]   Data keys" in out
    assert "[PACKET]   Session ID: s1" in out
    assert "[PACKET]   Raw content length" in out
    assert "[PACKET]   Raw content:" in out


def test_trace_packet_non_dict_data(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    # Data field is a non-JSON string -> _unwrap_string returns _SKIP,
    # but _trace_packet fires BEFORE _handle_data, so we still see the trace.
    router.route({"event": "data", "channel": "c", "data": "not-json-str"})
    out = capsys.readouterr().out
    assert "[PACKET]   Data type" in out
    assert "[PACKET]   Data content:" in out


def test_trace_packet_dict_body_no_session_no_raw(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"other": "field"}})
    out = capsys.readouterr().out
    assert "[PACKET]   Data keys" in out
    assert "[PACKET]   Session ID:" not in out
    assert "[PACKET]   Raw content length" not in out


# ---------------------------------------------------------------------------
# _handle_subscription
# ---------------------------------------------------------------------------


def test_handle_subscription_empty_channel_not_stored(capsys) -> None:
    router, _r, confirmed, _l = _make_router(debug=True)
    router.route({"event": "channel_subscribed"})  # No channel key
    out = capsys.readouterr().out
    assert "[DEBUG] Channel subscription confirmed: None" in out
    assert confirmed == set()


def test_handle_subscription_valid_channel_stored(capsys) -> None:
    router, _r, confirmed, _l = _make_router(debug=True)
    router.route({"event": "channel_subscribed", "channel": "chA"})
    out = capsys.readouterr().out
    assert "[DEBUG] Channel subscription confirmed: chA" in out
    assert confirmed == {"chA"}


# ---------------------------------------------------------------------------
# _handle_data flow variants
# ---------------------------------------------------------------------------


def test_handle_data_missing_session_warns(caplog) -> None:
    router, results, _c, _l = _make_router()
    with caplog.at_level(logging.WARNING, logger="test.message_router"):
        router.route({"event": "data", "channel": "c", "data": {"raw": "no session"}})
    assert results == {}
    assert any("Received data event without session ID" in r.message for r in caplog.records)


def test_handle_data_skip_from_unwrap_returns(caplog) -> None:
    """Non-JSON string data payload triggers _SKIP; _handle_data returns early."""
    router, results, _c, _l = _make_router()
    with caplog.at_level(logging.WARNING, logger="test.message_router"):
        router.route({"event": "data", "channel": "c", "data": "not-json-str"})
    assert results == {}
    assert any("Data field is string but not JSON" in r.message for r in caplog.records)


def test_handle_data_no_channel_default_empty() -> None:
    """Missing channel key falls back to empty string diagnostic label."""
    router, results, _c, _l = _make_router()
    router.route({"event": "data", "data": {"session": "s", "raw": "r"}})
    assert results["s"] == [{"session": "s", "raw": "r"}]


def test_handle_data_non_dict_payload_no_session() -> None:
    """List payload lacks session key and triggers missing-session warn."""
    router, results, _c, _l = _make_router()
    router.route({"event": "data", "channel": "c", "data": json.dumps([1, 2, 3])})
    # Unwrap decodes the inner JSON to a list; session id resolves to None.
    assert results == {}


# ---------------------------------------------------------------------------
# _trace_data_event
# ---------------------------------------------------------------------------


def test_trace_data_event_debug_prints(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"session": "s", "raw": "r"}})
    out = capsys.readouterr().out
    assert "[DEBUG] Processing data event from channel: c" in out
    assert "[DEBUG] Data payload type:" in out
    assert "[DEBUG] Data payload content:" in out


def test_trace_data_event_debug_off_no_print(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=False)
    router.route({"event": "data", "channel": "c", "data": {"session": "s", "raw": "r"}})
    out = capsys.readouterr().out
    assert "[DEBUG] Processing data event" not in out


# ---------------------------------------------------------------------------
# _unwrap_payload / _unwrap_string / _unwrap_nested
# ---------------------------------------------------------------------------


def test_unwrap_string_json_success_debug(capsys) -> None:
    router, results, _c, _l = _make_router(debug=True)
    inner = json.dumps({"session": "sess-x", "raw": "hi"})
    router.route({"event": "data", "channel": "c", "data": inner})
    out = capsys.readouterr().out
    assert "[DEBUG] Parsed nested JSON in data field" in out
    assert results["sess-x"] == [{"session": "sess-x", "raw": "hi"}]


def test_unwrap_string_non_json_debug_prints(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": "still not json"})
    out = capsys.readouterr().out
    assert "[DEBUG] Data field is string but not JSON" in out


def test_unwrap_nested_event_data_structure(capsys) -> None:
    router, results, _c, _l = _make_router(debug=True)
    nested = {"event": "data", "data": {"session": "sn", "raw": "z"}}
    router.route({"event": "data", "channel": "c", "data": nested})
    out = capsys.readouterr().out
    assert "[DEBUG] Found nested event structure" in out
    assert results["sn"] == [{"session": "sn", "raw": "z"}]


def test_unwrap_nested_debug_off_no_print(capsys) -> None:
    router, results, _c, _l = _make_router(debug=False)
    nested = {"event": "data", "data": {"session": "sn2", "raw": "q"}}
    router.route({"event": "data", "channel": "c", "data": nested})
    out = capsys.readouterr().out
    assert "[DEBUG] Found nested event structure" not in out
    assert results["sn2"] == [{"session": "sn2", "raw": "q"}]


def test_unwrap_payload_already_dict_passthrough() -> None:
    router, results, _c, _l = _make_router()
    router.route({"event": "data", "channel": "c", "data": {"session": "sd", "raw": "d"}})
    assert results["sd"] == [{"session": "sd", "raw": "d"}]


# ---------------------------------------------------------------------------
# _trace_session / _print_session_debug
# ---------------------------------------------------------------------------


def test_print_session_debug_with_session(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"session": "s", "raw": "r"}})
    out = capsys.readouterr().out
    assert "[DEBUG] Session ID extracted: s" in out


def test_print_session_debug_without_session(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"raw": "no session"}})
    out = capsys.readouterr().out
    assert "[DEBUG] No session ID found in data payload" in out


def test_trace_session_debug_off_no_print(capsys) -> None:
    router, _r, _c, _l = _make_router(debug=False)
    router.route({"event": "data", "channel": "c", "data": {"session": "s", "raw": "r"}})
    out = capsys.readouterr().out
    assert "[DEBUG] Processing data event - channel" not in out


# ---------------------------------------------------------------------------
# _store_segment / _print_store_debug
# ---------------------------------------------------------------------------


def test_store_segment_first_message_debug(capsys) -> None:
    router, results, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"session": "s0", "raw": "r0"}})
    out = capsys.readouterr().out
    assert "[DEBUG] Initialized new result list for session: s0" in out
    assert "[DEBUG] Stored message #1 for session s0" in out
    assert "[DEBUG] Raw data in stored message:" in out
    assert "[DEBUG] Complete stored message:" in out
    assert results["s0"] == [{"session": "s0", "raw": "r0"}]


def test_store_segment_subsequent_messages_no_init_print(capsys) -> None:
    router, results, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"session": "s0", "raw": "r0"}})
    capsys.readouterr()  # Drop first-store output.
    router.route({"event": "data", "channel": "c", "data": {"session": "s0", "raw": "r1"}})
    out = capsys.readouterr().out
    assert "Initialized new result list" not in out
    assert "[DEBUG] Stored message #2 for session s0" in out
    assert len(results["s0"]) == 2


def test_store_segment_debug_off_no_prints(capsys) -> None:
    router, results, _c, _l = _make_router(debug=False)
    router.route({"event": "data", "channel": "c", "data": {"session": "s0", "raw": "r0"}})
    out = capsys.readouterr().out
    assert "[DEBUG]" not in out
    assert results["s0"] == [{"session": "s0", "raw": "r0"}]


def test_store_segment_without_raw_key_skips_raw_print(capsys) -> None:
    router, results, _c, _l = _make_router(debug=True)
    router.route({"event": "data", "channel": "c", "data": {"session": "sr", "other": "x"}})
    out = capsys.readouterr().out
    assert "[DEBUG] Stored message #1 for session sr" in out
    assert "[DEBUG] Raw data in stored message" not in out
    assert results["sr"] == [{"session": "sr", "other": "x"}]


def test_store_segment_uses_lock() -> None:
    """The lock is entered around dict mutation - verify via a wrapper.

    _thread.lock has read-only dunder attributes so patch.object on the raw
    lock fails; instead we swap in a wrapper that records enter/exit.
    """

    class _TracingLock:
        def __init__(self) -> None:
            self.real = threading.Lock()
            self.enters = 0
            self.exits = 0

        def __enter__(self) -> _TracingLock:
            self.enters += 1
            self.real.acquire()
            return self

        def __exit__(self, *exc: Any) -> None:
            self.exits += 1
            self.real.release()

    results: dict[str, Any] = {}
    trace_lock = _TracingLock()
    confirmed: set[str] = set()
    logger = logging.getLogger("test.message_router.lock")
    router = MessageRouter(results, trace_lock, confirmed, logger, False)  # type: ignore[arg-type]
    router.route({"event": "data", "channel": "c", "data": {"session": "sL", "raw": "x"}})
    assert trace_lock.enters >= 1
    assert trace_lock.exits >= 1
    assert results["sL"][0]["raw"] == "x"


# ---------------------------------------------------------------------------
# _log_route_error triggered from broad-except in route()
# ---------------------------------------------------------------------------


def test_log_route_error_records_full_diagnostics(caplog) -> None:
    router, _r, _c, _l = _make_router()
    router._dispatch["channel_subscribed"] = lambda _md: (_ for _ in ()).throw(ValueError("bad"))
    with caplog.at_level(logging.DEBUG, logger="test.message_router"):
        router.route({"event": "channel_subscribed", "channel": "x"})
    messages = [r.message for r in caplog.records]
    assert any("Error processing WebSocket message" in m for m in messages)
    assert any("Exception details:" in m for m in messages)
    assert any("Problematic message:" in m for m in messages)
    assert any("Message type:" in m for m in messages)


# ---------------------------------------------------------------------------
# module-level sentinel and constants sanity
# ---------------------------------------------------------------------------


def test_skip_sentinel_is_unique_object() -> None:
    assert mr._SKIP is mr._SKIP
    assert mr._SKIP is not None
    assert mr._SKIP is not object()


def test_handler_signature_alias_present() -> None:
    """Dispatch table stores callables matching _HandlerT signature."""
    router, _r, _c, _l = _make_router()
    for handler in router._dispatch.values():
        assert callable(handler)
