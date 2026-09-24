"""SiteConfigExporter -- site-level WLAN, map, zone, and settings exports.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 19).
Handles site-level WLAN, map, zone, and settings exports.  All methods are
static -- no state is kept on the class.  Callers continue to reach it
through the ``MistHelper.SiteConfigExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import logging  # WHY: structured trace for export lifecycle events.
import os  # WHY: build the operator display path with the separator of the platform.
from typing import Any  # WHY: raw WLAN rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for sites/orgs endpoints.

from src.api.api_fetch_utils import APIFetchUtils  # WHY: 1014 P8 direct import (FR-005).
from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)
from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.export.site_export_utils import SiteExportUtils  # WHY: Pattern 1 inline construction for maps/zones exports.
from src.utils.tqdm_wrapper import tqdm  # WHY: 1015 T-14 -- canonical wrapper import (eliminates mh.tqdm).

logger = logging.getLogger(__name__)  # Use a module logger for non-exception export messages.

_DATA_SUBDIR: str = "data"  # WHY: the output folder that the operator notice names.


class SiteConfigExporter:
    """Site Configuration Exporter.

    Handles site-level WLAN, map, zone, and settings exports.
    Extracted from SiteExportUtils.
    """

    @staticmethod
    def _resolve_wlan_site_name(site_id: str) -> str:
        """Look up site name from org's site list, falling back to site_id on failure."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        try:
            response = mistapi.api.v1.orgs.sites.listOrgSites(  # List org sites.
                mh.apisession,
                mh.ConfigUtils.get_cached_or_prompted_org_id(),
            )
            sites = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            return next((site["name"] for site in sites if site["id"] == site_id), site_id)  # Match → name.
        except RuntimeError as exception:  # Name lookup failed at runtime.
            logging.error("Error getting site name for WLAN export: %s", exception)  # Log the error.
            return site_id  # Fall back to id.

    @staticmethod
    def _fetch_wlans_with_fallback(site_id: str) -> list[Any]:
        """Prefer derived WLANs (includes inherited/template). Fall back to site-local on failure."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        try:
            derived_response = mistapi.api.v1.sites.wlans.listSiteWlansDerived(  # List derived WLANs.
                mh.apisession,
                site_id,
                resolve=True,
            )
            return mistapi.get_all(response=derived_response, mist_session=mh.apisession)  # Page all rows.
        except RuntimeError as exception:  # Derived fetch failed at runtime and needs site-local fallback.
            logging.warning(
                "Failed to fetch derived WLANs for site %s, falling back to site-local WLANs: %s",
                site_id,
                exception,
            )
            local_response = mistapi.api.v1.sites.wlans.listSiteWlans(mh.apisession, site_id, limit=1000)
            return mistapi.get_all(response=local_response, mist_session=mh.apisession)  # Page all rows.

    @staticmethod
    def _persist_site_wlans_csv(rawdata: list[Any], filename: str, site_name: str) -> None:
        """Flatten + sort by SSID + write WLAN rows (or write empty CSV when none)."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        display_path = os.path.join(_DATA_SUBDIR, filename)  # WHY: name the file with the platform separator.
        if not rawdata:  # No rows.
            logger.warning("No data provided for output to %s", filename)  # Warn none.
            mh.DataExporter.write_with_format_selection([], filename, api_function_name="listSiteWlans")  # Empty CSV.
            logger.info("! 0 records exported to %s", display_path)  # WHY: operator notice for the empty file.
            return  # Done.
        logger.info("Writing %s WLAN records for site %s", len(rawdata), site_name)  # WHY: log before the write.
        processed = DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
        processed = DataProcessingUtils.escape_multiline(processed)  # CSV-safe.
        processed = sorted(processed, key=lambda row: row.get("ssid", ""))  # Sort by SSID.
        mh.DataExporter.write_with_format_selection(processed, filename, api_function_name="listSiteWlans")  # Persist.
        logger.info("! %s records exported to %s", len(processed), display_path)  # WHY: operator record-count notice.
        logger.info(
            "Exported %s WLAN records for site %s to %s", len(processed), site_name, filename
        )  # WHY: audit line that names the site.

    @staticmethod
    def wlans(site_id: str | None = None) -> None:
        """Export effective WLANs for a site to SiteWlans.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Starting export of site WLANs...")  # Log start.
        if not site_id:  # No site given.
            site_id = mh.PromptUtils.select_site()  # Select a site.
            if not site_id:  # No site.
                logger.error("No site selected. Exiting.")  # Log the error.
                return  # Abort.
        site_name = SiteConfigExporter._resolve_wlan_site_name(site_id)  # Resolve site name.
        filename = f"SiteWlans_{site_name.replace(' ', '_').replace('-', '_')}.csv"  # Build CSV name.
        rawdata = SiteConfigExporter._fetch_wlans_with_fallback(site_id)  # Derived → local fallback.
        SiteConfigExporter._persist_site_wlans_csv(rawdata, filename, site_name)  # Persist (or empty).

    @staticmethod
    def maps() -> None:
        """Export maps for a site to SiteMaps.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
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
            api_call=mistapi.api.v1.sites.maps.listSiteMaps, data_type="maps", sort_key="name"
        )

    @staticmethod
    def zones() -> None:
        """Export zones for a site to SiteZones.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
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
            api_call=mistapi.api.v1.sites.zones.listSiteZones, data_type="zones", sort_key="name"
        )

    @staticmethod
    def settings() -> None:
        """Export configuration settings for all sites to AllSiteConfigs.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        # WHY: Preserve user-facing banner verbatim.
        logger.info("Site Configuration Settings:")
        logger.info("Starting export of all site configuration settings...")  # Log start.
        current_org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        logger.debug("Using org_id: %s for site settings export.", current_org_id)  # Trace the org.
        data = APIFetchUtils.all_site_settings(mh.apisession, current_org_id, limit=1000)
        if data:  # Have data.
            logger.info("Fetched settings for %s sites. Flattening and sanitizing data...", len(data))
            data = DataProcessingUtils.flatten_nested_fields(data)  # Flatten nested fields.
            data = DataProcessingUtils.escape_multiline(data)  # CSV-safe.
            mh.DataExporter.write_with_format_selection(
                data, "AllSiteConfigs.csv", api_function_name="listSiteSettings"
            )  # Persist.
            # WHY: Preserve user-facing record-count notice verbatim.
            logger.info("! %s site configurations exported to AllSiteConfigs.csv", len(data))
            logger.info(" Site configs saved to AllSiteConfigs.csv")  # Log the save.
        else:
            logger.warning(" No site configs found.")  # Warn none found.
            # WHY: Preserve user-facing empty-result notice verbatim.
            logger.warning("! No site configurations found.")
