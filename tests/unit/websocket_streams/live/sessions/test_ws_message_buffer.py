"""Tests for the WebSockets message buffer."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import gc  # The memory test walks the kept object graph.
import json  # The tests decode the stored JSON text.
import sys  # The memory test reads the size of each kept object.

from src.mist.realtime.websocket_streams.live.sessions.buffer.message import (
    MessageDraft,
)  # Tests supply complete message inputs.
from src.mist.realtime.websocket_streams.live.sessions.buffer.message_buffer import MessageBuffer
from src.mist.realtime.websocket_streams.live.sessions.buffer.page import MessagePage  # The tests cover the buffer.


def deep_size(root: object) -> int:
    """Return the memory of an object graph, and count each object one time.

    Args:
        root: The first object of the graph.

    Returns:
        The total size in bytes.
    """
    seen: set[int] = set()  # Shared objects count one time only.
    stack = [root]  # Walk the graph without recursion.
    total = 0  # Add each object size here.
    while stack:  # Visit each reachable object.
        item = stack.pop()  # Take the next object.
        if item is None or isinstance(item, (bool, type)) or id(item) in seen:  # Skip singletons, types, and repeats.
            continue  # These objects are not part of one message.
        seen.add(id(item))  # Remember the object.
        total += sys.getsizeof(item)  # Add the object itself.
        if not isinstance(item, (str, bytes, int, float)):  # Text and numbers hold no references.
            stack.extend(gc.get_referents(item))  # Visit the slot values and the list items.
    return total  # The caller compares this with the counted footprint.


class TestMessageBuffer:
    """Verify buffer cap and read behavior."""

    def test_message_cap_drops_oldest_and_sets_gap(self) -> None:
        """Drop the oldest message when the count cap is exceeded."""
        buffer = MessageBuffer(max_messages=2, max_bytes=9999)  # Keep only two messages.
        buffer.add(MessageDraft("2026-01-01T00:00:00Z", "text", "one"))  # Store the first message.
        buffer.add(MessageDraft("2026-01-01T00:00:01Z", "text", "two"))  # Store the second message.
        buffer.add(MessageDraft("2026-01-01T00:00:02Z", "text", "three"))  # This drops the first message.
        messages, first_seq, gap = buffer.read_after(0, 10)  # Read from before the kept range.
        assert [message.seq for message in messages] == [2, 3]  # The newest two messages remain.
        assert first_seq == 2  # The oldest kept message has sequence two.
        assert gap is True  # The reader missed one dropped message.
        assert buffer.dropped == 1  # The drop counter records the removed message.

    def test_byte_cap_drops_oldest(self) -> None:
        """Drop old messages when the memory of the kept messages passes the byte cap."""
        one = len(json.dumps("a" * 15)) + MessageBuffer.MESSAGE_OVERHEAD_BYTES  # The footprint of one message.
        buffer = MessageBuffer(max_messages=10, max_bytes=2 * one)  # Two messages fit, and a third does not.
        for letter in "abc":  # Add three messages of the same size.
            buffer.add(MessageDraft("2026-01-01T00:00:00Z", "text", letter * 15))  # The third add forces a drop.
        messages, _first_seq, _gap = buffer.read_after(0, 10)  # Read the kept messages.
        contents = [json.loads("".join(message.json_parts()))["content"] for message in messages]  # Decode each text.
        assert contents == ["b" * 15, "c" * 15]  # The oldest message left.
        assert buffer.bytes_used == 2 * one  # The counter holds the footprint of the two kept messages.
        assert buffer.dropped == 1  # The drop counter records the removed message.

    def test_large_message_is_shortened(self) -> None:
        """Shorten a single message above 256 KB."""
        buffer = MessageBuffer(max_messages=10, max_bytes=999999)  # Keep enough bytes for the shortened message.
        buffer.add(MessageDraft("2026-01-01T00:00:00Z", "text", "x" * (257 * 1024)))  # Add above the limit.
        messages, _first_seq, _gap = buffer.read_after(0, 10)  # Read the stored message.
        content = json.loads("".join(messages[0].json_parts()))["content"]  # Decode the message text.
        assert messages[0].shortened is True  # The message is marked as shortened.
        assert isinstance(content, dict) and content["shortened"] is True  # The page receives the preview form.
        assert messages[0].size == 257 * 1024 + 2  # The size is the JSON text size before shortening.
        assert buffer.shortened == 1  # The shortening counter increments.

    def test_limit_applies_to_read(self) -> None:
        """Return no more than the requested read limit."""
        buffer = MessageBuffer(max_messages=10, max_bytes=9999)  # Keep all test messages.
        for index in range(3):  # Add three messages.
            buffer.add(MessageDraft("2026-01-01T00:00:00Z", "text", str(index)))  # Store one message.
        messages, _first_seq, gap = buffer.read_after(1, 1)  # Ask for one message after sequence one.
        assert len(messages) == 1  # The read limit is honored.
        assert messages[0].seq == 2  # The first unread sequence is returned.
        assert gap is False  # No unread message was dropped.

    def test_json_text_equals_a_full_sorted_encode(self) -> None:
        """Store compact JSON text, and join it into the same text that a full encode makes."""
        buffer = MessageBuffer(max_messages=10, max_bytes=9999)  # Keep the test message.
        content = {"name": "Caf\u00e9", "values": [1, 2], "nested": {"b": 1, "a": None}}  # Use text that is not ASCII.
        stored = buffer.add(MessageDraft("2026-01-01T00:00:00Z", "json", content, "site-a", "summary line"))  # Store.
        assert stored.content_json == json.dumps(
            content, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )  # The text is compact ASCII JSON.
        payload = {
            "seq": 1,
            "received_at": "2026-01-01T00:00:00Z",
            "kind": "json",
            "content": content,
            "summary": "summary line",
            "source": "site-a",
            "size": stored.size,
            "shortened": False,
        }  # The full message payload that the contract names.
        expected = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))  # A full encode.
        assert stored.size == len(stored.content_json)  # ASCII text has one byte for each character.
        assert "".join(stored.json_parts()) == expected  # The joined text is equal to the full encode, byte for byte.
        assert stored.json_parts()[1] is stored.content_json  # The parts share the stored text, with no copy.
        assert buffer.snapshot() == [stored]  # The download copy holds the same record.

    def test_page_text_decodes_to_the_contract_shape(self) -> None:
        """Join the message texts into one read answer that a JSON reader accepts."""
        buffer = MessageBuffer(max_messages=10, max_bytes=9999)  # Keep the test messages.
        first = buffer.add(MessageDraft("2026-01-01T00:00:00Z", "text", "one"))  # Store the first message.
        second = buffer.add(MessageDraft("2026-01-01T00:00:01Z", "json", {"up": True}, "site-a"))  # Store second.
        session = {"session_id": "abc123", "title": "Caf\u00e9 stats"}  # A session payload with text that is not ASCII.
        page = MessagePage(session, [first, second], 2, 1, False)  # Two messages.
        empty = MessagePage(session, [], 0, 0, False)  # A read with no new message.
        decoded = json.loads(page.to_json_text())  # The browser decodes the same text.
        assert decoded["session"] == session and decoded["next_after"] == 2  # The small fields keep their values.
        assert decoded["first_seq"] == 1 and decoded["gap"] is False  # The cursor fields keep their values.
        assert [message["content"] for message in decoded["messages"]] == ["one", {"up": True}]  # Both messages.
        assert json.loads(empty.to_json_text())["messages"] == []  # An empty read holds an empty list.
        assert page.to_json_text().isascii()  # The answer escapes text that is not ASCII, like Flask does.

    def test_byte_cap_bounds_the_real_memory(self) -> None:
        """Keep the real memory of a full buffer under the byte cap, which proves SC-005."""
        cap = 512 * 1024  # A small cap keeps the test fast.
        buffer = MessageBuffer(max_messages=500, max_bytes=cap)  # The byte cap binds before the count cap.
        for index in range(400):  # Add more than the cap can hold.
            stamp = f"2026-01-01T00:{index // 60:02d}:{index % 60:02d}Z"  # Each message owns its time text.
            row = {"index": index, "rows": [{"name": "v" * 30, "value": value} for value in range(40)]}  # About 2 KB.
            draft = MessageDraft(stamp, "packet", row, "site-a", f"10.0.0.1 > 10.0.0.2 TCP {index}")  # Shape input.
            buffer.add(draft)  # Add one packet message.
        records = buffer.snapshot()  # Copy the kept records.
        assert buffer.dropped > 0  # The test filled the buffer past the cap.
        assert deep_size(records) <= buffer.bytes_used <= cap  # The counted footprint covers the real memory.
