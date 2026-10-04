"""Tests for terminal input queue behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import pytest  # The tests assert contract refusals.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Tests verify exact refusal codes.
from src.mist.realtime.websocket_streams.live.terminal.input_queue import TerminalInput  # The tests cover this class.


class FakeClock:
    """A clock that tests can move."""

    def __init__(self) -> None:
        """Build a clock at zero seconds."""
        self.value = 0.0  # Tests mutate this value directly.

    def __call__(self) -> float:
        """Return the current fake time."""
        return self.value  # The rate limiter reads this value.


class TestTerminalInput:
    """Verify queue, release, close, and rate behavior."""

    def test_queues_before_release_and_sends_in_order(self) -> None:
        """Queue early input and flush it in order."""
        sent: list[str] = []  # Keep the exact device input order.
        terminal_input = TerminalInput()  # Build an input queue.
        terminal_input.bind(sent.append)  # Bind a fake device sender.
        first = terminal_input.submit("show ")  # Queue text before output.
        second = terminal_input.submit("version\r")  # Queue a second early text.
        terminal_input.release()  # First output releases the queue.
        direct = terminal_input.submit("exit\r")  # Later input sends at once.
        assert first is True  # Early input waits in the queue.
        assert second is True  # Early input waits in the queue.
        assert direct is False  # Ready input sends at once.
        assert sent == ["show ", "version\r", "exit\r"]  # The device sees exact order.

    def test_queue_limit_refuses_more_than_4096_characters(self) -> None:
        """Refuse early input that would exceed the pending character limit."""
        terminal_input = TerminalInput()  # Build an input queue.
        terminal_input.bind(lambda _text: None)  # Bind a sender that records nothing.
        accepted = terminal_input.submit("a" * 4096)  # Fill the queue exactly.
        with pytest.raises(StreamRequestError) as error:  # Capture the queue-limit refusal.
            terminal_input.submit("b")  # One more character exceeds the cap.
        assert accepted is True  # The exact cap is accepted.
        assert error.value.code == "input_full"  # The contract code is exact.

    def test_close_drops_queue_and_refuses_later_submit(self) -> None:
        """Drop queued text and refuse later input after close."""
        sent: list[str] = []  # Keep sent text.
        terminal_input = TerminalInput()  # Build an input queue.
        terminal_input.bind(sent.append)  # Bind a fake device sender.
        queued = terminal_input.submit("queued")  # Queue text before output.
        terminal_input.close()  # Close drops queued text.
        terminal_input.release()  # A later release sends nothing.
        with pytest.raises(StreamRequestError) as error:  # Capture the close refusal.
            terminal_input.submit("late")  # Closed queues refuse input.
        assert queued is True  # The first input was queued.
        assert sent == []  # Close dropped the queued text.
        assert error.value.code == "not_open"  # The contract code is exact.

    def test_rate_limit_allows_60_requests_per_second(self) -> None:
        """Refuse the sixty-first request in one second."""
        clock = FakeClock()  # Use deterministic time.
        terminal_input = TerminalInput(clock)  # Build an input queue with a fake clock.
        for _index in range(60):  # Send exactly the allowed count.
            terminal_input.rate.check()  # Count one accepted request.
        with pytest.raises(StreamRequestError) as error:  # Capture the rate-limit refusal.
            terminal_input.rate.check()  # The next request exceeds the cap.
        clock.value = 1.0  # Move the clock outside the one-second window.
        terminal_input.rate.check()  # A new window accepts another request.
        assert error.value.code == "rate_limited"  # The contract code is exact.

    def test_submit_without_sender_raises_not_open_after_release(self) -> None:
        """Refuse direct send when no sender is bound."""
        terminal_input = TerminalInput()  # Build an unbound input queue.
        terminal_input.release()  # Make later input send directly.
        with pytest.raises(StreamRequestError) as error:  # Capture the missing sender refusal.
            terminal_input.submit("x")  # The queue has no bound sender.
        assert error.value.code == "not_open"  # The contract code is exact.
