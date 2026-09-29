"""Mist API client for the RMA device replacement operation."""

from __future__ import annotations  # WHY: keep annotations lightweight during import.

import logging  # WHY: log before and after every Mist API call.
from typing import Any  # WHY: mistapi responses are dynamically typed.

import mistapi  # WHY: use the installed SDK operations verified in research.md.

from src.inventory.device_replace.models import InventoryDevice, ReplaceRequest  # WHY: client returns typed records.

logger = logging.getLogger(__name__)  # WHY: module log records identify the API seam.

DEFAULT_PAGE_LIMIT = 1000  # WHY: match the established inventory export page size.


class DeviceReplaceClient:
    """Read inventory, read old configuration, and send replacement requests."""

    def __init__(self, apisession: Any, org_id: str, page_limit: int = DEFAULT_PAGE_LIMIT) -> None:
        """Store the Mist session and organization context."""
        self._apisession = apisession  # WHY: every SDK call needs the active Mist session.
        self._org_id = org_id  # WHY: inventory calls are scoped to one organization.
        self._page_limit = max(1, int(page_limit))  # WHY: a nonpositive limit would make paging invalid.

    def list_inventory(self) -> list[InventoryDevice]:
        """Return normalized inventory devices for the organization."""
        logger.info("Reading organization inventory for device replacement org=%s", self._org_id)  # WHY: action log.
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(self._apisession, self._org_id, limit=self._page_limit)
        rows = mistapi.get_all(response=response, mist_session=self._apisession)  # WHY: include additional pages.
        devices = [InventoryDevice.from_row(row) for row in rows if isinstance(row, dict)]  # WHY: skip bad rows.
        logger.debug("Read %d inventory devices for replacement", len(devices))  # WHY: result summary after read.
        return devices  # WHY: operation layer owns selection and display.

    def get_old_configuration(self, old_device: InventoryDevice) -> dict[str, Any]:
        """Return the old device configuration from the site device endpoint."""
        logger.info("Reading old device configuration for backup device=%s", old_device.mac)  # WHY: action log.
        response = mistapi.api.v1.sites.devices.getSiteDevice(
            self._apisession, old_device.site_id, old_device.device_id
        )
        data = response.data if isinstance(response.data, dict) else {}  # WHY: backup JSON must be an object.
        logger.debug("Read old device configuration keys=%d", len(data))  # WHY: result summary without secrets.
        return dict(data)  # WHY: persistence should own an independent copy.

    def replace_device(self, request: ReplaceRequest) -> dict[str, Any]:
        """Send the replacement request to Mist."""
        body = request.as_body()  # WHY: construct the OpenAPI payload once for logging and send.
        logger.info("Sending Mist inventory replacement request org=%s old_mac=%s", self._org_id, request.mac)  # WHY.
        response = mistapi.api.v1.orgs.inventory.replaceOrgDevices(self._apisession, self._org_id, body)
        data = (
            response.data if isinstance(response.data, dict) else {"status_code": response.status_code}
        )  # WHY: stable.
        logger.debug("Mist replacement request returned status=%s", response.status_code)  # WHY: result summary.
        return dict(data)  # WHY: operation layer records the result message.
