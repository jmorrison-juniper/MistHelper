"""Inventory CSV comparison for address verification.

Extracts AddressComparisonCounters and InventoryCSVComparator from
MistHelper.py into a module with dependency injection for testability.
"""

# pylint: disable=too-many-lines,logging-fstring-interpolation,implicit-str-concat

from __future__ import annotations

import csv
import glob
import logging
import os
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv
from tqdm import tqdm


class AddressComparisonCounters:
    """Track comprehensive metrics for address comparison operations."""

    def __init__(self) -> None:
        """Initialize all counter attributes and timing."""
        self.total_devices: int = 0
        self.devices_enriched: int = 0
        self.devices_skipped: int = 0
        self.perfect_matches: int = 0
        self.mismatches_found: int = 0
        self.auto_corrections: int = 0
        self.comparison_failures: int = 0
        self.parse_failures: int = 0
        self.parse_failure_reasons: dict[str, int] = {}
        self.start_time: float | None = None
        self.end_time: float | None = None

    def start_timing(self) -> None:
        """Start the timing counter for performance tracking."""
        self.start_time = time.time()

    def end_timing(self) -> None:
        """End the timing counter for performance tracking."""
        self.end_time = time.time()

    def get_duration(self) -> float:
        """Get the elapsed time in seconds between start and end timing."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def increment_parse_failure(self, reason: str) -> None:
        """Increment parse failure counter and track the specific reason.

        Args:
            reason: The specific reason for the parse failure.
        """
        self.parse_failures += 1
        if reason in self.parse_failure_reasons:
            self.parse_failure_reasons[reason] += 1
        else:
            self.parse_failure_reasons[reason] = 1

    def log_summary(self) -> None:
        """Log a comprehensive summary of all counter metrics."""
        logging.info("Address comparison operation completed successfully")
        logging.info(f"Total devices processed: {self.total_devices}")
        logging.info(f"Devices enriched: {self.devices_enriched}")
        logging.info(f"Devices skipped: {self.devices_skipped}")
        logging.info(f"Perfect matches: {self.perfect_matches}")
        logging.info(f"Mismatches found: {self.mismatches_found}")
        logging.info(f"Auto corrections: {self.auto_corrections}")
        logging.info(f"Comparison failures: {self.comparison_failures}")
        logging.info(f"Parse failures: {self.parse_failures}")
        if self.parse_failure_reasons:
            logging.info(f"Parse failure breakdown: {self.parse_failure_reasons}")
        logging.info(f"Processing duration: {self.get_duration():.2f} seconds")


@dataclass
class ComparisonItemConfig:
    """Configuration for building mismatch and diff report items."""

    device: dict[str, Any]
    device_serial: str
    mist_address: dict[str, str]
    comparison_address: dict[str, str]
    comparison_result: dict[str, Any]
    week_key: str
    mismatch_type: str
    validation_result: dict[str, Any] | None


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

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        fast: bool,
        address_check: bool,
        debug: bool,
        skip_ssl_verify: bool,
        apisession: Any,
        get_csv_path_fn: Callable[[str], str],
        check_and_generate_csv_fn: Callable[..., Any],
        create_parse_failures_csv_fn: Callable[..., Any],
        devices_with_site_info_fn: Callable[..., Any],
        get_org_id_fn: Callable[..., str],
        get_device_identifier_fn: Callable[..., str],
        address_utils_cls: Any,
        nominatim_validator_cls: type,
        address_validation_config_cls: type,
    ) -> None:
        """Initialize the inventory comparator with configuration and dependencies.

        Args:
            fast: Enable optimized data generation with caching.
            address_check: Enable external address validation via Nominatim.
            debug: Enable detailed debug logging.
            skip_ssl_verify: Skip SSL verification for external APIs.
            apisession: Authenticated mistapi session object.
            get_csv_path_fn: Resolves CSV filenames to full paths.
            check_and_generate_csv_fn: Cache check/generation function.
            create_parse_failures_csv_fn: Creates parse failures CSV.
            devices_with_site_info_fn: Generates device inventory with sites.
            get_org_id_fn: Gets cached or prompted org ID.
            get_device_identifier_fn: Gets device display identifier.
            address_utils_cls: AddressUtils class reference.
            nominatim_validator_cls: NominatimValidator class reference.
            address_validation_config_cls: AddressValidationConfig class ref.
        """
        self.fast = fast
        self.address_check = address_check
        self.debug = debug
        self.skip_ssl_verify = skip_ssl_verify
        self._api = apisession
        self._get_csv_path = get_csv_path_fn
        self._check_and_generate_csv = check_and_generate_csv_fn
        self._create_parse_failures_csv = create_parse_failures_csv_fn
        self._devices_with_site_info = devices_with_site_info_fn
        self._get_org_id = get_org_id_fn
        self._get_device_identifier = get_device_identifier_fn
        self._address_utils = address_utils_cls
        self._nominatim_validator_cls = nominatim_validator_cls
        self._address_validation_config_cls = address_validation_config_cls
        self._init_state()

    def _init_state(self) -> None:
        """Initialize mutable state for a comparison run."""
        self.address_threshold: float = 75.0
        self.end_customer_name: str = ""
        self.end_customer_account_id: str = ""
        self.address_validation_enabled: bool = False
        self.site_configs: list[dict[str, Any]] = []
        self.comparison_data: list[dict[str, Any]] = []
        self.skip_addresses: list[dict[str, Any]] = []
        self.comparison_file: str = ""
        self.serial_field: str | None = None
        self.zip_field: str | None = None
        self.address_field: str | None = None
        self.city_field: str | None = None
        self.state_field: str | None = None
        self.country_field: str | None = None
        self.comparison_serials: dict[str, str] = {}
        self.comparison_address_lookup: dict[str, dict[str, str]] = {}
        self.mist_duplicates: dict[str, list[str]] = {}
        self.ref_duplicates: dict[str, list[str]] = {}
        self.counters = AddressComparisonCounters()
        self.parse_failures: list[dict[str, Any]] = []
        self.all_conflicts: list[dict[str, Any]] = []
        self.filtered_conflicts: list[dict[str, Any]] = []
        self.mismatched_items: list[dict[str, Any]] = []
        self.diff_report_items: list[dict[str, Any]] = []

    def execute(self) -> None:
        """Execute the complete inventory comparison workflow."""
        self.counters.start_timing()
        if not self._initialize_config():
            return
        if not self._load_source_data():
            return
        if not self._select_comparison_file():
            return
        if not self._load_comparison_data():
            return
        self._load_skip_addresses()
        if not self._detect_csv_fields():
            return
        self._build_lookup_dictionaries()
        self._detect_duplicate_addresses()
        self._process_all_devices()
        self._filter_conflicts()
        self._process_remaining_conflicts()
        self._finalize_and_display_results()

    # =================================================================
    # INITIALIZATION METHODS
    # =================================================================

    def _initialize_config(self) -> bool:
        """Load environment configuration and display header."""
        load_dotenv()
        self.end_customer_name = os.getenv("END_CUSTOMER_NAME", "")
        self.end_customer_account_id = os.getenv("END_CUSTOMER_ACCOUNT_ID", "")
        self.address_threshold = float(os.getenv("ADDRESS_MATCH_THRESHOLD", "75"))
        self._print_header()
        self._determine_validation_mode()
        return True

    def _print_header(self) -> None:
        """Display the operation header with configuration info."""
        print("* Data Integrity Analysis: Comparing Mist vs Comparison" " CSV addresses...")
        print(f"* Using address similarity threshold:" f" {self.address_threshold}%")
        print("* Enhanced features: defensive parsing, Unicode" " normalization, fuzzy matching")
        if self.fast:
            print("* Fast mode enabled: Using optimized data generation" " and caching")
        if self.debug:
            print(" Debug mode enabled: Detailed comparison logging active")
            logging.debug("ENTRY: InventoryCSVComparator.execute()")
            logging.debug(f"  Parameters: fast={self.fast}," f" address_check={self.address_check}")
            logging.debug(f"  ADDRESS_MATCH_THRESHOLD={self.address_threshold}")

    def _determine_validation_mode(self) -> None:
        """Determine if external address validation is enabled."""
        env_enabled = os.getenv("ENABLE_ADDRESS_VALIDATION", "false").lower() == "true"
        self.address_validation_enabled = self.address_check or env_enabled
        if self.address_validation_enabled:
            source = "--address-check flag" if self.address_check else ".env file"
            print(f"! External address validation enabled via {source}")
            print("   Address conflicts will be validated using" " Nominatim API")
            if self.debug:
                logging.debug(f"Address validation enabled via {source}")
        else:
            print("  External address validation disabled")
            print("   Use --address-check flag or set" " ENABLE_ADDRESS_VALIDATION=true")
            if self.debug:
                logging.debug("Address validation disabled")

    # =================================================================
    # DATA LOADING METHODS
    # =================================================================

    def _load_source_data(self) -> bool:
        """Load Mist device data with site information."""

        def generator() -> Any:
            return self._devices_with_site_info(fast=self.fast)

        self._check_and_generate_csv("AllDevicesWithSiteInfo.csv", generator)
        devices_path = self._get_csv_path("AllDevicesWithSiteInfo.csv")
        with open(devices_path, encoding="utf-8") as file_handle:
            self.site_configs = list(csv.DictReader(file_handle))
        return True

    def _select_comparison_file(self) -> bool:
        """Present CSV file selection to user and get selection."""
        csv_files = self._get_available_csv_files()
        if not csv_files:
            print(" No CSV files found in the data directory" " for comparison.")
            print("   Please place comparison CSV files in the" " 'data' folder.")
            logging.error("No CSV files found for comparison in data directory.")
            return False
        self._display_csv_file_list(csv_files)
        return self._get_user_csv_selection(csv_files)

    def _get_available_csv_files(self) -> list[str]:
        """Get list of CSV files available for comparison."""
        data_dir = "data"
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
        exclude_file = "AllDevicesWithSiteInfo.csv"
        return [os.path.basename(f) for f in csv_files if os.path.basename(f) != exclude_file]

    def _display_csv_file_list(self, csv_files: list[str]) -> None:
        """Display available CSV files for user selection."""
        print("\n  Available CSV files for comparison:")
        print("=" * 60)
        for idx, csv_file in enumerate(csv_files):
            print(f"[{idx}] {csv_file}")

    def _get_user_csv_selection(self, csv_files: list[str]) -> bool:
        """Get and validate user's CSV file selection."""
        try:
            prompt = f"\nEnter the index (0-{len(csv_files) - 1})" " of the CSV file to compare against: "
            user_input = input(prompt).strip()
            selected_index = int(user_input)
            if selected_index < 0 or selected_index >= len(csv_files):
                print(" Invalid index selected.")
                logging.error(f"Invalid CSV file index selected:" f" {selected_index}")
                return False
            self.comparison_file = csv_files[selected_index]
            print(f"! Selected comparison file:" f" {self.comparison_file}")
            logging.info(f"User selected comparison file:" f" {self.comparison_file}")
            return True
        except ValueError:
            print(" Invalid input. Please enter a numeric index.")
            logging.error("Invalid numeric input for CSV file selection.")
            return False
        except KeyboardInterrupt:
            print("\n Operation cancelled by user.")
            logging.info("CSV comparison operation cancelled by user.")
            return False

    def _load_comparison_data(self) -> bool:
        """Load the selected comparison CSV file."""
        try:
            comparison_path = self._get_csv_path(self.comparison_file)
            with open(comparison_path, encoding="utf-8") as file_handle:
                self.comparison_data = list(csv.DictReader(file_handle))
            print(f"! Loaded {len(self.site_configs)} devices from" " AllDevicesWithSiteInfo.csv")
            print(f"! Loaded {len(self.comparison_data)} records from" f" {self.comparison_file}")
            return True
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"! Error reading comparison file" f" {self.comparison_file}: {error}")
            logging.error(f"Error reading comparison file" f" {self.comparison_file}: {error}")
            return False

    def _load_skip_addresses(self) -> None:
        """Load the address skip list for automatic corrections."""
        skip_file_path = self._get_csv_path("AddressSkip.csv")
        try:
            with open(skip_file_path, encoding="utf-8") as file_handle:
                self.skip_addresses = list(csv.DictReader(file_handle))
            print(f"! Loaded {len(self.skip_addresses)} skip" " addresses from AddressSkip.csv")
            if self.debug:
                logging.debug(f"Loaded {len(self.skip_addresses)}" " addresses to skip")
        except FileNotFoundError:
            print("  AddressSkip.csv not found - no addresses" " will be automatically skipped")
            if self.debug:
                logging.debug("AddressSkip.csv not found - continuing" " without skip list")
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"!  Error loading AddressSkip.csv: {error}")
            logging.warning(f"Error loading AddressSkip.csv: {error}")

    # =================================================================
    # FIELD DETECTION METHODS
    # =================================================================

    def _detect_csv_fields(self) -> bool:
        """Detect and validate required fields in comparison CSV."""
        if not self.comparison_data:
            print(" Comparison CSV file is empty.")
            return False
        headers = self.comparison_data[0].keys()
        self._detect_serial_field(headers)
        self._detect_zip_field(headers)
        self._detect_address_fields(headers)
        if not self._validate_required_fields(headers):
            return False
        self._print_detected_fields()
        return True

    def _detect_serial_field(self, headers: Any) -> None:
        """Detect the serial number field in comparison CSV."""
        serial_terms = ["serial", "sn", "system serial"]
        for header in headers:
            if any(term in header.lower() for term in serial_terms):
                self.serial_field = header
                break

    def _detect_zip_field(self, headers: Any) -> None:
        """Detect the zip code field in comparison CSV."""
        zip_terms = ["zip", "postal", "zip code", "postal code"]
        for header in headers:
            if any(term in header.lower() for term in zip_terms):
                self.zip_field = header
                break

    def _detect_address_fields(self, headers: Any) -> None:
        """Detect address component fields in comparison CSV."""
        for header in headers:
            header_lower = header.lower()
            if any(term in header_lower for term in ["address", "street", "address line"]):
                self.address_field = header
            elif "city" in header_lower:
                self.city_field = header
            elif "state" in header_lower:
                self.state_field = header
            elif "country" in header_lower:
                self.country_field = header

    def _validate_required_fields(self, headers: Any) -> bool:
        """Validate that required fields were detected."""
        if not self.serial_field:
            print(" Could not find serial number field" " in comparison CSV.")
            print("   Looked for fields containing:" " 'serial', 'sn', 'system serial'")
            print(f"   Available fields: {list(headers)}")
            logging.error(f"Serial field not found." f" Available fields: {list(headers)}")
            return False
        if not self.zip_field:
            print(" Could not find zip code field" " in comparison CSV.")
            print("   Looked for fields containing:" " 'zip', 'postal', 'zip code', 'postal code'")
            print(f"   Available fields: {list(headers)}")
            logging.error(f"Zip field not found." f" Available fields: {list(headers)}")
            return False
        return True

    def _print_detected_fields(self) -> None:
        """Print the detected field mappings."""
        print(f"! Using serial field: '{self.serial_field}'")
        print(f"! Using zip field: '{self.zip_field}'")
        if self.address_field:
            print(f"! Using address field: '{self.address_field}'")
        if self.city_field:
            print(f"! Using city field: '{self.city_field}'")
        if self.state_field:
            print(f"! Using state field: '{self.state_field}'")
        if self.country_field:
            print(f"! Using country field: '{self.country_field}'")

    # =================================================================
    # LOOKUP BUILDER METHODS
    # =================================================================

    def _build_lookup_dictionaries(self) -> None:
        """Build lookup dictionaries from comparison data."""
        for row in self.comparison_data:
            serial = row.get(self.serial_field, "").strip() if self.serial_field else ""
            zip_code = row.get(self.zip_field, "").strip() if self.zip_field else ""
            if serial:
                normalized_zip = self._address_utils.normalize_zip(zip_code)
                self.comparison_serials[serial] = normalized_zip
                self.comparison_address_lookup[serial] = self._extract_address_from_row(row, zip_code)
        print(f"! Built comparison lookup with" f" {len(self.comparison_serials)} serial numbers")
        if self.address_validation_enabled:
            validation_count = self._count_devices_for_validation()
            print(f"! Will validate {validation_count} address" " conflicts using Nominatim API")

    def _extract_address_from_row(self, row: dict[str, Any], zip_code: str) -> dict[str, str]:
        """Extract address components from a comparison CSV row."""
        return {
            "Address": (row.get(self.address_field, "") if self.address_field else ""),
            "City": (row.get(self.city_field, "") if self.city_field else ""),
            "State": (row.get(self.state_field, "") if self.state_field else ""),
            "Country": (row.get(self.country_field, "") if self.country_field else ""),
            "Zip": zip_code,
        }

    def _count_devices_for_validation(self) -> int:
        """Count devices that will need external validation."""
        count = 0
        for device in self.site_configs:
            serial = device.get("serial", "").strip()
            if serial in self.comparison_serials:
                count += 1
        return count

    # =================================================================
    # DUPLICATE DETECTION METHODS
    # =================================================================

    def _detect_duplicate_addresses(self) -> None:
        """Detect duplicate addresses between sites."""
        print("\n  Checking for duplicate addresses between sites...")
        mist_site_addresses = self._build_mist_site_addresses()
        self.mist_duplicates = self._find_duplicates(mist_site_addresses)
        ref_site_addresses = self._build_ref_site_addresses()
        self.ref_duplicates = self._find_duplicates(ref_site_addresses)
        self._report_duplicates(mist_site_addresses, ref_site_addresses)

    def _build_mist_site_addresses(
        self,
    ) -> dict[str, dict[str, Any]]:
        """Build address mapping for Mist sites."""
        site_addresses: dict[str, dict[str, Any]] = {}
        for device in self.site_configs:
            site_name = device.get("site_name", "")
            if not site_name or site_name in site_addresses:
                continue
            mist_address = {
                "address": device.get("street", "").strip(),
                "city": device.get("city", "").strip(),
                "state": device.get("state", "").strip(),
                "zip": device.get("zip_code", "").strip(),
            }
            if not any(mist_address.values()):
                continue
            address_key = self._create_address_key(mist_address)
            site_addresses[site_name] = {
                "address_key": address_key,
                "address": mist_address,
            }
        return site_addresses

    def _build_ref_site_addresses(
        self,
    ) -> dict[str, dict[str, Any]]:
        """Build address mapping for reference sites."""
        site_addresses: dict[str, dict[str, Any]] = {}
        for device in self.site_configs:
            device_serial = device.get("serial", "").strip()
            site_name = device.get("site_name", "")
            if not site_name or site_name in site_addresses:
                continue
            if device_serial not in self.comparison_address_lookup:
                continue
            ref_data = self.comparison_address_lookup[device_serial]
            ref_address = {
                "address": ref_data.get("Address", "").strip(),
                "city": ref_data.get("City", "").strip(),
                "state": ref_data.get("State", "").strip(),
                "zip": ref_data.get("Zip", "").strip(),
            }
            if not any(ref_address.values()):
                continue
            address_key = self._create_address_key(ref_address)
            site_addresses[site_name] = {
                "address_key": address_key,
                "address": ref_address,
            }
        return site_addresses

    def _create_address_key(self, address: dict[str, str]) -> str:
        """Create a normalized address key for deduplication."""
        return (
            f"{address['address'].lower()}"
            f"|{address['city'].lower()}"
            f"|{address['state'].lower()}"
            f"|{address['zip']}"
        )

    def _find_duplicates(self, site_addresses: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
        """Find addresses shared by multiple sites."""
        address_to_sites: dict[str, list[str]] = {}
        for site_name, addr_data in site_addresses.items():
            address_key = addr_data["address_key"]
            if address_key not in address_to_sites:
                address_to_sites[address_key] = []
            address_to_sites[address_key].append(site_name)
        return {key: sites for key, sites in address_to_sites.items() if len(sites) > 1}

    def _report_duplicates(
        self,
        mist_addresses: dict[str, dict[str, Any]],
        ref_addresses: dict[str, dict[str, Any]],
    ) -> None:
        """Report duplicate address findings."""
        if self.mist_duplicates:
            self._print_duplicate_group("Mist", self.mist_duplicates, mist_addresses)
        if self.ref_duplicates:
            self._print_duplicate_group("Reference", self.ref_duplicates, ref_addresses)
        if not self.mist_duplicates and not self.ref_duplicates:
            print("    No duplicate addresses found between sites")
        else:
            self._print_duplicate_summary()

    def _print_duplicate_group(
        self,
        source: str,
        duplicates: dict[str, list[str]],
        addresses: dict[str, dict[str, Any]],
    ) -> None:
        """Print a group of duplicate addresses."""
        print(f"    {source} sites sharing the same address:")
        for _addr_key, sites in duplicates.items():
            sample_site = sites[0]
            addr = addresses[sample_site]["address"]
            print(f"        Address: {addr['address']}," f" {addr['city']}, {addr['state']}" f" {addr['zip']}")
            print(f"        Sites ({len(sites)}):" f" {', '.join(sites)}")

    def _print_duplicate_summary(self) -> None:
        """Print summary of duplicate findings."""
        mist_count = len(self.mist_duplicates)
        mist_sites = sum(len(sites) for sites in self.mist_duplicates.values())
        ref_count = len(self.ref_duplicates)
        ref_sites = sum(len(sites) for sites in self.ref_duplicates.values())
        print(f"     Found {mist_count} Mist address duplications" f" affecting {mist_sites} sites")
        print(f"     Found {ref_count} reference address" f" duplications affecting {ref_sites} sites")
        if self.debug:
            logging.info(f"DUPLICATE_CHECK: Found {mist_count} Mist" f" and {ref_count} reference duplicates")

    # =================================================================
    # DEVICE PROCESSING METHODS (Step 1)
    # =================================================================

    def _process_all_devices(self) -> None:
        """Process all devices to identify address conflicts."""
        print(f"\n  Processing {len(self.site_configs)}" " total devices...")
        print(" Step 1: Parsing and normalizing all addresses...")
        self.counters.total_devices = len(self.site_configs)
        first_missing_name_warned = False
        for device in tqdm(
            self.site_configs,
            desc="Step 1: Parsing Addresses",
            unit="device",
        ):
            first_missing_name_warned = self._process_device_in_loop(device, first_missing_name_warned)
        conflicts_found = len(self.all_conflicts)
        analyzed = self.counters.devices_enriched
        print(f"! Step 1 Complete: Found {conflicts_found}" f" address conflicts from {analyzed}" " analyzed devices")

    def _process_device_in_loop(
        self,
        device: dict[str, Any],
        first_missing_name_warned: bool,
    ) -> bool:
        """Process a single device within the main loop.

        Returns:
            Updated first_missing_name_warned flag.
        """
        device_serial = device.get("serial", "").strip()
        device_identifier = self._get_device_identifier(
            device,
            warn_on_missing=not first_missing_name_warned,
        )
        if not first_missing_name_warned and device_identifier != device.get("name", "").strip():
            first_missing_name_warned = True
        if device_serial not in self.comparison_serials:
            self.counters.devices_skipped += 1
            if self.debug:
                logging.debug(f"DEVICE_SKIP [{device_serial}]:" " Not found in comparison CSV")
            return first_missing_name_warned
        self.counters.devices_enriched += 1
        self._process_single_device(device, device_serial, device_identifier)
        return first_missing_name_warned

    def _process_single_device(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
    ) -> None:
        """Process a single device for address comparison."""
        try:
            mist_address = self._parse_mist_address(device, device_serial, device_identifier)
            comparison_address = self._get_comparison_address(device_serial)
            if not comparison_address:
                self.counters.devices_skipped += 1
                return
            comparison_result = self._address_utils.compare_with_threshold(
                mist_address,
                comparison_address,
                self.address_threshold,
                debug=self.debug,
            )
            if self.debug:
                logging.debug(f"DEVICE_COMPARISON [{device_serial}]:" f" Result: {comparison_result}")
            self._record_comparison_result(
                device,
                device_serial,
                device_identifier,
                mist_address,
                comparison_address,
                comparison_result,
            )
        except Exception as device_error:  # pylint: disable=broad-exception-caught
            logging.warning(f"! Error processing device" f" {device_serial}: {device_error}")
            self.counters.comparison_failures += 1
            self._record_device_parse_failure(
                device,
                device_serial,
                device_identifier,
                str(device_error),
            )

    def _record_comparison_result(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
        mist_address: dict[str, str],
        comparison_address: dict[str, str],
        comparison_result: dict[str, Any],
    ) -> None:
        """Record comparison result as match or conflict."""
        if comparison_result["is_match"]:
            self.counters.perfect_matches += 1
        else:
            self.counters.mismatches_found += 1
            self.all_conflicts.append(
                {
                    "device": device,
                    "device_serial": device_serial,
                    "device_identifier": device_identifier,
                    "mist_address": mist_address,
                    "comparison_address": comparison_address,
                    "comparison_result": comparison_result,
                }
            )

    def _parse_mist_address(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
    ) -> dict[str, str]:
        """Parse address from Mist device data."""
        mist_address_raw = device.get("site_address", "").strip()
        if not mist_address_raw:
            return self._get_component_address(device)
        parsed_mist = self._address_utils.enhanced_parse(mist_address_raw, debug=self.debug)
        if not parsed_mist["is_parseable"]:
            self._record_mist_parse_failure(
                device,
                device_serial,
                device_identifier,
                mist_address_raw,
                parsed_mist,
            )
            return self._get_component_address(device)
        return {
            "address": parsed_mist.get("address") or "",
            "city": parsed_mist.get("city") or "",
            "state": parsed_mist.get("state") or "",
            "zip": parsed_mist.get("zip") or "",
        }

    def _get_component_address(self, device: dict[str, Any]) -> dict[str, str]:
        """Get address from individual component fields."""
        return {
            "address": device.get("street", "").strip(),
            "city": device.get("city", "").strip(),
            "state": device.get("state", "").strip(),
            "zip": device.get("zip_code", "").strip(),
        }

    def _get_comparison_address(self, device_serial: str) -> dict[str, str] | None:
        """Get comparison address for a device serial."""
        comparison_data = self.comparison_address_lookup.get(device_serial, {})
        if not comparison_data or not any(comparison_data.values()):
            if self.debug:
                logging.debug(f"DEVICE_SKIP [{device_serial}]:" " No comparison address data")
            return None
        comparison_address = {
            "address": comparison_data.get("Address", "").strip(),
            "city": comparison_data.get("City", "").strip(),
            "state": comparison_data.get("State", "").strip(),
            "zip": comparison_data.get("Zip", "").strip(),
        }
        if not any(comparison_address.values()):
            if self.debug:
                logging.debug(f"DEVICE_SKIP [{device_serial}]:" " Empty comparison address")
            return None
        return comparison_address

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
            "site_id": device.get("site_id", ""),
            "site_name": device.get("site_name", ""),
            "device_id": device.get("id", ""),
            "device_serial": device_serial,
            "device_name": device_identifier,
            "original_address": raw_address,
            "parsed_tokens": str(raw_address.split(",")),
            "failure_reason": parsed_result["parse_reason"],
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.parse_failures.append(failure_record)
        self.counters.increment_parse_failure(parsed_result["parse_reason"])

    def _record_device_parse_failure(
        self,
        device: dict[str, Any],
        device_serial: str,
        device_identifier: str,
        error_msg: str,
    ) -> None:
        """Record a device processing error as parse failure."""
        failure_record = {
            "site_id": device.get("site_id", ""),
            "site_name": device.get("site_name", ""),
            "device_id": device.get("id", ""),
            "device_serial": device_serial,
            "device_name": device_identifier,
            "original_address": str(device.get("site_address", "")),
            "parsed_tokens": "N/A",
            "failure_reason": (f"device_processing_error: {error_msg}"),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.parse_failures.append(failure_record)
        self.counters.increment_parse_failure("device_processing_error")

    # =================================================================
    # CONFLICT FILTERING METHODS (Steps 2-3)
    # =================================================================

    def _filter_conflicts(self) -> None:
        """Filter conflicts through dedup and skip list."""
        unique_conflicts = self._remove_duplicate_conflicts()
        self.filtered_conflicts = self._apply_skip_filters(unique_conflicts)

    def _remove_duplicate_conflicts(
        self,
    ) -> list[dict[str, Any]]:
        """Remove duplicate address pairs from conflicts."""
        print(" Step 2: Removing duplicate addresses...")
        unique_conflicts: list[dict[str, Any]] = []
        seen_addresses: set[str] = set()
        for conflict in self.all_conflicts:
            address_key = self._create_conflict_address_key(conflict)
            if address_key not in seen_addresses:
                seen_addresses.add(address_key)
                unique_conflicts.append(conflict)
            elif self.debug:
                logging.debug("DUPLICATE_REMOVED" f" [{conflict['device_serial']}]")
        duplicates_removed = len(self.all_conflicts) - len(unique_conflicts)
        print(
            f"! Step 2 Complete: Removed {duplicates_removed}" f" duplicate pairs," f" {len(unique_conflicts)} remain"
        )
        return unique_conflicts

    def _create_conflict_address_key(self, conflict: dict[str, Any]) -> str:
        """Create a unique key for a conflict's address pair."""
        mist_addr = conflict["mist_address"]
        comp_addr = conflict["comparison_address"]
        mist_key = (
            f"{mist_addr['address'].lower().strip()}"
            f"|{mist_addr['city'].lower().strip()}"
            f"|{mist_addr['state'].lower().strip()}"
            f"|{mist_addr['zip'].strip()}"
        )
        comp_key = (
            f"{comp_addr['address'].lower().strip()}"
            f"|{comp_addr['city'].lower().strip()}"
            f"|{comp_addr['state'].lower().strip()}"
            f"|{comp_addr['zip'].strip()}"
        )
        return f"{mist_key}||{comp_key}"

    def _apply_skip_filters(self, unique_conflicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply address skip filters to conflicts."""
        print(" Step 3: Applying address skip filters...")
        filtered: list[dict[str, Any]] = []
        for conflict in unique_conflicts:
            comparison_address = conflict["comparison_address"]
            device_serial = conflict["device_serial"]
            should_skip, skip_reason = self._address_utils.check_should_skip(
                comparison_address,
                self.skip_addresses,
                debug=self.debug,
            )
            if should_skip:
                self._record_skipped_address(device_serial, skip_reason)
            else:
                filtered.append(conflict)
        skip_filtered = len(unique_conflicts) - len(filtered)
        print(f"! Step 3 Complete: Removed {skip_filtered}" f" via skip filters," f" {len(filtered)} require analysis")
        return filtered

    def _record_skipped_address(self, device_serial: str, skip_reason: str) -> None:
        """Record an auto-skipped address."""
        self.counters.perfect_matches += 1
        self.counters.auto_corrections += 1
        if self.debug:
            logging.debug(f"ADDRESS_SKIP [{device_serial}]:" f" {skip_reason}")
        print(f"    Auto-corrected: {device_serial}" f" (Skip reason: {skip_reason})")

    # =================================================================
    # VALIDATION AND MISMATCH PROCESSING (Step 4)
    # =================================================================

    def _process_remaining_conflicts(self) -> None:
        """Process remaining conflicts with optional validation."""
        if not self.filtered_conflicts:
            return
        if self.address_validation_enabled:
            self._process_with_validation()
        else:
            self._process_without_validation()

    def _process_without_validation(self) -> None:
        """Process conflicts without external validation."""
        print(f"\n  Step 4: Processing" f" {len(self.filtered_conflicts)}" " conflicts without validation...")
        for conflict in self.filtered_conflicts:
            self._generate_mismatch_records(conflict, validation_result=None)

    def _process_with_validation(self) -> None:
        """Process conflicts with external Nominatim validation."""
        total_validations = len(self.filtered_conflicts)
        print(f"\n  Step 4: External validation enabled -" f" {total_validations} conflicts need validation")
        print(" This may take several minutes due to" " API rate limiting (1 request/second)...")
        org_name = self._get_org_name_for_validation()
        for idx, conflict in enumerate(
            tqdm(
                self.filtered_conflicts,
                desc="Step 4: Validating",
                unit="device",
            )
        ):
            validation_result = self._validate_single_conflict(
                conflict,
                idx + 1,
                total_validations,
                org_name,
            )
            self._generate_mismatch_records(conflict, validation_result)

    def _get_org_name_for_validation(self) -> str | None:
        """Get organization name for tiebreaker logic."""
        try:
            if self.debug:
                logging.debug("Fetching organization information" " for tiebreaker logic...")
            import mistapi  # pylint: disable=import-outside-toplevel

            org_id = self._get_org_id()
            org_response = mistapi.api.v1.orgs.orgs.getOrg(self._api, org_id)
            if org_response.status_code == 200:
                org_name: str = org_response.data.get("name", "").strip()
                if self.debug:
                    logging.debug(f"Organization name retrieved:" f" '{org_name}'")
                return org_name
            if self.debug:
                logging.warning(f"Failed to retrieve org info:" f" HTTP {org_response.status_code}")
            return None
        except Exception as error:  # pylint: disable=broad-exception-caught
            if self.debug:
                logging.warning("Could not retrieve organization" f" name: {error}")
            return None

    def _validate_single_conflict(
        self,
        conflict: dict[str, Any],
        current: int,
        total: int,
        org_name: str | None,
    ) -> dict[str, Any] | None:
        """Validate a single conflict using Nominatim API."""
        device = conflict["device"]
        device_serial = conflict["device_serial"]
        mist_address = conflict["mist_address"]
        comparison_address = conflict["comparison_address"]
        self._print_validation_header(
            device_serial,
            mist_address,
            comparison_address,
            current,
            total,
        )
        try:
            timeout = int(os.getenv("ADDRESS_VALIDATION_TIMEOUT", "10"))
            validator_config = self._address_validation_config_cls(
                timeout=timeout,
                debug=self.debug,
                skip_ssl_verify=self.skip_ssl_verify,
                org_name=org_name,
                site_name=device.get("site_name", ""),
                mist_duplicates=self.mist_duplicates,
                ref_duplicates=self.ref_duplicates,
            )
            validator = self._nominatim_validator_cls(validator_config)
            validation_result = validator.validate(mist_address, comparison_address)
            self._print_validation_results(device_serial, validation_result)
            return validation_result  # type: ignore[no-any-return]
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"    Validation failed: {error!s}")
            logging.warning(f"ADDRESS_VALIDATION [{device_serial}]:" f" Validation failed: {error}")
            if self.debug:
                logging.debug(f"ADDRESS_VALIDATION [{device_serial}]:" f" {traceback.format_exc()}")
            return None

    def _print_validation_header(
        self,
        device_serial: str,
        mist_address: dict[str, str],
        comparison_address: dict[str, str],
        current: int,
        total: int,
    ) -> None:
        """Print validation header for a device."""
        mist_str = self._format_address_string(mist_address)
        comp_str = self._format_address_string(comparison_address)
        print(f"! [{current}/{total}]" f" Validating {device_serial}...")
        print(f"    Mist:       {mist_str}")
        print(f"    Reference:  {comp_str}")
        logging.info(f"ADDRESS_VALIDATION [{device_serial}]:" " Starting validation")
        logging.info(f"ADDRESS_VALIDATION [{device_serial}]:" f" Mist: {mist_str}")
        logging.info(f"ADDRESS_VALIDATION [{device_serial}]:" f" Comparison: {comp_str}")

    def _format_address_string(self, address: dict[str, str]) -> str:
        """Format address dictionary as display string."""
        return (
            (f"{address['address']}, {address['city']}," f" {address['state']} {address['zip']}")
            .replace(", , ", ", ")
            .strip(", ")
        )

    def _print_validation_results(
        self,
        device_serial: str,
        result: dict[str, Any],
    ) -> None:
        """Print validation results for a device."""
        mist_valid = result["mist_validation"]["valid"]
        comp_valid = result["comparison_validation"]["valid"]
        mist_status = " Valid" if mist_valid else " Invalid"
        comp_status = " Valid" if comp_valid else " Invalid"
        mist_conf = f"{result['mist_validation']['confidence']:.3f}" if mist_valid else "N/A"
        comp_conf = f"{result['comparison_validation']['confidence']:.3f}" if comp_valid else "N/A"
        recommendation_icon = {
            "mist": " Mist",
            "comparison": " Reference",
            "uncertain": " Uncertain",
        }
        recommendation_display = recommendation_icon.get(result["recommendation"], result["recommendation"])
        recommendation_reason = result.get("recommendation_reason", "No reason provided")
        print(
            f"    Results:    Mist: {mist_status}"
            f" (conf: {mist_conf})"
            f" | Reference: {comp_status}"
            f" (conf: {comp_conf})"
        )
        print(f"    Recommendation: {recommendation_display}")
        if result["recommendation"] != "uncertain" or "inconclusive" not in recommendation_reason.lower():
            print(f"    Reason: {recommendation_reason}")
        logging.info(f"ADDRESS_VALIDATION [{device_serial}]:" f" Mist valid={mist_valid}," f" conf={mist_conf}")
        logging.info(f"ADDRESS_VALIDATION [{device_serial}]:" f" Comp valid={comp_valid}," f" conf={comp_conf}")
        logging.info(f"ADDRESS_VALIDATION [{device_serial}]:" f" Recommendation: {result['recommendation']}")

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
            device = conflict["device"]
            device_serial = conflict["device_serial"]
            comparison_result = conflict["comparison_result"]
            mist_address = conflict["mist_address"]
            comparison_address = conflict["comparison_address"]
            week_key = self._get_week_key(device)
            mismatch_type = self._determine_mismatch_type(comparison_result)
            mismatch_item = self._build_mismatch_item(
                ComparisonItemConfig(
                    device=device,
                    device_serial=device_serial,
                    mist_address=mist_address,
                    comparison_address=comparison_address,
                    comparison_result=comparison_result,
                    week_key=week_key,
                    mismatch_type=mismatch_type,
                    validation_result=validation_result,
                )
            )
            self.mismatched_items.append(mismatch_item)
            diff_item = self._build_diff_item(
                ComparisonItemConfig(
                    device=device,
                    device_serial=device_serial,
                    mist_address=mist_address,
                    comparison_address=comparison_address,
                    comparison_result=comparison_result,
                    week_key=week_key,
                    mismatch_type=mismatch_type,
                    validation_result=validation_result,
                )
            )
            self.diff_report_items.append(diff_item)
        except Exception as error:  # pylint: disable=broad-exception-caught
            logging.warning(
                "! Error processing mismatch for device" f" {conflict.get('device_serial', 'unknown')}:" f" {error}"
            )
            self.counters.comparison_failures += 1

    def _get_week_key(self, device: dict[str, Any]) -> str:
        """Get the week key for a device based on creation time."""
        created_time = int(device.get("created_time", 0))
        created_date = datetime.fromtimestamp(created_time, tz=UTC)
        year, week, _ = created_date.isocalendar()
        return f"{year}_Week_{week:02d}"

    def _determine_mismatch_type(self, comparison_result: dict[str, Any]) -> str:
        """Determine the primary mismatch type."""
        failed_fields = comparison_result["failed_fields"]
        if "zip" in failed_fields and len(failed_fields) == 1:
            return "Zip Code Mismatch"
        if "address" in failed_fields:
            return "Address Mismatch"
        if "city" in failed_fields:
            return "City Mismatch"
        if "state" in failed_fields:
            return "State Mismatch"
        return "Multi-field Address Mismatch"

    def _build_mismatch_item(
        self,
        config: ComparisonItemConfig,
    ) -> dict[str, Any]:
        """Build a mismatch item dictionary."""
        return {
            "Week": config.week_key,
            "Full Site": config.device.get("site_name", ""),
            "System Serial Number": config.device_serial,
            "System Model Number": config.device.get("model", ""),
            "End Customer Name": self.end_customer_name,
            "Address Line 1": config.mist_address["address"],
            "Address Line 2": "",
            "City": config.mist_address["city"],
            "State": config.mist_address["state"],
            "Current Zip Code": config.mist_address["zip"],
            "Current Zip Normalized": (self._address_utils.normalize_zip(config.mist_address["zip"])),
            "Comparison Zip Code": config.comparison_address["zip"],
            "End Customer Account ID": (self.end_customer_account_id),
            "Mismatch Type": config.mismatch_type,
            "Overall Similarity": (f"{config.comparison_result['overall_similarity']:.1f}%"),
            "Address Similarity": (f"{config.comparison_result['field_similarities']['address']:.1f}%"),
            "City Similarity": (f"{config.comparison_result['field_similarities']['city']:.1f}%"),
            "State Similarity": (f"{config.comparison_result['field_similarities']['state']:.1f}%"),
            "Zip Similarity": (f"{config.comparison_result['field_similarities']['zip']:.1f}%"),
            "Failed Fields": ", ".join(config.comparison_result["failed_fields"]),
            "Mist_Parse_Status": config.comparison_result["parse_status"]["mist_parseable"],
            "Comparison_Parse_Status": config.comparison_result["parse_status"]["comparison_parseable"],
            "Parse_Issues": self._format_parse_issues(config.comparison_result),
            "Mist_Validation_Status": (self._get_validation_status(config.validation_result, "mist")),
            "Mist_Confidence": (self._get_validation_confidence(config.validation_result, "mist")),
            "Comparison_Validation_Status": (self._get_validation_status(config.validation_result, "comparison")),
            "Comparison_Confidence": (self._get_validation_confidence(config.validation_result, "comparison")),
            "Validation_Recommendation": (
                config.validation_result["recommendation"] if config.validation_result else "N/A"
            ),
        }

    def _build_diff_item(
        self,
        config: ComparisonItemConfig,
    ) -> dict[str, Any]:
        """Build a diff report item dictionary."""
        return {
            "Week": config.week_key,
            "Full Site": config.device.get("site_name", ""),
            "System Serial Number": config.device_serial,
            "System Model Number": config.device.get("model", ""),
            "End Customer Name": self.end_customer_name,
            "Mist_Address_Line_1": config.mist_address["address"],
            "Mist_City": config.mist_address["city"],
            "Mist_State": config.mist_address["state"],
            "Mist_Zip_Code": config.mist_address["zip"],
            "Mist_Zip_Normalized": (self._address_utils.normalize_zip(config.mist_address["zip"])),
            "Comparison_Address": (config.comparison_address["address"]),
            "Comparison_City": config.comparison_address["city"],
            "Comparison_State": config.comparison_address["state"],
            "Comparison_Zip_Code": config.comparison_address["zip"],
            "Comparison_Zip_Normalized": (self._address_utils.normalize_zip(config.comparison_address["zip"])),
            "End Customer Account ID": (self.end_customer_account_id),
            "Mismatch Type": config.mismatch_type,
            "Overall Similarity": (f"{config.comparison_result['overall_similarity']:.1f}%"),
            "Address Similarity": (f"{config.comparison_result['field_similarities']['address']:.1f}%"),
            "City Similarity": (f"{config.comparison_result['field_similarities']['city']:.1f}%"),
            "State Similarity": (f"{config.comparison_result['field_similarities']['state']:.1f}%"),
            "Zip Similarity": (f"{config.comparison_result['field_similarities']['zip']:.1f}%"),
            "Failed Fields": ", ".join(config.comparison_result["failed_fields"]),
            "Mist_Parse_Status": config.comparison_result["parse_status"]["mist_parseable"],
            "Comparison_Parse_Status": config.comparison_result["parse_status"]["comparison_parseable"],
            "Parse_Issues": self._format_parse_issues(config.comparison_result),
            "Mist_Validation_Status": (self._get_validation_status(config.validation_result, "mist")),
            "Mist_Confidence": (self._get_validation_confidence(config.validation_result, "mist")),
            "Comparison_Validation_Status": (self._get_validation_status(config.validation_result, "comparison")),
            "Comparison_Confidence": (self._get_validation_confidence(config.validation_result, "comparison")),
            "Validation_Recommendation": (
                config.validation_result["recommendation"] if config.validation_result else "N/A"
            ),
        }

    def _format_parse_issues(self, comparison_result: dict[str, Any]) -> str:
        """Format parse issues for display."""
        mist_reason = comparison_result["parse_status"]["mist_reason"]
        comp_reason = comparison_result["parse_status"]["comparison_reason"]
        return f"Mist: {mist_reason}, Comp: {comp_reason}"

    def _get_validation_status(
        self,
        validation_result: dict[str, Any] | None,
        source: str,
    ) -> str:
        """Get validation status for mist or comparison address."""
        if not validation_result:
            return "N/A"
        key = f"{source}_validation"
        return str(validation_result[key]["valid"])

    def _get_validation_confidence(
        self,
        validation_result: dict[str, Any] | None,
        source: str,
    ) -> str:
        """Get validation confidence for mist or comparison."""
        if not validation_result:
            return "N/A"
        key = f"{source}_validation"
        if validation_result[key]["valid"]:
            return f"{validation_result[key]['confidence']:.3f}"
        return "N/A"

    # =================================================================
    # RESULTS DISPLAY METHODS
    # =================================================================

    def _finalize_and_display_results(self) -> None:
        """Finalize processing and display results."""
        self.counters.end_timing()
        if self.parse_failures:
            self._create_parse_failures_csv(self.parse_failures)
        self._print_results_summary()
        self.counters.log_summary()
        if self.mismatched_items:
            self._display_conflict_preview()
            self._save_results_to_csv()
        else:
            self._print_success_message()

    def _print_results_summary(self) -> None:
        """Print comprehensive results summary."""
        print("\n  Data Integrity Analysis Results:")
        print(f"   Total devices analyzed:" f" {self.counters.total_devices}")
        print(f"   Devices with comparison data:" f" {self.counters.devices_enriched}")
        print(f"    Devices excluded (not in comparison CSV):" f" {self.counters.devices_skipped}")
        print(f"   Address conflicts found:" f" {self.counters.mismatches_found}")
        print(f"   Consistent addresses:" f" {self.counters.perfect_matches}")
        print(f"   Auto-skipped addresses:" f" {self.counters.auto_corrections}")
        print(f"   Parse failures:" f" {self.counters.parse_failures}")
        self._print_conflict_rate()
        self._print_parse_failure_breakdown()
        self._print_processing_rate()

    def _print_conflict_rate(self) -> None:
        """Print conflict rate if applicable."""
        if self.counters.mismatches_found > 0 and self.counters.devices_enriched > 0:
            conflict_rate = (self.counters.mismatches_found / self.counters.devices_enriched) * 100
            print(f"   Conflict rate: {conflict_rate:.1f}%" " of analyzed devices have discrepancies")

    def _print_parse_failure_breakdown(self) -> None:
        """Print parse failure breakdown if applicable."""
        if self.counters.parse_failures > 0:
            print("   Parse failure breakdown:")
            for reason, count in self.counters.parse_failure_reasons.items():
                print(f"      - {reason}: {count}")

    def _print_processing_rate(self) -> None:
        """Print processing rate if applicable."""
        duration = self.counters.get_duration()
        if duration > 0:
            processing_rate = self.counters.total_devices / duration
            print(f"    Processing rate:" f" {processing_rate:.1f} devices/second")

    def _display_conflict_preview(self) -> None:
        """Display preview of address conflicts."""
        print("\n  Data Integrity Conflicts" " (address discrepancies requiring review):")
        print("=" * 130)
        for idx, item in enumerate(self.mismatched_items[:10]):
            self._print_conflict_item(idx, item)
        if len(self.mismatched_items) > 10:
            remaining = len(self.mismatched_items) - 10
            print(f"   ... and {remaining} more conflicts" " (see CSV report for complete list)")

    def _print_conflict_item(self, idx: int, item: dict[str, Any]) -> None:
        """Print a single conflict item."""
        mist_addr = (
            f"{item.get('Mist_Address_Line_1', '')}," f" {item.get('Mist_City', '')}," f" {item.get('Mist_State', '')}"
        )
        comp_addr = (
            f"{item.get('Comparison_Address', '')},"
            f" {item.get('Comparison_City', '')},"
            f" {item.get('Comparison_State', '')}"
        )
        print(f"[{idx + 1:2}]" f" Serial: {item['System Serial Number']:<15}")
        print(f"     Mist:       {mist_addr}")
        print(f"     Reference:  {comp_addr}")
        print(f"     Similarity: {item['Overall Similarity']:<6}" f" | Type: {item['Mismatch Type']}")
        if self.address_validation_enabled and item.get("Validation_Recommendation", "N/A") != "N/A":
            print("     Recommendation:" f" {item['Validation_Recommendation']}")
        print()

    def _save_results_to_csv(self) -> None:
        """Save results to CSV file."""
        base_filename = self.comparison_file.replace(".csv", "")
        output_file = f"AddressMismatches_vs_{base_filename}.csv"
        fieldnames = self._get_output_fieldnames()
        with open(output_file, mode="w", newline="", encoding="utf-8") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.diff_report_items)
        self._print_save_confirmation(output_file)

    def _get_output_fieldnames(self) -> list[str]:
        """Get fieldnames for output CSV."""
        return [
            "Week",
            "Full Site",
            "System Serial Number",
            "System Model Number",
            "End Customer Name",
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
        ]

    def _print_save_confirmation(self, output_file: str) -> None:
        """Print save confirmation message."""
        print(f"! Data integrity report saved to: {output_file}")
        print(f"! Location: {self._get_csv_path(output_file)}")
        print("\n  Data Integrity Summary:")
        print(f"   Found {len(self.diff_report_items)}" " address conflicts requiring review")
        if self.address_validation_enabled:
            print("   External validation recommendations" " included")
            print("   Check 'Validation_Recommendation'" " column for guidance")
        else:
            print("    No external validation performed")
            print("   Run with --address-check for intelligent" " recommendations")
        logging.info(f"Saved {len(self.diff_report_items)}" f" address conflicts to {output_file}")

    def _print_success_message(self) -> None:
        """Print success message when no conflicts found."""
        total_good = self.counters.perfect_matches + self.counters.auto_corrections
        print(f"! Data integrity check complete!" f" All {total_good} addresses are consistent.")
        print("   No conflicts found between Mist" " and comparison data")
        if self.counters.auto_corrections > 0:
            print(f"   {self.counters.auto_corrections}" " addresses auto-skipped via" " AddressSkip.csv")
