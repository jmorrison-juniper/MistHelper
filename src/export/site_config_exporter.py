"""SiteConfigExporter -- site-level WLAN, map, zone, and settings exports.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 19).
Handles site-level WLAN, map, zone, and settings exports.  All methods are
static -- no state is kept on the class.  Callers continue to reach it
through the ``MistHelper.SiteConfigExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper classes without circular load.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw WLAN rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for sites/orgs endpoints.


class SiteConfigExporter:
    """Site Configuration Exporter.

    Handles site-level WLAN, map, zone, and settings exports.
    Extracted from SiteExportUtils.
    """

    @staticmethod
    def _resolve_wlan_site_name(site_id: str) -> str:
        """Look up site name from org's site list, falling back to site_id on failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + apisession.
        try:
            response = mistapi.api.v1.orgs.sites.listOrgSites(  # List org sites.
                mh.apisession,
                mh.ConfigUtils.get_cached_or_prompted_org_id(),
            )
            sites = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page all rows.
            return next((site["name"] for site in sites if site["id"] == site_id), site_id)  # Match → name.
        except Exception as exception:  # Name lookup failed.
            logging.error("Error getting site name for WLAN export: %s", exception)  # Log the error.
            return site_id  # Fall back to id.

    @staticmethod
    def _fetch_wlans_with_fallback(site_id: str) -> list[Any]:
        """Prefer derived WLANs (includes inherited/template); fall back to site-local on failure."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession module global.
        try:
            derived_response = mistapi.api.v1.sites.wlans.listSiteWlansDerived(  # List derived WLANs.
                mh.apisession,
                site_id,
                resolve=True,
            )
            return mistapi.get_all(response=derived_response, mist_session=mh.apisession)  # Page all rows.
        except Exception as exception:  # Derived fetch failed → site-local fallback.
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
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter helpers.
        if not rawdata:  # No rows.
            logging.warning("No data provided for output to %s", filename)  # Warn none.
            mh.DataExporter.write_with_format_selection([], filename)  # Empty CSV.
            print(f"! 0 records exported to data\\{filename}")  # Tell the user zero.
            return  # Done.
        processed = mh.DataProcessingUtils.flatten_nested_fields(rawdata)  # Flatten nested fields.
        processed = mh.DataProcessingUtils.escape_multiline(processed)  # CSV-safe.
        processed = sorted(processed, key=lambda row: row.get("ssid", ""))  # Sort by SSID.
        mh.DataExporter.write_with_format_selection(processed, filename)  # Persist.
        print(f"! {len(processed)} records exported to data\\{filename}")  # Tell the user.
        logging.info("Exported %s WLAN records for site %s to %s", len(processed), site_name, filename)

    @staticmethod
    def wlans(site_id: str | None = None) -> None:
        """Export effective WLANs for a site to SiteWlans.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptUtils helper.
        logging.info("Starting export of site WLANs...")  # Log start.
        if not site_id:  # No site given.
            site_id = mh.PromptUtils.select_site()  # Select a site.
            if not site_id:  # No site.
                logging.error("No site selected. Exiting.")  # Log the error.
                return  # Abort.
        site_name = SiteConfigExporter._resolve_wlan_site_name(site_id)  # Resolve site name.
        filename = f"SiteWlans_{site_name.replace(' ', '_').replace('-', '_')}.csv"  # Build CSV name.
        rawdata = SiteConfigExporter._fetch_wlans_with_fallback(site_id)  # Derived → local fallback.
        SiteConfigExporter._persist_site_wlans_csv(rawdata, filename, site_name)  # Persist (or empty).

    @staticmethod
    def maps() -> None:
        """Export maps for a site to SiteMaps.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of SiteExportUtils._export_data helper.
        mh.SiteExportUtils._export_data(  # Shared export scaffolding handles prompting + CSV write.
            api_call=mistapi.api.v1.sites.maps.listSiteMaps, data_type="maps", sort_key="name"
        )

    @staticmethod
    def zones() -> None:
        """Export zones for a site to SiteZones.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of SiteExportUtils._export_data helper.
        mh.SiteExportUtils._export_data(  # Shared export scaffolding handles prompting + CSV write.
            api_call=mistapi.api.v1.sites.zones.listSiteZones, data_type="zones", sort_key="name"
        )

    @staticmethod
    def settings() -> None:
        """Export configuration settings for all sites to AllSiteConfigs.csv."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of ConfigUtils/APIFetchUtils/DataProcessingUtils/DataExporter + apisession.
        print("Site Configuration Settings:")  # Header.
        logging.info("Starting export of all site configuration settings...")  # Log start.
        current_org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        logging.debug("Using org_id: %s for site settings export.", current_org_id)  # Trace the org.
        data = mh.APIFetchUtils.all_site_settings(mh.apisession, current_org_id, limit=1000)
        if data:  # Have data.
            logging.info("Fetched settings for %s sites. Flattening and sanitizing data...", len(data))
            data = mh.DataProcessingUtils.flatten_nested_fields(data)  # Flatten nested fields.
            data = mh.DataProcessingUtils.escape_multiline(data)  # CSV-safe.
            mh.DataExporter.write_with_format_selection(data, "AllSiteConfigs.csv")  # Persist.
            print(f"! {len(data)} site configurations exported to AllSiteConfigs.csv")  # Tell the user.
            logging.info(" Site configs saved to AllSiteConfigs.csv")  # Log the save.
        else:
            logging.warning(" No site configs found.")  # Warn none found.
            print("! No site configurations found.")  # Tell the user.
