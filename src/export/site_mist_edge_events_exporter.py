"""SiteMistEdgeEventsExporter -- site-level Mist Edge event search export.

Added for spec 890 / issue #1398.  Wraps the Mist API
``searchSiteMistEdgeEvents`` (``GET /api/v1/sites/{site_id}/mxedges/events/search``)
so operators can retrieve per-site Mist Edge event records through the
standard MistHelper menu + DataExporter pipeline (CSV/SQLite/ArangoDB).

Why:
    The endpoint was absent from MistHelper's menu, forcing users to write
    custom code to reach Mist Edge event history.  This exporter closes
    that gap while reusing the shared site-resolution + persistence
    scaffolding established by ``SiteGuestAuthorizationExporter`` and
    ``SiteDeviceExporter._resolve_site_for_stats()``.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw event rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for searchSiteMistEdgeEvents + get_all pagination.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten/escape helpers. Keeps CSV output consistent with peers.


class SiteMistEdgeEventsExporter:
    """Site Mist Edge Events search exporter.

    Why:
        Provides the sole MistHelper entry point for the
        ``searchSiteMistEdgeEvents`` operationId.  Static methods only --
        no per-instance state, matching the pattern used by
        ``SiteGuestAuthorizationExporter`` / ``SiteDeviceExporter``.
    """

    @staticmethod
    def _persist_site_mist_edge_events(rawdata: list[Any], site_name: str) -> None:
        """Flatten + persist Mist Edge event rows to a per-site file (or tell the user when empty).

        Why:
            Empty responses are legitimate (a site with no Mist Edge events
            in the query window). We surface a friendly message rather than
            failing so scheduled runs stay quiet in that case.

        Args:
            rawdata: Raw list returned by ``mistapi.get_all`` for the Mist Edge
                events search response.  May be empty.
            site_name: Human-readable site name used to name the output
                file (falls back to site_id when name lookup failed).
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        if not rawdata:  # No Mist Edge event rows for this site -- inform the operator and return.
            # WHY: ASCII-only user notice.
            logging.info("! No Mist Edge event data found for this site")
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe multiline escape.
        filename = f"SiteMistEdgeEvents_{site_name.replace(' ', '_')}.csv"  # Per-site filename.
        mh.DataExporter.write_with_format_selection(  # Persist through CSV/SQLite/Arango backend selector.
            sanitized_data, filename, api_function_name="searchSiteMistEdgeEvents"
        )
        logging.debug(  # DEBUG-level count trace per Action Logging principle (post-call).
            "searchSiteMistEdgeEvents persisted %d rows to %s", len(rawdata), filename
        )
        # WHY: user notice with count.
        logging.info("! %d Mist Edge event records exported to %s", len(rawdata), filename)

    @staticmethod
    def mist_edge_events() -> None:
        """Search Mist Edge events for a site and export to SiteMistEdgeEvents_<site>.csv.

        Why:
            Interactive menu entry point (menu 201).  Delegates site
            resolution to the shared helper so behavior stays consistent
            with peer site-scoped exports.  Errors are logged and surfaced
            to the user rather than crashing the menu loop.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + shared helpers.
        # WHY: menu header echoed to operator.
        logging.info("Site Mist Edge Events Search:")
        logging.info(  # INFO trace before the API call per Action Logging principle (pre-call).
            "Starting searchSiteMistEdgeEvents export..."
        )
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(  # Prompt + org/site resolution (shared).
            "Mist Edge events search"
        )
        if resolved is None:  # Operator declined selection or org unresolved -- shared helper already logged.
            return
        site_id, site_name = resolved  # Unpack resolved identifiers for the API call.
        try:
            logging.info(  # INFO trace immediately before the SDK call (with site context).
                "Calling searchSiteMistEdgeEvents for site_id=%s (%s)", site_id, site_name
            )
            response = mistapi.api.v1.sites.mxedges.searchSiteMistEdgeEvents(  # SDK call -- defaults for filters.
                mh.apisession, site_id
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            SiteMistEdgeEventsExporter._persist_site_mist_edge_events(rawdata, site_name)  # Persist or notify empty.
        except Exception as e:  # noqa: BLE001 -- surface any SDK/network error to the user instead of crashing.
            logging.error(  # ERROR trace with site context for post-mortem correlation.
                "Error fetching Mist Edge events for site %s: %s", site_name, e
            )
            # WHY: ASCII-only user notice.
            logging.info("! Error fetching Mist Edge event data: %s", e)
