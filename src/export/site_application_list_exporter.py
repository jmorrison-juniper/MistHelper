"""SiteApplicationListExporter -- site-level application list export.

Added for spec 666 / issue #1416. Wraps the Mist API ``getSiteApplicationList``
(``GET /api/v1/sites/{site_id}/wxtags/apps``) so operators can read the
applications a site recognizes through the standard MistHelper menu and
DataExporter pipeline (CSV, SQLite, or ArangoDB).

Why:
    The endpoint was absent from the menu, so operators had to write custom code
    to list the applications available for WxLAN tag rules.

Warning: the source spec names the SDK module ``mistapi.api.v1.sites.wxtags.apps``,
which does not exist. The real module is ``mistapi.api.v1.sites.wxtags``. See
issue #1757.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw application rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for getSiteApplicationList and get_all pagination.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.


class SiteApplicationListExporter:
    """Site application list exporter.

    Why:
        Provides the only MistHelper entry point for the
        ``getSiteApplicationList`` operationId. Static methods only, with no
        per-instance state, matching the peer site exporters.
    """

    @staticmethod
    def _persist_applications(rawdata: list[Any], site_name: str) -> None:
        """Flatten and persist application rows, or tell the operator when there are none.

        Why:
            An empty response is legitimate for a site with no recognized
            applications, so we report it plainly instead of failing.

        Args:
            rawdata: The raw rows returned for the application list. May be empty.
            site_name: The human-readable site name used to name the output file.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rawdata:  # No applications, so inform the operator and return.
            logging.info("! No application data found for this site")  # ASCII-only user notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Make multiline values CSV-safe.
        filename = f"SiteApplicationList_{site_name.replace(' ', '_')}.csv"  # Per-site filename.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name="getSiteApplicationList"
        )
        logging.debug(  # Post-call count trace per the action-logging rule.
            "getSiteApplicationList persisted %d rows to %s", len(rawdata), filename
        )
        logging.info("! %d application records exported to %s", len(rawdata), filename)  # User notice with count.

    @staticmethod
    def application_list() -> None:
        """Export the application list for a site (menu 213).

        Why:
            Interactive menu entry point. Site resolution is delegated to the
            shared helper so behavior matches the peer site-scoped exports.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Site Application List:")  # Menu header echoed to the operator.
        logging.info("Starting the getSiteApplicationList export...")  # Pre-call trace.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("application list")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the shared helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        try:
            logging.info("Calling getSiteApplicationList for site_id=%s (%s)", site_id, site_name)  # Pre-call log.
            response = mistapi.api.v1.sites.wxtags.getSiteApplicationList(  # SDK call for the site application list.
                mh.apisession, site_id
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            SiteApplicationListExporter._persist_applications(rawdata, site_name)  # Persist or report empty.
        except Exception as e:  # noqa: BLE001 -- surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching the application list for site %s: %s", site_name, e)  # Failure context.
            logging.info("! Error fetching application list data: %s", e)  # ASCII-only user notice.
