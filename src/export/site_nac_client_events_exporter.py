"""SiteNacClientEventsExporter -- site-level NAC client event search export.

Added for spec 891 / issue #1399.  Wraps the Mist API
``searchSiteNacClientEvents`` (``GET /api/v1/sites/{site_id}/nac_clients/events/search``)
so operators can retrieve per-site NAC client event records through the
standard MistHelper menu + DataExporter pipeline (CSV/SQLite/ArangoDB).

Why:
    The endpoint was absent from MistHelper's menu, forcing users to write
    custom code to reach NAC client event history.  This exporter closes
    that gap while reusing the shared site-resolution + persistence
    scaffolding established by ``SiteMistEdgeEventsExporter`` and
    ``SiteDeviceExporter._resolve_site_for_stats()``.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw event rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for searchSiteNacClientEvents + get_all pagination.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten/escape helpers. Keeps CSV output consistent with peers.


class SiteNacClientEventsExporter:
    """Site NAC Client Events search exporter.

    Why:
        Provides the sole MistHelper entry point for the
        ``searchSiteNacClientEvents`` operationId.  Static methods only --
        no per-instance state, matching the pattern used by
        ``SiteMistEdgeEventsExporter`` / ``SiteDeviceExporter``.
    """

    @staticmethod
    def _persist_site_nac_client_events(rawdata: list[Any], site_name: str) -> None:
        """Flatten + persist NAC client event rows to a per-site file (or tell the user when empty).

        Why:
            Empty responses are legitimate (a site with no NAC client events
            in the query window). We surface a friendly message rather than
            failing so scheduled runs stay quiet in that case.

        Args:
            rawdata: Raw list returned by ``mistapi.get_all`` for the NAC
                client events search response.  May be empty.
            site_name: Human-readable site name used to name the output
                file (falls back to site_id when name lookup failed).
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        if not rawdata:  # No NAC client event rows for this site -- inform the operator and return.
            # WHY: ASCII-only user notice.
            logging.info("! No NAC client event data found for this site")
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe multiline escape.
        filename = f"SiteNacClientEvents_{site_name.replace(' ', '_')}.csv"  # Per-site filename.
        mh.DataExporter.write_with_format_selection(  # Persist through CSV/SQLite/Arango backend selector.
            sanitized_data, filename, api_function_name="searchSiteNacClientEvents"
        )
        logging.debug(  # DEBUG-level count trace per Action Logging principle (post-call).
            "searchSiteNacClientEvents persisted %d rows to %s", len(rawdata), filename
        )
        # WHY: user notice with count.
        logging.info("! %d NAC client event records exported to %s", len(rawdata), filename)

    @staticmethod
    def nac_client_events() -> None:
        """Search NAC client events for a site and export to SiteNacClientEvents_<site>.csv.

        Why:
            Interactive menu entry point (menu 202).  Delegates site
            resolution to the shared helper so behavior stays consistent
            with peer site-scoped exports.  Errors are logged and surfaced
            to the user rather than crashing the menu loop.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession + shared helpers.
        # WHY: menu header echoed to operator.
        logging.info("Site NAC Client Events Search:")
        logging.info(  # INFO trace before the API call per Action Logging principle (pre-call).
            "Starting searchSiteNacClientEvents export..."
        )
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(  # Prompt + org/site resolution (shared).
            "NAC client events search"
        )
        if resolved is None:  # Operator declined selection or org unresolved -- shared helper already logged.
            return
        site_id, site_name = resolved  # Unpack resolved identifiers for the API call.
        try:
            logging.info(  # INFO trace immediately before the SDK call (with site context).
                "Calling searchSiteNacClientEvents for site_id=%s (%s)", site_id, site_name
            )
            response = mistapi.api.v1.sites.nac_clients.searchSiteNacClientEvents(  # SDK call -- defaults for filters.
                mh.apisession, site_id
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            SiteNacClientEventsExporter._persist_site_nac_client_events(rawdata, site_name)  # Persist or notify empty.
        except Exception as e:  # noqa: BLE001 -- surface any SDK/network error to the user instead of crashing.
            logging.error(  # ERROR trace with site context for post-mortem correlation.
                "Error fetching NAC client events for site %s: %s", site_name, e
            )
            # WHY: ASCII-only user notice.
            logging.info("! Error fetching NAC client event data: %s", e)
