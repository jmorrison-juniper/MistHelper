"""OrgSearchExporter -- organization-scoped search export operations.

Added for specs 878, 877, 875, 874, 879, and 870 (issues #1386, #1385, #1383,
#1382, #1379, and #1378). Wraps read-only Mist API search endpoints so operators reach them
through the standard MistHelper menu and DataExporter pipeline (CSV, SQLite, or
ArangoDB).

Covered operations:
    - ``searchOrgDevices`` (menu 249)
    - ``searchOrgWirelessClientSessions`` (menu 230)
    - ``searchOrgWirelessClientEvents`` (menu 231)
    - ``searchOrgWanClients`` (menu 232)
    - ``searchOrgWanClientEvents`` (menu 233)
    - ``searchOrgSystemEvents`` (menu 234)
    - ``searchOrgSites`` (menu 248)
    - ``searchOrgMxEdges`` (menu 250)

Why:
    Every endpoint takes a session and an organization and returns
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

_MXEDGE_FILTER_PROMPTS = {  # Keep the prompt order aligned with the endpoint contract.
    "mxedge_id": "MxEdge ID",  # Identify one Mist Edge when the operator supplies it.
    "site_id": "site ID",  # Restrict the search to one site when supplied.
    "mxcluster_id": "MxCluster ID",  # Restrict the search to one cluster when supplied.
    "model": "model",  # Restrict the search to one hardware model when supplied.
    "distro": "distro",  # Restrict the search to one distribution when supplied.
    "tunterm_version": "tunterm version",  # Restrict the search to one tunterm version when supplied.
    "stats": "stats (true/false)",  # Request statistics when the operator selects true.
    "limit": "limit",  # Limit the number of rows when supplied.
    "start": "start time",  # Set the start of the search window when supplied.
    "end": "end time",  # Set the end of the search window when supplied.
    "duration": "duration",  # Set the relative search window when supplied.
    "sort": "sort",  # Set the Mist sort expression when supplied.
    "search_after": "search_after cursor",  # Continue from a Mist pagination cursor when supplied.
}


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
    def devices() -> None:
        """Search the devices for an organization and export them (menu 249)."""
        OrgSearchExporter._run_org_search(  # Reuse the standard org search pipeline for consistent output.
            mistapi.api.v1.orgs.devices.searchOrgDevices,  # Call the organization device search endpoint.
            "searchOrgDevices",  # Route the response to the endpoint primary-key strategy.
            "OrgDevices",  # Keep the output filename stable for operators and automation.
            "device",  # Use the singular noun in empty and success messages.
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

    @staticmethod
    def sites() -> None:
        """Search the sites for an organization (menu 248)."""
        OrgSearchExporter._run_org_search(  # Reuse the standard org search pipeline for consistent output.
            mistapi.api.v1.orgs.sites.searchOrgSites,  # Call the Mist site search endpoint exposed by the SDK.
            "searchOrgSites",  # Route output storage through the endpoint strategy.
            "OrgSitesSearch",  # Use a stable filename prefix for the export.
            "site",  # Report the result type in operator messages.
        )

    @staticmethod
    def _prompt_mxedge_filters() -> dict[str, Any]:
        """Prompt for optional searchOrgMxEdges filters and omit blank values."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the safe prompt helper.
        filters: dict[str, Any] = {}  # Blank optional filters stay out of the SDK call.
        for name, label in _MXEDGE_FILTER_PROMPTS.items():  # Ask for each optional filter without using bare input().
            answer = mh.InputUtils.safe_input(  # safe_input keeps SSH, EOF, and Ctrl-C paths clean.
                f"Enter {label} for searchOrgMxEdges (optional): ",
                context=f"org_search_exporter.searchOrgMxEdges.{name}",
            ).strip()
            logging.debug("searchOrgMxEdges filter %s present=%s", name, bool(answer))  # Prompt result trace.
            if not answer:  # An empty optional filter means the SDK default.
                continue
            converted = OrgSearchExporter._coerce_mxedge_filter(name, answer)  # Validate each supplied filter.
            if converted is not None:  # Keep valid values and omit invalid integer input.
                filters[name] = converted  # Forward the validated value to the SDK.
        return filters

    @staticmethod
    def _coerce_mxedge_filter(name: str, answer: str) -> Any | None:
        """Convert one optional MxEdge filter to its SDK type."""
        if name == "stats":  # Convert the documented boolean text to the SDK boolean type.
            return answer.lower() in {"1", "true", "yes", "y"}  # Normalize common true values.
        if name == "limit":  # Convert the documented integer text before the request.
            try:
                return int(answer)  # Keep the SDK call type-safe for the limit.
            except ValueError:
                logging.warning("Ignoring invalid searchOrgMxEdges limit: %s", answer)  # Surface bad input.
                return None  # Omit invalid input instead of sending a bad request.
        return answer  # Forward string filters exactly as entered.

    @staticmethod
    def mx_edges() -> None:
        """Search organization MxEdges and export the result (menu 249)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of shared session and export helpers.
        logging.info("Organization MxEdge Search:")  # Menu header echoed to the operator.
        logging.info("Starting the searchOrgMxEdges export...")  # Pre-call trace.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the organization context.
        if not org_id:  # The operator declined, or no organization could be resolved.
            logging.error("No org_id available for searchOrgMxEdges. Exiting.")  # Abort reason.
            logging.info("! No organization selected. Exiting.")  # User-facing cancel line.
            return
        filters = OrgSearchExporter._prompt_mxedge_filters()  # Collect optional query filters safely.
        try:
            logging.info("Calling searchOrgMxEdges for org_id=%s", org_id)  # Pre-call log.
            response = mistapi.api.v1.orgs.mxedges.searchOrgMxEdges(  # Invoke the installed SDK endpoint.
                mh.apisession, org_id, **filters
            )
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            OrgSearchExporter._persist(rawdata, "OrgMxEdges", "searchOrgMxEdges", "MxEdge")  # Persist results.
        except Exception as e:  # Surface SDK or network errors without crashing the menu loop.
            logging.error("Error fetching MxEdge data for org %s: %s", org_id, e)  # Failure context.
            logging.info("! Error fetching MxEdge data: %s", e)  # ASCII-only user notice.
