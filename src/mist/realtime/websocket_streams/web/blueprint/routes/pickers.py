"""Mist resource picker routes for WebSocket starts."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Response, request  # Read the optional site and type responses.

from src.mist.realtime.websocket_streams.web.blueprint.requests.identifiers import (
    IdentifierRequest,
)  # Validate UUID values.
from src.mist.realtime.websocket_streams.web.blueprint.requests.services import ServiceRequest  # Resolve app services.
from src.mist.realtime.websocket_streams.web.blueprint.responses.json_response import (
    JsonResponse,
)  # Convert service results.


class PickerRoutes:
    """Serve each WebSocket resource picker."""

    @staticmethod
    def devices(site_id: str) -> Response | tuple[Response, int]:
        """Return device picker rows."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: IdentifierRequest.require_uuid(site_id, "site_id") or services.pickers.site.devices(site_id)
        )  # Validate and return device rows inside the error boundary.

    @staticmethod
    def maps(site_id: str) -> Response | tuple[Response, int]:
        """Return map picker rows."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: IdentifierRequest.require_uuid(site_id, "site_id") or services.pickers.site.maps(site_id)
        )  # Validate and return map rows inside the error boundary.

    @staticmethod
    def assets(site_id: str) -> Response | tuple[Response, int]:
        """Return asset picker rows."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: IdentifierRequest.require_uuid(site_id, "site_id") or services.pickers.site.assets(site_id)
        )  # Validate and return asset rows inside the error boundary.

    @staticmethod
    def sdkclients(site_id: str, map_id: str) -> Response | tuple[Response, int]:
        """Return SDK client picker rows."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: (
                IdentifierRequest.require_uuid(site_id, "site_id"),
                IdentifierRequest.require_uuid(map_id, "map_id"),
                services.pickers.related.sdkclients(site_id, map_id),
            )[2]
        )  # Validate both identifiers and return client rows inside the error boundary.

    @staticmethod
    def mxedges() -> Response | tuple[Response, int]:
        """Return Mist Edge picker rows."""
        site_id = request.args.get("site_id")  # Read the optional site filter.
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: IdentifierRequest.require_optional_uuid(site_id, "site_id")
            or services.pickers.related.mxedges(site_id)
        )  # Validate and return Mist Edge rows inside the error boundary.


class ClientPickerRoutes:
    """Serve the selected-device client suggestion route."""

    @staticmethod
    def clients(site_id: str, device_id: str) -> Response | tuple[Response, int]:
        """Return wired-client suggestions for one selected device."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(
            lambda: (
                IdentifierRequest.require_uuid(site_id, "site_id"),
                IdentifierRequest.require_uuid(device_id, "device_id"),
                services.pickers.clients.clients(site_id, device_id),
            )[2]
        )  # Validate both target identifiers before the Mist read.
