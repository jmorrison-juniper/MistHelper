"""Dependency injection context for WebSocket command classes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class WebSocketCmdDeps:
    """Injected dependencies for WebSocket command methods.

    Passed from MistHelper dispatch table to avoid direct MistHelper global usage
    inside extracted src/websocket modules.
    """

    apisession: Any
    select_site_fn: Callable
    select_device_fn: Callable
    validate_target_fn: Callable
    list_devices_fn: Callable
    safe_input_fn: Callable
