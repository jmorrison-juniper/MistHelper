"""Organization inventory search export for ``searchOrgInventory``.

The endpoint is read-only and returns paginated device rows. This module keeps
the prompts, SDK call, pagination, and standard output selection together so
menu 248 behaves like the other search exports.
"""

from __future__ import annotations

import logging
from typing import Any

import mistapi

from src.foundation.models.data.data_processing_utils import DataProcessingUtils
from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.

_OPERATION = "searchOrgInventory"
_PREFIX = "OrgInventorySearch"
_FILTERS = (
    ("type", "Inventory type (ap, gateway, switch)", "org_inventory_search.type"),
    ("mac", "MAC address or wildcard", "org_inventory_search.mac"),
    ("model", "Device model or wildcard", "org_inventory_search.model"),
    ("name", "Device name", "org_inventory_search.name"),
    ("site_id", "Site ID", "org_inventory_search.site_id"),
    ("serial", "Serial number or wildcard", "org_inventory_search.serial"),
    ("master", "Virtual Chassis master filter", "org_inventory_search.master"),
    ("sku", "Device SKU or wildcard", "org_inventory_search.sku"),
    ("version", "Device version or wildcard", "org_inventory_search.version"),
    ("status", "Device status (connected, disconnected)", "org_inventory_search.status"),
    ("text", "Text search for name, MAC, or serial", "org_inventory_search.text"),
    ("limit", "Maximum results per page", "org_inventory_search.limit"),
    ("sort", "Sort field", "org_inventory_search.sort"),
    ("search_after", "Pagination cursor", "org_inventory_search.search_after"),
)


class OrgInventorySearchExporter:
    """Prompt for filters and export organization inventory search results."""

    @staticmethod
    def _prompt_filters(mh: Any) -> dict[str, Any]:
        """Collect optional SDK query parameters with EOF-safe prompts."""
        filters: dict[str, Any] = {}
        for field, label, context in _FILTERS:
            value = mh.InputUtils.safe_input(f"{label} (optional): ", context=context)
            if value:
                filters[field] = int(value) if field == "limit" else value
        logger.debug("Collected %d searchOrgInventory filter(s)", len(filters))
        return filters

    @staticmethod
    def _persist(rows: list[Any], org_id: str, mh: Any) -> None:
        """Flatten and write rows through the configured output backend."""
        if not rows:  # A validated successful request can have no matching inventory.
            logger.info("! No organization inventory search data found")  # Keep the normal empty-result message.
            return  # Do not create output for an empty search.
        logger.info("Preparing %d %s row(s) for export", len(rows), _OPERATION)  # Identify the data transform.
        flattened = DataProcessingUtils.flatten_nested_fields(rows)  # Keep the configured output row shape.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # Keep multiline fields safe for output.
        logger.debug("%s prepared %d row(s)", _OPERATION, len(sanitized))  # Record the transform result.
        filename = f"{_PREFIX}_{org_id}.csv"  # Preserve the established output name.
        logger.info("Writing %s output to %s", _OPERATION, filename)  # Identify the attempted output.
        success = mh.DataExporter.write_with_format_selection(  # Read the writer result before claiming success.
            sanitized, filename, api_function_name=_OPERATION
        )
        if not success:  # The writer can report failure without raising an exception.
            logger.error("%s export failed for org_id=%s: writer returned False for %s", _OPERATION, org_id, filename)
            return  # Do not claim persistence or export success after a failed write.
        logger.debug("%s persisted %d rows to %s", _OPERATION, len(rows), filename)  # Confirm successful output only.
        logger.info(
            "! %d organization inventory search record(s) exported to %s", len(rows), filename
        )  # Confirm output.

    @staticmethod
    def _validate_response(response: Any) -> None:
        """Reject failed initial responses before the SDK can treat them as empty."""
        status_code = getattr(response, "status_code", None)  # Native transport failures have no HTTP status.
        if isinstance(status_code, bool) or not isinstance(
            status_code, int
        ):  # Reject malformed statuses without data logs.
            raise RuntimeError(
                f"{_OPERATION} request failed: missing or invalid initial HTTP status"
            )  # Retain error handling.
        if not 200 <= status_code < 300:  # Reject every integer outside the HTTP success range.
            raise RuntimeError(f"{_OPERATION} request failed: initial HTTP status {status_code}")  # Report the status.

    @staticmethod
    def inventory() -> None:
        """Search organization inventory and export the result (menu 248)."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Organization Inventory Search:")
        logger.info("Starting the %s export...", _OPERATION)
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()
        if not org_id:
            logger.info("! No organization selected. Exiting.")
            return
        try:
            filters = OrgInventorySearchExporter._prompt_filters(mh)
            logger.info("Calling %s for org_id=%s", _OPERATION, org_id)
            response = mistapi.api.v1.orgs.inventory.searchOrgInventory(mh.apisession, org_id, **filters)
            OrgInventorySearchExporter._validate_response(response)  # Check the initial request before pagination.
            rows = mistapi.get_all(response=response, mist_session=mh.apisession)
            logger.debug("%s returned %d row(s)", _OPERATION, len(rows))
            OrgInventorySearchExporter._persist(rows, org_id, mh)
        except Exception as error:
            logging.error("Error fetching organization inventory search for %s: %s", org_id, error)
            logging.info("! Error fetching organization inventory search data: %s", error)
