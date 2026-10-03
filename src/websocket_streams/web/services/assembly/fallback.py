"""Provide safe not-ready collaborators for WebSocket routes."""

from __future__ import annotations  # Keep annotations lazy.

import logging  # Structured events use repository handlers.

from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep fallback fields safe and bounded.


class EmptySessionManager:
    """Answer safe list and shutdown calls before the engine is ready."""

    def list_payload(self) -> dict[str, object]:
        """Return an empty session list."""
        return {"sessions": [], "limits": {"max_sessions": 0, "live_count": 0}}  # Preserve the list shape.

    def shutdown(self) -> None:
        """Confirm that no manager requires shutdown."""
        logger.emit(logging.DEBUG, "web.service.empty.stop", {"status": "missing"})  # Record the safe no-op.


class FallbackSettings:
    """Return stable limits before normal settings can load."""

    def limits_payload(self) -> dict[str, int]:
        """Return zero live limits and the established capture limit."""
        return {"max_sessions": 0, "idle_seconds": 0, "capture_seconds": 60}  # Preserve the public shape.
