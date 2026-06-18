"""Security export orchestration extracted from MistHelper offender #8."""

import csv
import importlib
import logging
import os
import time
from types import SimpleNamespace
from typing import Any


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static src imports."""
    misthelper_module = importlib.import_module("MistHelper")
    return SimpleNamespace(
        ConfigUtils=misthelper_module.ConfigUtils,
        PROGRESS_EMITTER=getattr(misthelper_module, "PROGRESS_EMITTER", None),
        TimeUtils=misthelper_module.TimeUtils,
        CacheUtils=misthelper_module.CacheUtils,
        OrgSiteExporter=misthelper_module.OrgSiteExporter,
        DataProcessingUtils=misthelper_module.DataProcessingUtils,
        DataExporter=misthelper_module.DataExporter,
        FilePathUtils=misthelper_module.FilePathUtils,
        mistapi=misthelper_module.mistapi,
        apisession=misthelper_module.apisession,
        tqdm=misthelper_module.tqdm,
        csv_freshness_minutes=getattr(misthelper_module, "CSV_FRESHNESS_MINUTES", 60),
    )


class SecurityEventsService:
    """Owns organization security export flow formerly embedded in MistHelper."""

    @staticmethod
    def execute(fast: bool = False):  # noqa: C901, PLR0912, PLR0915
        """Run the organization security export workflow."""
        deps = _resolve_runtime_dependencies()
        output_files = ["OrgSecurityPolicies.csv", "OrgSecIntelProfiles.csv", "OrgRogueData.csv"]

        if fast and SecurityEventsService._all_outputs_fresh(deps, output_files):
            logging.info("Fast mode cache hit: All security data CSVs are fresh; skipping fetch.")
            print("* Fast mode: Using cached security data (all files fresh)")
            return

        print("Export Organization Security Data:")
        logging.info("Starting export of organization security policies, intelligence profiles, and rogue data...")
        emitter = deps.PROGRESS_EMITTER
        if emitter:
            emitter.emit_progress_start("42", "security_events", 3)

        op_start = time.time()
        current_org_id = deps.ConfigUtils.get_cached_or_prompted_org_id()

        SecurityEventsService._export_flattened_dataset(
            deps,
            current_org_id,
            "OrgSecurityPolicies.csv",
            "security policies",
            "secpolicies",
            lambda: deps.mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies(
                deps.apisession, current_org_id, limit=1000
            ),
            "No data to export for OrgSecurityPolicies.csv (zero policies returned).",
            "(no policies found)",
        )
        SecurityEventsService._export_flattened_dataset(
            deps,
            current_org_id,
            "OrgSecIntelProfiles.csv",
            "security intelligence profiles",
            "secintel profiles",
            lambda: deps.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles(deps.apisession, current_org_id),
            "No data to export for OrgSecIntelProfiles.csv (zero profiles returned).",
            "(no profiles found)",
        )
        SecurityEventsService._export_rogue_data(deps)

        print("Security data export completed (3 files generated)")
        logging.info("Completed security policies, intelligence profiles, and rogue data export aggregate.")
        if emitter:
            emitter.emit_progress_complete("42", "security_events", 3, 3, False, time.time() - op_start)

    @staticmethod
    def _all_outputs_fresh(deps: SimpleNamespace, output_files: list[str]) -> bool:
        """Return True when every expected CSV exists and is still fresh."""
        for output_file in output_files:
            try:
                path = deps.FilePathUtils.get_csv_path(output_file)
                if os.path.exists(path):
                    age_minutes = (time.time() - os.path.getmtime(path)) / 60.0
                    if age_minutes >= deps.csv_freshness_minutes:
                        return False
                else:
                    return False
            except Exception:
                return False
        return True

    @staticmethod
    def _export_flattened_dataset(
        deps: SimpleNamespace,
        current_org_id: str,
        output_file: str,
        data_label: str,
        start_label: str,
        fetcher,
        empty_message: str,
        empty_suffix: str,
    ) -> None:
        """Fetch, flatten, and export a single org dataset."""
        dataset: list[dict[str, Any]] = []
        try:
            logging.info("Fetching organization %s...", start_label)
            response = fetcher()
            dataset = deps.mistapi.get_all(response=response, mist_session=deps.apisession) or []
            logging.debug("%s fetched: %d", data_label.capitalize(), len(dataset))
        except Exception as error:
            logging.warning("Failed to fetch %s: %s", start_label, error)

        if dataset:
            processed = deps.DataProcessingUtils.flatten_nested_fields(dataset)
            processed = deps.DataProcessingUtils.escape_multiline(processed)
            deps.DataExporter.save_data_to_output(processed, output_file)
            print(f"! {len(processed)} {data_label} exported to {output_file}")
            logging.info("Exported %d %s to %s", len(processed), data_label, output_file)
        else:
            print(f"! 0 {data_label} exported to {output_file} {empty_suffix}")
            logging.warning(empty_message)
            deps.DataExporter.save_data_to_output([], output_file)

    @staticmethod
    def _export_rogue_data(deps: SimpleNamespace) -> None:
        """Fetch rogue AP and client data across all sites and export combined rows."""
        lookback_hours = deps.TimeUtils.get_dynamic_lookback_hours(168, 1)
        rogue_duration = f"{lookback_hours}h"
        deps.TimeUtils.log_dynamic_lookback("rogue data fetch", lookback_hours)
        logging.info("Fetching rogue APs and clients from all sites via insights...")
        deps.CacheUtils.check_and_generate_csv("SiteList.csv", deps.OrgSiteExporter.sites)

        all_rogue_aps: list[dict[str, Any]] = []
        all_rogue_clients: list[dict[str, Any]] = []
        try:
            site_list_path = deps.FilePathUtils.get_csv_path("SiteList.csv")
            with open(site_list_path, encoding="utf-8") as file_handle:
                sites = list(csv.DictReader(file_handle))
            for site in deps.tqdm(sites, desc="Sites", unit="site"):
                if deps.ConfigUtils.check_stop_signal():
                    break
                site_id = site.get("id")
                site_name = site.get("name", "Unknown Site")
                if not site_id:
                    continue
                try:
                    response_aps = deps.mistapi.api.v1.sites.insights.listSiteRogueAPs(
                        deps.apisession, site_id, duration=rogue_duration, limit=1000
                    )
                    site_rogue_aps = deps.mistapi.get_all(response=response_aps, mist_session=deps.apisession) or []
                    for rogue_access_point in site_rogue_aps:
                        rogue_access_point["site_id"] = site_id
                        rogue_access_point["site_name"] = site_name
                        rogue_access_point["rogue_type"] = "AP"
                    all_rogue_aps.extend(site_rogue_aps)

                    response_clients = deps.mistapi.api.v1.sites.insights.listSiteRogueClients(
                        deps.apisession, site_id, duration=rogue_duration, limit=1000
                    )
                    site_rogue_clients = (
                        deps.mistapi.get_all(response=response_clients, mist_session=deps.apisession) or []
                    )
                    for client in site_rogue_clients:
                        client["site_id"] = site_id
                        client["site_name"] = site_name
                        client["rogue_type"] = "Client"
                    all_rogue_clients.extend(site_rogue_clients)
                    logging.info(
                        "! Fetched %d rogue APs and %d rogue clients from site: %s",
                        len(site_rogue_aps),
                        len(site_rogue_clients),
                        site_name,
                    )
                except Exception as error:
                    logging.warning("! Failed to fetch rogue data from site %s: %s", site_name, error)
                    continue
        except Exception as error:
            logging.error("Failed to process sites for rogue data: %s", error)
            return

        all_rogue_data = all_rogue_aps + all_rogue_clients
        if all_rogue_data:
            processed = deps.DataProcessingUtils.flatten_nested_fields(all_rogue_data)
            processed = deps.DataProcessingUtils.escape_multiline(processed)
            deps.DataExporter.save_data_to_output(processed, "OrgRogueData.csv")
            print(f"! {len(processed)} rogue devices exported to OrgRogueData.csv")
            logging.info("Exported %d rogue devices to OrgRogueData.csv", len(processed))
        else:
            print("! 0 rogue devices exported to OrgRogueData.csv (no rogue devices found)")
            logging.info("No rogue devices found across all sites (OrgRogueData.csv written empty).")
            deps.DataExporter.save_data_to_output([], "OrgRogueData.csv")
