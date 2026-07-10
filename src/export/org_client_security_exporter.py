"""OrgClientSecurityExporter -- org wireless/wired client + rogue + security exporters.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 32).
Backs menu options 24 (security events), 27 (wireless clients), 28 (wired clients),
29 (rogue clients), 30 (rogue APs). Direct imports cover stdlib + installed
packages (mistapi, tqdm). Live-global reads (``apisession``, ``OrgExportUtils``,
``TimeUtils``, ``CacheUtils``, ``OrgSiteExporter``, ``FilePathUtils``,
``CSV_FRESHNESS_MINUTES``, ``ConfigUtils``, ``DataProcessingUtils``,
``DataExporter``) are resolved via lazy ``mh = importlib.import_module("MistHelper")``
inside each helper. Callers continue to reach the class through the
``MistHelper.OrgClientSecurityExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import csv  # WHY: parse cached SiteList.csv into dict rows.
import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for rogue export lifecycle events.
import os  # WHY: file existence + mtime check for fast-mode cache freshness.
import time  # WHY: compute cache age vs freshness window.
from typing import Any  # WHY: mistapi response payloads + site rows are duck-typed here.

import mistapi  # WHY: direct calls to orgs.clients + sites.insights list endpoints + get_all pager.
from tqdm import tqdm  # WHY: per-site progress bar for rogue fan-out.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.time.time_utils import TimeUtils  # WHY: 1014 P6 direct import (FR-005).


class OrgClientSecurityExporter:
    """Organization Client and Security Exporter.

    Handles wireless/wired client data and security event exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def wireless_clients() -> None:  # Export wireless client security.
        """Export wireless client statistics for the entire organization to OrgWirelessClients.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils facade.
        mh.OrgExportUtils.export_data(
            api_call=mistapi.api.v1.orgs.clients.searchOrgWirelessClients, data_type="wireless clients", sort_key="mac"
        )

    @staticmethod
    def wired_clients() -> None:  # Export wired client security.
        """Export wired client statistics for the entire organization to OrgWiredClients.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils facade.
        mh.OrgExportUtils.export_data(
            api_call=mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients,
            data_type="wired clients",
            sort_key="mac",
        )

    @staticmethod
    def security_events(fast: bool = False) -> None:
        """Export security policies, intelligence profiles, and rogue data.

        Fast Mode Behavior:
            - Cache hit: If all 3 output CSVs exist and are fresh, skip entirely.
            - Reduced lookback: Uses dynamic lookback (1h in test) instead of hardcoded 7d.
        """
        from src.refactors.serial_cc.security_events import SecurityEventsService  # noqa: PLC0415

        SecurityEventsService.execute(fast)  # Run the security export.

    @staticmethod
    def rogue_clients(fast: bool = False) -> None:
        """Export rogue clients to OrgRogueClients.csv with fast-mode cache reuse."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CacheUtils/OrgSiteExporter.
        output_file = "OrgRogueClients.csv"  # Destination CSV for this export
        if OrgClientSecurityExporter._check_csv_cache_fresh(output_file, fast):  # Fast-mode cache hit short-circuits
            return  # Skip the API calls entirely
        logging.info("Starting export of rogue clients from all sites...")  # Log the start of the export
        lookback_hours = TimeUtils.get_dynamic_lookback_hours(168, 1)  # 7 days normally, 1 hour in test mode
        rogue_duration = f"{lookback_hours}h"  # Format the lookback as the API's duration string
        TimeUtils.log_dynamic_lookback("rogue clients fetch", lookback_hours)  # Log which lookback window is used
        mh.CacheUtils.check_and_generate_csv(
            "SiteList.csv", mh.OrgSiteExporter.sites
        )  # Ensure site list CSV is current
        rogues = OrgClientSecurityExporter._collect_rogues_across_sites(
            mistapi.api.v1.sites.insights.listSiteRogueClients,  # Per-site rogue-clients API endpoint
            rogue_duration,
            "rogue clients",
        )  # Fan out to every site
        if rogues is None:  # Iterating the site list failed
            return  # Abort the export
        OrgClientSecurityExporter._export_rogues(rogues, "OrgRogueClients", "rogue clients")  # Write the CSV

    @staticmethod
    def rogue_aps(fast: bool = False) -> None:
        """Export rogue APs to OrgRogueAPs.csv with fast-mode cache reuse."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of CacheUtils/OrgSiteExporter.
        output_file = "OrgRogueAPs.csv"  # Destination CSV for this export
        if OrgClientSecurityExporter._check_csv_cache_fresh(output_file, fast):  # Fast-mode cache hit short-circuits
            return  # Skip the API calls entirely
        logging.info("Starting export of rogue APs from all sites...")  # Log the start of the export
        lookback_hours = TimeUtils.get_dynamic_lookback_hours(168, 1)  # 7 days normally, 1 hour in test mode
        rogue_duration = f"{lookback_hours}h"  # Format the lookback as the API's duration string
        TimeUtils.log_dynamic_lookback("rogue APs fetch", lookback_hours)  # Log which lookback window is used
        mh.CacheUtils.check_and_generate_csv(
            "SiteList.csv", mh.OrgSiteExporter.sites
        )  # Ensure site list CSV is current
        rogues = OrgClientSecurityExporter._collect_rogues_across_sites(
            mistapi.api.v1.sites.insights.listSiteRogueAPs,  # Per-site rogue-APs API endpoint
            rogue_duration,
            "rogue APs",
        )  # Fan out to every site
        if rogues is None:  # Iterating the site list failed
            return  # Abort the export
        OrgClientSecurityExporter._export_rogues(rogues, "OrgRogueAPs", "rogue APs")  # Write the CSV

    @staticmethod
    def _check_csv_cache_fresh(output_file: str, fast: bool) -> bool:
        """Return True when fast-mode is on AND a CSV named output_file exists within the freshness window."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils + CSV_FRESHNESS_MINUTES.
        if not fast:  # Cache check only matters in fast mode
            return False  # Force a fresh fetch in normal mode
        try:
            path = mh.FilePathUtils.get_csv_path(output_file)  # Resolve the cached file path
            if not os.path.exists(path):  # No prior export to reuse
                return False  # Fall through to fetch
            age_minutes = (time.time() - os.path.getmtime(path)) / 60.0  # File age in minutes
            if age_minutes >= mh.CSV_FRESHNESS_MINUTES:  # Cached file is stale
                logging.debug("Cache for %s is stale (%.1fm)", output_file, age_minutes)  # Trace staleness
                return False  # Force a fresh fetch
            logging.info(
                "Fast mode cache hit: %s is fresh (%.1fm); skipping fetch.", output_file, age_minutes
            )  # Log the cache hit
            print(f"* Fast mode: Using cached {output_file} (age {age_minutes:.1f}m)")  # Inform user
            return True  # Cache hit short-circuits the orchestrator
        except Exception as cache_error:  # Inspecting the cache failed
            logging.debug("Fast mode freshness check failed for %s: %s", output_file, cache_error)  # Trace
            return False  # Fall through to fetch on any cache error

    @staticmethod
    def _load_site_list() -> list[dict[str, Any]] | None:
        """Load the cached SiteList.csv into a list of dict rows, or None when reading the CSV fails."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils facade.
        site_list_path = mh.FilePathUtils.get_csv_path("SiteList.csv")  # Resolve the site list CSV path
        try:
            with open(site_list_path, encoding="utf-8") as f:  # Open the cached site list
                rows = list(csv.DictReader(f))  # Read all sites as dictionaries
            logging.debug("Loaded %s sites from SiteList.csv", len(rows))  # Trace site count
            return rows  # Return the loaded rows
        except Exception as e:  # Failure reading the cached site list
            logging.error("Failed to process sites for rogue export: %s", e)  # Log the broader failure
            return None  # Signal caller to abort

    @staticmethod
    def _fetch_rogues_for_one_site(
        fetch_callable: Any, site_id: str, site_name: str, rogue_duration: str, label: str
    ) -> list[dict[str, Any]]:
        """Fetch one site's rogue entries (clients or APs) and tag each with site_id and site_name."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        try:
            response = fetch_callable(
                mh.apisession, site_id, duration=rogue_duration, limit=1000
            )  # Request this site's rogues
            rogues = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all results
            for rogue in rogues:  # Tag each rogue with site context
                rogue["site_id"] = site_id  # Record which site detected it
                rogue["site_name"] = site_name  # Record the site name for readability
            logging.info("! Fetched %s %s from site: %s", len(rogues), label, site_name)  # Per-site summary
            return rogues  # type: ignore[no-any-return]  # Return the tagged list
        except Exception as e:  # This site's fetch failed
            logging.warning("! Failed to fetch %s from site %s: %s", label, site_name, e)  # Warn but keep going
            return []  # Empty result lets the aggregator continue with the next site

    @staticmethod
    def _collect_rogues_across_sites(
        fetch_callable: Any, rogue_duration: str, label: str
    ) -> list[dict[str, Any]] | None:
        """Aggregate rogue entries (clients or APs) across every site, returning None if the site list fails."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils facade.
        sites = OrgClientSecurityExporter._load_site_list()  # Read SiteList.csv into rows
        if sites is None:  # Failure reading the cached site list
            return None  # Signal caller to abort
        aggregate: list[dict[str, Any]] = []  # Accumulate rogues across all sites
        for site in tqdm(sites, desc="Sites", unit="site"):  # Iterate with progress bar
            if mh.ConfigUtils.check_stop_signal():  # The user requested an early stop
                break  # Exit the loop gracefully
            site_id = site.get("id")  # The site's unique ID
            site_name = site.get("name", "Unknown Site")  # The site's display name
            if not site_id:  # Defensive: skip rows missing an ID
                continue  # Move to the next site
            site_rogues = OrgClientSecurityExporter._fetch_rogues_for_one_site(
                fetch_callable, site_id, site_name, rogue_duration, label
            )  # Fetch this site's rogues
            aggregate.extend(site_rogues)  # Add this site's rogues to the aggregate
        return aggregate  # Return the cross-site list

    @staticmethod
    def _export_rogues(rogues: list[dict[str, Any]], csv_basename: str, label: str) -> None:
        """Flatten + escape + write the aggregated rogue list, or report the empty-result case."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataProcessingUtils + DataExporter.
        if rogues:  # At least one rogue was found
            flattened = DataProcessingUtils.flatten_nested_fields(rogues)  # Flatten nested JSON to CSV rows
            sanitized = DataProcessingUtils.escape_multiline(flattened)
            mh.DataExporter.write_with_format_selection(sanitized, csv_basename)
            logging.info("! %s %s exported to %s", len(rogues), label, csv_basename)  # Log the export
            print(f"! {len(rogues)} {label} exported to {csv_basename}")  # Report the count to the user
        else:  # No rogues found anywhere
            logging.info("No %s found across all sites", label)  # Log the empty result
            print(f" No {label} detected across all sites")  # Inform the user
