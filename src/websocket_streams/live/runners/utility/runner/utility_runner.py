"""Start and stop one background utility execution."""

from __future__ import annotations

import logging
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from src.websocket_streams.intake.start_request.models import StartRequest
from src.websocket_streams.live.runners.utility.runner.execution import UtilityExecution
from src.websocket_streams.live.runners.utility.triggers.models import UtilityRequest
from src.websocket_streams.live.runners.utility.triggers.table import UtilityTriggerTable
from src.websocket_streams.live.sessions.record.state import SessionSink
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from src.websocket_streams.live.transport.stream_client import StreamClient

logger = StructuredTransportLogger(logging.getLogger(__name__))


@runtime_checkable
class ApiSessionProtocol(Protocol):
    """Define the REST methods that utility requests use."""

    def mist_post(self, uri: str, body: object | None = None) -> object: ...

    def mist_get(self, uri: str) -> object: ...

    def mist_delete(self, uri: str) -> object: ...


@dataclass(slots=True)
class RunnerState:
    """Hold mutable state shared with stop."""

    stopping: threading.Event = field(default_factory=threading.Event)
    live_marked: bool = False
    output_count: int = 0
    client: StreamClient | None = None
    trigger: UtilityRequest | None = None
    answer: Mapping[str, object] | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass(frozen=True, slots=True)
class RunContext:
    """Hold collaborators for one utility run."""

    apisession: ApiSessionProtocol
    endpoint: MistStreamEndpoint
    request: StartRequest
    sink: SessionSink
    triggers: UtilityTriggerTable
    state: RunnerState


class UtilityRunner:
    """Start and stop one utility trigger and output stream."""

    def __init__(
        self,
        apisession: object,
        endpoint: MistStreamEndpoint,
        request: StartRequest,
        sink: SessionSink,
        *trigger_tables: UtilityTriggerTable,
    ) -> None:
        """Build one utility runner."""
        if len(trigger_tables) > 1:
            raise RuntimeError("The utility runner accepts one trigger table.")
        triggers = trigger_tables[0] if trigger_tables else UtilityTriggerTable()
        self._context = self._context_for(apisession, endpoint, request, sink, triggers)
        self._execution = UtilityExecution(self._context)

    def start(self) -> None:
        """Start the utility and return at once."""
        key = self._context.request.key
        logger.emit(logging.INFO, "utility_runner_start", {"action": key})
        thread = threading.Thread(target=self._execution.run, name=f"ws-util-{key}", daemon=True)
        thread.start()
        logger.emit(logging.DEBUG, "utility_runner_started", {"action": key})

    def stop(self) -> None:
        """Ask the utility to stop and return at once."""
        logger.emit(logging.INFO, "utility_runner_stop", {"action": self._context.request.key})
        self._context.state.stopping.set()
        with self._context.state.lock:
            client = self._context.state.client
        if client is not None:
            client.close()
        logger.emit(logging.DEBUG, "utility_runner_stop_requested", {"status": "stopping"})

    @staticmethod
    def _context_for(
        apisession: object,
        endpoint: MistStreamEndpoint,
        request: StartRequest,
        sink: SessionSink,
        triggers: UtilityTriggerTable,
    ) -> RunContext:
        """Return a checked run context."""
        if not isinstance(apisession, ApiSessionProtocol):
            raise RuntimeError("The API session cannot send utility trigger requests.")
        return RunContext(apisession, endpoint, request, sink, triggers, RunnerState())
