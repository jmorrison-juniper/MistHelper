"""Route channel events to session messages without exposing channel paths."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Event routing uses structured JSON records.

from src.mist.realtime.websocket_streams.catalog.model import ChannelDefinition  # Channel requests build channel paths.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Broken request contracts fail safely.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # Routing accepts checked requests only.
from src.mist.realtime.websocket_streams.live.runners.channel.contracts import (
    ChannelRunnerState,
)  # Routing records health evidence.
from src.mist.realtime.websocket_streams.live.runners.text.messages import (
    MessageShaper,
)  # Channel payloads need nested JSON decoding.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionSink,
)  # Routing writes through the session protocol.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies the bounded JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply one safe structured logger.


class ChannelSourceMap:
    """Build private channel paths and their public source values."""

    def __init__(self, request: StartRequest) -> None:
        """Store one checked channel request."""
        self._request = request  # Path and source values come from this checked request.

    def build(self) -> dict[str, str | None]:
        """Return the private path-to-source map."""
        logger.emit(logging.INFO, "channel_source_map_started")  # Log before path construction.
        paths = self._definition().build_paths(self._request.targets)  # Build checked private paths.
        values = self._values()  # Read public source values in matching order.
        mapped = {path: values[index] if index < len(values) else None for index, path in enumerate(paths)}
        return self._completed(mapped)  # Log the count and return the private map.

    def _definition(self) -> ChannelDefinition:
        """Return the checked channel definition."""
        definition = self._request.definition  # Narrow the checked definition once.
        if not isinstance(definition, ChannelDefinition):  # A channel request must hold a channel definition.
            raise StreamRequestError("bad_request", "The channel definition is not valid.")  # Preserve failure text.
        return definition  # The caller can use channel-only path behavior.

    def _values(self) -> tuple[str, ...]:
        """Return repeatable source values in path order."""
        repeatable = self._definition().repeatable  # Only channel definitions own this field.
        return self._request.targets.get(str(repeatable), ()) if repeatable else ()  # Preserve target ordering.

    @staticmethod
    def _completed(mapped: dict[str, str | None]) -> dict[str, str | None]:
        """Log the map size and return the private mapping."""
        logger.emit(logging.DEBUG, "channel_source_map_completed", {"count": len(mapped)})  # Log only the count.
        return mapped  # The private path keys never enter a log record.


class ChannelEventRouter:
    """Shape channel events and map private paths to public sources."""

    def __init__(self, request: StartRequest, sink: SessionSink, state: ChannelRunnerState) -> None:
        """Build one event router from a checked channel request."""
        self._sink = sink  # The router sends each shaped event to this session.
        self._state = state  # Delivered events update the current health evidence.
        self._shaper = MessageShaper()  # One shaper preserves the existing page message form.
        self._source_by_path = ChannelSourceMap(request).build()  # Paths stay inside the server process.
        self.paths = tuple(self._source_by_path)  # The client subscribes to each private path.

    def mark_live(self) -> None:
        """Mark the session live after every successful subscription."""
        logger.emit(logging.INFO, "channel_mark_live_started")  # Log before the session state change.
        self._sink.mark_live("The WebSocket connection opened.")  # Preserve the existing live note.
        logger.emit(logging.DEBUG, "channel_mark_live_completed", {"status": "live"})  # Log the safe result.

    def deliver(self, message: dict[str, object]) -> None:
        """Shape and deliver one decoded channel event."""
        kind, content, path = self._shape(message)  # Preserve nested JSON decoding.
        source = self._source_by_path.get(path or "")  # Replace the private path with its public identifier.
        self._state.attempt.received_event = True  # One delivered event earns a fresh retry budget.
        self._sink.add_message(kind, content, source=source)  # Preserve event routing and message form.
        logger.emit(logging.DEBUG, "channel_event_delivery_completed", {"count": 1})  # Log the bounded result.

    def _shape(self, message: dict[str, object]) -> tuple[str, object, str | None]:
        """Shape one event and log bounded result metadata."""
        logger.emit(logging.INFO, "channel_event_shape_started")  # Log before the data transformation.
        result = self._shaper.channel_message(message)  # Preserve the existing message shaping behavior.
        logger.emit(logging.DEBUG, "channel_event_shape_completed", {"status": result[0]})  # Log the kind only.
        return result  # The caller routes the private path without logging it.
