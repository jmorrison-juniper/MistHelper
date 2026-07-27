"""CacheUtils -- centralized cache management utilities.

Extracted from MistHelper.py during initiative 1014 (Cat E, position 14).
Canonical body lives here; MistHelper.py provides a top-level re-export
alias (``from src.cache.cache_utils import CacheUtils``) so historical
``MistHelper.CacheUtils`` / ``mh.CacheUtils`` callers keep working.

Cross-class references (``FilePathUtils``) and the module-level
``CSV_FRESHNESS_MINUTES`` constant are resolved lazily via
``importlib.import_module("MistHelper")`` inside method bodies to keep
FR-028 IG-health clean (no top-level MistHelper import statement).
"""

from __future__ import annotations  # WHY: PEP 604 unions in annotations.

import csv  # WHY: CSV reading/writing helpers.
import importlib  # WHY: lazy MistHelper fetch of FilePathUtils + CSV_FRESHNESS_MINUTES.
import logging  # WHY: debug/trace + failure reporting.
import os  # WHY: filesystem existence checks + listdir/remove.
import time  # WHY: fast_cache_hit uses time.time() for age math.
from collections.abc import Callable  # WHY: generator callable annotation for CSV producers.
from datetime import datetime, timedelta  # WHY: mtime comparisons in freshness gate.
from typing import Any  # WHY: dynamic row payload annotations.


class CacheUtils:
    """Centralized cache management utilities.

    Handles CSV caching, freshness checks, regeneration, and so on
    """

    _ADDRESS_PARSE_FAILURE_FIELDNAMES: list[str] = [  # Stable column order for AddressParseFailures CSV
        "site_id",
        "site_name",
        "device_id",
        "device_serial",
        "device_name",
        "original_address",
        "parsed_tokens",
        "failure_reason",
        "timestamp",
    ]

    @staticmethod
    def check_and_generate_csv(
        file_name: str,
        generate_function: Callable,  # type: ignore[type-arg]
        freshness_minutes: int | None = None,
    ) -> bool:
        """Return True if file_name's CSV exists and is fresh; otherwise run generate_function.

        freshness_minutes defaults to CSV_FRESHNESS_MINUTES (.env). Returns True when the file is
        fresh or was regenerated successfully, False if regeneration failed.
        """
        logging.debug(
            "ENTRY: CacheUtils.check_and_generate_csv(file_name=%s, generate_function=%s, freshness_minutes=%s)",
            file_name,
            generate_function.__name__,
            freshness_minutes,
        )

        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils + CSV_FRESHNESS_MINUTES.
        if freshness_minutes is None:  # No explicit override supplied
            freshness_minutes = mh.CSV_FRESHNESS_MINUTES  # Fall back to the configured default freshness

        full_file_path = mh.FilePathUtils.get_csv_path(file_name)  # Resolve the CSV path under data/
        if CacheUtils._is_csv_fresh(full_file_path, file_name, freshness_minutes):  # Existing file still fresh?
            return True  # Use the cached file -- no regeneration needed
        return CacheUtils._run_csv_generator(generate_function, file_name)  # Stale/missing -- (re)generate now

    @staticmethod
    def _is_csv_fresh(full_file_path: str, file_name: str, freshness_minutes: int) -> bool:  # Cache freshness check
        """Return True only when the file exists and was modified within freshness_minutes (else regenerate)."""
        if not os.path.exists(full_file_path):  # File missing entirely
            logging.info("* %s not found. Generating...", file_name)  # Tell operator it will be generated
            return False  # Not fresh -- caller regenerates
        try:  # Reading mtime can fail on permission/metadata errors
            file_mtime = datetime.fromtimestamp(os.path.getmtime(full_file_path))  # Last-modified timestamp
            logging.debug("File I/O: read mtime for %s: %s", full_file_path, file_mtime)  # Trace the mtime read
            if datetime.now() - file_mtime < timedelta(minutes=freshness_minutes):  # Within the freshness window
                logging.info("! Using cached %s (fresh)", file_name)  # Tell operator the cache is being used
                return True  # Fresh -- skip regeneration
            logging.info("* %s is older than %s minutes. Regenerating...", file_name, freshness_minutes)  # Stale notice
            return False  # Stale -- caller regenerates
        except OSError as error:  # Could not read the file's metadata
            logging.error("File I/O: Failed to read modification time for %s: %s", full_file_path, error)  # Log failure
            logging.info("* %s exists but cannot read metadata. Regenerating...", file_name)  # Tell operator
            return False  # Treat unreadable metadata as stale

    @staticmethod
    def _run_csv_generator(generate_function: Callable, file_name: str) -> bool:  # type: ignore[type-arg]  # Run generator
        """Invoke the generate_function to produce the CSV; return True on success, False on failure."""
        logging.info("* Running %s to generate %s...", generate_function.__name__, file_name)  # Log before generating
        try:  # The generator may raise; never let that crash the caller
            generate_function()  # Produce or refresh the CSV file
            logging.info("! %s generated or refreshed.", file_name)  # Confirm success to operator
            return True  # Generation succeeded
        except Exception as error:  # Generation failed for any reason
            logging.error("Failed to generate %s using %s: %s", file_name, generate_function.__name__, error)  # Log it
            return False  # Generation failed

    @staticmethod
    def load_csv_grouped_by_key(filename: str, key: str) -> dict[str, list[dict[str, Any]]]:
        """Load a CSV into a dict keyed by the named column; value is the list of rows sharing it."""
        logging.info(
            "Loading CSV file '%s' into dictionary keyed by '%s'...", filename, key
        )  # Log before reading the file
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        csv_file_path = mh.FilePathUtils.get_csv_path(filename)  # Resolve the CSV path under the data/ directory
        with open(csv_file_path, encoding="utf-8") as file:  # Open the CSV for reading
            reader = csv.DictReader(file)  # Parse each row into a dictionary keyed by column name
            data_dict: dict[str, list[dict[str, Any]]] = {}  # Group rows by the chosen key column
            row_count = 0  # Count how many valid rows we ingest
            for row in reader:  # Process each CSV row
                data_key = row.get(key)  # Extract the grouping key value from this row
                if data_key is None:  # The key column is missing on this row
                    logging.warning("Row missing key '%s': %s", key, row)  # Warn about the malformed row
                    continue  # Skip rows that cannot be grouped
                if data_key not in data_dict:  # First time we've seen this key value
                    data_dict[data_key] = []  # Start a new bucket for it
                data_dict[data_key].append(row)  # Add this row to its key's bucket
                row_count += 1  # Tally the ingested row
            logging.info(
                "Loaded %s rows from '%s'. Found %s unique keys for '%s'.", row_count, filename, len(data_dict), key
            )  # Summary log
        return data_dict  # Return the grouped-by-key dictionary

    @staticmethod
    def _collect_csv_fieldnames(data: dict[str, list[dict[str, Any]]]) -> list[str]:
        """Return sorted union of keys across every row in every section."""
        fieldnames: set[str] = set()  # Accumulate every distinct key seen across all sections
        for section_name, section in data.items():  # Walk each named section once
            logging.debug("Processing section '%s' with %s rows.", section_name, len(section))
            for row in section:  # Each row contributes its keys to the union
                fieldnames.update(row.keys())  # Set update is O(k) and dedupes for us
        return sorted(fieldnames)  # Sort so the CSV column order is deterministic

    @staticmethod
    def _write_data_rows_to_csv(writer: csv.DictWriter, data: dict[str, list[dict[str, Any]]]) -> int:  # type: ignore[type-arg]
        """Write every row from every section through writer; return total row count."""
        row_count = 0  # Tally rows actually written so the caller can log the total
        for section in data.values():  # Iterate sections in insertion order; keys are unused here
            for row in section:  # Write each row through the DictWriter
                writer.writerow(row)  # csv handles encoding/escaping for us
                row_count += 1  # Increment after a successful write
        return row_count  # Caller logs this for operator visibility

    @staticmethod
    def write_support_data_to_csv(data: dict[str, list[dict[str, Any]]], filename: str) -> None:
        """Write the support package (dict of section -> rows) to filename under data/."""
        logging.debug("Preparing to write support package to %s...", filename)  # Log before doing IO
        fieldnames_sorted = CacheUtils._collect_csv_fieldnames(data)  # Union of keys, deterministic order
        logging.debug("Final CSV fieldnames: %s", fieldnames_sorted)  # Trace exact header order
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        csv_file_path = mh.FilePathUtils.get_csv_path(filename)  # SECURITY: anchor under data/
        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:  # Open for writing
            writer = csv.DictWriter(file, fieldnames=fieldnames_sorted)  # Bind writer to fixed header
            writer.writeheader()  # Emit header before any data rows
            row_count = CacheUtils._write_data_rows_to_csv(writer, data)  # Stream all rows through
            logging.info("Wrote %s rows to %s for support package.", row_count, csv_file_path)
        logging.info("Support package written to %s", csv_file_path)  # Final success message

    # Known generated cache CSV filenames -- cleared by Menu 175
    GENERATED_FILES: set[str] = {  # Explicit list of MistHelper-generated cache CSVs to protect non-data files
        "AllDevicesWithSiteInfo.csv",
        "GatewayDeviceStats.csv",
        "GatewayDeviceStatsWithSiteInfo.csv",
        "GatewayMgmtIPs.csv",
        "OrgDeviceEvents.csv",
        "OrgInventory.csv",
        "OrgSwitchVCStats.csv",
        "PortStats.csv",
        "SiteList.csv",
        "SitePortStats.csv",
        "VPNPeerStats.csv",
    }

    # Generated CSV filename prefixes -- any file in data/ matching these is a cache candidate
    GENERATED_PREFIXES: tuple[str, ...] = (  # Prefixes that identify auto-generated cache files
        "AllDevices",
        "AuditLogs",
        "DeviceEvents",
        "DevicePort",
        "Gateway",
        "Org",
        "Port",
        "Site",
        "Switch",
        "VPN",
    )

    @staticmethod
    def _is_generated_file(filename: str) -> bool:  # Check if file is MistHelper-generated
        """Return True if the filename matches a known generated cache file."""
        name = os.path.basename(filename)  # Strip any path component for clean matching
        if name in CacheUtils.GENERATED_FILES:  # Exact match against the explicit allowlist
            return True  # Explicitly listed -- safe to delete
        if name.endswith(".csv") and name.startswith(CacheUtils.GENERATED_PREFIXES):  # Prefix match
            return True  # Prefix match -- safe to delete
        return False  # Not a recognised generated file -- leave it alone

    @staticmethod
    def clear_cache() -> None:  # Menu 175: delete all generated cache CSVs from data/ directory
        """Delete all MistHelper-generated cache CSV files from the data/ directory."""
        data_dir = "data"  # Relative path to data/ consistent with FilePathUtils.get_csv_path()
        logging.info("Scanning data directory for generated cache CSVs: %s", data_dir)  # Log scan target
        candidates = CacheUtils._scan_cache_candidates(data_dir)  # List safe-to-delete files (None on scan error)
        if candidates is None:  # Directory could not be listed (already reported by the scanner)
            return  # Abort -- nothing to delete if we cannot list the directory
        if not candidates:  # Nothing to delete -- inform operator and return early
            # WHY (#886 Phase 2): consolidate print+info into single WARNING so operator sees notice
            # on the default root-logger config (INFO is suppressed by default).
            logging.warning("No generated cache CSV files found to delete.")
            return  # Early return -- nothing to do
        logging.warning(
            "Found %d generated cache CSV file(s) to delete:", len(candidates)
        )  # Show operator what will be removed (WARNING surfaces on default root-logger)
        for name in sorted(candidates):  # Sort for readable output
            logging.warning("  %s", name)  # List each file so operator knows exactly what is affected
        deleted, errors = CacheUtils._delete_cache_files(data_dir, candidates)  # Delete each file, counting outcomes
        # WHY (#886 Phase 2): consolidate print+info into single WARNING for post-run operator summary.
        logging.warning("Cache cleared: %d file(s) deleted, %d error(s).", deleted, errors)

    @staticmethod
    def _scan_cache_candidates(data_dir: str) -> list[str] | None:  # List generated cache files, or None on error
        """Return the list of generated cache filenames in data_dir, or None if the directory cannot be listed."""
        logging.debug("Listing generated cache candidates in %s", data_dir)  # Trace the scan before listing
        try:  # Listing can fail on permissions or a missing directory
            return [
                name for name in os.listdir(data_dir) if CacheUtils._is_generated_file(name)
            ]  # Keep only MistHelper-generated cache files (safe to delete)
        except OSError as scan_error:  # Permission or missing-directory error
            logging.error("Failed to list data directory %s: %s", data_dir, scan_error)  # Log I/O failure with context
            # WHY (#886 Phase 2): retire print() in favor of logging.error (surfaces on default root-logger).
            logging.error("Error scanning data directory: %s", scan_error)
            return None  # Signal the caller to abort

    @staticmethod
    def _delete_cache_files(data_dir: str, candidates: list[str]) -> tuple[int, int]:  # Delete files, count outcomes
        """Delete each candidate cache file; return (deleted_count, error_count)."""
        deleted = 0  # Track successful deletions for summary
        errors = 0  # Track failures for summary
        for name in candidates:  # Delete each identified cache file
            full_path = os.path.join(data_dir, name)  # Build the path for deletion
            logging.info("Deleting cache CSV: %s", full_path)  # Log before deletion for audit trail
            try:  # Individual deletions may fail without aborting the batch
                os.remove(full_path)  # Delete the file from disk
                logging.debug("Deleted: %s", full_path)  # Confirm deletion at debug level
                deleted += 1  # Increment success counter
            except OSError as delete_error:  # Handle individual file deletion failures
                logging.error("Failed to delete %s: %s", full_path, delete_error)  # Log failure with path and reason
                # WHY (#886 Phase 2): retire print() in favor of logging.error (surfaces on default root-logger).
                logging.error("  Could not delete %s: %s", name, delete_error)
                errors += 1  # Increment error counter
        return deleted, errors  # Report totals to the caller

    @staticmethod
    def create_address_parse_failures_csv(
        parse_failures: list[dict[str, Any]], filename: str = "AddressParseFailures.csv"
    ) -> None:
        """Write address-parse failures to a CSV in data/; safe no-op when list is empty."""
        if not parse_failures:
            logging.info("No address parsing failures to document.")
            return
        try:
            mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
            output_path = mh.FilePathUtils.get_csv_path(filename)  # Resolve target path under data/
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CacheUtils._ADDRESS_PARSE_FAILURE_FIELDNAMES)
                writer.writeheader()  # Header row first
                for failure in parse_failures:
                    writer.writerow(failure)  # One row per failure record
            logging.info("Address parsing failures documented in: %s (%s records)", filename, len(parse_failures))
            # WHY (#886 Phase 2): consolidate print+info into single WARNING so operator sees notice
            # on the default root-logger config (INFO is suppressed by default).
            logging.warning("Address parsing failures documented in: %s (%d records)", filename, len(parse_failures))
        except Exception as e:
            logging.error("Failed to create address parse failures CSV: %s", e)
            # WHY (#886 Phase 2): retire print() in favor of logging.error (surfaces on default root-logger).
            logging.error("Failed to create address parse failures CSV: %s", e)

    @staticmethod
    def fast_cache_hit(filename: str, max_age_minutes: int = 60) -> bool:  # Check if cached output file is fresh
        """Return True when filename exists in data/ and is younger than max_age_minutes."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils.
        full_path = mh.FilePathUtils.get_csv_path(filename)  # Resolve path inside data/ directory
        logging.debug("fast_cache_hit check for %s (max_age=%d min)", filename, max_age_minutes)  # Log check
        if not os.path.exists(full_path):  # File not present -- always a miss
            logging.debug("fast_cache_hit MISS: %s not found", filename)  # Log miss reason
            return False  # Cache miss -- caller should generate the file
        try:
            age_seconds = time.time() - os.path.getmtime(full_path)  # Seconds since last modification
            age_minutes = age_seconds / 60.0  # Convert to minutes for readable comparison
            if age_minutes <= max_age_minutes:  # File is within the freshness window
                # WHY (#886 Phase 2): consolidate print+info into single WARNING so operator sees
                # the cache-hit notice on the default root-logger config (INFO is suppressed).
                logging.warning("Using cached %s (%.0f min old) -- skipping re-generation.", filename, age_minutes)
                return True  # Cache hit -- caller can skip expensive work
            logging.debug("fast_cache_hit MISS: %s is stale (%.1f min old)", filename, age_minutes)  # Log stale
            return False  # File is too old -- cache miss
        except OSError as stat_error:  # Handle race conditions or permission issues
            logging.warning("fast_cache_hit: could not stat %s: %s", filename, stat_error)  # Log I/O issue
            return False  # Treat stat failure as a miss to be safe
