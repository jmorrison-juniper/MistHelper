"""``OrgInventoryExporter`` extracted from MistHelper (initiative 1015 T-06).

Backs menu options 12 (inventory), 15 (devices with site info), 17 (all
devices), and 25 (combined weekly inventory + master CSV). All methods
are ``@staticmethod`` with no instance state, so this extraction lands
as a bare re-export from ``MistHelper.py`` (no Pattern 1 DI wrapper, no
delegator) following the T-09 / T-10 / T-13 precedent.

Direct imports cover stdlib + installed packages + canonical ``src/``
utility homes. Live-module globals with no ``src/`` home yet
(``apisession``, ``PROGRESS_EMITTER``, ``DEFAULT_API_PAGE_LIMIT``,
``DataExporter``) are resolved via lazy ``mh = importlib.import_module(
"MistHelper")`` inside each helper. Callers continue to reach the class
through the ``MistHelper.OrgInventoryExporter`` re-export alias.

Issue: initiative 1015 T-06 (Cat E fresh extraction).
"""

from __future__ import annotations  # PEP 604 unions for return types.

import csv  # DictReader/DictWriter for weekly + master CSV IO.
import importlib  # Lazy MistHelper import for live module globals.
import json  # Diagnostic raw-inventory JSON dump.
import logging  # Structured trace for API + persistence lifecycle.
import os  # Filesystem paths + environment lookups.
import time  # Progress emitter elapsed-time measurements.
from collections import defaultdict  # Weekly bucket accumulator.
from datetime import UTC, datetime  # ISO week bucketing (deterministic UTC).
from typing import Any  # Duck-typed device rows + PrettyTable payloads.

import mistapi  # Direct calls to orgs.inventory/orgs/devices endpoints.
from dotenv import load_dotenv  # END_CUSTOMER_* env resolution for weekly export.
from prettytable import PrettyTable  # Debug-log summary tables.
from tqdm import tqdm  # Progress bars for per-device enrichment loops.

from src.api.api_core_fetch_utils import APICoreFetchUtils  # all_sites/all_inventory helpers.
from src.cache.cache_utils import CacheUtils  # check_and_generate_csv gate.
from src.config.config_utils import ConfigUtils  # Cached-or-prompted org id.
from src.data.data_processing_utils import DataProcessingUtils  # Flatten/escape helpers.
from src.dataclasses.progress_event import ProgressContext  # Progress emitter payload shape.
from src.export.org_site_exporter import OrgSiteExporter  # SiteList.csv generator for cache path.
from src.utils.file_path_utils import FilePathUtils  # get_csv_path canonical location.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger routes operator notices through capture/redirection.


class OrgInventoryExporter:  # Org inventory exporters.
    """Organization Inventory and Device Exporter.

    Handles inventory, device, and combined site-device exports.
    Extracted from OrgExportUtils.
    """

    # Stable weekly-export column order for CombinedInventory outputs (downstream consumers depend on it).
    _COMBINED_INVENTORY_FIELDNAMES = [
        "Full Site",
        "System Serial Number",
        "System MAC Address",
        "System Model Number",
        "End Customer Name",
        "Address Line 1",
        "Address Line 2",
        "City",
        "State",
        "Country",
        "Zip Code / Postal Code",
        "End Customer Account ID",
    ]

    @staticmethod
    def inventory():  # Export org device inventory.
        """Fetch and export the full inventory of devices in the organization to OrgInventory.csv.

        Uses APIDataFetcher to handle API call, CSV writing, and table display.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PROGRESS_EMITTER + APIDataFetcher.
        logging.info("Starting export of organization device inventory...")  # Log inventory export start.
        emitter = mh.PROGRESS_EMITTER  # Capture progress emitter.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_start("12", "inventory", 1)  # Emit progress start.
        op_start = time.time()  # Record operation start time.
        mh.APIDataFetcher(
            title="Org Inventory:",
            api_call=mistapi.api.v1.orgs.inventory.getOrgInventory,
            filename="OrgInventory.csv",
            sort_key="model",
            vc=True,  # Include all physical VC member devices (6186 vs 3224 logical)
            limit=1000,
        ).execute()
        logging.info("Completed organization inventory export and wrote results to OrgInventory.csv.")
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_complete(ProgressContext("12", "inventory", 1), 1, False, time.time() - op_start)

    @staticmethod
    def devices():  # Export all org devices.
        """Fetch and export a list of all devices in the organization to OrgDevices.csv.

        Uses APIDataFetcher to handle API call, CSV writing, and table display.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PROGRESS_EMITTER + APIDataFetcher.
        logging.info("Starting export of all organization devices...")  # Log devices export start.
        emitter = mh.PROGRESS_EMITTER  # Capture progress emitter.
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_start("17", "devices", 1)  # Emit progress start.
        op_start = time.time()  # Record operation start time.
        mh.APIDataFetcher(  # Fetch and write devices.
            title="Org Devices:",
            api_call=mistapi.api.v1.orgs.devices.listOrgDevices,
            filename="OrgDevices.csv",
            sort_key="type",
        ).execute()
        logging.info("Completed organization devices export and wrote results to OrgDevices.csv.")
        if emitter:  # Branch: emitter present.
            emitter.emit_progress_complete(ProgressContext("17", "devices", 1), 1, False, time.time() - op_start)

    @staticmethod
    def _resolve_combined_inventory_org_name(current_org_id: str | None, fallback_org_name: str | None) -> str:
        """Resolve organization name used for combined inventory output filenames."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        org_name_for_filename = None  # Start with no resolved org name so API lookup can fill it in.
        try:  # Resolve org name from live Mist API first so filenames follow authoritative naming.
            org_response = mistapi.api.v1.orgs.orgs.getOrg(
                mh.apisession, current_org_id
            )  # Fetch org details for filename metadata.
            org_name_for_filename = getattr(org_response, "data", {}).get(
                "name"
            )  # Pull org name from the response payload if present.
        except Exception as exception:  # API resolution failure should not block report generation.
            logging.warning(
                "Unable to resolve org name from API for combined inventory filename: %s", exception
            )  # Log fallback reason for operators.
        if not org_name_for_filename:  # Fall back to customer name from environment when API name is unavailable.
            org_name_for_filename = fallback_org_name  # Use configured customer-friendly name if present.
        if not org_name_for_filename:  # Final fallback ensures a stable filename even with missing metadata.
            org_name_for_filename = current_org_id or "UnknownOrg"  # Use org ID or sentinel value as a last resort.
        return org_name_for_filename  # Return resolved display name for downstream filename sanitization.

    @staticmethod
    def _build_safe_org_name(org_name_for_filename: str) -> str:  # Build filesystem-safe org name.
        """Sanitize organization name so generated filenames stay filesystem-safe."""
        return "".join(  # Build safe filename character-by-character to preserve readable names.
            character if character.isalnum() or character in "-_" else "_" for character in org_name_for_filename
        )

    @staticmethod
    def _fetch_and_persist_raw_inventory_variant(
        filename: str, request_kwargs: dict, current_org_id: str, output_folder: str
    ) -> int:
        """Fetch one inventory variant and persist as raw JSON; return row count."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        logging.info("Fetching raw inventory variant for %s...", filename)  # Log before API call
        response = mistapi.api.v1.orgs.inventory.getOrgInventory(mh.apisession, current_org_id, **request_kwargs)
        raw_inventory = mistapi.get_all(response=response, mist_session=mh.apisession)  # Paginate all results
        output_path = os.path.join(output_folder, filename)  # Build deterministic file path
        with open(output_path, "w", encoding="utf-8") as json_file:  # UTF-8 for portable JSON encoding
            json.dump(raw_inventory, json_file, indent=2, default=str)  # Pretty-print so humans can diff variants
        logging.info("Saved %d entries to %s", len(raw_inventory), output_path)  # Log per-file count
        return len(raw_inventory)  # Return for summary aggregation

    @staticmethod
    def _export_combined_inventory_raw_json(output_folder: str, current_org_id: str) -> None:
        """Export raw inventory JSON variants used for VC delta analysis."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DEFAULT_API_PAGE_LIMIT module global.
        logging.info("Saving raw inventory JSON for delta comparison...")  # Log start of diagnostic exports
        try:  # Raw JSON export is diagnostic only and must never block the main report
            os.makedirs(output_folder, exist_ok=True)  # Ensure shared output folder exists
            page_limit = mh.DEFAULT_API_PAGE_LIMIT  # Read live default page size.
            request_specs = [  # One spec per inventory query variant for consistent export loop
                ("raw_inventory_vc_true.json", {"vc": True, "type": "switch", "limit": page_limit}),
                ("raw_inventory_vc_false.json", {"vc": False, "type": "switch", "limit": page_limit}),
                ("raw_inventory_no_vc_param.json", {"type": "switch", "limit": page_limit}),
            ]
            counts_by_filename: dict[str, int] = {
                filename: OrgInventoryExporter._fetch_and_persist_raw_inventory_variant(
                    filename, kwargs, current_org_id, output_folder
                )
                for filename, kwargs in request_specs
            }
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info(  # Show concise operator summary once all diagnostic files are written
                "  Raw JSON saved: vc=True (%s), vc=False (%s), no-vc (%s) entries",
                counts_by_filename.get("raw_inventory_vc_true.json", 0),
                counts_by_filename.get("raw_inventory_vc_false.json", 0),
                counts_by_filename.get("raw_inventory_no_vc_param.json", 0),
            )
        except Exception as json_save_error:  # Diagnostic failure is non-fatal by design
            logging.warning("Failed to save raw inventory JSON: %s", json_save_error)  # Preserve root cause

    @staticmethod
    def _load_combined_inventory_rows() -> list[dict[str, str]]:  # Load combined inventory rows.
        """Load enriched device rows from AllDevicesWithSiteInfo.csv."""
        devices_with_site_info_path = FilePathUtils.get_csv_path(
            "AllDevicesWithSiteInfo.csv"
        )  # Resolve current CSV path through shared path utility.
        with open(
            devices_with_site_info_path, encoding="utf-8"
        ) as file:  # Open generated enrichment CSV for downstream grouping logic.
            return list(csv.DictReader(file))  # Materialize all rows so weekly grouping can iterate more than once.

    @staticmethod
    def _split_physical_vs_virtual_inventory(
        all_devices: list[dict[str, str]],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Split combined inventory into (physical_devices, virtual_vc_placeholders)."""
        virtual_entries = [
            d for d in all_devices if d.get("mac", "").startswith("020003")
        ]  # 020003* = synthetic VC MAC
        site_configs = [d for d in all_devices if not d.get("mac", "").startswith("020003")]  # Real chassis only
        return site_configs, virtual_entries  # Caller continues with VC classification

    @staticmethod
    def _classify_empty_vc_shells(
        virtual_entries: list[dict[str, str]], site_configs: list[dict[str, str]]
    ) -> tuple[list[dict[str, str]], int]:
        """Return (empty_vc_shells, duplicate_vc_entries) for the virtual-entry analysis."""
        physical_vc_macs = {d.get("vc_mac", "") for d in site_configs if d.get("vc_mac")}  # Set of VC parent MACs
        empty_shells = [e for e in virtual_entries if e.get("mac") not in physical_vc_macs]  # No physical members
        duplicates = len(virtual_entries) - len(empty_shells)  # Remainder mirrors real hardware
        return empty_shells, duplicates  # Caller logs the diagnostics

    @staticmethod
    def _partition_combined_inventory_rows(  # Partition combined inventory rows.
        all_devices: list[dict[str, str]],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
        """Separate physical inventory rows from virtual VC placeholders and count duplicates."""
        site_configs, virtual_entries = OrgInventoryExporter._split_physical_vs_virtual_inventory(
            all_devices
        )  # Bucket by MAC prefix
        empty_vc_shells, duplicate_vc_entries = OrgInventoryExporter._classify_empty_vc_shells(
            virtual_entries, site_configs
        )  # Analyze the virtual bucket
        return site_configs, empty_vc_shells, duplicate_vc_entries  # Physical rows + shell diagnostics

    @staticmethod
    def _emit_vc_shell_dashboard_diff(
        site_configs: list[dict[str, str]], empty_vc_shells: list[dict[str, str]]
    ) -> None:
        """Log the dashboard-vs-report parity note when empty VC shells exist."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "  NOTE: %s provisioned VC shells exist with no physical members.",
            len(empty_vc_shells),
        )  # Explain why dashboard counts may exceed report counts
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(  # Provide explicit comparison so operators trust the physical-only report totals
            "        Dashboard shows %s 'Physical Devices' but %s are empty VC placeholders (020003* MAC, no serial/SKU).",  # noqa: E501
            len(site_configs) + len(empty_vc_shells),
            len(empty_vc_shells),
        )
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "        Report correctly includes only %s devices with real hardware.",
            len(site_configs),
        )  # Confirm report logic remains intentional

    @staticmethod
    def _log_combined_inventory_vc_summary(  # Log virtual-chassis summary.
        all_devices: list[dict[str, str]],
        site_configs: list[dict[str, str]],
        empty_vc_shells: list[dict[str, str]],
        duplicate_vc_entries: int,
    ) -> None:
        """Log and print the virtual chassis filtering summary for operators."""
        logging.info(  # Explain how many rows were filtered to reach physical-hardware-only reporting
            "Loaded %d total devices, filtered to %d physical devices (excluded %d virtual VC identifiers)",
            len(all_devices),
            len(site_configs),
            len(all_devices) - len(site_configs),
        )
        logging.info(  # Break down virtual rows into duplicates versus empty VC shells
            "Virtual VC breakdown: %d duplicate entries (real hardware counted elsewhere) + %d empty VC shells (provisioned but no physical members assigned)",  # noqa: E501
            duplicate_vc_entries,
            len(empty_vc_shells),
        )
        if empty_vc_shells:  # Surface dashboard/report parity nuance only when empty shells actually exist
            OrgInventoryExporter._emit_vc_shell_dashboard_diff(site_configs, empty_vc_shells)  # Print parity note

    @staticmethod
    def _build_combined_inventory_weekly_row(  # Build one weekly inventory row.
        device: dict[str, str],
        end_customer_name: str | None,
        end_customer_account_id: str | None,
    ) -> dict[str, str | None]:
        """Build one weekly export row from a physical device record."""
        return {  # Shape output row once so weekly writer can stay simple and deterministic.
            "Full Site": device.get("site_name", ""),
            "System Serial Number": device.get("serial", ""),
            "System MAC Address": device.get("mac", ""),
            "System Model Number": device.get("model", ""),
            "End Customer Name": end_customer_name,
            "Address Line 1": device.get("street", ""),
            "Address Line 2": "",
            "City": device.get("city", ""),
            "State": device.get("state", ""),
            "Country": device.get("country", "US"),
            "Zip Code / Postal Code": device.get("zip_code", ""),
            "End Customer Account ID": end_customer_account_id,
        }

    @staticmethod
    def _bucket_device_into_week(
        device: dict[str, str],
        weekly_data: defaultdict,
        summary_data: defaultdict,
        end_customer_name: str | None,
        end_customer_account_id: str | None,
    ) -> None:
        """Bucket one device into the correct ISO-week weekly_data + summary_data."""
        try:  # One bad device row must not derail the full export
            created_time = int(device.get("created_time", 0))  # Convert API timestamp to epoch seconds
            created_date = datetime.fromtimestamp(created_time, tz=UTC)  # UTC for deterministic bucketing
            year, week, _ = created_date.isocalendar()  # Derive ISO calendar week for CSV naming
            week_key = f"{year}_Week_{week:02d}"  # Stable filename segment
            weekly_data[week_key].append(  # Append detailed export row to the correct weekly bucket
                OrgInventoryExporter._build_combined_inventory_weekly_row(
                    device, end_customer_name, end_customer_account_id
                )
            )
            summary_data[(year, week)] += 1  # Increment summary counter for the same ISO week
        except Exception as exception:  # Row-level failure logged for cleanup
            logging.warning("! Skipping device due to error: %s", exception)  # Log row-level failure

    @staticmethod
    def _build_combined_inventory_weekly_data(  # Build weekly inventory dataset.
        site_configs: list[dict[str, str]],
        end_customer_name: str | None,
        end_customer_account_id: str | None,
    ) -> tuple[defaultdict[str, list[dict[str, str | None]]], defaultdict[tuple[int, int], int]]:
        """Group physical devices into ISO calendar-week buckets and summary counts."""
        weekly_data: defaultdict[str, list[dict[str, str | None]]] = defaultdict(list)  # Per-week export rows
        summary_data: defaultdict[tuple[int, int], int] = defaultdict(int)  # Per-week device counts
        for device in site_configs:  # Process each physical device row exactly once
            OrgInventoryExporter._bucket_device_into_week(
                device,
                weekly_data,
                summary_data,
                end_customer_name,
                end_customer_account_id,
            )
        return weekly_data, summary_data  # Return both detailed buckets and summary counts

    @staticmethod
    def _write_combined_inventory_weekly_csvs(  # Write weekly inventory CSVs.
        output_folder: str,
        fieldnames: list[str],
        weekly_data: defaultdict[str, list[dict[str, str | None]]],
    ) -> None:
        """Write one CSV file per ISO week bucket."""
        for (
            week_key,
            rows,
        ) in (
            weekly_data.items()
        ):  # Emit each week as its own CSV so downstream consumers can process incremental periods.
            output_file = os.path.join(output_folder, f"{week_key}.csv")  # Build deterministic weekly CSV path.
            with open(
                output_file, mode="w", newline="", encoding="utf-8"
            ) as file:  # Open weekly file for a clean rewrite each run.
                writer = csv.DictWriter(
                    file, fieldnames=fieldnames
                )  # Use explicit field order so exports stay stable over time.
                writer.writeheader()  # Always emit header row for spreadsheet compatibility.
                writer.writerows(rows)  # Write all device rows for this ISO week.

    @staticmethod
    def _write_combined_inventory_summary(  # Write combined inventory summary.
        output_folder: str,
        summary_data: defaultdict[tuple[int, int], int],
    ) -> None:
        """Write summary CSV containing device counts per ISO year/week."""
        summary_file = os.path.join(
            output_folder, "CombinedInventory_Summary.csv"
        )  # Use fixed summary filename for discoverability.
        with open(
            summary_file, mode="w", newline="", encoding="utf-8"
        ) as file:  # Rewrite summary on each run so counts remain current.
            summary_writer = csv.writer(file)  # Use plain CSV writer because summary rows are positional.
            summary_writer.writerow(["Year", "Week", "Device Count"])  # Emit stable summary header.
            for (year, week), count in sorted(summary_data.items()):  # Sort chronologically for human readability.
                summary_writer.writerow([year, week, count])  # Persist per-week device totals.

    @staticmethod
    def _build_master_csv_row(device: dict[str, str]) -> dict[str, str]:
        """Build one flattened master-CSV row from a physical device record."""
        return {  # Simplified headers expected by downstream consumers
            "serial": device.get("serial", ""),
            "mac": device.get("mac", ""),
            "model": device.get("model", ""),
            "Street Address": device.get("street", ""),
            "City": device.get("city", ""),
            "State": device.get("state", ""),
            "Zip": device.get("zip_code", ""),
        }

    @staticmethod
    def _persist_master_csv(master_csv_file: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
        """Write master inventory rows to CSV with explicit field order."""
        with open(master_csv_file, mode="w", newline="", encoding="utf-8") as file:  # Rewrite each run
            writer = csv.DictWriter(file, fieldnames=fieldnames)  # Explicit header ordering
            writer.writeheader()  # Column names for spreadsheet/ETL workflows
            writer.writerows(rows)  # Persist all physical-device rows

    @staticmethod
    def _write_combined_inventory_master_csv(  # Write combined inventory master CSV.
        output_folder: str,
        safe_org_name: str,
        site_configs: list[dict[str, str]],
    ) -> tuple[str, int]:
        """Write simplified master combined-inventory CSV and return filename plus row count."""
        master_csv_data = [
            OrgInventoryExporter._build_master_csv_row(device) for device in site_configs
        ]  # Build all master rows up front
        master_csv_filename = (
            f"{safe_org_name}_CombinedInventory_Master.csv"  # Include org for multi-org runs  # noqa: E501
        )
        master_csv_file = os.path.join(output_folder, master_csv_filename)  # Final path
        master_csv_fieldnames = ["serial", "mac", "model", "Street Address", "City", "State", "Zip"]  # Stable order
        OrgInventoryExporter._persist_master_csv(master_csv_file, master_csv_fieldnames, master_csv_data)
        return master_csv_filename, len(master_csv_data)  # Metadata for final summary message

    @staticmethod
    def _prepare_combined_inventory_context() -> tuple[str, str | None, str | None, str, str]:
        """Resolve org, customer, safe org name, and output folder for combined inventory export."""
        load_dotenv()  # Load customer metadata from .env
        end_customer_name = os.getenv("END_CUSTOMER_NAME")  # Used in weekly export columns
        end_customer_account_id = os.getenv("END_CUSTOMER_ACCOUNT_ID")  # Used in weekly export columns
        current_org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org context first
        org_name_for_filename = OrgInventoryExporter._resolve_combined_inventory_org_name(
            current_org_id, end_customer_name
        )  # Authoritative org name with safe fallbacks
        safe_org_name = OrgInventoryExporter._build_safe_org_name(org_name_for_filename)  # Portable filenames
        output_folder = os.path.join("data", "CombinedInventory_ByWeek")  # Predictable subfolder
        return current_org_id, end_customer_name, end_customer_account_id, safe_org_name, output_folder

    @staticmethod
    def _emit_combined_inventory_outputs(
        output_folder: str,
        safe_org_name: str,
        site_configs: list[dict[str, str]],
        weekly_data: defaultdict,
        summary_data: defaultdict,
    ) -> tuple[str, int]:
        """Emit weekly CSVs + summary + master CSV; return master filename + row count."""
        fieldnames = OrgInventoryExporter._COMBINED_INVENTORY_FIELDNAMES  # Stable weekly-export column order
        OrgInventoryExporter._write_combined_inventory_weekly_csvs(output_folder, fieldnames, weekly_data)
        OrgInventoryExporter._write_combined_inventory_summary(output_folder, summary_data)  # Year/week summary
        return OrgInventoryExporter._write_combined_inventory_master_csv(
            output_folder, safe_org_name, site_configs
        )  # Simplified master CSV used by external consumers

    @staticmethod
    def combined_inventory_with_site_info():  # Export devices with site info.
        """Combine fresh AllDevicesWithSiteInfo data into weekly CSV files + summary + master CSV."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Combined Inventory with Site Info by Calendar Week:")  # Announce menu 25 export scope
        ctx = OrgInventoryExporter._prepare_combined_inventory_context()  # Resolve org + customer + paths
        current_org_id, end_customer_name, end_customer_account_id, safe_org_name, output_folder = ctx
        OrgInventoryExporter.devices_with_site_info()  # Regenerate enriched inventory CSV first
        OrgInventoryExporter._export_combined_inventory_raw_json(output_folder, current_org_id)  # Diagnostic JSON
        all_devices = OrgInventoryExporter._load_combined_inventory_rows()  # Load enriched CSV rows
        site_configs, empty_vc_shells, duplicate_vc_entries = OrgInventoryExporter._partition_combined_inventory_rows(
            all_devices
        )  # Separate physical devices from virtual VC placeholders
        OrgInventoryExporter._log_combined_inventory_vc_summary(
            all_devices, site_configs, empty_vc_shells, duplicate_vc_entries
        )  # Surface physical-vs-virtual filtering details
        weekly_data, summary_data = OrgInventoryExporter._build_combined_inventory_weekly_data(
            site_configs, end_customer_name, end_customer_account_id
        )  # Group into per-week export buckets
        master_csv_filename, master_row_count = OrgInventoryExporter._emit_combined_inventory_outputs(
            output_folder, safe_org_name, site_configs, weekly_data, summary_data
        )
        OrgInventoryExporter._print_combined_inventory_summary(
            weekly_data, site_configs, master_csv_filename, master_row_count
        )  # Tell operator where the three output artifacts landed

    @staticmethod
    def _print_combined_inventory_summary(
        weekly_data: Any,
        site_configs: Any,
        master_csv_filename: str,
        master_row_count: int,
    ) -> None:
        """Log the three CombinedInventory output locations (weekly CSVs, summary, master) for the operator."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "! %s weekly CSV files created in data/CombinedInventory_ByWeek/ folder (%s total devices processed)",
            len(weekly_data),
            len(site_configs),
        )  # Summarize weekly export output counts for the operator.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "! Summary report exported to data/CombinedInventory_ByWeek/CombinedInventory_Summary.csv"
        )  # Confirm summary report location.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info(
            "! Master inventory exported to data/CombinedInventory_ByWeek/%s (%s devices)",
            master_csv_filename,
            master_row_count,
        )  # Confirm master report path and row count.

    @staticmethod
    def _build_site_lookup_from_api(org_id: str) -> dict:  # type: ignore[type-arg]
        """Fetch sites from the API and build an id -> {name, address} lookup map."""
        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch sites from API.
        site_lookup = {  # Build site lookup from API rows.
            site["id"]: {"name": site.get("name", ""), "address": site.get("address", "")} for site in sites
        }
        logging.debug("Loaded %s sites for lookup.", len(site_lookup))  # Log loaded site count.
        return site_lookup  # Site id -> info map.

    @staticmethod
    def _load_site_lookup_from_cache(org_id: str) -> dict:  # type: ignore[type-arg]
        """Load the site lookup from cached SiteList.csv, falling back to the API on any read failure."""
        try:  # Cached CSV is preferred; fall back to the API if it is missing or unreadable.
            site_list_path = FilePathUtils.get_csv_path("SiteList.csv")  # Resolve site CSV path.
            with open(site_list_path, encoding="utf-8") as file:  # Open cached site CSV.
                reader = csv.DictReader(file)  # Read site CSV rows.
                site_lookup = {  # Build site lookup from CSV rows.
                    row["id"]: {"name": row.get("name", ""), "address": row.get("address", "")} for row in reader
                }
            logging.debug("Loaded %s sites from cached SiteList.csv", len(site_lookup))  # Log loaded site count.
            return site_lookup  # Cached site lookup.
        except Exception as exception:  # Cached read failed.
            logging.warning("Failed to load from cached SiteList.csv, falling back to API: %s", exception)  # Warn.
            return OrgInventoryExporter._build_site_lookup_from_api(org_id)  # API fallback.

    @staticmethod
    def _load_inventory_from_cache(org_id: str) -> list:  # type: ignore[type-arg]
        """Load the org inventory from cached OrgInventory.csv, falling back to the API on any read failure."""
        try:  # Cached CSV is preferred; fall back to the API if it is missing or unreadable.
            inventory_path = FilePathUtils.get_csv_path("OrgInventory.csv")  # Resolve inventory CSV path.
            with open(inventory_path, encoding="utf-8") as file:  # Open cached inventory CSV.
                reader = csv.DictReader(file)  # Read inventory CSV rows.
                inventory = list(reader)  # Materialize inventory rows.
            logging.debug("Loaded %s devices from cached OrgInventory.csv", len(inventory))  # Log loaded device count.
            return inventory  # Cached inventory rows.
        except Exception as exception:  # Cached read failed.
            logging.warning("Failed to load from cached OrgInventory.csv, falling back to API: %s", exception)  # Warn.
            inventory = APICoreFetchUtils.all_inventory_with_limit(org_id)  # Fetch inventory from API.
            logging.debug("Loaded %s devices from API fallback", len(inventory))  # Log API fallback count.
            return inventory  # API fallback inventory rows.

    @staticmethod
    def _devices_load_data(org_id: str, fast: bool) -> tuple[dict, list]:  # type: ignore[type-arg]
        """Load (site_lookup, inventory): cached CSVs (with API fallback) in fast mode, else direct API."""
        if fast:  # Fast mode reuses cached CSVs to avoid redundant API calls.
            CacheUtils.check_and_generate_csv("SiteList.csv", OrgSiteExporter.sites)  # Ensure site CSV cached.
            CacheUtils.check_and_generate_csv("OrgInventory.csv", OrgInventoryExporter.inventory)  # Ensure inv cached.
            site_lookup = OrgInventoryExporter._load_site_lookup_from_cache(org_id)  # Load sites from cache (or API).
            inventory = OrgInventoryExporter._load_inventory_from_cache(org_id)  # Load inventory from cache (or API).
            return site_lookup, inventory  # Cached data (with fallback already applied).
        site_lookup = OrgInventoryExporter._build_site_lookup_from_api(org_id)  # Non-fast: fetch sites from API.
        inventory = APICoreFetchUtils.all_inventory_with_limit(org_id)  # Non-fast: fetch inventory from API.
        logging.debug("Loaded %s devices from org inventory.", len(inventory))  # Log loaded device count.
        return site_lookup, inventory  # Direct-API data.

    @staticmethod
    def _build_mac_to_site_id(inventory: list) -> dict:  # type: ignore[type-arg]
        """Index every device's mac -> site_id so VC members without a site_id can inherit one from their parent.

        Physical VC members carry vc_mac but no site_id; that vc_mac may point at the virtual VC entry (020003* MAC)
        or the primary physical chassis MAC. Indexing ALL devices with a site_id covers both cases.
        """
        mac_to_site_id: dict[str, str] = {}  # Universal mac -> site_id lookup for inheritance.
        for device in inventory:  # Scan all inventory entries.
            mac = device.get("mac", "")  # Get device MAC address.
            if mac and device.get("site_id"):  # Any device with a site assignment.
                mac_to_site_id[mac] = device["site_id"]  # Index for vc_mac lookups.
        logging.info(  # Log the built index size.
            "Built mac->site_id lookup with %d entries for VC member site inheritance", len(mac_to_site_id)
        )
        return mac_to_site_id  # mac -> site_id inheritance map.

    @staticmethod
    def _enrich_one_device(device: dict, site_lookup: dict, mac_to_site_id: dict) -> bool:  # type: ignore[type-arg]
        """Attach site name/address + split-address fields to one device; return True if its site was VC-inherited."""
        site_id = device.get("site_id")  # Check if device has its own site_id.
        inherited = False  # Track whether this device inherited its site from a VC parent.
        if not site_id and device.get("vc_mac"):  # Device missing a site assignment but part of a VC.
            inherited_site_id = mac_to_site_id.get(device["vc_mac"])  # Look up site from the VC parent MAC.
            if inherited_site_id:  # Found the parent's site.
                site_id = inherited_site_id  # Use the parent's site_id for enrichment.
                device["site_id"] = inherited_site_id  # Persist inherited site_id on the device record.
                inherited = True  # Mark this device as having inherited its site.
        site_info = site_lookup.get(site_id, {"name": "Unknown", "address": "Unknown"})  # Resolve site details.
        device["site_name"] = site_info["name"]  # Apply site name to device record.
        device["site_address"] = site_info["address"]  # Apply full site address to device record.
        street, city, state, zip_code, country = OrgInventoryExporter._split_full_address(
            site_info["address"]
        )  # Split.
        device["street"] = street  # Set street address component.
        device["city"] = city  # Set city component.
        device["state"] = state  # Set state/province component.
        device["zip_code"] = zip_code  # Set postal/zip code component.
        device["country"] = country  # Set country component.
        return inherited  # Whether the site was inherited from a VC parent.

    @staticmethod
    def _enrich_devices_with_site_info(inventory: list, site_lookup: dict, mac_to_site_id: dict) -> list:  # type: ignore[type-arg]
        """Enrich every device with site info (inheriting VC-member sites) and return the enriched list."""
        enriched_devices = []  # Init enriched device list.
        vc_inherited_count = 0  # Track how many physical members inherited site info from their VC.
        for device in tqdm(inventory, desc="Processing Devices", unit="device"):  # type: ignore[no-untyped-call]
            inherited = OrgInventoryExporter._enrich_one_device(device, site_lookup, mac_to_site_id)  # Enrich one.
            if inherited:  # The device inherited its site from a VC parent.
                vc_inherited_count += 1  # Count successful inheritance.
            enriched_devices.append(device)  # Add enriched device to output list.
            logging.debug("Enriched device %s (%s) with site info.", device.get("name", ""), device.get("mac", ""))
        if vc_inherited_count:  # Log inheritance summary if any members were fixed.
            logging.info("%d physical VC members inherited site info from their VC parent", vc_inherited_count)
        return enriched_devices  # Enriched device records.

    @staticmethod
    def _flatten_sort_export_devices(devices: list) -> list:  # type: ignore[type-arg]
        """Flatten, escape, sort by site name, and write the all-devices CSV; return the processed rows for display."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter (T-08 pending).
        devices = DataProcessingUtils.flatten_nested_fields(devices)  # Flatten enriched fields.
        devices = DataProcessingUtils.escape_multiline(devices)  # type: ignore[no-untyped-call]
        devices = sorted(devices, key=lambda x: x.get("site_name", ""))  # Sort by site name.
        mh.DataExporter.write_with_format_selection(devices, "AllDevicesWithSiteInfo.csv")  # type: ignore[no-untyped-call]
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! %s devices exported to AllDevicesWithSiteInfo.csv", len(devices))  # Confirm export to operator.
        logging.info("All device data written to AllDevicesWithSiteInfo.csv (%s records).", len(devices))  # Log write.
        return devices  # Processed rows for the summary table.

    @staticmethod
    def _display_devices_summary_table(devices: list) -> None:  # type: ignore[type-arg]
        """Build a PrettyTable of the enriched devices and debug-log it for operator visibility."""
        table = PrettyTable()  # Build display table.
        table.field_names = [  # Define table columns.
            "name",
            "mac",
            "model",
            "serial",
            "type",
            "site_name",
            "street",
            "city",
            "state",
            "zip_code",
            "country",
        ]
        for device in devices:  # Iterate enriched devices for rows.
            table.add_row([device.get(column, "") for column in table.field_names])  # One cell per defined column.
        logging.debug("\n%s", table.get_string())  # Debug-log the table.

    @staticmethod
    def devices_with_site_info(fast: bool = False):
        """Fetch all org devices, enrich them with site/address info, and export AllDevicesWithSiteInfo.csv.

        When ``fast`` is True, cached SiteList.csv / OrgInventory.csv are used (with API fallback); otherwise
        the data is fetched directly from the API. Physical VC members without a site_id inherit one from
        their VC parent. Also debug-logs a summary table.
        """
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("All Devices with Site and Address Info:")  # Inform operator of export.
        logging.info("Fetching All Devices with Site Info...")  # Log fetch start.
        if fast:  # Fast mode reuses cached CSVs.
            logging.info(" Fast mode enabled for devices with site info export")  # Log fast mode enabled.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.
        site_lookup, inventory = OrgInventoryExporter._devices_load_data(org_id, fast)  # Load sites + inventory.
        mac_to_site_id = OrgInventoryExporter._build_mac_to_site_id(inventory)  # Build VC inheritance index.
        enriched_devices = OrgInventoryExporter._enrich_devices_with_site_info(  # Enrich every device with site info.
            inventory, site_lookup, mac_to_site_id
        )
        processed = OrgInventoryExporter._flatten_sort_export_devices(enriched_devices)  # Flatten/sort/write the CSV.
        OrgInventoryExporter._display_devices_summary_table(processed)  # Debug-log a summary table of the devices.

    @staticmethod
    def gateways_with_site_info():  # Export gateways with site info.
        """Export gateway devices enriched with site and address info to GatewaysWithSiteInfo.csv.

        Fetches all gateway devices in the organization, enriches them with site and
        address info, writes GatewaysWithSiteInfo.csv, and logs a summary table.
        """
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("Gateways with Site and Address Info:")  # Inform operator of export.
        logging.info("Fetching Gateways with Site Info...")  # Log fetch start.
        org_id = ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org id.

        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # Fetch sites from API.
        site_lookup = {site["id"]: {"name": site.get("name", ""), "address": site.get("address", "")} for site in sites}
        logging.debug("Loaded %s sites for lookup.", len(site_lookup))  # Log loaded site count.

        inventory = APICoreFetchUtils.all_inventory_with_limit(org_id)  # Fetch inventory from API.
        logging.debug("Loaded %s devices from org inventory.", len(inventory))  # Log loaded device count.

        gateways = OrgInventoryExporter._enrich_gateways_with_site_info(inventory, site_lookup)  # Filter + enrich
        logging.info("Enriched %s gateway devices with site info.", len(gateways))  # Log enriched gateway count.
        gateways = OrgInventoryExporter._flatten_sort_export_gateways(gateways)  # Flatten/sort/write CSV; returns rows
        OrgInventoryExporter._display_gateways_summary_table(gateways)  # Debug-log a PrettyTable of the gateways.

    @staticmethod
    def _flatten_sort_export_gateways(gateways: list) -> list:  # type: ignore[type-arg]  # Flatten/sort/write the CSV
        """Flatten, escape, sort by site name, and write the gateways CSV; return the processed rows for display."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter (T-08 pending).
        gateways = DataProcessingUtils.flatten_nested_fields(gateways)  # Flatten gateway fields.
        gateways = DataProcessingUtils.escape_multiline(gateways)  # type: ignore[no-untyped-call]
        gateways = sorted(gateways, key=lambda x: x.get("site_name", ""))  # Sort by site name.
        mh.DataExporter.write_with_format_selection(gateways, "GatewaysWithSiteInfo.csv")  # type: ignore[no-untyped-call]
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! %s gateways exported to GatewaysWithSiteInfo.csv", len(gateways))  # Confirm export to operator.
        logging.info("Gateway data written to GatewaysWithSiteInfo.csv")  # Log write success.
        return gateways  # Processed rows for the summary table

    @staticmethod
    def _split_full_address(address: str) -> tuple[str, str, str, str, str]:  # Parse address into parts.
        """Split a full address into (street, city, state, zip, country); raw street + blanks on parse failure."""
        try:
            parts = address.split(", ")  # Split on comma separators.
            state_zip = parts[2].split()  # Split state and zip.
            return parts[0], parts[1], state_zip[0], state_zip[1], parts[3]  # street, city, state, zip, country
        except Exception as exception:  # Catch parse errors.
            logging.debug("Failed to split address '%s': %s", address, exception)  # Log parse failure.
            return address, "", "", "", ""  # Return raw address fallback.

    @staticmethod
    def _enrich_gateways_with_site_info(inventory: list, site_lookup: dict) -> list:  # type: ignore[type-arg]
        """Filter inventory to gateways and attach site name/address plus split address fields to each."""
        gateways = []  # Init gateway list.
        for device in tqdm(inventory, desc="Processing Gateways", unit="device"):  # type: ignore[no-untyped-call]
            if device.get("type") != "gateway":  # Only gateways are enriched/exported
                continue  # Skip non-gateway devices
            site_id = device.get("site_id")  # Read device site id.
            site_info = site_lookup.get(site_id, {"name": "Unknown", "address": "Unknown"})  # Look up site info.
            device["site_name"] = site_info["name"]  # Attach site name.
            device["site_address"] = site_info["address"]  # Attach site address.
            street, city, state, zip_code, country = OrgInventoryExporter._split_full_address(site_info["address"])
            device["street"] = street  # Attach street.
            device["city"] = city  # Attach city.
            device["state"] = state  # Attach state.
            device["zip_code"] = zip_code  # Attach zip code.
            device["country"] = country  # Attach country.
            gateways.append(device)  # Add gateway to list.
        return gateways  # Enriched gateway records

    @staticmethod
    def _display_gateways_summary_table(gateways: list) -> None:  # type: ignore[type-arg]  # Debug-log a table
        """Build a PrettyTable of the enriched gateways and debug-log it for operator visibility."""
        table = PrettyTable()  # Build display table.
        table.field_names = [  # Define table columns.
            "name",
            "mac",
            "model",
            "serial",
            "site_name",
            "street",
            "city",
            "state",
            "zip_code",
            "country",
        ]
        for gateway in gateways:  # Iterate gateways for rows.
            table.add_row(  # Add gateway row to table.
                [gateway.get(column, "") for column in table.field_names]  # One cell per defined column
            )
        logging.debug("\n%s", table.get_string())  # Debug-log the table.
