"""OfflineDeviceReporter -- offline-device inventory report (Menu 158).

Extracted from MistHelper.py during initiative 1013 (Cat B, position 44)
under the SC-001 facade pattern. Scans org inventory via
listOrgDevicesStats, filters devices offline beyond a user-configurable
threshold (default 48h), displays summary + PrettyTable, and saves a
human-readable CSV to data/.

Direct imports cover stdlib (importlib, logging, time, datetime.datetime)
and third-party (prettytable.PrettyTable). Every live-global read
(``IS_TEST_MODE``, ``InputUtils``, ``APICoreFetchUtils``, ``mistapi``,
``apisession``, ``DataExporter``, ``ConfigUtils``) is resolved via lazy
``mh = importlib.import_module("MistHelper")`` inside the methods that
need them. Callers continue to reach the class through the
``MistHelper.OfflineDeviceReporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace + info/warn/error logging.
import time  # WHY: wall-time epoch + elapsed timing.
from datetime import datetime  # WHY: format epoch to human timestamp. Timestamp CSV filename.
from typing import Any  # WHY: device dicts carry heterogeneous values.

from prettytable import PrettyTable  # WHY: render offline device rows as a table.

from src.utils.console import echo  # WHY: 1031 stdout + INFO log helper replaces legacy WARNING-channel echoes.


class OfflineDeviceReporter:  # Offline device inventory report.
    """Offline Device Report (Menu 158).

    Scans org inventory via listOrgDevicesStats, filters devices offline
    beyond a user-configurable threshold (default 48h), displays summary
    and PrettyTable on screen, saves human-readable CSV to data/.

    Usage:
        OfflineDeviceReporter.execute()
    """

    MAX_DISPLAY_ROWS = 50
    DEFAULT_THRESHOLD_HOURS = 48
    MIN_THRESHOLD_HOURS = 1
    MAX_THRESHOLD_HOURS = 8760
    MAX_INPUT_RETRIES = 3

    @staticmethod
    def _parse_threshold_attempt(raw: str) -> int | None:
        """Parse one user attempt. Return validated hours or None to retry."""
        try:
            hours = int(raw)  # Coerce to int.
            min_h = OfflineDeviceReporter.MIN_THRESHOLD_HOURS  # Local alias for line length.
            max_h = OfflineDeviceReporter.MAX_THRESHOLD_HOURS  # Local alias for line length.
            if min_h <= hours <= max_h:
                return hours  # Valid -- accept.
            logging.warning(
                "! Threshold must be between %s and %s hours.", min_h, max_h
            )  # Out-of-range echo via logger.
        except ValueError:
            logging.warning("! Invalid input '%s'. Please enter a number.", raw)  # Bad-type echo via logger.
        return None

    @staticmethod
    def _prompt_threshold() -> int:
        """Prompt user for offline threshold in hours, with validation."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of IS_TEST_MODE + InputUtils.
        if mh.IS_TEST_MODE:  # Test mode skips interactive prompt.
            logging.debug("Test mode: using default threshold 48 hours")  # Log shortcut.
            return OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS  # Default value.
        for attempt in range(OfflineDeviceReporter.MAX_INPUT_RETRIES):  # Bounded retry loop.
            raw = mh.InputUtils.safe_input(
                f"Enter offline threshold in hours (default {OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS}): ",
                default_value=str(OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS),
                context="offline_threshold",
            )  # EOF-safe input.
            parsed = OfflineDeviceReporter._parse_threshold_attempt(raw)  # Validate this attempt.
            if parsed is not None:  # Valid value.
                return parsed
            remaining = OfflineDeviceReporter.MAX_INPUT_RETRIES - attempt - 1  # Attempts left.
            if remaining > 0:
                echo("  (%s attempt(s) remaining)", remaining)
        logging.warning("Max retries exceeded for threshold input, using default 48 hours")  # Log fallback.
        echo("  Using default threshold: %s hours", OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS)
        return OfflineDeviceReporter.DEFAULT_THRESHOLD_HOURS

    @staticmethod
    def _fetch_data(current_org_id: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
        """Fetch site lookup and device stats from Mist API."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APICoreFetchUtils/mistapi/apisession.
        logging.info("Fetching site information for offline device report...")
        echo("  Fetching site information...")
        all_sites = mh.APICoreFetchUtils.all_sites_with_limit(current_org_id)
        site_lookup: dict[str, str] = {}
        for site in all_sites:
            site_id = site.get("id")
            if site_id:
                site_lookup[site_id] = site.get("name", "Unknown Site")

        logging.info("Fetching device stats for offline device report...")
        echo("  Fetching device statistics...")
        stats_resp = mh.mistapi.api.v1.orgs.stats.listOrgDevicesStats(
            mh.apisession, current_org_id, type="all", status="all", fields="*", limit=1000
        )
        all_devices: list[dict[str, Any]] = mh.mistapi.get_all(response=stats_resp, mist_session=mh.apisession)
        logging.info("Retrieved stats for %s devices", len(all_devices))
        echo("  Retrieved %s devices from API", len(all_devices))
        return site_lookup, all_devices

    @staticmethod
    def _format_offline_timing(last_seen_epoch: float, offline_seconds: float) -> tuple[str, str, float]:
        """Return (last_seen_str, duration_str, sort_key) for one offline device."""
        if last_seen_epoch == 0.0:  # Device has never connected.
            return "Never Connected", "Never Connected", float("inf")
        last_seen_str = datetime.fromtimestamp(last_seen_epoch).strftime(
            "%Y-%m-%d %H:%M:%S"
        )  # Human-readable timestamp.
        total_hours = int(offline_seconds // 3600)  # Whole hours offline.
        days, hours = total_hours // 24, total_hours % 24  # Split into days and hours.
        duration_str = f"{days} days {hours} hours" if days > 0 else f"{hours} hours"  # Pick format.
        return last_seen_str, duration_str, offline_seconds

    @staticmethod
    def _compile_offline_record(
        device: dict, site_lookup: dict[str, str], last_seen_str: str, duration_str: str, sort_key: float
    ) -> dict:
        """Build the display/CSV record for one offline device."""
        device_type_raw = device.get("type", "unknown")  # Raw device type from API.
        type_display = {"ap": "AP", "switch": "Switch", "gateway": "Gateway"}.get(
            device_type_raw, device_type_raw.capitalize()
        )  # Friendly label.
        site_name = site_lookup.get(device.get("site_id", ""), "Unknown Site")  # Resolve site name.
        device_name = device.get("name") or "(unnamed)"  # Name fallback.
        return {
            "Device Name": device_name,
            "Device Type": type_display,
            "Site Name": site_name,
            "MAC Address": device.get("mac", ""),
            "Serial Number": device.get("serial", ""),
            "Model": device.get("model", ""),
            "Last Seen": last_seen_str,
            "Offline Duration": duration_str,
            "Status": device.get("status", "disconnected"),
            "_sort_key": str(sort_key),
        }

    @staticmethod
    def _parse_last_seen_epoch(device: dict) -> float:
        """Coerce a device's ``last_seen`` field to a float epoch (returns 0.0 when missing/blank)."""
        last_seen_raw = device.get("last_seen") or 0  # Treat None/blank/0 uniformly as 0
        if not last_seen_raw:  # Explicit guard so the float() cast can never see empty
            return 0.0
        return float(last_seen_raw)  # Numeric epoch ready for arithmetic

    @staticmethod
    def _maybe_build_offline_record(
        device: dict, site_lookup: dict[str, str], now: float, threshold_seconds: int
    ) -> dict | None:
        """Return offline record for device if it qualifies as offline. None to skip."""
        if device.get("status") == "connected":  # Skip currently-connected devices
            return None
        last_seen_epoch = OfflineDeviceReporter._parse_last_seen_epoch(device)  # Float epoch (0.0 = never seen)
        offline_seconds = now - last_seen_epoch  # Time since last contact
        if offline_seconds < threshold_seconds and last_seen_epoch > 0:  # Inside threshold + seen before
            return None
        last_seen_str, duration_str, sort_key = OfflineDeviceReporter._format_offline_timing(
            last_seen_epoch, offline_seconds
        )  # Format display values
        return OfflineDeviceReporter._compile_offline_record(device, site_lookup, last_seen_str, duration_str, sort_key)

    @staticmethod
    def _process_devices(
        all_devices: list[dict[str, Any]],
        site_lookup: dict[str, str],
        threshold_hours: int,
    ) -> list[dict[str, Any]]:
        """Filter offline devices beyond threshold, enrich with site names."""
        now = time.time()  # Current epoch.
        threshold_seconds = threshold_hours * 3600  # Convert threshold to seconds.
        offline_records: list[dict[str, Any]] = []  # Accumulator.
        for device in all_devices:  # Walk all devices once.
            record = OfflineDeviceReporter._maybe_build_offline_record(
                device, site_lookup, now, threshold_seconds
            )  # Build or skip.
            if record is not None:  # Device qualifies as offline.
                offline_records.append(record)
        offline_records.sort(key=lambda r: float(r["_sort_key"]), reverse=True)  # Sort by offline duration desc.
        return offline_records

    @staticmethod
    def _render_offline_breakdowns(type_counts: dict[str, int], site_counts: dict[str, int]) -> None:
        """Print 'By Type' and 'Top 5 Sites' breakdowns from precomputed counts."""
        echo("\nBy Type:")
        for device_type in ["AP", "Switch", "Gateway"]:  # Stable display order.
            count = type_counts.get(device_type, 0)  # Lookup count.
            if count > 0:  # Suppress zeros.
                echo("  %ss: %s", device_type, count)
        sorted_sites = sorted(site_counts.items(), key=lambda item: item[1], reverse=True)[:5]  # Top 5 by count.
        if sorted_sites:
            echo("\nTop 5 Sites:")
            for rank, (site_name, count) in enumerate(sorted_sites, 1):  # Rank each top site.
                echo("  %s. %s: %s offline", rank, site_name, count)

    @staticmethod
    def _display_summary(
        total_device_count: int,
        offline_records: list[dict[str, str]],
        threshold_hours: int,
    ) -> None:
        """Display summary statistics before the detail table."""
        echo("\n--- Summary ---")
        echo("Total devices in org: %s", f"{total_device_count:,}")
        echo("Devices offline > %s hours: %s", threshold_hours, len(offline_records))
        type_counts: dict[str, int] = {}  # Per-type tally.
        site_counts: dict[str, int] = {}  # Per-site tally.
        for record in offline_records:  # Walk each offline record once.
            type_counts[record["Device Type"]] = type_counts.get(record["Device Type"], 0) + 1  # Bump type.
            site_counts[record["Site Name"]] = site_counts.get(record["Site Name"], 0) + 1  # Bump site.
        OfflineDeviceReporter._render_offline_breakdowns(type_counts, site_counts)  # Render breakdowns.

    _OFFLINE_DISPLAY_FIELDS: tuple[str, ...] = (
        "Device Name",
        "Device Type",
        "Site Name",
        "MAC Address",
        "Serial Number",
        "Model",
        "Last Seen",
        "Offline Duration",
        "Status",
    )

    @staticmethod
    def _save_offline_csv(offline_records: list[dict[str, str]], total_count: int) -> None:
        """Build CSV rows and persist via shared exporter. Log + print result."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter.
        fields = OfflineDeviceReporter._OFFLINE_DISPLAY_FIELDS  # Column order.
        csv_records = [{f: record.get(f, "") for f in fields} for record in offline_records]  # Strip helper keys.
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")  # Timestamp for filename.
        filename = f"OfflineDeviceReport_{timestamp_str}.csv"  # Output filename.
        mh.DataExporter.write_with_format_selection(
            data=csv_records, filename_or_table=filename, api_function_name="listOrgDevicesStats"
        )  # Persist.
        logging.info("CSV saved: data/%s (%s devices)", filename, total_count)  # Log save.
        echo("\nCSV saved: data/%s (%s devices)", filename, total_count)

    @staticmethod
    def _present_results(offline_records: list[dict[str, str]]) -> None:  # Render and save offline results.
        """Display PrettyTable and save CSV for offline devices."""
        fields = OfflineDeviceReporter._OFFLINE_DISPLAY_FIELDS  # Column order.
        total_count = len(offline_records)  # Total rows.
        show_count = min(total_count, OfflineDeviceReporter.MAX_DISPLAY_ROWS)  # Cap display.
        echo("\n--- Offline Devices (showing %s of %s) ---", show_count, total_count)
        table = PrettyTable()  # Build display table.
        table.field_names = list(fields)  # Set columns.
        for record in offline_records[:show_count]:  # Show capped rows.
            table.add_row([record.get(f, "") for f in fields])  # Add each row.
        echo("%s", table)
        OfflineDeviceReporter._save_offline_csv(offline_records, total_count)  # Persist CSV + log.

    @staticmethod
    def _gather_offline_inputs() -> tuple[str | None, int]:
        """Resolve org_id + threshold prompt; (None, _) signals early-abort."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils.
        current_org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        if not current_org_id:  # No org selected.
            echo("! No organization selected. Exiting.")
            return None, 0  # Caller must abort.
        threshold_hours = OfflineDeviceReporter._prompt_threshold()  # Prompt threshold.
        echo("Threshold: %s hours\n", threshold_hours)
        return current_org_id, threshold_hours

    @staticmethod
    def _finalize_offline_report(
        total_count: int, offline_records: list[dict], threshold_hours: int, start_time: float
    ) -> None:
        """Display summary + present results + log elapsed for offline report."""
        OfflineDeviceReporter._display_summary(total_count, offline_records, threshold_hours)  # Summary section.
        OfflineDeviceReporter._present_results(offline_records)  # Detail table + CSV.
        elapsed = time.time() - start_time  # Elapsed wall time.
        logging.info("Offline device report completed in %.1f seconds", elapsed)  # Log duration.
        echo("\nReport completed in %.1f seconds", elapsed)

    @staticmethod
    def execute() -> None:  # Run the offline report.
        """Main entry point for offline device report (Menu 158)."""
        echo("\n=== Offline Device Report ===")
        logging.info("Starting offline device report...")  # Log start.
        start_time = time.time()  # Start timer.
        current_org_id, threshold_hours = OfflineDeviceReporter._gather_offline_inputs()  # Org + threshold.
        if not current_org_id:  # Abort signaled.
            return
        try:
            site_lookup, all_devices = OfflineDeviceReporter._fetch_data(current_org_id)  # Fetch sites + devices.
        except Exception as error:  # Fetch failed.
            logging.error("Failed to fetch data from Mist API: %s", error)  # Log error.
            echo("! Failed to fetch data. Please check your API credentials and network connection.")
            return
        if not all_devices:  # No devices in org.
            logging.info("No devices found in organization")  # Log it.
            echo("No devices found in this organization.")
            return
        offline_records = OfflineDeviceReporter._process_devices(all_devices, site_lookup, threshold_hours)  # Filter.
        if not offline_records:  # Nothing offline.
            echo("No devices found offline for more than %s hours. All clear!", threshold_hours)
            logging.info("No devices offline beyond %sh threshold", threshold_hours)  # Log all-clear.
            return
        OfflineDeviceReporter._finalize_offline_report(len(all_devices), offline_records, threshold_hours, start_time)
