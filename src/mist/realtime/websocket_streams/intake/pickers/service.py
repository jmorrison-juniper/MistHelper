"""The assembled picker service used by the WebSocket portal."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Report unavailable client association as an explicit route error.
from src.mist.realtime.websocket_streams.intake.pickers.devices import (
    DevicePicker,
)  # Device behavior owns the short cache.
from src.mist.realtime.websocket_streams.intake.pickers.resources import (
    EdgePicker,
    ResourcePicker,
    WiredClientPicker,
)  # Site and edge SDK reads.


class StreamPickerService(DevicePicker, ResourcePicker, WiredClientPicker, EdgePicker):
    """Provide all picker capabilities through named behavior classes."""

    def __init__(self, apisession: object, org_id: str) -> None:
        """Store shared SDK state and the device cache."""
        self._apisession = apisession  # Every picker read uses the same authenticated session.
        self._org_id = org_id  # Organization-scope Mist Edge reads use this identifier.
        self._device_cache: dict[str, tuple[float, list[dict[str, object]]]] = {}  # Cache devices for 30 seconds.

    def clients(self, site_id: str, device_id: str) -> dict[str, object]:
        """Return read-only wired choices for one selected switch."""
        device = self.describe_device(site_id, device_id)  # Resolve the ID only within the selected site.
        if device is None:
            raise StreamRequestError(
                "picker_unavailable", "The selected device is not available at this site. Enter a MAC address manually."
            )  # Do not query a device outside the selected site.
        if device.family != "ex":
            raise StreamRequestError(
                "picker_unavailable",
                "Gateway association is not verified. Enter a client MAC address manually.",
            )  # Do not use site-wide WAN clients for gateways.
        device_mac = device.mac  # Use the validated MAC from the site-scoped device record.
        if device_mac is None:
            raise StreamRequestError(
                "picker_unavailable", "The selected switch has no verified MAC address. Enter a MAC address manually."
            )  # Do not query a switch with unknown identity.
        return WiredClientPicker.clients(self, site_id, device_mac)  # Run only the proven EX wired-client lookup.
