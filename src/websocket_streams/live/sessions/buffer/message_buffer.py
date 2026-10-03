"""Keep bounded messages for one WebSocket session."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Buffer actions use the shared structured logger.
from collections import deque  # The oldest message leaves first.
from itertools import islice  # Reads stop at the requested limit.

from src.websocket_streams.live.sessions.buffer.encoding import MessageContentEncoder  # Encode content once.
from src.websocket_streams.live.sessions.buffer.message import (
    MessageDraft,
    StreamMessage,
)  # Store draft and final records.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies bounded JSON logging.


class BufferMetrics:
    """Expose bounded buffer measurements."""

    MESSAGE_OVERHEAD_BYTES = 320  # Preserve the measured record memory margin.
    _bytes: int  # Concrete buffers update the retained memory count.
    _next_seq: int  # Concrete buffers reserve monotonically increasing sequences.
    _messages: deque[StreamMessage]  # Concrete buffers keep records in sequence order.

    @property
    def bytes_used(self) -> int:
        """Return the counted memory of kept messages."""
        return self._bytes  # The buffer updates this total on each add and drop.

    @property
    def last_seq(self) -> int:
        """Return the newest sequence number, or zero when empty."""
        return self._next_seq - 1  # The next sequence is one above the newest record.

    @property
    def first_seq(self) -> int:
        """Return the oldest sequence number, or zero when empty."""
        return self._messages[0].seq if self._messages else 0  # Empty buffers have no cursor.

    @classmethod
    def footprint(cls, message: StreamMessage) -> int:
        """Return the conservative memory count for one message."""
        text_bytes = (
            len(message.content_json) + len(message.summary or "") + len(message.source or "")
        )  # Count owned text.
        return text_bytes + cls.MESSAGE_OVERHEAD_BYTES  # Include the record, time, numbers, and deque slot.


class MessageBuffer(BufferMetrics):
    """Store messages under count and memory limits."""

    MAX_MESSAGE_BYTES = MessageContentEncoder.MAX_MESSAGE_BYTES  # Keep the public limit used by focused tests.

    def __init__(self, max_messages: int, max_bytes: int) -> None:
        """Build one empty bounded buffer."""
        self._max_messages = max_messages  # Settings define the count cap.
        self._max_bytes = max_bytes  # Settings define the memory cap.
        self._messages: deque[StreamMessage] = deque()  # Keep sequence order.
        self._bytes, self._next_seq = 0, 1  # Start empty with sequence one.
        self.dropped, self.shortened = 0, 0  # Expose existing session counters.
        self._encoder = MessageContentEncoder()  # Encode and shorten content in one collaborator.
        self._logger = StructuredTransportLogger(logging.getLogger(__name__))  # Use bounded structured records.

    def add(self, draft: MessageDraft) -> StreamMessage:
        """Add one message and enforce both limits."""
        self._logger.emit(
            logging.DEBUG, "session_message_add_start", {"count": self._next_seq}
        )  # Log safe sequence data.
        content_json, size, shortened = self._encoder.encode(draft.content)  # Encode once and apply the message limit.
        message = StreamMessage(
            self._next_seq, draft.received_at, draft.kind, content_json, size, shortened, draft.source, draft.summary
        )  # Store one immutable record.
        self._messages.append(message)  # Add the newest record at the right side.
        self._next_seq += 1  # Reserve the next sequence number.
        self._bytes += self.footprint(message)  # Count the new record memory.
        self.shortened += int(shortened)  # Preserve the public shortening counter.
        self._trim()  # Drop old records until both caps are safe.
        self._logger.emit(logging.DEBUG, "session_message_add_complete", {"count": message.seq})  # Confirm safely.
        return message  # The session updates its rate window from this accepted record.

    def read_after(self, after: int, limit: int) -> tuple[list[StreamMessage], int, bool]:
        """Return kept records after one sequence cursor."""
        newer = (message for message in self._messages if message.seq > after)  # Keep current sequence order.
        selected = list(islice(newer, limit))  # Stop after the requested count.
        gap = bool(self._messages and after < self.first_seq - 1 and self.dropped)  # Report dropped unread data.
        fields = {"count": len(selected), "status": "gap" if gap else "complete"}  # Use bounded read evidence.
        self._logger.emit(logging.DEBUG, "session_message_read_complete", fields)  # Log no content.
        return selected, self.first_seq, gap  # Return copied references and gap metadata.

    def snapshot(self) -> list[StreamMessage]:
        """Return a small reference copy for a download."""
        self._logger.emit(logging.INFO, "session_message_snapshot_start")  # Log before copying the deque.
        records = list(self._messages)  # Let downloads continue while later messages arrive.
        self._logger.emit(logging.DEBUG, "session_message_snapshot_complete", {"count": len(records)})  # Log the count.
        return records  # Share immutable message text with the buffer.

    def _trim(self) -> None:
        """Drop oldest records until both limits are satisfied."""
        while self._messages and (
            len(self._messages) > self._max_messages or self._bytes > self._max_bytes
        ):  # Apply both caps.
            removed = self._messages.popleft()  # Remove the oldest record first.
            self._bytes = max(0, self._bytes - self.footprint(removed))  # Release its counted memory.
            self.dropped += 1  # Preserve the public dropped-message count.
            self._logger.emit(logging.DEBUG, "session_message_drop", {"count": removed.seq})  # Log sequence only.
