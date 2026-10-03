"""Filter and bound structured transport log fields."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from collections.abc import Mapping  # Callers provide small field mappings.
from typing import Final  # Field sets stay immutable.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.bounds import (
    MAX_FIELD_LENGTH,
    MAX_FIELDS,
)  # Apply shared record bounds.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.redaction import (
    SecretRedactor,
)  # Redact every permitted text value.

SAFE_FIELDS: Final = frozenset(
    {"action", "byte_count", "code", "count", "detail", "dropped", "status", "timeout_seconds"}
)  # Only operational metadata can cross the logging boundary.
SENSITIVE_FIELDS: Final = frozenset(
    {"cookie", "cookies", "pasted_text", "private_key", "shell_path", "shell_url", "terminal_output", "token"}
)  # Known secret-bearing fields are reported without values.


class SafeFieldFilter:
    """Return only bounded operational fields."""

    def __init__(self, redactor: SecretRedactor) -> None:
        """Store the text redactor used for approved string fields."""
        self._redactor = redactor  # One boundary policy handles all text.

    def safe_fields(self, fields: Mapping[str, object]) -> dict[str, object]:
        """Return allowlisted fields and redaction evidence."""
        safe: dict[str, object] = {}  # Build a new record so caller mappings stay unchanged.
        redacted: list[str] = []  # Report sensitive field names without values.
        for key, value in list(fields.items())[:MAX_FIELDS]:  # Bound work before inspecting caller fields.
            if key in SENSITIVE_FIELDS:  # Sensitive values must never cross the boundary.
                redacted.append(key[:MAX_FIELD_LENGTH])  # Keep bounded evidence of redaction.
            elif key in SAFE_FIELDS:  # Unknown fields do not enter the record.
                safe[key] = self.safe_value(value)  # Bound and redact each approved value.
        if redacted:  # Add evidence only when sensitive fields were supplied.
            safe["redacted"] = redacted  # The list contains field names, not secret values.
        return safe  # Return the complete safe field set.

    def safe_value(self, value: object) -> object:
        """Return one bounded scalar value."""
        if isinstance(value, bool):  # Preserve booleans before the integer check.
            return value  # Boolean status is safe and already bounded.
        if isinstance(value, int):  # Counts and codes need a fixed numeric range.
            return max(-1_000_000_000, min(value, 1_000_000_000))  # Clamp hostile numeric input.
        if isinstance(value, float):  # Timeout values need a fixed numeric range.
            return max(-86_400.0, min(value, 86_400.0))  # Clamp floats to one day in either direction.
        return self._redactor.redact(str(value), MAX_FIELD_LENGTH)  # Redact and bound other values.
