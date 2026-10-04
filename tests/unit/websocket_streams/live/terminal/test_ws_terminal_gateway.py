"""Focused tests for terminal gateway behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import time  # Wait-cap tests use short bounded waits.
from collections.abc import Callable  # Fake runners can forward bytes to the transport.
from concurrent.futures import ThreadPoolExecutor  # Long-poll tests use worker threads.
from types import SimpleNamespace  # Test sessions need small mutable records.
from unittest.mock import Mock  # Test sessions expose one observed method.

import pytest  # The tests assert contract refusals.
import websocket  # The production shell client uses the installed WebSocket transport.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Tests verify refusal codes.
from src.mist.realtime.websocket_streams.live.terminal.byte_history import ByteHistory  # Tests build terminal state.
from src.mist.realtime.websocket_streams.live.terminal.gateway import TerminalGateway  # Tests cover this class.
from src.mist.realtime.websocket_streams.live.terminal.input_queue import TerminalInput  # Tests build writable state.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Tests build terminal state.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (  # Tests build a safe loopback endpoint.
    MistStreamEndpoint,
    ShellAddressPolicy,
    TransportProfile,
)
from src.mist.realtime.websocket_streams.live.transport.shell_client import (
    ShellClient,
)  # Send paste bytes through production transport.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import FakeApiSession  # Supply endpoint auth.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.devices import (
    ShellDevice,
)  # Receive exact paste bytes.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeConnection,
    FakeMistCloud,
    HandshakeFault,
)  # Host the fake shell.


class PasteSinkShellDevice(ShellDevice):
    """Receive exact paste bytes without command-response backpressure."""

    def _process_input(self, connection: FakeConnection, data: bytes) -> None:
        """Keep received bytes without interpreting pasted lines as commands."""
        del connection, data  # The inherited receive path already stored the exact bytes.


class FakeRunner:
    """Record exact terminal input and size order."""

    def __init__(self, sender: Callable[[str], None] | None = None) -> None:
        """Build an empty runner recorder with an optional transport sender."""
        self.sent: list[str] = []  # Keep exact input order.
        self.sizes: list[tuple[int, int]] = []  # Keep accepted size order.
        self.sender = sender  # Forward accepted input when a transport test supplies a sender.

    def send_input(self, text: str) -> None:
        """Record exact input text and optionally send it to the fake device."""
        self.sent.append(text)  # Tests compare exact gateway input.
        if self.sender is not None:  # Device-bound tests supply the production client sender.
            self.sender(text)  # Send accepted bytes through ShellClient.

    def resize(self, cols: int, rows: int) -> None:
        """Record one terminal size."""
        self.sizes.append((cols, rows))  # Tests compare exact device sizes.


class FakeLookup:
    """Return test sessions by identifier."""

    def __init__(self, sessions: dict[str, SimpleNamespace]) -> None:
        """Store known test sessions."""
        self._sessions = sessions  # The gateway resolves sessions from this map.

    def session(self, session_id: str) -> SimpleNamespace:
        """Return a session or raise not_found."""
        session = self._sessions.get(session_id)  # Find the requested session.
        if session is None:  # Unknown sessions use the route contract error.
            raise StreamRequestError("not_found", "The session was not found.")  # Refuse it.
        return session  # Return the known test session.


def _gateway(
    clock: list[float] | None = None,
    sender: Callable[[str], None] | None = None,
) -> tuple[TerminalGateway, SimpleNamespace, FakeRunner]:
    """Build one live writable terminal gateway."""
    values = clock if clock is not None else [0.0]  # Use caller time or a new clock.
    terminal_input = TerminalInput(lambda: values[0])  # Build deterministic rate state.
    terminal = TerminalState(ByteHistory(), terminal_input, 1800.0, "2026-10-01T09:30:00Z")  # Build state.
    runner = FakeRunner(sender)  # Record actions and optionally forward input.
    terminal_input.bind(runner.send_input)  # Bind the runner sender.
    session = SimpleNamespace(
        terminal=terminal,
        runner=runner,
        live=True,
        state=SimpleNamespace(value="live"),
        reason="",
        input_ready=False,
        mark_read=Mock(),
    )  # Build the mutable live terminal session.
    gateway = TerminalGateway(FakeLookup({"abc123": session}))  # Build the route gateway.
    return gateway, session, runner  # Return all focused test handles.


class TestTerminalGatewayRead:
    """Verify terminal reads and long-poll limits."""

    def test_read_returns_available_bytes_and_marks_activity(self) -> None:
        """Read available bytes without waiting."""
        gateway, session, _runner = _gateway()  # Build a writable terminal session.
        session.terminal.history.append(b"abc")  # Add terminal output.
        payload = gateway.read("abc123", 0, 0.0)  # Read without a long poll.
        assert payload["data"] == "YWJj"  # The answer carries base64 bytes.
        assert payload["next"] == 3  # The cursor advances by the byte count.
        session.mark_read.assert_called_once_with()  # The read updates idle activity.

    def test_waiting_read_wakes_on_new_bytes(self) -> None:
        """Wake a long poll when output arrives."""
        gateway, session, _runner = _gateway()  # Build a writable terminal session.
        with ThreadPoolExecutor(max_workers=1) as pool:  # Run the long poll in another thread.
            future = pool.submit(gateway.read, "abc123", 0, 1.0)  # Start one bounded wait.
            self._wait_for_count(gateway, 1)  # Wait until the gateway reserves its slot.
            session.terminal.history.append(b"ok")  # Wake the read with output.
            payload = future.result(timeout=2.0)  # Bound the test wait.
        assert payload["data"] == "b2s="  # The answer carries the new bytes.
        assert gateway._waiting_reads == 0  # The completed read released its slot.

    def test_waiting_read_wakes_on_close_with_final_state(self) -> None:
        """Wake a long poll when the terminal closes."""
        gateway, session, _runner = _gateway()  # Build a writable terminal session.
        with ThreadPoolExecutor(max_workers=1) as pool:  # Run the long poll in another thread.
            future = pool.submit(gateway.read, "abc123", 0, 1.0)  # Start one bounded wait.
            self._wait_for_count(gateway, 1)  # Wait until the gateway reserves its slot.
            session.state.value, session.reason = "finished", "done"  # Set final public state.
            session.terminal.close()  # Wake the read by closing terminal state.
            payload = future.result(timeout=2.0)  # Bound the test wait.
        assert (payload["state"], payload["reason"]) == ("finished", "done")  # Return final metadata.

    def test_ninth_wait_returns_without_reserving_a_slot(self) -> None:
        """Return the ninth process-wide long poll at once."""
        gateway, session, _runner = _gateway()  # Build a writable terminal session.
        with ThreadPoolExecutor(max_workers=8) as pool:  # Fill all wait slots.
            futures = [pool.submit(gateway.read, "abc123", 0, 1.0) for _index in range(8)]  # Start waits.
            self._wait_for_count(gateway, 8)  # Confirm all slots are reserved.
            ninth = gateway.read("abc123", 0, 1.0)  # This read cannot reserve a slot.
            session.terminal.close()  # Wake the eight reserved reads.
            [future.result(timeout=2.0) for future in futures]  # Confirm every worker ended.
        assert ninth["data"] == ""  # The ninth read returned immediately.

    def _wait_for_count(self, gateway: TerminalGateway, count: int) -> None:
        """Wait for one bounded waiter count."""
        deadline = time.monotonic() + 1.0  # Bound the synchronization wait.
        while time.monotonic() < deadline:  # Poll until the expected count appears.
            if gateway._waiting_reads == count:  # Read the focused diagnostic count.
                return  # The worker threads reached the expected state.
            time.sleep(0.01)  # Let worker threads reserve their slots.
        raise AssertionError(f"expected {count} waiters")  # Report the missing count.


class TestTerminalGatewayWrite:
    """Verify input, resize, rates, and refusal behavior."""

    def test_queued_send_then_release_preserves_order(self) -> None:
        """Queue early input and preserve exact device order."""
        gateway, session, runner = _gateway()  # Build a writable terminal session.
        first = gateway.send("abc123", "show ")  # Queue the first early input.
        second = gateway.send("abc123", "version\r")  # Queue the second early input.
        session.terminal.input.release()  # First output releases queued input.
        third = gateway.send("abc123", "exit\r")  # Later input sends directly.
        assert [first["queued"], second["queued"], third["queued"]] == [True, True, False]  # Check states.
        assert runner.sent == ["show ", "version\r", "exit\r"]  # Preserve exact device order.

    def test_input_size_and_rate_limits_preserve_contract_codes(self) -> None:
        """Apply UTF-8 size and shared request rate limits."""
        clock = [0.0]  # Keep all requests in one deterministic window.
        gateway, session, runner = _gateway(clock)  # Build a writable terminal session.
        session.terminal.input.release()  # Send accepted input directly.
        exact = "é" * 8192  # This text is exactly 16 KiB in UTF-8.
        accepted = gateway.send("abc123", exact)  # Accept the exact byte limit.
        with pytest.raises(StreamRequestError) as large:  # Capture the oversize refusal.
            gateway.send("abc123", "a" * (16 * 1024 + 1))  # Exceed the limit by one byte.
        for _index in range(58):  # Reach sixty total accepted or checked requests.
            gateway.send("abc123", "x")  # Count one request in the shared window.
        with pytest.raises(StreamRequestError) as rate:  # Capture the next rate refusal.
            gateway.send("abc123", "x")  # Exceed the request rate.
        assert accepted == {"accepted": 16 * 1024, "queued": False}  # Keep the size contract.
        assert runner.sent[0] == exact  # Preserve the exact Unicode text.
        assert (large.value.code, rate.value.code) == ("too_large", "rate_limited")  # Keep codes.

    def test_input_and_resize_share_monotonic_rate_window(self) -> None:
        """Share one safe rate window across both write routes."""
        clock = [10.0]  # Keep both routes in one deterministic monotonic second.
        gateway, session, runner = _gateway(clock)  # Build one session-scoped request window.
        session.terminal.input.release()  # Send accepted input directly to the fake runner.
        for _index in range(59):  # Use requests one through 59 with input writes.
            gateway.send("abc123", "x")  # Count one input request in the shared window.
        accepted = gateway.resize("abc123", 80, 24)  # Accept resize request 60.
        with pytest.raises(StreamRequestError) as rate:  # Capture mixed-route request 61.
            gateway.send("abc123", "x")  # Refuse input after the accepted resize.
        clock[0] = 9.0  # Simulate a clock rollback without expiring safe history.
        with pytest.raises(StreamRequestError) as rollback:  # Capture the rollback request.
            gateway.resize("abc123", 81, 25)  # Refuse request 61 after the rollback.
        assert accepted == {"cols": 80, "rows": 24}  # Keep the accepted resize response.
        assert runner.sizes == [(80, 24)]  # Send only the accepted resize to the device.
        assert (rate.value.code, rollback.value.code) == ("rate_limited", "rate_limited")  # Keep codes.

    def test_two_thousand_line_paste_reaches_device_one_hundred_times(self) -> None:
        """Preserve a 2,000-line paste through the gateway and ShellClient in 100 runs."""
        paste = "".join(f"show line {index}\r" for index in range(2000))  # Build the ordered paste.
        parts = [paste[index : index + 4096] for index in range(0, len(paste), 4096)]  # Match browser chunks.
        expected = paste.encode("utf-8")  # Compare exact device bytes for each complete run.
        with FakeMistCloud() as cloud:  # Host every complete production connection.
            for run_number in range(100):  # Prove every required complete run independently.
                path = f"/shell/paste-{run_number}"  # Give each fake device one isolated route.
                device = PasteSinkShellDevice()  # Receive this run at the simulated device boundary.
                cloud.register(path, device)  # Route this production client to its fake device.
                client = self._shell_client(cloud)  # Build this run's production shell transport.
                try:  # Always close this production connection after its flow.
                    client.open(f"{cloud.base_ws_url}{path}", 80, 24)  # Open this device session.
                    gateway, session, _runner = _gateway(sender=client.send)  # Connect the gateway to ShellClient.
                    session.terminal.input.release()  # Release browser-sized parts to the transport.
                    for part in parts:  # Deliver every paste part through the production gateway.
                        gateway.send("abc123", part)  # Preserve browser order through both boundaries.
                    received = device.wait_for_input(len(expected), 5.0)  # Await this run's device bytes.
                    assert received == expected  # Require complete ordered bytes at the device boundary.
                finally:
                    client.close()  # Stop this socket before the next complete run.

    @staticmethod
    def _shell_client(cloud: FakeMistCloud, subscribe_timeout_seconds: float = 10.0) -> ShellClient:
        """Build a production shell client for the safe loopback cloud."""
        profile = TransportProfile(
            stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=True,
            subscribe_timeout_seconds=subscribe_timeout_seconds,
        )  # Allow test loopback and caller-controlled handshake timing.
        endpoint = MistStreamEndpoint(FakeApiSession(), profile)  # Supply fake authentication fields.
        policy = ShellAddressPolicy(endpoint.cloud_host, allow_loopback=True)  # Restrict the client to this host.
        return ShellClient(endpoint, policy, factory=websocket.create_connection)  # Use production socket creation.

    def test_connection_error_after_shell_reset_stops_terminal_transport(self) -> None:
        """Keep a reset connection closed before terminal input can start."""
        with FakeMistCloud() as cloud:  # Host one deterministic reset handshake.
            path = "/shell/connection-error"  # Isolate this failure from other fake routes.
            cloud.fail_handshake(path, HandshakeFault("reset"))  # Reset the TCP connection during open.
            client = self._shell_client(cloud, subscribe_timeout_seconds=0.5)  # Keep the failed open bounded.
            with pytest.raises(ConnectionError) as error:  # Capture the operating system connection failure.
                client.open(f"{cloud.base_ws_url}{path}", 80, 24)  # Open through the production shell client.
            requests = cloud.wait_for_requests(1, 1.0)  # Confirm the request reached the fake Mist cloud.
            assert requests[0].path == path  # The reset occurred on the intended shell endpoint.
            assert error.value.__class__.__name__ == "ConnectionResetError"  # Preserve the exact failure family.
            with pytest.raises(StreamRequestError) as closed:  # A failed open must leave writes unavailable.
                client.send("show version\r")  # Attempt input after the connection failure.
            assert closed.value.code == "not_open"  # The transport did not publish a partial connection.

    def test_connection_timeout_after_shell_stall_stops_terminal_transport(self) -> None:
        """Keep a stalled connection closed before terminal input can start."""
        with FakeMistCloud() as cloud:  # Host one deterministic stalled handshake.
            path = "/shell/connection-timeout"  # Isolate this failure from other fake routes.
            cloud.fail_handshake(path, HandshakeFault("stall"))  # Leave the opening handshake unanswered.
            client = self._shell_client(cloud, subscribe_timeout_seconds=0.2)  # Bound the deliberate stall.
            with pytest.raises(websocket.WebSocketTimeoutException) as error:  # Capture the handshake timeout.
                client.open(f"{cloud.base_ws_url}{path}", 80, 24)  # Open through the production shell client.
            requests = cloud.wait_for_requests(1, 1.0)  # Confirm the request reached the fake Mist cloud.
            assert requests[0].path == path  # The timeout occurred on the intended shell endpoint.
            assert "Timeout" in error.value.__class__.__name__  # Preserve the WebSocket timeout family.
            with pytest.raises(StreamRequestError) as closed:  # A timed-out open must leave writes unavailable.
                client.send("show version\r")  # Attempt input after the connection timeout.
            assert closed.value.code == "not_open"  # The transport did not publish a partial connection.

    @pytest.mark.parametrize("status_code", [403, 503], ids=["http_4xx", "http_5xx"])
    def test_http_4xx_and_http_5xx_shell_refusals_preserve_status(self, status_code: int) -> None:
        """Preserve the HTTP refusal status and keep terminal transport closed."""
        with FakeMistCloud() as cloud:  # Host one deterministic HTTP handshake refusal.
            path = f"/shell/http-{status_code}"  # Isolate each refusal status on its own endpoint.
            cloud.fail_handshake(path, HandshakeFault("refuse", status_code=status_code))  # Refuse the upgrade.
            client = self._shell_client(cloud, subscribe_timeout_seconds=0.5)  # Keep the failed open bounded.
            with pytest.raises(websocket.WebSocketBadStatusException) as error:  # Capture the HTTP refusal.
                client.open(f"{cloud.base_ws_url}{path}", 80, 24)  # Open through the production shell client.
            requests = cloud.wait_for_requests(1, 1.0)  # Confirm the request reached the fake Mist cloud.
            assert requests[0].path == path  # The refusal occurred on the intended shell endpoint.
            assert error.value.status_code == status_code  # Preserve the exact HTTP 4xx or HTTP 5xx status.
            with pytest.raises(StreamRequestError) as closed:  # A refused open must leave writes unavailable.
                client.send("show version\r")  # Attempt input after the HTTP refusal.
            assert closed.value.code == "not_open"  # The transport did not publish a partial connection.

    def test_resize_accepts_edges_and_refuses_bad_sizes(self) -> None:
        """Accept valid edges and refuse invalid dimensions."""
        gateway, _session_value, runner = _gateway()  # Build a writable terminal session.
        low = gateway.resize("abc123", 20, 5)  # Accept the low contract edge.
        high = gateway.resize("abc123", 500, 200)  # Accept the high contract edge.
        with pytest.raises(StreamRequestError) as error:  # Capture an invalid column count.
            gateway.resize("abc123", 19, 5)  # Refuse a value below the contract range.
        assert (low, high) == ({"cols": 20, "rows": 5}, {"cols": 500, "rows": 200})  # Keep payloads.
        assert runner.sizes == [(20, 5), (500, 200)]  # Send only accepted sizes.
        assert error.value.code == "bad_request"  # Keep the size refusal code.

    def test_session_and_write_refusals_preserve_contract_codes(self) -> None:
        """Preserve not-found, not-terminal, read-only, and not-open codes."""
        gateway, session, _runner = _gateway()  # Build a writable terminal session.
        plain = SimpleNamespace(terminal=None)  # Build a non-terminal session.
        screen_state = TerminalState(ByteHistory(), None, 1.0, "soon")  # Build read-only state.
        read_only = SimpleNamespace(terminal=screen_state)  # Build a read-only terminal session.
        lookup = FakeLookup({"plain": plain, "screen": read_only, "ended": session})  # Mix states.
        mixed = TerminalGateway(lookup)  # Build one gateway for refusal checks.
        session.live = False  # End the writable terminal before the last check.
        actions = [lambda: mixed.read("plain", 0, 0.0), lambda: mixed.send("screen", "x")]  # Type checks.
        actions += [lambda: mixed.send("missing", "x"), lambda: mixed.send("ended", "x")]  # State checks.
        codes = ["not_terminal", "read_only", "not_found", "not_open"]  # Keep exact contract order.
        for action, code in zip(actions, codes, strict=True):  # Run each focused refusal.
            with pytest.raises(StreamRequestError) as error:  # Capture the route refusal.
                action()  # Execute the refused operation.
            assert error.value.code == code  # Preserve the exact contract code.

    def test_bad_read_values_raise_bad_request(self) -> None:
        """Refuse invalid terminal read values."""
        gateway, _session_value, _runner = _gateway()  # Build a writable terminal session.
        actions = [lambda: gateway.read("abc123", -1, 0.0)]  # Refuse a negative cursor.
        actions += [lambda: gateway.read("abc123", 0, -0.1)]  # Refuse a negative wait.
        for action in actions:  # Run each invalid request.
            with pytest.raises(StreamRequestError) as error:  # Capture the refusal.
                action()  # Execute the invalid request.
            assert error.value.code == "bad_request"  # Preserve the common contract code.

    def test_empty_body_terminal_input_raises_bad_request(self) -> None:
        """Refuse an empty terminal input body before session lookup."""
        gateway, _session_value, runner = _gateway()  # Build a writable terminal session.
        empty_body = b""  # Model the empty HTTP request body before route text decoding.
        with pytest.raises(StreamRequestError) as error:  # Capture the empty-body refusal.
            gateway.send("abc123", empty_body.decode("utf-8"))  # Submit the empty text that the route extracted.
        assert error.value.code == "bad_request"  # Preserve the route contract code.
        assert runner.sent == []  # The empty body never reached the terminal runner.

    def test_malformed_json_terminal_input_is_sent_verbatim(self) -> None:
        """Treat malformed JSON text as terminal input instead of parsing it."""
        gateway, session, runner = _gateway()  # Build a writable terminal session.
        session.terminal.input.release()  # Send accepted input directly to the runner.
        malformed_json = "bad json"  # Build text that no JSON parser can decode.
        result = gateway.send("abc123", malformed_json)  # Submit the text through the terminal gateway.
        assert result == {"accepted": len(malformed_json), "queued": False}  # Count the exact ASCII bytes.
        assert runner.sent == [malformed_json]  # Preserve the malformed JSON text byte-for-byte.
