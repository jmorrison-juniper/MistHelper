"""Session lifecycle routes for the WebSocket portal."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Response, request  # Read methods and type responses.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Query refusals share JSON.
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


class BatchSessionRoutes:
    """Serve Multi Site preview, session, target, and artifact requests."""

    @staticmethod
    def batch_preview() -> Response | tuple[Response, int]:
        """Create one read-only Multi Site target preview."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        body = request.get_json(silent=True)  # The batch service validates the exact request shape.
        return JsonResponse.call(lambda: services.sessions.batches.preview(body), 201)  # Do not start work.

    @staticmethod
    def batch_start() -> Response | tuple[Response, int]:
        """Admit one preview-bound Multi Site parent session."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        body = request.get_json(silent=True)  # The batch service validates the exact request shape.
        return JsonResponse.call(lambda: services.sessions.batches.start(body), 201)  # Admit one public parent.

    @staticmethod
    def batch_summary(session_id: str) -> Response | tuple[Response, int]:
        """Return one batch parent and its current aggregate state."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: services.sessions.batches.summary(session_id)
        )  # Preserve the parent session response shape.

    @staticmethod
    def batch_targets(session_id: str) -> Response | tuple[Response, int]:
        """Return one page of stable target outcomes."""
        values = TargetPageQuery.values()  # Reject malformed cursors before service access.
        if isinstance(values, StreamRequestError):  # Reject bad query values before service access.
            return JsonResponse.error(values)  # Preserve the shared error response shape.
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        after, limit = values  # Keep the validated cursor values together.
        return JsonResponse.call(
            lambda: services.sessions.batches.targets(session_id, after, limit)
        )  # Preserve the batch target response.

    @staticmethod
    def batch_artifacts(session_id: str) -> Response | tuple[Response, int]:
        """Return one safe batch artifact manifest."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: services.artifacts.manifest(session_id)
        )  # Expose only the safe server-owned manifest.


class TargetPageQuery:
    """Validate the cursor and page size for target progress."""

    @staticmethod
    def values() -> tuple[int, int] | StreamRequestError:
        """Return a safe target cursor and bounded page size."""
        if set(request.args) - {"after", "limit"}:  # Refuse query values outside the endpoint contract.
            return StreamRequestError(
                "bad_request", "The target page has an unknown query field."
            )  # Keep the unsupported-query error clear.
        try:  # Parse only integer cursor and size values.
            after = int(request.args.get("after", "0"))  # Default the first target page to zero.
            limit = int(request.args.get("limit", "100"))  # Default to a bounded page size.
        except ValueError:  # Refuse malformed query text before any service call.
            return StreamRequestError(
                "bad_request", "The target page cursor or size is not an integer."
            )  # Keep malformed input distinct.
        if after < 0 or limit < 1:  # Require a nonnegative cursor and positive size.
            return StreamRequestError(
                "bad_request", "The target page cursor or size is not valid."
            )  # Refuse invalid pagination values.
        return after, min(limit, 500)  # Apply the documented maximum page size.
