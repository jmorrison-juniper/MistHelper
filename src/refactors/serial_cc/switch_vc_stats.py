"""Switch VC stats orchestration extracted from MistHelper high-CC offender."""

import csv  # Read cached OrgInventory.csv rows for switch selection
import importlib  # Resolve MistHelper runtime dependencies lazily
import logging  # Emit operator-visible progress and diagnostics
from concurrent.futures import ThreadPoolExecutor, as_completed  # Parallelize per-switch VC API calls in fast mode
from types import SimpleNamespace  # Bundle resolved runtime dependencies
from typing import Any  # Runtime dependency surface is dynamic from MistHelper module


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper runtime dependencies without static cross-module imports."""
    misthelper_module = importlib.import_module("MistHelper")  # Import at runtime to avoid circular imports
    return SimpleNamespace(
        CacheUtils=misthelper_module.CacheUtils,  # Ensure OrgInventory cache file exists before reading
        OrgInventoryExporter=misthelper_module.OrgInventoryExporter,  # Cache regeneration callback for OrgInventory
        FilePathUtils=misthelper_module.FilePathUtils,  # Resolve canonical data/ CSV paths
        ConfigUtils=misthelper_module.ConfigUtils,  # Stop-signal polling between switch fetches
        DataProcessingUtils=misthelper_module.DataProcessingUtils,  # Flatten and sanitize exported rows
        DataExporter=misthelper_module.DataExporter,  # Persist VC stats to configured output backend
        mistapi=misthelper_module.mistapi,  # Mist SDK root for VC stats API calls
        apisession=misthelper_module.apisession,  # Active API session object
        tqdm=misthelper_module.tqdm,  # Existing progress-bar implementation used throughout MistHelper
        FAST_MODE_ENABLED=getattr(misthelper_module, "FAST_MODE_ENABLED", False),  # Fast-mode toggle flag
        FAST_MODE_MAX_CONCURRENT_CONNECTIONS=getattr(
            misthelper_module,
            "FAST_MODE_MAX_CONCURRENT_CONNECTIONS",
            8,
        ),  # Fast-mode worker cap (defaults to 8)
    )


class SwitchVcStatsService:
    """Owns switch virtual chassis statistics export formerly embedded in OrgDeviceStatsExporter."""

    @staticmethod
    def _load_switches(deps: SimpleNamespace) -> list[dict[str, Any]]:
        """Load switch rows with vc_mac from cached OrgInventory.csv."""
        deps.CacheUtils.check_and_generate_csv("OrgInventory.csv", deps.OrgInventoryExporter.inventory)  # Ensure cache
        inventory_path = deps.FilePathUtils.get_csv_path("OrgInventory.csv")  # Resolve canonical inventory CSV path
        with open(inventory_path, encoding="utf-8") as file_handle:  # Read the cached inventory CSV
            reader = csv.DictReader(file_handle)  # Parse rows as dictionaries keyed by header
            switches = [
                row for row in reader if row.get("type") == "switch" and row.get("vc_mac", "").strip()
            ]  # Keep only switches participating in a VC
        return switches  # Return VC-eligible switch rows for per-switch API fetches

    @staticmethod
    def _fetch_vc_for_switch(deps: SimpleNamespace, switch: dict[str, Any]) -> dict[str, Any] | None:
        """Fetch VC stats for one switch and merge with inventory row context."""
        site_id = switch.get("site_id")  # Site context required by getSiteDeviceVirtualChassis API
        device_id = switch.get("id")  # Device UUID required by getSiteDeviceVirtualChassis API
        name = switch.get("name", "")  # Human-readable device name for logging context
        mac = switch.get("mac", "")  # Device MAC for logging context
        model = switch.get("model", "")  # Device model for logging context
        serial = switch.get("serial", "")  # Device serial for logging context
        logging.debug(
            "Processing switch: name=%s, id=%s, site_id=%s, mac=%s, model=%s, serial=%s",
            name,
            device_id,
            site_id,
            mac,
            model,
            serial,
        )  # Trace per-switch context before issuing VC API call
        if not site_id or not device_id:  # Skip records missing required path parameters
            logging.warning(
                "Skipping switch with missing site_id or device_id: name=%s, mac=%s",
                name,
                mac,
            )  # Warn so operators can inspect malformed inventory rows
            return None  # Signal caller to omit this switch from export rows
        try:  # Non-fatal API failures should not abort whole export
            vc_stats = deps.mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(
                deps.apisession,
                site_id,
                device_id,
            ).data  # Fetch VC membership and stacking cable details for switch
            logging.debug("Fetched VC stats for switch %s (%s)", name, device_id)  # Trace successful fetch
            return {**switch, **vc_stats}  # Merge inventory context with VC API payload for export
        except Exception as fetch_error:  # Keep processing other switches when one fetch fails
            logging.warning(
                "Failed to fetch VC stats for switch %s (%s): %s",
                name,
                device_id,
                fetch_error,
            )  # Warn with device context for troubleshooting
            return None  # Signal caller to omit failed switch

    @classmethod
    def _collect_vc_stats(cls, deps: SimpleNamespace, switches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Collect VC stats either concurrently (fast mode) or sequentially."""
        all_vc_stats: list[dict[str, Any]] = []  # Accumulate one merged row per successful switch fetch
        if deps.FAST_MODE_ENABLED:  # Use concurrent fetch strategy when fast mode is active
            max_workers = deps.FAST_MODE_MAX_CONCURRENT_CONNECTIONS  # Respect configured worker cap
            logging.info(
                "Fast mode: fetching VC stats for %d switches with %d concurrent workers",
                len(switches),
                max_workers,
            )  # Log concurrency plan before pool starts
            with ThreadPoolExecutor(max_workers=max_workers) as executor:  # Spawn bounded worker pool
                future_to_switch = {
                    executor.submit(cls._fetch_vc_for_switch, deps, switch): switch for switch in switches
                }  # Submit one VC fetch future per switch
                with deps.tqdm(total=len(switches), desc="Switches", unit="switch") as progress:
                    for future in as_completed(future_to_switch):  # Consume completed futures as they finish
                        if deps.ConfigUtils.check_stop_signal():  # Honor stop signal between completions
                            break  # Exit early while keeping already-completed results
                        result = future.result()  # Resolve merged VC row or None from worker
                        if result is not None:  # Keep only successful merged rows
                            all_vc_stats.append(result)  # Append successful row to export accumulator
                        progress.update(1)  # Advance progress for each completed future
            return all_vc_stats  # Return concurrent-collection results

        for switch in deps.tqdm(switches, desc="Switches", unit="switch"):
            if deps.ConfigUtils.check_stop_signal():  # Honor stop signal between sequential fetches
                break  # Exit early while keeping already-collected rows
            result = cls._fetch_vc_for_switch(deps, switch)  # Fetch VC stats for current switch
            if result is not None:  # Keep only successful merged rows
                all_vc_stats.append(result)  # Append successful row to export accumulator
        return all_vc_stats  # Return sequential-collection results

    @staticmethod
    def _emit_debug_preview(all_vc_stats: list[dict[str, Any]]) -> None:
        """Emit first-row sample and compact summary table for debug logs."""
        if not all_vc_stats:  # Nothing to preview when export rows are empty
            return  # Exit early with no preview output
        logging.debug("Sample VC stats row: %s", all_vc_stats[0])  # Log first row for raw payload visibility
        try:  # PrettyTable may fail if columns are malformed; keep preview non-fatal
            from prettytable import PrettyTable  # Lazy import to match existing MistHelper display behavior

            table = PrettyTable()  # Build compact summary table for debug readability
            summary_fields = [
                "name",
                "mac",
                "model",
                "serial",
                "site_id",
                "vc_mac",
                "status",
                "members_0_vc_role",
                "members_1_vc_role",
            ]  # Keep summary aligned with prior in-method preview fields
            table.field_names = [field for field in summary_fields if field in all_vc_stats[0]]  # Keep present cols
            for row in all_vc_stats:  # Add one summary row per switch
                table.add_row([row.get(field, "") for field in table.field_names])  # Extract display fields
            logging.debug("\n%s", table.get_string())  # Emit rendered summary table to debug log
        except Exception as preview_error:  # Never fail export because preview generation failed
            logging.debug("Skipping VC stats PrettyTable preview due to error: %s", preview_error)  # Trace skip cause

    @classmethod
    def execute(cls) -> None:
        """Run switch VC stats export workflow and write OrgSwitchVCStats.csv."""
        deps = _resolve_runtime_dependencies()  # Resolve all runtime collaborators from MistHelper
        print("Switch Virtual Chassis Statistics:")  # User-facing operation banner
        logging.info("Exporting all switch virtual chassis stats...")  # Log workflow start for operators

        switches = cls._load_switches(deps)  # Load VC-eligible switch rows from cached OrgInventory.csv
        if not switches:  # Nothing to process when inventory has no VC switches
            logging.warning("No switches found in OrgInventory.csv.")  # Log empty-input condition
            return  # Exit without producing a stats file

        all_vc_stats = cls._collect_vc_stats(deps, switches)  # Fetch/merge VC stats across all switches
        logging.info("Flattening and sanitizing %d VC stats entries for CSV export.", len(all_vc_stats))  # Trace size
        all_vc_stats = deps.DataProcessingUtils.flatten_nested_fields(all_vc_stats)  # Flatten nested fields for CSV
        all_vc_stats = deps.DataProcessingUtils.escape_multiline(all_vc_stats)  # Sanitize multiline fields
        deps.DataExporter.write_with_format_selection(all_vc_stats, "OrgSwitchVCStats.csv")  # Persist VC stats
        print(f"! {len(all_vc_stats)} switch VC stats exported to OrgSwitchVCStats.csv")  # User-facing result count
        logging.info(
            "! Switch VC stats exported to OrgSwitchVCStats.csv (%d records).",
            len(all_vc_stats),
        )  # Log success
        cls._emit_debug_preview(all_vc_stats)  # Emit optional debug preview for operator diagnostics
