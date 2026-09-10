"""Organization inventory search export for ``searchOrgInventory``.

The endpoint is read-only and returns paginated device rows. This module keeps
the prompts, SDK call, pagination, and standard output selection together so
menu 248 behaves like the other search exports.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

import mistapi

from src.data.data_processing_utils import DataProcessingUtils

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
        logging.debug("Collected %d searchOrgInventory filter(s)", len(filters))
        return filters

    @staticmethod
    def _persist(rows: list[Any], org_id: str, mh: Any) -> None:
        """Flatten and write rows through the configured output backend."""
        if not rows:
            logging.info("! No organization inventory search data found")
            return
        flattened = DataProcessingUtils.flatten_nested_fields(rows)
        sanitized = DataProcessingUtils.escape_multiline(flattened)
        filename = f"{_PREFIX}_{org_id}.csv"
        mh.DataExporter.write_with_format_selection(sanitized, filename, api_function_name=_OPERATION)
        logging.debug("%s persisted %d rows to %s", _OPERATION, len(rows), filename)
        logging.info("! %d organization inventory search record(s) exported to %s", len(rows), filename)

    @staticmethod
    def inventory() -> None:
        """Search organization inventory and export the result (menu 248)."""
        mh = importlib.import_module("MistHelper")
        logging.info("Organization Inventory Search:")
        logging.info("Starting the %s export...", _OPERATION)
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()
        if not org_id:
            logging.info("! No organization selected. Exiting.")
            return
        try:
            filters = OrgInventorySearchExporter._prompt_filters(mh)
            logging.info("Calling %s for org_id=%s", _OPERATION, org_id)
            response = mistapi.api.v1.orgs.inventory.searchOrgInventory(mh.apisession, org_id, **filters)
            rows = mistapi.get_all(response=response, mist_session=mh.apisession)
            logging.debug("%s returned %d row(s)", _OPERATION, len(rows))
            OrgInventorySearchExporter._persist(rows, org_id, mh)
        except Exception as error:
            logging.error("Error fetching organization inventory search for %s: %s", org_id, error)
            logging.info("! Error fetching organization inventory search data: %s", error)
