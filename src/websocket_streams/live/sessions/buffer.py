"""Keep bounded WebSocket messages for one session.

Why:
    Issue #3551. A browser can leave a stream open for minutes. The portal
    must keep only a bounded message list, count each dropped message, and
    shorten a message that is too large for a safe page response.

    The buffer keeps each message as compact JSON text. The T075 load check
    measured decoded objects at about 3.5 times their JSON size. A full
    8 MiB buffer then held about 28 MiB. The byte cap now counts the memory
    that each kept message uses, so the cap is a true memory limit.

    A read joins the stored JSON text into the page response in one step.
    A read does not decode the content, so a full first read stays fast.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # The buffer keeps each message as compact JSON text.
import logging  # The buffer reports each drop and shortening event.
from collections import deque  # A ring buffer drops the oldest message first.
from dataclasses import dataclass  # Each message is one value record.
from itertools import islice  # A read copies only the records that it returns.

logger = logging.getLogger(__name__)  # Keep buffer log records under this module.

COMPACT_SEPARATORS = (",", ":")  # Compact JSON has no padding spaces, like the page response.


@dataclass(frozen=True, slots=True)
class StreamMessage:
    """One buffered message of a stream session.

    Attributes:
        seq: The sequence number inside the session.
        received_at: The UTC receive time with a trailing ``Z``.
        kind: The view kind, such as ``json`` or ``text``.
        content_json: The page-safe message content as compact ASCII JSON text.
        size: The compact JSON size in bytes before shortening.
        shortened: True when the content was shortened.
        source: The repeatable identifier value of the message source.
        summary: The packet summary line, or None.
    """

    seq: int  # The page uses this value as the next read cursor.
    received_at: str  # The page shows when the server received the message.
    kind: str  # The page chooses a renderer from this value.
    content_json: str  # Text uses about 3.5 times less memory than decoded objects.
    size: int  # The page can show the size before shortening.
    shortened: bool  # The page marks a large message with this flag.
    source: str | None = None  # The page labels repeated streams with this value.
    summary: str | None = None  # Packet views show this line.

    def json_parts(self) -> tuple[str, str, str]:
        """Return the public JSON form of one message as three text parts.

        The caller joins the parts with other text in one step, so the large
        content text is copied one time only, and it is never decoded. The
        ``content`` key sorts first, so the joined text is equal to a full
        sorted encode of the message payload.

        Returns:
            The opening text, the stored content text, and the closing text.
        """
        fields = {
            "seq": self.seq,  # The client sends this value as the next cursor.
            "received_at": self.received_at,  # The page shows this receive time.
            "kind": self.kind,  # The page picks the renderer from this value.
            "summary": self.summary,  # Only packet messages use this line.
            "source": self.source,  # The source is an identifier, not a path.
            "size": self.size,  # The page can show the original size.
            "shortened": self.shortened,  # The page marks shortened content.
        }
        other_text = json.dumps(
            fields, ensure_ascii=True, sort_keys=True, separators=COMPACT_SEPARATORS
        )  # Encode the small fields only. The text always starts with "{".
        return '{"content":', self.content_json, "," + other_text[1:]  # Put the stored text first, with no decode.


@dataclass(frozen=True, slots=True)
class MessagePage:
    """One message read answer that the route sends as joined JSON text.

    Attributes:
        session: The public session payload.
        messages: The returned message records in sequence order.
        next_after: The cursor for the next read.
        first_seq: The oldest kept sequence number.
        gap: True when the buffer dropped a message that the page did not read.
    """

    session: dict[str, object]  # The page updates the session card from this payload.
    messages: list[StreamMessage]  # The records are immutable, so the route can format them after the lock.
    next_after: int  # The page sends this value as the next cursor.
    first_seq: int  # The page shows a gap note from this value.
    gap: bool  # The page warns the operator about missed messages.

    def to_json_text(self) -> str:
        """Return the JSON text of the read answer.

        Returns:
            The compact JSON text that the route sends with no decode step.
        """
        fields = {
            "session": self.session,  # The session card payload.
            "next_after": self.next_after,  # The next read cursor.
            "first_seq": self.first_seq,  # The oldest kept sequence number.
            "gap": self.gap,  # The missed-message flag.
        }
        head = json.dumps(
            fields, ensure_ascii=True, sort_keys=True, separators=COMPACT_SEPARATORS
        )  # Encode the small fields only. The text always ends with "}".
        parts = [head[:-1], ',"messages":[']  # Open the message array as the last field.
        for index, message in enumerate(self.messages):  # Add each message in sequence order.
            parts.append("," if index else "")  # Separate the messages with a comma.
            parts.extend(message.json_parts())  # Add the parts. The join copies each part one time.
        parts.append("]}")  # Close the array and the answer.
        return "".join(parts)  # One join copies the large content text one time only.


class MessageBuffer:
    """A count-limited and memory-limited message buffer."""

    MAX_MESSAGE_BYTES = 256 * 1024  # One very large message is shortened before storage.
    MESSAGE_OVERHEAD_BYTES = 320  # The T075 measure of one record without its text, with a margin.

    def __init__(self, max_messages: int, max_bytes: int) -> None:
        """Build one empty message buffer.

        Args:
            max_messages: The maximum count of messages to keep.
            max_bytes: The maximum memory of the kept messages, in bytes.
        """
        self._max_messages = max_messages  # The settings define this cap.
        self._max_bytes = max_bytes  # The settings define this cap.
        self._messages: deque[StreamMessage] = deque()  # The oldest message sits at the left.
        self._bytes = 0  # Track the memory total without summing the whole buffer each time.
        self._next_seq = 1  # Sequence numbers start at one.
        self.dropped = 0  # The session counters expose this number.
        self.shortened = 0  # The session counters expose this number.

    @property
    def bytes_used(self) -> int:
        """Return the memory that the kept messages use, in bytes."""
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
        logger.debug("Adding a WebSockets stream message")  # Debug level: a stream can add many messages each second.
        content_json, size, shortened = self._shape_content(content)  # Encode once and apply the single-message cap.
        message = StreamMessage(
            self._next_seq, received_at, kind, content_json, size, shortened, source, summary
        )  # Store one immutable record.
        self._messages.append(message)  # Add the newest message at the right side.
        self._next_seq += 1  # Reserve the next sequence number.
        self._bytes += self.footprint(message)  # Count the memory that the new message holds.
        self.shortened += int(shortened)  # Count shortened messages for the session card.
        self._trim()  # Drop old messages until the caps are safe.
        logger.debug("Stored WebSockets stream message seq=%s", message.seq)  # Log safe metadata only.
        return message  # The session can update its rate window.

    def read_after(self, after: int, limit: int) -> tuple[list[StreamMessage], int, bool]:
        """Return the kept records with a sequence number above the cursor.

        The caller holds the session lock, so this method copies record
        references only. The manager formats the records after the session
        releases the lock, so a runner callback does not wait for the format.

        Args:
            after: The last sequence number that the page has.
            limit: The maximum count to return.

        Returns:
            The records in sequence order, the first kept sequence, and the gap flag.
        """
        logger.debug("Reading WebSockets stream messages after seq=%s", after)  # The page polls each second.
        newer = (message for message in self._messages if message.seq > after)  # The deque keeps sequence order.
        selected = list(islice(newer, limit))  # Stop at the limit instead of a scan of the full buffer.
        gap = bool(
            self._messages and after < self.first_seq - 1 and self.dropped
        )  # A dropped unread message creates a gap.
        logger.debug("Read %s WebSockets stream messages", len(selected))  # Log the result count.
        return selected, self.first_seq, gap  # The manager formats the records outside the session lock.

    def snapshot(self) -> list[StreamMessage]:
        """Return a copy of the kept record list for a download.

        Returns:
            The records in sequence order. The records share their text, so the copy is small.
        """
        logger.info("Copying WebSockets stream messages for a download")  # Log before the copy.
        records = list(self._messages)  # A copy lets the download continue while new messages arrive.
        logger.debug("Copied %s WebSockets stream messages for a download", len(records))  # Log the result count.
        return records  # The manager formats one record at a time while the file streams.

    @classmethod
    def footprint(cls, message: StreamMessage) -> int:
        """Return the memory that one kept message uses, in bytes.

        Args:
            message: The kept message.

        Returns:
            The text length plus the fixed cost of one record.
        """
        text_bytes = (
            len(message.content_json) + len(message.summary or "") + len(message.source or "")
        )  # ASCII text uses one byte for each character. Count a shared source again to stay safe.
        return (
            text_bytes + cls.MESSAGE_OVERHEAD_BYTES
        )  # Add the record, the time text, the numbers, and the queue slot.

    def _shape_content(self, content: object) -> tuple[str, int, bool]:
        """Return compact JSON text that fits the single-message cap.

        Args:
            content: The original message content.

        Returns:
            The safe JSON text, the original byte size, and the shortened flag.
        """
        encoded = json.dumps(
            content, ensure_ascii=True, sort_keys=True, default=str, separators=COMPACT_SEPARATORS
        )  # ASCII text has one byte for each character, so the length is the byte size.
        if len(encoded) <= self.MAX_MESSAGE_BYTES:  # Small content can stay unchanged.
            return encoded, len(encoded), False  # No shortening happened.
        logger.warning("Shortening one large WebSockets stream message")  # The content can be sensitive, so omit it.
        preview = {"shortened": True, "preview": encoded[: self.MAX_MESSAGE_BYTES]}  # Keep a safe prefix only.
        shortened_json = json.dumps(
            preview, ensure_ascii=True, sort_keys=True, separators=COMPACT_SEPARATORS
        )  # Store the shortened form as text too.
        return shortened_json, len(encoded), True  # Mark the content as shortened.

    def _trim(self) -> None:
        """Drop old messages until both caps are satisfied."""
        while self._messages and (
            len(self._messages) > self._max_messages or self._bytes > self._max_bytes
        ):  # Both caps apply.
            removed = self._messages.popleft()  # The oldest message leaves first.
            self._bytes = max(0, self._bytes - self.footprint(removed))  # Release the memory of the removed message.
            self.dropped += 1  # Count each dropped message for the session card.
            logger.debug("Dropped WebSockets stream message seq=%s", removed.seq)  # Log safe metadata only.
