"""Build the public WebSocket catalog payload."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any  # Catalog and settings use behavior types.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep catalog fields safe and bounded.


class WebSocketCatalogService:
    """Build catalog readiness, entries, and limits."""

    def __init__(self, catalog: Any | None, settings: Any, reason: str | None) -> None:
        """Store catalog collaborators and readiness."""
        self._catalog = catalog  # A not-ready service has no catalog.
        self._settings = settings  # Limits remain available in every state.
        self._reason = reason  # Plain readiness reason for the page.

    def payload(self) -> dict[str, object]:
        """Return the complete public catalog payload."""
        logger.emit(logging.INFO, "web.catalog.payload.start")  # Record the bounded build action.
        payload = self._base_payload()  # Read entries or a safe empty shape.
        payload["ready"] = self._reason is None  # Tell the page whether starts can run.
        payload["reason"] = self._reason  # Preserve the plain readiness reason.
        payload["limits"] = self._settings.limits_payload()  # Add current server limits.
        logger.emit(logging.DEBUG, "web.catalog.payload.finish", {"status": payload["ready"]})  # Log readiness.
        return payload  # Return JSON-safe catalog data.

    def _base_payload(self) -> dict[str, object]:
        """Return catalog entries or a safe empty shape."""
        if self._catalog is None:  # A not-ready portal has no catalog collaborator.
            return {"flags": {}, "channels": [], "utilities": []}  # Preserve the public shape.
        payload = self._catalog.page_payload()  # Let the catalog remove raw channel paths.
        if not isinstance(payload, dict):  # Refuse an invalid collaborator result.
            return {"flags": {}, "channels": [], "utilities": []}  # Prevent unsafe data exposure.
        return payload  # Return the checked catalog payload.
