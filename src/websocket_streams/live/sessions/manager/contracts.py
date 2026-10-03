"""Define session manager runner contracts."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # Shared manager attributes include locks, events, and threads.
from collections.abc import Callable  # Shared manager operations use typed callables.
from typing import Protocol  # Managers depend on runner behavior only.

from src.websocket_streams.intake.start_request.models import StartRequest  # Factories receive checked requests.
from src.websocket_streams.live.sessions.record.session import StreamSession  # The manager stores concrete sessions.
from src.websocket_streams.live.sessions.record.state import SessionSink  # Runners write through the session sink.
from src.websocket_streams.live.sessions.settings import StreamSettings  # Shared operations use configured limits.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import StructuredTransportLogger  # T072.


class StreamRunner(Protocol):
    """Describe the lifecycle behavior of each runner."""

    def start(self) -> None:
        """Start stream work and return at once."""

    def stop(self) -> None:
        """Request stream stop and return at once."""


class RunnerFactoryLike(Protocol):
    """Describe a factory that builds one stream runner."""

    def build(self, request: StartRequest, sink: SessionSink) -> StreamRunner:
        """Build the runner for one checked request."""


class SessionBuilderLike(Protocol):
    """Describe a builder that returns one complete stopped session."""

    def build(self, request: StartRequest) -> StreamSession:
        """Build a session and attach its runner."""


class ManagerAttributes:
    """Declare state shared by all concrete manager operation classes."""

    _settings: StreamSettings  # Admission and cleanup use immutable limits.
    _clock: Callable[[], float]  # Cleanup uses production or fake monotonic time.
    _lock: threading.RLock  # Web requests and cleanup share the session map.
    _sessions: dict[str, StreamSession]  # Public identifiers map to sessions.
    _builder: SessionBuilderLike  # Starts build complete sessions before insertion.
    _logger: StructuredTransportLogger  # All records cross the T072 boundary.
    _reaper_stop: threading.Event  # Shutdown wakes the cleanup wait.
    _reaper_thread: threading.Thread | None  # Cleanup starts lazily.
    _shutdown: bool  # Repeat shutdown stays safe.
    session: Callable[[str], StreamSession]  # Operations resolve one public identifier.
    stop: Callable[..., dict[str, object]]  # Cleanup reuses normal stop semantics.
    _reap_session: Callable[[StreamSession], None]  # Reaper applies one-session rules.
    _prune_ended: Callable[[], None]  # Reaper applies ended-session retention.
