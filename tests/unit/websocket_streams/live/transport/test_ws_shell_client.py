"""Tests for the issue #3671 shell client."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # Send from another thread is part of the contract.

import pytest  # Tests assert expected transport errors.

from src.websocket_streams.intake.fields import StreamRequestError
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, ShellAddressPolicy, TransportProfile
from src.websocket_streams.live.transport.frames import ConnectionClosed
from src.websocket_streams.live.transport.shell_client import ShellClient
from tests.support.fake_mist_cloud.api import FakeApiSession
from tests.support.fake_mist_cloud.devices import ShellDevice
from tests.support.fake_mist_cloud.server import FakeConnection, FakeMistCloud


class SplitUtf8Device:
    """A fake device that sends split UTF-8 bytes."""

    def on_connect(self, connection: FakeConnection) -> None:
        """Send split text and binary bytes after connect."""
        connection.send_text_bytes(b"\xe2")  # Send the first byte of a UTF-8 character as a text frame.
        connection.send_binary(b"\x98\x83")  # Send the remaining bytes as a binary frame.


class TestShellClient:
    """Verify shell client behavior against the fake cloud."""

    def test_open_read_send_and_resize(self) -> None:
        """Open the shell, read output, send input, and resize."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud)  # Build a shell client.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open and send initial size.
                first = client.read(1.0)  # Read the banner.
                second = client.read(1.0)  # Read the prompt.
                client.send("show version\r")  # Send one shell command.
                received = device.wait_for_input(len("show version\r"), 1.0)  # Wait for exact bytes.
                client.resize(100, 40)  # Send a resize frame.
                resize_frames = device.wait_for_resize(2, 1.0)  # Wait for the initial and explicit resize frames.
                assert first == b"Welcome to Fake Mist Shell\r\n"  # Banner bytes are unchanged.
                assert second == b"\x1b[?2004hdevice> "  # Prompt includes bracketed paste mode.
                assert received == b"show version\r"  # The device sees input after NUL removal.
                assert device.received_frames[-1] == b"\x00show version\r"  # The NUL prefix is intact on the wire.
                assert resize_frames[-1] == {"resize": {"width": 100, "height": 40}}  # Resize shape.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_send_from_second_thread_preserves_bytes(self) -> None:
        """Allow send on a web thread while another thread can read."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud)  # Build a shell client.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                thread = threading.Thread(target=client.send, args=("unicode \u2603\r",), daemon=True)  # Web thread.
                thread.start()  # Send from another thread.
                thread.join(timeout=1.0)  # The send must not block.
                received = device.wait_for_input(len("unicode \u2603\r".encode("utf-8")), 1.0)  # Wait for bytes.
                assert thread.is_alive() is False  # The send completed.
                assert received == "unicode \u2603\r".encode("utf-8")  # Unicode text is UTF-8 on the wire.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_read_returns_none_after_quiet_interval(self) -> None:
        """Return None when no output arrives within the timeout."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud)  # Build a shell client.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                client.read(1.0)  # Drain the banner.
                client.read(1.0)  # Drain the prompt.
                assert client.read(0.1) is None  # A quiet interval returns None.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_quiet_shell_stays_open_when_pongs_arrive(self) -> None:
        """Keep a quiet shell open when pongs arrive."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud, read_timeout=0.05)  # Use a short keepalive interval.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                client.read(1.0)  # Drain the banner.
                client.read(1.0)  # Drain the prompt.
                result = client.read(0.25)  # Wait for more than four keepalive intervals.
                pings = cloud.wait_for_pings(3, 1.0)  # The fake cloud records received pings.
                assert result is None  # No shell output arrived.
                assert len(pings) >= 3  # Pongs kept the quiet connection alive.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_quiet_shell_closes_when_pongs_do_not_arrive(self) -> None:
        """Close a quiet shell after two silent intervals without pongs."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.answer_pings = False  # Simulate a dead peer that does not answer pings.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud, read_timeout=0.05)  # Use a short keepalive interval.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                client.read(1.0)  # Drain the banner.
                client.read(1.0)  # Drain the prompt.
                with pytest.raises(ConnectionClosed) as caught:  # Silent peer should close.
                    client.read(0.5)  # Wait through two quiet intervals.
                assert caught.value.dropped is True  # The close is a dropped connection.
                assert caught.value.code is None  # A silent peer has no close code.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_read_raises_connection_closed_after_device_close(self) -> None:
        """Raise ConnectionClosed when the device closes the shell."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud)  # Build a shell client.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                client.send("exit\r")  # Ask the device to close normally.
                with pytest.raises(ConnectionClosed) as caught:  # read() must report the close.
                    while True:  # Drain any close notice first.
                        client.read(1.0)  # The fake closes after output.
                assert caught.value.dropped is True  # Device close is remote.
                assert caught.value.code == 1000  # The close code must be preserved.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_read_raises_without_code_after_device_drop(self) -> None:
        """Raise ConnectionClosed with no code after TCP loss."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud)  # Build a shell client.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                device.drop()  # Drop TCP with no close frame.
                with pytest.raises(ConnectionClosed) as caught:  # read() must report the drop.
                    client.read(1.0)  # Read after the drop.
                assert caught.value.dropped is True  # The close is remote.
                assert caught.value.code is None  # TCP loss has no close code.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_read_returns_text_and_binary_bytes_without_utf8_validation(self) -> None:
        """Return split UTF-8 bytes from text and binary frames unchanged."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.register("/shell/default", SplitUtf8Device())  # Route a split UTF-8 device.
            client = self._client(cloud)  # Build a shell client.
            try:
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                assert client.read(1.0) == b"\xe2"  # Text frame bytes stay unchanged.
                assert client.read(1.0) == b"\x98\x83"  # Binary frame bytes stay unchanged.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_send_and_resize_refuse_when_not_open(self) -> None:
        """Raise not_open when no shell connection exists."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            client = self._client(cloud)  # Build a shell client but do not open it.
            with pytest.raises(StreamRequestError) as send_error:  # send() must refuse.
                client.send("show version")  # No socket exists.
            with pytest.raises(StreamRequestError) as resize_error:  # resize() must refuse.
                client.resize(80, 24)  # No socket exists.
            assert send_error.value.code == "not_open"  # The send refusal uses the contract code.
            assert resize_error.value.code == "not_open"  # The resize refusal uses the contract code.

    def test_open_refuses_bad_shell_address(self) -> None:
        """Refuse a shell URL outside the policy."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            client = self._client(cloud, allow_loopback=False)  # Build a production-safe policy.
            with pytest.raises(StreamRequestError) as caught:  # open() must refuse before connecting.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Loopback is not allowed here.
            assert caught.value.code == "bad_request"  # Unsafe addresses are bad requests.

    def test_connection_error_from_factory_surfaces(self) -> None:
        """Raise a connection error when the socket cannot open."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud for the endpoint profile only.
            client = self._client(cloud)  # Build a shell client.
            with pytest.raises(Exception) as caught:  # websocket-client raises its own connection error type.
                client.open("ws://127.0.0.1:1/shell/default", 80, 24)  # Port 1 should not accept.
            assert caught.value.__class__.__name__ in {
                "ConnectionRefusedError",
                "WebSocketProxyException",
            }  # Exact class.

    def test_fake_cloud_records_early_hook_and_bytes(self) -> None:
        """Guarantee the reusable fake records input bytes and early publishes."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            api = FakeApiSession(cloud)  # Build fake API session with cloud URLs.
            called: list[str] = []  # The hook records call order.
            api.before_post_return = lambda uri, _body: called.append(uri)  # Hook runs before mist_post returns.
            response = api.mist_post("/api/v1/sites/site/devices/device/shell", body={})  # Trigger shell URL.
            client = self._client(cloud)  # Build a shell client.
            try:
                client.open(str(response.data["url"]), 80, 24)  # Connect to the returned URL.
                client.send("paste\r")  # Send input for byte recording.
                received = device.wait_for_input(len("paste\r"), 1.0)  # Wait for recorded bytes.
                assert called == ["/api/v1/sites/site/devices/device/shell"]  # The hook ran during mist_post.
                assert received == b"paste\r"  # The fake exposes bytes after NUL removal.
                assert device.received_frames[-1] == b"\x00paste\r"  # The raw record keeps the NUL prefix.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def _client(self, cloud: FakeMistCloud, allow_loopback: bool = True, read_timeout: float = 20.0) -> ShellClient:
        """Build a shell client for the fake cloud."""
        profile = TransportProfile(
            stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=allow_loopback,
            read_timeout_seconds=read_timeout,
        )  # Configure loopback.
        endpoint = MistStreamEndpoint(FakeApiSession(), profile)  # Build endpoint with fake auth.
        policy = ShellAddressPolicy(endpoint.cloud_host, allow_loopback=allow_loopback)  # Build address policy.
        return ShellClient(endpoint, policy)  # Return the client under test.
