"""Route incoming WebSocket messages to the shared command_results buffer.

Replaces the body of WebSocketManager._on_message. Each helper keeps
CC <= 5 and preserves every print / log line the user sees.
"""

from __future__ import annotations  # WHY: PEP 563 postponed evaluation of type hints.

import json  # WHY: Parse JSON payloads from the WebSocket stream.
import logging  # WHY: Shared logger from the manager.
import threading  # WHY: Lock around command_results.
from collections.abc import Callable  # WHY: Handler signature alias source.
from dataclasses import dataclass  # WHY: Frozen slotted holder for router collaborators.
from typing import Any  # WHY: Generic message dicts.

_EVENT_KEY = "event"  # WHY: Route dispatch key on the outer envelope.
_CHANNEL_KEY = "channel"  # WHY: Subscription and data-event channel key.
_DATA_KEY = "data"  # WHY: Payload wrapper key inside both envelopes.
_SESSION_KEY = "session"  # WHY: Session identifier field inside a data payload.
_RAW_KEY = "raw"  # WHY: Raw command output field inside a data payload.
_EVT_SUB = "channel_subscribed"  # WHY: Subscription confirmation event name.
_EVT_DATA = "data"  # WHY: Data event name shared with the wrapped payload.
_DBG = "[DEBUG]"  # WHY: Preserved verbatim debug-print prefix.
_PKT = "[PACKET]"  # WHY: Preserved verbatim packet-trace prefix.

_HandlerT = Callable[[dict[str, Any]], None]  # WHY: Dispatch-table handler signature alias.

_SKIP: Any = object()  # WHY: Sentinel signaling _unwrap_payload wants routing aborted.


@dataclass(frozen=True, slots=True)  # WHY: Immutable, slotted holder minimizes ctx cost.
class _RouterCtx:  # WHY: Bundle manager-owned collaborators into one immutable holder.
    """Manager-owned collaborators packed into a single immutable holder."""

    results: dict[str, Any]  # WHY: Session -> segments map owned by the manager.
    lock: threading.Lock  # WHY: Guards mutations of the results map.
    confirmed: set[str]  # WHY: Set of channel names with confirmed subscriptions.
    logger: logging.Logger  # WHY: Emits parity trace preserved verbatim.
    debug: bool  # WHY: Verbose print toggle propagated from the manager.


class MessageRouter:  # WHY: Public API preserved for WebSocketManager collaborator wiring.
    """Parse incoming WebSocket frames and store command output by session."""

    def __init__(
        self,
        command_results: dict[str, Any],
        results_lock: threading.Lock,
        confirmed_subscriptions: set[str],
        logger: logging.Logger,
        debug_mode: bool,
    ) -> None:  # WHY: Preserve original five-argument constructor for the manager.
        """Bundle manager-owned collaborators into an immutable ``_RouterCtx``.

        Why:
            The original ``WebSocketManager._on_message`` passed five loose
            arguments each call. Packing them into a frozen dataclass makes
            attribute access cheaper (slots) and prevents accidental mutation
            by dispatch handlers while preserving the constructor signature
            expected by manager-side wiring.

        Args:
            command_results: Session → response-segments map owned by the
                manager. Mutated by handlers under ``results_lock``.
            results_lock: Threading lock that serializes writes to
                ``command_results``.
            confirmed_subscriptions: Set of channel names that have received
                a confirmation frame. Used to gate downstream dispatch.
            logger: Logger used for parity trace lines (preserved verbatim
                from the pre-extraction ``_on_message`` code path).
            debug_mode: Verbose-trace toggle propagated from the manager.
        """
        self._ctx = _RouterCtx(  # WHY: Pack manager state into one immutable holder.
            results=command_results,
            lock=results_lock,
            confirmed=confirmed_subscriptions,
            logger=logger,
            debug=debug_mode,
        )
        self._dispatch: dict[str, _HandlerT] = _build_dispatch(self._ctx)  # WHY: Table-driven routing.

    def route(self, message: Any) -> None:  # WHY: Single public entry retained for _on_message.
        """Parse one WebSocket message and dispatch by event type."""
        ctx = self._ctx  # WHY: Local alias trims repeated attribute access.
        ctx.logger.info("Routing incoming WebSocket message")  # WHY: Pre-action log preserved.
        try:  # WHY: Broad-except parity with original _on_message behavior.
            _trace_raw(ctx, message)  # WHY: Verbose raw-message trace.
            message_data = _parse(ctx, message)  # WHY: Parse to dict or skip.
            if message_data is None:  # WHY: Skip signal from _parse aborts routing.
                return  # WHY: Unparseable message already logged inside _parse.
            _trace_packet(ctx, message_data)  # WHY: Verbatim [PACKET] block.
            event = message_data.get(_EVENT_KEY)  # WHY: Event type drives dispatch.
            handler = self._dispatch.get(event)  # WHY: Table lookup avoids elif chain.
            if handler is not None:  # WHY: Known event -> invoke matched handler.
                handler(message_data)  # WHY: Invoke matched closure handler.
                return  # WHY: Successful dispatch exits the try block.
            ctx.logger.debug("Unhandled message event type: %s", event)  # WHY: Unknown event.
        except Exception as message_error:  # WHY: Match original broad except.
            _log_route_error(ctx, message, message_error)  # WHY: Preserve verbatim error trace.
        ctx.logger.debug("Routing complete")  # WHY: Post-action log preserved.


def _build_dispatch(ctx: _RouterCtx) -> dict[str, _HandlerT]:  # WHY: Closure factory packs ctx.
    """Return event->handler dispatch table with ctx captured by closure."""
    return {  # WHY: Closures pack ctx so handlers match _HandlerT signature.
        _EVT_SUB: lambda md: _handle_subscription(ctx, md),  # WHY: Subscription-confirmed path.
        _EVT_DATA: lambda md: _handle_data(ctx, md),  # WHY: Data-event storage path.
    }


def _log_route_error(ctx: _RouterCtx, message: Any, err: Exception) -> None:  # WHY: Except-arm log helper.
    """Emit the verbatim error trace preserved from the original except block."""
    ctx.logger.error("Error processing WebSocket message: %s", err)  # WHY: Error surfaced.
    ctx.logger.debug("Exception details:", exc_info=True)  # WHY: Stack trace at debug.
    ctx.logger.debug("Problematic message: %s", repr(message))  # WHY: Preserve payload for triage.
    ctx.logger.debug("Message type: %s", type(message))  # WHY: Type context aids diagnosis.


def _trace_raw(ctx: _RouterCtx, message: Any) -> None:  # WHY: Emit verbatim [DEBUG] raw trace.
    """Emit the raw-message trace preserved verbatim from the original."""
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Raw WebSocket message received: {repr(message)} (type: {type(message)})")  # WHY: Verbatim.
    ctx.logger.debug("Raw WebSocket message received: %s (type: %s)", repr(message), type(message))  # WHY: Log.


def _parse(ctx: _RouterCtx, message: Any) -> dict[str, Any] | None:  # WHY: Dispatch by message type.
    """Parse a string or dict message into a dict. Return None to skip."""
    if isinstance(message, str):  # WHY: JSON-string path handled separately.
        return _parse_string(ctx, message)  # WHY: Delegate JSON-decode path.
    if isinstance(message, dict):  # WHY: Pre-parsed dict path handled separately.
        return _accept_dict(ctx, message)  # WHY: Trace and return dict as-is.
    _log_unexpected_type(ctx, message)  # WHY: Warn about neither-string-nor-dict payloads.
    return None  # WHY: Caller treats None as skip signal.


def _accept_dict(ctx: _RouterCtx, message: dict[str, Any]) -> dict[str, Any]:  # WHY: Dict passthrough.
    """Return an already-parsed dict message after tracing it."""
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Received dict message: {message}")  # WHY: Preserve verbatim trace.
    ctx.logger.debug("Received dict message: %s", message)  # WHY: Preserve verbatim trace.
    return message  # WHY: Dict passes through without JSON decoding.


def _log_unexpected_type(ctx: _RouterCtx, message: Any) -> None:  # WHY: Warn about wrong-type payload.
    """Warn when the incoming message is neither a string nor a dict."""
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Unexpected message type: {type(message)}, content: {repr(message)}")  # WHY: Verbatim.
    ctx.logger.warning("Unexpected message type: %s, content: %s", type(message), repr(message))  # WHY: Log.


def _parse_string(ctx: _RouterCtx, message: str) -> dict[str, Any] | None:  # WHY: JSON string path.
    """Decode JSON string. Return None on decode failure or non-dict result."""
    data = _json_load(ctx, message)  # WHY: Isolate try/except in a helper.
    if data is _SKIP:  # WHY: Decode failed and was already logged.
        return None  # WHY: Decode already logged inside _json_load.
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Successfully parsed JSON message: {data}")  # WHY: Preserve verbatim trace.
    ctx.logger.debug("Successfully parsed JSON message: %s", data)  # WHY: Preserve verbatim trace.
    if not isinstance(data, dict):  # WHY: Non-dict decode result is unusable.
        _log_non_dict(ctx, data)  # WHY: Emit type-mismatch warning.
        return None  # WHY: Non-dict payload is not routable.
    return data  # WHY: Successfully decoded dict.


def _json_load(ctx: _RouterCtx, message: str) -> Any:  # WHY: Isolate decode try/except.
    """Return json.loads result, or _SKIP sentinel after logging decode errors."""
    try:  # WHY: Isolate JSON decode from surrounding routing logic.
        return json.loads(message)  # WHY: Standard library JSON decode.
    except json.JSONDecodeError as json_error:  # WHY: Malformed JSON is logged, not raised.
        _log_json_error(ctx, message, json_error)  # WHY: Preserve verbatim decode-error trace.
        return _SKIP  # WHY: Sentinel bubbles abort upward.


def _log_json_error(ctx: _RouterCtx, message: str, err: json.JSONDecodeError) -> None:  # WHY: Decode log.
    """Emit the verbatim decode-failure trace preserved from the original."""
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Failed to parse JSON message: {err}")  # WHY: Preserve verbatim trace.
        print(f"{_DBG} Raw message content: {repr(message)}")  # WHY: Preserve verbatim trace.
    ctx.logger.warning("Failed to parse JSON message: %s", err)  # WHY: Preserve log line.
    ctx.logger.debug("Raw message content: %s", repr(message))  # WHY: Preserve log line.


def _log_non_dict(ctx: _RouterCtx, data: Any) -> None:  # WHY: Type-mismatch log helper.
    """Log a type mismatch when the decoded JSON is not a dict."""
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Message data is not a dict after parsing: {type(data)}")  # WHY: Verbatim.
    ctx.logger.error("Message data is not a dict after parsing: %s", type(data))  # WHY: Preserve log.


def _trace_packet(ctx: _RouterCtx, message_data: dict[str, Any]) -> None:  # WHY: [PACKET] block emitter.
    """Verbatim [PACKET] block preserved from the original implementation."""
    if not ctx.debug:  # WHY: Packet trace is debug-only.
        return  # WHY: Guard-clause skips packet trace entirely when debug off.
    _print_packet_header(message_data)  # WHY: Emit event/channel lines.
    if _DATA_KEY not in message_data:  # WHY: No body to trace when data field absent.
        print(f"{_PKT}   No data field in message")  # WHY: Preserve verbatim trace.
        return  # WHY: No data field means no body to trace.
    _print_packet_body(message_data[_DATA_KEY])  # WHY: Emit data-type and content trace.


def _print_packet_header(message_data: dict[str, Any]) -> None:  # WHY: Emit packet header lines.
    """Emit the verbatim event/channel header lines of a packet trace."""
    print(f"{_PKT} WebSocket packet details:")  # WHY: Preserve verbatim trace.
    print(f"{_PKT}   Event: {message_data.get(_EVENT_KEY, 'unknown')}")  # WHY: Preserve verbatim.
    print(f"{_PKT}   Channel: {message_data.get(_CHANNEL_KEY, 'unknown')}")  # WHY: Preserve verbatim.


def _print_packet_body(data_content: Any) -> None:  # WHY: Emit packet body lines.
    """Emit the packet trace for a data payload, verbatim from the original."""
    print(f"{_PKT}   Data type: {type(data_content)}")  # WHY: Preserve verbatim trace.
    if not isinstance(data_content, dict):  # WHY: Non-dict body prints repr and stops.
        print(f"{_PKT}   Data content: {repr(data_content)}")  # WHY: Non-dict fallback trace.
        return  # WHY: Non-dict payload has no keys to enumerate.
    print(f"{_PKT}   Data keys: {list(data_content.keys())}")  # WHY: Preserve verbatim trace.
    if _SESSION_KEY in data_content:  # WHY: Only trace session key when present.
        print(f"{_PKT}   Session ID: {data_content[_SESSION_KEY]}")  # WHY: Preserve trace.
    if _RAW_KEY in data_content:  # WHY: Only trace raw content when present.
        _print_packet_raw(data_content[_RAW_KEY])  # WHY: Length + repr lines.


def _print_packet_raw(raw_content: Any) -> None:  # WHY: Emit raw-content packet lines.
    """Emit the raw-content packet trace lines preserved verbatim."""
    print(f"{_PKT}   Raw content length: {len(str(raw_content))} chars")  # WHY: Preserve trace.
    print(f"{_PKT}   Raw content: {repr(raw_content)}")  # WHY: Preserve trace.


def _handle_subscription(ctx: _RouterCtx, message_data: dict[str, Any]) -> None:  # WHY: Sub handler.
    """Record a confirmed channel subscription."""
    channel = message_data.get(_CHANNEL_KEY)  # WHY: Subscription target key.
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Channel subscription confirmed: {channel}")  # WHY: Preserve verbatim.
    ctx.logger.info("Channel subscription confirmed: %s", channel)  # WHY: Preserve log line.
    if channel:  # WHY: Defensive - only track non-empty channel names.
        ctx.confirmed.add(channel)  # WHY: Track only non-empty channel names.


def _handle_data(ctx: _RouterCtx, message_data: dict[str, Any]) -> None:  # WHY: Data event handler.
    """Extract session/payload from a data event and store it."""
    channel = message_data.get(_CHANNEL_KEY, "")  # WHY: Diagnostic label only.
    data_payload = _unwrap_payload(ctx, message_data.get(_DATA_KEY, {}))  # WHY: Normalize wrapper.
    if data_payload is _SKIP:  # WHY: Sentinel means unwrap aborted upstream.
        return  # WHY: Sentinel means routing aborted upstream.
    _trace_data_event(ctx, channel, data_payload)  # WHY: Verbatim [DEBUG] block.
    session_id = data_payload.get(_SESSION_KEY) if isinstance(data_payload, dict) else None  # WHY: Session key.
    _trace_session(ctx, channel, session_id, data_payload)  # WHY: Session diagnostic trace.
    if not session_id:  # WHY: Cannot store a segment without a session key.
        _log_missing_session(ctx, message_data, data_payload)  # WHY: Warn on absent session id.
        return  # WHY: Cannot store without a session key.
    _store_segment(ctx, session_id, data_payload)  # WHY: Append segment under lock.


def _trace_data_event(ctx: _RouterCtx, channel: str, data_payload: Any) -> None:  # WHY: Data trace block.
    """Emit the verbatim [DEBUG] block describing the data event."""
    if not ctx.debug:  # WHY: Trace is debug-only.
        return  # WHY: Guard-clause skips trace when debug disabled.
    print(f"{_DBG} Processing data event from channel: {channel}")  # WHY: Preserve verbatim.
    print(f"{_DBG} Data payload type: {type(data_payload)}")  # WHY: Preserve verbatim.
    print(f"{_DBG} Data payload content: {repr(data_payload)}")  # WHY: Preserve verbatim.


def _log_missing_session(ctx: _RouterCtx, message_data: dict[str, Any], data_payload: Any) -> None:  # WHY: Warn.
    """Warn about a data event that lacks a session identifier."""
    ctx.logger.warning("Received data event without session ID. Full message: %s", message_data)  # WHY: Log.
    ctx.logger.warning("Data payload: %s", data_payload)  # WHY: Preserve verbatim log line.


def _unwrap_payload(ctx: _RouterCtx, data_payload: Any) -> Any:  # WHY: Normalize wrapper shapes.
    """Unwrap JSON-string payloads and nested event structures."""
    if isinstance(data_payload, str):  # WHY: String path decodes first.
        data_payload = _unwrap_string(ctx, data_payload)  # WHY: Decode string wrapper.
        if data_payload is _SKIP:  # WHY: Non-JSON string aborts routing upstream.
            return _SKIP  # WHY: Bubble abort signal to caller.
    if isinstance(data_payload, dict) and data_payload.get(_EVENT_KEY) == _EVT_DATA:  # WHY: Nested envelope.
        return _unwrap_nested(ctx, data_payload)  # WHY: Extract inner data field.
    return data_payload  # WHY: Already normalized payload.


def _unwrap_string(ctx: _RouterCtx, data_payload: str) -> Any:  # WHY: Decode nested JSON strings.
    """Parse a JSON-string data field. Return _SKIP if not JSON."""
    try:  # WHY: Isolate nested JSON decode.
        parsed = json.loads(data_payload)  # WHY: Standard library JSON decode.
    except json.JSONDecodeError:  # WHY: Non-JSON string is only logged, not raised.
        _log_non_json_data(ctx, data_payload)  # WHY: Preserve verbatim not-JSON trace.
        return _SKIP  # WHY: Bubble abort signal to caller.
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Parsed nested JSON in data field: {parsed}")  # WHY: Preserve verbatim.
    ctx.logger.debug("Parsed nested JSON in data field: %s", parsed)  # WHY: Preserve log line.
    return parsed  # WHY: Successfully decoded nested JSON.


def _log_non_json_data(ctx: _RouterCtx, data_payload: str) -> None:  # WHY: Warn non-JSON strings.
    """Emit the verbatim trace for a data field that is a non-JSON string."""
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Data field is string but not JSON: {data_payload}")  # WHY: Preserve verbatim.
    ctx.logger.warning("Data field is string but not JSON: %s", data_payload)  # WHY: Preserve log.


def _unwrap_nested(ctx: _RouterCtx, data_payload: dict[str, Any]) -> Any:  # WHY: Collapse nested wrap.
    """Extract the inner 'data' field of a nested event=data structure."""
    actual_data = data_payload.get(_DATA_KEY, {})  # WHY: Collapse nested envelope.
    if ctx.debug:  # WHY: Guard-clause skips print when debug disabled.
        print(f"{_DBG} Found nested event structure, extracting actual data: {actual_data}")  # WHY: Verbatim.
    ctx.logger.debug("Found nested event structure, extracting actual data: %s", actual_data)  # WHY: Log.
    return actual_data  # WHY: Inner data becomes the effective payload.


def _trace_session(ctx: _RouterCtx, channel: str, session_id: str | None, data_payload: Any) -> None:  # WHY: Trace.
    """Verbatim per-data-event diagnostic trace."""
    if ctx.debug:  # WHY: Debug print block is optional.
        _print_session_debug(channel, session_id, data_payload)  # WHY: Preserve verbatim.
    ctx.logger.debug("Processing data event - channel: %s, session: %s", channel, session_id)  # WHY: Log.
    ctx.logger.debug("Final data payload: %s", data_payload)  # WHY: Preserve verbatim log line.


def _print_session_debug(channel: str, session_id: str | None, data_payload: Any) -> None:  # WHY: Debug block.
    """Emit the [DEBUG] session-diagnostic block preserved verbatim."""
    print(f"{_DBG} Processing data event - channel: {channel}, session: {session_id}")  # WHY: Verbatim.
    print(f"{_DBG} Final data payload: {data_payload}")  # WHY: Preserve verbatim.
    if session_id:  # WHY: Two-branch trace based on whether session id resolved.
        print(f"{_DBG} Session ID extracted: {session_id}")  # WHY: Preserve verbatim.
    else:  # WHY: Absent-session branch preserves original trace line.
        print(f"{_DBG} No session ID found in data payload")  # WHY: Preserve verbatim.


def _store_segment(ctx: _RouterCtx, session_id: str, data_payload: dict[str, Any]) -> None:  # WHY: Append.
    """Append a message segment to the session list under lock."""
    with ctx.lock:  # WHY: Serialize appends across threads.
        bucket = ctx.results.setdefault(session_id, [])  # WHY: Init list on first message.
        if not bucket and ctx.debug:  # WHY: First-segment debug trace preserves original message.
            print(f"{_DBG} Initialized new result list for session: {session_id}")  # WHY: Verbatim.
        bucket.append(data_payload)  # WHY: Store segment in arrival order.
        if ctx.debug:  # WHY: Full post-store debug block preserved verbatim.
            _print_store_debug(session_id, data_payload, len(bucket))  # WHY: Verbatim trace.
        ctx.logger.debug("Stored command result for session %s: %s", session_id, data_payload)  # WHY: Log.
        ctx.logger.debug("Command result segment received for session: %s", session_id)  # WHY: Log.
        ctx.logger.debug("Total segments for session: %s", len(bucket))  # WHY: Preserve log line.


def _print_store_debug(session_id: str, data_payload: dict[str, Any], current_count: int) -> None:  # WHY: Store trace.
    """Emit the [DEBUG] block preserved verbatim after storing a segment."""
    print(f"{_DBG} Stored message #{current_count} for session {session_id}")  # WHY: Verbatim.
    if _RAW_KEY in data_payload:  # WHY: Only trace raw content when present in stored message.
        print(f"{_DBG} Raw data in stored message: {repr(data_payload[_RAW_KEY])}")  # WHY: Verbatim.
    print(f"{_DBG} Complete stored message: {data_payload}")  # WHY: Preserve verbatim trace.
