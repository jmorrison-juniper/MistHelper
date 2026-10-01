"""Tests for terminal state and chunk payloads."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import pytest  # The tests assert contract refusals.

from src.websocket_streams.intake.fields import StreamRequestError  # Tests verify exact refusal codes.
from src.websocket_streams.live.terminal.byte_history import ByteHistory, HistoryRead  # Tests build read values.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Tests build writable terminal state.
from src.websocket_streams.live.terminal.state import (
    TerminalChunk,
    TerminalState,
    TerminalStatus,
)  # The tests cover these classes.


class TestTerminalState:
    """Verify terminal state behavior."""

    def test_size_returns_copy_and_accepts_range_edges(self) -> None:
        """Return a copy and accept valid edge sizes."""
        state = TerminalState(ByteHistory(), TerminalInput(), 10.0, "2026-10-01T09:30:00Z")  # Build state.
        state.set_size(20, 5)  # Accept the low edge.
        low = state.size()  # Copy the low edge size.
        low.cols = 99  # Mutate the copy to prove isolation.
        state.set_size(500, 200)  # Accept the high edge.
        high = state.size()  # Copy the high edge size.
        assert (low.cols, low.rows) == (99, 5)  # The copy can change locally.
        assert (high.cols, high.rows) == (500, 200)  # The stored high edge is exact.

    def test_invalid_size_values_raise_bad_request(self) -> None:
        """Refuse terminal sizes outside the contract range."""
        state = TerminalState(ByteHistory(), TerminalInput(), 10.0, "2026-10-01T09:30:00Z")  # Build state.
        bad_values = [(19, 5), (501, 5), (20, 4), (20, 201)]  # Cover each range edge failure.
        for cols, rows in bad_values:  # Check each invalid size.
            with pytest.raises(StreamRequestError) as error:  # Capture the size refusal.
                state.set_size(cols, rows)  # This size is outside the contract range.
            assert error.value.code == "bad_request"  # The contract code is exact.

    def test_read_only_and_close(self) -> None:
        """Report read-only state and close child state."""
        writable_input = TerminalInput()  # Build a writable input queue.
        writable = TerminalState(ByteHistory(), writable_input, 10.0, "2026-10-01T09:30:00Z")  # Build shell state.
        read_only = TerminalState(ByteHistory(), None, 10.0, "2026-10-01T09:30:00Z")  # Build screen state.
        writable.close()  # Close history and input.
        closed_read = writable.history.read(0)  # Read the closed history.
        with pytest.raises(StreamRequestError) as error:  # Capture input close refusal.
            writable_input.submit("x")  # Closed input refuses later text.
        assert writable.read_only is False  # Shell state is writable.
        assert read_only.read_only is True  # Screen state is read-only.
        assert closed_read.closed is True  # Close marks the history as closed.
        assert error.value.code == "not_open"  # The contract code is exact.


class TestTerminalChunk:
    """Verify terminal read payload shape."""

    def test_payload_matches_contract_fields(self) -> None:
        """Build a terminal read answer with every contract field."""
        read = HistoryRead(b"show arp\n", 0, 9, 0, False)  # Build a byte history answer.
        status = TerminalStatus("live", "", True)  # Build status metadata.
        terminal = TerminalState(ByteHistory(), TerminalInput(), 10.0, "2026-10-01T09:30:00Z")  # Build terminal.
        chunk = TerminalChunk(read, status, terminal)  # Build a payload.
        payload = chunk.payload()  # Convert to JSON-safe data.
        expected = {
            "data": "c2hvdyBhcnAK",
            "first": 0,
            "next": 9,
            "gap": 0,
            "state": "live",
            "reason": "",
            "input_ready": True,
            "read_only": False,
            "expires_at": "2026-10-01T09:30:00Z",
        }  # Contract answer shape.
        assert payload == expected  # The payload matches the HTTP contract.
