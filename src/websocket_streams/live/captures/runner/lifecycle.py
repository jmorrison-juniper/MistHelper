"""Separate capture admission, cloud stop, and connection cleanup."""

from __future__ import annotations

import logging

from requests.exceptions import RequestException

from src.websocket_streams.intake.fields import StreamRequestError
from src.websocket_streams.live.captures.control import CaptureAPI
from src.websocket_streams.live.captures.model import CaptureContext
from src.websocket_streams.live.captures.transport import CaptureConnection, CaptureFeed, CaptureRecords
from src.websocket_streams.live.sessions.record import SessionState
from websocket import WebSocketException

logger = logging.getLogger(__name__)


class CaptureSubscription:
    """Wait for the exact confirmation instead of an open socket."""

    def __init__(self, context: CaptureContext) -> None:
        """Share the capture clock and stop signals."""
        self.context = context

    def wait(self) -> bool:
        """Bound confirmation wait and admit no capture after an earlier stop."""
        context = self.context
        deadline = context.dependencies.clock() + 10.0
        while not context.events.stopping.is_set():
            with context.events.lock:
                if context.progress.outcome is not None:
                    raise StreamRequestError("not_ready", context.progress.outcome[1])
                if context.events.subscribed.is_set():
                    return True
            remaining = deadline - context.dependencies.clock()
            if remaining <= 0:
                raise StreamRequestError(
                    "not_ready", "The packet subscription was not confirmed before the time limit."
                )
            context.dependencies.wait(context.events.wake, min(0.25, remaining))
            context.events.wake.clear()
        return False


class CaptureMonitor:
    """Own target checks, capture admission, and the selected duration."""

    def __init__(self, apisession: object, context: CaptureContext) -> None:
        """Build the private API transport and owned record path."""
        self.context = context
        self.api = CaptureAPI(apisession, context)
        self.records = CaptureRecords(context)
        self.connection = CaptureConnection(apisession, context, CaptureFeed(context, self.records))

    def run(self) -> None:
        """Require confirmation and finalize every admitted worker."""
        context = self.context
        try:
            self._observe()
        except StreamRequestError as error:
            state = (
                SessionState.STOPPED
                if error.code == "not_open" and context.events.stopping.is_set()
                else SessionState.FAILED
            )
            context.progress.outcome = (state, error.message)
            logger.error("Packet capture worker refused code=%s", error.code)
        except (OSError, RuntimeError, ValueError, RequestException, WebSocketException) as error:
            context.progress.outcome = (
                SessionState.FAILED,
                "The packet capture failed. Its cloud state can be uncertain.",
            )
            logger.error("Packet capture worker failed error_type=%s", type(error).__name__)
        finally:
            CaptureFinalizer(context, self.api, self.connection).finish()

    def _observe(self) -> None:
        """Keep target checks and confirmed subscription before capture admission."""
        if self.context.events.stopping.is_set():
            return
        self.api.authorize()
        if self.context.events.stopping.is_set():
            return
        self.connection.open()
        if CaptureSubscription(self.context).wait():
            self._start()
            self._wait()

    def _start(self) -> None:
        """Establish accepted identity before pending records reach the card."""
        context = self.context
        with context.events.lock:
            if context.events.stopping.is_set():
                return
        capture_id = self.api.start()
        with context.events.lock:
            context.progress.capture_id = capture_id
            context.progress.deadline = context.dependencies.clock() + context.plan.duration
            if not context.events.stopping.is_set() and context.progress.outcome is None:
                context.sink.mark_live(f"Mist accepted a capture for {context.plan.duration} seconds.")
                self.records.flush()

    def _wait(self) -> None:
        """Keep the stream through the accepted capture's own deadline."""
        context = self.context
        while not context.events.stopping.is_set() and context.progress.outcome is None:
            deadline = context.progress.deadline
            if deadline is None:
                raise StreamRequestError("not_ready", "The packet capture has no confirmed duration.")
            remaining = deadline - context.dependencies.clock()
            if remaining <= 0:
                state = SessionState.FINISHED if context.progress.packets else SessionState.TIMED_OUT
                context.progress.outcome = (state, "The selected packet capture duration ended.")
                return
            context.dependencies.wait(context.events.wake, min(0.25, remaining))
            context.events.wake.clear()


class CaptureFinalizer:
    """Attempt cloud stop independently of connection cleanup."""

    def __init__(self, context: CaptureContext, api: CaptureAPI, connection: CaptureConnection) -> None:
        """Keep final actions under one capture's ownership."""
        self.context = context
        self.api = api
        self.connection = connection

    def finish(self) -> None:
        """Retain failures and release resources even after a refused cloud stop."""
        with self.context.events.lock:
            self.context.progress.ending = True
        outcome = self.context.progress.outcome
        try:
            outcome = self._stop(outcome)
        except (StreamRequestError, OSError, RuntimeError, ValueError, RequestException, WebSocketException) as error:
            outcome = self._failure(error)
        outcome = self._close(outcome)
        state, reason = outcome or (SessionState.FAILED, "The packet capture ended without a confirmed outcome.")
        self.context.sink.finish(state, reason)

    def _stop(self, outcome: tuple[SessionState, str] | None) -> tuple[SessionState, str] | None:
        """Confirm the single matching cloud stop before a successful stop state."""
        progress = self.context.progress
        stopping = self.context.events.stopping.is_set()
        if progress.capture_id and (stopping or (outcome and outcome[0] is SessionState.FAILED)):
            self.api.stop(progress.capture_id)
            if stopping:
                return SessionState.STOPPED, "Mist accepted the stop request for this capture."
        if stopping:
            return outcome or (SessionState.STOPPED, "The packet capture stopped before capture start.")
        return outcome

    def _close(self, outcome: tuple[SessionState, str] | None) -> tuple[SessionState, str] | None:
        """Close both transports without letting one failure skip the other."""
        try:
            self.connection.close()
        except (StreamRequestError, OSError, RuntimeError, ValueError, RequestException, WebSocketException) as error:
            outcome = self._failure(error)
        try:
            self.api.close()
        except (OSError, RuntimeError, ValueError, RequestException) as error:
            outcome = self._failure(error)
        return outcome

    @staticmethod
    def _failure(error: Exception) -> tuple[SessionState, str]:
        """Report safe action failures without remote exception text."""
        logger.error("Packet capture cleanup failed error_type=%s", type(error).__name__)
        reason = (
            error.message
            if isinstance(error, StreamRequestError)
            else "The capture cleanup failed. Mist can still capture packets."
        )
        return SessionState.FAILED, reason
