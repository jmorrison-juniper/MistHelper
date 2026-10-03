"""Build the WebSocket portal blueprint from bounded route classes."""

from __future__ import annotations  # Keep Flask annotations lazy.

from flask import Blueprint  # Register the portal routes.

from src.websocket_streams.web.blueprint.responses.download import DownloadResponse  # Register the download route.
from src.websocket_streams.web.blueprint.routes.page import PageRoutes  # Register page and catalog routes.
from src.websocket_streams.web.blueprint.routes.pickers import PickerRoutes  # Register picker routes.
from src.websocket_streams.web.blueprint.routes.sessions import SessionRoutes  # Register session routes.
from src.websocket_streams.web.blueprint.routes.terminal import TerminalRoutes  # Register terminal routes.


class WebSocketBlueprint:
    """Create one Flask blueprint with the established route contract."""

    @classmethod
    def create(cls) -> Blueprint:
        """Return a new WebSocket blueprint."""
        blueprint = Blueprint(  # Keep templates and assets rooted in the web package.
            "websockets",
            "src.websocket_streams.web",
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
            "/api/websockets/sites/<site_id>/devices", view_func=PickerRoutes.devices
        )  # Preserve device picker.
        blueprint.add_url_rule("/api/websockets/sites/<site_id>/maps", view_func=PickerRoutes.maps)  # Preserve maps.
        blueprint.add_url_rule(
            "/api/websockets/sites/<site_id>/assets", view_func=PickerRoutes.assets
        )  # Preserve assets.
        blueprint.add_url_rule(
            "/api/websockets/sites/<site_id>/maps/<map_id>/sdkclients", view_func=PickerRoutes.sdkclients
        )  # Preserve SDK client picker.
        blueprint.add_url_rule("/api/websockets/mxedges", view_func=PickerRoutes.mxedges)  # Preserve Mist Edges.
