"""SiteSystemEventsExporter -- site-level system event search export.

Added for spec 898 / issue #1406. Wraps the Mist API ``searchSiteSystemEvents``
(``GET /api/v1/sites/{site_id}/events/system/search``) so operators can retrieve
per-site system events through the standard MistHelper menu and DataExporter
pipeline (CSV, SQLite, or ArangoDB).

Why:
    The endpoint was absent from the menu, so operators had to write custom code
    to reach site system events during an incident review.

Warning: the source spec names the SDK module
``mistapi.api.v1.sites.events.system.search``, which does not exist. The real
module is ``mistapi.api.v1.sites.events``. See issue #1757.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw event rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for searchSiteSystemEvents and get_all pagination.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.


class SiteSystemEventsExporter:
    """Site system event search exporter.

    Why:
        Provides the only MistHelper entry point for the
        ``searchSiteSystemEvents`` operationId. Static methods only, with no
        per-instance state, matching the peer site exporters.
    """

    @staticmethod
    def _persist_system_events(rawdata: list[Any], site_name: str) -> None:
        """Flatten and persist system event rows, or tell the operator when there are none.

        Why:
            An empty response is legitimate when a site logged no system events
            in the query window, so we report it plainly instead of failing.

        Args:
            rawdata: The raw rows returned by the event search. May be empty.
            site_name: The human-readable site name used to name the output file.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rawdata:  # No events, so inform the operator and return.
            logging.info("! No system event data found for this site")  # ASCII-only user notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Make multiline values CSV-safe.
        filename = f"SiteSystemEvents_{site_name.replace(' ', '_')}.csv"  # Per-site filename.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name="searchSiteSystemEvents"
        )
        logging.debug(  # Post-call count trace per the action-logging rule.
            "searchSiteSystemEvents persisted %d rows to %s", len(rawdata), filename
        )
        logging.info("! %d system event records exported to %s", len(rawdata), filename)  # User notice with count.

    @staticmethod
    def system_events() -> None:
        """Search system events for a site and export them (menu 214).

        Why:
            Interactive menu entry point. Site resolution is delegated to the
            shared helper so behavior matches the peer site-scoped exports.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Site System Event Search:")  # Menu header echoed to the operator.
        logging.info("Starting the searchSiteSystemEvents export...")  # Pre-call trace.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("system event search")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the shared helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        try:
            logging.info("Calling searchSiteSystemEvents for site_id=%s (%s)", site_id, site_name)  # Pre-call log.
            response = mistapi.api.v1.sites.events.searchSiteSystemEvents(  # SDK call with default filters.
                mh.apisession, site_id
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            SiteSystemEventsExporter._persist_system_events(rawdata, site_name)  # Persist or report empty.
        except Exception as e:  # surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching system events for site %s: %s", site_name, e)  # Failure context.
            logging.info("! Error fetching system event data: %s", e)  # ASCII-only user notice.
