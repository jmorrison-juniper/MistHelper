"""Inventory CSV comparison for address verification.

Extracts AddressComparisonCounters and InventoryCSVComparator from
MistHelper.py into a module with dependency injection for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations  # WHY: enable postponed evaluation for typing hints.

import csv  # WHY: comparison CSV load/save requires DictReader/DictWriter.
import glob  # WHY: enumerate candidate comparison CSVs by wildcard.
import logging  # WHY: emit debug/info/warning traces for observability.
import os  # WHY: env vars + path joins.
import time  # WHY: timing counters wrap perf-heavy comparison phase.
import traceback  # WHY: capture full stack when Nominatim validation raises.
from collections.abc import Callable  # WHY: type hint injected dependency functions.
from dataclasses import dataclass  # WHY: group injected params + item configs.
from datetime import UTC, datetime  # WHY: parse device created_time to ISO week key.
from typing import Any  # WHY: injected classes/dicts are heterogeneous.

from dotenv import load_dotenv  # WHY: load ADDRESS_MATCH_THRESHOLD/END_CUSTOMER_NAME.
from tqdm import tqdm  # WHY: progress bar over device iteration.

from src.utils.input_utils import InputUtils  # WHY: EOF-safe input wrapper (issue #452).


class AddressComparisonCounters:
    """Track comprehensive metrics for address comparison operations."""

    def __init__(self) -> None:
        """Initialize all counter attributes and timing."""
        self.total_devices: int = 0  # WHY: rolled up in final summary/rate calc.
        self.devices_enriched: int = 0  # WHY: matched by serial to comparison CSV.
        self.devices_skipped: int = 0  # WHY: no comparison row or empty address.
        self.perfect_matches: int = 0  # WHY: addresses within threshold similarity.
        self.mismatches_found: int = 0  # WHY: fed downstream to conflict report.
        self.auto_corrections: int = 0  # WHY: increments per AddressSkip hit.
        self.comparison_failures: int = 0  # WHY: exceptions during per-device compare.
        self.parse_failures: int = 0  # WHY: totals unparseable Mist addresses.
        self.parse_failure_reasons: dict[str, int] = {}  # WHY: histogram by reason code.
        self.start_time: float | None = None  # WHY: measures throughput.
        self.end_time: float | None = None  # WHY: pairs with start_time for duration.

    def start_timing(self) -> None:
        """Start the timing counter for performance tracking."""
        self.start_time = time.time()  # WHY: monotonic-ish wallclock start.

    def end_timing(self) -> None:
        """End the timing counter for performance tracking."""
        self.end_time = time.time()  # WHY: pairs with start_time in get_duration.

    def get_duration(self) -> float:
        """Get the elapsed time in seconds between start and end timing."""
        if self.start_time is None or self.end_time is None:  # WHY: defensive when unset.
            return 0.0  # WHY: safe default that avoids divide-by-zero downstream.
        return self.end_time - self.start_time  # WHY: return seconds elapsed.

    def increment_parse_failure(self, reason: str) -> None:
        """Increment parse failure counter and track the specific reason.

        Args:
            reason: The specific reason for the parse failure.
        """
        self.parse_failures += 1  # WHY: aggregate total across reasons.
        if reason in self.parse_failure_reasons:  # WHY: histogram lookup.
            self.parse_failure_reasons[reason] += 1  # WHY: bump existing reason count.
        else:
            self.parse_failure_reasons[reason] = 1  # WHY: seed a new reason bucket.

    def log_summary(self) -> None:
        """Log a comprehensive summary of all counter metrics."""
        logging.info("Address comparison operation completed successfully")  # WHY: anchor log for tailers.
        logging.info("Total devices processed: %s", self.total_devices)  # WHY: capacity/perf reference.
        logging.info("Devices enriched: %s", self.devices_enriched)  # WHY: analysed subset size.
        logging.info("Devices skipped: %s", self.devices_skipped)  # WHY: measures data gap.
        logging.info("Perfect matches: %s", self.perfect_matches)  # WHY: baseline "clean" count.
        logging.info("Mismatches found: %s", self.mismatches_found)  # WHY: main output signal.
        logging.info("Auto corrections: %s", self.auto_corrections)  # WHY: measures skip-list impact.
        logging.info("Comparison failures: %s", self.comparison_failures)  # WHY: reliability signal.
        logging.info("Parse failures: %s", self.parse_failures)  # WHY: data-quality signal.
        if self.parse_failure_reasons:  # WHY: only log breakdown when non-empty.
            logging.info("Parse failure breakdown: %s", self.parse_failure_reasons)  # WHY: reason histogram.
        logging.info("Processing duration: %.2f seconds", self.get_duration())  # WHY: perf reference.


@dataclass
class ComparisonItemConfig:
    """Configuration for building mismatch and diff report items."""

    device: dict[str, Any]  # WHY: original device row from Mist inventory.
    device_serial: str  # WHY: primary key for reporting/logging.
    mist_address: dict[str, str]  # WHY: parsed Mist address components.
    comparison_address: dict[str, str]  # WHY: parsed comparison-CSV address.
    comparison_result: dict[str, Any]  # WHY: fuzzy-match verdict + similarities.
    week_key: str  # WHY: ISO year+week for weekly rollups.
    mismatch_type: str  # WHY: categorises which fields diverged.
    validation_result: dict[str, Any] | None  # WHY: optional Nominatim verdict.


@dataclass
class ComparatorFlags:
    """Runtime toggles for InventoryCSVComparator."""

    fast: bool = False  # WHY: enables cached data generation.
    address_check: bool = False  # WHY: opts into Nominatim validation.
    debug: bool = False  # WHY: verbose logging + traceback capture.
    skip_ssl_verify: bool = True  # WHY: default relaxed for internal APIs.


@dataclass
class ComparatorDependencies:
    """Injected callables and classes used by the comparator."""

    apisession: Any  # WHY: authenticated mistapi session for org lookups.
    get_csv_path_fn: Callable[[str], str]  # WHY: resolves relative CSV names to disk paths.
    check_and_generate_csv_fn: Callable[..., Any]  # WHY: cache-and-generate wrapper.
    create_parse_failures_csv_fn: Callable[..., Any]  # WHY: emits parse-failure CSV.
    devices_with_site_info_fn: Callable[..., Any]  # WHY: generator for device+site rows.
    get_org_id_fn: Callable[..., str]  # WHY: cached/prompted org id for validation.
    get_device_identifier_fn: Callable[..., str]  # WHY: user-facing device label.
    address_utils_cls: Any  # WHY: parse/normalize/compare address utilities.
    nominatim_validator_cls: type  # WHY: external validation service class.
    address_validation_config_cls: type  # WHY: config dataclass for validator.


@dataclass
class RecordComparisonInputs:
    """Bundle of per-device state passed to _record_comparison_result."""

    device: dict[str, Any]  # WHY: retained on conflict for downstream reporting.
    device_serial: str  # WHY: primary key across all conflict/skip records.
    device_identifier: str  # WHY: human-readable label reused in preview.
    mist_address: dict[str, str]  # WHY: parsed source-of-truth address.
    comparison_address: dict[str, str]  # WHY: parsed comparison-target address.
    comparison_result: dict[str, Any]  # WHY: similarity + failed-field verdict.


# WHY: table-driven classifier — reduces nested if/elif in _detect_address_fields.
_ADDRESS_FIELD_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("address_field", ("address", "street", "address line")),  # WHY: main street field.
    ("city_field", ("city",)),  # WHY: city component.
    ("state_field", ("state",)),  # WHY: state/province component.
    ("country_field", ("country",)),  # WHY: country component.
)

# WHY: table-driven mismatch categoriser — replaces if/elif ladder.
_MISMATCH_TYPE_TABLE: tuple[tuple[str, str], ...] = (
    ("address", "Address Mismatch"),  # WHY: prefer address label when it fails.
    ("city", "City Mismatch"),  # WHY: fall back to city label.
    ("state", "State Mismatch"),  # WHY: fall back to state label.
)


class InventoryCSVComparator:  # pylint: disable=too-many-instance-attributes
    """Compare Mist inventory data with external CSV files for address verification.

    Performs multi-step comparison workflow:
    1. Load and parse Mist device data with site information
    2. Select and load comparison CSV with automatic field detection
    3. Parse and normalize addresses using enhanced parsing
    4. Detect duplicate addresses between sites
    5. Filter conflicts through skip list and deduplication
    6. Optional external validation via Nominatim API
    7. Generate comprehensive mismatch reports

    Uses configurable ADDRESS_MATCH_THRESHOLD from .env file for fuzzy matching.
    """

    # WHY: fixed lead-in columns shared by mismatch + diff reports.
    _COMMON_FIELDS: tuple[str, ...] = (
        "Week",
        "Full Site",
        "System Serial Number",
        "System Model Number",
        "End Customer Name",
    )
    # WHY: diff-specific column set — Mist + Comparison side by side.
    _DIFF_ADDRESS_FIELDS: tuple[str, ...] = (
        "Mist_Address_Line_1",
        "Mist_City",
        "Mist_State",
        "Mist_Zip_Code",
        "Mist_Zip_Normalized",
        "Comparison_Address",
        "Comparison_City",
        "Comparison_State",
        "Comparison_Zip_Code",
        "Comparison_Zip_Normalized",
    )
    # WHY: trailing metadata columns shared across reports.
    _TRAILING_FIELDS: tuple[str, ...] = (
        "End Customer Account ID",
        "Mismatch Type",
        "Overall Similarity",
        "Address Similarity",
        "City Similarity",
        "State Similarity",
        "Zip Similarity",
        "Failed Fields",
        "Mist_Parse_Status",
        "Comparison_Parse_Status",
        "Parse_Issues",
        "Mist_Validation_Status",
        "Mist_Confidence",
        "Comparison_Validation_Status",
        "Comparison_Confidence",
        "Validation_Recommendation",
    )

    def __init__(
        self,
        flags: ComparatorFlags,
        deps: ComparatorDependencies,
    ) -> None:
        """Initialize the inventory comparator with grouped config + dependencies.

        Args:
            flags: Runtime toggles bundle (fast/address_check/debug/skip_ssl_verify).
            deps: Injected callables and classes bundle.
        """
        self._store_flags(flags)  # WHY: expose boolean toggles as instance attrs.
        self._store_deps(deps)  # WHY: expose injected callables/classes as instance attrs.
        self._init_state()  # WHY: initialise mutable run state for a comparison invocation.

    def _store_flags(self, flags: ComparatorFlags) -> None:
        """Copy runtime flags onto the instance for hot-path access."""
        self.fast = flags.fast  # WHY: consumed by cache-aware data generation.
        self.address_check = flags.address_check  # WHY: gates Nominatim validation.
        self.debug = flags.debug  # WHY: gates verbose logging + tracebacks.
        self.skip_ssl_verify = flags.skip_ssl_verify  # WHY: passed through to validator.

    def _store_deps(self, deps: ComparatorDependencies) -> None:
        """Copy injected callables and classes onto the instance."""
        self._api = deps.apisession  # WHY: mistapi session for org lookups.
        self._get_csv_path = deps.get_csv_path_fn  # WHY: relative-to-absolute CSV path.
        self._check_and_generate_csv = deps.check_and_generate_csv_fn  # WHY: cache wrapper.
        self._create_parse_failures_csv = deps.create_parse_failures_csv_fn  # WHY: parse-failure CSV.
        self._devices_with_site_info = deps.devices_with_site_info_fn  # WHY: source-data generator.
        self._get_org_id = deps.get_org_id_fn  # WHY: cached/prompted org id fetch.
        self._get_device_identifier = deps.get_device_identifier_fn  # WHY: user-facing label.
        self._address_utils = deps.address_utils_cls  # WHY: parse/normalize utilities.
        self._nominatim_validator_cls = deps.nominatim_validator_cls  # WHY: external validator class.
        self._address_validation_config_cls = deps.address_validation_config_cls  # WHY: validator config.

    def _init_state(self) -> None:
        """Initialize mutable state for a comparison run."""
        self._init_config_state()  # WHY: env-derived thresholds/tenant identity.
        self._init_lookup_state()  # WHY: CSV data + field detection caches.
        self._init_run_state()  # WHY: per-run counters + collected records.

    def _init_config_state(self) -> None:
        """Initialise env-driven configuration state."""
        self.address_threshold: float = 75.0  # WHY: default until .env override applies.
        self.end_customer_name: str = ""  # WHY: rolled into mismatch report columns.
        self.end_customer_account_id: str = ""  # WHY: rolled into mismatch report columns.
        self.address_validation_enabled: bool = False  # WHY: derived from flag+env below.

    def _init_lookup_state(self) -> None:
        """Initialise CSV-derived lookup dictionaries."""
        self.site_configs: list[dict[str, Any]] = []  # WHY: rows from device inventory CSV.
        self.comparison_data: list[dict[str, Any]] = []  # WHY: rows from selected comparison CSV.
        self.skip_addresses: list[dict[str, Any]] = []  # WHY: AddressSkip rows for auto-correct.
        self.comparison_file: str = ""  # WHY: filename selected by user.
        self.serial_field: str | None = None  # WHY: detected header for serial column.
        self.zip_field: str | None = None  # WHY: detected header for zip column.
        self.address_field: str | None = None  # WHY: detected header for street column.
        self.city_field: str | None = None  # WHY: detected header for city column.
        self.state_field: str | None = None  # WHY: detected header for state column.
        self.country_field: str | None = None  # WHY: detected header for country column.
        self.comparison_serials: dict[str, str] = {}  # WHY: serial -> normalised zip.
        self.comparison_address_lookup: dict[str, dict[str, str]] = {}  # WHY: serial -> address dict.
        self.mist_duplicates: dict[str, list[str]] = {}  # WHY: address_key -> list of Mist site names.
        self.ref_duplicates: dict[str, list[str]] = {}  # WHY: address_key -> list of reference sites.

    def _init_run_state(self) -> None:
        """Initialise per-run counters and result collections."""
        self.counters = AddressComparisonCounters()  # WHY: aggregate metrics across the run.
        self.parse_failures: list[dict[str, Any]] = []  # WHY: rows for the parse-failures CSV.
        self.all_conflicts: list[dict[str, Any]] = []  # WHY: raw mismatches pre-dedup.
        self.filtered_conflicts: list[dict[str, Any]] = []  # WHY: after dedup + skip-list filters.
        self.mismatched_items: list[dict[str, Any]] = []  # WHY: rows for mismatch report.
        self.diff_report_items: list[dict[str, Any]] = []  # WHY: rows for diff-report CSV.

    def execute(self) -> None:
        """Execute the complete inventory comparison workflow."""
        self.counters.start_timing()  # WHY: bracket the whole run for perf metrics.
        # WHY: iterate guard-returning steps to keep cyclomatic complexity low.
        guarded_steps: tuple[Callable[[], bool], ...] = (
            self._initialize_config,  # WHY: env + header.
            self._load_source_data,  # WHY: Mist devices+sites.
            self._select_comparison_file,  # WHY: user picks CSV.
            self._load_comparison_data,  # WHY: parse selected CSV.
        )
        for step in guarded_steps:  # WHY: short-circuit on first failure.
            if not step():  # WHY: any False halts the workflow.
                return  # WHY: preserve original early-return semantics.
        self._load_skip_addresses()  # WHY: optional AddressSkip loader.
        if not self._detect_csv_fields():  # WHY: required-field detection can still fail.
            return  # WHY: bail if headers cannot be resolved.
        self._run_processing_phase()  # WHY: remaining phases have no guards.

    def _run_processing_phase(self) -> None:
        """Execute post-load processing phases in fixed order."""
        self._build_lookup_dictionaries()  # WHY: keyed indices for O(1) serial lookup.
        self._detect_duplicate_addresses()  # WHY: pre-flight duplicate diagnostics.
        self._process_all_devices()  # WHY: run comparisons per device.
        self._filter_conflicts()  # WHY: dedup + skip-list filtering.
        self._process_remaining_conflicts()  # WHY: optional Nominatim validation.
        self._finalize_and_display_results()  # WHY: emit reports + summary.

    # =================================================================
    # INITIALIZATION METHODS
    # =================================================================

    def _initialize_config(self) -> bool:
        """Load environment configuration and display header."""
        load_dotenv()  # WHY: pull END_CUSTOMER_* + ADDRESS_MATCH_THRESHOLD.
        self.end_customer_name = os.getenv("END_CUSTOMER_NAME", "")  # WHY: mismatch column value.
        self.end_customer_account_id = os.getenv("END_CUSTOMER_ACCOUNT_ID", "")  # WHY: mismatch column value.
        self.address_threshold = float(os.getenv("ADDRESS_MATCH_THRESHOLD", "75"))  # WHY: fuzzy threshold.
        self._print_header()  # WHY: user-facing config summary.
        self._determine_validation_mode()  # WHY: sets address_validation_enabled flag.
        return True  # WHY: this step cannot currently fail — sentinel for uniform guard interface.

    def _print_header(self) -> None:
        """Display the operation header with configuration info."""
        print("* Data Integrity Analysis: Comparing Mist vs Comparison" " CSV addresses...")  # WHY: banner.
        print(f"* Using address similarity threshold:" f" {self.address_threshold}%")  # WHY: echo threshold.
        # WHY: feature banner announcing parsing/matching capabilities.
        print("* Enhanced features: defensive parsing, Unicode" " normalization, fuzzy matching")
        if self.fast:  # WHY: only announce fast mode when enabled.
            print("* Fast mode enabled: Using optimized data generation" " and caching")  # WHY: user visibility.
        if self.debug:  # WHY: debug-only diagnostics.
            print(" Debug mode enabled: Detailed comparison logging active")  # WHY: user visibility.
            logging.debug("ENTRY: InventoryCSVComparator.execute()")  # WHY: trace entry point.
            logging.debug("  Parameters: fast=%s, address_check=%s", self.fast, self.address_check)  # WHY: params.
            logging.debug("  ADDRESS_MATCH_THRESHOLD=%s", self.address_threshold)  # WHY: threshold trace.

    def _determine_validation_mode(self) -> None:
        """Determine if external address validation is enabled."""
        env_enabled = os.getenv("ENABLE_ADDRESS_VALIDATION", "false").lower() == "true"  # WHY: env override.
        self.address_validation_enabled = self.address_check or env_enabled  # WHY: flag OR env.
        if self.address_validation_enabled:  # WHY: split branches into helpers.
            self._announce_validation_enabled(env_enabled)  # WHY: user-facing enable notice.
        else:
            self._announce_validation_disabled()  # WHY: user-facing disable notice.

    def _announce_validation_enabled(self, env_enabled: bool) -> None:
        """Emit console + debug output when validation is enabled."""
        source = "--address-check flag" if self.address_check else ".env file"  # WHY: report source.
        print(f"! External address validation enabled via {source}")  # WHY: user visibility.
        print("   Address conflicts will be validated using" " Nominatim API")  # WHY: user visibility.
        if self.debug:  # WHY: debug-only trace.
            logging.debug("Address validation enabled via %s", source)  # WHY: trace source.
        _ = env_enabled  # WHY: retained arg documents callsite intent even if unused after refactor.

    def _announce_validation_disabled(self) -> None:
        """Emit console + debug output when validation is disabled."""
        print("  External address validation disabled")  # WHY: user visibility.
        print("   Use --address-check flag or set" " ENABLE_ADDRESS_VALIDATION=true")  # WHY: hint.
        if self.debug:  # WHY: debug-only trace.
            logging.debug("Address validation disabled")  # WHY: trace disabled state.

    # =================================================================
    # DATA LOADING METHODS
    # =================================================================

    def _load_source_data(self) -> bool:
        """Load Mist device data with site information."""

        def generator() -> Any:  # WHY: bind fast flag for cache wrapper.
            return self._devices_with_site_info(fast=self.fast)  # WHY: cache-friendly source.

        self._check_and_generate_csv("AllDevicesWithSiteInfo.csv", generator)  # WHY: refresh cache.
        devices_path = self._get_csv_path("AllDevicesWithSiteInfo.csv")  # WHY: resolve to absolute path.
        with open(devices_path, encoding="utf-8") as file_handle:  # WHY: UTF-8 handles unicode addresses.
            self.site_configs = list(csv.DictReader(file_handle))  # WHY: eagerly materialise rows.
        return True  # WHY: successful load.

    def _select_comparison_file(self) -> bool:
        """Present CSV file selection to user and get selection."""
        csv_files = self._get_available_csv_files()  # WHY: enumerate candidates.
        if not csv_files:  # WHY: nothing to compare against.
            print(" No CSV files found in the data directory" " for comparison.")  # WHY: user visibility.
            print("   Please place comparison CSV files in the" " 'data' folder.")  # WHY: guidance.
            logging.error("No CSV files found for comparison in data directory.")  # WHY: log record.
            return False  # WHY: cannot proceed.
        self._display_csv_file_list(csv_files)  # WHY: numbered menu.
        return self._get_user_csv_selection(csv_files)  # WHY: capture selection.

    def _get_available_csv_files(self) -> list[str]:
        """Get list of CSV files available for comparison."""
        data_dir = "data"  # WHY: canonical relative data folder.
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))  # WHY: enumerate CSVs.
        exclude_file = "AllDevicesWithSiteInfo.csv"  # WHY: never self-compare source data.
        return [os.path.basename(f) for f in csv_files if os.path.basename(f) != exclude_file]  # WHY: filter+basename.

    def _display_csv_file_list(self, csv_files: list[str]) -> None:
        """Display available CSV files for user selection."""
        print("\n  Available CSV files for comparison:")  # WHY: menu header.
        print("=" * 60)  # WHY: visual separator.
        for idx, csv_file in enumerate(csv_files):  # WHY: index-labelled menu.
            print(f"[{idx}] {csv_file}")  # WHY: menu entry.

    def _get_user_csv_selection(self, csv_files: list[str]) -> bool:
        """Get and validate user's CSV file selection."""
        try:
            # WHY: prompt shown when asking user to pick a CSV file by index.
            prompt = f"\nEnter the index (0-{len(csv_files) - 1})" " of the CSV file to compare against: "
            user_input = InputUtils.safe_input(prompt, context="csv_comparator_index")  # WHY: EOF-safe input.
            selected_index = int(user_input)  # WHY: numeric index.
            if selected_index < 0 or selected_index >= len(csv_files):  # WHY: range check.
                print(" Invalid index selected.")  # WHY: user visibility.
                logging.error("Invalid CSV file index selected: %s", selected_index)  # WHY: log record.
                return False  # WHY: cannot proceed.
            self.comparison_file = csv_files[selected_index]  # WHY: persist choice.
            print(f"! Selected comparison file:" f" {self.comparison_file}")  # WHY: echo choice.
            logging.info("User selected comparison file: %s", self.comparison_file)  # WHY: log record.
            return True  # WHY: success.
        except ValueError:  # WHY: non-numeric input.
            print(" Invalid input. Please enter a numeric index.")  # WHY: user visibility.
            logging.error("Invalid numeric input for CSV file selection.")  # WHY: log record.
            return False  # WHY: cannot proceed.
        except KeyboardInterrupt:  # WHY: user cancels.
            print("\n Operation cancelled by user.")  # WHY: user visibility.
            logging.info("CSV comparison operation cancelled by user.")  # WHY: log record.
            return False  # WHY: cannot proceed.

    def _load_comparison_data(self) -> bool:
        """Load the selected comparison CSV file."""
        try:
            comparison_path = self._get_csv_path(self.comparison_file)  # WHY: absolute path.
            with open(comparison_path, encoding="utf-8") as file_handle:  # WHY: UTF-8 read.
                self.comparison_data = list(csv.DictReader(file_handle))  # WHY: eager row load.
            print(f"! Loaded {len(self.site_configs)} devices from" " AllDevicesWithSiteInfo.csv")  # WHY: user info.
            print(f"! Loaded {len(self.comparison_data)} records from" f" {self.comparison_file}")  # WHY: user info.
            return True  # WHY: success.
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: catch-all around file IO.
            print(f"! Error reading comparison file" f" {self.comparison_file}: {error}")  # WHY: user visibility.
            logging.error("Error reading comparison file %s: %s", self.comparison_file, error)  # WHY: log record.
            return False  # WHY: cannot proceed.

    def _load_skip_addresses(self) -> None:
        """Load the address skip list for automatic corrections."""
        skip_file_path = self._get_csv_path("AddressSkip.csv")  # WHY: canonical skip-list name.
        try:
            with open(skip_file_path, encoding="utf-8") as file_handle:  # WHY: UTF-8 read.
                self.skip_addresses = list(csv.DictReader(file_handle))  # WHY: eager load.
            print(f"! Loaded {len(self.skip_addresses)} skip" " addresses from AddressSkip.csv")  # WHY: user info.
            if self.debug:  # WHY: debug detail.
                logging.debug("Loaded %s addresses to skip", len(self.skip_addresses))  # WHY: trace count.
        except FileNotFoundError:  # WHY: optional file.
            print("  AddressSkip.csv not found - no addresses" " will be automatically skipped")  # WHY: user info.
            if self.debug:  # WHY: debug detail.
                logging.debug("AddressSkip.csv not found - continuing" " without skip list")  # WHY: trace.
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: tolerate malformed skip file.
            print(f"!  Error loading AddressSkip.csv: {error}")  # WHY: user visibility.
            logging.warning("Error loading AddressSkip.csv: %s", error)  # WHY: log record.

    # =================================================================
    # FIELD DETECTION METHODS
    # =================================================================

    def _detect_csv_fields(self) -> bool:
        """Detect and validate required fields in comparison CSV."""
        if not self.comparison_data:  # WHY: empty file cannot be processed.
            print(" Comparison CSV file is empty.")  # WHY: user visibility.
            return False  # WHY: cannot proceed.
        headers = self.comparison_data[0].keys()  # WHY: first-row keys carry header names.
        self._detect_serial_field(headers)  # WHY: locate primary key column.
        self._detect_zip_field(headers)  # WHY: locate zip column.
        self._detect_address_fields(headers)  # WHY: locate address components.
        if not self._validate_required_fields(headers):  # WHY: serial+zip mandatory.
            return False  # WHY: cannot proceed.
        self._print_detected_fields()  # WHY: user visibility.
        return True  # WHY: success.

    def _detect_serial_field(self, headers: Any) -> None:
        """Detect the serial number field in comparison CSV."""
        serial_terms = ("serial", "sn", "system serial")  # WHY: matched header substrings.
        for header in headers:  # WHY: linear scan is O(cols).
            if any(term in header.lower() for term in serial_terms):  # WHY: case-insensitive match.
                self.serial_field = header  # WHY: capture first match.
                break  # WHY: first match wins.

    def _detect_zip_field(self, headers: Any) -> None:
        """Detect the zip code field in comparison CSV."""
        zip_terms = ("zip", "postal", "zip code", "postal code")  # WHY: matched header substrings.
        for header in headers:  # WHY: linear scan is O(cols).
            if any(term in header.lower() for term in zip_terms):  # WHY: case-insensitive match.
                self.zip_field = header  # WHY: capture first match.
                break  # WHY: first match wins.

    def _detect_address_fields(self, headers: Any) -> None:
        """Detect address component fields in comparison CSV."""
        for header in headers:  # WHY: linear scan over headers.
            self._classify_address_header(header)  # WHY: delegate to table-driven classifier.

    def _classify_address_header(self, header: str) -> None:
        """Assign header to matching address attribute using the term table."""
        lowered = header.lower()  # WHY: case-insensitive matching.
        for attr, terms in _ADDRESS_FIELD_TERMS:  # WHY: fixed dispatch table avoids elif ladder.
            if any(term in lowered for term in terms):  # WHY: substring match against terms.
                setattr(self, attr, header)  # WHY: assign detected column.
                return  # WHY: first-match wins per original semantics.

    def _validate_required_fields(self, headers: Any) -> bool:
        """Validate that required fields were detected."""
        if not self.serial_field:  # WHY: cannot map devices without serial.
            print(" Could not find serial number field" " in comparison CSV.")  # WHY: user visibility.
            print("   Looked for fields containing:" " 'serial', 'sn', 'system serial'")  # WHY: hint.
            print(f"   Available fields: {list(headers)}")  # WHY: debug help.
            logging.error("Serial field not found. Available fields: %s", list(headers))  # WHY: log record.
            return False  # WHY: cannot proceed.
        if not self.zip_field:  # WHY: cannot compare without zip.
            print(" Could not find zip code field" " in comparison CSV.")  # WHY: user visibility.
            print("   Looked for fields containing:" " 'zip', 'postal', 'zip code', 'postal code'")  # WHY: hint.
            print(f"   Available fields: {list(headers)}")  # WHY: debug help.
            logging.error("Zip field not found. Available fields: %s", list(headers))  # WHY: log record.
            return False  # WHY: cannot proceed.
        return True  # WHY: mandatory fields present.

    def _print_detected_fields(self) -> None:
        """Print the detected field mappings."""
        print(f"! Using serial field: '{self.serial_field}'")  # WHY: echo mandatory field.
        print(f"! Using zip field: '{self.zip_field}'")  # WHY: echo mandatory field.
        if self.address_field:  # WHY: only announce detected optional columns.
            print(f"! Using address field: '{self.address_field}'")  # WHY: user visibility.
        if self.city_field:  # WHY: only announce detected optional columns.
            print(f"! Using city field: '{self.city_field}'")  # WHY: user visibility.
        if self.state_field:  # WHY: only announce detected optional columns.
            print(f"! Using state field: '{self.state_field}'")  # WHY: user visibility.
        if self.country_field:  # WHY: only announce detected optional columns.
            print(f"! Using country field: '{self.country_field}'")  # WHY: user visibility.

    # =================================================================
    # LOOKUP BUILDER METHODS
    # =================================================================

    def _build_lookup_dictionaries(self) -> None:
        """Build lookup dictionaries from comparison data."""
        for row in self.comparison_data:  # WHY: single pass over comparison rows.
            self._ingest_lookup_row(row)  # WHY: delegate row-level work to keep CC low.
        print(f"! Built comparison lookup with" f" {len(self.comparison_serials)} serial numbers")  # WHY: user info.
        self._maybe_announce_validation_count()  # WHY: extract branchy notice into helper.

    def _ingest_lookup_row(self, row: dict[str, Any]) -> None:
        """Add a single comparison row to the serial and address lookups."""
        serial = row.get(self.serial_field, "").strip() if self.serial_field else ""  # WHY: guard None field name.
        zip_code = row.get(self.zip_field, "").strip() if self.zip_field else ""  # WHY: guard None field name.
        if not serial:  # WHY: keyless rows cannot be indexed.
            return  # WHY: skip malformed row.
        normalized_zip = self._address_utils.normalize_zip(zip_code)  # WHY: canonical zip form.
        self.comparison_serials[serial] = normalized_zip  # WHY: serial -> zip index.
        self.comparison_address_lookup[serial] = self._extract_address_from_row(row, zip_code)  # WHY: full address.

    def _maybe_announce_validation_count(self) -> None:
        """Print validation candidate count when validation is enabled."""
        if not self.address_validation_enabled:  # WHY: only announce when relevant.
            return  # WHY: nothing to say when disabled.
        validation_count = self._count_devices_for_validation()  # WHY: expected API-call volume.
        print(f"! Will validate {validation_count} address" " conflicts using Nominatim API")  # WHY: user info.

    def _extract_address_from_row(self, row: dict[str, Any], zip_code: str) -> dict[str, str]:
        """Extract address components from a comparison CSV row."""
        return {
            "Address": (row.get(self.address_field, "") if self.address_field else ""),  # WHY: guard optional.
            "City": (row.get(self.city_field, "") if self.city_field else ""),  # WHY: guard optional.
            "State": (row.get(self.state_field, "") if self.state_field else ""),  # WHY: guard optional.
            "Country": (row.get(self.country_field, "") if self.country_field else ""),  # WHY: guard optional.
            "Zip": zip_code,  # WHY: caller supplies pre-stripped zip.
        }

    def _count_devices_for_validation(self) -> int:
        """Count devices that will need external validation."""
        count = 0  # WHY: accumulator.
        for device in self.site_configs:  # WHY: linear scan over inventory.
            serial = device.get("serial", "").strip()  # WHY: strip padding whitespace.
            if serial in self.comparison_serials:  # WHY: matched serial => candidate.
                count += 1  # WHY: bump count.
        return count  # WHY: total candidates.

    # =================================================================
    # DUPLICATE DETECTION METHODS
    # =================================================================

    def _detect_duplicate_addresses(self) -> None:
        """Detect duplicate addresses between sites."""
        print("\n  Checking for duplicate addresses between sites...")  # WHY: user visibility.
        mist_site_addresses = self._build_mist_site_addresses()  # WHY: build Mist side.
        self.mist_duplicates = self._find_duplicates(mist_site_addresses)  # WHY: address_key -> sites.
        ref_site_addresses = self._build_ref_site_addresses()  # WHY: build reference side.
        self.ref_duplicates = self._find_duplicates(ref_site_addresses)  # WHY: reference duplicates.
        self._report_duplicates(mist_site_addresses, ref_site_addresses)  # WHY: user-facing summary.

    def _build_mist_site_addresses(
        self,
    ) -> dict[str, dict[str, Any]]:
        """Build address mapping for Mist sites."""
        site_addresses: dict[str, dict[str, Any]] = {}  # WHY: accumulator.
        for device in self.site_configs:  # WHY: scan devices for unique sites.
            site_name = device.get("site_name", "")  # WHY: primary key.
            if not site_name or site_name in site_addresses:  # WHY: skip missing or duplicate keys.
                continue  # WHY: keep first occurrence per site.
            mist_address = {
                "address": device.get("street", "").strip(),  # WHY: strip padding.
                "city": device.get("city", "").strip(),  # WHY: strip padding.
                "state": device.get("state", "").strip(),  # WHY: strip padding.
                "zip": device.get("zip_code", "").strip(),  # WHY: strip padding.
            }
            if not any(mist_address.values()):  # WHY: skip fully-empty addresses.
                continue  # WHY: nothing to index.
            address_key = self._create_address_key(mist_address)  # WHY: normalised join.
            site_addresses[site_name] = {
                "address_key": address_key,  # WHY: index for duplicate detection.
                "address": mist_address,  # WHY: retained for reporting.
            }
        return site_addresses  # WHY: caller diffs against ref.

    def _build_ref_site_addresses(
        self,
    ) -> dict[str, dict[str, Any]]:
        """Build address mapping for reference sites."""
        site_addresses: dict[str, dict[str, Any]] = {}  # WHY: accumulator.
        for device in self.site_configs:  # WHY: scan devices to find ref matches.
            entry = self._extract_ref_site_entry(device, site_addresses)  # WHY: helper for CC control.
            if entry is None:  # WHY: helper signals "skip this device".
                continue  # WHY: preserve original guard semantics.
            site_name, payload = entry  # WHY: unpack helper return.
            site_addresses[site_name] = payload  # WHY: index by first-seen site name.
        return site_addresses  # WHY: caller diffs against Mist.

    def _extract_ref_site_entry(
        self,
        device: dict[str, Any],
        already_indexed: dict[str, dict[str, Any]],
    ) -> tuple[str, dict[str, Any]] | None:
        """Return (site_name, payload) for a ref-side device or None to skip."""
        device_serial = device.get("serial", "").strip()  # WHY: primary lookup key.
        site_name = device.get("site_name", "")  # WHY: site is the aggregation key.
        if not site_name or site_name in already_indexed:  # WHY: dedupe on site name.
            return None  # WHY: caller skips.
        if device_serial not in self.comparison_address_lookup:  # WHY: only ref-matched devices.
            return None  # WHY: caller skips.
        ref_data = self.comparison_address_lookup[device_serial]  # WHY: pull ref row.
        ref_address = {
            "address": ref_data.get("Address", "").strip(),  # WHY: strip padding.
            "city": ref_data.get("City", "").strip(),  # WHY: strip padding.
            "state": ref_data.get("State", "").strip(),  # WHY: strip padding.
            "zip": ref_data.get("Zip", "").strip(),  # WHY: strip padding.
        }
        if not any(ref_address.values()):  # WHY: skip fully-empty addresses.
            return None  # WHY: nothing to index.
        address_key = self._create_address_key(ref_address)  # WHY: normalised join.
        return site_name, {"address_key": address_key, "address": ref_address}  # WHY: caller assigns.

    def _create_address_key(self, address: dict[str, str]) -> str:
        """Create a normalized address key for deduplication."""
        return (
            f"{address['address'].lower()}"  # WHY: canonical lowercase street.
            f"|{address['city'].lower()}"  # WHY: canonical lowercase city.
            f"|{address['state'].lower()}"  # WHY: canonical lowercase state.
            f"|{address['zip']}"  # WHY: zip is already normalised upstream.
        )

    def _find_duplicates(self, site_addresses: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
        """Find addresses shared by multiple sites."""
        address_to_sites: dict[str, list[str]] = {}  # WHY: reverse index.
        for site_name, addr_data in site_addresses.items():  # WHY: invert the mapping.
            address_key = addr_data["address_key"]  # WHY: canonical key.
            if address_key not in address_to_sites:  # WHY: init bucket lazily.
                address_to_sites[address_key] = []  # WHY: fresh bucket.
            address_to_sites[address_key].append(site_name)  # WHY: append site.
        return {key: sites for key, sites in address_to_sites.items() if len(sites) > 1}  # WHY: >1 => duplicate.

    def _report_duplicates(
        self,
        mist_addresses: dict[str, dict[str, Any]],
        ref_addresses: dict[str, dict[str, Any]],
    ) -> None:
        """Report duplicate address findings."""
        if self.mist_duplicates:  # WHY: only print if any found.
            self._print_duplicate_group("Mist", self.mist_duplicates, mist_addresses)  # WHY: Mist group.
        if self.ref_duplicates:  # WHY: only print if any found.
            self._print_duplicate_group("Reference", self.ref_duplicates, ref_addresses)  # WHY: ref group.
        if not self.mist_duplicates and not self.ref_duplicates:  # WHY: reassure user when clean.
            print("    No duplicate addresses found between sites")  # WHY: user visibility.
        else:
            self._print_duplicate_summary()  # WHY: counts summary.

    def _print_duplicate_group(
        self,
        source: str,
        duplicates: dict[str, list[str]],
        addresses: dict[str, dict[str, Any]],
    ) -> None:
        """Print a group of duplicate addresses."""
        print(f"    {source} sites sharing the same address:")  # WHY: section header.
        for _addr_key, sites in duplicates.items():  # WHY: iterate duplicate buckets.
            sample_site = sites[0]  # WHY: pick a representative site.
            addr = addresses[sample_site]["address"]  # WHY: representative address.
            print(f"        Address: {addr['address']}," f" {addr['city']}, {addr['state']}" f" {addr['zip']}")  # WHY.
            print(f"        Sites ({len(sites)}):" f" {', '.join(sites)}")  # WHY: list all sites.

    def _print_duplicate_summary(self) -> None:
        """Print summary of duplicate findings."""
        mist_count = len(self.mist_duplicates)  # WHY: number of duplicate groups on Mist side.
        mist_sites = sum(len(sites) for sites in self.mist_duplicates.values())  # WHY: total impacted sites.
        ref_count = len(self.ref_duplicates)  # WHY: number of duplicate groups on ref side.
        ref_sites = sum(len(sites) for sites in self.ref_duplicates.values())  # WHY: total impacted sites.
        print(f"     Found {mist_count} Mist address duplications" f" affecting {mist_sites} sites")  # WHY: user info.
        print(f"     Found {ref_count} reference address" f" duplications affecting {ref_sites} sites")  # WHY.
        if self.debug:  # WHY: only log when debug.
            logging.info("DUPLICATE_CHECK: Found %s Mist and %s reference duplicates", mist_count, ref_count)  # WHY.

    # =================================================================
    # DEVICE PROCESSING METHODS (Step 1)
    # =================================================================

    def _process_all_devices(self) -> None:
        """Process all devices to identify address conflicts."""
        print(f"\n  Processing {len(self.site_configs)}" " total devices...")  # WHY: user info.
        print(" Step 1: Parsing and normalizing all addresses...")  # WHY: user info.
        self.counters.total_devices = len(self.site_configs)  # WHY: seed counter.
        first_missing_name_warned = False  # WHY: dedupe missing-name warning noise.
        for device in tqdm(
            self.site_configs,  # WHY: iterate all devices.
            desc="Step 1: Parsing Addresses",  # WHY: progress bar label.
            unit="device",  # WHY: unit label.
        ):
            first_missing_name_warned = self._process_device_in_loop(device, first_missing_name_warned)  # WHY: step.
        conflicts_found = len(self.all_conflicts)  # WHY: mismatches recorded so far.
        analyzed = self.counters.devices_enriched  # WHY: analysed subset.
        print(
            f"! Step 1 Complete: Found {conflicts_found}"  # WHY: user info line.
            f" address conflicts from {analyzed}"
            " analyzed devices"
        )

    def _process_device_in_loop(
        self,
        device: dict[str, Any],
        first_missing_name_warned: bool,
    ) -> bool:
        """Process a single device within the main loop.

        Returns:
            Updated first_missing_name_warned flag.
        """
        device_serial = device.get("serial", "").strip()  # WHY: primary key.
        device_identifier = self._get_device_identifier(
            device,  # WHY: device row for label composition.
            warn_on_missing=not first_missing_name_warned,  # WHY: warn once.
        )
        if not first_missing_name_warned and device_identifier != device.get("name", "").strip():  # WHY: flip flag.
            first_missing_name_warned = True  # WHY: prevent repeated warnings.
        if device_serial not in self.comparison_serials:  # WHY: nothing to compare against.
            self.counters.devices_skipped += 1  # WHY: skip metric.
            if self.debug:  # WHY: only log when debugging.
                logging.debug("DEVICE_SKIP [%s]: Not found in comparison CSV", device_serial)  # WHY: trace.
            return first_missing_name_warned  # WHY: preserve caller state.
        self.counters.devices_enriched += 1  # WHY: matched device metric.
        self._process_single_device(device, device_serial, device_identifier)  # WHY: perform compare.
        return first_missing_name_warned  # WHY: preserve caller state.

    def _process_single_device(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
    ) -> None:
        """Process a single device for address comparison."""
        try:
            self._compare_and_record(device, device_serial, device_identifier)  # WHY: happy path.
        except Exception as device_error:  # pylint: disable=broad-exception-caught  # WHY: contain per-device errors.
            self._handle_device_error(device, device_serial, device_identifier, device_error)  # WHY: log+record.

    def _compare_and_record(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
    ) -> None:
        """Parse both sides, compare, and record the result for one device."""
        mist_address = self._parse_mist_address(device, device_serial, device_identifier)  # WHY: parse Mist side.
        comparison_address = self._get_comparison_address(device_serial)  # WHY: fetch ref side.
        if not comparison_address:  # WHY: no ref data => skip.
            self.counters.devices_skipped += 1  # WHY: metric.
            return  # WHY: nothing to compare.
        comparison_result = self._compare_addresses(mist_address, comparison_address, device_serial)  # WHY: verdict.
        inputs = RecordComparisonInputs(
            device=device,  # WHY: passthrough for reporting.
            device_serial=device_serial,  # WHY: passthrough for reporting.
            device_identifier=device_identifier,  # WHY: passthrough for reporting.
            mist_address=mist_address,  # WHY: parsed source address.
            comparison_address=comparison_address,  # WHY: parsed ref address.
            comparison_result=comparison_result,  # WHY: verdict.
        )
        self._record_comparison_result(inputs)  # WHY: match vs conflict bookkeeping.

    def _handle_device_error(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
        device_error: Exception,
    ) -> None:
        """Log per-device failure and register a parse-failure row."""
        logging.warning("! Error processing device %s: %s", device_serial, device_error)  # WHY: log record.
        self.counters.comparison_failures += 1  # WHY: reliability metric.
        self._record_device_parse_failure(
            device,  # WHY: retained on failure record.
            device_serial,  # WHY: primary key.
            device_identifier,  # WHY: label.
            str(device_error),  # WHY: reason.
        )

    def _compare_addresses(
        self,
        mist_address: dict[str, str],
        comparison_address: dict[str, str],
        device_serial: str,
    ) -> dict[str, Any]:
        """Run the fuzzy comparison and log the verdict when debug is on."""
        comparison_result = self._address_utils.compare_with_threshold(
            mist_address,  # WHY: source address.
            comparison_address,  # WHY: ref address.
            self.address_threshold,  # WHY: fuzzy threshold.
            debug=self.debug,  # WHY: propagate debug for detailed logging.
        )
        if self.debug:  # WHY: only trace when debug.
            logging.debug("DEVICE_COMPARISON [%s]: Result: %s", device_serial, comparison_result)  # WHY: trace.
        return comparison_result  # type: ignore[no-any-return]  # WHY: dict typed via injected class.

    def _record_comparison_result(self, inputs: RecordComparisonInputs) -> None:
        """Record comparison result as match or conflict."""
        if inputs.comparison_result["is_match"]:  # WHY: within threshold => match.
            self.counters.perfect_matches += 1  # WHY: match metric.
            return  # WHY: nothing else to record for matches.
        self.counters.mismatches_found += 1  # WHY: mismatch metric.
        self.all_conflicts.append(
            {
                "device": inputs.device,  # WHY: retained for reporting.
                "device_serial": inputs.device_serial,  # WHY: primary key.
                "device_identifier": inputs.device_identifier,  # WHY: label.
                "mist_address": inputs.mist_address,  # WHY: source snapshot.
                "comparison_address": inputs.comparison_address,  # WHY: ref snapshot.
                "comparison_result": inputs.comparison_result,  # WHY: verdict.
            }
        )

    def _parse_mist_address(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
    ) -> dict[str, str]:
        """Parse address from Mist device data."""
        mist_address_raw = device.get("site_address", "").strip()  # WHY: prefer single-line address.
        if not mist_address_raw:  # WHY: fall back to per-component fields.
            return self._get_component_address(device)  # WHY: component fallback.
        parsed_mist = self._address_utils.enhanced_parse(mist_address_raw, debug=self.debug)  # WHY: parse.
        if not parsed_mist["is_parseable"]:  # WHY: parse failed.
            self._record_mist_parse_failure(
                device,  # WHY: retained on failure record.
                device_serial,  # WHY: primary key.
                device_identifier,  # WHY: label.
                mist_address_raw,  # WHY: original input.
                parsed_mist,  # WHY: reason payload.
            )
            return self._get_component_address(device)  # WHY: component fallback keeps compare running.
        return self._parsed_result_to_address(parsed_mist)  # WHY: normalised result.

    def _parsed_result_to_address(self, parsed_mist: dict[str, Any]) -> dict[str, str]:
        """Convert enhanced_parse output to the canonical address dict shape."""
        return {
            "address": parsed_mist.get("address") or "",  # WHY: normalise None to empty.
            "city": parsed_mist.get("city") or "",  # WHY: normalise None to empty.
            "state": parsed_mist.get("state") or "",  # WHY: normalise None to empty.
            "zip": parsed_mist.get("zip") or "",  # WHY: normalise None to empty.
        }

    def _get_component_address(self, device: dict[str, Any]) -> dict[str, str]:
        """Get address from individual component fields."""
        return {
            "address": device.get("street", "").strip(),  # WHY: strip padding.
            "city": device.get("city", "").strip(),  # WHY: strip padding.
            "state": device.get("state", "").strip(),  # WHY: strip padding.
            "zip": device.get("zip_code", "").strip(),  # WHY: strip padding.
        }

    def _get_comparison_address(self, device_serial: str) -> dict[str, str] | None:
        """Get comparison address for a device serial."""
        comparison_data = self.comparison_address_lookup.get(device_serial, {})  # WHY: lookup.
        if not comparison_data or not any(comparison_data.values()):  # WHY: empty payload.
            self._debug_log_skip(device_serial, "No comparison address data")  # WHY: trace.
            return None  # WHY: signal caller to skip.
        comparison_address = {
            "address": comparison_data.get("Address", "").strip(),  # WHY: strip padding.
            "city": comparison_data.get("City", "").strip(),  # WHY: strip padding.
            "state": comparison_data.get("State", "").strip(),  # WHY: strip padding.
            "zip": comparison_data.get("Zip", "").strip(),  # WHY: strip padding.
        }
        if not any(comparison_address.values()):  # WHY: all fields blank after strip.
            self._debug_log_skip(device_serial, "Empty comparison address")  # WHY: trace.
            return None  # WHY: signal caller to skip.
        return comparison_address  # WHY: usable address for compare.

    def _debug_log_skip(self, device_serial: str, reason: str) -> None:
        """Emit a DEVICE_SKIP trace when debug is enabled."""
        if not self.debug:  # WHY: keep prod logs quiet.
            return  # WHY: bail early.
        logging.debug("DEVICE_SKIP [%s]: %s", device_serial, reason)  # WHY: trace skip reason.

    def _record_mist_parse_failure(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
        raw_address: str,
        parsed_result: dict[str, Any],
    ) -> None:
        """Record a Mist address parse failure."""
        failure_record = {
            "site_id": device.get("site_id", ""),  # WHY: cross-reference to Mist site.
            "site_name": device.get("site_name", ""),  # WHY: readable name.
            "device_id": device.get("id", ""),  # WHY: device pk.
            "device_serial": device_serial,  # WHY: primary key.
            "device_name": device_identifier,  # WHY: label.
            "original_address": raw_address,  # WHY: preserve input verbatim.
            "parsed_tokens": str(raw_address.split(",")),  # WHY: hint at split state.
            "failure_reason": parsed_result["parse_reason"],  # WHY: reason code.
            "timestamp": datetime.now(UTC).isoformat(),  # WHY: audit timestamp.
        }
        self.parse_failures.append(failure_record)  # WHY: rows for CSV output.
        self.counters.increment_parse_failure(parsed_result["parse_reason"])  # WHY: histogram bump.

    def _record_device_parse_failure(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
        error_msg: str,
    ) -> None:
        """Record a device processing error as parse failure."""
        failure_record = {
            "site_id": device.get("site_id", ""),  # WHY: cross-reference to Mist site.
            "site_name": device.get("site_name", ""),  # WHY: readable name.
            "device_id": device.get("id", ""),  # WHY: device pk.
            "device_serial": device_serial,  # WHY: primary key.
            "device_name": device_identifier,  # WHY: label.
            "original_address": str(device.get("site_address", "")),  # WHY: verbatim input.
            "parsed_tokens": "N/A",  # WHY: no split available on exception path.
            "failure_reason": (f"device_processing_error: {error_msg}"),  # WHY: reason code + detail.
            "timestamp": datetime.now(UTC).isoformat(),  # WHY: audit timestamp.
        }
        self.parse_failures.append(failure_record)  # WHY: rows for CSV output.
        self.counters.increment_parse_failure("device_processing_error")  # WHY: histogram bump.

    # =================================================================
    # CONFLICT FILTERING METHODS (Steps 2-3)
    # =================================================================

    def _filter_conflicts(self) -> None:
        """Filter conflicts through dedup and skip list."""
        unique_conflicts = self._remove_duplicate_conflicts()  # WHY: strip duplicate address pairs.
        self.filtered_conflicts = self._apply_skip_filters(unique_conflicts)  # WHY: apply AddressSkip.csv.

    def _remove_duplicate_conflicts(
        self,
    ) -> list[dict[str, Any]]:
        """Remove duplicate address pairs from conflicts."""
        print(" Step 2: Removing duplicate addresses...")  # WHY: user info.
        unique_conflicts: list[dict[str, Any]] = []  # WHY: dedup accumulator.
        seen_addresses: set[str] = set()  # WHY: address-pair key registry.
        for conflict in self.all_conflicts:  # WHY: scan all conflicts.
            address_key = self._create_conflict_address_key(conflict)  # WHY: pair key.
            if address_key not in seen_addresses:  # WHY: first sighting.
                seen_addresses.add(address_key)  # WHY: mark as seen.
                unique_conflicts.append(conflict)  # WHY: retain unique.
            elif self.debug:  # WHY: log dropped duplicates in debug only.
                logging.debug("DUPLICATE_REMOVED [%s]", conflict["device_serial"])  # WHY: trace.
        duplicates_removed = len(self.all_conflicts) - len(unique_conflicts)  # WHY: metric.
        print(
            f"! Step 2 Complete: Removed {duplicates_removed}"  # WHY: user info line.
            f" duplicate pairs,"
            f" {len(unique_conflicts)} remain"
        )
        return unique_conflicts  # WHY: fed to skip filter.

    def _create_conflict_address_key(self, conflict: dict[str, Any]) -> str:
        """Create a unique key for a conflict's address pair."""
        mist_addr = conflict["mist_address"]  # WHY: source side.
        comp_addr = conflict["comparison_address"]  # WHY: ref side.
        mist_key = (
            f"{mist_addr['address'].lower().strip()}"  # WHY: normalise for dedupe.
            f"|{mist_addr['city'].lower().strip()}"
            f"|{mist_addr['state'].lower().strip()}"
            f"|{mist_addr['zip'].strip()}"
        )
        comp_key = (
            f"{comp_addr['address'].lower().strip()}"  # WHY: normalise for dedupe.
            f"|{comp_addr['city'].lower().strip()}"
            f"|{comp_addr['state'].lower().strip()}"
            f"|{comp_addr['zip'].strip()}"
        )
        return f"{mist_key}||{comp_key}"  # WHY: combined pair key.

    def _apply_skip_filters(self, unique_conflicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply address skip filters to conflicts."""
        print(" Step 3: Applying address skip filters...")  # WHY: user info.
        filtered: list[dict[str, Any]] = []  # WHY: post-skip accumulator.
        for conflict in unique_conflicts:  # WHY: scan unique conflicts.
            comparison_address = conflict["comparison_address"]  # WHY: skip list matches ref side.
            device_serial = conflict["device_serial"]  # WHY: primary key for logging.
            should_skip, skip_reason = self._address_utils.check_should_skip(
                comparison_address,  # WHY: address to check.
                self.skip_addresses,  # WHY: skip-list rows.
                debug=self.debug,  # WHY: propagate debug for tracing.
            )
            if should_skip:  # WHY: skip-list hit auto-corrects.
                self._record_skipped_address(device_serial, skip_reason)  # WHY: metric + trace.
            else:
                filtered.append(conflict)  # WHY: keep for downstream.
        skip_filtered = len(unique_conflicts) - len(filtered)  # WHY: metric.
        print(
            f"! Step 3 Complete: Removed {skip_filtered}"  # WHY: user info line.
            f" via skip filters,"
            f" {len(filtered)} require analysis"
        )
        return filtered  # WHY: post-skip conflicts.

    def _record_skipped_address(self, device_serial: str, skip_reason: str) -> None:
        """Record an auto-skipped address."""
        self.counters.perfect_matches += 1  # WHY: treat skip as match for headline metric.
        self.counters.auto_corrections += 1  # WHY: separate auto-correct metric.
        if self.debug:  # WHY: debug-only trace.
            logging.debug("ADDRESS_SKIP [%s]: %s", device_serial, skip_reason)  # WHY: trace skip reason.
        print(f"    Auto-corrected: {device_serial}" f" (Skip reason: {skip_reason})")  # WHY: user visibility.

    # =================================================================
    # VALIDATION AND MISMATCH PROCESSING (Step 4)
    # =================================================================

    def _process_remaining_conflicts(self) -> None:
        """Process remaining conflicts with optional validation."""
        if not self.filtered_conflicts:  # WHY: no work to do.
            return  # WHY: early exit.
        if self.address_validation_enabled:  # WHY: choose branch based on flag.
            self._process_with_validation()  # WHY: call Nominatim.
        else:
            self._process_without_validation()  # WHY: skip external API.

    def _process_without_validation(self) -> None:
        """Process conflicts without external validation."""
        print(f"\n  Step 4: Processing" f" {len(self.filtered_conflicts)}" " conflicts without validation...")  # WHY.
        for conflict in self.filtered_conflicts:  # WHY: iterate all remaining.
            self._generate_mismatch_records(conflict, validation_result=None)  # WHY: no validation payload.

    def _process_with_validation(self) -> None:
        """Process conflicts with external Nominatim validation."""
        total_validations = len(self.filtered_conflicts)  # WHY: total-count denominator.
        print(f"\n  Step 4: External validation enabled -" f" {total_validations} conflicts need validation")  # WHY.
        print(" This may take several minutes due to" " API rate limiting (1 request/second)...")  # WHY: user notice.
        org_name = self._get_org_name_for_validation()  # WHY: tiebreaker hint.
        for idx, conflict in enumerate(
            tqdm(
                self.filtered_conflicts,  # WHY: iterate remaining.
                desc="Step 4: Validating",  # WHY: progress bar label.
                unit="device",  # WHY: unit label.
            )
        ):
            validation_result = self._validate_single_conflict(
                conflict,  # WHY: conflict payload.
                idx + 1,  # WHY: 1-indexed current.
                total_validations,  # WHY: total denominator.
                org_name,  # WHY: tiebreaker.
            )
            self._generate_mismatch_records(conflict, validation_result)  # WHY: emit records.

    def _get_org_name_for_validation(self) -> str | None:
        """Get organization name for tiebreaker logic."""
        try:
            org_response = self._fetch_org_response()  # WHY: single-purpose helper.
            return self._parse_org_response(org_response)  # WHY: single-purpose helper.
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: tolerate mistapi errors.
            if self.debug:  # WHY: debug-only trace.
                logging.warning("Could not retrieve organization name: %s", error)  # WHY: log record.
            return None  # WHY: caller treats None as "no tiebreaker".

    def _fetch_org_response(self) -> Any:
        """Call mistapi to fetch the org record for the current session."""
        if self.debug:  # WHY: debug-only trace.
            logging.debug("Fetching organization information" " for tiebreaker logic...")  # WHY: trace entry.
        import mistapi  # pylint: disable=import-outside-toplevel  # WHY: import lazily to avoid cycle.

        org_id = self._get_org_id()  # WHY: cached/prompted org id.
        return mistapi.api.v1.orgs.orgs.getOrg(self._api, org_id)  # WHY: raw response.

    def _parse_org_response(self, org_response: Any) -> str | None:
        """Extract the org name from the mistapi response or return None."""
        if org_response.status_code == 200:  # WHY: only 200 responses have payload.
            org_name: str = org_response.data.get("name", "").strip()  # WHY: strip padding.
            if self.debug:  # WHY: debug-only trace.
                logging.debug("Organization name retrieved: '%s'", org_name)  # WHY: trace value.
            return org_name  # WHY: usable tiebreaker string.
        if self.debug:  # WHY: debug-only trace.
            logging.warning("Failed to retrieve org info: HTTP %s", org_response.status_code)  # WHY: trace.
        return None  # WHY: caller treats None as "no tiebreaker".

    def _validate_single_conflict(
        self,
        conflict: dict[str, Any],
        current: int,
        total: int,
        org_name: str | None,
    ) -> dict[str, Any] | None:
        """Validate a single conflict using Nominatim API."""
        device = conflict["device"]  # WHY: retained for site_name lookup.
        device_serial = conflict["device_serial"]  # WHY: primary key.
        mist_address = conflict["mist_address"]  # WHY: source side.
        comparison_address = conflict["comparison_address"]  # WHY: ref side.
        self._print_validation_header(
            device_serial,  # WHY: primary key label.
            mist_address,  # WHY: displayed to user.
            comparison_address,  # WHY: displayed to user.
            current,  # WHY: progress indicator.
            total,  # WHY: progress indicator.
        )
        return self._run_validator(device, device_serial, mist_address, comparison_address, org_name)

    def _run_validator(
        self,
        device: dict[str, Any],
        device_serial: str,
        mist_address: dict[str, str],
        comparison_address: dict[str, str],
        org_name: str | None,
    ) -> dict[str, Any] | None:
        """Instantiate and invoke the Nominatim validator with error handling."""
        try:
            validator = self._build_validator(device, org_name)  # WHY: encapsulate config build.
            validation_result = validator.validate(mist_address, comparison_address)  # WHY: run API.
            self._print_validation_results(device_serial, validation_result)  # WHY: user visibility.
            return validation_result  # type: ignore[no-any-return]  # WHY: dict typed via injected class.
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: tolerate Nominatim failure.
            self._log_validator_failure(device_serial, error)  # WHY: consolidated failure trace.
            return None  # WHY: caller treats None as "no validation".

    def _log_validator_failure(self, device_serial: str, error: Exception) -> None:
        """Emit user-visible + logged traces for a validation failure."""
        print(f"    Validation failed: {error!s}")  # WHY: user visibility.
        logging.warning("ADDRESS_VALIDATION [%s]: Validation failed: %s", device_serial, error)  # WHY: log record.
        if self.debug:  # WHY: only capture traceback in debug.
            logging.debug("ADDRESS_VALIDATION [%s]: %s", device_serial, traceback.format_exc())  # WHY: full trace.

    def _build_validator(self, device: dict[str, Any], org_name: str | None) -> Any:
        """Construct the Nominatim validator with per-run configuration."""
        timeout = int(os.getenv("ADDRESS_VALIDATION_TIMEOUT", "10"))  # WHY: env-driven timeout.
        validator_config = self._address_validation_config_cls(
            timeout=timeout,  # WHY: HTTP timeout for Nominatim.
            debug=self.debug,  # WHY: propagate debug flag.
            skip_ssl_verify=self.skip_ssl_verify,  # WHY: honour caller preference.
            org_name=org_name,  # WHY: tiebreaker hint.
            site_name=device.get("site_name", ""),  # WHY: extra hint for tiebreaker.
            mist_duplicates=self.mist_duplicates,  # WHY: shared context for validator.
            ref_duplicates=self.ref_duplicates,  # WHY: shared context for validator.
        )
        return self._nominatim_validator_cls(validator_config)  # WHY: instantiate validator.

    def _print_validation_header(
        self,
        device_serial: str,
        mist_address: dict[str, str],
        comparison_address: dict[str, str],
        current: int,
        total: int,
    ) -> None:
        """Print validation header for a device."""
        mist_str = self._format_address_string(mist_address)  # WHY: user-facing string.
        comp_str = self._format_address_string(comparison_address)  # WHY: user-facing string.
        print(f"! [{current}/{total}]" f" Validating {device_serial}...")  # WHY: user visibility.
        print(f"    Mist:       {mist_str}")  # WHY: user visibility.
        print(f"    Reference:  {comp_str}")  # WHY: user visibility.
        logging.info("ADDRESS_VALIDATION [%s]: Starting validation", device_serial)  # WHY: log record.
        logging.info("ADDRESS_VALIDATION [%s]: Mist: %s", device_serial, mist_str)  # WHY: log record.
        logging.info("ADDRESS_VALIDATION [%s]: Comparison: %s", device_serial, comp_str)  # WHY: log record.

    def _format_address_string(self, address: dict[str, str]) -> str:
        """Format address dictionary as display string."""
        return (
            (f"{address['address']}, {address['city']}," f" {address['state']} {address['zip']}")  # WHY: join fields.
            .replace(", , ", ", ")  # WHY: collapse empty commas.
            .strip(", ")  # WHY: trim leading/trailing separators.
        )

    def _print_validation_results(
        self,
        device_serial: str,
        result: dict[str, Any],
    ) -> None:
        """Print validation results for a device."""
        formatted = self._format_validation_summary(result)  # WHY: bundle status+confidence strings.
        self._emit_validation_lines(device_serial, formatted, result)  # WHY: separate stdout/log emission.

    def _format_validation_summary(self, result: dict[str, Any]) -> dict[str, str]:
        """Build user-facing strings for a validation result."""
        mist_valid = result["mist_validation"]["valid"]  # WHY: bool flag from validator.
        comp_valid = result["comparison_validation"]["valid"]  # WHY: bool flag from validator.
        mist_status = " Valid" if mist_valid else " Invalid"  # WHY: user-facing.
        comp_status = " Valid" if comp_valid else " Invalid"  # WHY: user-facing.
        # WHY: format confidence only when the corresponding side validated cleanly.
        mist_conf = f"{result['mist_validation']['confidence']:.3f}" if mist_valid else "N/A"
        comp_conf = f"{result['comparison_validation']['confidence']:.3f}" if comp_valid else "N/A"
        recommendation_icon = {
            "mist": " Mist",  # WHY: recommend Mist address.
            "comparison": " Reference",  # WHY: recommend comparison address.
            "uncertain": " Uncertain",  # WHY: no recommendation.
        }
        display = recommendation_icon.get(result["recommendation"], result["recommendation"])  # WHY: fallback to raw.
        return {
            "mist_status": mist_status,  # WHY: display line.
            "comp_status": comp_status,  # WHY: display line.
            "mist_conf": mist_conf,  # WHY: display line.
            "comp_conf": comp_conf,  # WHY: display line.
            "mist_valid": str(mist_valid),  # WHY: for logging.
            "comp_valid": str(comp_valid),  # WHY: for logging.
            "display": display,  # WHY: recommendation line.
        }

    def _emit_validation_lines(
        self,
        device_serial: str,
        formatted: dict[str, str],
        result: dict[str, Any],
    ) -> None:
        """Print + log a validation summary using the formatted strings."""
        self._print_validation_lines(formatted, result)  # WHY: user-visible summary block.
        self._log_validation_lines(device_serial, formatted, result)  # WHY: matching log record block.

    def _print_validation_lines(self, formatted: dict[str, str], result: dict[str, Any]) -> None:
        """Print the human-readable validation summary."""
        print(
            f"    Results:    Mist: {formatted['mist_status']}"  # WHY: line 1 of results.
            f" (conf: {formatted['mist_conf']})"
            f" | Reference: {formatted['comp_status']}"
            f" (conf: {formatted['comp_conf']})"
        )
        print(f"    Recommendation: {formatted['display']}")  # WHY: line 2 of results.
        reason = result.get("recommendation_reason", "No reason provided")  # WHY: reason text.
        if result["recommendation"] != "uncertain" or "inconclusive" not in reason.lower():  # WHY: filter noise.
            print(f"    Reason: {reason}")  # WHY: user visibility.

    def _log_validation_lines(
        self,
        device_serial: str,
        formatted: dict[str, str],
        result: dict[str, Any],
    ) -> None:
        """Emit structured log records for the validation summary."""
        logging.info(
            "ADDRESS_VALIDATION [%s]: Mist valid=%s, conf=%s",  # WHY: log Mist verdict.
            device_serial,
            formatted["mist_valid"],
            formatted["mist_conf"],
        )
        logging.info(
            "ADDRESS_VALIDATION [%s]: Comp valid=%s, conf=%s",  # WHY: log comparison verdict.
            device_serial,
            formatted["comp_valid"],
            formatted["comp_conf"],
        )
        logging.info("ADDRESS_VALIDATION [%s]: Recommendation: %s", device_serial, result["recommendation"])  # WHY.

    # =================================================================
    # MISMATCH RECORD GENERATION METHODS
    # =================================================================

    def _generate_mismatch_records(
        self,
        conflict: dict[str, Any],
        validation_result: dict[str, Any] | None,
    ) -> None:
        """Generate mismatch and diff report items."""
        try:
            config = self._build_item_config(conflict, validation_result)  # WHY: shared config object.
            self.mismatched_items.append(self._build_mismatch_item(config))  # WHY: mismatch report row.
            self.diff_report_items.append(self._build_diff_item(config))  # WHY: diff report row.
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: tolerate row-build errors.
            logging.warning(
                "! Error processing mismatch for device %s: %s",  # WHY: log record with device context.
                conflict.get("device_serial", "unknown"),
                error,
            )
            self.counters.comparison_failures += 1  # WHY: reliability metric.

    def _build_item_config(
        self,
        conflict: dict[str, Any],
        validation_result: dict[str, Any] | None,
    ) -> ComparisonItemConfig:
        """Assemble the ComparisonItemConfig used by mismatch + diff builders."""
        device = conflict["device"]  # WHY: source device row.
        device_serial = conflict["device_serial"]  # WHY: primary key.
        comparison_result = conflict["comparison_result"]  # WHY: verdict.
        mist_address = conflict["mist_address"]  # WHY: source snapshot.
        comparison_address = conflict["comparison_address"]  # WHY: ref snapshot.
        week_key = self._get_week_key(device)  # WHY: ISO year+week bucket.
        mismatch_type = self._determine_mismatch_type(comparison_result)  # WHY: primary label.
        return ComparisonItemConfig(
            device=device,  # WHY: retained for later reads.
            device_serial=device_serial,  # WHY: primary key.
            mist_address=mist_address,  # WHY: source snapshot.
            comparison_address=comparison_address,  # WHY: ref snapshot.
            comparison_result=comparison_result,  # WHY: verdict.
            week_key=week_key,  # WHY: rollup key.
            mismatch_type=mismatch_type,  # WHY: report label.
            validation_result=validation_result,  # WHY: optional validation payload.
        )

    def _get_week_key(self, device: dict[str, Any]) -> str:
        """Get the week key for a device based on creation time."""
        created_time = int(device.get("created_time", 0))  # WHY: unix epoch.
        created_date = datetime.fromtimestamp(created_time, tz=UTC)  # WHY: aware datetime.
        year, week, _ = created_date.isocalendar()  # WHY: ISO year+week+day.
        return f"{year}_Week_{week:02d}"  # WHY: zero-padded label.

    def _determine_mismatch_type(self, comparison_result: dict[str, Any]) -> str:
        """Determine the primary mismatch type."""
        failed_fields = comparison_result["failed_fields"]  # WHY: list of failing keys.
        if "zip" in failed_fields and len(failed_fields) == 1:  # WHY: solo zip failure is special.
            return "Zip Code Mismatch"  # WHY: specific label.
        for field_name, label in _MISMATCH_TYPE_TABLE:  # WHY: table-driven dispatch avoids elif ladder.
            if field_name in failed_fields:  # WHY: first matching entry wins.
                return label  # WHY: return primary label.
        return "Multi-field Address Mismatch"  # WHY: default when no priority field matches.

    def _build_mismatch_item(
        self,
        config: ComparisonItemConfig,
    ) -> dict[str, Any]:
        """Build a mismatch item dictionary."""
        common = self._common_report_fields(config)  # WHY: reuse header block.
        return {
            **common,  # WHY: unpack shared header.
            "Address Line 1": config.mist_address["address"],  # WHY: mismatch report uses Mist-only address.
            "Address Line 2": "",  # WHY: legacy column preserved.
            "City": config.mist_address["city"],  # WHY: Mist-only city.
            "State": config.mist_address["state"],  # WHY: Mist-only state.
            "Current Zip Code": config.mist_address["zip"],  # WHY: source zip.
            # WHY: normalise Mist zip for comparison-friendly output.
            "Current Zip Normalized": self._address_utils.normalize_zip(config.mist_address["zip"]),
            "Comparison Zip Code": config.comparison_address["zip"],  # WHY: ref zip.
            **self._trailing_report_fields(config),  # WHY: reuse shared trailing block.
        }

    def _build_diff_item(
        self,
        config: ComparisonItemConfig,
    ) -> dict[str, Any]:
        """Build a diff report item dictionary."""
        common = self._common_report_fields(config)  # WHY: reuse header block.
        return {
            **common,  # WHY: unpack shared header.
            **self._diff_address_fields(config),  # WHY: side-by-side address block.
            **self._trailing_report_fields(config),  # WHY: reuse shared trailing block.
        }

    def _common_report_fields(self, config: ComparisonItemConfig) -> dict[str, Any]:
        """Fields shared between mismatch + diff reports."""
        return {
            "Week": config.week_key,  # WHY: rollup key.
            "Full Site": config.device.get("site_name", ""),  # WHY: site label.
            "System Serial Number": config.device_serial,  # WHY: primary key.
            "System Model Number": config.device.get("model", ""),  # WHY: device model.
            "End Customer Name": self.end_customer_name,  # WHY: tenant name.
        }

    def _diff_address_fields(self, config: ComparisonItemConfig) -> dict[str, Any]:
        """Side-by-side address block used by diff report."""
        return {
            "Mist_Address_Line_1": config.mist_address["address"],  # WHY: source street.
            "Mist_City": config.mist_address["city"],  # WHY: source city.
            "Mist_State": config.mist_address["state"],  # WHY: source state.
            "Mist_Zip_Code": config.mist_address["zip"],  # WHY: source zip.
            "Mist_Zip_Normalized": (self._address_utils.normalize_zip(config.mist_address["zip"])),  # WHY: normalise.
            "Comparison_Address": (config.comparison_address["address"]),  # WHY: ref street.
            "Comparison_City": config.comparison_address["city"],  # WHY: ref city.
            "Comparison_State": config.comparison_address["state"],  # WHY: ref state.
            "Comparison_Zip_Code": config.comparison_address["zip"],  # WHY: ref zip.
            "Comparison_Zip_Normalized": (
                self._address_utils.normalize_zip(config.comparison_address["zip"])  # WHY: normalise.
            ),
        }

    def _trailing_report_fields(self, config: ComparisonItemConfig) -> dict[str, Any]:
        """Fields shared by both reports after their address section."""
        return {
            "End Customer Account ID": (self.end_customer_account_id),  # WHY: tenant account id.
            "Mismatch Type": config.mismatch_type,  # WHY: label.
            **self._similarity_fields(config),  # WHY: bundle similarity block.
            "Failed Fields": ", ".join(config.comparison_result["failed_fields"]),  # WHY: join list.
            **self._parse_status_fields(config),  # WHY: bundle parse-status block.
            **self._validation_fields(config),  # WHY: bundle validation block.
        }

    def _similarity_fields(self, config: ComparisonItemConfig) -> dict[str, Any]:
        """Similarity percentages block shared by both reports."""
        result = config.comparison_result  # WHY: shorten access.
        field_sims = result["field_similarities"]  # WHY: shorten access.
        return {
            "Overall Similarity": (f"{result['overall_similarity']:.1f}%"),  # WHY: percent format.
            "Address Similarity": (f"{field_sims['address']:.1f}%"),  # WHY: percent format.
            "City Similarity": (f"{field_sims['city']:.1f}%"),  # WHY: percent format.
            "State Similarity": (f"{field_sims['state']:.1f}%"),  # WHY: percent format.
            "Zip Similarity": (f"{field_sims['zip']:.1f}%"),  # WHY: percent format.
        }

    def _parse_status_fields(self, config: ComparisonItemConfig) -> dict[str, Any]:
        """Parse-status columns block shared by both reports."""
        parse_status = config.comparison_result["parse_status"]  # WHY: shorten access.
        return {
            "Mist_Parse_Status": parse_status["mist_parseable"],  # WHY: bool string.
            "Comparison_Parse_Status": parse_status["comparison_parseable"],  # WHY: bool string.
            "Parse_Issues": self._format_parse_issues(config.comparison_result),  # WHY: reasons blob.
        }

    def _validation_fields(self, config: ComparisonItemConfig) -> dict[str, Any]:
        """Validation columns block shared by both reports."""
        return {
            "Mist_Validation_Status": (self._get_validation_status(config.validation_result, "mist")),  # WHY: str.
            "Mist_Confidence": (self._get_validation_confidence(config.validation_result, "mist")),  # WHY: str.
            "Comparison_Validation_Status": (
                self._get_validation_status(config.validation_result, "comparison")  # WHY: str.
            ),
            "Comparison_Confidence": (
                self._get_validation_confidence(config.validation_result, "comparison")  # WHY: str.
            ),
            "Validation_Recommendation": (
                config.validation_result["recommendation"] if config.validation_result else "N/A"  # WHY: default.
            ),
        }

    def _format_parse_issues(self, comparison_result: dict[str, Any]) -> str:
        """Format parse issues for display."""
        mist_reason = comparison_result["parse_status"]["mist_reason"]  # WHY: reason string.
        comp_reason = comparison_result["parse_status"]["comparison_reason"]  # WHY: reason string.
        return f"Mist: {mist_reason}, Comp: {comp_reason}"  # WHY: single joined blob.

    def _get_validation_status(
        self,
        validation_result: dict[str, Any] | None,
        source: str,
    ) -> str:
        """Get validation status for mist or comparison address."""
        if not validation_result:  # WHY: no validation ran.
            return "N/A"  # WHY: default label.
        key = f"{source}_validation"  # WHY: nested dict key.
        return str(validation_result[key]["valid"])  # WHY: bool -> str.

    def _get_validation_confidence(
        self,
        validation_result: dict[str, Any] | None,
        source: str,
    ) -> str:
        """Get validation confidence for mist or comparison."""
        if not validation_result:  # WHY: no validation ran.
            return "N/A"  # WHY: default label.
        key = f"{source}_validation"  # WHY: nested dict key.
        if validation_result[key]["valid"]:  # WHY: only report confidence if valid.
            return f"{validation_result[key]['confidence']:.3f}"  # WHY: fixed format.
        return "N/A"  # WHY: default label when invalid.

    # =================================================================
    # RESULTS DISPLAY METHODS
    # =================================================================

    def _finalize_and_display_results(self) -> None:
        """Finalize processing and display results."""
        self.counters.end_timing()  # WHY: stop the wallclock.
        if self.parse_failures:  # WHY: only emit failures CSV when non-empty.
            self._create_parse_failures_csv(self.parse_failures)  # WHY: caller-provided emitter.
        self._print_results_summary()  # WHY: user-facing summary.
        self.counters.log_summary()  # WHY: log-oriented summary.
        if self.mismatched_items:  # WHY: only save/display if there were mismatches.
            self._display_conflict_preview()  # WHY: user preview.
            self._save_results_to_csv()  # WHY: persist to disk.
        else:
            self._print_success_message()  # WHY: reassure user everything matched.

    def _print_results_summary(self) -> None:
        """Print comprehensive results summary."""
        print("\n  Data Integrity Analysis Results:")  # WHY: section header.
        print(f"   Total devices analyzed:" f" {self.counters.total_devices}")  # WHY: user info.
        print(f"   Devices with comparison data:" f" {self.counters.devices_enriched}")  # WHY: user info.
        print(f"    Devices excluded (not in comparison CSV):" f" {self.counters.devices_skipped}")  # WHY: user info.
        print(f"   Address conflicts found:" f" {self.counters.mismatches_found}")  # WHY: user info.
        print(f"   Consistent addresses:" f" {self.counters.perfect_matches}")  # WHY: user info.
        print(f"   Auto-skipped addresses:" f" {self.counters.auto_corrections}")  # WHY: user info.
        print(f"   Parse failures:" f" {self.counters.parse_failures}")  # WHY: user info.
        self._print_conflict_rate()  # WHY: optional percent-of-analysed line.
        self._print_parse_failure_breakdown()  # WHY: optional histogram.
        self._print_processing_rate()  # WHY: throughput display.

    def _print_conflict_rate(self) -> None:
        """Print conflict rate if applicable."""
        if self.counters.mismatches_found > 0 and self.counters.devices_enriched > 0:  # WHY: avoid div-by-zero.
            conflict_rate = (self.counters.mismatches_found / self.counters.devices_enriched) * 100  # WHY: percent.
            print(f"   Conflict rate: {conflict_rate:.1f}%" " of analyzed devices have discrepancies")  # WHY: user.

    def _print_parse_failure_breakdown(self) -> None:
        """Print parse failure breakdown if applicable."""
        if self.counters.parse_failures > 0:  # WHY: only when non-empty.
            print("   Parse failure breakdown:")  # WHY: section header.
            for reason, count in self.counters.parse_failure_reasons.items():  # WHY: iterate histogram.
                print(f"      - {reason}: {count}")  # WHY: user info.

    def _print_processing_rate(self) -> None:
        """Print processing rate if applicable."""
        duration = self.counters.get_duration()  # WHY: seconds elapsed.
        if duration > 0:  # WHY: avoid div-by-zero.
            processing_rate = self.counters.total_devices / duration  # WHY: devices per second.
            print(f"    Processing rate:" f" {processing_rate:.1f} devices/second")  # WHY: user info.

    def _display_conflict_preview(self) -> None:
        """Display preview of address conflicts."""
        print("\n  Data Integrity Conflicts" " (address discrepancies requiring review):")  # WHY: section header.
        print("=" * 130)  # WHY: visual separator.
        for idx, item in enumerate(self.mismatched_items[:10]):  # WHY: cap preview to first 10 items.
            self._print_conflict_item(idx, item)  # WHY: per-item print.
        if len(self.mismatched_items) > 10:  # WHY: only show truncation notice when truncated.
            remaining = len(self.mismatched_items) - 10  # WHY: remaining count.
            print(f"   ... and {remaining} more conflicts" " (see CSV report for complete list)")  # WHY: user info.

    def _print_conflict_item(self, idx: int, item: dict[str, Any]) -> None:
        """Print a single conflict item."""
        mist_addr = (
            f"{item.get('Mist_Address_Line_1', '')},"  # WHY: join Mist addr for display.
            f" {item.get('Mist_City', '')},"
            f" {item.get('Mist_State', '')}"
        )
        comp_addr = (
            f"{item.get('Comparison_Address', '')},"  # WHY: join comparison addr for display.
            f" {item.get('Comparison_City', '')},"
            f" {item.get('Comparison_State', '')}"
        )
        print(f"[{idx + 1:2}]" f" Serial: {item['System Serial Number']:<15}")  # WHY: header line.
        print(f"     Mist:       {mist_addr}")  # WHY: user visibility.
        print(f"     Reference:  {comp_addr}")  # WHY: user visibility.
        # WHY: user-facing similarity/type readout.
        print(f"     Similarity: {item['Overall Similarity']:<6} | Type: {item['Mismatch Type']}")
        if self.address_validation_enabled and item.get("Validation_Recommendation", "N/A") != "N/A":  # WHY: only.
            print("     Recommendation:" f" {item['Validation_Recommendation']}")  # WHY: user visibility.
        print()  # WHY: separator line.

    def _save_results_to_csv(self) -> None:
        """Save results to CSV file."""
        base_filename = self.comparison_file.replace(".csv", "")  # WHY: strip extension for slug.
        output_file = f"AddressMismatches_vs_{base_filename}.csv"  # WHY: canonical output name.
        fieldnames = self._get_output_fieldnames()  # WHY: fixed column order.
        with open(output_file, mode="w", newline="", encoding="utf-8") as file_handle:  # WHY: UTF-8 write.
            writer = csv.DictWriter(file_handle, fieldnames=fieldnames)  # WHY: dict rows to CSV.
            writer.writeheader()  # WHY: emit column headers.
            writer.writerows(self.diff_report_items)  # WHY: dump all rows.
        self._print_save_confirmation(output_file)  # WHY: user visibility.

    def _get_output_fieldnames(self) -> list[str]:
        """Get fieldnames for output CSV."""
        # WHY: concat class-level tuples to keep the function short + column order stable.
        return list(self._COMMON_FIELDS + self._DIFF_ADDRESS_FIELDS + self._TRAILING_FIELDS)

    def _print_save_confirmation(self, output_file: str) -> None:
        """Print save confirmation message."""
        print(f"! Data integrity report saved to: {output_file}")  # WHY: user visibility.
        print(f"! Location: {self._get_csv_path(output_file)}")  # WHY: absolute path.
        print("\n  Data Integrity Summary:")  # WHY: section header.
        print(f"   Found {len(self.diff_report_items)}" " address conflicts requiring review")  # WHY: user info.
        if self.address_validation_enabled:  # WHY: only when validation ran.
            print("   External validation recommendations" " included")  # WHY: user info.
            print("   Check 'Validation_Recommendation'" " column for guidance")  # WHY: hint.
        else:
            print("    No external validation performed")  # WHY: user info.
            print("   Run with --address-check for intelligent" " recommendations")  # WHY: hint.
        logging.info("Saved %s address conflicts to %s", len(self.diff_report_items), output_file)  # WHY: log record.

    def _print_success_message(self) -> None:
        """Print success message when no conflicts found."""
        total_good = self.counters.perfect_matches + self.counters.auto_corrections  # WHY: aggregate matches.
        print(f"! Data integrity check complete!" f" All {total_good} addresses are consistent.")  # WHY: user info.
        print("   No conflicts found between Mist" " and comparison data")  # WHY: user info.
        if self.counters.auto_corrections > 0:  # WHY: only mention when non-zero.
            print(f"   {self.counters.auto_corrections}" " addresses auto-skipped via" " AddressSkip.csv")  # WHY.
