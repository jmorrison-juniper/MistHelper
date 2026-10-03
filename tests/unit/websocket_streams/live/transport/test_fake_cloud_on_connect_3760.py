"""Tests for the issue #3760 nullable on_connect guard in the fake Mist cloud."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import base64  # The client handshake needs a base64 key.
import logging  # Each test step writes an action log record.
import os  # The client handshake key and frame mask need random bytes.
import socket  # The test client uses a plain loopback TCP socket.
import struct  # The close frame payload uses network byte order.
import threading  # The known device signals its on_connect call with an event.

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

    def handshake(self, path: str) -> bytes:
        """Send the opening request and return the status line."""
        key = base64.b64encode(os.urandom(16)).decode("ascii")  # RFC 6455 requires a random 16-byte key.
        request = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nSec-WebSocket-Key: {key}\r\n\r\n"  # Minimal request.
        self.sock.sendall(request.encode("ascii"))  # Send the opening request.
        answer = b""  # Accumulate the answer until the blank line.
        while b"\r\n\r\n" not in answer:  # The answer headers end with a blank line.
            answer += self.sock.recv(4096)  # Read the next answer segment.
        return answer.split(b"\r\n", 1)[0]  # Return only the status line.

    def close_and_read_echo(self) -> bytes:
        """Send a masked normal close and return the first two echo bytes."""
        mask = os.urandom(4)  # Clients must mask every frame.
        payload = struct.pack("!H", 1000)  # A normal close code.
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))  # Apply the client mask.
        self.sock.sendall(bytes([0x88, 0x82]) + mask + masked)  # Send a masked close frame.
        return self.sock.recv(2)  # The fake cloud echoes a close frame header.

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
            client = RawLoopbackClient(cloud.port)  # Connect a raw client.
            LOGGER.info("Opening known route /known")  # Log before the handshake.
            status = client.handshake("/known")  # Complete the opening handshake.
            called = device.connected.wait(WAIT_SECONDS)  # Wait for the on_connect call with a bound.
            echo = client.close_and_read_echo()  # Close normally and read the echo.
            client.shut()  # Release the client socket.
            LOGGER.debug("Known route status %r called %s", status, called)  # Log the result.
        assert status == b"HTTP/1.1 101 Switching Protocols"  # The handshake succeeded.
        assert called is True  # The device received on_connect.
        assert device.paths == ["/known"]  # Exactly one call with the exact path.
        assert echo == CLOSE_FRAME  # The fixture echoed a normal close.

    def test_missing_route_skips_on_connect_and_keeps_serving(self) -> None:
        """Skip on_connect for a missing route and keep the existing close behavior."""
        with FakeMistCloud() as cloud:  # Start and stop the fixture with its own cleanup.
            client = RawLoopbackClient(cloud.port)  # Connect a raw client.
            LOGGER.info("Opening missing route /missing")  # Log before the handshake.
            status = client.handshake("/missing")  # No device is registered for this path.
            requests = cloud.wait_for_requests(1, WAIT_SECONDS)  # Wait for the request record with a bound.
            echo = client.close_and_read_echo()  # The worker must still serve the close.
            client.shut()  # Release the client socket.
            LOGGER.debug("Missing route status %r requests %d", status, len(requests))  # Log the result.
        assert status == b"HTTP/1.1 101 Switching Protocols"  # The handshake succeeded.
        assert [request.path for request in requests] == ["/missing"]  # One exact request record.
        assert echo == CLOSE_FRAME  # The worker reached the read loop and echoed close.
