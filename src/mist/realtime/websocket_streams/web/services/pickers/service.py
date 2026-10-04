"""Own the five Mist picker service actions."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any, cast  # Picker collaborators use behavior types.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Refuse pickers while not ready.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep picker fields safe and bounded.


class SitePickerService:
    """Read device, map, and asset picker rows."""

    def __init__(self, picker: Any | None, reason: str | None) -> None:
        """Store the Mist picker and readiness."""
        self._picker = picker  # A not-ready service has no Mist picker.
        self._reason = reason  # A reason blocks every picker action.

    def devices(self, site_id: str) -> dict[str, object]:
        """Return device picker rows."""
        picker = self._ready_picker("devices")  # Require the production picker.
        return cast(dict[str, object], picker.devices(site_id))  # Preserve device filtering and cache behavior.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return map picker rows."""
        picker = self._ready_picker("maps")  # Require the production picker.
        return cast(dict[str, object], picker.maps(site_id))  # Preserve map filtering and cache behavior.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return asset picker rows."""
        picker = self._ready_picker("assets")  # Require the production picker.
        return cast(dict[str, object], picker.assets(site_id))  # Preserve asset filtering and cache behavior.

    def _ready_picker(self, action: str) -> Any:
        """Return the ready picker or raise the contract error."""
        if self._reason is not None or self._picker is None:  # Pickers need credentials and imports.
            raise StreamRequestError("not_ready", self._reason or "The WebSocket engine is not ready.")  # Refuse.
        logger.emit(logging.DEBUG, "web.picker.read", {"action": action})  # Log only the fixed picker kind.
        return self._picker  # Return the ready Mist picker.
