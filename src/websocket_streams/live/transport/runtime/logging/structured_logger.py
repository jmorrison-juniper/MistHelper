"""Emit bounded ASCII JSON records for live transport actions."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Structured records use one JSON object for each log message.
import logging  # The adapter writes through the repository logging system.
from collections.abc import Mapping  # Callers provide small field mappings.

from src.websocket_streams.live.transport.runtime.logging.bounds import (
    MAX_EVENT_LENGTH,
)  # Bound every event name.
from src.websocket_streams.live.transport.runtime.logging.fields import (
    SafeFieldFilter,
)  # Permit only approved operational fields.
from src.websocket_streams.live.transport.runtime.logging.redaction import (
    SecretRedactor,
)  # Redact event names and approved text fields.


class StructuredTransportLogger:
    """Write bounded transport events without remote or operator content."""

    def __init__(self, target: logging.Logger) -> None:
        """Build the boundary collaborators for one standard logger."""
        self._target = target  # The repository controls handlers and log levels.
        self._redactor = SecretRedactor()  # One redactor protects event names.
        self._fields = SafeFieldFilter(self._redactor)  # One filter protects metadata.

    def emit(
        self,
        level: int,
        event: str,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        """Filter, serialize, and write one record."""
        safe_event = self._redactor.redact(event, MAX_EVENT_LENGTH)  # Redact and bound the event name.
        record: dict[str, object] = {"event": safe_event}  # Start with the required safe event field.
        record.update(self._fields.safe_fields(fields or {}))  # Add only approved operational metadata.
        message = json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True)  # Emit ASCII JSON.
        self._target.log(level, "%s", message)  # Defer handler formatting to standard logging.
