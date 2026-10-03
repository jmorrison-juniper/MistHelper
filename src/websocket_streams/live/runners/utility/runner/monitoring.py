"""Monitor utility output and choose final session outcomes."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.websocket_streams.catalog.model import UtilityDefinition
from src.websocket_streams.intake.fields.error import StreamRequestError
from src.websocket_streams.live.runners.text.packets import PacketSummary
from src.websocket_streams.live.runners.utility.filters.message_filter import UtilityMessageFilter
from src.websocket_streams.live.runners.utility.triggers.models import UtilityTiming
from src.websocket_streams.live.sessions.record.state import SessionState
from src.websocket_streams.live.transport.endpoint import ConnectFailure
from src.websocket_streams.live.transport.runtime.frame_decoder import FrameDecoder, SubscribeError
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from src.websocket_streams.live.transport.runtime.reader.contracts import ConnectionClosed
from src.websocket_streams.live.transport.stream_client import StreamClient

if TYPE_CHECKING:
    from src.websocket_streams.live.runners.utility.runner.utility_runner import RunContext

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

    @dataclass(frozen=True, slots=True)
    class Outcome:
        """Hold the terminal decision before cleanup starts."""

        state: SessionState
        reason: str

    context: RunContext

    def decide(self, started: float, completed: float) -> UtilityFinisher.Outcome:
        """Freeze the normal decision at the original completion point."""
        if self.context.state.stopping.is_set():
            return self.Outcome(SessionState.STOPPED, "The operator stopped the session.")
        if self.context.state.output_count == 0:
            reason = (
                "The device sent no output before the time limit. "
                "Check that the device is connected, then try again."
            )
            return self.Outcome(SessionState.TIMED_OUT, reason)
        return self.Outcome(SessionState.FINISHED, self._reason(started, completed))

    def finish(self, outcome: UtilityFinisher.Outcome) -> None:
        """Publish one immutable decision after cleanup resolves."""
        logger.emit(logging.INFO, "utility_terminal_publish", {"status": outcome.state.value, "count": 1})
        if outcome.state == SessionState.STOPPED:
            logger.emit(logging.INFO, "utility_runner_stopped")
        elif outcome.state == SessionState.FAILED:
            logger.emit(logging.WARNING, "utility_runner_failed", {"status": "failed", "detail": outcome.reason})
        self.context.sink.finish(outcome.state, outcome.reason)
        logger.emit(logging.DEBUG, "utility_terminal_published", {"status": outcome.state.value, "count": 1})

    def _reason(self, started: float, completed: float) -> str:
        """Return the normal completion reason."""
        trigger = self.context.state.trigger
        if trigger is None:
            return "The utility finished."
        total = trigger.listen.timing.total_seconds
        if completed - started >= total:
            return f"The utility reached its time limit of {total:g} seconds."
        return "The utility finished."


@dataclass(slots=True)
class UtilityErrorFinisher:
    """Map one utility exception to a safe session outcome."""

    context: RunContext

    def decide(self, error: Exception) -> UtilityFinisher.Outcome:
        """Freeze one expected or unexpected error before cleanup."""
        if self.context.state.stopping.is_set():
            return UtilityFinisher.Outcome(SessionState.STOPPED, "The operator stopped the session.")
        reason = self._reason(error)
        if reason is not None:
            return UtilityFinisher.Outcome(SessionState.FAILED, reason)
        logger.emit(logging.ERROR, "utility_runner_crash", {"detail": type(error).__name__, "status": "failed"})
        return UtilityFinisher.Outcome(SessionState.FAILED, "The utility failed. Read the portal log for the cause.")

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
