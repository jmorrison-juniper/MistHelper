"""Tests for live transport frame reading and keepalive behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # FrameReader needs a close event.
import time  # TLS buffer tests measure the read wait.
from socket import socket as RealSocket  # The TLS fake wraps a real idle socket.
from socket import socketpair  # Select needs a real socket with no data.

import pytest  # Close frame tests assert structured errors.

from src.websocket_streams.live.transport.runtime.reader.contracts import ConnectionClosed, FrameRead
from src.websocket_streams.live.transport.runtime.reader.frame_reader import FrameReader
from websocket import ABNF  # Tests use concrete opcode values.


class FrameSocket:
    """Return one configured frame and record keepalive actions."""

    def __init__(self, opcode: int, payload: bytes) -> None:
        """Store the frame and action counters."""
        self._frame = (opcode, payload)  # The reader receives this frame once.
        self.pings = 0  # Keepalive tests count ping calls.
        self.closed = 0  # Dead-peer tests count close calls.

    def recv_data(self, control_frame: bool = False) -> tuple[int, bytes]:
        """Return the configured frame."""
        assert control_frame is True  # The reader must request control frames.
        return self._frame  # Return the configured opcode and payload.

    def ping(self) -> None:
        """Record one keepalive ping."""
        self.pings += 1  # The test observes ping behavior without network I/O.

    def close(self) -> None:
        """Record one socket close."""
        self.closed += 1  # The test observes dead-peer cleanup.


class PendingRawSocket:
    """Expose a real file number and a configured TLS byte count."""

    def __init__(self, idle_socket: RealSocket, pending_count: int) -> None:
        """Store the idle socket and pending byte count."""
        self._idle_socket = idle_socket  # Select waits on this real idle socket.
        self._pending_count = pending_count  # pending() reports decrypted TLS bytes.

    def fileno(self) -> int:
        """Return the real socket file number."""
        return self._idle_socket.fileno()  # Select needs the underlying file number.

    def pending(self) -> int:
        """Return the configured decrypted byte count."""
        return self._pending_count  # Model ssl.SSLSocket.pending().


class TlsBufferedSocket(FrameSocket):
    """Return a binary frame held by the TLS layer."""

    def __init__(self, raw_socket: PendingRawSocket) -> None:
        """Store the raw socket and shell frame."""
        super().__init__(ABNF.OPCODE_BINARY, b"\x00switch> ")  # Preserve the held shell frame.
        self.sock = raw_socket  # websocket-client exposes its raw socket here.


class QuietSocket(FrameSocket):
    """Expose an idle raw socket for keepalive timeout tests."""

    def __init__(self, raw_socket: RealSocket) -> None:
        """Store the idle raw socket and unused application frame."""
        super().__init__(ABNF.OPCODE_BINARY, b"unused")  # The quiet test never receives this frame.
        self.sock = raw_socket  # Select waits on the idle real socket.


@pytest.mark.parametrize("payload, expected", [(b"", 1005), ((1000).to_bytes(2, "big"), 1000)])
def test_close_frame_preserves_status_behavior(payload: bytes, expected: int) -> None:
    """Map empty and populated close frames to their expected status."""
    reader = FrameReader(FrameSocket(ABNF.OPCODE_CLOSE, payload), threading.Event(), lambda: 1.0, 20.0)  # Build.
    with pytest.raises(ConnectionClosed) as caught:  # A close frame must end the read.
        reader.read(0.1)  # Read the configured close frame.
    assert caught.value.code == expected  # Preserve RFC 6455 and normal close-code behavior.


def test_data_and_control_frames_preserve_behavior() -> None:
    """Return application data and suppress control frames."""
    data_reader = FrameReader(FrameSocket(ABNF.OPCODE_BINARY, b"value"), threading.Event(), lambda: 1.0, 20.0)  # Data.
    pong_reader = FrameReader(FrameSocket(ABNF.OPCODE_PONG, b""), threading.Event(), lambda: 1.0, 20.0)  # Control.
    assert data_reader.read(0.1) == FrameRead(ABNF.OPCODE_BINARY, b"value")  # Return raw application bytes.
    assert pong_reader.read(0.1) is None  # Keep control frames out of application output.


def test_keepalive_pings_then_closes_after_two_intervals() -> None:
    """Send one ping, then close a peer that stays silent."""
    moments = iter([0.0, 10.0, 20.0])  # Initialize, reach one interval, then reach two intervals.
    idle_socket, peer_socket = socketpair()  # The peer stays silent for both keepalive decisions.
    with idle_socket, peer_socket:  # Close both real sockets after the test.
        socket = QuietSocket(idle_socket)  # Select sees no readable network data.
        reader = FrameReader(socket, threading.Event(), lambda: next(moments), 10.0)  # Inject the quiet clock.
        assert reader.read(0.0) is None  # The first quiet interval sends a ping and returns no data.
        with pytest.raises(ConnectionClosed) as caught:  # The second quiet interval closes the dead peer.
            reader.read(0.0)  # Run the second keepalive decision.
    assert (socket.pings, socket.closed, caught.value.dropped) == (1, 1, True)  # Preserve keepalive behavior.


def test_tls_buffer_reads_without_network_wait() -> None:
    """Read held TLS bytes without waiting for new network data."""
    idle_socket, peer_socket = socketpair()  # The peer sends no new kernel data.
    with idle_socket, peer_socket:  # Close both sockets after the test.
        reader = FrameReader(
            TlsBufferedSocket(PendingRawSocket(idle_socket, 9)), threading.Event(), time.monotonic, 20.0
        )
        started = time.monotonic()  # Measure the operator-visible wait.
        frame = reader.read(3.0)  # Read the frame that TLS already holds.
        elapsed = time.monotonic() - started  # Calculate the completed wait.
    assert frame == FrameRead(ABNF.OPCODE_BINARY, b"\x00switch> ")  # Preserve the held frame.
    assert elapsed < 1.0  # Do not wait for another network packet.


def test_empty_tls_buffer_waits_for_socket_timeout() -> None:
    """Keep the network wait when TLS holds no bytes."""
    idle_socket, peer_socket = socketpair()  # The peer sends no data.
    with idle_socket, peer_socket:  # Close both sockets after the test.
        reader = FrameReader(
            TlsBufferedSocket(PendingRawSocket(idle_socket, 0)), threading.Event(), time.monotonic, 20.0
        )
        assert reader.read(0.05) is None  # A quiet socket returns no frame.
