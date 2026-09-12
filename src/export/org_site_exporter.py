"""OrgSiteExporter -- org-level site listings and guest exports.

Extracted from MistHelper.py during initiative 1014 (Cat E, position 9).
Canonical body lives here; MistHelper.py provides a top-level re-export
alias (``from src.export.org_site_exporter import OrgSiteExporter``) so
historical ``MistHelper.OrgSiteExporter`` / ``mh.OrgSiteExporter`` callers
keep working.

Cross-class references (``APIDataFetcher``, ``ConfigUtils``, ``APICoreFetchUtils``,
``DataProcessingUtils``, ``DataExporter``, ``ProgressContext``) and module-level
globals (``apisession``, ``PROGRESS_EMITTER``, ``OUTPUT_FORMAT``) are resolved
lazily via ``importlib.import_module("MistHelper")`` inside method bodies to keep
FR-028 IG-health clean (no top-level MistHelper import statement).
"""

from __future__ import annotations  # WHY: PEP 604 unions in annotations.

import importlib  # WHY: lazy MistHelper fetch of cross-class refs + globals.
import logging  # WHY: structured trace + failure reporting.
import os  # WHY: cache-file existence checks for sites_list_api.
import time  # WHY: epoch math for historical guest window + progress timing.

import mistapi  # WHY: dotted-path Mist API resolution + pagination helper.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class OrgSiteExporter:  # Org site exporters.
    """Organization Site Data Exporter.

    Handles site listings, site locations, and guest data exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def sites():  # Export the org site list.
        """Fetch and export the list of all sites in the organization.

        Output format determined by global OUTPUT_FORMAT setting.
        Uses APIDataFetcher to handle API call and output writing.
        """
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of APIDataFetcher + PROGRESS_EMITTER + OUTPUT_FORMAT.
        logging.info("Starting export of organization site list...")  # Log site export start.
        emitter = mh.PROGRESS_EMITTER  # Capture progress emitter.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_start("11", "sites", 1)  # Emit progress start.
        op_start = time.time()  # Record operation start time.
        mh.APIDataFetcher(  # Fetch and write sites.
            title="Site List:",
            api_call=mistapi.api.v1.orgs.sites.listOrgSites,
            filename="SiteList",
            sort_key="name",
            limit=1000,
        ).execute()
        output_desc = "SQLite table" if mh.OUTPUT_FORMAT == "sqlite" else "CSV file"  # Describe output backend.
        logging.info("Completed site list export and wrote results to %s.", output_desc)  # Log site export success.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_complete(mh.ProgressContext("11", "sites", 1), 1, False, time.time() - op_start)

    @staticmethod
    def sites_list_api():  # Export sites via list API.
        """Export all sites via 'list' endpoint to SiteList_ListAPI.csv (skip if cached file exists)."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of ConfigUtils/APICoreFetchUtils/DataProcessingUtils/DataExporter.
        output_file = "SiteList_ListAPI.csv"  # Define output filename.
        if os.path.exists(output_file):  # Branch: cached file exists.
            logging.info("! Using cached %s (already exists)", output_file)  # Log cache reuse.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info("! Using cached %s (already exists)", output_file)
            return  # Skip re-fetch.
        logging.info("Fetching all sites using the 'list' sites API endpoint...")  # Log fetch start.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("Fetching all sites using the 'list' sites API endpoint...")
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        sites = mh.APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch all sites.
        if not sites:  # Branch: no sites returned.
            logging.warning(" No sites returned from API.")  # Log empty result.
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logging.info(" No sites returned from API.")
            return  # Skip write.
        sites = DataProcessingUtils.flatten_nested_fields(sites)  # Flatten nested site fields.
        # Normalize nested JSON structures into a flat row-per-record format for CSV/DB output
        sites = DataProcessingUtils.flatten_nested_fields(sites)  # Flatten again post-merge.
        sites = DataProcessingUtils.escape_multiline(sites)  # type: ignore[no-untyped-call]
        # Write to the configured output backend (CSV or SQLite) via the DataExporter abstraction
        mh.DataExporter.write_with_format_selection(sites, output_file)  # type: ignore[no-untyped-call]
        logging.info("! Sites exported to %s", output_file)  # Log the successful export
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! Sites exported to %s", output_file)

    @staticmethod
    def sites_with_location():  # Export sites with location.
        """Export a list of sites with all available fields to SitesWithLocations.csv."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of ConfigUtils/APICoreFetchUtils/DataProcessingUtils/DataExporter.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("Sites with Location and Timezone Info:")
        logging.info("Listing Sites with Full Info:")  # Log listing start.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        logging.debug("Using org_id: %s for site location export.", org_id)  # Log org id used.
        sites = mh.APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch all sites.
        logging.info("Fetched %s sites from the organization.", len(sites))  # Log fetched site count.
        flattened_sites = DataProcessingUtils.flatten_nested_fields(sites)  # Flatten nested site fields.
        sanitized_sites = DataProcessingUtils.escape_multiline(flattened_sites)  # type: ignore[no-untyped-call]
        mh.DataExporter.write_with_format_selection(sanitized_sites, "SitesWithLocations.csv")  # type: ignore[no-untyped-call]
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! %s sites exported to SitesWithLocations.csv", len(sanitized_sites))
        logging.info(" Full site data written to SitesWithLocations.csv")  # Log write success.

    @staticmethod
    def current_guests() -> None:  # Export current guest users.
        """Export all current guest users in the org to OrgCurrentGuests.csv."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of ConfigUtils/DataProcessingUtils/DataExporter + apisession.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("Current and Historical Guest Users:")
        logging.info("Exporting all current guest users in the org...")  # Log guest export start.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        logging.debug("Using org_id: %s for current guest export.", org_id)  # Log org id used.
        response = mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization(mh.apisession, org_id, limit=1000)
        guests = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all guests.
        logging.info("Fetched %s current guest users from API.", len(guests))  # Log fetched guest count.
        guests = DataProcessingUtils.flatten_nested_fields(guests)  # Flatten nested guest fields.
        guests = DataProcessingUtils.escape_multiline(guests)  # type: ignore[no-untyped-call]
        mh.DataExporter.write_with_format_selection(guests, "OrgCurrentGuests.csv")  # type: ignore[no-untyped-call]
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! %s current guest users exported to OrgCurrentGuests.csv", len(guests))
        logging.info(" Current guests exported to OrgCurrentGuests.csv")  # Log write success.

    @staticmethod
    def historical_guests() -> None:  # Export 7-day guest history.
        """Export all guest users from the last 7 days to OrgHistoricalGuests.csv."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of ConfigUtils/DataProcessingUtils/DataExporter + apisession.
        logging.info("Exporting all guest users from the last 7 days...")  # Log historical export start.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        end_time = int(time.time())  # Capture end time as now.
        start_time = end_time - 7 * 24 * 3600  # Compute 7-day start time.
        logging.debug("Fetching guest authorizations from %s to %s (epoch seconds).", start_time, end_time)
        response = mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization(  # Search guests in window.
            mh.apisession, org_id, limit=1000, start=start_time, end=end_time
        )
        guests = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all guests.
        logging.info("Fetched %s historical guest users from API.", len(guests))  # Log fetched guest count.
        guests = DataProcessingUtils.flatten_nested_fields(guests)  # Flatten nested guest fields.
        guests = DataProcessingUtils.escape_multiline(guests)  # type: ignore[no-untyped-call]
        mh.DataExporter.write_with_format_selection(guests, "OrgHistoricalGuests.csv")  # type: ignore[no-untyped-call]
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logging.info("! %s historical guest users exported to OrgHistoricalGuests.csv", len(guests))
        logging.info(" Historical guests exported to OrgHistoricalGuests.csv")  # Log write success.
