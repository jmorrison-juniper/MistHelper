"""Page and catalog routes for the WebSocket portal."""

from __future__ import annotations  # Keep Flask annotations lazy.

import logging  # Structured events use repository handlers.

from flask import Response, render_template  # Render the page and type JSON responses.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.
from src.mist.realtime.websocket_streams.web.blueprint.requests.services import ServiceRequest  # Resolve app services.
from src.mist.realtime.websocket_streams.web.blueprint.responses.json_response import (
    JsonResponse,
)  # Convert service results.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep route fields safe and bounded.


class PageRoutes:
    """Serve the WebSocket page and catalog."""

    @staticmethod
    def page() -> str:
        """Render the WebSocket page."""
        logger.emit(logging.INFO, "web.route.page.start")  # Record the bounded render action.
        html: str = render_template("websockets_page.html")  # Render the established page template.
        logger.emit(logging.DEBUG, "web.route.page.finish", {"byte_count": len(html)})  # Report size only.
        return html  # Flask accepts the rendered HTML.

    @staticmethod
    def catalog() -> Response | tuple[Response, int]:
        """Return the WebSocket catalog."""
        services = ServiceRequest.current()  # Resolve the app-scoped service bundle.
        return JsonResponse.call(services.catalog.payload)  # Convert the catalog payload to JSON.
