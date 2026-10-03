"""Execute one utility stream with subscribe-first ordering."""

from __future__ import annotations

import logging
import time
import traceback
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.websocket_streams.intake.fields.error import StreamRequestError
from src.websocket_streams.live.runners.utility.filters.message_filter import UtilityMessageFilter
from src.websocket_streams.live.runners.utility.runner.capture import CaptureCleanup
from src.websocket_streams.live.runners.utility.runner.monitoring import (
    UtilityErrorFinisher,
    UtilityFinisher,
    UtilityOutput,
    UtilityStreamMonitor,
)
from src.websocket_streams.live.runners.utility.triggers.models import UtilityRequest
from src.websocket_streams.live.sessions.record.state import SessionState
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from src.websocket_streams.live.transport.stream_client import StreamClient

if TYPE_CHECKING:
    from src.websocket_streams.live.runners.utility.runner.utility_runner import RunContext

logger = StructuredTransportLogger(logging.getLogger(__name__))


@dataclass(slots=True)
class UtilityStreamOpener:
    """Build the trigger and subscribe its stream."""

    context: RunContext

    def open(self) -> tuple[UtilityRequest, StreamClient]:
        """Return the checked trigger and subscribed client."""
        trigger = self._trigger()
        client = self._client(trigger)
        return trigger, client

    def _trigger(self) -> UtilityRequest:
        """Build and publish one checked trigger."""
        trigger = self.context.triggers.request_for(self.context.request)
        if trigger.listen.channel == "url":
            raise StreamRequestError("bad_request", "This utility must run through the screen runner.")
        with self.context.state.lock:
            self.context.state.trigger = trigger
        return trigger

    def _client(self, trigger: UtilityRequest) -> StreamClient:
        """Subscribe before the REST trigger can emit output."""
        logger.emit(logging.INFO, "utility_stream_open", {"action": trigger.key})
        with self.context.state.lock:
            self.context.state.client = client = StreamClient(self.context.endpoint, [trigger.listen.channel_path])
        client.open()
        logger.emit(logging.DEBUG, "utility_stream_opened", {"action": trigger.key})
        return client


@dataclass(slots=True)
class UtilityTriggerSender:
    """Send one REST trigger and publish its answer."""

    context: RunContext
    output: UtilityOutput

    def send(self, trigger: UtilityRequest) -> Mapping[str, object]:
        """Return one checked trigger answer."""
        logger.emit(logging.INFO, "utility_trigger_send", {"action": trigger.key})
        answer = self._answer(trigger)
        self._publish(answer)
        logger.emit(logging.DEBUG, "utility_trigger_sent", {"status": 200})
        return answer

    def _answer(self, trigger: UtilityRequest) -> Mapping[str, object]:
        """Send one REST request and validate its response."""
        senders = {
            "POST": lambda: self.context.apisession.mist_post(trigger.path, trigger.body),
            "GET": lambda: self.context.apisession.mist_get(trigger.path),
            "DELETE": lambda: self.context.apisession.mist_delete(trigger.path),
        }
        response = senders[trigger.method]()
        status, data = int(getattr(response, "status_code", 0)), getattr(response, "data", {})
        if status != 200 or not isinstance(data, Mapping):
            raise RuntimeError(f"The utility failed with status {status}.")
        return data

    def _publish(self, answer: Mapping[str, object]) -> None:
        """Publish the answer for filtering and capture cleanup."""
        with self.context.state.lock:
            self.context.state.answer = answer
        self.output.mark_live()


@dataclass(slots=True)
class UtilityStarter:
    """Run the subscribe-first trigger sequence."""

    context: RunContext
    output: UtilityOutput

    def start(self) -> tuple[StreamClient, UtilityRequest, UtilityMessageFilter]:
        """Subscribe, guard stop, trigger, and bind."""
        trigger, client = UtilityStreamOpener(self.context).open()
        if self.context.state.stopping.is_set():
            raise RuntimeError("The operator stopped the session.")
        filterer = UtilityMessageFilter(trigger.listen.channel)
        self.output.bind_filter(filterer, UtilityTriggerSender(self.context, self.output).send(trigger))
        return client, trigger, filterer


class UtilityExecution:
    """Own one utility run from preparation through cleanup."""

    def __init__(self, context: RunContext) -> None:
        """Build the run collaborators."""
        self._context = context
        self._output = UtilityOutput(context)
        self._starter = UtilityStarter(context, self._output)
        self._finisher = UtilityFinisher(context)
        self._monitor = UtilityStreamMonitor(context, self._output)

    def run(self) -> None:
        """Execute the complete utility lifecycle."""
        started = time.monotonic()
        try:
            completed = self._execute(started)
            outcome = self._finisher.decide(started, completed)
        except Exception as error:
            outcome = UtilityErrorFinisher(self._context).decide(error)
        except BaseException:
            self._close(self._context.state.stopping.is_set())
            raise
        # Keep cleanup and notification on one decision. A late stop cannot change its state.
        cleanup_failed = self._close(outcome.state == SessionState.STOPPED)
        if cleanup_failed:
            outcome = UtilityFinisher.Outcome(
                SessionState.FAILED, "The utility cleanup failed. Read the portal log for the cause."
            )
        self._finisher.finish(outcome)

    def _execute(self, started: float) -> float:
        """Start and monitor one utility without terminal notification."""
        client, trigger, filterer = self._starter.start()
        self._monitor.read(client, trigger.listen.timing, filterer, started)
        return time.monotonic()

    def _close(self, stopped: bool) -> bool:
        """Attempt both cleanup actions before the terminal notification."""
        with self._context.state.lock:
            client = self._context.state.client
            self._context.state.client = None
        actions = [CaptureCleanup(self._context, stopped).stop_if_needed]
        if client is not None:
            actions.insert(0, client.close)
        failed = False
        for action in actions:
            logger.emit(logging.INFO, "utility_cleanup_start", {"action": action.__name__})
            try:
                action()
                logger.emit(logging.DEBUG, "utility_cleanup_done", {"action": action.__name__})
            except Exception as error:
                failed = True
                self._cleanup_error(error)
        return failed

    @staticmethod
    def _cleanup_error(error: Exception) -> None:
        """Log traceback locations without remote exception content."""
        logger.emit(logging.ERROR, "utility_cleanup_failed", {"detail": type(error).__name__, "status": "failed"})
        for frame in traceback.extract_tb(error.__traceback__):
            logger.emit(
                logging.ERROR, "utility_cleanup_trace", {"detail": f"{frame.filename}:{frame.lineno}:{frame.name}"}
            )
