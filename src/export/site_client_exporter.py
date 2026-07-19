"""SiteClientExporter -- site-level client/beacon/wifi export operations.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 14).
Handles site-level client data, WiFi clients, and beacon exports.  All methods
are static -- no state is kept on the class.  Callers continue to reach it
through the ``MistHelper.SiteClientExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper classes without circular load.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw client rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for listSiteWirelessClientsStats + beacons endpoints.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.export.site_export_utils import SiteExportUtils  # WHY: Pattern 1 inline construction for beacons export.
from src.export.wan_client_events_exporter import (
    WanClientEventsExporter,
)  # WHY: spec 899 / issue #1407 -- delegate WAN client event search to dedicated exporter.
from src.export.wifi_clients_exporter import WifiClientsExporter  # Extracted WiFi export orchestrator.
from src.utils.tqdm_wrapper import (
    tqdm,
)  # WHY: 1015 T-14 -- import directly from canonical wrapper (eliminates mh.tqdm).


class SiteClientExporter:
    """Site Client Data Exporter.

    Handles site-level client data, WiFi clients, and beacon exports.
    Extracted from SiteExportUtils.
    """

    @staticmethod
    def _persist_site_clients(rawdata: list[Any], site_name: str) -> None:
        """Flatten + persist site-clients rows to a per-site CSV (or tell the user when empty)."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter helpers.
        if not rawdata:  # No clients -- tell the user and return.
            print("! No client data found for this site")  # User notice.
            return
        flattened_data = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
        sanitized_data = DataProcessingUtils.escape_multiline(flattened_data)  # CSV-safe.
        filename = f"SiteClients_{site_name.replace(' ', '_')}.csv"  # Per-site CSV name.
        mh.DataExporter.write_with_format_selection(sanitized_data, filename)  # Persist.
        print(f"! {len(rawdata)} client records exported to {filename}")  # User notice with count.

    @staticmethod
    def clients() -> None:
        """Export client data for a site to SiteClients.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of SiteDeviceExporter + apisession module global.
        print("Site Client Statistics:")  # Header.
        logging.info("Starting export of site client statistics...")  # Trace start.
        resolved = mh.SiteDeviceExporter._resolve_site_for_stats(  # Prompt + org/site resolution (shared).
            "client statistics"
        )
        if resolved is None:  # Abort signaled by resolver.
            return
        site_id, site_name = resolved  # Unpack resolved identifiers.
        try:
            response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(mh.apisession, site_id, limit=1000)
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            SiteClientExporter._persist_site_clients(rawdata, site_name)  # Persist or tell user empty.
        except Exception as e:  # Fetch failed.
            logging.error("Error fetching client stats for site %s: %s", site_name, e)  # Log the error.
            print(f"! Error fetching client data: {e}")  # Tell the user.

    @staticmethod
    def client_insights() -> None:
        """Delegated site client insights entrypoint preserved for compatibility."""
        # WHY: local import keeps the serial_cc service optional at module-load time.
        from src.refactors.serial_cc.site_client_insights import SiteClientInsightsService

        SiteClientInsightsService.execute()  # Run the insights export.

    @staticmethod
    def _normalize_client_mac_or_none(client_mac: str) -> str | None:
        """Validate and normalize client MAC for site insights endpoints."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PacketCaptureManager helper.
        if not client_mac:  # Empty input.
            return None
        if not mh.PacketCaptureManager.validate_mac_address(client_mac):  # Invalid MAC.
            return None
        return mh.PacketCaptureManager.normalize_mac_address(client_mac)  # Normalized MAC.

    @staticmethod
    def wifi_clients(site_id: str | None = None) -> None:
        """Compatibility facade that delegates WiFi client export to extracted exporter."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live helper globals + apisession.
        logging.info(
            "Delegating wifi_clients to WifiClientsExporter"
        )  # Log before constructing extracted exporter dependencies.
        exporter = WifiClientsExporter(  # Preserve existing utility wiring to avoid behavior drift.
            cache_utils=mh.CacheUtils,
            org_site_exporter=mh.OrgSiteExporter,
            prompt_utils=mh.PromptUtils,
            file_path_utils=mh.FilePathUtils,
            data_processing_utils=DataProcessingUtils,
            data_exporter=mh.DataExporter,
            mistapi_module=mistapi,
            apisession=mh.apisession,
        )
        logging.debug(
            "Initialized WifiClientsExporter for site_id=%s", site_id
        )  # Log exporter construction completion.
        exporter.execute(site_id=site_id)  # Delegate export execution while preserving facade signature.
        logging.debug("Completed delegated wifi_clients export workflow")  # Log delegated exporter completion.

    @staticmethod
    def wan_client_events(site_id: str | None = None) -> None:
        """Facade delegating WAN client event search to :class:`WanClientEventsExporter`.

        Why:
            Spec 899 / issue #1407 registers a new menu item that surfaces
            ``mistapi.api.v1.sites.wan_clients.events.search.searchSiteWanClientEvents``.
            Keeping the delegation shape identical to :meth:`wifi_clients`
            preserves the SiteClientExporter facade pattern and avoids
            leaking dataclass wiring into ``MistHelper.py``'s menu dict.

        Args:
            site_id: Optional preselected site UUID; ``None`` prompts the
                operator for a site via the injected ``PromptUtils``.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of MistHelper globals to avoid circular import.
        logging.info(
            "Delegating wan_client_events to WanClientEventsExporter"
        )  # WHY: trace facade dispatch for the WAN client event exporter.
        exporter = WanClientEventsExporter(  # WHY: build orchestrator with the same injected deps used by wifi_clients.
            cache_utils=mh.CacheUtils,  # WHY: reuse cached site-name resolver so we skip a redundant listSites call.
            org_site_exporter=mh.OrgSiteExporter,  # WHY: shared site-list emitter feeds the CSV cache fallback lookup.
            prompt_utils=mh.PromptUtils,  # WHY: interactive site selection mirrors sibling site exporters.
            file_path_utils=mh.FilePathUtils,  # WHY: shared SiteList.csv discovery keeps behavior consistent.
            data_processing_utils=DataProcessingUtils,  # WHY: canonical flatten/escape helper for CSV safety.
            data_exporter=mh.DataExporter,  # WHY: multi-backend writer via write_with_format_selection.
            mistapi_module=mistapi,  # WHY: SDK module hosting the wan_clients.events.search endpoint + get_all pager.
            apisession=mh.apisession,  # WHY: authenticated mistapi session shared across all menu actions.
        )
        logging.debug(
            "Initialized WanClientEventsExporter for site_id=%s", site_id
        )  # WHY: capture construction for diagnostics.
        exporter.execute(site_id=site_id)  # WHY: run the fetch + persist pipeline defined by the extracted exporter.
        logging.debug(
            "Completed delegated wan_client_events export workflow"
        )  # WHY: mark facade completion for log timeline correlation.

    @staticmethod
    def beacons() -> None:
        """Export beacons for a site to SiteBeacons.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: fetch live dep symbols for SiteExportUtils construction.
        SiteExportUtils(
            apisession=mh.apisession,
            PromptUtils=mh.PromptUtils,
            ConfigUtils=mh.ConfigUtils,
            DataProcessingUtils=DataProcessingUtils,
            DataExporter=mh.DataExporter,
            TimeUtils=mh.TimeUtils,
            EnhancedSSHRunner=mh.EnhancedSSHRunner,
            InsightMetricsUtils=mh.InsightMetricsUtils,
            PacketCaptureManager=mh.PacketCaptureManager,
            APICoreFetchUtils=mh.APICoreFetchUtils,
            check_fn=mh.IsDebugMode.check,
            PrettyTable=mh.PrettyTable,
            tqdm=tqdm,  # 1015 T-14: canonical import from src.utils.tqdm_wrapper (no mh.* reach-back).
            mistapi=mh.mistapi,
        )._export_data(  # Shared export scaffolding handles prompting + CSV write.
            api_call=mistapi.api.v1.sites.beacons.listSiteBeacons, data_type="beacons", sort_key="name"
        )
