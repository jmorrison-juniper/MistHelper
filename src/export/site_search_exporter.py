"""SiteSearchExporter -- site-scoped search export operations.

Added for specs 879, 880, 881, 882 and 897 (issues #1387, #1388, #1389, #1390
and #1405), then extended for specs 903, 900, 884, 886 and 895 (issues #1411,
#1408, #1392, #1394 and #1403). Wraps read-only Mist API search endpoints so
operators reach them through the standard MistHelper menu and DataExporter
pipeline (CSV, SQLite, or ArangoDB).

Covered operations:
    - ``searchSiteAlarms`` (menu 215)
    - ``searchSiteAssets`` (menu 216)
    - ``searchSiteBgpStats`` (menu 217)
    - ``searchSiteCalls`` (menu 218)
    - ``searchSiteSkyatpEvents`` (menu 219)
    - ``searchSiteWirelessClientEvents`` (menu 220)
    - ``searchSiteWanClients`` (menu 221)
    - ``searchSiteDeviceEvents`` (menu 222)
    - ``searchSiteDevices`` (menu 223)
    - ``searchSiteRogueEvents`` (menu 224)

Why:
    All of these endpoints take the same arguments, a session and a site, and
    return a paginated row set. One shared helper therefore runs the whole
    prompt, fetch, and persist sequence, and each menu entry supplies only the
    parts that differ. That keeps the operations consistent and avoids one copy
    of the same code per endpoint.

Warning: the ``**mistapi SDK module**`` line in the source specs is wrong for
several of these operations. See issue #1757. Every module path below was
resolved against the installed SDK.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from collections.abc import Callable  # WHY: the per-operation SDK callable is injected.
from typing import Any

import mistapi  # WHY: direct SDK access for the five search endpoints and get_all pagination.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.


class SiteSearchExporter:
    """Site-scoped search exporter.

    Why:
        Provides the only MistHelper entry points for the search operationIds
        listed above. Static methods only, with no per-instance state, matching
        the peer site exporters.
    """

    @staticmethod
    def _persist(rawdata: list[Any], site_name: str, prefix: str, operation: str, label: str) -> None:
        """Flatten and persist search rows, or tell the operator when there are none.

        Why:
            An empty result is legitimate when the site logged nothing in the
            query window, so we report it plainly instead of failing.

        Args:
            rawdata: The raw rows returned by the search. May be empty.
            site_name: The human-readable site name used to name the output file.
            prefix: The filename prefix that identifies the operation.
            operation: The operationId used to route the primary-key strategy.
            label: A human-readable noun used in the operator messages.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rawdata:  # No rows, so inform the operator and return.
            logging.info("! No %s data found for this site", label)  # ASCII-only user notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Make multiline values CSV-safe.
        filename = f"{prefix}_{site_name.replace(' ', '_')}.csv"  # Per-site filename.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name=operation
        )
        logging.debug("%s persisted %d rows to %s", operation, len(rawdata), filename)  # Post-call count trace.
        logging.info("! %d %s records exported to %s", len(rawdata), label, filename)  # User notice with count.

    @staticmethod
    def _run_site_search(
        api_call: Callable[..., Any],
        operation: str,
        prefix: str,
        label: str,
    ) -> None:
        """Run the shared prompt, fetch, and persist sequence for one search endpoint.

        Why:
            The five endpoints differ only in the SDK callable and the naming, so
            one helper keeps their behavior identical. Errors are logged and
            surfaced to the operator rather than crashing the menu loop.

        Args:
            api_call: The SDK function to invoke with the session and the site.
            operation: The operationId used to route the primary-key strategy.
            prefix: The filename prefix that identifies the operation.
            label: A human-readable noun used in the operator messages.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Site %s Search:", label.title())  # Menu header echoed to the operator.
        logging.info("Starting the %s export...", operation)  # Pre-call trace.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(f"{label} search")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the shared helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        try:
            logging.info("Calling %s for site_id=%s (%s)", operation, site_id, site_name)  # Pre-call log.
            response = api_call(mh.apisession, site_id)  # SDK call with default filters.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            SiteSearchExporter._persist(rawdata, site_name, prefix, operation, label)  # Persist or report empty.
        except Exception as e:  # noqa: BLE001 -- surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching %s for site %s: %s", label, site_name, e)  # Failure context.
            logging.info("! Error fetching %s data: %s", label, e)  # ASCII-only user notice.

    @staticmethod
    def alarms() -> None:
        """Search the alarms for a site and export them (menu 215)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.alarms.searchSiteAlarms,
            "searchSiteAlarms",
            "SiteAlarms",
            "alarm",
        )

    @staticmethod
    def assets() -> None:
        """Search the tracked assets for a site and export them (menu 216)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.stats.searchSiteAssets,
            "searchSiteAssets",
            "SiteAssets",
            "asset",
        )

    @staticmethod
    def bgp_stats() -> None:
        """Search the BGP peer statistics for a site and export them (menu 217)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.stats.searchSiteBgpStats,
            "searchSiteBgpStats",
            "SiteBgpStats",
            "BGP stat",
        )

    @staticmethod
    def calls() -> None:
        """Search the call quality records for a site and export them (menu 218)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.stats.searchSiteCalls,
            "searchSiteCalls",
            "SiteCalls",
            "call",
        )

    @staticmethod
    def skyatp_events() -> None:
        """Search the Sky ATP security events for a site and export them (menu 219)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.skyatp.searchSiteSkyatpEvents,
            "searchSiteSkyatpEvents",
            "SiteSkyatpEvents",
            "Sky ATP event",
        )

    @staticmethod
    def wireless_client_events() -> None:
        """Search the wireless client events for a site and export them (menu 220)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.clients.searchSiteWirelessClientEvents,
            "searchSiteWirelessClientEvents",
            "SiteWirelessClientEvents",
            "wireless client event",
        )

    @staticmethod
    def wan_clients() -> None:
        """Search the WAN clients for a site and export them (menu 221)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.wan_clients.searchSiteWanClients,
            "searchSiteWanClients",
            "SiteWanClients",
            "WAN client",
        )

    @staticmethod
    def device_events() -> None:
        """Search the device events for a site and export them (menu 222)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.devices.searchSiteDeviceEvents,
            "searchSiteDeviceEvents",
            "SiteDeviceEvents",
            "device event",
        )

    @staticmethod
    def devices() -> None:
        """Search the devices for a site and export them (menu 223)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.devices.searchSiteDevices,
            "searchSiteDevices",
            "SiteDevices",
            "device",
        )

    @staticmethod
    def rogue_events() -> None:
        """Search the rogue access point events for a site and export them (menu 224)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.rogues.searchSiteRogueEvents,
            "searchSiteRogueEvents",
            "SiteRogueEvents",
            "rogue event",
        )
