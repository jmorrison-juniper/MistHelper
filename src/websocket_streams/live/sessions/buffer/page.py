"""Build one bounded message page response."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Page metadata uses compact ASCII JSON.
from dataclasses import dataclass  # The page is an immutable response record.

from src.websocket_streams.live.sessions.buffer.message import StreamMessage  # Pages contain buffered messages.


@dataclass(frozen=True, slots=True)
class MessagePage:
    """Hold one message read answer."""

    session: dict[str, object]  # The page refreshes the session card from this payload.
    messages: list[StreamMessage]  # The route formats immutable message records after the lock.
    next_after: int  # The browser sends this cursor with the next read.
    first_seq: int  # The browser reports a gap from this oldest kept sequence.
    gap: bool  # This flag tells the operator that unread messages were dropped.

    def to_json_text(self) -> str:
        """Return compact ASCII JSON without decoding stored message content."""
        head = json.dumps(
            self._metadata(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )  # Encode small fields.
        parts = [head[:-1], ',"messages":[']  # Open the message array as the last field.
        self._append_messages(parts)  # Add each stored message without a content copy.
        parts.append("]}")  # Close the message array and the response object.
        return "".join(parts)  # Join all text one time for the HTTP response.

    def _metadata(self) -> dict[str, object]:
        """Return the response fields other than messages."""
        return {
            "session": self.session,  # The response includes the current session payload.
            "next_after": self.next_after,  # The browser stores this next cursor.
            "first_seq": self.first_seq,  # The browser can describe the oldest kept message.
            "gap": self.gap,  # The browser warns when it missed buffered messages.
        }

    def _append_messages(self, parts: list[str]) -> None:
        """Append compact message text to the response part list."""
        for index, message in enumerate(self.messages):  # Preserve sequence order.
            parts.append("," if index else "")  # Separate messages after the first record.
            parts.extend(message.json_parts())  # Reuse the stored content JSON text.
