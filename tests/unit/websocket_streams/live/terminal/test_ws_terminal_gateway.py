"""Tests for terminal gateway behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import time  # Wait-cap tests use short bounded waits.
from concurrent.futures import ThreadPoolExecutor  # Gateway wait tests run reads in worker threads.

import pytest  # The tests assert contract refusals.

import websocket  # Failure tests build the same exception type as websocket-client.
from src.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Tests build minimal definitions.
from src.websocket_streams.intake.fields import StreamRequestError  # Tests verify exact refusal codes.
from src.websocket_streams.intake.start_request import StartRequest  # Tests build checked requests by hand.
from src.websocket_streams.live.sessions.buffer import MessageBuffer  # Tests inject a small message buffer.
from src.websocket_streams.live.sessions.manager import RunnerFactory, StreamSessionManager  # Real paste path.
from src.websocket_streams.live.sessions.record import SessionState, StreamSession  # Tests build fake sessions.
from src.websocket_streams.live.sessions.settings import StreamSettings  # Real paste path uses normal settings.
from src.websocket_streams.live.terminal.byte_history import ByteHistory  # Tests build terminal state.
from src.websocket_streams.live.terminal.gateway import TerminalGateway  # The tests cover this class.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Tests build writable state.
from src.websocket_streams.live.terminal.state import TerminalState  # Tests build terminal state.
from src.websocket_streams.live.transport.endpoint import (
    ConnectFailure,
    TransportProfile,
)  # Real paste path uses loopback cloud.
from tests.support.fake_mist_cloud.api import FakeApiSession  # Real paste path uses fake Mist triggers.
from tests.support.fake_mist_cloud.devices import ShellDevice  # Real paste path uses fake shell device.
from tests.support.fake_mist_cloud.server import (  # Loopback server for paste test.
    FakeConnection,
    FakeMistCloud,
    HandshakeFault,  # Fake cloud handshake failure control.
)


class FakeClock:
    """A clock that tests can move."""

    def __init__(self) -> None:
        """Build a clock at zero seconds."""
        self.value = 0.0  # Tests mutate this value directly.

    def __call__(self) -> float:
        """Return the current fake time."""
        return self.value  # The session and rate limiter read this value.


class FakeRunner:
    """A fake terminal runner."""

    def __init__(self) -> None:
        """Build an empty runner recorder."""
        self.sent: list[str] = []  # Keep exact input order.
        self.sizes: list[tuple[int, int]] = []  # Keep each accepted size.

    def send_input(self, text: str) -> None:
        """Record exact input text.

        Args:
            text: The exact terminal input text.
        """
        self.sent.append(text)  # Tests compare exact text order.

    def resize(self, cols: int, rows: int) -> None:
        """Record exact terminal size.

        Args:
            cols: The column count.
            rows: The row count.
        """
        self.sizes.append((cols, rows))  # Tests compare exact size order.


class FakeLookup:
    """A fake session lookup service."""

    def __init__(self, sessions: dict[str, StreamSession]) -> None:
        """Build a lookup with known sessions.

        Args:
            sessions: The session map by identifier.
        """
        self._sessions = sessions  # The gateway asks this map for sessions.

    def session(self, session_id: str) -> StreamSession:
        """Return a session or raise not_found.

        Args:
            session_id: The public session identifier.

        Returns:
            The matching session.
        """
        session = self._sessions.get(session_id)  # Look up the requested session.
        if session is None:  # Unknown sessions use the contract refusal.
            raise StreamRequestError("not_found", "The session was not found.")  # Contract error.
        return session  # Return the known session.


class QuietShellDevice(ShellDevice):
    """A fake shell that records input without echoing every pasted byte."""

    def _process_input(self, connection: FakeConnection, data: bytes) -> None:
        """Skip echo output so the paste stress test stays bounded.

        Args:
            connection: The open fake shell connection.
            data: The bytes already recorded by the base class.
        """
        del connection, data  # The base class already recorded the bytes, and this device sends no echo.
        return None  # The test verifies received bytes only.


class TestTerminalGateway:
    """Verify terminal gateway contract behavior."""

    def test_read_without_wait_returns_available_bytes(self) -> None:
        """Read immediately when bytes are available."""
        gateway, session, _runner = self._gateway()  # Build a writable terminal session.
        session.add_bytes(b"abc")  # Add terminal output.
        payload = gateway.read("abc123", 0, 0.0)  # Read without a long poll.
        assert payload["data"] == "YWJj"  # The answer carries base64 bytes.
        assert payload["next"] == 3  # The cursor advances by the byte count.
        assert payload["input_ready"] is False  # No first output flag was set.

    def test_waiting_read_wakes_on_new_bytes(self) -> None:
        """Wake a waiting gateway read when output arrives."""
        gateway, session, _runner = self._gateway()  # Build a writable terminal session.
        with ThreadPoolExecutor(max_workers=1) as pool:  # Run the waiting read in another thread.
            future = pool.submit(gateway.read, "abc123", 0, 1.0)  # Start a bounded long poll.
            self._wait_for_waiters(gateway, 1)  # Wait until the gateway has reserved a slot.
            session.add_bytes(b"ok")  # Wake the long poll with output.
            payload = future.result(timeout=2.0)  # Bound the test wait.
        assert payload["data"] == "b2s="  # The answer carries the new bytes.
        assert payload["next"] == 2  # The cursor advances by two bytes.

    def test_waiting_read_wakes_on_close(self) -> None:
        """Wake a waiting gateway read when the session ends."""
        gateway, session, _runner = self._gateway()  # Build a writable terminal session.
        with ThreadPoolExecutor(max_workers=1) as pool:  # Run the waiting read in another thread.
            future = pool.submit(gateway.read, "abc123", 0, 1.0)  # Start a bounded long poll.
            self._wait_for_waiters(gateway, 1)  # Wait until the gateway has reserved a slot.
            session.finish(SessionState.FINISHED, "done")  # Close the terminal state.
            payload = future.result(timeout=2.0)  # Bound the test wait.
        assert payload["data"] == ""  # No output arrived before close.
        assert payload["state"] == "finished"  # The read returns the final state.
        assert payload["reason"] == "done"  # The read returns the final reason.

    def test_wait_limit_of_8_returns_ninth_read_immediately(self) -> None:
        """Answer the ninth process-wide waiting read at once."""
        gateway, session, _runner = self._gateway()  # Build a writable terminal session.
        with ThreadPoolExecutor(max_workers=8) as pool:  # Fill all wait slots.
            futures = [pool.submit(gateway.read, "abc123", 0, 1.0) for _index in range(8)]  # Start 8 waits.
            self._wait_for_waiters(gateway, 8)  # Wait until each slot is reserved.
            ninth = gateway.read("abc123", 0, 1.0)  # This read cannot reserve a wait slot.
            session.finish(SessionState.FINISHED, "done")  # Release the waiting reads.
            results = [future.result(timeout=2.0) for future in futures]  # Confirm each worker ended.
        assert ninth["data"] == ""  # The ninth read returns immediately with no data.
        assert [result["state"] for result in results] == ["finished"] * 8  # All waiters saw the close.

    def test_ended_session_read_returns_final_state(self) -> None:
        """Read an ended terminal session without a wait."""
        gateway, session, _runner = self._gateway()  # Build a writable terminal session.
        session.add_bytes(b"bye")  # Add output before the end.
        session.finish(SessionState.STOPPED, "operator")  # End the session.
        payload = gateway.read("abc123", 0, 0.0)  # Read after the end.
        assert payload["data"] == "Ynll"  # The history remains readable.
        assert payload["state"] == "stopped"  # The final state is visible.
        assert payload["reason"] == "operator"  # The final reason is visible.

    def test_not_terminal_read_only_not_found_and_not_open_refusals(self) -> None:
        """Refuse sessions that cannot accept terminal operations."""
        _gateway, session, _runner = self._gateway()  # Build a writable terminal session.
        not_terminal = self._session(FakeClock(), None)  # Build a message-list session.
        screen = self._screen_session(FakeClock())  # Build a read-only terminal session.
        lookup = FakeLookup({"abc123": session, "plain": not_terminal, "screen": screen})  # Build lookup.
        mixed_gateway = TerminalGateway(lookup)  # Use the mixed session lookup.
        session.finish(SessionState.FINISHED, "done")  # End the writable terminal.
        checks = [
            lambda: mixed_gateway.read("plain", 0, 0.0),
            lambda: mixed_gateway.send("screen", "x"),
            lambda: mixed_gateway.send("missing", "x"),
            lambda: mixed_gateway.send("abc123", "x"),
        ]  # Cover the four refusal paths.
        expected = ["not_terminal", "read_only", "not_found", "not_open"]  # Exact refusal code order.
        for action, code in zip(checks, expected, strict=True):  # Run each refusal case.
            with pytest.raises(StreamRequestError) as error:  # Capture the contract refusal.
                action()  # Execute the refused gateway action.
            assert error.value.code == code  # The contract code is exact.

    def test_queued_send_then_release_preserves_order(self) -> None:
        """Queue input before first output and release it in order."""
        gateway, session, runner = self._gateway()  # Build a writable terminal session.
        first = gateway.send("abc123", "show ")  # Queue early input.
        second = gateway.send("abc123", "version\r")  # Queue more early input.
        session.mark_input_ready()  # First output releases queued input.
        third = gateway.send("abc123", "exit\r")  # Later input sends at once.
        assert first == {"accepted": 5, "queued": True}  # The first input is queued.
        assert second == {"accepted": 8, "queued": True}  # The second input is queued.
        assert third == {"accepted": 5, "queued": False}  # The third input is direct.
        assert runner.sent == ["show ", "version\r", "exit\r"]  # The device order is exact.

    def test_too_large_and_exact_16_kib_unicode_input(self) -> None:
        """Accept exactly 16 KiB and refuse one byte more."""
        gateway, session, runner = self._gateway()  # Build a writable terminal session.
        session.mark_input_ready()  # Direct sends avoid the early 4,096 character cap.
        exact = "é" * 8192  # This text is exactly 16 KiB in UTF-8.
        accepted = gateway.send("abc123", exact)  # Send the exact byte limit.
        with pytest.raises(StreamRequestError) as error:  # Capture the oversize refusal.
            gateway.send("abc123", "a" * (16 * 1024 + 1))  # Send one byte too many.
        assert accepted == {"accepted": 16 * 1024, "queued": False}  # The exact byte limit passes.
        assert runner.sent == [exact]  # The accepted Unicode text reaches the runner.
        assert error.value.code == "too_large"  # The contract code is exact.

    def test_rate_limited_on_sixty_first_request(self) -> None:
        """Refuse the sixty-first terminal request in one second."""
        clock = FakeClock()  # Use deterministic rate time.
        gateway, session, _runner = self._gateway(clock)  # Build a writable terminal session.
        session.mark_input_ready()  # Direct sends keep the queue size out of this test.
        results = [gateway.send("abc123", "x") for _index in range(60)]  # Send the allowed request count.
        with pytest.raises(StreamRequestError) as error:  # Capture the rate-limit refusal.
            gateway.send("abc123", "x")  # The sixty-first request exceeds the cap.
        assert results[-1] == {"accepted": 1, "queued": False}  # The sixtieth request succeeds.
        assert error.value.code == "rate_limited"  # The contract code is exact.

    def test_resize_accepts_edges_and_refuses_out_of_range(self) -> None:
        """Accept and refuse terminal size range edges."""
        accepted_values = [(20, 5), (500, 200)]  # Cover both valid edges.
        for cols, rows in accepted_values:  # Build a fresh session for each valid size.
            gateway, session, runner = self._gateway(FakeClock())  # Build a writable terminal session.
            session.mark_input_ready()  # Mark input ready before resize.
            payload = gateway.resize("abc123", cols, rows)  # Send the size.
            assert payload == {"cols": cols, "rows": rows}  # The answer returns the accepted size.
            assert runner.sizes == [(cols, rows)]  # The runner receives the accepted size.
        bad_values = [(19, 5), (501, 5), (20, 4), (20, 201)]  # Cover each invalid edge.
        for cols, rows in bad_values:  # Build a fresh session for each invalid size.
            gateway, session, _runner = self._gateway(FakeClock())  # Build a writable terminal session.
            session.mark_input_ready()  # Mark input ready before resize.
            with pytest.raises(StreamRequestError) as error:  # Capture the size refusal.
                gateway.resize("abc123", cols, rows)  # This size is invalid.
            assert error.value.code == "bad_request"  # The contract code is exact.

    def test_bad_after_and_wait_values_raise_bad_request(self) -> None:
        """Refuse invalid read cursor and wait values."""
        gateway, _session, _runner = self._gateway()  # Build a writable terminal session.
        cases = [(-1, 0.0), (0, -0.1), (1, 0.0)]  # Cover negative cursor, negative wait, and future cursor.
        for after, wait in cases:  # Run each invalid read.
            with pytest.raises(StreamRequestError) as error:  # Capture the read refusal.
                gateway.read("abc123", after, wait)  # The read values are invalid.
            assert error.value.code == "bad_request"  # The contract code is exact.

    def test_sc002_paste_stress_keeps_exact_device_bytes(self) -> None:
        """SC-002: send 100 large pastes through the real manager and shell runner."""
        clock = FakeClock()  # The gateway rate limiter reads this fake time.
        source = self._paste_source()  # Build one 2,000-line paste body.
        parts = self._split_utf8(source, 4096)  # Match the page chunk size with UTF-8 boundaries.
        expected = b""  # Keep the cumulative byte stream expected at the fake device.
        with FakeMistCloud() as cloud:  # Start the loopback WebSocket server.
            shell = QuietShellDevice()  # Record input without echoing every byte back to the runner.
            cloud.register("/shell/default", shell)  # The fake API session returns this shell path.
            manager = self._real_manager(cloud, clock)  # Build a real manager with the real runner factory.
            gateway = TerminalGateway(manager)  # Send paste chunks through the production gateway.
            try:  # Always stop the runner before the fake cloud closes.
                session_id = str(manager.start(self._shell_request())["session_id"])  # Start one shell session.
                self._wait_for_terminal_ready(manager, session_id)  # Wait until first output released input.
                for _run in range(100):  # Repeat the paste to catch chunk ordering defects.
                    expected += self._send_parts(gateway, session_id, parts)  # Send one complete paste.
                    received = shell.wait_for_input(len(expected), 2.0)  # Wait for all bytes from this run.
                    assert received == expected  # The device receives exactly the original UTF-8 bytes.
                    clock.value += 1.1  # Open a new limiter window without slowing the test.
            finally:  # End the shell thread before the context manager closes sockets.
                manager.shutdown()  # Stop the real shell runner and any reaper thread.

    @pytest.mark.parametrize(
        ("fault", "error"),
        [
            (
                HandshakeFault("refuse", status_code=403),
                websocket.WebSocketBadStatusException("Handshake status 403", 403),
            ),
            (
                HandshakeFault("refuse", status_code=503),
                websocket.WebSocketBadStatusException("Handshake status 503", 503),
            ),
            (HandshakeFault("stall"), TimeoutError("The handshake stalled.")),
            (HandshakeFault("reset"), ConnectionError("The peer reset the handshake.")),
        ],
    )
    def test_real_manager_open_failures_are_readable_through_gateway(
        self,
        fault: HandshakeFault,
        error: BaseException,
    ) -> None:
        """Terminal reads show final state after real shell open failures."""
        expected = ConnectFailure.reason(error)  # Compute expected text through the production mapper.
        assert isinstance(expected, str)  # Each table row must map to public operator text.
        clock = FakeClock()  # Use deterministic rate time for the gateway.
        with FakeMistCloud() as cloud:  # The fake cloud drives the real WebSocket open path.
            cloud.fail_handshake("/shell/fail", fault)  # Force this shell path to fail its handshake.
            api = FakeApiSession(cloud)  # Build a fake Mist API session.
            api.add_override("/shell", status_code=200, data={"url": f"{cloud.base_ws_url}/shell/fail"})  # Route.
            manager = self._real_manager(cloud, clock, api)  # Use the real manager and shell runner.
            gateway = TerminalGateway(manager)  # Read the terminal through the gateway under test.
            session_id = str(manager.start(self._shell_request())["session_id"])  # Start returns before failure.
            session = self._wait_for_state(manager, session_id, {SessionState.FAILED}, timeout=5.0)  # Wait.
            payload = gateway.read(session_id, 0, 0.0)  # Read the final terminal state through gateway.
            requests = cloud.wait_for_requests(1, 5.0)  # Prove that the WebSocket path was attempted.
        assert requests[0].path == "/shell/fail"  # The fake cloud recorded the failed open.
        assert session.reason == expected  # The stored session has the mapped reason.
        assert payload["reason"] == expected  # The gateway answer exposes the mapped reason.
        assert "fake-token" not in payload["reason"]  # The reason must not expose secrets.

    def test_bad_json_trigger_body_is_readable_through_gateway(self) -> None:
        """A malformed trigger body reaches the gateway as a failed terminal."""
        clock = FakeClock()  # Use deterministic gateway time.
        with FakeMistCloud() as cloud:  # The fake cloud proves no WebSocket open happens.
            api = FakeApiSession(cloud)  # Build a fake Mist API session.
            api.add_override("/shell", status_code=200, data="bad json")  # Model JSONDecodeError output.
            manager = self._real_manager(cloud, clock, api)  # Use the real manager and shell runner.
            gateway = TerminalGateway(manager)  # Read the final terminal state through gateway.
            session_id = str(manager.start(self._shell_request())["session_id"])  # Start returns before failure.
            session = self._wait_for_state(manager, session_id, {SessionState.FAILED})  # Wait for failure.
            payload = gateway.read(session_id, 0, 0.0)  # Read the failure through the gateway.
        assert cloud.requests == []  # A malformed trigger body must not open a WebSocket.
        assert session.reason == "The Mist cloud did not return a terminal address."  # Plain reason is stored.
        assert payload["reason"] == "The Mist cloud did not return a terminal address."  # Gateway reports it.

    def _gateway(self, clock: FakeClock | None = None) -> tuple[TerminalGateway, StreamSession, FakeRunner]:
        """Build a gateway with one writable terminal session.

        Args:
            clock: The fake clock, or None for a new clock.

        Returns:
            The gateway, session, and runner.
        """
        chosen_clock = clock if clock is not None else FakeClock()  # Use a deterministic clock by default.
        terminal_input = TerminalInput(chosen_clock)  # Build a writable input queue.
        terminal = TerminalState(ByteHistory(), terminal_input, 1800.0, "2026-10-01T09:30:00Z")  # Build state.
        session = self._session(chosen_clock, terminal)  # Build a terminal session.
        runner = FakeRunner()  # Build a fake runner.
        terminal_input.bind(runner.send_input)  # Bind the runner input sender.
        session.runner = runner  # Store the runner on the session.
        session.mark_live()  # Make the session accept terminal bytes.
        gateway = TerminalGateway(FakeLookup({"abc123": session}))  # Build the gateway.
        return gateway, session, runner  # Return all test handles.

    def _screen_session(self, clock: FakeClock) -> StreamSession:
        """Build a read-only terminal session.

        Args:
            clock: The fake clock.

        Returns:
            A live read-only terminal session.
        """
        terminal = TerminalState(ByteHistory(), None, 1800.0, "2026-10-01T09:30:00Z")  # Build screen state.
        session = self._session(clock, terminal)  # Build a terminal session.
        session.mark_live()  # Make the session readable.
        return session  # Return the read-only session.

    def _session(self, clock: FakeClock, terminal: TerminalState | None) -> StreamSession:
        """Build one test session.

        Args:
            clock: The fake clock.
            terminal: The terminal state, or None.

        Returns:
            A new stream session.
        """
        definition = ChannelDefinition(
            "site.stats.devices", "site", "Device statistics", "Live data.", "/sites/a"
        )  # Build definition.
        request = StartRequest("shell", definition, {"site_id": ("site-a",)}, {}, "Shell - HQ")  # Build request.
        buffer = MessageBuffer(10, 9999)  # Build a small message buffer.
        return StreamSession("abc123", request, buffer, clock, terminal)  # Return a session record.

    def _wait_for_waiters(self, gateway: TerminalGateway, count: int) -> None:
        """Wait until the gateway has the expected waiter count.

        Args:
            gateway: The gateway under test.
            count: The expected waiting-read count.
        """
        deadline = time.monotonic() + 1.0  # Bound the wait for the test.
        while time.monotonic() < deadline:  # Poll for a bounded period.
            if gateway._waiting_reads == count:  # The gateway uses a process-wide wait counter.
                return  # The expected count is present.
            time.sleep(0.01)  # Sleep briefly so worker threads can enter the wait.
        raise AssertionError(f"expected {count} waiters")  # Fail with the expected count.

    def _real_manager(
        self, cloud: FakeMistCloud, clock: FakeClock, api: FakeApiSession | None = None
    ) -> StreamSessionManager:
        """Build a real session manager for loopback shell testing.

        Args:
            cloud: The started fake Mist cloud.
            clock: The fake monotonic clock for terminal rate checks.
            api: The fake API session, or None for a default session.

        Returns:
            A manager that uses real shell runners against the fake cloud.
        """
        profile = TransportProfile(
            stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
            allow_loopback=True,
            read_timeout_seconds=0.2,
            subscribe_timeout_seconds=0.2,
            reconnect_delays=(),
        )  # Keep transport waits short and allow the loopback shell URL.
        api_session = api if api is not None else FakeApiSession(cloud)  # Use caller overrides when provided.
        factory = RunnerFactory(api_session, profile)  # Build real runners with fake Mist triggers.
        settings = StreamSettings(max_sessions=1, max_stream_seconds=120)  # One reused shell keeps the test fast.
        return StreamSessionManager(settings, factory, clock)  # Return the real manager under test.

    def _wait_for_state(
        self, manager: StreamSessionManager, session_id: str, states: set[SessionState], timeout: float = 2.0
    ) -> StreamSession:
        """Wait until one session reaches an expected state.

        Args:
            manager: The manager that owns the session.
            session_id: The selected session identifier.
            states: Acceptable final states.
            timeout: Maximum wait seconds.

        Returns:
            The session after it reaches one expected state.
        """
        deadline = time.monotonic() + timeout  # Bound each async assertion.
        while time.monotonic() < deadline:  # Poll for a short time.
            session = manager.session(session_id)  # Read the current session state.
            if session.state in states:  # The background runner reached the target state.
                return session  # The caller can assert the reason.
            time.sleep(0.01)  # Avoid a busy loop while the runner thread works.
        return manager.session(session_id)  # Return the observed state for assertion failure context.

    def _shell_request(self) -> StartRequest:
        """Build a checked shell request for the paste test.

        Returns:
            A shell start request.
        """
        target = FieldSpec("device_id", "Device", FieldKind.UUID, picker="devices")  # Build the device field.
        definition = UtilityDefinition(
            "ex.shell", "ex", "createShellSession", "Shell", "Open a shell.", (), Safety.SHELL, "terminal", (target,)
        )  # Build the shell utility definition.
        return StartRequest(
            "shell", definition, {"site_id": ("site-a",), "device_id": ("dev-a",)}, {}, "Shell", device_name="ap-a"
        )  # Return a checked shell request.

    def _wait_for_terminal_ready(self, manager: StreamSessionManager, session_id: str) -> None:
        """Wait until the real shell runner releases terminal input.

        Args:
            manager: The manager that owns the shell session.
            session_id: The shell session identifier.
        """
        deadline = time.monotonic() + 2.0  # Bound the wait so a bad runner fails fast.
        while time.monotonic() < deadline:  # Poll until first output reaches the session.
            if manager.session(session_id).payload()["input_ready"] is True:  # The queue has been released.
                return  # The test can now send directly.
            time.sleep(0.01)  # Let the runner thread read the fake banner.
        raise AssertionError("terminal input was not ready")  # Give the failing readiness state.

    def _send_parts(self, gateway: TerminalGateway, session_id: str, parts: list[str]) -> bytes:
        """Send one paste as ordered gateway chunks.

        Args:
            gateway: The terminal gateway under test.
            session_id: The shell session identifier.
            parts: UTF-8-safe paste chunks.

        Returns:
            The bytes that should arrive at the fake shell device.
        """
        expected = b""  # Accumulate the exact bytes for this paste.
        for part in parts:  # Send one browser-sized chunk at a time.
            payload = gateway.send(session_id, part)  # Exercise production validation and queueing.
            expected += part.encode("utf-8")  # The fake device sees UTF-8 bytes after the NUL prefix.
            assert payload == {"accepted": len(part.encode("utf-8")), "queued": False}  # Input is direct.
        return expected  # Return the complete paste byte stream.

    def _paste_source(self) -> str:
        """Build the multi-byte paste body used by SC-002.

        Returns:
            A 2,000-line paste string.
        """
        return "".join(
            f"line {index:04d}\tvalue-é\t日本\tcolumn {index % 7}  \r" for index in range(2000)
        )  # Include tabs, UTF-8, and trailing spaces before Enter.

    def _split_utf8(self, text: str, limit: int) -> list[str]:
        """Split text without crossing UTF-8 byte boundaries.

        Args:
            text: The source text.
            limit: The maximum byte count in each chunk.

        Returns:
            Ordered chunks at or below the byte limit.
        """
        chunks: list[str] = []  # Store chunks for ordered sending.
        current: list[str] = []  # Accumulate characters for one chunk.
        current_size = 0  # Track bytes in the current chunk.
        for character in text:  # Python iterates Unicode code points.
            size = len(character.encode("utf-8"))  # UTF-8 size decides the split point.
            if current and current_size + size > limit:  # The next character would exceed the limit.
                chunks.append("".join(current))  # Save the current valid chunk.
                current = []  # Start the next chunk.
                current_size = 0  # Reset the byte count for the next chunk.
            current.append(character)  # Add the character to the current chunk.
            current_size += size  # Track the resulting byte count.
        if current:  # Save the final chunk.
            chunks.append("".join(current))  # Keep the tail in order.
        return chunks  # Return all chunks.
