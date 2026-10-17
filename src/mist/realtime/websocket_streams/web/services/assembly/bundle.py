"""Group the five route-facing WebSocket service classes."""

from __future__ import annotations  # Keep collaborator annotations lazy.

from dataclasses import dataclass  # Store the fixed service set.
from typing import TYPE_CHECKING, Any  # Leaf service types stay independent of assembly.

if TYPE_CHECKING:
    from src.mist.realtime.websocket_streams.web.services.pickers.related import (
        BatchTargetPickerService,
    )  # Keep the target-picker contract typed without a runtime import.


@dataclass(frozen=True, slots=True)
class WebSocketServiceBundle:
    """Hold the five route-facing service boundaries."""

    catalog: Any  # Build the public catalog response.
    sessions: SessionServices  # Own session lifecycle actions.
    artifacts: Any  # Own deletion and download behavior.
    terminal: Any  # Own terminal read, input, and resize behavior.
    pickers: PickerServices  # Own the five Mist picker actions.


@dataclass(frozen=True, slots=True)
class SessionServices:
    """Group lifecycle, messages, and Multi Site batch services."""

    lifecycle: Any  # Start, list, stop, and shut down sessions.
    messages: Any  # Read message pages.
    batches: Any  # Create and admit preview-bound Multi Site work.


@dataclass(frozen=True, slots=True)
class PickerServices:
    """Group site and related resource picker services."""

    site: Any  # Read device, map, and asset rows.
    related: Any  # Read SDK client and Mist Edge rows.
    clients: Any  # Read verified client choices for a selected device.
    batch: BatchTargetPickerService  # Discover targets for one catalog operation.
