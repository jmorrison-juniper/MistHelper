"""Tests for the issue #3671 shell client."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Logging tests parse structured transport records.
import logging  # Logging tests capture debug records.
import threading  # Send from another thread is part of the contract.
from collections.abc import Callable  # The client helper accepts fake factories.

import pytest  # Tests assert expected transport errors.
from websocket._url import get_proxy_info  # FR-005: the pinned library reads the proxy of the host.

import websocket  # Socket fakes raise websocket-client write errors.
from src.websocket_streams.intake.fields.error import StreamRequestError  # Sends use the request error contract.
from src.websocket_streams.live.transport.endpoint import (  # Build client endpoints.
    MistStreamEndpoint,
    ShellAddressPolicy,
    TransportProfile,
)
from src.websocket_streams.live.transport.runtime.reader.contracts import (
    ConnectionClosed,
)  # Read errors use this structured close.
from src.websocket_streams.live.transport.shell_client import ShellClient  # Test the shell transport client.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import (
    FakeApiSession,
)  # Fake sessions provide endpoint fields.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.devices import (
    ShellDevice,
)  # Shell tests need a fake terminal endpoint.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeConnection,
    FakeMistCloud,
    HandshakeFault,
)  # Fake WebSocket I/O.


class SplitUtf8Device:
    """A fake device that sends split UTF-8 bytes."""

    def on_connect(self, connection: FakeConnection) -> None:
        """Send split text and binary bytes after connect."""
        connection.send_text_bytes(b"\xe2")  # Send the first byte of a UTF-8 character as a text frame.
        connection.send_binary(b"\x98\x83")  # Send the remaining bytes as a binary frame.


class MarkerDevice:
    """A fake device that sends output frames with and without Mist channel markers."""

    def on_connect(self, connection: FakeConnection) -> None:
        """Send marker edge cases after connect."""
        connection.send_binary(b"\x00abc")  # A normal Mist output frame has one leading NUL.
        connection.send_binary(b"abc")  # A frame without the marker must stay unchanged.
        connection.send_binary(b"\x00")  # A marker-only frame becomes empty.
        connection.send_binary(b"\x00\x00x")  # Only the first marker byte is removed.


class WriteFailSocket:
    """A socket fake that can fail writes after open."""

    def __init__(self, fail_binary: bool = False, fail_text_after: int = 99) -> None:
        """Build a write-failure socket."""
        self.fail_binary = fail_binary  # Tests choose whether input fails.
        self.fail_text_after = fail_text_after  # Tests choose which resize fails.
        self.text_writes = 0  # Count resize writes.
        self.binary_writes = 0  # Count input writes.
        self.timeout_value: float | None = None  # The open path stores the stable timeout.
        self.aborted = False  # close_socket should abort before close.
        self.closed = False  # close_socket should call close.
        self.shutdown_called = False  # close_socket should call shutdown after close.

    def settimeout(self, timeout: float) -> None:
        """Record the stable socket timeout."""
        self.timeout_value = timeout  # The client should set one connection timeout.

    def send(self, _message: str) -> None:
        """Send or fail one text frame."""
        self.text_writes += 1  # Count the resize attempt.
        if self.text_writes > self.fail_text_after:  # Tests can fail a later resize.
            raise websocket.WebSocketException("resize failed")  # The client maps this to not_open.

    def send_binary(self, _payload: bytes) -> None:
        """Send or fail one binary frame."""
        self.binary_writes += 1  # Count the input attempt.
        if self.fail_binary:  # Tests can fail the paste write.
            raise OSError("input failed")  # The client maps OS write errors to not_open.

    def abort(self) -> None:
        """Wake a blocked reader."""
        self.aborted = True  # close_socket should call abort.

    def close(self) -> None:
        """Record a close call."""
        self.closed = True  # close_socket should call close.

    def shutdown(self) -> None:
        """Record a shutdown call."""
        self.shutdown_called = True  # close_socket should call shutdown.


class RecordingFactory:
    """A shell WebSocket factory that records the connect timeout and the options."""

    def __init__(self, socket: WriteFailSocket) -> None:
        """Build a factory for one socket."""
        self.socket = socket  # The factory returns this socket.
        self.timeout: float | None = None  # Tests assert the timeout argument.
        self.options: dict[str, object] = {}  # Tests assert the other keyword arguments.

    def __call__(self, *_args: object, timeout: float | None = None, **options: object) -> WriteFailSocket:
        """Return the configured socket."""
        self.timeout = timeout  # Record the connect timeout.
        self.options = dict(options)  # Record the options that websocket-client would get.
        return self.socket  # Return the fake socket.


class BadJsonShellDevice:
    """A shell device that sends malformed JSON text as terminal output."""

    def on_connect(self, connection: FakeConnection) -> None:
        """Send malformed JSON text after connect."""
        connection.send_text("bad json")  # ShellClient must return these bytes unchanged.


class TestShellClient:
    """Verify shell client behavior against the fake cloud."""

    def test_open_read_send_and_resize(self) -> None:
        """Open the shell, read output, send input, and resize."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud)  # Build a shell client.
            try:  # Always close the client after the open-read-send path.
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
            try:  # Always close the client after the thread send path.
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
            try:  # Always close the client after the quiet read path.
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
            try:  # Always close the client after the keepalive success path.
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
            try:  # Always close the client after the keepalive failure path.
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
            try:  # Always close the client after the device-close path.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                client.send("exit\r")  # Ask the device to close normally.
                with pytest.raises(ConnectionClosed) as caught:  # read() must report the close.
                    while True:  # Drain any close notice first.
                        client.read(1.0)  # The fake closes after output.
                assert caught.value.dropped is True  # Device close is remote.
                assert caught.value.code == 1005  # Mist sends an empty close payload after exit.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_read_raises_without_code_after_device_drop(self) -> None:
        """Raise ConnectionClosed with no code after TCP loss."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a fake shell.
            cloud.register("/shell/default", device)  # Route the shell path.
            client = self._client(cloud)  # Build a shell client.
            try:  # Always close the client after the TCP-drop path.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                client.read(1.0)  # Drain the banner before the drop.
                client.read(1.0)  # Drain the prompt before the drop.
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
            try:  # Always close the client after the split-frame path.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                assert client.read(1.0) == b"\xe2"  # Text frame bytes stay unchanged.
                assert client.read(1.0) == b"\x98\x83"  # Binary frame bytes stay unchanged.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_read_removes_one_leading_mist_channel_marker(self) -> None:
        """Remove exactly one leading NUL from shell output frames."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.register("/shell/default", MarkerDevice())  # Route marker edge-case frames.
            client = self._client(cloud)  # Build a shell client.
            try:  # Always close the client after the marker-stripping path.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell.
                assert client.read(1.0) == b"abc"  # One leading NUL is removed.
                assert client.read(1.0) == b"abc"  # Frames without the marker stay unchanged.
                assert client.read(1.0) == b""  # A marker-only frame becomes empty output.
                assert client.read(1.0) == b"\x00x"  # Only one leading NUL is removed.
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

    def test_connection_error_from_fake_cloud_reset_surfaces(self) -> None:
        """Raise a connection error when the fake cloud resets the handshake."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.fail_handshake("/shell/default", HandshakeFault("reset"))  # Force a TCP reset.
            client = self._client(cloud, subscribe_timeout=0.5)  # Use a bounded connect timeout.
            with pytest.raises(ConnectionError) as caught:  # Reset is a ConnectionError subclass.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Attempt the opening handshake.
            requests = cloud.wait_for_requests(1, 1.0)  # The fake cloud recorded the request.
            assert requests[0].path == "/shell/default"  # The handshake reached the fake cloud.
            assert caught.value.__class__.__name__ == "ConnectionResetError"  # The reset path is exact.

    def test_connection_timeout_from_fake_cloud_stall_surfaces(self) -> None:
        """Raise a timeout when the fake cloud stalls the handshake."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.fail_handshake("/shell/default", HandshakeFault("stall"))  # Force a stalled handshake.
            client = self._client(cloud, subscribe_timeout=0.5)  # Keep the stall test fast.
            with pytest.raises(websocket.WebSocketTimeoutException) as caught:  # TimeoutError family.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Attempt the opening handshake.
            requests = cloud.wait_for_requests(1, 1.0)  # The fake cloud recorded the request.
            assert requests[0].path == "/shell/default"  # The handshake reached the fake cloud.
            assert "Timeout" in caught.value.__class__.__name__  # The failure is a timeout.

    @pytest.mark.parametrize(("status_code",), [(403,), (503,)])
    def test_http_refusal_from_fake_cloud_surfaces_status(self, status_code: int) -> None:
        """Raise a bad status error for HTTP handshake refusal."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.fail_handshake(
                "/shell/default", HandshakeFault("refuse", status_code=status_code)
            )  # Force an HTTP refusal.
            client = self._client(cloud, subscribe_timeout=0.5)  # Use a bounded connect timeout.
            with pytest.raises(websocket.WebSocketBadStatusException) as caught:  # HTTP refusal.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Attempt the opening handshake.
            requests = cloud.wait_for_requests(1, 1.0)  # The fake cloud recorded the request.
            assert requests[0].path == "/shell/default"  # The handshake reached the fake cloud.
            assert caught.value.status_code == status_code  # The HTTP status is observable.

    def test_bad_json_shell_output_returns_unchanged_bytes(self) -> None:
        """Return malformed JSON shell output without parsing it."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.register("/shell/default", BadJsonShellDevice())  # Route a text-output shell.
            client = self._client(cloud, subscribe_timeout=0.5)  # Build a fast shell client.
            try:  # Always close the client after the malformed-output path.
                client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open the shell socket.
                assert client.read(1.0) == b"bad json"  # Shell output stays byte-for-byte.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def test_open_passes_connect_timeout_to_factory(self) -> None:
        """Pass a bounded connect timeout to websocket-client."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud for a safe shell URL.
            socket = WriteFailSocket()  # Build a socket that accepts the initial resize.
            factory = RecordingFactory(socket)  # Record the factory arguments.
            client = self._client(cloud, factory=factory, subscribe_timeout=0.6)  # Use a distinct timeout.
            client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open through the fake factory.
            client.close()  # Close to exercise abort, close, and shutdown.
            assert factory.timeout == 0.6  # The factory received the connect timeout.
            assert socket.timeout_value == 0.6  # The stable socket timeout matches the profile.
            assert socket.shutdown_called is True  # close() shut down the socket after close.

    def test_open_leaves_the_proxy_to_the_host_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Use the proxy settings of the host for the shell connection (FR-005)."""
        for name in ("no_proxy", "NO_PROXY"):  # Start with no proxy exception on the host.
            monkeypatch.delenv(name, raising=False)  # Remove each spelling, because Linux keeps both.
        monkeypatch.setenv("https_proxy", "http://proxy.example.net:3128")  # The host names a proxy for TLS.
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud for a safe shell URL.
            factory = RecordingFactory(WriteFailSocket())  # Record the factory arguments.
            client = self._client(cloud, factory=factory)  # Use the recording factory.
            client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Open through the fake factory.
            client.close()  # Close the fake socket.
        proxy_keys = [key for key in factory.options if "proxy" in key]  # A proxy key would hide the host setting.
        host, port, _auth = get_proxy_info("api-ws.mist.com", True)  # websocket-client reads the host setting.
        monkeypatch.setenv("no_proxy", "api-ws.mist.com")  # The host skips the proxy for the shell host.
        skipped = get_proxy_info("api-ws.mist.com", True)  # websocket-client reads the exception list.
        assert "sslopt" in factory.options  # The factory got the normal connection options.
        assert proxy_keys == []  # The client never replaces the proxy of the host.
        assert (host, port) == ("proxy.example.net", 3128)  # The shell connection uses the host proxy.
        assert skipped == (None, 0, None)  # The exception list of the host still applies.

    def test_send_write_error_closes_client_and_returns_not_open(self) -> None:
        """Close the shell client after a failed input write."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud for a safe shell URL.
            socket = WriteFailSocket(fail_binary=True)  # Make the input write fail.
            client = self._client(cloud, factory=RecordingFactory(socket))  # Use the failing socket.
            client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Initial resize succeeds.
            with pytest.raises(StreamRequestError) as caught:  # The route expects a contract error.
                client.send("show version\r")  # The failing socket simulates a broken TLS write.
            assert caught.value.code == "not_open"  # Failed writes map to not_open.
            assert socket.shutdown_called is True  # The failed write closed the client.

    def test_resize_write_error_closes_client_and_returns_not_open(self) -> None:
        """Close the shell client after a failed resize write."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud for a safe shell URL.
            socket = WriteFailSocket(fail_text_after=1)  # Let the initial resize pass and fail the next one.
            client = self._client(cloud, factory=RecordingFactory(socket))  # Use the failing socket.
            client.open(f"{cloud.base_ws_url}/shell/default", 80, 24)  # Initial resize succeeds.
            with pytest.raises(StreamRequestError) as caught:  # The route expects a contract error.
                client.resize(100, 30)  # The failing socket simulates a broken TLS write.
            assert caught.value.code == "not_open"  # Failed writes map to not_open.
            assert socket.shutdown_called is True  # The failed write closed the client.

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
            try:  # Always close the client after fake-cloud record checks.
                client.open(str(response.data["url"]), 80, 24)  # Connect to the returned URL.
                client.send("paste\r")  # Send input for byte recording.
                received = device.wait_for_input(len("paste\r"), 1.0)  # Wait for recorded bytes.
                assert called == ["/api/v1/sites/site/devices/device/shell"]  # The hook ran during mist_post.
                assert received == b"paste\r"  # The fake exposes bytes after NUL removal.
                assert device.received_frames[-1] == b"\x00paste\r"  # The raw record keeps the NUL prefix.
            finally:
                client.close()  # Ensure the socket and server thread stop.

    def _client(
        self,
        cloud: FakeMistCloud,
        allow_loopback: bool = True,
        read_timeout: float = 20.0,
        subscribe_timeout: float = 1.0,
        factory: Callable[..., object] | None = None,
    ) -> ShellClient:
        """Build a shell client for the fake cloud."""
        profile = TransportProfile(
            stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=allow_loopback,
            read_timeout_seconds=read_timeout,
            subscribe_timeout_seconds=subscribe_timeout,
        )  # Configure loopback.
        endpoint = MistStreamEndpoint(FakeApiSession(), profile)  # Build endpoint with fake auth.
        policy = ShellAddressPolicy(endpoint.cloud_host, allow_loopback=allow_loopback)  # Build address policy.
        return ShellClient(endpoint, policy, factory=factory or websocket.create_connection)  # Return the client.


class TestShellStructuredLogging:
    """Verify shell records use the T072 safe JSON boundary."""

    def test_shell_records_are_json_and_exclude_input(self, caplog: pytest.LogCaptureFixture) -> None:
        """Emit structured records without shell addresses or terminal input."""
        caplog.set_level(logging.DEBUG, logger="src.websocket_streams.live.transport.shell_client")  # Capture events.
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            device = ShellDevice()  # Build a normal shell device.
            cloud.register("/shell/private-token", device)  # Use a path that must not enter logs.
            client = TestShellClient()._client(cloud)  # Build the client with focused test collaborators.
            client.open(f"{cloud.base_ws_url}/shell/private-token", 80, 24)  # Emit open and resize records.
            client.send("terminal-secret-text\r")  # Emit an input record with only a byte count.
            client.close()  # Emit close records.
        records = [  # Parse only records from this client and exclude concurrent logger output.
            json.loads(record.message) for record in caplog.records if record.name.endswith("shell_client")
        ]
        serialized = json.dumps(records)  # Build one text value for secret checks.
        assert len(records) == 8  # The shell client must emit the complete open, write, and close sequence.
        assert all("event" in record for record in records)  # Every record has the required event field.
        assert "private-token" not in serialized  # The shell path must not cross the log boundary.
        assert "terminal-secret-text" not in serialized  # Terminal input must not cross the log boundary.
