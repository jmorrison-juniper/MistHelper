"""Route incoming WebSocket messages to the shared command_results buffer.

Replaces the body of WebSocketManager._on_message. Each helper keeps
CC <= 10 and preserves every print / log line the user sees.
"""

from __future__ import annotations

import json  # Parses JSON payloads from the WebSocket
import logging  # Shared logger from the manager
import threading  # Lock around command_results
from typing import Any  # Generic message dicts


class MessageRouter:
    """Parse incoming WebSocket frames and store command output by session."""

    def __init__(
        self,
        command_results: dict[str, Any],
        results_lock: threading.Lock,
        confirmed_subscriptions: set[str],
        logger: logging.Logger,
        debug_mode: bool,
    ) -> None:
        self._results = command_results  # Manager-owned session->segments map
        self._lock = results_lock  # Lock guarding _results
        self._confirmed = confirmed_subscriptions  # Manager-owned subscription set
        self._logger = logger  # Manager logger
        self._debug = debug_mode  # Verbose print toggle

    def route(self, message: Any) -> None:
        """Parse one WebSocket message and dispatch by event type."""
        self._logger.info("Routing incoming WebSocket message")  # Pre-action log
        try:
            self._trace_raw(message)  # Verbose raw-message trace
            message_data = self._parse(message)  # Parse to dict or skip
            if message_data is None:
                return
            self._trace_packet(message_data)  # Verbatim [PACKET] block
            event = message_data.get("event")  # Event type drives dispatch
            if event == "channel_subscribed":
                self._handle_subscription(message_data)
                return
            if event == "data":
                self._handle_data(message_data)
                return
            self._logger.debug(f"Unhandled message event type: {event}")  # Unknown event
        except Exception as message_error:  # Match original broad except
            self._logger.error(f"Error processing WebSocket message: {message_error}")
            self._logger.debug("Exception details:", exc_info=True)
            self._logger.debug(f"Problematic message: {repr(message)}")
            self._logger.debug(f"Message type: {type(message)}")
        self._logger.debug("Routing complete")  # Post-action log

    def _trace_raw(self, message: Any) -> None:
        """Emit the raw-message trace preserved verbatim from the original."""
        if self._debug:
            print(f"[DEBUG] Raw WebSocket message received: {repr(message)} (type: {type(message)})")
        self._logger.debug(f"Raw WebSocket message received: {repr(message)} (type: {type(message)})")

    def _parse(self, message: Any) -> dict[str, Any] | None:
        """Parse a string or dict message into a dict; return None to skip."""
        if isinstance(message, str):
            return self._parse_string(message)
        if isinstance(message, dict):
            if self._debug:
                print(f"[DEBUG] Received dict message: {message}")
            self._logger.debug(f"Received dict message: {message}")
            return message
        if self._debug:
            print(f"[DEBUG] Unexpected message type: {type(message)}, content: {repr(message)}")
        self._logger.warning(f"Unexpected message type: {type(message)}, content: {repr(message)}")
        return None

    def _parse_string(self, message: str) -> dict[str, Any] | None:
        """Decode JSON string; return None on decode failure or non-dict result."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError as json_error:
            if self._debug:
                print(f"[DEBUG] Failed to parse JSON message: {json_error}")
                print(f"[DEBUG] Raw message content: {repr(message)}")
            self._logger.warning(f"Failed to parse JSON message: {json_error}")
            self._logger.debug(f"Raw message content: {repr(message)}")
            return None
        if self._debug:
            print(f"[DEBUG] Successfully parsed JSON message: {data}")
        self._logger.debug(f"Successfully parsed JSON message: {data}")
        if not isinstance(data, dict):
            if self._debug:
                print(f"[DEBUG] Message data is not a dict after parsing: {type(data)}")
            self._logger.error(f"Message data is not a dict after parsing: {type(data)}")
            return None
        return data

    def _trace_packet(self, message_data: dict[str, Any]) -> None:
        """Verbatim [PACKET] block preserved from the original implementation."""
        if not self._debug:
            return
        print("[PACKET] WebSocket packet details:")
        print(f"[PACKET]   Event: {message_data.get('event', 'unknown')}")
        print(f"[PACKET]   Channel: {message_data.get('channel', 'unknown')}")
        if "data" not in message_data:
            print("[PACKET]   No data field in message")
            return
        data_content = message_data["data"]
        print(f"[PACKET]   Data type: {type(data_content)}")
        if not isinstance(data_content, dict):
            print(f"[PACKET]   Data content: {repr(data_content)}")
            return
        print(f"[PACKET]   Data keys: {list(data_content.keys())}")
        if "session" in data_content:
            print(f"[PACKET]   Session ID: {data_content['session']}")
        if "raw" in data_content:
            raw_content = data_content["raw"]
            print(f"[PACKET]   Raw content length: {len(str(raw_content))} chars")
            print(f"[PACKET]   Raw content: {repr(raw_content)}")

    def _handle_subscription(self, message_data: dict[str, Any]) -> None:
        """Record a confirmed channel subscription."""
        channel = message_data.get("channel")
        if self._debug:
            print(f"[DEBUG] Channel subscription confirmed: {channel}")
        self._logger.info(f"Channel subscription confirmed: {channel}")
        if channel:  # Defensive — only track non-empty channel names
            self._confirmed.add(channel)

    def _handle_data(self, message_data: dict[str, Any]) -> None:
        """Extract session/payload from a data event and store it."""
        channel = message_data.get("channel", "")
        data_payload = self._unwrap_payload(message_data.get("data", {}))
        if data_payload is _SKIP:  # Sentinel used by _unwrap_payload to abort routing
            return
        if self._debug:
            print(f"[DEBUG] Processing data event from channel: {channel}")
            print(f"[DEBUG] Data payload type: {type(data_payload)}")
            print(f"[DEBUG] Data payload content: {repr(data_payload)}")
        session_id = data_payload.get("session") if isinstance(data_payload, dict) else None
        self._trace_session(channel, session_id, data_payload)
        if not session_id:
            self._logger.warning(f"Received data event without session ID. Full message: {message_data}")
            self._logger.warning(f"Data payload: {data_payload}")
            return
        self._store_segment(session_id, data_payload)

    def _unwrap_payload(self, data_payload: Any) -> Any:
        """Unwrap JSON-string payloads and nested event structures."""
        if isinstance(data_payload, str):
            try:
                data_payload = json.loads(data_payload)
                if self._debug:
                    print(f"[DEBUG] Parsed nested JSON in data field: {data_payload}")
                self._logger.debug(f"Parsed nested JSON in data field: {data_payload}")
            except json.JSONDecodeError:
                if self._debug:
                    print(f"[DEBUG] Data field is string but not JSON: {data_payload}")
                self._logger.warning(f"Data field is string but not JSON: {data_payload}")
                return _SKIP  # Signal caller to abort routing
        if isinstance(data_payload, dict) and data_payload.get("event") == "data":
            actual_data = data_payload.get("data", {})
            if self._debug:
                print(f"[DEBUG] Found nested event structure, extracting actual data: {actual_data}")
            self._logger.debug(f"Found nested event structure, extracting actual data: {actual_data}")
            data_payload = actual_data
        return data_payload

    def _trace_session(self, channel: str, session_id: str | None, data_payload: Any) -> None:
        """Verbatim per-data-event diagnostic trace."""
        if self._debug:
            print(f"[DEBUG] Processing data event - channel: {channel}, session: {session_id}")
            print(f"[DEBUG] Final data payload: {data_payload}")
            if session_id:
                print(f"[DEBUG] Session ID extracted: {session_id}")
            else:
                print("[DEBUG] No session ID found in data payload")
        self._logger.debug(f"Processing data event - channel: {channel}, session: {session_id}")
        self._logger.debug(f"Final data payload: {data_payload}")

    def _store_segment(self, session_id: str, data_payload: dict[str, Any]) -> None:
        """Append a message segment to the session list under lock."""
        with self._lock:
            bucket = self._results.setdefault(session_id, [])  # Init list on first message
            if not bucket and self._debug:
                print(f"[DEBUG] Initialized new result list for session: {session_id}")
            bucket.append(data_payload)
            if self._debug:
                current_count = len(bucket)
                print(f"[DEBUG] Stored message #{current_count} for session {session_id}")
                if "raw" in data_payload:
                    print(f"[DEBUG] Raw data in stored message: {repr(data_payload['raw'])}")
                print(f"[DEBUG] Complete stored message: {data_payload}")
            self._logger.debug(f"Stored command result for session {session_id}: {data_payload}")
            self._logger.debug(f"Command result segment received for session: {session_id}")
            self._logger.debug(f"Total segments for session: {len(bucket)}")


# Sentinel used internally by MessageRouter to signal "skip this message".
_SKIP: Any = object()
