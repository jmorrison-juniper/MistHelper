"""Redact recognized secret forms from bounded transport text."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import re  # Boundary redaction removes recognized secret forms.
from typing import Final  # The compiled pattern set stays immutable.

from src.websocket_streams.live.transport.runtime.logging.bounds import (
    REDACTED_VALUE,
)  # Use one marker for every redacted value.

_SECRET_PATTERNS: Final = (
    re.compile(r"(?i)\b(?:api[_-]?token|token|authorization)\s*[:=]\s*\S+"),  # Redact named token values.
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
