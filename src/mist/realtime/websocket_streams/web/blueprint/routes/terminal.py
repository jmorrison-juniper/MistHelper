"""Interactive terminal routes for WebSocket sessions."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Response, request  # Read JSON bodies and type responses.

from src.mist.realtime.websocket_streams.web.blueprint.requests.services import ServiceRequest  # Resolve app services.
from src.mist.realtime.websocket_streams.web.blueprint.requests.terminal import (
    TerminalRequest,
)  # Validate terminal values.
from src.mist.realtime.websocket_streams.web.blueprint.responses.json_response import (
    JsonResponse,
)  # Convert service results.


class TerminalRoutes:
    """Serve terminal input, output, and size requests."""

    @staticmethod
    def send(session_id: str) -> Response | tuple[Response, int]:
        """Send exact key or paste text to one terminal."""
        body = request.get_json(silent=True)  # Read the untrusted JSON body once.
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: services.terminal.send(session_id, TerminalRequest.input_text(body)), 202
        )  # Validate and send exact text inside the error boundary.

    @staticmethod
    def read(session_id: str) -> Response | tuple[Response, int]:
        """Read terminal bytes with a bounded wait."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: services.terminal.read(session_id, *TerminalRequest.read_query())
        )  # Validate and long poll inside the error boundary.

    @staticmethod
    def resize(session_id: str) -> Response | tuple[Response, int]:
        """Send one checked terminal size."""
        body = request.get_json(silent=True)  # Read the untrusted JSON body once.
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: services.terminal.resize(session_id, *TerminalRequest.size(body)), 202
        )  # Validate and resize inside the error boundary.
