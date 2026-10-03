"""Tests for terminal byte history."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from concurrent.futures import ThreadPoolExecutor  # Wait tests run one read in another thread.

import pytest  # The tests assert contract refusals.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Tests verify exact refusal codes.
from src.mist.realtime.websocket_streams.live.terminal.byte_history import ByteHistory  # The tests cover this class.


class TestByteHistory:
    """Verify retained terminal byte reads."""

    def test_trim_reports_gap_and_keeps_newest_bytes(self) -> None:
        """Trim old bytes and report the lost byte count."""
        history = ByteHistory(limit=5)  # Use a small cap so trimming is visible.
        history.append(b"abcdef")  # Add more bytes than the cap.
        result = history.read(0)  # Read from the beginning.
        assert result.data == b"bcdef"  # The newest five bytes remain.
        assert result.first == 1  # The first absolute byte was trimmed.
        assert result.next_position == 6  # The cursor follows the returned bytes.
        assert result.gap == 1  # The read reports the one lost byte.
        assert result.closed is False  # The history is still live.

    def test_bad_positions_raise_bad_request(self) -> None:
        """Refuse negative and future read positions."""
        history = ByteHistory(limit=10)  # Build an empty history.
        with pytest.raises(StreamRequestError) as negative:  # Capture the negative position refusal.
            history.read(-1)  # Negative positions are invalid.
        with pytest.raises(StreamRequestError) as future:  # Capture the future position refusal.
            history.read(1)  # Future positions are invalid.
        assert negative.value.code == "bad_request"  # The contract code is exact.
        assert future.value.code == "bad_request"  # The contract code is exact.

    def test_wait_returns_when_bytes_arrive(self) -> None:
        """Wake a waiting read when output arrives."""
        history = ByteHistory(limit=10)  # Build an empty history.
        with ThreadPoolExecutor(max_workers=1) as pool:  # Run the waiting read in another thread.
            future = pool.submit(history.read, 0, 1.0)  # Start a bounded wait.
            history.append(b"ok")  # Wake the waiting read with output.
            result = future.result(timeout=2.0)  # Bound the test wait.
        assert result.data == b"ok"  # The read returns the appended bytes.
        assert result.next_position == 2  # The cursor advances by the byte count.

    def test_close_wakes_waiting_read(self) -> None:
        """Wake a waiting read when the history closes."""
        history = ByteHistory(limit=10)  # Build an empty history.
        with ThreadPoolExecutor(max_workers=1) as pool:  # Run the waiting read in another thread.
            future = pool.submit(history.read, 0, 1.0)  # Start a bounded wait.
            history.close()  # Wake the waiting read without output.
            result = future.result(timeout=2.0)  # Bound the test wait.
        assert result.data == b""  # No output arrived.
        assert result.closed is True  # The read reports the closed state.

    def test_read_answer_is_limited_to_512_kib(self) -> None:
        """Return a large backlog in several reads."""
        history = ByteHistory(limit=1024 * 1024)  # Keep the full test backlog.
        history.append(b"a" * (512 * 1024 + 3))  # Add more than one read answer can hold.
        first = history.read(0)  # Read the first chunk.
        second = history.read(first.next_position)  # Read the remaining bytes.
        assert len(first.data) == 512 * 1024  # The first answer is capped.
        assert first.next_position == 512 * 1024  # The cursor stops at the answer cap.
        assert second.data == b"aaa"  # The second read returns the tail.
