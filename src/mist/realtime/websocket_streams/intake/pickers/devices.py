"""Device picker behavior and its short cache."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.
import time  # Cache age uses a monotonic clock.
from typing import cast  # Device family data is checked before record construction.

from src.mist.realtime.websocket_streams.intake.identifiers.identity_rules import (
    IdentityIdentifierRules,
)  # Validate device MACs before they scope a client read.
from src.mist.realtime.websocket_streams.intake.pickers.records import PickerRuntime  # Shared state and row shaping.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    DeviceFacts,
)  # Device checks share this immutable record.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep picker logs bounded and identifier-free.


class DevicePicker(PickerRuntime):
    """List devices and describe one cached device."""

    def devices(self, site_id: str) -> dict[str, object]:
        """Return device rows for one site."""
        logger.emit(logging.INFO, "intake_device_picker_started", {"action": "list"})  # Log no site identifier.
        rows = self._public_device_rows(site_id)  # Keep server-only scope data out of the JSON answer.
        logger.emit(logging.DEBUG, "intake_device_picker_finished", {"count": len(rows)})  # Log the bounded count.
        return self._payload(rows, "The site has no devices that the portal can list.")  # Explain an empty list.

    def device_mac(self, site_id: str, device_id: str) -> str | None:
        """Return a validated MAC for a device cached under the selected site."""
        match = next(
            (row for row in self._cached_devices(site_id) if row.get("id") == device_id), None
        )  # Find only a device returned for this site.
        value = match.get("_device_mac") if match is not None else None  # Read the private association field.
        if not IdentityIdentifierRules.is_mac(value):
            return None  # Do not scope a read with malformed device identity.
        return IdentityIdentifierRules.normalize_mac(str(value))  # Use the SDK's compact MAC form.

    def describe_device(self, site_id: str, device_id: str) -> DeviceFacts | None:
        """Return the family facts for one selected device."""
        logger.emit(logging.INFO, "intake_device_lookup_started", {"action": "cache_read"})  # Log no identifiers.
        match = next(
            (row for row in self._cached_devices(site_id) if row.get("id") == device_id), None
        )  # Find selection.
        logger.emit(
            logging.DEBUG, "intake_device_lookup_finished", {"status": match is not None}
        )  # Log the result only.
        if match is None:  # The selected device is absent from the current site list.
            return None  # The request checker converts absence to a contract error.
        return DeviceFacts(str(match.get("label") or ""), cast(str | None, match.get("family")))  # Return safe facts.

    def _cached_devices(self, site_id: str) -> list[dict[str, object]]:
        """Return fresh copied device rows."""
        now = time.monotonic()  # Wall-clock changes cannot invalidate cache age.
        cached = self._device_cache.get(site_id)  # Read the current site entry.
        if cached and now - cached[0] <= 30.0:  # Reuse rows for the required 30-second interval.
            return [dict(row) for row in cached[1]]  # Protect cached rows from caller mutation.
        rows = self._fetch_devices(site_id)  # Read Mist after cache absence or expiry.
        if rows:  # Empty answers can be transient failures.
            self._device_cache[site_id] = (now, [dict(row) for row in rows])  # Store a defensive copy.
        return rows  # Return fresh normalized rows.

    def _fetch_devices(self, site_id: str) -> list[dict[str, object]]:
        """Read and normalize device rows from Mist."""
        try:
            import mistapi  # Import here so focused tests can replace the SDK seam.

            response = mistapi.api.v1.sites.devices.listSiteDevices(
                self._apisession, site_id=site_id, type="all"
            )  # Request every device type.
            rows = [self._device_row(record) for record in self._records(response)]  # Normalize each SDK row.
            logger.emit(logging.DEBUG, "intake_device_fetch_finished", {"count": len(rows)})  # Log no row content.
            return rows  # Return the complete normalized result.
        except Exception as error:
            logger.emit(logging.ERROR, "intake_device_fetch_failed", {"detail": type(error).__name__})  # Log safe type.
            return []  # The public payload supplies the operator reason.

    def _public_device_rows(self, site_id: str) -> list[dict[str, object]]:
        """Remove private association data before returning device options."""
        return [
            {key: value for key, value in row.items() if key != "_device_mac"} for row in self._cached_devices(site_id)
        ]  # Keep the response contract unchanged.

    def _device_row(self, record: dict[str, object]) -> dict[str, object]:
        """Return one normalized device row."""
        family = self._device_family(record)  # Utility filtering needs the family.
        row = self._row(record, ("name", "mac", "id"), ("model", "type"), family)  # Prefer names for operators.
        device_mac = record.get("mac")  # Keep the SDK device MAC for a verified lookup.
        row["_device_mac"] = device_mac if IdentityIdentifierRules.is_mac(device_mac) else None  # Keep it server-side.
        return row  # Preserve the validated device scope for later picker actions.
