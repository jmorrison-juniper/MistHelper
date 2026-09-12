"""Dependency injection context for WebSocket command classes."""

from __future__ import annotations  # WHY: postponed evaluation for PEP 604 unions on 3.13

from collections.abc import Callable  # WHY: precise callable type for injected functions
from dataclasses import dataclass  # WHY: frozen-shape container for DI bundle
from typing import Any  # WHY: apisession + callables are structurally opaque


@dataclass
class WebSocketCmdDeps:  # WHY: DI bundle passed from MistHelper to /websocket handlers
    """Injected dependencies for WebSocket command methods.

    Passed from MistHelper dispatch table to avoid direct MistHelper global usage
    inside extracted src/websocket modules.
    """

    apisession: Any  # WHY: mistapi session object used by every ws command
    select_site_fn: Callable[..., Any]  # WHY: interactive site picker callback
    select_device_fn: Callable[..., Any]  # WHY: interactive device picker callback
    validate_target_fn: Callable[..., Any]  # WHY: pre-flight target validator callback
    list_devices_fn: Callable[..., Any]  # WHY: device enumeration helper callback
    safe_input_fn: Callable[..., Any]  # WHY: EOF-safe input reader for prompts
