"""Define one immutable buffered WebSocket message."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Message parts use compact ASCII JSON.
from dataclasses import dataclass  # The message is an immutable value record.


@dataclass(frozen=True, slots=True)
class StreamMessage:
    """Hold one buffered message and its public metadata."""

    seq: int  # The page uses this sequence as its read cursor.
    received_at: str  # The page shows the UTC receive time.
    kind: str  # The page selects a renderer from this kind.
    content_json: str  # The buffer stores content once as compact JSON text.
    size: int  # The page shows the original compact JSON byte count.
    shortened: bool  # The page marks content that exceeded the message limit.
    source: str | None = None  # Repeated streams use one safe source identifier.
    summary: str | None = None  # Packet views show one summary line.

    def json_parts(self) -> tuple[str, str, str]:
        """Return three parts that form the public compact JSON object."""
        fields = self._metadata()  # Encode only the small message metadata.
        encoded = json.dumps(fields, ensure_ascii=True, sort_keys=True, separators=(",", ":"))  # Use stable ASCII JSON.
        return '{"content":', self.content_json, "," + encoded[1:]  # Reuse the stored content without decoding it.

    def _metadata(self) -> dict[str, object]:
        """Return the message fields other than content."""
        return {
            "seq": self.seq,  # The client uses this value as the next cursor.
            "received_at": self.received_at,  # The page shows the receive time.
            "kind": self.kind,  # The page selects the matching renderer.
            "summary": self.summary,  # Packet messages can show this line.
            "source": self.source,  # The source contains an identifier, not a path.
            "size": self.size,  # The page shows the original content size.
            "shortened": self.shortened,  # The page marks shortened content.
        }


@dataclass(frozen=True, slots=True)
class MessageDraft:
    """Hold one message before sequence assignment and content encoding."""

    received_at: str  # The session supplies the UTC receive time.
    kind: str  # The runner supplies the public message kind.
    content: object  # The encoder converts this value to compact JSON.
    source: str | None = None  # Repeated streams can supply one safe identifier.
    summary: str | None = None  # Packet messages can supply one summary line.
