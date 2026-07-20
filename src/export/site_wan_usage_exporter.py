"""SiteWanUsageExporter -- site-level WAN usage search export.

Added for spec 901 / issue #1409.  Wraps the Mist API
``searchSiteWanUsage`` (``GET /api/v1/sites/{site_id}/wan_usages/search``)
so operators can retrieve per-site WAN usage records through the standard
MistHelper menu + DataExporter pipeline (CSV/SQLite/ArangoDB).

Why:
    The endpoint was absent from MistHelper's menu, forcing users to write
    custom code to reach WAN usage records.  This exporter closes that gap
    while reusing the shared site-resolution + persistence scaffolding
    established by ``SiteClientExporter.clients()`` and
    ``SiteDeviceExporter._resolve_site_for_stats()``.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw WAN usage rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for searchSiteWanUsage + get_all pagination.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten/escape helpers; keeps CSV output consistent with peers.


class SiteWanUsageExporter:
    """Site WAN Usage search exporter.

    Why:
        Provides the sole MistHelper entry point for the
        ``searchSiteWanUsage`` operationId.  Static methods only -- no
        per-instance state, matching the pattern used by
        ``SiteClientExporter`` / ``SiteDeviceExporter``.
    """

    @staticmethod
    def _persist_site_wan_usages(rawdata: list[Any], site_name: str) -> None:
        """Flatten + persist WAN usage rows to a per-site file (or tell the user when empty).

        Why:
            Empty responses are legitimate (a site with no WAN telemetry in
            the query window); we surface a friendly message rather than
            failing so scheduled runs stay quiet in that case.

        Args:
            rawdata: Raw list returned by ``mistapi.get_all`` for the WAN
                usage search response.  May be empty.
            site_name: Human-readable site name used to name the output
                file (falls back to site_id when name lookup failed).
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        if not rawdata:  # No WAN usage rows for this site -- inform the operator and return.
            # WHY: ASCII-only user notice.
            logging.info("! No WAN usage data found for this site")
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe multiline escape.
        filename = f"SiteWanUsages_{site_name.replace(' ', '_')}.csv"  # Per-site filename, spaces to underscores.
        mh.DataExporter.write_with_format_selection(  # Persist through CSV/SQLite/Arango backend selector.
            sanitized_data, filename, api_function_name="searchSiteWanUsage"
        )
        logging.debug(  # DEBUG-level count trace per Action Logging principle (post-call).
            "searchSiteWanUsage persisted %d rows to %s", len(rawdata), filename
        )
        # WHY: user notice with count.
        logging.info("! %d WAN usage records exported to %s", len(rawdata), filename)

    @staticmethod
    def wan_usages() -> None:
        """Search WAN usages for a site and export to SiteWanUsages.csv.

        Why:
            Interactive menu entry point (menu 198).  Delegates site
            resolution to the shared helper so behavior stays consistent
            with peer site-scoped exports.  Errors are logged and surfaced
            to the user rather than crashing the menu loop.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + shared helpers.
        # WHY: menu header echoed to operator.
        logging.info("Site WAN Usage Search:")
        logging.info(  # INFO trace before the API call per Action Logging principle (pre-call).
            "Starting searchSiteWanUsage export..."
        )
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(  # Prompt + org/site resolution (shared).
            "WAN usage search"
        )
        if resolved is None:  # Operator declined selection or org unresolved -- shared helper already logged.
            return
        site_id, site_name = resolved  # Unpack resolved identifiers for the API call.
        try:
            logging.info(  # INFO trace immediately before the SDK call (with site context).
                "Calling searchSiteWanUsage for site_id=%s (%s)", site_id, site_name
            )
            response = mistapi.api.v1.sites.wan_usages.searchSiteWanUsage(  # SDK call -- defaults for filters.
                mh.apisession, site_id
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            SiteWanUsageExporter._persist_site_wan_usages(rawdata, site_name)  # Persist or notify empty.
        except Exception as e:  # noqa: BLE001 -- surface any SDK/network error to the user instead of crashing.
            logging.error(  # ERROR trace with site context for post-mortem correlation.
                "Error fetching WAN usage for site %s: %s", site_name, e
            )
            # WHY: ASCII-only user notice.
            logging.info("! Error fetching WAN usage data: %s", e)
