"""Focused tests for terminal gateway behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import time  # Wait-cap tests use short bounded waits.
from concurrent.futures import ThreadPoolExecutor  # Long-poll tests use worker threads.
from types import SimpleNamespace  # Test sessions need small mutable records.
from unittest.mock import Mock  # Test sessions expose one observed method.

import pytest  # The tests assert contract refusals.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Tests verify refusal codes.
from src.websocket_streams.live.terminal.byte_history import ByteHistory  # Tests build terminal state.
from src.websocket_streams.live.terminal.gateway import TerminalGateway  # Tests cover this class.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Tests build writable state.
from src.websocket_streams.live.terminal.state.terminal_state import TerminalState  # Tests build terminal state.


class FakeRunner:
    """Record exact terminal input and size order."""

    def __init__(self) -> None:
        """Build an empty runner recorder."""
        self.sent: list[str] = []  # Keep exact input order.
        self.sizes: list[tuple[int, int]] = []  # Keep accepted size order.

    def send_input(self, text: str) -> None:
        """Record exact input text."""
        self.sent.append(text)  # Tests compare exact device input.

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


def _gateway(clock: list[float] | None = None) -> tuple[TerminalGateway, SimpleNamespace, FakeRunner]:
    """Build one live writable terminal gateway."""
    values = clock if clock is not None else [0.0]  # Use caller time or a new clock.
    terminal_input = TerminalInput(lambda: values[0])  # Build deterministic rate state.
    terminal = TerminalState(ByteHistory(), terminal_input, 1800.0, "2026-10-01T09:30:00Z")  # Build state.
    runner = FakeRunner()  # Record exact input and resize calls.
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

    def test_bad_read_and_empty_input_values_raise_bad_request(self) -> None:
        """Refuse invalid read values and empty input."""
        gateway, _session_value, _runner = _gateway()  # Build a writable terminal session.
        actions = [lambda: gateway.read("abc123", -1, 0.0)]  # Refuse a negative cursor.
        actions += [lambda: gateway.read("abc123", 0, -0.1)]  # Refuse a negative wait.
        actions += [lambda: gateway.send("abc123", "")]  # Refuse empty input.
        for action in actions:  # Run each invalid request.
            with pytest.raises(StreamRequestError) as error:  # Capture the refusal.
                action()  # Execute the invalid request.
            assert error.value.code == "bad_request"  # Preserve the common contract code.
