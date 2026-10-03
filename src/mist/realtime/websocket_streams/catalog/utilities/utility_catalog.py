"""Provide immutable utility discovery and lookup."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The shared logger writes through standard logging.

from src.mist.realtime.websocket_streams.catalog.model import UtilityDefinition  # Type the immutable catalog entries.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_discovery import (
    UtilityDiscovery,
)  # Discover SDK utilities.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Apply the shared safe JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep catalog records in one bounded JSON format.


class UtilityCatalog:
    """Hold every supported Mist device utility definition."""

    def __init__(self) -> None:
        """Build one immutable utility lookup table."""
        logger.emit(logging.INFO, "catalog.utility.build.start")  # Record the bounded build action.
        self._entries = UtilityDiscovery().entries()  # Discover each supported SDK utility once.
        self._by_key = {entry.key: entry for entry in self._entries}  # Give constant-time lookup by checked key.
        fields = {"count": len(self._entries), "status": "ready"}  # Report only bounded operational fields.
        logger.emit(logging.DEBUG, "catalog.utility.build.finish", fields)  # Record the completed build.

    def entries(self) -> tuple[UtilityDefinition, ...]:
        """Return all utility definitions in SDK order."""
        logger.emit(logging.INFO, "catalog.utility.read.start")  # Record the immutable catalog read.
        logger.emit(logging.DEBUG, "catalog.utility.read.finish", {"count": len(self._entries)})  # Log the count.
        return self._entries  # Prevent caller mutation with the stored tuple.

    def get(self, key: str) -> UtilityDefinition | None:
        """Return one utility definition for a checked key."""
        logger.emit(logging.INFO, "catalog.utility.find.start")  # Do not log the operator-controlled key.
        entry = self._by_key.get(key)  # Read the immutable lookup table.
        logger.emit(logging.DEBUG, "catalog.utility.find.finish", {"status": entry is not None})  # Log the result.
        return entry  # Let the request checker handle an unknown key.
