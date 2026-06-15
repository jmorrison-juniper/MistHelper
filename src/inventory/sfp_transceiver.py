"""SFP / transceiver data correlation processor.

Extracted from the MistHelper monolith so this logic lives in a single, testable home
under ``src/`` instead of being duplicated inline. ``MistHelper.py`` imports the class
from here, making this module the single source of truth (no inline copy, no facade).

RATIONALE:
    This logic was previously a standalone function (``process_and_merge_csv_for_sfp_address``).
    It is only invoked by menu option 77 and has no tight coupling with most runtime state.
    Encapsulating it in a class improves hierarchy and opens the door for future extensions
    (e.g., JSON export, filtering, unit tests) without growing the monolithic global scope.

SECURITY:
    Operates only on locally generated CSV artifacts inside the controlled ``data/`` directory.
    No external network or credential usage. Filenames are static and not user-injected.
"""

import csv  # Parse the prerequisite CSV artifacts (port stats + device/site info)
import logging  # Emit structured action logs for every step of the merge
import os  # Probe the filesystem to detect missing prerequisite CSVs


class SFPTransceiverDataProcessor:
    """Process and correlate SFP / transceiver data with site & device context."""

    OUTPUT_FILENAME = "MergedTransceiverData.csv"  # Static output name written to the data/ dir

    @staticmethod
    def merge_transceiver_data():
        """Generate a merged transceiver CSV linking port optics to site + device context.

        Steps:
            1. Ensure prerequisite CSVs exist (generate if missing):
               - OrgDevicePortStats.csv
               - AllDevicesWithSiteInfo.csv
            2. Load device/site context keyed by MAC.
            3. Filter port stats to rows containing a non-empty transceiver model.
            4. Write merged result to `MergedTransceiverData.csv` via DataExporter.
        """
        # Late import from the monolith avoids a circular import at module load time:
        # MistHelper.py imports this class near its definition site, so these names are
        # only resolved when the menu actually runs the merge (well after both modules load).
        from MistHelper import (
            DataExporter,  # Multi-backend writer used to persist the merged rows
            export_device_port_stats_to_csv,  # Generates OrgDevicePortStats.csv when missing
            export_devices_with_site_info_to_csv,  # Generates AllDevicesWithSiteInfo.csv when missing
            get_csv_file_path,  # Resolves a filename to its canonical path in the data/ dir
        )

        logging.debug("ENTRY: SFPTransceiverDataProcessor.merge_transceiver_data()")  # Trace entry for diagnostics

        org_port_stats_path = get_csv_file_path("OrgDevicePortStats.csv")  # Resolve port-stats CSV path
        devices_with_site_info_path = get_csv_file_path("AllDevicesWithSiteInfo.csv")  # Resolve device/site CSV path

        # Generate prerequisites if absent (idempotent behavior matches prior function)
        if not os.path.exists(org_port_stats_path):  # Port-stats CSV is required input; create if missing
            print("* OrgDevicePortStats.csv not found. Generating it now...")  # Inform the operator
            # Regenerate the missing port-stats CSV from the Mist API before merging
            logging.info("OrgDevicePortStats.csv missing; invoking export_device_port_stats_to_csv()")
            export_device_port_stats_to_csv()  # Build the port-stats CSV from the Mist API

        if not os.path.exists(devices_with_site_info_path):  # Device/site CSV is required input; create if missing
            print("* AllDevicesWithSiteInfo.csv not found. Generating it now...")  # Inform the operator
            # Regenerate the missing device/site CSV from the Mist API before merging
            logging.info("AllDevicesWithSiteInfo.csv missing; invoking export_devices_with_site_info_to_csv()")
            export_devices_with_site_info_to_csv()  # Build the device/site CSV from the Mist API

        try:
            # Load context keyed by MAC
            logging.debug(f"File I/O: Reading {devices_with_site_info_path}")  # Trace the file being read
            with open(devices_with_site_info_path, encoding="utf-8") as file:  # Open device/site CSV (read mode)
                reader = csv.DictReader(file)  # Treat each row as a dict keyed by header name
                site_info = {  # Build a MAC -> {site/device context} lookup for fast joins
                    row["mac"]: {  # Key the lookup on the device MAC address
                        "site_name": row.get("site_name", ""),  # Site name (blank if absent)
                        "site_address": row.get("site_address", ""),  # Site street address (blank if absent)
                        "device_name": row.get("name", ""),  # Device hostname from the 'name' column
                    }
                    for row in reader  # Iterate every device/site row
                }
            logging.info(f"Loaded {len(site_info)} device entries from {devices_with_site_info_path}")

            merged_data = []  # Accumulator for the joined output rows
            total_rows = 0  # Count of every port-stats row examined
            # candidate_rows: rows with a non-empty optic model (may not map to a known device MAC)
            candidate_rows = 0  # Tally of rows that have a populated transceiver model
            matched_rows = 0  # rows contributing to merged output
            unique_devices_with_transceivers: set[str] = set()  # Distinct MACs that contributed optics

            logging.debug(f"File I/O: Reading {org_port_stats_path}")  # Trace the file being read
            with open(org_port_stats_path, encoding="utf-8") as file:  # Open port-stats CSV (read mode)
                reader = csv.DictReader(file)  # Treat each row as a dict keyed by header name
                for row in reader:  # Walk every port-stats row
                    total_rows += 1  # Tally the row toward the grand total
                    mac = row.get("mac")  # Device MAC used to join against site_info
                    # Optic model; blank string means no transceiver present in this port
                    transceiver_model = row.get("xcvr_model", "").strip()

                    if transceiver_model:  # Only rows with a populated optic model are candidates
                        candidate_rows += 1  # Tally the candidate optic row

                    # Keep rows that both carry an optic and map to a known device MAC
                    if mac in site_info and transceiver_model:
                        matched_rows += 1  # Tally the contributing row
                        unique_devices_with_transceivers.add(mac)  # Record the distinct device MAC
                        merged_data.append(
                            {  # Emit the joined site + device + optic record
                                "site_name": site_info[mac]["site_name"],  # Site name from the lookup
                                "site_address": site_info[mac]["site_address"],  # Site address from the lookup
                                "device_name": site_info[mac]["device_name"],  # Device hostname from the lookup
                                "port_id": row.get("port_id", ""),  # Physical port the optic is seated in
                                "transceiver_part_number": row.get("xcvr_part_number", ""),  # Optic part number
                                "transceiver_model": transceiver_model,  # Optic model (already stripped above)
                                "transceiver_serial_number": row.get("xcvr_serial", ""),  # Optic serial number
                            }
                        )

            if matched_rows == 0:
                # Use INFO (not WARNING): an empty optic set is a legitimate state. DataExporter
                # itself emits a WARNING when handed 0 rows, so we explain the cause here.
                logging.info(
                    "Processed port stats; no matching transceivers found. "
                    "total_rows=%d candidate_rows=%d known_devices=%d. "
                    "Normal if the inventory currently has no optics populated.",
                    total_rows,
                    candidate_rows,
                    len(site_info),  # Counts that explain the empty result
                )
            else:
                # Summarize the successful merge with the contributing counts
                logging.info(
                    "Processed port stats; %d ports with transceivers found "
                    "(total_rows=%d candidate_rows=%d unique_devices=%d)",
                    matched_rows,
                    total_rows,
                    candidate_rows,
                    len(unique_devices_with_transceivers),
                )

            # Persist the merged rows through the selected output backend (CSV/SQLite/etc.)
            DataExporter.save_data_to_output(merged_data, SFPTransceiverDataProcessor.OUTPUT_FILENAME)
            logging.info(f"Wrote {len(merged_data)} rows to {SFPTransceiverDataProcessor.OUTPUT_FILENAME}")
            print(f"! Merged data written to {SFPTransceiverDataProcessor.OUTPUT_FILENAME}")  # Confirm completion
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - success")  # Trace exit
        except FileNotFoundError as e:  # A prerequisite CSV vanished between the check and the read
            logging.error(f"File I/O: Required CSV file not found: {e}")  # Log the missing-file detail
            # Trace the failure path before propagating to the caller
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - file not found")
            raise  # Re-raise so the caller/menu surfaces the error
        except csv.Error as e:  # The CSV parser rejected malformed content
            logging.error(f"File I/O: CSV processing error: {e}")  # Log the parse error detail
            # Trace the failure path before propagating to the caller
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - CSV error")
            raise  # Re-raise so the caller/menu surfaces the error
        except Exception as e:  # Catch-all guard so unexpected failures are logged before propagating
            logging.error(f"File I/O: Unexpected error during transceiver merge: {e}")  # Log the detail
            # Trace the failure path before propagating to the caller
            logging.debug("EXIT: SFPTransceiverDataProcessor.merge_transceiver_data - unexpected error")
            raise  # Re-raise so the caller/menu surfaces the error
