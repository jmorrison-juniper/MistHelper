"""Tests for the issue #3760 nullable on_connect guard in the fake Mist cloud."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import base64  # The client handshake needs a base64 key.
import logging  # Each test step writes an action log record.
import os  # The client handshake key and frame mask need random bytes.
import socket  # The test client uses a plain loopback TCP socket.
import struct  # The close frame payload uses network byte order.
import threading  # The known device signals its on_connect call with an event.
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeConnection,
    FakeMistCloud,
)  # The fixture under test and its connection handle.

LOGGER = logging.getLogger(__name__)  # Action logs for this test module.
WAIT_SECONDS = 2.0  # Bound every wait so a failure cannot hang the suite.
CLOSE_FRAME = bytes([0x88, 0x02])  # A final close frame header with a two-byte payload.


class RecordingDevice:
    """A known device that records each on_connect call."""

    def __init__(self) -> None:
        """Build a device with no calls."""
        self.paths: list[str] = []  # The request path of each on_connect call.
        self.connected = threading.Event()  # The test waits on this event with a bound.

    def on_connect(self, connection: FakeConnection) -> None:
        """Record the connection path and signal the test."""
        self.paths.append(connection.path)  # Keep the exact path for the assertion.
        self.connected.set()  # Wake the waiting test.


class RawLoopbackClient:
    """A minimal RFC 6455 client that drives the fake cloud directly."""

    def __init__(self, port: int) -> None:
        """Open a TCP connection to the fake cloud."""
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=WAIT_SECONDS)  # Bounded loopback connect.

    def __enter__(self) -> RawLoopbackClient:
        """Keep the client socket under context ownership."""
        return self

    def __exit__(self, *_args: object) -> None:
        """Release the socket even when a test fails."""
        self.shut()

    def _receive(self, count: int, deadline: float) -> bytes:
        """Read bytes within the operation deadline, or report EOF."""
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Loopback response deadline expired")
        self.sock.settimeout(remaining)
        chunk = self.sock.recv(count)
        if not chunk:
            raise EOFError("Loopback peer closed before the response completed")
        return chunk

    def handshake(self, path: str) -> bytes:
        """Send the opening request and return the status line."""
        LOGGER.info("Reading loopback handshake for %s", path)
        deadline = time.monotonic() + WAIT_SECONDS
        key = base64.b64encode(os.urandom(16)).decode("ascii")  # RFC 6455 requires a random 16-byte key.
        request = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nSec-WebSocket-Key: {key}\r\n\r\n"  # Minimal request.
        self.sock.sendall(request.encode("ascii"))  # Send the opening request.
        answer = b""  # Accumulate the answer until the blank line.
        while b"\r\n\r\n" not in answer:  # The answer headers end with a blank line.
            answer += self._receive(1, deadline)  # Stop at the header boundary without consuming frame bytes.
        LOGGER.debug("Read %d handshake bytes", len(answer))
        return answer.split(b"\r\n", 1)[0]  # Return only the status line.

    def close_and_read_echo(self) -> bytes:
        """Send a masked normal close and return the first two echo bytes."""
        LOGGER.info("Reading loopback close echo")
        deadline = time.monotonic() + WAIT_SECONDS
        mask = os.urandom(4)  # Clients must mask every frame.
        payload = struct.pack("!H", 1000)  # A normal close code.
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))  # Apply the client mask.
        self.sock.sendall(bytes([0x88, 0x82]) + mask + masked)  # Send a masked close frame.
        echo = b""
        while len(echo) < len(CLOSE_FRAME):
            echo += self._receive(1, deadline)
        LOGGER.debug("Read %d close header bytes", len(echo))
        return echo

    def shut(self) -> None:
        """Close the client socket."""
        self.sock.close()  # Release the loopback socket.


class TestFakeCloudOnConnectGuard:
    """Verify the on_connect guard for known and missing routes."""

    def test_known_route_calls_on_connect_once(self) -> None:
        """Call on_connect exactly once for a registered device."""
        device = RecordingDevice()  # The known route handler.
        with FakeMistCloud() as cloud:  # Start and stop the fixture with its own cleanup.
            cloud.register("/known", device)  # Register the known route.
            with RawLoopbackClient(cloud.port) as client:
                LOGGER.info("Opening known route /known")  # Log before the handshake.
                status = client.handshake("/known")  # Complete the opening handshake.
                called = device.connected.wait(WAIT_SECONDS)  # Wait for the on_connect call with a bound.
                echo = client.close_and_read_echo()  # Close normally and read the echo.
            LOGGER.debug("Known route status %r called %s", status, called)  # Log the result.
        assert status == b"HTTP/1.1 101 Switching Protocols"  # The handshake succeeded.
        assert called is True  # The device received on_connect.
        assert device.paths == ["/known"]  # Exactly one call with the exact path.
        assert echo == CLOSE_FRAME  # The fixture echoed a normal close.

    def test_missing_route_skips_on_connect_and_keeps_serving(self) -> None:
        """Skip on_connect for a missing route and keep the existing close behavior."""
        with FakeMistCloud() as cloud:  # Start and stop the fixture with its own cleanup.
            with RawLoopbackClient(cloud.port) as client:
                LOGGER.info("Opening missing route /missing")  # Log before the handshake.
                status = client.handshake("/missing")  # No device is registered for this path.
                requests = cloud.wait_for_requests(1, WAIT_SECONDS)  # Wait for the request record with a bound.
                echo = client.close_and_read_echo()  # The worker must still serve the close.
            LOGGER.debug("Missing route status %r requests %d", status, len(requests))  # Log the result.
        assert status == b"HTTP/1.1 101 Switching Protocols"  # The handshake succeeded.
        assert [request.path for request in requests] == ["/missing"]  # One exact request record.
        assert echo == CLOSE_FRAME  # The worker reached the read loop and echoed close.

    @contextmanager
    def controlled_peer(self) -> Iterator[tuple[RawLoopbackClient, socket.socket]]:
        """Own both endpoints of a real loopback connection."""
        with socket.create_server(("127.0.0.1", 0)) as listener:
            listener.settimeout(WAIT_SECONDS)
            with RawLoopbackClient(listener.getsockname()[1]) as client:
                peer, _address = listener.accept()
                with peer:
                    peer.settimeout(WAIT_SECONDS)
                    yield client, peer

    @pytest.mark.parametrize("prefix", [b"", b"HTTP/1.1 101\r\n"])
    def test_handshake_eof_reports_incomplete_response(self, prefix: bytes) -> None:
        """Reject EOF before or during the handshake headers."""
        with self.controlled_peer() as (client, peer):
            peer.sendall(prefix)
            peer.shutdown(socket.SHUT_WR)
            with pytest.raises(EOFError, match="before the response completed"):
                client.handshake("/controlled")

    def test_partial_headers_leave_close_bytes_available(self) -> None:
        """Read headers and close bytes independently through real TCP."""
        with self.controlled_peer() as (client, peer):
            peer.sendall(b"HTTP/1.1 101 Switching Protocols\r\n\r\n" + CLOSE_FRAME)
            assert client.handshake("/controlled") == b"HTTP/1.1 101 Switching Protocols"
            assert client.close_and_read_echo() == CLOSE_FRAME

    def test_partial_close_eof_reports_incomplete_response(self) -> None:
        """Reject a close header that ends after one byte."""
        with self.controlled_peer() as (client, peer):
            peer.sendall(CLOSE_FRAME[:1])
            peer.shutdown(socket.SHUT_WR)
            with pytest.raises(EOFError, match="before the response completed"):
                client.close_and_read_echo()

    def test_expired_deadline_rejects_read(self) -> None:
        """Reject a read when the operation deadline expires."""
        with self.controlled_peer() as (client, _peer):
            with pytest.raises(TimeoutError, match="deadline expired"):
                client._receive(1, time.monotonic() - 1)

    def test_exception_closes_owned_client_socket(self) -> None:
        """Close the client socket when the context raises an exception."""
        with pytest.raises(RuntimeError, match="controlled test failure"):
            with self.controlled_peer() as (client, _peer):
                raise RuntimeError("controlled test failure")
        assert client.sock.fileno() == -1
