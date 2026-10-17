"""Mist resource picker routes for WebSocket starts."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Response, request  # Read the optional site and type responses.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Return the shared error contract.
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


class OrganizationPickerRoutes:
    """Serve organization-wide WebSocket target discovery."""

    @staticmethod
    def sites() -> Response | tuple[Response, int]:
        """Return complete site rows for the configured organization."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.

        def action() -> dict[str, object]:
            kind, key, _parents = BatchTargetPickerRoutes._query({"kind", "key"})
            return services.pickers.batch.sites(kind, key)  # Validate operation scope before listing sites.

        return JsonResponse.call(action)  # Keep operation-driven site discovery inside the error boundary.


class BatchTargetPickerRoutes:
    """Serve catalog-scoped Multi Site target discovery."""

    @staticmethod
    def site_targets(site_id: str) -> Response | tuple[Response, int]:
        """Return eligible targets for one selected organization site."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.

        def action() -> dict[str, object]:
            IdentifierRequest.require_uuid(site_id, "site_id")  # Validate scope before any Mist request.
            kind, key, parents = BatchTargetPickerRoutes._query(
                {"kind", "key", "device_id", "map_id"}
            )  # Reject unknown and repeated query fields.
            return services.pickers.batch.targets(site_id, kind, key, parents)  # Use catalog metadata.

        return JsonResponse.call(action)  # Convert checked discovery errors to the route contract.

    @staticmethod
    def organization_targets() -> Response | tuple[Response, int]:
        """Return eligible targets for one organization-scoped operation."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.

        def action() -> dict[str, object]:
            kind, key, parents = BatchTargetPickerRoutes._query({"kind", "key"})
            return services.pickers.batch.targets(None, kind, key, parents)  # Keep organization scope server-owned.

        return JsonResponse.call(action)  # Convert checked discovery errors to the route contract.

    @staticmethod
    def _query(allowed: set[str]) -> tuple[str, str, dict[str, str]]:
        """Read one catalog identity and only allowed parent identifiers."""
        values = BatchTargetPickerRoutes._query_values(allowed)  # Validate parameter names and duplicate values.
        kind, key = request.args.get("kind"), request.args.get("key")  # Read the required catalog identity.
        if not kind or not key:
            raise StreamRequestError("bad_request", "The target request needs a catalog operation.")
        parents = {name: value[0] for name, value in values.items() if name in {"device_id", "map_id"} and value}
        for name, value in parents.items():
            IdentifierRequest.require_uuid(value, name)  # Validate parent identifiers before discovery.
        return kind, key, parents  # Pass only the checked catalog identity and required parents.

    @staticmethod
    def _query_values(allowed: set[str]) -> dict[str, list[str]]:
        """Reject unknown or repeated target query fields."""
        unknown = set(request.args.keys()) - allowed  # Refuse browser-supplied discovery controls.
        if unknown:
            raise StreamRequestError("bad_request", "The target request has an unknown field.")
        values = {name: request.args.getlist(name) for name in allowed}  # Preserve duplicate query parameters.
        if any(len(value) > 1 for value in values.values()):
            raise StreamRequestError("bad_request", "The target request repeats a field.")
        return values  # Keep only complete, single-value route parameters.
