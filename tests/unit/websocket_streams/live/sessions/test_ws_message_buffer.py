"""Tests for the WebSockets message buffer."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from src.websocket_streams.live.sessions.buffer import MessageBuffer  # The tests cover the buffer caps.


class TestMessageBuffer:
    """Verify buffer cap and read behavior."""

    def test_message_cap_drops_oldest_and_sets_gap(self) -> None:
        """Drop the oldest message when the count cap is exceeded."""
        buffer = MessageBuffer(max_messages=2, max_bytes=9999)  # Keep only two messages.
        buffer.add("2026-01-01T00:00:00Z", "text", "one", None, None)  # Store the first message.
        buffer.add("2026-01-01T00:00:01Z", "text", "two", None, None)  # Store the second message.
        buffer.add("2026-01-01T00:00:02Z", "text", "three", None, None)  # This drops the first message.
        messages, first_seq, gap = buffer.read_after(0, 10)  # Read from before the kept range.
        assert [message["seq"] for message in messages] == [2, 3]  # The newest two messages remain.
        assert first_seq == 2  # The oldest kept message has sequence two.
        assert gap is True  # The reader missed one dropped message.
        assert buffer.dropped == 1  # The drop counter records the removed message.

    def test_byte_cap_drops_oldest(self) -> None:
        """Drop old messages when the byte cap is exceeded."""
        buffer = MessageBuffer(max_messages=10, max_bytes=20)  # Use a small byte cap.
        buffer.add("2026-01-01T00:00:00Z", "text", "a" * 15, None, None)  # Store one larger message.
        buffer.add("2026-01-01T00:00:01Z", "text", "b" * 15, None, None)  # This forces a drop.
        messages, _first_seq, _gap = buffer.read_after(0, 10)  # Read the kept messages.
        assert len(messages) == 1  # Only one message fits the byte cap.
        assert messages[0]["content"] == "b" * 15  # The newest message remains.

    def test_large_message_is_shortened(self) -> None:
        """Shorten a single message above 256 KB."""
        buffer = MessageBuffer(max_messages=10, max_bytes=999999)  # Keep enough bytes for the shortened message.
        buffer.add("2026-01-01T00:00:00Z", "text", "x" * (257 * 1024), None, None)  # Add a message above the limit.
        messages, _first_seq, _gap = buffer.read_after(0, 10)  # Read the stored message.
        assert messages[0]["shortened"] is True  # The message is marked as shortened.
        assert buffer.shortened == 1  # The shortening counter increments.

    def test_limit_applies_to_read(self) -> None:
        """Return no more than the requested read limit."""
        buffer = MessageBuffer(max_messages=10, max_bytes=9999)  # Keep all test messages.
        for index in range(3):  # Add three messages.
            buffer.add("2026-01-01T00:00:00Z", "text", str(index), None, None)  # Store one message.
        messages, _first_seq, gap = buffer.read_after(1, 1)  # Ask for one message after sequence one.
        assert len(messages) == 1  # The read limit is honored.
        assert messages[0]["seq"] == 2  # The first unread sequence is returned.
        assert gap is False  # No unread message was dropped.
