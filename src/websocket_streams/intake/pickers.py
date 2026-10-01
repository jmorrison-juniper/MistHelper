"""Picker lists for the WebSockets page.

Why:
    Issue #3551. The WebSockets page must fill each identifier from Mist data.
    The service returns small, safe rows and never sends a raw channel path.
"""

from __future__ import annotations  # Keep annotations lazy for the portal import path.

import logging  # Use the project logging system for picker visibility.
import time  # Age the device cache with a monotonic clock.
from typing import cast  # Check SDK data before the page receives it.

from src.websocket_streams.intake.start_request import DeviceFacts  # Share the checker device shape.

logger = logging.getLogger(__name__)  # Keep picker records under this module name.


class StreamPickerService:
    """Build picker answers for the WebSockets start form."""

    def __init__(self, apisession: object, org_id: str) -> None:
        """Store the Mist session and the organization identifier.

        Args:
            apisession: The Mist SDK session object.
            org_id: The Mist organization identifier.
        """
        self._apisession = apisession  # The SDK needs this object for every read.
        self._org_id = org_id  # Mist Edge reads can use the organization scope.
        self._device_cache: dict[str, tuple[float, list[dict[str, object]]]] = {}  # Reuse site devices briefly.

    def devices(self, site_id: str) -> dict[str, object]:
        """Return the devices of one site.

        Args:
            site_id: The site identifier.

        Returns:
            The picker payload with device rows.
        """
        logger.info("Listing WebSocket devices for site %s", site_id)  # Log before the SDK read.
        rows = self._cached_devices(site_id)  # Use the shared cache for picker and start checks.
        logger.debug("Listed %d WebSocket devices for site %s", len(rows), site_id)  # Log the row count.
        return self._payload(rows, "The site has no devices that the portal can list.")  # Explain an empty list.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return the maps of one site.

        Args:
            site_id: The site identifier.

        Returns:
            The picker payload with map rows.
        """
        return self._simple_site_picker(site_id, "maps", "listSiteMaps", "The site has no maps.")  # Read maps.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return the BLE assets of one site.

        Args:
            site_id: The site identifier.

        Returns:
            The picker payload with asset rows.
        """
        return self._simple_site_picker(site_id, "assets", "listSiteAssets", "The site has no assets.")  # Read assets.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return the SDK clients of one map.

        Args:
            site_id: The site identifier.
            map_id: The map identifier.

        Returns:
            The picker payload with SDK client rows.
        """
        logger.info("Listing WebSocket SDK clients for site %s", site_id)  # Log before the SDK read.
        try:  # A picker must answer with a reason instead of raising.
            import mistapi  # Import here so unit tests can patch the installed SDK.

            response = mistapi.api.v1.sites.stats.getSiteSdkStatsByMap(
                self._apisession, site_id, map_id
            )  # Read clients.
            records = self._records(response)  # Normalize the SDK answer.
            rows = [
                self._row(record, ("name", "hostname", "mac"), ("mac", "status"), None) for record in records
            ]  # Rows.
            logger.debug("Listed %d WebSocket SDK clients for site %s", len(rows), site_id)  # Log the row count.
            return self._payload(rows, "The map has no SDK clients.")  # Explain an empty list.
        except Exception as error:  # Keep the form usable when Mist refuses the read.
            logger.exception(
                "Failed to list WebSocket SDK clients for site %s with %s", site_id, type(error).__name__
            )  # Log.
            return self._payload([], "The portal could not list SDK clients from Mist.")  # Tell the operator.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return the Mist Edges of the organization or one site.

        Args:
            site_id: The optional site identifier.

        Returns:
            The picker payload with Mist Edge rows.
        """
        logger.info("Listing WebSocket Mist Edges for site %s", site_id or "organization")  # Log before the SDK read.
        try:  # A picker must answer with a reason instead of raising.
            records = self._mxedge_records(site_id)  # Read the requested Mist Edge scope.
            rows = [self._row(record, ("name", "id"), ("model", "status"), "mxedge") for record in records]  # Rows.
            logger.debug("Listed %d WebSocket Mist Edges", len(rows))  # Log the row count.
            return self._payload(rows, "No Mist Edge matches this scope.")  # Explain an empty list.
        except Exception as error:  # Keep the form usable when Mist refuses the read.
            logger.exception(
                "Failed to list WebSocket Mist Edges with %s", type(error).__name__
            )  # Log the failure class.
            return self._payload([], "The portal could not list Mist Edges from Mist.")  # Tell the operator.

    def describe_device(self, site_id: str, device_id: str) -> DeviceFacts | None:
        """Return the family facts for one device.

        Args:
            site_id: The site identifier.
            device_id: The device identifier.

        Returns:
            The device facts, or None when the device is absent.
        """
        logger.info("Looking up WebSocket device facts for site %s", site_id)  # Log before the cached read.
        rows = self._cached_devices(site_id)  # Reuse the picker read for 30 seconds.
        match = next((row for row in rows if row.get("id") == device_id), None)  # Find the chosen device.
        logger.debug("WebSocket device facts found: %s", match is not None)  # Log only the boolean result.
        if match is None:  # The device is not in the current site list.
            return None  # The start checker turns this into a bad request.
        return DeviceFacts(name=str(match.get("label") or ""), family=cast(str | None, match.get("family")))  # Facts.

    def _simple_site_picker(
        self, site_id: str, family: str, function_name: str, empty_reason: str
    ) -> dict[str, object]:
        """Return a simple picker that reads a site SDK list."""
        logger.info("Listing WebSocket %s for site %s", family, site_id)  # Log before the SDK read.
        try:  # A picker must answer with a reason instead of raising.
            import mistapi  # Import here so tests can patch the installed SDK.

            namespace = getattr(mistapi.api.v1.sites, family)  # Select the SDK group by picker family.
            function = getattr(namespace, function_name)  # Select the SDK read function.
            response = function(self._apisession, site_id)  # Read the site list from Mist.
            rows = [
                self._row(record, ("name", "id"), ("type", "status"), None) for record in self._records(response)
            ]  # Rows.
            logger.debug("Listed %d WebSocket %s for site %s", len(rows), family, site_id)  # Log row count.
            return self._payload(rows, empty_reason)  # Return the common payload.
        except Exception as error:  # Keep the form usable when Mist refuses the read.
            logger.exception(
                "Failed to list WebSocket %s for site %s with %s", family, site_id, type(error).__name__
            )  # Log.
            return self._payload([], "The portal could not list this data from Mist.")  # Tell the operator.

    def _cached_devices(self, site_id: str) -> list[dict[str, object]]:
        """Return fresh device rows from cache or Mist."""
        now = time.monotonic()  # Use monotonic time so clock changes do not break the cache.
        cached = self._device_cache.get(site_id)  # Read the current cache entry.
        if cached and now - cached[0] <= 30.0:  # A 30-second cache protects repeat starts.
            logger.debug("Reused %d cached WebSocket devices for site %s", len(cached[1]), site_id)  # Log reuse.
            return [dict(row) for row in cached[1]]  # Return a copy so callers cannot change the cache.
        rows = self._fetch_devices(site_id)  # Read Mist when the cache is absent or old.
        if rows:  # Empty answers can be transient failures.
            self._device_cache[site_id] = (now, [dict(row) for row in rows])  # Keep a defensive copy.
        return rows  # Return the fresh rows.

    def _fetch_devices(self, site_id: str) -> list[dict[str, object]]:
        """Read device rows from Mist."""
        try:  # A picker must answer with a reason instead of raising.
            import mistapi  # Import here so tests can patch the installed SDK.

            response = mistapi.api.v1.sites.devices.listSiteDevices(
                self._apisession, site_id=site_id, type="all"
            )  # Read all.
            rows = [self._device_row(record) for record in self._records(response)]  # Convert each device.
            logger.debug("Fetched %d WebSocket devices from Mist for site %s", len(rows), site_id)  # Log row count.
            return rows  # Return the normalized rows.
        except Exception as error:  # Keep the form usable when Mist refuses the read.
            logger.exception(
                "Failed to list WebSocket devices for site %s with %s", site_id, type(error).__name__
            )  # Log.
            return []  # The public method adds the plain reason.

    def _mxedge_records(self, site_id: str | None) -> list[dict[str, object]]:
        """Read Mist Edge records from the selected SDK scope."""
        import mistapi  # Import here so tests can patch the installed SDK.

        if site_id:  # A site selection narrows the list.
            response = mistapi.api.v1.sites.mxedges.listSiteMxEdges(self._apisession, site_id)  # Read site Mist Edges.
        else:  # No site means organization scope.
            response = mistapi.api.v1.orgs.mxedges.listOrgMxEdges(
                self._apisession, self._org_id
            )  # Read org Mist Edges.
        return self._records(response)  # Normalize the SDK answer.

    def _device_row(self, record: dict[str, object]) -> dict[str, object]:
        """Return one device row for the page."""
        family = self._device_family(record)  # The page filters utilities by this value.
        return self._row(record, ("name", "mac", "id"), ("model", "type"), family)  # Use name or MAC as label.

    def _device_family(self, record: dict[str, object]) -> str | None:
        """Return the utility family of one device record."""
        device_type = str(record.get("type") or "").casefold()  # Mist sends ap, switch, or gateway.
        model = str(record.get("model") or "").casefold()  # Gateways need the model split.
        if device_type == "ap":  # Access points use the AP utility group.
            return "ap"  # The catalog family key.
        if device_type == "switch":  # Switches use the EX utility group.
            return "ex"  # The catalog family key.
        if device_type == "gateway" and "srx" in model:  # SRX gateways use SRX utilities.
            return "srx"  # The catalog family key.
        if device_type == "gateway":  # Other gateways use SSR utilities.
            return "ssr"  # The catalog family key.
        return None  # Unknown types have no utility list.

    def _row(
        self,
        record: dict[str, object],
        label_fields: tuple[str, ...],
        detail_fields: tuple[str, ...],
        family: str | None,
    ) -> dict[str, object]:
        """Return one picker row."""
        identifier = str(record.get("id") or record.get("mac") or "")  # Pickers need a stable value.
        label = self._first_text(record, label_fields) or identifier  # Operators read names first.
        detail = self._first_text(record, detail_fields)  # Detail helps identify similar names.
        return {"id": identifier, "label": label, "family": family, "detail": detail}  # Contract row shape.

    def _first_text(self, record: dict[str, object], fields: tuple[str, ...]) -> str:
        """Return the first non-empty text value from one record."""
        for field in fields:  # Search the preferred display fields in order.
            value = str(record.get(field) or "").strip()  # Normalize a missing value to empty text.
            if value:  # The first useful value wins.
                return value  # Return the display text.
        return ""  # No field held display text.

    def _records(self, response: object) -> list[dict[str, object]]:
        """Return dictionary records from an SDK answer."""
        data = getattr(response, "data", [])  # The Mist SDK stores rows on the data attribute.
        if isinstance(data, dict):  # Some stats answers wrap rows inside one object.
            data = data.get("results") or data.get("items") or data.get("sdkclients") or []  # Common list keys.
        if not isinstance(data, list):  # A non-list answer cannot fill a picker.
            return []  # Refuse the unknown shape safely.
        return [dict(item) for item in data if isinstance(item, dict)]  # Keep only mapping rows.

    def _payload(self, rows: list[dict[str, object]], empty_reason: str) -> dict[str, object]:
        """Return the common picker payload."""
        rows.sort(key=lambda row: str(row.get("label") or "").casefold())  # Keep lists stable for operators.
        reason = None if rows else empty_reason  # Give a reason only when the list is blank.
        return {"rows": rows, "total_count": len(rows), "reason": reason}  # Contract payload shape.
