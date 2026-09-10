"""OrgSearchExporter -- organization-scoped search export operations.

Added for specs 878, 877, 875, 874, 879, 870, 872, and 869 (issues #1386, #1385,
#1383, #1382, #1379, #1378, #1380, and #1377). Wraps read-only Mist API search
endpoints so operators reach them through the standard MistHelper menu and
DataExporter pipeline (CSV, SQLite, or ArangoDB).

Covered operations:
    - ``searchOrgDevices`` (menu 249)
    - ``searchOrgWirelessClientSessions`` (menu 230)
    - ``searchOrgWirelessClientEvents`` (menu 231)
    - ``searchOrgWanClients`` (menu 232)
    - ``searchOrgWanClientEvents`` (menu 233)
    - ``searchOrgSystemEvents`` (menu 234)
    - ``searchOrgSites`` (menu 248)
    - ``searchOrgUserMacs`` (menu 251)
    - ``searchOrgMxEdges`` (menu 253)
    - ``searchOrgPskPortalLogs`` (menu 255)

Why:
    Every endpoint takes a session and an organization and returns
    a paginated row set. One shared helper therefore runs the whole resolve,
    prompt, fetch, and persist sequence, and each menu entry supplies only the
    parts that differ, which are the SDK callable, the naming, and the optional
    filters. This mirrors ``SiteSearchExporter`` for the site-scoped peers.

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

    # WHY: the installed SDK declares a type for some filters, so one map converts each answer once.
    _BOOLEAN_FILTERS = frozenset({"stats"})  # Filters the SDK declares as a boolean.
    _INTEGER_FILTERS = frozenset({"limit"})  # Filters the SDK declares as an integer.
    _LIST_FILTERS = frozenset({"labels"})  # Filters the SDK declares as a list of strings.

    # WHY: these are the optional searchOrgMxEdges filters in the installed SDK signature.
    _MXEDGE_FILTER_PROMPTS = {
        "hostname": "hostname",  # The SDK accepts a full or partial MxEdge hostname.
        "mxedge_id": "MxEdge ID",  # The SDK accepts one MxEdge identifier.
        "mxcluster_id": "MxCluster ID",  # The SDK accepts one MxCluster identifier.
        "model": "model",  # The SDK accepts one hardware model name.
        "distro": "distro",  # The SDK accepts one distribution name.
        "tunterm_version": "tunterm version",  # The SDK accepts one tunnel terminator version.
        "site_id": "site ID",  # The SDK accepts one site identifier.
        "stats": "stats (true or false)",  # The SDK accepts a boolean that adds statistics.
        "limit": "page size limit",  # The SDK accepts an integer page size.
        "start": "start time",  # The SDK accepts the start of the query window.
        "end": "end time",  # The SDK accepts the end of the query window.
        "duration": "duration",  # The SDK accepts a duration instead of an end time.
        "sort": "sort field, with a - prefix for descending order",  # The SDK accepts one sort field.
        "search_after": "search_after cursor",  # The SDK accepts one deep-page cursor.
    }

    # WHY: these are the optional searchOrgUserMacs filters in the installed SDK signature.
    # The SDK also accepts a page number, but mistapi.get_all owns the page walk, so the
    # prompt list holds no page filter. A page filter would fight the shared pagination.
    _USER_MAC_FILTER_PROMPTS = {
        "mac": "MAC address, full or partial",  # The SDK accepts a full or partial MAC address.
        "labels": "labels, separated by commas",  # The SDK accepts a list of label strings.
        "limit": "page size limit",  # The SDK accepts an integer page size.
        "sort": "sort field, with a - prefix for descending order",  # The SDK accepts one sort field.
    }

    @staticmethod
    def _coerce_filter(operation: str, name: str, answer: str) -> Any:
        """Convert one filter answer to the type that the installed SDK declares.

        Why:
            The operator types every answer as text, but the SDK declares a
            boolean, an integer, or a list for some filters. One converter keeps
            the request type-safe for every search that uses a prompt.

        Args:
            operation: The operationId, used only in the log line.
            name: The SDK parameter name of the filter.
            answer: The trimmed text that the operator typed.

        Returns:
            The converted value, or None when the answer cannot be used.
        """
        if name in OrgSearchExporter._BOOLEAN_FILTERS:  # The SDK declares a boolean for this filter.
            return answer.lower() in {"1", "true", "yes", "y"}  # Accept the common words for true.
        if name in OrgSearchExporter._LIST_FILTERS:  # The SDK declares a list for this filter.
            return [item.strip() for item in answer.split(",") if item.strip()] or None  # Drop blank items.
        if name in OrgSearchExporter._INTEGER_FILTERS:  # The SDK declares an integer for this filter.
            try:
                return int(answer)  # Keep the request type-safe for the page size.
            except ValueError:  # The operator typed text that is not a number.
                logging.warning("Ignoring the invalid %s %s value: %s", operation, name, answer)  # Bad input.
                return None
        return answer  # Every other filter is a plain string.

    @staticmethod
    def _prompt_filters(operation: str, prompts: dict[str, str]) -> dict[str, Any]:
        """Ask for the optional filters of one search and omit every blank answer.

        Why:
            A blank answer must leave the SDK default in place, so the exporter
            sends only the filters that the operator supplied. The unattended
            ``--test`` sweep runs these menus, and a ``safe`` menu must not read
            stdin, so test mode skips every prompt. See issue #1765.

        Args:
            operation: The operationId shown in the prompt and the log.
            prompts: A map of SDK parameter name to operator-facing label.

        Returns:
            The filters to forward to the SDK call. The map can be empty.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the safe prompt helper.
        if getattr(mh, "IS_TEST_MODE", False):  # The unattended sweep must never block on stdin.
            logging.info("Test mode skips the optional %s filters", operation)  # Action log before the skip.
            logging.debug("Completed the %s prompts with 0 filters", operation)  # Result trace.
            return {}
        logging.info("Prompting the operator for the optional %s filters", operation)  # Action log before.
        filters: dict[str, Any] = {}  # A blank optional filter stays out of the SDK call.
        for name, label in prompts.items():  # Ask for each optional filter through the safe wrapper.
            prompt_text = f"Enter {label} for {operation} (optional): "  # Name the filter and the operation.
            context = f"org_search_exporter.{operation}.{name}"  # Tag the prompt for the log.
            answer = str(mh.InputUtils.safe_input(prompt_text, context=context)).strip()  # EOF-safe prompt.
            if not answer:  # A blank optional filter means the SDK default.
                continue
            value = OrgSearchExporter._coerce_filter(operation, name, answer)  # Convert to the SDK type.
            if value is None:  # The answer was unusable, so leave the SDK default in place.
                continue
            filters[name] = value  # Forward the converted filter.
        logging.debug("Completed the %s prompts with %d filters", operation, len(filters))  # Result trace.
        return filters

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
        prompts: dict[str, str] | None = None,
    ) -> None:
        """Run the shared resolve, fetch, and persist sequence for one search endpoint.

        Why:
            The endpoints differ only in the SDK callable, the naming, and the
            optional filters, so one helper keeps their behavior identical.
            Errors are logged and surfaced to the operator rather than crashing
            the menu loop.

        Args:
            api_call: The SDK function to invoke with the session and the org.
            operation: The operationId used to route the primary-key strategy.
            prefix: The filename prefix that identifies the operation.
            label: A human-readable noun used in the operator messages.
            prompts: The optional filter prompts, or None to ask for no filter.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Organization %s Search:", label.title())  # Menu header echoed to the operator.
        logging.info("Starting the %s export...", operation)  # Pre-call trace.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the organization context.
        if not org_id:  # The operator declined, or no organization could be resolved.
            logging.error("No org_id available for %s. Exiting.", operation)  # Abort reason.
            logging.info("! No organization selected. Exiting.")  # User-facing cancel line.
            return
        filters = OrgSearchExporter._prompt_filters(operation, prompts) if prompts else {}  # Optional filters.
        try:
            logging.info("Calling %s for org_id=%s", operation, org_id)  # Pre-call log.
            response = api_call(mh.apisession, org_id, **filters)  # SDK call with the supplied filters.
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
    def mx_edges() -> None:
        """Search organization MxEdges and export the result (menu 253)."""
        OrgSearchExporter._run_org_search(  # Reuse the standard org search pipeline for consistent output.
            mistapi.api.v1.orgs.mxedges.searchOrgMxEdges,  # Call the Mist MxEdge search endpoint.
            "searchOrgMxEdges",  # Route output storage through the endpoint strategy.
            "OrgMxEdges",  # Use a stable filename prefix for the export.
            "MxEdge",  # Report the result type in operator messages.
            OrgSearchExporter._MXEDGE_FILTER_PROMPTS,  # Ask for the optional SDK filters.
        )

    @staticmethod
    def user_macs() -> None:
        """Search user MAC assignments for an organization (menu 251)."""
        OrgSearchExporter._run_org_search(  # Reuse the standard org search pipeline for consistent output.
            mistapi.api.v1.orgs.usermacs.searchOrgUserMacs,  # Call the Mist user MAC search endpoint.
            "searchOrgUserMacs",  # Route output storage through the endpoint strategy.
            "OrgUserMacs",  # Use a stable filename prefix for the export.
            "user MAC",  # Report the result type in operator messages.
            OrgSearchExporter._USER_MAC_FILTER_PROMPTS,  # Ask for the optional SDK filters.
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
    def org_vars() -> None:
        """Search organization variables (menu 250)."""
        OrgSearchExporter._run_org_search(
            mistapi.api.v1.orgs.vars.searchOrgVars,
            "searchOrgVars",
            "OrgVars",
            "organization variable",
        )

    @staticmethod
    def psk_portal_logs() -> None:
        """Search PSK portal logs for an organization (menu 255)."""
        OrgSearchExporter._run_org_search(
            mistapi.api.v1.orgs.pskportals.searchOrgPskPortalLogs,
            "searchOrgPskPortalLogs",
            "OrgPskPortalLogs",
            "PSK portal log",
        )
