"""Redact recognized secret forms from bounded transport text."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import re  # Boundary redaction removes recognized secret forms.
from typing import Final  # The compiled pattern set stays immutable.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.bounds import (
    REDACTED_VALUE,
)  # Use one marker for every redacted value.

_SECRET_PATTERNS: Final = (
    re.compile(
        r"(?i)\b(?:api[_-]?token|token|authorization)\s*[:=]\s*(?:bearer\s+)?\S+"
    ),  # Redact complete bearer fields.
    re.compile(r"(?i)\bbearer\s+\S+"),  # Redact bearer credentials without a field label.
    re.compile(r"(?i)\b(?:cookie|set-cookie)\s*[:=]\s*[^\s,;]+"),  # Redact cookie header values.
    re.compile(r"(?i)\b(?:session|sid)=[^\s,;]+"),  # Redact common session cookie forms.
    re.compile(r"(?i)\bwss?://[^\s\"']+"),  # Redact shell WebSocket addresses and paths.
    re.compile(r"(?i)(?:[A-Z]:\\|/)(?:[^ \t\r\n]+[/\\])+[^ \t\r\n]*"),  # Redact filesystem and URL paths.
)  # Every permitted text value passes through all boundary patterns.


class SecretRedactor:
    """Remove secret forms before text enters a log record."""

    def redact(self, value: str, limit: int) -> str:
        """Return redacted text within the requested bound."""
        if "PRIVATE KEY" in value.upper():  # A private key can span lines and bypass token patterns.
            return REDACTED_VALUE  # Replace the complete value at the logging boundary.
        cleaned = value  # Apply each pattern to the same safe working value.
        for pattern in _SECRET_PATTERNS:  # Check all recognized forms before serialization.
            cleaned = pattern.sub(REDACTED_VALUE, cleaned)  # Replace secrets without preserving fragments.
        return cleaned[:limit]  # Bound the redacted value before it enters the record.


class LineSecretRedactor:
    """Redact complete text lines without exposing split credentials."""

    DEFAULT_LINE_LIMIT = 1024 * 1024  # Keep an unfinished line within the result-record bound.

    def __init__(self, max_line_bytes: int = DEFAULT_LINE_LIMIT) -> None:
        """Create one bounded line buffer for a target output stream."""
        if max_line_bytes < 1:  # A zero limit cannot retain even a safe line.
            raise ValueError("The line limit must be positive.")  # Reject invalid internal configuration.
        self._max_line_bytes = max_line_bytes  # Bound each untrusted terminal line.
        self._redactor = SecretRedactor()  # Reuse the same patterns as persisted records.
        self._pending = ""  # Keep incomplete lines until their secrets can be checked.
        self._discarding = False  # Drop the rest of an overlong line after a safe marker.

    def feed(self, chunk: str, final: bool = False) -> str:
        """Return safe complete lines and retain an incomplete bounded line."""
        output: list[str] = []  # Emit only text that has passed full-line redaction.
        lines = chunk.split("\n")  # Newline ends the token forms recognized by the boundary patterns.
        for index, line in enumerate(lines):  # Check every complete line in this transport chunk.
            complete = index < len(lines) - 1  # The split omits the newline from each piece.
            if self._discarding:  # An overlong line cannot re-enter the output stream.
                self._discarding = not complete  # Resume only after its newline arrives.
                continue  # Drop every remaining byte from that unsafe line.
            self._pending += line + ("\n" if complete else "")  # Reassemble one original text line.
            if complete:  # Redact only after the full line boundary arrives.
                output.append(self._redactor.redact(self._pending, self._max_line_bytes))  # Hide split secrets.
                self._pending = ""  # Keep memory bounded between complete lines.
            elif len(self._pending.encode("utf-8")) > self._max_line_bytes:  # Reject an unbounded line.
                output.append(REDACTED_VALUE + "\n")  # Preserve a safe record for the omitted line.
                self._pending = ""  # Remove the complete unsafe prefix from memory.
                self._discarding = True  # Drop the rest of this line through its newline.
        if final:  # Flush one final line only after its complete secret scan.
            if self._pending:  # An output stream can end without a final newline.
                output.append(self._redactor.redact(self._pending, self._max_line_bytes))  # Redact the final line.
            self._pending = ""  # Release any text retained for the completed target.
            self._discarding = False  # Reset state after the target ends.
        return "".join(output)  # Return only redacted text to the parent buffer.
