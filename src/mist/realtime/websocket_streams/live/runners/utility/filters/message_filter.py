"""Coordinate early buffering and utility payload matching."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from src.mist.realtime.websocket_streams.live.runners.utility.filters.early_buffer import EarlyPayloadBuffer
from src.mist.realtime.websocket_streams.live.runners.utility.filters.payload_matcher import UtilityPayloadMatcher
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)

logger = StructuredTransportLogger(logging.getLogger(__name__))


class UtilityMessageFilter:
    """Keep only messages that belong to one utility trigger."""

    def __init__(self, channel: str) -> None:
        """Build one filter for a checked utility channel."""
        logger.emit(logging.INFO, "utility_filter_build", {"action": channel})
        self._matcher = UtilityPayloadMatcher(channel)
        self._buffer = EarlyPayloadBuffer()
        self._value: str | None = None
        self.capture_ended = False

    @property
    def dropped_count(self) -> int:
        """Return the count of early payloads that exceeded the bound."""
        return self._buffer.dropped_count

    def bind(self, answer: Mapping[str, object]) -> list[object]:
        """Bind the trigger answer and return held matching payloads."""
        logger.emit(logging.INFO, "utility_filter_bind")
        value = self._matcher.answer_value(answer)
        with self._buffer.lock:
            self._value = value
            held = self._buffer.drain()
        matches = []
        for payload in held:
            content = self._content(payload, value)
            if content is not None:
                matches.append(content)
        logger.emit(logging.DEBUG, "utility_filter_bound", {"count": len(matches)})
        return matches

    def offer(self, payload: object) -> list[object]:
        """Return one matching payload or hold an early payload."""
        with self._buffer.lock:
            if self._value is None:
                self._buffer.hold(payload)
                return []
            value = self._value
        content = self._content(payload, value)
        return [content] if content is not None else []

    def _content(self, payload: object, value: str) -> object | None:
        """Return matching output and record a matching capture end."""
        if self._matcher.is_capture_end(payload, value):
            self.capture_ended = True
            return None
        return self._matcher.content(payload, value)
