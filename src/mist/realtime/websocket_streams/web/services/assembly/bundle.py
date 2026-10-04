"""Group the five route-facing WebSocket service classes."""

from __future__ import annotations  # Keep collaborator annotations lazy.

from dataclasses import dataclass  # Store the fixed service set.
from typing import Any  # Leaf service types stay independent of assembly.


@dataclass(frozen=True, slots=True)
class WebSocketServiceBundle:
    """Hold the five route-facing service boundaries."""

    catalog: Any  # Build the public catalog response.
    sessions: Any  # Own session lifecycle actions.
    artifacts: Any  # Own deletion and download behavior.
    terminal: Any  # Own terminal read, input, and resize behavior.
    pickers: Any  # Own the five Mist picker actions.


@dataclass(frozen=True, slots=True)
class SessionServices:
    """Group lifecycle and message session services."""

    lifecycle: Any  # Start, list, stop, and shut down sessions.
    messages: Any  # Read message pages.


@dataclass(frozen=True, slots=True)
class PickerServices:
    """Group site and related resource picker services."""

    site: Any  # Read device, map, and asset rows.
    related: Any  # Read SDK client and Mist Edge rows.
