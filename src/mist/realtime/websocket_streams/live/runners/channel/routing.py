"""Route channel events to session messages without exposing channel paths."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Event routing uses structured JSON records.
from collections.abc import Callable  # Output failure stops the shared channel connection.

from src.mist.realtime.websocket_streams.catalog.model import ChannelDefinition  # Channel requests build channel paths.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Broken request contracts fail safely.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    BatchExecutionPlan,
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
        plan = self._request.batch_plan  # A batch expands checked targets from its frozen preview.
        if plan is not None:
            return self._batch_paths(plan)
        paths = self._definition().build_paths(self._request.targets)  # Build checked private paths.
        repeatable = self._definition().repeatable  # Only channel definitions own repeatable values.
        values = self._request.targets.get(str(repeatable), ()) if repeatable else ()
        mapped = {path: values[index] if index < len(values) else None for index, path in enumerate(paths)}
        logger.emit(logging.DEBUG, "channel_source_map_completed", {"count": len(mapped)})  # Log only the count.
        return mapped  # The private path keys never enter a log record.

    def _batch_paths(self, plan: BatchExecutionPlan) -> dict[str, str | None]:
        """Build one path per checked batch target and map it to its natural key."""
        paths: dict[str, str | None] = {}
        for target in plan.targets:
            for path in self._definition().build_paths(target.request.targets):
                previous = paths.get(path)
                if previous is not None and previous != target.target_key:
                    raise StreamRequestError("bad_request", "Two batch targets resolved to one channel path.")
                paths[path] = target.target_key
        logger.emit(logging.DEBUG, "channel_source_map_completed", {"count": len(paths)})  # Log only the count.
        return paths  # The private path keys never enter a log record.

    def _definition(self) -> ChannelDefinition:
        """Return the checked channel definition."""
        definition = self._request.definition  # Narrow the checked definition once.
        if not isinstance(definition, ChannelDefinition):  # A channel request must hold a channel definition.
            raise StreamRequestError("bad_request", "The channel definition is not valid.")  # Preserve failure text.
        return definition  # The caller can use channel-only path behavior.


class ChannelEventRouter:
    """Shape channel events and map private paths to public sources."""

    def __init__(
        self,
        request: StartRequest,
        sink: SessionSink,
        state: ChannelRunnerState,
        on_output_failure: Callable[[], None] | None = None,
    ) -> None:
        """Build one event router from a checked channel request."""
        self._sink = sink  # The router sends each shaped event to this session.
        self._state = state  # Delivered events update the current health evidence.
        self._shaper = MessageShaper()  # One shaper preserves the existing page message form.
        self._source_by_path = ChannelSourceMap(request).build()  # Paths stay inside the server process.
        plan = request.batch_plan
        self._batch_plan = plan
        self._on_output_failure = on_output_failure  # Keep a safe callback for required output failures.
        self._batch_identity = (
            {target.target_key: dict(target.identity) for target in plan.targets} if plan is not None else {}
        )
        self.paths = tuple(self._source_by_path)  # The client subscribes to each private path.

    def mark_live(self) -> None:
        """Mark the session live after every successful subscription."""
        logger.emit(logging.INFO, "channel_mark_live_started")  # Log before the session state change.
        self._sink.mark_live("The WebSocket connection opened.")  # Preserve the existing live note.
        if self._batch_plan is not None:
            for target in self._batch_plan.targets:
                self._batch_plan.progress.transitions.transition(target.target_key, "running")
        logger.emit(logging.DEBUG, "channel_mark_live_completed", {"status": "live"})  # Log the safe result.

    def deliver(self, message: dict[str, object]) -> None:
        """Shape and deliver one decoded channel event."""
        logger.emit(logging.INFO, "channel_event_shape_started")  # Log before the data transformation.
        kind, content, path = self._shaper.channel_message(message)  # Preserve nested JSON decoding.
        logger.emit(logging.DEBUG, "channel_event_shape_completed", {"status": kind})  # Log the kind only.
        source = self._source_by_path.get(path or "")  # Replace the private path with its public identifier.
        if self._batch_plan is not None:
            attributed = self._deliver_batch(kind, content, source)
            if attributed is None:
                return  # Preserve target attribution in every batch result.
            content = attributed
        self._state.attempt.received_event = True  # One delivered event earns a fresh retry budget.
        self._sink.add_message(kind, content, source=source)  # Preserve event routing and message form.
        logger.emit(logging.DEBUG, "channel_event_delivery_completed", {"count": 1})  # Log the bounded result.

    def _deliver_batch(self, kind: str, content: object, source: str | None) -> dict[str, object] | None:
        """Save one batch event and retain its frozen target identity."""
        identity = self._batch_identity.get(source or "")
        if identity is None:  # Do not publish an event without a target identity.
            logger.emit(logging.WARNING, "channel_batch_event_unmapped", {"status": "discarded"})  # Log no path.
            return None
        plan = self._batch_plan
        if plan is None or source is None:  # Ignore an impossible incomplete target mapping.
            return None  # No result can be attributed safely.
        if not plan.progress.artifacts.write_result(source, identity, kind, content, None):
            plan.progress.transitions.transition(source, "failed", "output_failed")
            self._sink.add_message(
                "error",
                {"target": identity, "reason_code": "output_failed"},
                source=source,
            )  # Preserve the storage failure under the affected target.
            if self._on_output_failure is not None:  # Stop the shared connection after a storage error.
                self._on_output_failure()
            return None  # Stop delivering after the required output failure.
        plan.progress.transitions.record_result(source)  # Count only events accepted for this target.
        return {"target": identity, "data": content}  # Bind output to the frozen natural-key identity.
