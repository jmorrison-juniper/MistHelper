"""The assembled picker service used by the WebSocket portal."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from src.mist.realtime.websocket_streams.intake.pickers.devices import (
    DevicePicker,
)  # Device behavior owns the short cache.
from src.mist.realtime.websocket_streams.intake.pickers.resources import (
    EdgePicker,
    ResourcePicker,
)  # Site and edge SDK reads.


class StreamPickerService(DevicePicker, ResourcePicker, EdgePicker):
    """Provide all picker capabilities through named behavior classes."""

    def __init__(self, apisession: object, org_id: str) -> None:
        """Store shared SDK state and the device cache."""
        self._apisession = apisession  # Every picker read uses the same authenticated session.
        self._org_id = org_id  # Organization-scope Mist Edge reads use this identifier.
        self._device_cache: dict[str, tuple[float, list[dict[str, object]]]] = {}  # Cache devices for 30 seconds.
