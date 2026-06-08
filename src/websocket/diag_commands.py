"""Thin façade for WebSocket network diagnostic commands (ping + ARP).

The real implementations live under :mod:`src.websocket.diagnostics` as focused
executor classes. This module preserves the legacy public class and static-method
signatures so callers and tests continue to import ``WebSocketNetworkDiagCommands``
from here.
"""

from __future__ import annotations  # Defer annotation evaluation for forward refs

from src.websocket.context import WebSocketCmdDeps  # Injected dependency bundle (back-compat)
from src.websocket.diagnostics import (  # Executor collaborators implementing the real workflow
    ArpDeviceExecutor,
    PingDeviceExecutor,
)

__all__ = ["WebSocketNetworkDiagCommands"]  # Explicit public surface for this façade module


class WebSocketNetworkDiagCommands:
    """WebSocket Network Diagnostic Commands (thin façade).

    Handles ping and ARP operations via WebSocket. The behavior is delegated to
    :class:`~src.websocket.diagnostics.PingDeviceExecutor` and
    :class:`~src.websocket.diagnostics.ArpDeviceExecutor` so each diagnostic
    workflow can be evolved and tested independently.
    """

    @staticmethod
    def ping_device(deps: WebSocketCmdDeps) -> None:
        """Execute the interactive ping-over-WebSocket workflow."""
        PingDeviceExecutor().execute(deps)  # Delegate to the per-call executor instance

    @staticmethod
    def arp_device(deps: WebSocketCmdDeps) -> None:
        """Execute the interactive ARP-over-WebSocket workflow."""
        ArpDeviceExecutor().execute(deps)  # Delegate to the per-call executor instance
