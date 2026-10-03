"""Own SDK client and Mist Edge picker actions."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any, cast  # Picker collaborators use behavior types.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Refuse pickers while not ready.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep picker fields safe and bounded.


class RelatedPickerService:
    """Read SDK client and Mist Edge picker rows."""

    def __init__(self, picker: Any | None, reason: str | None) -> None:
        """Store the Mist picker and readiness."""
        self._picker = picker  # A not-ready service has no Mist picker.
        self._reason = reason  # A reason blocks every picker action.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return SDK client picker rows."""
        picker = self._ready_picker("sdkclients")  # Require the production picker.
        return cast(dict[str, object], picker.sdkclients(site_id, map_id))  # Preserve map-scoped behavior.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return Mist Edge picker rows."""
        picker = self._ready_picker("mxedges")  # Require the production picker.
        return cast(dict[str, object], picker.mxedges(site_id))  # Preserve optional site filtering.

    def _ready_picker(self, action: str) -> Any:
        """Return the ready picker or raise the contract error."""
        if self._reason is not None or self._picker is None:  # Pickers need credentials and imports.
            raise StreamRequestError("not_ready", self._reason or "The WebSocket engine is not ready.")  # Refuse.
        logger.emit(logging.DEBUG, "web.picker.read", {"action": action})  # Log only the fixed picker kind.
        return self._picker  # Return the ready Mist picker.
