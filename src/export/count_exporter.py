"""CountExporter -- org, site, and MSP count-endpoint exports.

Added for issue #1802, which covers the 67 open count-endpoint issues as one
family instead of one operation each. Every Mist count endpoint shares a shape:
it takes an org, site, or MSP identifier plus an optional ``distinct`` field,
and returns a count distribution rather than a record list.

Covered menus:
    - Org counts (menu 235) -- any org-scoped ``count*`` operation.
    - Site counts (menu 236) -- any site-scoped ``count*`` operation.
    - MSP counts (menu 237) -- any MSP-scoped ``count*`` operation.

Why:
    Shipping one menu entry per endpoint would add 67 rows to ``menu_actions``,
    taking it from 235 to 302. The operator would scroll past 67 near-identical
    lines. One entry per scope keeps the menu readable and puts the choice in a
    prompt, where the operator can see the operations grouped together.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the project toolchain.

import importlib  # WHY: lazy MistHelper import avoids a circular load at module init.
import logging  # WHY: structured trace for export lifecycle events.
from dataclasses import dataclass  # WHY: the operation table needs a named, frozen row type.
from typing import Any  # WHY: raw count rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for every count operation.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: canonical flatten and escape helpers keep CSV output consistent with peers.
from src.utils.input_utils import InputUtils  # WHY: the shared, EOF-safe MSP identifier prompt.


@dataclass(frozen=True)
class _CountOp:
    """One count operation: its operationId, its SDK module path, and its scope."""

    operation: str  # The Mist operationId, used for the primary-key strategy lookup.
    module: str  # The dotted SDK module that defines the callable.


# Grouped by scope so each menu entry offers only the operations it can run.
# The names were resolved against the installed SDK, not against the spec text,
# because 245 endpoint specs name a module path that does not exist (issue #1757).
_ORG_OPS: tuple[_CountOp, ...] = (
    _CountOp("countOrgAlarms", "mistapi.api.v1.orgs.alarms"),
    _CountOp("countOrgAssetsByDistanceField", "mistapi.api.v1.orgs.stats"),
    _CountOp("countOrgAuditLogs", "mistapi.api.v1.orgs.logs"),
    _CountOp("countOrgBgpStats", "mistapi.api.v1.orgs.stats"),
    _CountOp("countOrgDeviceEvents", "mistapi.api.v1.orgs.devices"),
    _CountOp("countOrgDeviceLastConfigs", "mistapi.api.v1.orgs.devices"),
    _CountOp("countOrgDevices", "mistapi.api.v1.orgs.devices"),
    _CountOp("countOrgGuestAuthorizations", "mistapi.api.v1.orgs.guests"),
    _CountOp("countOrgInventory", "mistapi.api.v1.orgs.inventory"),
    _CountOp("countOrgJsiAssetsAndContracts", "mistapi.api.v1.orgs.jsi"),
    _CountOp("countOrgJsiPbn", "mistapi.api.v1.orgs.jsi"),
    _CountOp("countOrgJsiSirt", "mistapi.api.v1.orgs.jsi"),
    _CountOp("countOrgMarvisClientEvents", "mistapi.api.v1.orgs.marvisclients"),
    _CountOp("countOrgMarvisClientsStats", "mistapi.api.v1.orgs.stats"),
    _CountOp("countOrgMxEdges", "mistapi.api.v1.orgs.mxedges"),
    _CountOp("countOrgNacClientEvents", "mistapi.api.v1.orgs.nac_clients"),
    _CountOp("countOrgNacClients", "mistapi.api.v1.orgs.nac_clients"),
    _CountOp("countOrgOspfStats", "mistapi.api.v1.orgs.stats"),
    _CountOp("countOrgOtherDeviceEvents", "mistapi.api.v1.orgs.otherdevices"),
    _CountOp("countOrgPeerPathStats", "mistapi.api.v1.orgs.stats"),
    _CountOp("countOrgPskPortalLogs", "mistapi.api.v1.orgs.pskportals"),
    _CountOp("countOrgSiteMxEdgeEvents", "mistapi.api.v1.orgs.mxedges"),
    _CountOp("countOrgSites", "mistapi.api.v1.orgs.sites"),
    _CountOp("countOrgSwOrGwPorts", "mistapi.api.v1.orgs.stats"),
    _CountOp("countOrgSystemEvents", "mistapi.api.v1.orgs.events"),
    _CountOp("countOrgTickets", "mistapi.api.v1.orgs.tickets"),
    _CountOp("countOrgTunnelsStats", "mistapi.api.v1.orgs.stats"),
    _CountOp("countOrgUserMacs", "mistapi.api.v1.orgs.usermacs"),
    _CountOp("countOrgWanClientEvents", "mistapi.api.v1.orgs.wan_client"),
    _CountOp("countOrgWanClients", "mistapi.api.v1.orgs.wan_clients"),
    _CountOp("countOrgWebhooksDeliveries", "mistapi.api.v1.orgs.webhooks"),
    _CountOp("countOrgWiredClients", "mistapi.api.v1.orgs.wired_clients"),
    _CountOp("countOrgWirelessClientEvents", "mistapi.api.v1.orgs.clients"),
    _CountOp("countOrgWirelessClients", "mistapi.api.v1.orgs.clients"),
    _CountOp("countOrgWirelessClientsSessions", "mistapi.api.v1.orgs.clients"),
)

_SITE_OPS: tuple[_CountOp, ...] = (
    _CountOp("countSiteAlarms", "mistapi.api.v1.sites.alarms"),
    _CountOp("countSiteApps", "mistapi.api.v1.sites.stats"),
    _CountOp("countSiteAssets", "mistapi.api.v1.sites.stats"),
    _CountOp("countSiteBgpStats", "mistapi.api.v1.sites.stats"),
    _CountOp("countSiteCalls", "mistapi.api.v1.sites.stats"),
    _CountOp("countSiteClientFingerprints", "mistapi.api.v1.sites.insights"),
    _CountOp("countSiteDeviceConfigHistory", "mistapi.api.v1.sites.devices"),
    _CountOp("countSiteDeviceEvents", "mistapi.api.v1.sites.devices"),
    _CountOp("countSiteDeviceLastConfig", "mistapi.api.v1.sites.devices"),
    _CountOp("countSiteDevices", "mistapi.api.v1.sites.devices"),
    _CountOp("countSiteDiscoveredSwitches", "mistapi.api.v1.sites.stats"),
    _CountOp("countSiteGuestAuthorizations", "mistapi.api.v1.sites.guests"),
    _CountOp("countSiteMarvisConfigActions", "mistapi.api.v1.sites.marvis_configs"),
    _CountOp("countSiteMxEdgeEvents", "mistapi.api.v1.sites.mxedges"),
    _CountOp("countSiteNacClientEvents", "mistapi.api.v1.sites.nac_clients"),
    _CountOp("countSiteNacClients", "mistapi.api.v1.sites.nac_clients"),
    _CountOp("countSiteOspfStats", "mistapi.api.v1.sites.stats"),
    _CountOp("countSiteOtherDeviceEvents", "mistapi.api.v1.sites.otherdevices"),
    _CountOp("countSiteRogueEvents", "mistapi.api.v1.sites.rogues"),
    _CountOp("countSiteServicePathEvents", "mistapi.api.v1.sites.services"),
    _CountOp("countSiteSkyatpEvents", "mistapi.api.v1.sites.skyatp"),
    _CountOp("countSiteSwOrGwPorts", "mistapi.api.v1.sites.stats"),
    _CountOp("countSiteSystemEvents", "mistapi.api.v1.sites.events"),
    _CountOp("countSiteWanClientEvents", "mistapi.api.v1.sites.wan_client"),
    _CountOp("countSiteWanClients", "mistapi.api.v1.sites.wan_clients"),
    _CountOp("countSiteWanUsage", "mistapi.api.v1.sites.wan_usages"),
    _CountOp("countSiteWebhooksDeliveries", "mistapi.api.v1.sites.webhooks"),
    _CountOp("countSiteWiredClients", "mistapi.api.v1.sites.wired_clients"),
    _CountOp("countSiteWirelessClientEvents", "mistapi.api.v1.sites.clients"),
    _CountOp("countSiteWirelessClientSessions", "mistapi.api.v1.sites.clients"),
    _CountOp("countSiteWirelessClients", "mistapi.api.v1.sites.clients"),
    _CountOp("countSiteZoneSessions", "mistapi.api.v1.sites.count"),
)

_MSP_OPS: tuple[_CountOp, ...] = (
    _CountOp("countMspAuditLogs", "mistapi.api.v1.msps.logs"),
    _CountOp("countMspTickets", "mistapi.api.v1.msps.tickets"),
    _CountOp("countMspsMarvisActions", "mistapi.api.v1.msps.suggestion"),
)


class CountExporter:
    """Exporter for every Mist count endpoint, grouped by scope.

    Why:
        One class covers 70 operations that differ only by name, module, and the
        identifier they need. Static methods only, with no per-instance state,
        matching the pattern that ``SiteAssetExporter`` established.
    """

    @staticmethod
    def _resolve(operation: _CountOp) -> Any:
        """Return the SDK callable for one operation, or None when it is absent.

        Why:
            The table is written by hand, so a typo or an SDK upgrade must fail
            loudly at the point of use rather than crash the menu.
        """
        try:
            module = importlib.import_module(operation.module)  # Load the SDK module lazily.
        except ImportError:  # The SDK moved or dropped the module between releases.
            logging.error("SDK module %s is not importable", operation.module)  # Name the gap.
            return None
        callable_obj = getattr(module, operation.operation, None)  # Fetch the operation function.
        if callable_obj is None:  # The module exists but no longer defines this operation.
            logging.error("SDK module %s does not define %s", operation.module, operation.operation)  # Name the gap.
        return callable_obj

    @staticmethod
    def _choose(operations: tuple[_CountOp, ...], scope_label: str) -> _CountOp | None:
        """Prompt the operator to pick one operation from the scope's table.

        Why:
            One menu entry per scope keeps ``menu_actions`` small. The choice
            moves into a prompt, which also lets the operator see the related
            operations side by side.

        Args:
            operations: The operations offered for this scope, in table order.
            scope_label: The noun shown in the prompt, for example ``org``.

        Returns:
            The chosen operation, or None when the operator declines.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch keeps the import acyclic.
        logging.info("Offering %d %s count operations", len(operations), scope_label)  # Pre-prompt log.
        for index, operation in enumerate(operations, start=1):  # Number the rows from one.
            print(f"  [{index}] {operation.operation}")  # Operator-facing choice row.
        answer = str(  # WHY: the lazy module attribute is untyped, so pin the declared str return.
            mh.InputUtils.safe_input(
                f"Select a {scope_label} count operation (1-{len(operations)}): ",
                allow_empty=False,  # An empty answer cannot select an operation.
                context=f"count_exporter.{scope_label}.selection",
            )
        ).strip()
        logging.debug("Operator answered %r for the %s selection", answer, scope_label)  # Answer trace.
        if not answer.isdigit():  # A non-numeric answer, an EOF, or an interrupt aborts.
            logging.info("! No operation selected. Returning to the menu.")  # User-facing cancel.
            return None
        position = int(answer)  # Convert once the value is known to be all digits.
        if not 1 <= position <= len(operations):  # Guard the table bounds before indexing.
            logging.error("Selection %d is outside 1-%d", position, len(operations))  # Bound breach.
            logging.info("! That number is not on the list. Returning to the menu.")  # User notice.
            return None
        return operations[position - 1]  # Menu rows are one-based, the tuple is zero-based.

    @staticmethod
    def _persist(rawdata: list[Any], filename: str, operation: str) -> None:
        """Flatten and persist count rows, or report that the endpoint returned none.

        Why:
            An empty count response is legitimate, for example an org with no
            alarms. We report it plainly so scheduled runs stay quiet.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the DataExporter helper.
        if not rawdata:  # No rows, so inform the operator and return.
            logging.info("! No %s data found", operation)  # ASCII-only user notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten for CSV.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # Make CSV-safe.
        mh.DataExporter.write_with_format_selection(  # Persist through the shared selector.
            sanitized_data, filename, api_function_name=operation
        )
        logging.debug("%s persisted %d rows to %s", operation, len(rawdata), filename)  # Post-call count.
        logging.info("! %d %s records exported to %s", len(rawdata), operation, filename)  # User notice.

    @staticmethod
    def _run(operation: _CountOp, identifier: str, label: str) -> None:
        """Call one count operation for one identifier and persist the result.

        Why:
            Every count operation takes the same two positional arguments, so a
            single caller covers all 70.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession.
        callable_obj = CountExporter._resolve(operation)  # Resolve the SDK function.
        if callable_obj is None:  # The resolver already logged which part was missing.
            logging.info("! %s is unavailable in this SDK version.", operation.operation)  # Notice.
            return
        try:
            logging.info("Calling %s for %s", operation.operation, identifier)  # Pre-call log.
            response = callable_obj(mh.apisession, identifier)  # Every count takes session + id.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            filename = f"{operation.operation}_{label.replace(' ', '_')}.csv"  # Per-target filename.
            CountExporter._persist(rawdata, filename, operation.operation)  # Write the result.
        except Exception as e:  # surface any SDK or network error, keep the menu alive.
            logging.error("Error running %s for %s: %s", operation.operation, label, e)  # Context.
            logging.info("! Error running %s: %s", operation.operation, e)  # ASCII-only user notice.

    @staticmethod
    def org_counts() -> None:
        """Run any org-scoped count operation (menu 235)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the org resolver.
        logging.info("Org Counts:")  # Menu header echoed to the operator.
        operation = CountExporter._choose(_ORG_OPS, "org")  # Ask which count to run.
        if operation is None:  # The chooser already logged the cancellation.
            return
        org_id = str(mh.ConfigUtils.get_cached_or_prompted_org_id())  # Reuse the shared org resolver.
        if not org_id:  # No org means no call is possible.
            logging.info("! No org selected. Returning to the menu.")  # User-facing cancel.
            return
        CountExporter._run(operation, org_id, org_id)  # Execute and persist.

    @staticmethod
    def site_counts() -> None:
        """Run any site-scoped count operation (menu 236)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of the shared site resolver.
        logging.info("Site Counts:")  # Menu header echoed to the operator.
        operation = CountExporter._choose(_SITE_OPS, "site")  # Ask which count to run.
        if operation is None:  # The chooser already logged the cancellation.
            return
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats("site counts")  # Shared site prompt.
        if resolved is None:  # The operator declined, and the helper already logged the reason.
            return
        site_id, site_name = resolved  # Unpack the resolved identifiers for the API call.
        CountExporter._run(operation, site_id, site_name)  # Execute and persist.

    @staticmethod
    def msp_counts() -> None:
        """Run any MSP-scoped count operation (menu 237)."""
        logging.info("MSP Counts:")  # Menu header echoed to the operator.
        operation = CountExporter._choose(_MSP_OPS, "msp")  # Ask which count to run.
        if operation is None:  # The chooser already logged the cancellation.
            return
        msp_id = InputUtils.prompt_msp_id()  # MSP identifiers have no cached resolver.
        if msp_id is None:  # The prompt helper already logged the cancellation.
            return
        CountExporter._run(operation, msp_id, msp_id)  # Execute and persist.
