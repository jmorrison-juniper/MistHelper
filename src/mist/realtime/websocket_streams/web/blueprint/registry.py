"""Build the WebSocket portal blueprint from bounded route classes."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Blueprint  # Register the portal routes.

from src.mist.realtime.websocket_streams.web.blueprint.responses.download import (
    DownloadResponse,
)  # Register the download route.
from src.mist.realtime.websocket_streams.web.blueprint.routes.page import (
    PageRoutes,
)  # Register page and catalog routes.
from src.mist.realtime.websocket_streams.web.blueprint.routes.pickers import (
    BatchTargetPickerRoutes,
    ClientPickerRoutes,
    OrganizationPickerRoutes,
    PickerRoutes,
)  # Register resource picker routes.
from src.mist.realtime.websocket_streams.web.blueprint.routes.sessions import (
    BatchSessionRoutes,
    SessionRoutes,
)  # Register session route groups.
from src.mist.realtime.websocket_streams.web.blueprint.routes.terminal import (
    TerminalRoutes,
)  # Register terminal routes.


class WebSocketBlueprint:
    """Create one Flask blueprint with the established route contract."""

    @classmethod
    def create(cls) -> Blueprint:
        """Return a new WebSocket blueprint."""
        blueprint = Blueprint(  # Keep templates and assets rooted in the web package.
            "websockets",
            "src.mist.realtime.websocket_streams.web",
            template_folder="templates",
            static_folder="static",
            static_url_path="/websockets/assets",
        )
        cls._add_page_routes(blueprint)  # Add the page and catalog endpoints.
        cls._add_session_routes(blueprint)  # Add session lifecycle endpoints.
        cls._add_terminal_routes(blueprint)  # Add terminal input and read endpoints.
        cls._add_picker_routes(blueprint)  # Add Mist picker endpoints.
        return blueprint  # Let each application own one blueprint instance.

    @staticmethod
    def _add_page_routes(blueprint: Blueprint) -> None:
        """Add page and catalog routes."""
        blueprint.add_url_rule("/websockets", view_func=PageRoutes.page)  # Preserve the portal page route.
        blueprint.add_url_rule("/api/websockets/catalog", view_func=PageRoutes.catalog)  # Preserve catalog JSON.

    @staticmethod
    def _add_session_routes(blueprint: Blueprint) -> None:
        """Add session lifecycle and download routes."""
        BatchSessionRouteRegistry.add(blueprint)  # Keep Multi Site routes under their own route group.
        blueprint.add_url_rule(
            "/api/websockets/sessions", view_func=SessionRoutes.sessions, methods=["GET", "POST"]
        )  # Preserve list and start methods.
        blueprint.add_url_rule(
            "/api/websockets/sessions/<session_id>/messages", view_func=SessionRoutes.messages
        )  # Preserve message polling.
        blueprint.add_url_rule(
            "/api/websockets/sessions/<session_id>/stop", view_func=SessionRoutes.stop, methods=["POST"]
        )  # Preserve asynchronous stop.
        blueprint.add_url_rule(
            "/api/websockets/sessions/<session_id>", view_func=SessionRoutes.delete, methods=["DELETE"]
        )  # Preserve ended-session deletion.
        blueprint.add_url_rule(
            "/api/websockets/sessions/<session_id>/download", view_func=DownloadResponse.download
        )  # Preserve streamed JSON Lines downloads.

    @staticmethod
    def _add_terminal_routes(blueprint: Blueprint) -> None:
        """Add terminal input, read, and resize routes."""
        blueprint.add_url_rule(
            "/api/websockets/sessions/<session_id>/input", view_func=TerminalRoutes.send, methods=["POST"]
        )  # Preserve exact terminal input.
        blueprint.add_url_rule(
            "/api/websockets/sessions/<session_id>/terminal", view_func=TerminalRoutes.read
        )  # Preserve bounded long polling.
        blueprint.add_url_rule(
            "/api/websockets/sessions/<session_id>/resize", view_func=TerminalRoutes.resize, methods=["POST"]
        )  # Preserve terminal resize.

    @staticmethod
    def _add_picker_routes(blueprint: Blueprint) -> None:
        """Add all Mist picker routes."""
        blueprint.add_url_rule(
            "/api/websockets/batches/sites", view_func=OrganizationPickerRoutes.sites
        )  # Expose complete organization site discovery for batch selection.
        blueprint.add_url_rule(
            "/api/websockets/batches/sites/<site_id>/targets", view_func=BatchTargetPickerRoutes.site_targets
        )  # Expose operation-scoped resources for one site.
        blueprint.add_url_rule(
            "/api/websockets/batches/targets", view_func=BatchTargetPickerRoutes.organization_targets
        )  # Expose organization-scoped operation targets.
        blueprint.add_url_rule(
            "/api/websockets/sites/<site_id>/devices", view_func=PickerRoutes.devices
        )  # Preserve device picker.
        blueprint.add_url_rule(
            "/api/websockets/sites/<site_id>/devices/<device_id>/clients", view_func=ClientPickerRoutes.clients
        )  # Add the read-only scoped client picker.
        blueprint.add_url_rule("/api/websockets/sites/<site_id>/maps", view_func=PickerRoutes.maps)  # Preserve maps.
        blueprint.add_url_rule(
            "/api/websockets/sites/<site_id>/assets", view_func=PickerRoutes.assets
        )  # Preserve assets.
        blueprint.add_url_rule(
            "/api/websockets/sites/<site_id>/maps/<map_id>/sdkclients", view_func=PickerRoutes.sdkclients
        )  # Preserve SDK client picker.
        blueprint.add_url_rule("/api/websockets/mxedges", view_func=PickerRoutes.mxedges)  # Preserve Mist Edges.


class BatchSessionRouteRegistry:
    """Register the additive batch session endpoints."""

    @staticmethod
    def add(blueprint: Blueprint) -> None:
        """Add preview, progress, and archive routes for Multi Site sessions."""
        BatchSessionRouteRegistry._preview_routes(blueprint)  # Register target discovery and session routes.
        BatchSessionRouteRegistry._artifact_routes(blueprint)  # Register manifest and archive access.

    @staticmethod
    def _preview_routes(blueprint: Blueprint) -> None:
        """Add batch preview and target progress routes."""
        blueprint.add_url_rule(
            "/api/websockets/batches/previews", view_func=BatchSessionRoutes.batch_preview, methods=["POST"]
        )  # Create a read-only complete target snapshot.
        blueprint.add_url_rule(
            "/api/websockets/batches", view_func=BatchSessionRoutes.batch_start, methods=["POST"]
        )  # Admit one preview-bound public parent session.
        blueprint.add_url_rule(
            "/api/websockets/batches/<session_id>", view_func=BatchSessionRoutes.batch_summary
        )  # Read the public parent and aggregate target progress.
        blueprint.add_url_rule(
            "/api/websockets/batches/<session_id>/targets", view_func=BatchSessionRoutes.batch_targets
        )  # Read a stable target-list page.

    @staticmethod
    def _artifact_routes(blueprint: Blueprint) -> None:
        """Add batch artifact manifest and archive routes."""
        blueprint.add_url_rule(
            "/api/websockets/batches/<session_id>/artifacts", view_func=BatchSessionRoutes.batch_artifacts
        )  # Read the safe file manifest and retention deadline.
        blueprint.add_url_rule(
            "/api/websockets/batches/<session_id>/download", view_func=DownloadResponse.batch_zip
        )  # Download the selected saved layout as ZIP.
