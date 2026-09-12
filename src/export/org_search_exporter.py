"""OrgSearchExporter -- organization-scoped search export operations.

Added for specs 878, 877, 875, 874 and 879 (issues #1386, #1385, #1383, #1382
and #1379). Wraps read-only Mist API search endpoints so operators reach them
through the standard MistHelper menu and DataExporter pipeline (CSV, SQLite, or
ArangoDB).

Covered operations:
    - ``searchOrgWirelessClientSessions`` (menu 230)
    - ``searchOrgWirelessClientEvents`` (menu 231)
    - ``searchOrgWanClients`` (menu 232)
    - ``searchOrgWanClientEvents`` (menu 233)
    - ``searchOrgSystemEvents`` (menu 234)

Why:
    Every one of these endpoints takes a session and an organization and returns
    a paginated row set. One shared helper therefore runs the whole resolve,
    fetch, and persist sequence, and each menu entry supplies only the parts that
    differ. This mirrors ``SiteSearchExporter`` for the site-scoped peers.

Warning: the ``**mistapi SDK module**`` line in the source specs is wrong for
many endpoints. See issue #1757. Every module path below was resolved against
the installed SDK.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+ toolchains.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from collections.abc import Callable  # WHY: the per-operation SDK callable is injected.
from typing import Any

import mistapi  # WHY: direct SDK access for the search endpoints and get_all pagination.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.


class OrgSearchExporter:
    """Organization-scoped search exporter.

    Why:
        Provides the only MistHelper entry points for the search operationIds
        listed above. Static methods only, with no per-instance state, matching
        the peer organization exporters.
    """

    @staticmethod
    def _persist(rawdata: list[Any], prefix: str, operation: str, label: str) -> None:
        """Flatten and persist search rows, or tell the operator when there are none.

        Why:
            An empty result is legitimate when the organization logged nothing in
            the query window, so we report it plainly instead of failing.

        Args:
            rawdata: The raw rows returned by the search. May be empty.
            prefix: The filename prefix that identifies the operation.
            operation: The operationId used to route the primary-key strategy.
            label: A human-readable noun used in the operator messages.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rawdata:  # No rows, so inform the operator and return.
            logging.info("! No %s data found for this organization", label)  # ASCII-only user notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested dicts for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Make multiline values CSV-safe.
        filename = f"{prefix}.csv"  # Organization exports are not split per site.
        mh.DataExporter.write_with_format_selection(  # Persist through the CSV, SQLite, or Arango selector.
            sanitized_data, filename, api_function_name=operation
        )
        logging.debug("%s persisted %d rows to %s", operation, len(rawdata), filename)  # Post-call count trace.
        logging.info("! %d %s records exported to %s", len(rawdata), label, filename)  # User notice with count.

    @staticmethod
    def _run_org_search(
        api_call: Callable[..., Any],
        operation: str,
        prefix: str,
        label: str,
    ) -> None:
        """Run the shared resolve, fetch, and persist sequence for one search endpoint.

        Why:
            The endpoints differ only in the SDK callable and the naming, so one
            helper keeps their behavior identical. Errors are logged and surfaced
            to the operator rather than crashing the menu loop.

        Args:
            api_call: The SDK function to invoke with the session and the org.
            operation: The operationId used to route the primary-key strategy.
            prefix: The filename prefix that identifies the operation.
            label: A human-readable noun used in the operator messages.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Organization %s Search:", label.title())  # Menu header echoed to the operator.
        logging.info("Starting the %s export...", operation)  # Pre-call trace.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the organization context.
        if not org_id:  # The operator declined, or no organization could be resolved.
            logging.error("No org_id available for %s. Exiting.", operation)  # Abort reason.
            logging.info("! No organization selected. Exiting.")  # User-facing cancel line.
            return
        try:
            logging.info("Calling %s for org_id=%s", operation, org_id)  # Pre-call log.
            response = api_call(mh.apisession, org_id)  # SDK call with default filters.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            OrgSearchExporter._persist(rawdata, prefix, operation, label)  # Persist or report empty.
        except Exception as e:  # surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching %s for org %s: %s", label, org_id, e)  # Failure context.
            logging.info("! Error fetching %s data: %s", label, e)  # ASCII-only user notice.

    @staticmethod
    def wireless_client_sessions() -> None:
        """Search the wireless client sessions for an organization (menu 230)."""
        OrgSearchExporter._run_org_search(
            mistapi.api.v1.orgs.clients.searchOrgWirelessClientSessions,
            "searchOrgWirelessClientSessions",
            "OrgWirelessClientSessions",
            "wireless client session",
        )

    @staticmethod
    def wireless_client_events() -> None:
        """Search the wireless client events for an organization (menu 231)."""
        OrgSearchExporter._run_org_search(
            mistapi.api.v1.orgs.clients.searchOrgWirelessClientEvents,
            "searchOrgWirelessClientEvents",
            "OrgWirelessClientEvents",
            "wireless client event",
        )

    @staticmethod
    def wan_clients() -> None:
        """Search the WAN clients for an organization (menu 232)."""
        OrgSearchExporter._run_org_search(
            mistapi.api.v1.orgs.wan_clients.searchOrgWanClients,
            "searchOrgWanClients",
            "OrgWanClients",
            "WAN client",
        )

    @staticmethod
    def wan_client_events() -> None:
        """Search the WAN client events for an organization (menu 233)."""
        OrgSearchExporter._run_org_search(
            mistapi.api.v1.orgs.wan_clients.searchOrgWanClientEvents,
            "searchOrgWanClientEvents",
            "OrgWanClientEvents",
            "WAN client event",
        )

    @staticmethod
    def system_events() -> None:
        """Search the system events for an organization (menu 234)."""
        OrgSearchExporter._run_org_search(
            mistapi.api.v1.orgs.events.searchOrgSystemEvents,
            "searchOrgSystemEvents",
            "OrgSystemEvents",
            "system event",
        )
