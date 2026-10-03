"""Resolve the WebSocket service bundle for the active Flask app."""

from __future__ import annotations  # Keep Flask annotations lazy.

from typing import Any, cast  # Resolve the Flask local proxy safely.

from flask import current_app  # Read the active application.

from src.websocket_streams.web.services.assembly.bundle import WebSocketServiceBundle  # Type the route service set.
from src.websocket_streams.web.services.registry import WebSocketServiceRegistry  # Build or reuse app services.


class ServiceRequest:
    """Return the app-scoped service bundle for one route request."""

    @staticmethod
    def current() -> WebSocketServiceBundle:
        """Return the current application's service bundle."""
        app = cast(Any, current_app)._get_current_object()  # Resolve the Flask proxy for the registry.
        return cast(WebSocketServiceBundle, WebSocketServiceRegistry.for_app(app))  # Preserve test injection.
