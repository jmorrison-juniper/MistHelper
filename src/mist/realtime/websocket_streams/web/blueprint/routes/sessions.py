"""Session lifecycle routes for the WebSocket portal."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Response, request  # Read methods and type responses.

from src.mist.realtime.websocket_streams.web.blueprint.requests.services import ServiceRequest  # Resolve app services.
from src.mist.realtime.websocket_streams.web.blueprint.responses.json_response import (
    JsonResponse,
)  # Convert service results.
from src.mist.realtime.websocket_streams.web.blueprint.responses.message import (
    MessageResponse,
)  # Preserve direct JSON text reads.


class SessionRoutes:
    """Serve session lifecycle requests."""

    @staticmethod
    def sessions() -> Response | tuple[Response, int]:
        """List sessions or start one session."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        if request.method == "POST":  # A POST starts one checked session.
            body = request.get_json(silent=True)  # Let the request checker reject an invalid body.
            return JsonResponse.call(lambda: services.sessions.lifecycle.start(body), 201)  # Return the new session.
        return JsonResponse.call(services.sessions.lifecycle.list)  # Return all live and ended sessions.

    @staticmethod
    def messages(session_id: str) -> Response | tuple[Response, int]:
        """Return messages after one sequence number."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return MessageResponse.read(services.sessions.messages, session_id)  # Preserve direct JSON text.

    @staticmethod
    def stop(session_id: str) -> Response | tuple[Response, int]:
        """Stop one session."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(lambda: services.sessions.lifecycle.stop(session_id), 202)  # Return accepted status.

    @staticmethod
    def delete(session_id: str) -> Response | tuple[Response, int]:
        """Delete one ended session."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(lambda: services.artifacts.delete(session_id))  # Return deletion confirmation.
