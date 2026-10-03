"""Hold bounded channel runner state and result contracts."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # Runner state uses events and locks across two threads.
from dataclasses import dataclass, field  # Related mutable values stay grouped.
from enum import StrEnum  # Attempt results need stable text values.

from src.websocket_streams.live.transport.stream_client import StreamClient  # Runtime state owns the active client.


class AttemptResult(StrEnum):
    """Name each result from one channel connection attempt."""

    STOPPED = "stopped"  # The operator stopped the runner.
    HEALTHY_DROP = "healthy_drop"  # Useful or stable operation earned a new budget.
    DROPPED = "dropped"  # The attempt failed before healthy operation.
    FINAL = "final"  # A permanent failure already finished the session.


@dataclass(slots=True)
class ChannelRuntimeState:
    """Hold thread controls for one channel runner."""

    client: StreamClient | None = None  # stop() closes the active client.
    thread: threading.Thread | None = None  # start() stores the reader thread.
    stop: threading.Event = field(default_factory=threading.Event)  # Stop wakes waits and reads.


@dataclass(slots=True)
class ChannelOutcomeState:
    """Hold final outcome and retry reason state."""

    finish_lock: threading.Lock = field(default_factory=threading.Lock)  # One final state can win.
    finished: bool = False  # The first finish operation sets this value.
    last_open_failure: str | None = None  # Retry exhaustion uses the last safe reason.


@dataclass(slots=True)
class ChannelAttemptState:
    """Hold health evidence for one connection attempt."""

    received_event: bool = False  # A delivered event proves useful operation.
    subscribed_at: float | None = None  # Stable time starts after all subscriptions succeed.


@dataclass(slots=True)
class ChannelRunnerState:
    """Group all mutable channel runner state."""

    runtime: ChannelRuntimeState = field(default_factory=ChannelRuntimeState)  # Own thread controls.
    outcome: ChannelOutcomeState = field(default_factory=ChannelOutcomeState)  # Own final result data.
    attempt: ChannelAttemptState = field(default_factory=ChannelAttemptState)  # Own current health data.
