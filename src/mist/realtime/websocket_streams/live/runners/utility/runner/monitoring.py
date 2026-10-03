"""Monitor utility output and choose final session outcomes."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.mist.realtime.websocket_streams.catalog.model import UtilityDefinition
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError
from src.mist.realtime.websocket_streams.live.runners.text.packets import PacketSummary
from src.mist.realtime.websocket_streams.live.runners.utility.filters.message_filter import UtilityMessageFilter
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.models import UtilityTiming
from src.mist.realtime.websocket_streams.live.sessions.record.state import SessionState
from src.mist.realtime.websocket_streams.live.transport.endpoint import ConnectFailure
from src.mist.realtime.websocket_streams.live.transport.runtime.frame_decoder import FrameDecoder, SubscribeError
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from src.mist.realtime.websocket_streams.live.transport.runtime.reader.contracts import ConnectionClosed
from src.mist.realtime.websocket_streams.live.transport.stream_client import StreamClient

if TYPE_CHECKING:
    from src.mist.realtime.websocket_streams.live.runners.utility.runner.utility_runner import RunContext

logger = StructuredTransportLogger(logging.getLogger(__name__))


@dataclass(slots=True)
class UtilityOutput:
    """Write filtered utility output to the session sink."""

    context: RunContext

    def bind_filter(self, filterer: UtilityMessageFilter, answer: Mapping[str, object]) -> None:
        """Bind one filter and emit held matching output."""
        held = filterer.bind(answer)
        for payload in held:
            self.emit(payload)
        logger.emit(logging.DEBUG, "utility_filter_output", {"count": len(held)})

    def emit(self, payload: object) -> None:
        """Emit one command line or packet record."""
        self.context.state.output_count += 1
        definition = self._definition()
        self.mark_live()
        if definition.output == "packets":
            packet = self._packet(payload)
            summary = PacketSummary.summarize(packet)
            self.context.sink.add_message("packet", packet, summary=summary)
            return
        self.context.sink.add_message("text", str(payload))

    def mark_live(self) -> None:
        """Mark the session live one time."""
        if self.context.state.live_marked:
            return
        self.context.state.live_marked = True
        self.context.sink.mark_live()

    def _definition(self) -> UtilityDefinition:
        """Return the checked utility definition."""
        definition = self.context.request.definition
        if not isinstance(definition, UtilityDefinition):
            raise StreamRequestError("bad_request", "The utility definition is not valid.")
        return definition

    @staticmethod
    def _packet(payload: object) -> object:
        """Return packet content from a capture payload."""
        if isinstance(payload, Mapping) and "pcap_dict" in payload:
            return payload["pcap_dict"]
        return payload


@dataclass(slots=True)
class UtilityStreamMonitor:
    """Read utility events until output, quiet, total, or stop limits."""

    context: RunContext
    output: UtilityOutput

    def read(self, client: StreamClient, timing: UtilityTiming, filterer: UtilityMessageFilter, started: float) -> None:
        """Read and filter events until one limit ends the run."""
        last_output = started
        first_deadline = started + timing.first_output_seconds
        total_deadline = started + timing.total_seconds
        while not self._done(first_deadline, total_deadline, last_output, timing):
            event = self._next(client)
            if event is None:
                continue
            last_output = self._handle(event, filterer, last_output)

    def _next(self, client: StreamClient) -> Mapping[str, object] | None:
        """Read one event or absorb a local stop close."""
        try:
            return client.next_event(0.05)
        except ConnectionClosed:
            if self.context.state.stopping.is_set():
                return None
            raise

    def _done(self, first_deadline: float, total_deadline: float, last_output: float, timing: UtilityTiming) -> bool:
        """Return whether a run limit ended the monitor."""
        now = time.monotonic()
        if self.context.state.stopping.is_set() or now >= total_deadline:
            return True
        if self.context.state.output_count == 0:
            return now >= first_deadline
        return now - last_output >= timing.quiet_seconds

    def _handle(self, event: Mapping[str, object], filterer: UtilityMessageFilter, previous: float) -> float:
        """Filter one event and return its output time."""
        payload = FrameDecoder.data_payload(event)
        matches = filterer.offer(payload)
        for match in matches:
            self.output.emit(match)
        return time.monotonic() if matches else previous


@dataclass(slots=True)
class UtilityFinisher:
    """Map utility results to stable session outcomes."""

    context: RunContext

    def finish(self, started: float) -> None:
        """Finish after normal monitoring ends."""
        if self.context.state.stopping.is_set():
            self.stopped()
            return
        if self.context.state.output_count == 0:
            reason = (
                "The device sent no output before the time limit. "
                "Check that the device is connected, then try again."
            )
            self.context.sink.finish(SessionState.TIMED_OUT, reason)
            return
        self.context.sink.finish(SessionState.FINISHED, self._reason(started))

    def stopped(self) -> None:
        """Finish after an operator stop."""
        logger.emit(logging.INFO, "utility_runner_stopped")
        self.context.sink.finish(SessionState.STOPPED, "The operator stopped the session.")

    def failure(self, reason: str) -> None:
        """Finish with one safe failure reason."""
        logger.emit(logging.WARNING, "utility_runner_failed", {"status": "failed", "detail": reason})
        self.context.sink.finish(SessionState.FAILED, reason)

    def error(self, error: Exception) -> None:
        """Map one run exception to a safe final state."""
        UtilityErrorFinisher(self.context, self).finish(error)

    def _reason(self, started: float) -> str:
        """Return the normal completion reason."""
        trigger = self.context.state.trigger
        if trigger is None:
            return "The utility finished."
        total = trigger.listen.timing.total_seconds
        if time.monotonic() - started >= total:
            return f"The utility reached its time limit of {total:g} seconds."
        return "The utility finished."


@dataclass(slots=True)
class UtilityErrorFinisher:
    """Map one utility exception to a safe session outcome."""

    context: RunContext
    finisher: UtilityFinisher

    def finish(self, error: Exception) -> None:
        """Finish one expected or unexpected error."""
        if self.context.state.stopping.is_set():
            self.finisher.stopped()
            return
        reason = self._reason(error)
        if reason is not None:
            self.finisher.failure(reason)
            return
        logger.emit(logging.ERROR, "utility_runner_crash", {"detail": type(error).__name__, "status": "failed"})
        self.context.sink.finish(SessionState.FAILED, "The utility failed. Read the portal log for the cause.")

    @staticmethod
    def _reason(error: Exception) -> str | None:
        """Return a safe expected failure reason."""
        if isinstance(error, SubscribeError):
            return f"The stream subscription failed: {error.detail}."
        if isinstance(error, ConnectionClosed):
            return str(error) or "The utility failed."
        reason = ConnectFailure.reason(error)
        if reason is None and isinstance(error, (StreamRequestError, RuntimeError)):
            reason = str(error) or "The utility failed."
        return reason
