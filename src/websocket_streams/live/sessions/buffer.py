"""Keep bounded WebSocket messages for one session.

Why:
    Issue #3551. A browser can leave a stream open for minutes. The portal
    must keep only a bounded message list, count each dropped message, and
    shorten a message that is too large for a safe page response.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Message size uses the JSON form that the page receives.
import logging  # The buffer reports each drop and shortening event.
from collections import deque  # A ring buffer drops the oldest message first.
from collections.abc import Iterable  # The read method returns immutable copies.
from dataclasses import dataclass  # Each message is one value record.

logger = logging.getLogger(__name__)  # Keep buffer log records under this module.


@dataclass(frozen=True, slots=True)
class StreamMessage:
    """One buffered message of a stream session.

    Attributes:
        seq: The sequence number inside the session.
        received_at: The UTC receive time with a trailing ``Z``.
        kind: The view kind, such as ``json`` or ``text``.
        content: The page-safe message content.
        size: The original JSON size in bytes.
        shortened: True when the content was shortened.
        source: The repeatable identifier value of the message source.
        summary: The packet summary line, or None.
    """

    seq: int  # The page uses this value as the next read cursor.
    received_at: str  # The page shows when the server received the message.
    kind: str  # The page chooses a renderer from this value.
    content: object  # The payload contains JSON-safe data only.
    size: int  # The byte cap uses the original serialized size.
    shortened: bool  # The page marks a large message with this flag.
    source: str | None = None  # The page labels repeated streams with this value.
    summary: str | None = None  # Packet views show this line.

    def to_payload(self) -> dict[str, object]:
        """Return the public JSON form of one message.

        Returns:
            The message payload that the API sends.
        """
        return {
            "seq": self.seq,  # The client sends this value as the next cursor.
            "received_at": self.received_at,  # The page shows this receive time.
            "kind": self.kind,  # The page picks the renderer from this value.
            "content": self.content,  # The content is already page-safe.
            "summary": self.summary,  # Only packet messages use this line.
            "source": self.source,  # The source is an identifier, not a path.
            "size": self.size,  # The page can show the original size.
            "shortened": self.shortened,  # The page marks shortened content.
        }


class MessageBuffer:
    """A count-limited and byte-limited message buffer."""

    MAX_MESSAGE_BYTES = 256 * 1024  # One very large message is shortened before storage.

    def __init__(self, max_messages: int, max_bytes: int) -> None:
        """Build one empty message buffer.

        Args:
            max_messages: The maximum count of messages to keep.
            max_bytes: The maximum count of message bytes to keep.
        """
        self._max_messages = max_messages  # The settings define this cap.
        self._max_bytes = max_bytes  # The settings define this cap.
        self._messages: deque[StreamMessage] = deque()  # The oldest message sits at the left.
        self._bytes = 0  # Track bytes without summing the whole buffer each time.
        self._next_seq = 1  # Sequence numbers start at one.
        self.dropped = 0  # The session counters expose this number.
        self.shortened = 0  # The session counters expose this number.

    @property
    def bytes_used(self) -> int:
        """Return the current buffered byte total."""
        return self._bytes  # The value updates on each add and drop.

    @property
    def last_seq(self) -> int:
        """Return the newest sequence number, or zero when empty."""
        return self._next_seq - 1  # The next sequence is always one above the newest.

    @property
    def first_seq(self) -> int:
        """Return the oldest sequence number, or zero when empty."""
        first = self._messages[0].seq if self._messages else 0  # Empty buffers have no cursor.
        return first  # The read payload includes this value.

    def add(
        self, received_at: str, kind: str, content: object, source: str | None, summary: str | None
    ) -> StreamMessage:
        """Add one message and enforce both caps.

        Args:
            received_at: The UTC receive time.
            kind: The message kind.
            content: The page-safe message content before shortening.
            source: The repeatable identifier value, or None.
            summary: The packet summary, or None.

        Returns:
            The stored message.
        """
        logger.info("Adding a WebSockets stream message")  # Log before changing the buffer.
        safe_content, size, shortened = self._shape_content(content)  # Apply the single-message cap.
        message = StreamMessage(
            self._next_seq, received_at, kind, safe_content, size, shortened, source, summary
        )  # Store one immutable record.
        self._messages.append(message)  # Add the newest message at the right side.
        self._next_seq += 1  # Reserve the next sequence number.
        self._bytes += size  # Track the original message size.
        self.shortened += int(shortened)  # Count shortened messages for the session card.
        self._trim()  # Drop old messages until the caps are safe.
        logger.debug("Stored WebSockets stream message seq=%s", message.seq)  # Log safe metadata only.
        return message  # The session can update its rate window.

    def read_after(self, after: int, limit: int) -> tuple[list[dict[str, object]], int, bool]:
        """Return messages with a sequence number above the cursor.

        Args:
            after: The last sequence number that the page has.
            limit: The maximum count to return.

        Returns:
            The message payloads, the first kept sequence, and the gap flag.
        """
        logger.info("Reading WebSockets stream messages after seq=%s", after)  # Log before reading the buffer.
        selected = [message.to_payload() for message in self._messages if message.seq > after][:limit]  # Keep order.
        gap = bool(
            self._messages and after < self.first_seq - 1 and self.dropped
        )  # A dropped unread message creates a gap.
        logger.debug("Read %s WebSockets stream messages", len(selected))  # Log the result count.
        return selected, self.first_seq, gap  # The manager builds the full read payload.

    def iter_payloads(self) -> Iterable[dict[str, object]]:
        """Return an iterable of all kept message payloads.

        Returns:
            Payload dictionaries in sequence order.
        """
        logger.info("Building WebSockets stream download messages")  # Log before reading all messages.
        payloads = [message.to_payload() for message in self._messages]  # Copy each payload for the caller.
        logger.debug("Built %s WebSockets stream download messages", len(payloads))  # Log the result count.
        return payloads  # The manager serializes each payload as JSON Lines.

    def _shape_content(self, content: object) -> tuple[object, int, bool]:
        """Return content that fits the single-message cap.

        Args:
            content: The original message content.

        Returns:
            The safe content, the original byte size, and the shortened flag.
        """
        encoded = json.dumps(content, ensure_ascii=True, sort_keys=True, default=str).encode(
            "utf-8"
        )  # Measure page bytes.
        if len(encoded) <= self.MAX_MESSAGE_BYTES:  # Small content can stay unchanged.
            return content, len(encoded), False  # No shortening happened.
        logger.warning("Shortening one large WebSockets stream message")  # The content can be sensitive, so omit it.
        preview = encoded[: self.MAX_MESSAGE_BYTES].decode("utf-8", errors="ignore")  # Keep a safe prefix only.
        return {"shortened": True, "preview": preview}, len(encoded), True  # Mark the content as shortened.

    def _trim(self) -> None:
        """Drop old messages until both caps are satisfied."""
        while self._messages and (
            len(self._messages) > self._max_messages or self._bytes > self._max_bytes
        ):  # Both caps apply.
            removed = self._messages.popleft()  # The oldest message leaves first.
            self._bytes = max(0, self._bytes - removed.size)  # Keep the byte counter non-negative.
            self.dropped += 1  # Count each dropped message for the session card.
            logger.debug("Dropped WebSockets stream message seq=%s", removed.seq)  # Log safe metadata only.
