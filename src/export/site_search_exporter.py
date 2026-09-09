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
    - ``searchSiteOspfStats`` (menu 225)
    - ``searchSiteDeviceLastConfigs`` (menu 226)
    - ``searchSiteDeviceConfigHistory`` (menu 227)
    - ``searchSiteDiscoveredSwitches`` (menu 228)
    - ``searchSiteZoneSessions`` (menu 229)

Why:
    Nearly all of these endpoints take the same arguments, a session and a site,
    and return a paginated row set. One shared helper therefore runs the whole
    prompt, fetch, and persist sequence, and each menu entry supplies only the
    parts that differ. That keeps the operations consistent and avoids one copy
    of the same code per endpoint. ``searchSiteZoneSessions`` is the exception,
    because it puts a zone type in the URL path, so it prompts for that value and
    passes it through as an extra argument.

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

_VALID_ZONE_TYPES = frozenset({"zones", "rssizones"})  # WHY: the SDK rejects any other value in the URL path.
_DEFAULT_ZONE_TYPE = "zones"  # WHY: the common case, so an empty answer stays useful.


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
        extra_args: tuple[Any, ...] = (),
    ) -> None:
        """Run the shared prompt, fetch, and persist sequence for one search endpoint.

        Why:
            The endpoints differ only in the SDK callable and the naming, so one
            helper keeps their behavior identical. Errors are logged and surfaced
            to the operator rather than crashing the menu loop.

        Args:
            api_call: The SDK function to invoke with the session and the site.
            operation: The operationId used to route the primary-key strategy.
            prefix: The filename prefix that identifies the operation.
            label: A human-readable noun used in the operator messages.
            extra_args: Any further positional arguments the endpoint requires
                after the site. Only searchSiteZoneSessions needs one today.
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
            response = api_call(mh.apisession, site_id, *extra_args)  # SDK call with default filters.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all rows.
            SiteSearchExporter._persist(rawdata, site_name, prefix, operation, label)  # Persist or report empty.
        except Exception as e:  # surface any SDK or network error rather than crashing the menu.
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

    @staticmethod
    def ospf_stats() -> None:
        """Search the OSPF neighbor statistics for a site and export them (menu 225)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.stats.searchSiteOspfStats,
            "searchSiteOspfStats",
            "SiteOspfStats",
            "OSPF stat",
        )

    @staticmethod
    def device_last_configs() -> None:
        """Search the last device configurations for a site and export them (menu 226)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.devices.searchSiteDeviceLastConfigs,
            "searchSiteDeviceLastConfigs",
            "SiteDeviceLastConfigs",
            "device last config",
        )

    @staticmethod
    def device_config_history() -> None:
        """Search the device configuration history for a site and export it (menu 227)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.devices.searchSiteDeviceConfigHistory,
            "searchSiteDeviceConfigHistory",
            "SiteDeviceConfigHistory",
            "device config history",
        )

    @staticmethod
    def discovered_switches() -> None:
        """Search the discovered switches for a site and export them (menu 228)."""
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.stats.searchSiteDiscoveredSwitches,
            "searchSiteDiscoveredSwitches",
            "SiteDiscoveredSwitches",
            "discovered switch",
        )

    @staticmethod
    def _prompt_identifier(prompt_text: str, context: str) -> str | None:
        """Prompt for one required identifier and reject an empty answer.

        Why:
            The troubleshoot endpoint cannot run without its identifiers, and
            ``safe_input`` keeps the prompt safe under SSH and container EOF.

        Args:
            prompt_text: The text shown to the operator.
            context: A tag recorded in the logs to locate the prompt.

        Returns:
            The trimmed identifier, or None when the operator gave no answer.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils keeps the import acyclic.
        logging.info("Prompting the operator for %s", context)  # Action log before the prompt.
        value = str(  # WHY: the lazy module attribute is untyped, so pin the declared str return.
            mh.InputUtils.safe_input(  # safe_input enforces EOF-safe prompting.
                prompt_text,
                allow_empty=False,  # An empty identifier is invalid for the API path.
                context=context,
            )
        ).strip()  # Strip whitespace so stray spaces do not pass validation.
        logging.debug("Completed the %s prompt with value_present=%s", context, bool(value))  # Prompt result trace.
        if not value:  # A blank answer, an EOF, or an interrupt must abort before any API call.
            logging.error("No value provided for %s. Exiting.", context)  # Abort reason.
            logging.info("! No identifier supplied. Exiting.")  # User-facing cancel line.
            return None
        return value

    @staticmethod
    def _normalize_payload(response_payload: Any) -> list[dict[str, Any]]:
        """Normalize a troubleshoot payload to a list of dict rows.

        Why:
            The endpoint returns one object with a ``results`` array, but
            ``DataExporter`` expects iterable rows. Wrapping here keeps the
            caller uniform with the search operations.

        Args:
            response_payload: The decoded body from the SDK response. May be a
                dict, a list, or None.

        Returns:
            A list of dict rows, which is empty when the payload carries no data.
        """
        if response_payload is None:  # An empty body is a legitimate result, so return no rows.
            return []
        if isinstance(response_payload, list):  # Defensive support for list payloads from wrappers and mocks.
            rows = [row for row in response_payload if isinstance(row, dict)]  # Keep only dict rows.
            logging.debug("Normalized list payload to %d dict rows", len(rows))  # Coercion trace.
            return rows
        if isinstance(response_payload, dict):  # The expected SDK path returns one object as a dict.
            if isinstance(response_payload.get("results"), list):  # The documented shape nests the rows under results.
                rows = [row for row in response_payload["results"] if isinstance(row, dict)]  # Keep only dict rows.
                if rows:  # A non-empty results array is the row set to export.
                    logging.debug("Normalized results array to %d dict rows", len(rows))  # Coercion trace.
                    return rows
            logging.debug("Normalized dict payload to a single-row list")  # Coercion trace.
            return [response_payload]
        logging.warning(  # An unexpected type means the SDK contract changed, so say so instead of failing.
            "Unexpected payload type %s; treating it as an empty result",
            type(response_payload).__name__,
        )
        return []

    @staticmethod
    def troubleshoot_call() -> None:
        """Export the call troubleshooting diagnostics for one client meeting (menu 246).

        Why:
            Interactive menu entry point for ``troubleshootSiteCall``. The
            endpoint needs a site, a client MAC, and a meeting ID, so it prompts
            for the two identifiers before it calls the SDK.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession and the shared helpers.
        logging.info("Site Call Troubleshoot:")  # Menu header echoed to the operator.
        logging.info("Starting the troubleshootSiteCall export...")  # Pre-call trace.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("call troubleshoot")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the shared helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        client_mac = SiteSearchExporter._prompt_identifier(  # Ask for the required client MAC.
            "Enter Client MAC for troubleshootSiteCall (e.g. 98:3a:78:ea:4a:44): ",
            "site_search_exporter.troubleshootSiteCall.client_mac",
        )
        if client_mac is None:  # The prompt helper already logged the cancellation.
            return
        meeting_id = SiteSearchExporter._prompt_identifier(  # Ask for the required meeting ID.
            "Enter Meeting ID for troubleshootSiteCall (UUID): ",
            "site_search_exporter.troubleshootSiteCall.meeting_id",
        )
        if meeting_id is None:  # The prompt helper already logged the cancellation.
            return
        try:
            logging.info(  # Pre-call log with full context.
                "Calling troubleshootSiteCall for site_id=%s client_mac=%s meeting_id=%s",
                site_id,
                client_mac,
                meeting_id,
            )
            response = mistapi.api.v1.sites.stats.troubleshootSiteCall(  # SDK troubleshoot call.
                mh.apisession, site_id, client_mac, meeting_id
            )
            payload = getattr(response, "data", response)  # Support both object and dict responses.
            rows = SiteSearchExporter._normalize_payload(payload)  # Normalize the payload to rows.
            SiteSearchExporter._persist(  # Persist or report empty through the shared helper.
                rows, site_name, "SiteTroubleshootCall", "troubleshootSiteCall", "call troubleshoot"
            )  # The helper builds the per-site filename from the prefix and site name.
        except Exception as e:  # surface any SDK or network error rather than crashing the menu.
            logging.error("Error fetching call troubleshoot for site %s: %s", site_name, e)  # Failure context.
            logging.info("! Error fetching call troubleshoot data: %s", e)  # ASCII-only user notice.

    @staticmethod
    def _prompt_zone_type() -> str | None:
        """Ask which zone family to search and reject anything outside the two valid values.

        Why:
            ``searchSiteZoneSessions`` puts the zone family in the URL path, so a
            wrong value produces a 404 rather than an empty result. The SDK
            accepts only ``zones`` and ``rssizones``, so the prompt validates
            against that pair before any request goes out.

        Returns:
            The chosen zone type, or None when the operator gave no valid answer.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of InputUtils keeps the import acyclic.
        logging.info("Prompting the operator for the zone type")  # Action log before the prompt.
        answer = str(
            mh.InputUtils.safe_input(  # safe_input enforces EOF-safe prompting.
                "Enter the zone type for searchSiteZoneSessions [zones/rssizones, default zones]: ",
                default_value=_DEFAULT_ZONE_TYPE,  # An empty answer means the common case.
                context="site_search_exporter.searchSiteZoneSessions.zone_type",
            )
        ).strip()
        zone_type = answer or _DEFAULT_ZONE_TYPE  # An empty answer falls back to the default.
        logging.debug("Zone type prompt resolved to %s", zone_type)  # Prompt result trace.
        if zone_type not in _VALID_ZONE_TYPES:  # A wrong value would produce a 404, so stop here.
            logging.error("Invalid zone type %s for searchSiteZoneSessions. Exiting.", zone_type)
            logging.info("! Zone type must be one of: %s", ", ".join(sorted(_VALID_ZONE_TYPES)))
            return None
        return zone_type

    @staticmethod
    def zone_sessions() -> None:
        """Search the zone sessions for a site and export them (menu 229).

        Why:
            This endpoint needs a zone type in the URL path, so it prompts for
            that value before it reaches the shared search helper.
        """
        zone_type = SiteSearchExporter._prompt_zone_type()  # Gather and validate the extra path parameter.
        if zone_type is None:  # The prompt helper already logged the reason.
            return
        SiteSearchExporter._run_site_search(
            mistapi.api.v1.sites.visits.searchSiteZoneSessions,
            "searchSiteZoneSessions",
            f"SiteZoneSessions_{zone_type}",
            "zone session",
            extra_args=(zone_type,),
        )
