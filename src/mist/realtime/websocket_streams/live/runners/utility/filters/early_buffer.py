"""Hold bounded utility output until the trigger answer arrives."""

from __future__ import annotations

import logging
import threading

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)

logger = StructuredTransportLogger(logging.getLogger(__name__))


class EarlyPayloadBuffer:
    """Store a bounded sequence of early utility payloads."""

    _LIMIT = 2000

    def __init__(self) -> None:
        """Build an empty thread-safe buffer."""
        self._payloads: list[object] = []
        self._dropped = 0
        self.lock = threading.Lock()

    @property
    def dropped_count(self) -> int:
        """Return the protected drop count."""
        with self.lock:
            return self._dropped

    def hold(self, payload: object) -> None:
        """Hold one payload or count one bounded drop."""
        if len(self._payloads) >= self._LIMIT:
            self._dropped += 1
            logger.emit(logging.DEBUG, "utility_early_drop", {"dropped": self._dropped})
            return
        self._payloads.append(payload)

    def drain(self) -> list[object]:
        """Return held payloads and release their memory."""
        payloads = self._payloads
        self._payloads = []
        logger.emit(logging.DEBUG, "utility_early_drain", {"count": len(payloads)})
        return payloads
