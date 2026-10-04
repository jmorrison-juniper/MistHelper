"""Redact shell WebSocket addresses from SDK log records."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The SDK filter receives standard log records.
import re  # One bounded pattern identifies complete WebSocket addresses.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies the bounded JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply one safe structured logger.


class ShellAddressFilter(logging.Filter):
    """Remove Mist shell WebSocket addresses from log records."""

    ADDRESS_RE = re.compile(r"wss://\S+")  # The address can contain a session credential.

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact each complete WebSocket address and keep the record."""
        rendered = record.getMessage()  # Render arguments before replacing secret text.
        redacted = self.ADDRESS_RE.sub("wss://[redacted]", rendered)  # Replace each full address.
        if redacted != rendered:  # Mutate only a record that held a secret-bearing address.
            record.msg = redacted  # Store the already rendered safe message.
            record.args = ()  # Clear arguments because the message now contains their safe text.
            logger.emit(logging.DEBUG, "shell_address_redacted", {"count": 1})  # Log no address content.
        return True  # The logging system keeps the redacted record.
