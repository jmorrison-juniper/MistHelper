"""Tests for the issue #3671 WebSocket frame decoder."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The cut-frame test proves that the frame is not valid JSON.
import threading  # FrameReader needs a close event for close-origin decisions.
import time  # The TLS buffer test measures the read wait.
from socket import socket as RealSocket  # The TLS buffer fake waits on a real idle socket.
from socket import socketpair  # select needs a real socket that holds no data.

import pytest  # The cut-frame test asserts the parser error.

from src.websocket_streams.live.transport.frames import (  # Test frame contracts.
    ConnectionClosed,
    FrameDecoder,
    FrameRead,
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


class TimeoutTrapSocket(CloseFrameSocket):
    """A socket fake that fails if a read changes the socket timeout."""

    def settimeout(self, _timeout: float) -> None:
        """Fail if FrameReader changes the shared socket timeout."""
        raise AssertionError("FrameReader changed the socket timeout.")  # Shell writes need one stable timeout.


class PendingRawSocket:
    """A raw TLS socket fake with held TLS bytes and an empty kernel buffer."""

    def __init__(self, idle_socket: RealSocket, pending_count: int) -> None:
        """Store the idle socket and the held byte count."""
        self._idle_socket = idle_socket  # select waits on this real socket, which never holds data.
        self._pending_count = pending_count  # The TLS layer reports this count from pending().

    def fileno(self) -> int:
        """Return the file number of the idle socket."""
        return self._idle_socket.fileno()  # select needs a real file number.

    def pending(self) -> int:
        """Return the count of decrypted bytes that no read took."""
        return self._pending_count  # A real ssl.SSLSocket reports its held bytes here.


class TlsBufferedSocket:
    """A websocket-client fake whose TLS layer holds one shell frame."""

    def __init__(self, raw_socket: PendingRawSocket) -> None:
        """Store the raw socket where FrameReader waits."""
        self.sock = raw_socket  # websocket-client keeps the TCP or TLS socket in this attribute.

    def recv_data(self, control_frame: bool = False) -> tuple[int, bytes]:
        """Return the shell frame that the TLS layer held."""
        assert control_frame is True  # FrameReader must request control frames.
        return ABNF.OPCODE_BINARY, b"\x00switch> "  # The second frame of one TLS record.


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

    def test_event_wraps_cut_json_frame_as_raw_text(self) -> None:
        """Wrap a cut JSON frame as raw text."""
        frame = '{"event": "data", "data": '  # A dropped connection can cut a frame in the middle.
        with pytest.raises(json.JSONDecodeError):  # Prove that the frame is malformed JSON.
            json.loads(frame)  # The standard parser refuses the cut frame.
        assert FrameDecoder.event(frame) == {"raw": frame}  # The decoder keeps the cut frame visible as text.

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

    def test_read_does_not_change_socket_timeout(self) -> None:
        """Leave the shared socket timeout unchanged while reading."""
        socket = TimeoutTrapSocket((1000).to_bytes(2, "big"))  # Fail if read calls settimeout.
        reader = FrameReader(socket, threading.Event(), lambda: 1.0, 20.0)  # Build a reader around it.
        try:  # The close frame should still be read.
            reader.read(0.1)  # Read without mutating the socket timeout.
        except ConnectionClosed as error:
            assert error.code == 1000  # The test reached the close frame.
        else:
            raise AssertionError("ConnectionClosed was not raised.")  # A close frame must end the read.


class TestTlsBufferedRead:
    """Verify that a frame held by the TLS layer does not wait for network data."""

    def test_held_tls_frame_reads_without_a_network_wait(self) -> None:
        """Read a frame at once when select sees no data but TLS holds bytes."""
        idle_socket, peer_socket = socketpair()  # The peer never sends, so select sees no data.
        with idle_socket, peer_socket:  # Close both sockets after the test.
            reader = FrameReader(
                TlsBufferedSocket(PendingRawSocket(idle_socket, 9)), threading.Event(), time.monotonic, 20.0
            )  # The TLS layer holds the 9 bytes of one shell frame.
            started = time.monotonic()  # Measure the read wait.
            frame = reader.read(3.0)  # Before the repair, select waited the full 3 seconds.
            elapsed = time.monotonic() - started  # The wait that the operator sees in the terminal.
        assert frame == FrameRead(ABNF.OPCODE_BINARY, b"\x00switch> ")  # The held frame reaches the caller.
        assert elapsed < 1.0  # The read must not wait for more network data.

    def test_empty_tls_buffer_still_waits_on_the_socket(self) -> None:
        """Keep the socket wait when the TLS layer holds no bytes."""
        idle_socket, peer_socket = socketpair()  # The peer never sends, so select sees no data.
        with idle_socket, peer_socket:  # Close both sockets after the test.
            reader = FrameReader(
                TlsBufferedSocket(PendingRawSocket(idle_socket, 0)), threading.Event(), time.monotonic, 20.0
            )  # The TLS layer holds no bytes.
            frame = reader.read(0.05)  # select times out because no data arrives.
        assert frame is None  # A quiet socket gives no frame and no false read.
