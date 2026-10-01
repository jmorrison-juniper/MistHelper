"""Private plans and shared state for one packet capture."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from mistapi.websockets.__ws_client import _MistWebsocket

from src.websocket_streams.intake.start_request import StartRequest
from src.websocket_streams.live.sessions.record import SessionSink, SessionState


@dataclass(frozen=True, slots=True)
class CapturePlan:
    """Keep a checked request and its private capture transport values."""

    request: StartRequest
    channel: str
    duration: int
    body: dict[str, object]
    scope: tuple[str, str]


@dataclass(frozen=True, slots=True)
class CaptureDependencies:
    """Supply a controlled clock and SDK client without a replacement service."""

    clock: Callable[[], float] = time.monotonic
    wait: Callable[[threading.Event, float], bool] = threading.Event.wait
    client_type: type[_MistWebsocket] = _MistWebsocket


@dataclass(slots=True)
class CaptureEvents:
    """Synchronize subscription, stop, and SDK callbacks."""

    stopping: threading.Event = field(default_factory=threading.Event)
    subscribed: threading.Event = field(default_factory=threading.Event)
    closed: threading.Event = field(default_factory=threading.Event)
    wake: threading.Event = field(default_factory=threading.Event)
    lock: threading.RLock = field(default_factory=threading.RLock)


@dataclass(slots=True)
class CaptureProgress:
    """Keep the accepted identity and the first terminal outcome."""

    capture_id: str | None = None
    deadline: float | None = None
    outcome: tuple[SessionState, str] | None = None
    ending: bool = False
    packets: int = 0


@dataclass(slots=True)
class CaptureContext:
    """Share one capture's plan, sink, clock, and synchronized progress."""

    plan: CapturePlan
    sink: SessionSink
    dependencies: CaptureDependencies
    events: CaptureEvents = field(default_factory=CaptureEvents)
    progress: CaptureProgress = field(default_factory=CaptureProgress)
