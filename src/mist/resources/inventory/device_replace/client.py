"""Mist API client for the RMA device replacement operation."""

from __future__ import annotations  # WHY: keep annotations lightweight during import.

import logging  # WHY: log before and after every Mist API call.
from typing import Any  # WHY: mistapi responses are dynamically typed.

import mistapi  # WHY: use the installed SDK operations verified in research.md.

from src.mist.resources.inventory.device_replace.models import (
    InventoryDevice,
    ReplaceRequest,
)  # WHY: client returns typed records.

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
        self._raise_for_status(response, "getOrgInventory")  # WHY: a failed inventory read must stop the workflow.
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
        self._raise_for_status(response, "getSiteDevice")  # WHY: a failed backup read must stop replacement.
        data = response.data if isinstance(response.data, dict) else {}  # WHY: backup JSON must be an object.
        logger.debug("Read old device configuration keys=%d", len(data))  # WHY: result summary without secrets.
        return dict(data)  # WHY: persistence should own an independent copy.

    def replace_device(self, request: ReplaceRequest) -> dict[str, Any]:
        """Send the replacement request to Mist."""
        body = request.as_body()  # WHY: construct the OpenAPI payload once for logging and send.
        logger.info("Sending Mist inventory replacement request org=%s old_mac=%s", self._org_id, request.mac)  # WHY.
        response = mistapi.api.v1.orgs.inventory.replaceOrgDevices(self._apisession, self._org_id, body)
        self._raise_for_status(response, "replaceOrgDevices")  # WHY: rejected replacement requests need clear errors.
        data = (
            response.data if isinstance(response.data, dict) else {"status_code": response.status_code}
        )  # WHY: stable.
        logger.debug("Mist replacement request returned status=%s", response.status_code)  # WHY: result summary.
        return dict(data)  # WHY: operation layer records the result message.

    @staticmethod
    def _raise_for_status(response: Any, operation_name: str) -> None:
        """Raise a clear error when Mist returns a failed HTTP status."""
        status_code = int(getattr(response, "status_code", 0) or 0)  # WHY: missing status values are unsafe.
        if 200 <= status_code < 300:  # WHY: only successful HTTP responses can continue.
            return  # WHY: caller can process the response body.
        data = getattr(response, "data", {})  # WHY: Mist often returns the reason in the JSON body.
        message = DeviceReplaceClient._error_message(data)  # WHY: keep error extraction small and testable.
        logger.error("%s returned HTTP %s: %s", operation_name, status_code, message)  # WHY: action failure log.
        raise RuntimeError(f"{operation_name} returned HTTP {status_code}: {message}")  # WHY: caller logs the result.

    @staticmethod
    def _error_message(data: Any) -> str:
        """Return a short error message from a Mist response body."""
        if isinstance(data, dict):  # WHY: Mist error bodies are usually JSON objects.
            value = data.get("message") or data.get("error") or data.get("detail")  # WHY: common error fields.
            return str(value or "Mist API request failed.")  # WHY: empty bodies still need a useful reason.
        return "Mist API request failed."  # WHY: non-object bodies must not leak raw content.
