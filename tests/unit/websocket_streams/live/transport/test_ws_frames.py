"""Tests for the issue #3671 WebSocket frame decoder."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # FrameReader needs a close event for close-origin decisions.

from src.websocket_streams.live.transport.frames import (  # Test frame contracts.
    ConnectionClosed,
    FrameDecoder,
    FrameReader,
    SubscribeError,
)
from websocket import ABNF  # Tests use concrete opcode values.


class CloseFrameSocket:
    """A minimal socket that returns one close frame."""

    def __init__(self, payload: bytes) -> None:
        """Store the close payload."""
        self._payload = payload  # The frame reader reads this payload once.

    def settimeout(self, _timeout: float) -> None:
        """Accept the timeout value."""

    def recv_data(self, control_frame: bool = False) -> tuple[int, bytes]:
        """Return one close frame."""
        assert control_frame is True  # FrameReader must request control frames.
        return ABNF.OPCODE_CLOSE, self._payload  # Return the configured close payload.


class TestFrameDecoder:
    """Verify stream frame decoding."""

    def test_event_removes_nul_from_binary_json(self) -> None:
        """Remove NUL bytes before JSON decoding."""
        frame = b'\x00{"event": "data", "channel": "c", "data": "{}"}\x00'  # Binary frames can contain NUL bytes.
        expected = {"event": "data", "channel": "c", "data": "{}"}  # The decoded event should be clean.
        assert FrameDecoder.event(frame) == expected  # NUL bytes must not break JSON decoding.

    def test_event_wraps_text_that_is_not_json(self) -> None:
        """Wrap non-JSON text as raw text."""
        assert FrameDecoder.event("plain text") == {"raw": "plain text"}  # Match the SDK fallback shape.

    def test_event_wraps_empty_body(self) -> None:
        """Wrap an empty text frame as raw text."""
        assert FrameDecoder.event("") == {"raw": ""}  # Empty frames stay observable.

    def test_data_payload_decodes_json_text(self) -> None:
        """Decode JSON text inside a data event."""
        event = {"event": "data", "data": '{"session": "one", "raw": "show \\u2603"}'}  # Unicode stays JSON text.
        expected = {"session": "one", "raw": "show \u2603"}  # JSON decoding must preserve Unicode.
        assert FrameDecoder.data_payload(event) == expected  # The inner payload is decoded.

    def test_data_payload_keeps_malformed_json_text(self) -> None:
        """Keep malformed JSON text unchanged."""
        event = {"event": "data", "data": "{broken"}  # Malformed data can appear in edge tests.
        assert FrameDecoder.data_payload(event) == "{broken"  # The decoder must not hide malformed text.

    def test_data_payload_keeps_non_text_value(self) -> None:
        """Return non-text data unchanged."""
        event = {"event": "data", "data": {"value": 1}}  # Some callers already decode data.
        assert FrameDecoder.data_payload(event) == {"value": 1}  # Already-decoded data stays unchanged.


class TestTransportErrors:
    """Verify transport error fields."""

    def test_connection_closed_fields(self) -> None:
        """Store the close code and drop marker."""
        error = ConnectionClosed(code=1000, dropped=False)  # Build a clean local close error.
        assert error.code == 1000  # The close code is visible.
        assert error.dropped is False  # The local close is not a drop.

    def test_subscribe_error_fields(self) -> None:
        """Store subscription error details."""
        error = SubscribeError("/channel", "timeout")  # Build a timeout error.
        assert error.channel == "/channel"  # The channel is visible.
        assert error.detail == "timeout"  # The detail is visible.

    def test_empty_close_frame_reports_no_status_code_1005(self) -> None:
        """Map an empty close frame to RFC 6455 code 1005."""
        socket = CloseFrameSocket(b"")  # Build a close frame with no status payload.
        reader = FrameReader(socket, threading.Event(), lambda: 1.0, 20.0)  # Build a reader around it.
        try:  # The close frame should raise the structured close error.
            reader.read(0.1)  # Read the close frame.
        except ConnectionClosed as error:
            assert error.code == 1005  # Empty close frames report no status received.
        else:
            raise AssertionError("ConnectionClosed was not raised.")  # A close frame must end the read.

    def test_two_byte_close_frame_keeps_status_code(self) -> None:
        """Keep a two-byte close status code."""
        socket = CloseFrameSocket((1000).to_bytes(2, "big"))  # Build a normal close frame.
        reader = FrameReader(socket, threading.Event(), lambda: 1.0, 20.0)  # Build a reader around it.
        try:  # The close frame should keep its status code.
            reader.read(0.1)  # Read the close frame.
        except ConnectionClosed as error:
            assert error.code == 1000  # The close code must be preserved.
        else:
            raise AssertionError("ConnectionClosed was not raised.")  # A close frame must end the read.
