"""SFPTransceiverDataProcessor -- SFP/transceiver CSV merge for menu 77.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 27).
Correlates OrgDevicePortStats.csv (per-port optics) with AllDevicesWithSiteInfo.csv
(device+site context) and writes MergedTransceiverData.csv. All methods are
static -- no state is kept on the class. Callers continue to reach it through
the ``MistHelper.SFPTransceiverDataProcessor`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import csv  # WHY: DictReader for header-keyed CSV parsing of port stats + device inventory.
import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for merge lifecycle events.
import os  # WHY: filesystem existence checks for prerequisite CSVs.


class SFPTransceiverDataProcessor:
    """Process and correlate SFP / transceiver data with site & device context.

    RATIONALE:
        This logic was previously a standalone function (`process_and_merge_csv_for_sfp_address`).
        It is only invoked by menu option 77 and has no tight coupling with most runtime state.
        Encapsulating it in a class improves hierarchy and opens the door for future extensions
        (e.g., JSON export, filtering, unit tests) without growing the legacy global scope.

    SECURITY:
        Operates only on locally generated CSV artifacts inside the controlled `data/` directory.
        No external network or credential usage. Filenames are static and not user-injected.
    """

    OUTPUT_FILENAME = "MergedTransceiverData.csv"

    @staticmethod
    def _ensure_prerequisite_csvs(org_port_stats_path: str, devices_with_site_info_path: str) -> None:
        """Generate prerequisite CSVs (port stats and devices-with-site-info) if missing."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of exporter facades.
        logging.debug(
            "ENTRY: _ensure_prerequisite_csvs(%s, %s)",
            org_port_stats_path,
            devices_with_site_info_path,
        )  # Trace entry with both target paths
        if not os.path.exists(org_port_stats_path):  # Port-stats CSV missing -> regenerate it
            print("* OrgDevicePortStats.csv not found. Generating it now...")  # User-facing notice
            logging.info(
                "OrgDevicePortStats.csv missing; invoking OrgDeviceStatsExporter.device_port_stats()"
            )  # Action log before generating port-stats CSV
            mh.OrgDeviceStatsExporter.device_port_stats()  # Generate the port-stats CSV
        if not os.path.exists(devices_with_site_info_path):  # Devices+site CSV missing -> regenerate it
            print("* AllDevicesWithSiteInfo.csv not found. Generating it now...")  # User-facing notice
            logging.info(
                "AllDevicesWithSiteInfo.csv missing; invoking OrgInventoryExporter.devices_with_site_info()"
            )  # Action log before generating devices+site CSV
            mh.OrgInventoryExporter.devices_with_site_info()  # Generate the devices+site CSV
        logging.debug("EXIT: _ensure_prerequisite_csvs")  # Trace exit

    @staticmethod
    def _load_device_site_context(devices_with_site_info_path: str) -> dict[str, dict[str, str]]:
        """Load device->site mapping keyed by MAC from the devices-with-site-info CSV."""
        logging.debug("ENTRY: _load_device_site_context(%s)", devices_with_site_info_path)  # Trace entry
        logging.debug("File I/O: Reading %s", devices_with_site_info_path)  # Trace the read for I/O auditing
        with open(devices_with_site_info_path, encoding="utf-8") as file:  # Open device+site CSV
            reader = csv.DictReader(file)  # Header-keyed reader for stable field access
            site_info = {
                row["mac"]: {
                    "site_name": row.get("site_name", ""),
                    "site_address": row.get("site_address", ""),
                    "device_name": row.get("name", ""),
                }
                for row in reader  # Build a MAC-keyed lookup of site context for every row
            }
        logging.info("Loaded %s device entries from %s", len(site_info), devices_with_site_info_path)  # Summary
        return site_info  # Return the MAC->site context map

    @staticmethod
    def _extract_transceiver_row(
        row: dict[str, str], site_info: dict[str, dict[str, str]]
    ) -> tuple[dict[str, str] | None, bool, str | None]:
        """Return (merged_row|None, has_transceiver, mac_with_transceiver|None) for one port-stats row."""
        mac = row.get("mac")  # Pull MAC for site-info lookup
        transceiver_model = row.get("xcvr_model", "").strip()  # Normalize transceiver model string
        if not transceiver_model:  # No optic populated -> not a candidate
            return (None, False, None)  # Skip this row entirely
        if mac not in site_info:  # Optic present but device MAC absent from inventory
            return (None, True, None)  # Counted as candidate but no merge row produced
        merged_row = {
            "site_name": site_info[mac]["site_name"],
            "site_address": site_info[mac]["site_address"],
            "device_name": site_info[mac]["device_name"],
            "port_id": row.get("port_id", ""),
            "transceiver_part_number": row.get("xcvr_part_number", ""),
            "transceiver_model": transceiver_model,
            "transceiver_serial_number": row.get("xcvr_serial", ""),
        }  # Compose merged row preserving exact field semantics of the original loop body
        return (merged_row, True, mac)  # Candidate with merged row and matched MAC

    @staticmethod
    def _scan_port_stats(
        org_port_stats_path: str, site_info: dict[str, dict[str, str]]
    ) -> tuple[list[dict[str, str]], int, int, int, set[str]]:
        """Read port-stats CSV and merge rows whose MAC is in site_info and have a non-empty optic."""
        logging.debug("ENTRY: _scan_port_stats(%s)", org_port_stats_path)  # Trace entry
        merged_data: list[dict[str, str]] = []  # Output rows collected here
        total_rows = candidate_rows = matched_rows = 0  # Init all three row counters at once
        unique_devices_with_transceivers: set[str] = set()  # Track distinct MACs that contributed an output row
        logging.debug("File I/O: Reading %s", org_port_stats_path)  # Trace the read for I/O auditing
        with open(org_port_stats_path, encoding="utf-8") as file:  # Open port-stats CSV
            reader = csv.DictReader(file)  # Header-keyed reader
            for row in reader:  # Iterate every port-stats row
                total_rows += 1  # Always increment total row counter
                merged_row, has_transceiver, mac_match = SFPTransceiverDataProcessor._extract_transceiver_row(
                    row, site_info
                )  # Per-row extraction handles transceiver + MAC logic
                if has_transceiver:  # Rows with a non-empty optic count as candidates
                    candidate_rows += 1  # Increment candidate counter
                if merged_row is None:  # No merge contribution from this row
                    continue  # Skip to next row to keep nesting shallow
                matched_rows += 1  # Row produced an output entry
                merged_data.append(merged_row)  # Append the merged row to output
                if mac_match is not None:  # Track unique MACs that contributed an output row
                    unique_devices_with_transceivers.add(mac_match)  # Record this MAC
        logging.debug("EXIT: _scan_port_stats matched=%d", matched_rows)  # Trace exit with match count
        return merged_data, total_rows, candidate_rows, matched_rows, unique_devices_with_transceivers

    @staticmethod
    def _log_merge_summary(
        matched_rows: int,
        total_rows: int,
        candidate_rows: int,
        site_info_count: int,
        unique_devices_count: int,
    ) -> None:
        """Emit the exact INFO log message corresponding to the matched-rows outcome."""
        if matched_rows == 0:  # No matching transceivers found path
            logging.info(
                "Processed port stats; no matching transceivers found. total_rows=%d candidate_rows=%d known_devices=%d. "  # noqa: E501
                "This can be normal if the inventory currently has no optics populated.",
                total_rows,
                candidate_rows,
                site_info_count,
            )  # Preserve the original DataExporter-zero-rows informational message verbatim
            return  # Early return keeps the success-path log on a flat branch
        logging.info(
            "Processed port stats; %d ports with transceivers found (total_rows=%d candidate_rows=%d unique_devices=%d)",  # noqa: E501
            matched_rows,
            total_rows,
            candidate_rows,
            unique_devices_count,
        )  # Preserve the original success-path informational message verbatim

    @staticmethod
    def _finalize_merge_output(merged_data: list[dict[str, str]]) -> None:
        """Write merged rows to disk and emit the success-path INFO and user-facing messages."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter helper.
        mh.DataExporter.write_with_format_selection(
            merged_data, SFPTransceiverDataProcessor.OUTPUT_FILENAME
        )  # Write merged rows to backend
        logging.info(
            "Wrote %s rows to %s", len(merged_data), SFPTransceiverDataProcessor.OUTPUT_FILENAME
        )  # Log the row count written
        print(
            f"! Merged data written to {SFPTransceiverDataProcessor.OUTPUT_FILENAME}"
        )  # Tell the user where the file landed
        logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - success")  # Trace successful exit

    @staticmethod
    def _run_merge_pipeline(org_port_stats_path: str, devices_with_site_info_path: str) -> None:
        """Run load->scan->summary->write inside a unified try/except for CSV/IO failures."""
        try:
            site_info = SFPTransceiverDataProcessor._load_device_site_context(devices_with_site_info_path)
            merged_data, total_rows, candidate_rows, matched_rows, unique_devices = (
                SFPTransceiverDataProcessor._scan_port_stats(org_port_stats_path, site_info)
            )  # Scan port stats and produce merged rows + counters
            SFPTransceiverDataProcessor._log_merge_summary(
                matched_rows, total_rows, candidate_rows, len(site_info), len(unique_devices)
            )  # Emit the matched-rows-aware summary log
            SFPTransceiverDataProcessor._finalize_merge_output(merged_data)  # Persist + notify user
        except FileNotFoundError as e:  # Missing input CSV
            logging.error("File I/O: Required CSV file not found: %s", e)  # Log absent file
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - file not found")  # Trace
            raise  # Re-raise to caller
        except csv.Error as e:  # Malformed CSV
            logging.error("File I/O: CSV processing error: %s", e)  # Log parse error
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - CSV error")  # Trace
            raise  # Re-raise to caller
        except Exception as e:  # Any other unexpected failure during the merge
            logging.error("File I/O: Unexpected error during transceiver merge: %s", e)  # Log unexpected
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - unexpected error")  # Trace
            raise  # Re-raise to caller

    @staticmethod
    def merge_transceiver_data() -> None:
        """Generate a merged transceiver CSV linking port optics to site + device context.

        Steps:
            1. Ensure prerequisite CSVs exist (generate if missing):
               - OrgDevicePortStats.csv
               - AllDevicesWithSiteInfo.csv
            2. Load device/site context keyed by MAC.
            3. Filter port stats to rows containing a non-empty transceiver model.
            4. Write merged result to `MergedTransceiverData.csv` via DataExporter.
        """
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils helper.
        logging.debug("ENTRY: SFPTransceiverDataProcessor.merge_transceiver_data()")  # Trace entry
        org_port_stats_path = mh.FilePathUtils.get_csv_path("OrgDevicePortStats.csv")  # Source: per-port stats CSV
        devices_with_site_info_path = mh.FilePathUtils.get_csv_path("AllDevicesWithSiteInfo.csv")  # Source: device+site
        SFPTransceiverDataProcessor._ensure_prerequisite_csvs(
            org_port_stats_path, devices_with_site_info_path
        )  # Generate either prerequisite CSV if missing
        SFPTransceiverDataProcessor._run_merge_pipeline(
            org_port_stats_path, devices_with_site_info_path
        )  # Load->scan->summary->write inside one try/except
