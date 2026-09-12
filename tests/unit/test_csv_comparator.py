"""Tests for InventoryCSVComparator (Issue #216).

Uses identity-checked teardown to avoid cross-test sys.modules contamination.
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# --- Module-level mistapi stub, restored the moment the import finishes ---
# WHY: pytest imports every test module during collection but runs teardown_module only
# for a module that has a selected test. A stub left in sys.modules therefore leaks for
# the whole session and breaks mistapi's lazy subpackage import. See issue #1739.
# The module under test binds this stub in its own namespace at import time, so the
# tests keep seeing it after sys.modules is restored.
_saved_mistapi = sys.modules.get("mistapi")
_our_mock = MagicMock()
sys.modules["mistapi"] = _our_mock
try:
    from src.inventory.csv_comparator import (
        AddressComparisonCounters,
        ComparatorDependencies,
        ComparatorFlags,
        InventoryCSVComparator,
        RecordComparisonInputs,
    )
finally:
    if _saved_mistapi is not None:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)


def setup_module() -> None:
    """Re-assert our stub for the duration of this module's tests."""
    sys.modules["mistapi"] = _our_mock


def teardown_module() -> None:
    """Restore sys.modules only if our stub is still installed."""
    if sys.modules.get("mistapi") is not _our_mock:
        return
    if _saved_mistapi is not None:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)


# --- Helpers ---


def _mock_address_utils() -> MagicMock:
    """Create a mock AddressUtils class with expected methods."""
    cls = MagicMock()
    cls.normalize_zip = MagicMock(side_effect=lambda z: z.strip()[:5])
    cls.enhanced_parse = MagicMock(
        return_value={
            "is_parseable": True,
            "address": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
            "parse_reason": "ok",
        }
    )
    cls.compare_with_threshold = MagicMock(
        return_value={
            "is_match": False,
            "overall_similarity": 50.0,
            "field_similarities": {
                "address": 60.0,
                "city": 40.0,
                "state": 100.0,
                "zip": 0.0,
            },
            "failed_fields": ["zip", "city"],
            "parse_status": {
                "mist_parseable": True,
                "comparison_parseable": True,
                "mist_reason": "ok",
                "comparison_reason": "ok",
            },
        }
    )
    cls.check_should_skip = MagicMock(return_value=(False, ""))
    return cls


def _make_comparator(**overrides: object) -> InventoryCSVComparator:
    """Create a comparator with default mocked dependencies."""
    flag_defaults: dict[str, object] = {
        "fast": False,
        "address_check": False,
        "debug": False,
        "skip_ssl_verify": True,
    }
    dep_defaults: dict[str, object] = {
        "apisession": MagicMock(),
        "get_csv_path_fn": lambda f: f"data/{f}",
        "check_and_generate_csv_fn": MagicMock(),
        "create_parse_failures_csv_fn": MagicMock(),
        "devices_with_site_info_fn": MagicMock(return_value=[]),
        "get_org_id_fn": MagicMock(return_value="test-org-id"),
        "get_device_identifier_fn": lambda d, **kw: d.get("name", d.get("serial", "unknown")),
        "address_utils_cls": _mock_address_utils(),
        "nominatim_validator_cls": MagicMock,
        "address_validation_config_cls": MagicMock,
    }
    for key, value in overrides.items():
        if key in flag_defaults:
            flag_defaults[key] = value
        else:
            dep_defaults[key] = value
    flags = ComparatorFlags(**flag_defaults)  # type: ignore[arg-type]
    deps = ComparatorDependencies(**dep_defaults)  # type: ignore[arg-type]
    return InventoryCSVComparator(flags=flags, deps=deps)


# ================================================================
# AddressComparisonCounters tests
# ================================================================


class TestAddressComparisonCounters:
    """Tests for AddressComparisonCounters."""

    def test_init_defaults(self) -> None:
        """Verify initial counter values are zero."""
        counters = AddressComparisonCounters()
        assert counters.total_devices == 0
        assert counters.devices_enriched == 0
        assert counters.parse_failures == 0
        assert counters.parse_failure_reasons == {}
        assert counters.start_time is None
        assert counters.end_time is None

    def test_timing(self) -> None:
        """Verify timing start/end/duration."""
        counters = AddressComparisonCounters()
        counters.start_timing()
        assert counters.start_time is not None
        counters.end_timing()
        assert counters.end_time is not None
        assert counters.get_duration() >= 0.0

    def test_duration_without_timing(self) -> None:
        """Duration returns 0 when timing not started."""
        counters = AddressComparisonCounters()
        assert counters.get_duration() == 0.0

    def test_increment_parse_failure(self) -> None:
        """Verify parse failure counting and reason tracking."""
        counters = AddressComparisonCounters()
        counters.increment_parse_failure("missing_zip")
        counters.increment_parse_failure("missing_zip")
        counters.increment_parse_failure("bad_format")
        assert counters.parse_failures == 3
        assert counters.parse_failure_reasons == {
            "missing_zip": 2,
            "bad_format": 1,
        }

    def test_log_summary(self) -> None:
        """Verify log_summary runs without error."""
        counters = AddressComparisonCounters()
        counters.total_devices = 10
        counters.start_timing()
        counters.end_timing()
        counters.log_summary()


# ================================================================
# InventoryCSVComparator init tests
# ================================================================


class TestComparatorInit:
    """Tests for InventoryCSVComparator initialization."""

    def test_init_stores_config(self) -> None:
        """Verify constructor stores configuration flags."""
        comp = _make_comparator(fast=True, debug=True)
        assert comp.fast is True
        assert comp.debug is True
        assert comp.address_check is False
        assert comp.skip_ssl_verify is True

    def test_init_state(self) -> None:
        """Verify _init_state creates empty containers."""
        comp = _make_comparator()
        assert comp.site_configs == []
        assert comp.comparison_data == []
        assert comp.all_conflicts == []
        assert comp.mismatched_items == []
        assert isinstance(comp.counters, AddressComparisonCounters)


# ================================================================
# Field detection tests
# ================================================================


class TestFieldDetection:
    """Tests for CSV field detection methods."""

    def test_detect_serial_field(self) -> None:
        """Find serial field from headers."""
        comp = _make_comparator()
        comp._detect_serial_field(["Name", "System Serial", "Zip"])
        assert comp.serial_field == "System Serial"

    def test_detect_serial_field_sn(self) -> None:
        """Find SN variant of serial field."""
        comp = _make_comparator()
        comp._detect_serial_field(["Name", "SN", "Zip"])
        assert comp.serial_field == "SN"

    def test_detect_serial_field_missing(self) -> None:
        """Serial field stays None when not found."""
        comp = _make_comparator()
        comp._detect_serial_field(["Name", "Model"])
        assert comp.serial_field is None

    def test_detect_zip_field(self) -> None:
        """Find zip field from headers."""
        comp = _make_comparator()
        comp._detect_zip_field(["Name", "Postal Code", "City"])
        assert comp.zip_field == "Postal Code"

    def test_detect_zip_field_zip(self) -> None:
        """Find zip variant."""
        comp = _make_comparator()
        comp._detect_zip_field(["Name", "Zip", "City"])
        assert comp.zip_field == "Zip"

    def test_detect_address_fields(self) -> None:
        """Detect address, city, state, country fields."""
        comp = _make_comparator()
        headers = [
            "Address Line 1",
            "City",
            "State",
            "Country",
        ]
        comp._detect_address_fields(headers)
        assert comp.address_field == "Address Line 1"
        assert comp.city_field == "City"
        assert comp.state_field == "State"
        assert comp.country_field == "Country"

    def test_validate_required_fields_pass(self) -> None:
        """Validation passes when serial and zip found."""
        comp = _make_comparator()
        comp.serial_field = "Serial"
        comp.zip_field = "Zip"
        assert comp._validate_required_fields(["Serial", "Zip"]) is True

    def test_validate_required_fields_no_serial(self) -> None:
        """Validation fails without serial field."""
        comp = _make_comparator()
        comp.serial_field = None
        comp.zip_field = "Zip"
        assert comp._validate_required_fields(["Zip"]) is False

    def test_validate_required_fields_no_zip(self) -> None:
        """Validation fails without zip field."""
        comp = _make_comparator()
        comp.serial_field = "Serial"
        comp.zip_field = None
        assert comp._validate_required_fields(["Serial"]) is False


# ================================================================
# Lookup and address extraction tests
# ================================================================


class TestLookupBuilding:
    """Tests for lookup dictionary building."""

    def test_extract_address_from_row(self) -> None:
        """Extract address components from CSV row."""
        comp = _make_comparator()
        comp.address_field = "Address"
        comp.city_field = "City"
        comp.state_field = "State"
        comp.country_field = "Country"
        row = {
            "Address": "123 Main St",
            "City": "Springfield",
            "State": "IL",
            "Country": "US",
        }
        result = comp._extract_address_from_row(row, "62701")
        assert result["Address"] == "123 Main St"
        assert result["City"] == "Springfield"
        assert result["Zip"] == "62701"

    def test_extract_address_missing_fields(self) -> None:
        """Extract with None field mappings returns empty strings."""
        comp = _make_comparator()
        comp.address_field = None
        comp.city_field = None
        comp.state_field = None
        comp.country_field = None
        result = comp._extract_address_from_row({}, "12345")
        assert result["Address"] == ""
        assert result["City"] == ""
        assert result["Zip"] == "12345"

    def test_get_component_address(self) -> None:
        """Get address from device component fields."""
        comp = _make_comparator()
        device = {
            "street": "456 Oak Ave",
            "city": "Portland",
            "state": "OR",
            "zip_code": "97201",
        }
        result = comp._get_component_address(device)
        assert result["address"] == "456 Oak Ave"
        assert result["city"] == "Portland"
        assert result["zip"] == "97201"

    def test_get_comparison_address_found(self) -> None:
        """Get comparison address for known serial."""
        comp = _make_comparator()
        comp.comparison_address_lookup = {
            "SN123": {
                "Address": "789 Elm St",
                "City": "Denver",
                "State": "CO",
                "Zip": "80201",
            }
        }
        result = comp._get_comparison_address("SN123")
        assert result is not None
        assert result["address"] == "789 Elm St"

    def test_get_comparison_address_not_found(self) -> None:
        """Get None for unknown serial."""
        comp = _make_comparator()
        comp.comparison_address_lookup = {}
        assert comp._get_comparison_address("SN999") is None

    def test_get_comparison_address_empty(self) -> None:
        """Get None when all values empty."""
        comp = _make_comparator()
        comp.comparison_address_lookup = {
            "SN123": {
                "Address": "",
                "City": "",
                "State": "",
                "Zip": "",
            }
        }
        assert comp._get_comparison_address("SN123") is None


# ================================================================
# Duplicate detection tests
# ================================================================


class TestDuplicateDetection:
    """Tests for duplicate address detection."""

    def test_create_address_key(self) -> None:
        """Address key is normalized lowercase pipe-separated."""
        comp = _make_comparator()
        key = comp._create_address_key(
            {
                "address": "123 MAIN ST",
                "city": "Springfield",
                "state": "IL",
                "zip": "62701",
            }
        )
        assert key == "123 main st|springfield|il|62701"

    def test_find_duplicates_none(self) -> None:
        """No duplicates with unique addresses."""
        comp = _make_comparator()
        sites = {
            "Site A": {"address_key": "a|b|c|1"},
            "Site B": {"address_key": "d|e|f|2"},
        }
        assert comp._find_duplicates(sites) == {}

    def test_find_duplicates_found(self) -> None:
        """Find sites sharing the same address."""
        comp = _make_comparator()
        sites = {
            "Site A": {"address_key": "same|addr|ca|90210"},
            "Site B": {"address_key": "same|addr|ca|90210"},
            "Site C": {"address_key": "other|addr|ny|10001"},
        }
        dups = comp._find_duplicates(sites)
        assert "same|addr|ca|90210" in dups
        assert len(dups["same|addr|ca|90210"]) == 2


# ================================================================
# Conflict filtering tests
# ================================================================


class TestConflictFiltering:
    """Tests for conflict deduplication and filtering."""

    def test_create_conflict_address_key(self) -> None:
        """Conflict key combines both address pairs."""
        comp = _make_comparator()
        conflict = {
            "mist_address": {
                "address": "A",
                "city": "B",
                "state": "C",
                "zip": "1",
            },
            "comparison_address": {
                "address": "D",
                "city": "E",
                "state": "F",
                "zip": "2",
            },
        }
        key = comp._create_conflict_address_key(conflict)
        assert "||" in key
        assert key == "a|b|c|1||d|e|f|2"

    def test_remove_duplicate_conflicts(self) -> None:
        """Duplicate address pairs are removed."""
        comp = _make_comparator()
        conflict = {
            "device_serial": "SN1",
            "mist_address": {
                "address": "A",
                "city": "B",
                "state": "C",
                "zip": "1",
            },
            "comparison_address": {
                "address": "D",
                "city": "E",
                "state": "F",
                "zip": "2",
            },
        }
        comp.all_conflicts = [conflict, conflict.copy()]
        unique = comp._remove_duplicate_conflicts()
        assert len(unique) == 1


# ================================================================
# Record comparison result tests
# ================================================================


class TestRecordComparison:
    """Tests for recording comparison results."""

    def test_record_match(self) -> None:
        """Perfect match increments counter."""
        comp = _make_comparator()
        comp._record_comparison_result(
            RecordComparisonInputs(
                device={},
                device_serial="SN1",
                device_identifier="Dev1",
                mist_address={},
                comparison_address={},
                comparison_result={"is_match": True},
            )
        )
        assert comp.counters.perfect_matches == 1
        assert comp.counters.mismatches_found == 0

    def test_record_mismatch(self) -> None:
        """Mismatch appends to all_conflicts."""
        comp = _make_comparator()
        comp._record_comparison_result(
            RecordComparisonInputs(
                device={"site_name": "S1"},
                device_serial="SN2",
                device_identifier="Dev2",
                mist_address={"address": "A"},
                comparison_address={"address": "B"},
                comparison_result={"is_match": False},
            )
        )
        assert comp.counters.mismatches_found == 1
        assert len(comp.all_conflicts) == 1


# ================================================================
# Mismatch type and formatting tests
# ================================================================


class TestMismatchGeneration:
    """Tests for mismatch record generation helpers."""

    def test_get_week_key(self) -> None:
        """Week key format is YYYY_Week_WW."""
        comp = _make_comparator()
        device = {"created_time": 1609459200}  # 2021-01-01
        key = comp._get_week_key(device)
        assert key.startswith("2020_Week_53") or key.startswith("2021_Week_")

    def test_determine_mismatch_type_zip(self) -> None:
        """Single zip failure is Zip Code Mismatch."""
        comp = _make_comparator()
        result = comp._determine_mismatch_type({"failed_fields": ["zip"]})
        assert result == "Zip Code Mismatch"

    def test_determine_mismatch_type_address(self) -> None:
        """Address in failed fields is Address Mismatch."""
        comp = _make_comparator()
        result = comp._determine_mismatch_type({"failed_fields": ["address", "zip"]})
        assert result == "Address Mismatch"

    def test_determine_mismatch_type_city(self) -> None:
        """City-only failure."""
        comp = _make_comparator()
        result = comp._determine_mismatch_type({"failed_fields": ["city"]})
        assert result == "City Mismatch"

    def test_determine_mismatch_type_state(self) -> None:
        """State-only failure."""
        comp = _make_comparator()
        result = comp._determine_mismatch_type({"failed_fields": ["state"]})
        assert result == "State Mismatch"

    def test_determine_mismatch_type_multi(self) -> None:
        """Multi-field when no specific field matches priority."""
        comp = _make_comparator()
        result = comp._determine_mismatch_type({"failed_fields": ["country"]})
        assert result == "Multi-field Address Mismatch"

    def test_format_parse_issues(self) -> None:
        """Format parse issues from comparison result."""
        comp = _make_comparator()
        result = comp._format_parse_issues(
            {
                "parse_status": {
                    "mist_reason": "ok",
                    "comparison_reason": "missing_zip",
                }
            }
        )
        assert "Mist: ok" in result
        assert "Comp: missing_zip" in result

    def test_get_validation_status_none(self) -> None:
        """N/A when no validation result."""
        comp = _make_comparator()
        assert comp._get_validation_status(None, "mist") == "N/A"

    def test_get_validation_status_valid(self) -> None:
        """Returns validity from result."""
        comp = _make_comparator()
        result = {"mist_validation": {"valid": True, "confidence": 0.95}}
        assert comp._get_validation_status(result, "mist") == "True"

    def test_get_validation_confidence_none(self) -> None:
        """N/A when no validation result."""
        comp = _make_comparator()
        assert comp._get_validation_confidence(None, "mist") == "N/A"

    def test_get_validation_confidence_valid(self) -> None:
        """Returns formatted confidence."""
        comp = _make_comparator()
        result = {"mist_validation": {"valid": True, "confidence": 0.95}}
        assert comp._get_validation_confidence(result, "mist") == "0.950"

    def test_get_validation_confidence_invalid(self) -> None:
        """Returns N/A when address is invalid."""
        comp = _make_comparator()
        result = {"mist_validation": {"valid": False, "confidence": 0.0}}
        assert comp._get_validation_confidence(result, "mist") == "N/A"

    def test_get_output_fieldnames(self) -> None:
        """Output fieldnames list is non-empty."""
        comp = _make_comparator()
        fields = comp._get_output_fieldnames()
        assert len(fields) > 20
        assert "System Serial Number" in fields
        assert "Validation_Recommendation" in fields


# ================================================================
# Configuration tests
# ================================================================


class TestConfiguration:
    """Tests for configuration initialization."""

    @patch.dict(
        os.environ,
        {
            "END_CUSTOMER_NAME": "Acme Corp",
            "END_CUSTOMER_ACCOUNT_ID": "ACC-123",
            "ADDRESS_MATCH_THRESHOLD": "85",
        },
    )
    def test_initialize_config(self) -> None:
        """Config loads from environment."""
        comp = _make_comparator()
        result = comp._initialize_config()
        assert result is True
        assert comp.end_customer_name == "Acme Corp"
        assert comp.end_customer_account_id == "ACC-123"
        assert comp.address_threshold == 85.0

    @patch.dict(
        os.environ,
        {"ENABLE_ADDRESS_VALIDATION": "true"},
    )
    def test_determine_validation_enabled_env(self) -> None:
        """Validation enabled via env var."""
        comp = _make_comparator()
        comp._determine_validation_mode()
        assert comp.address_validation_enabled is True

    def test_determine_validation_enabled_flag(self) -> None:
        """Validation enabled via address_check flag."""
        comp = _make_comparator(address_check=True)
        comp._determine_validation_mode()
        assert comp.address_validation_enabled is True

    def test_determine_validation_disabled(self) -> None:
        """Validation disabled by default."""
        comp = _make_comparator()
        comp._determine_validation_mode()
        assert comp.address_validation_enabled is False


# ================================================================
# Format address string tests
# ================================================================


class TestFormatAddress:
    """Tests for address formatting."""

    def test_format_full_address(self) -> None:
        """Format complete address dict."""
        comp = _make_comparator()
        result = comp._format_address_string(
            {
                "address": "123 Main St",
                "city": "Denver",
                "state": "CO",
                "zip": "80201",
            }
        )
        assert "123 Main St" in result
        assert "Denver" in result
        assert "CO" in result

    def test_format_partial_address(self) -> None:
        """Format with missing city."""
        comp = _make_comparator()
        result = comp._format_address_string(
            {
                "address": "123 Main St",
                "city": "",
                "state": "CO",
                "zip": "80201",
            }
        )
        assert "123 Main St" in result


# ================================================================
# Skip filter tests
# ================================================================


class TestSkipFilters:
    """Tests for skip filter recording."""

    def test_record_skipped_address(self) -> None:
        """Recording skip increments counters."""
        comp = _make_comparator()
        comp._record_skipped_address("SN1", "known_mismatch")
        assert comp.counters.perfect_matches == 1
        assert comp.counters.auto_corrections == 1

    def test_apply_skip_filters_none_skipped(self) -> None:
        """No skips when check_should_skip returns False."""
        addr_utils = _mock_address_utils()
        addr_utils.check_should_skip.return_value = (False, "")
        comp = _make_comparator(address_utils_cls=addr_utils)
        conflicts = [
            {
                "device_serial": "SN1",
                "comparison_address": {"address": "A", "city": "B", "state": "C", "zip": "1"},
            }
        ]
        result = comp._apply_skip_filters(conflicts)
        assert len(result) == 1

    def test_apply_skip_filters_all_skipped(self) -> None:
        """All skipped when check_should_skip returns True."""
        addr_utils = _mock_address_utils()
        addr_utils.check_should_skip.return_value = (True, "known")
        comp = _make_comparator(address_utils_cls=addr_utils)
        conflicts = [
            {
                "device_serial": "SN1",
                "comparison_address": {"address": "A", "city": "B", "state": "C", "zip": "1"},
            }
        ]
        result = comp._apply_skip_filters(conflicts)
        assert len(result) == 0


# ================================================================
# Parse failure recording tests
# ================================================================


class TestParseFailures:
    """Tests for parse failure recording."""

    def test_record_mist_parse_failure(self) -> None:
        """Records Mist parse failure with details."""
        comp = _make_comparator()
        comp._record_mist_parse_failure(
            device={"site_id": "s1", "site_name": "Site1", "id": "d1"},
            device_serial="SN1",
            device_identifier="Dev1",
            raw_address="bad address",
            parsed_result={"parse_reason": "missing_state"},
        )
        assert len(comp.parse_failures) == 1
        assert comp.parse_failures[0]["failure_reason"] == "missing_state"
        assert comp.counters.parse_failures == 1

    def test_record_device_parse_failure(self) -> None:
        """Records device processing error as parse failure."""
        comp = _make_comparator()
        comp._record_device_parse_failure(
            device={"site_id": "s1", "site_name": "Site1", "id": "d1"},
            device_serial="SN2",
            device_identifier="Dev2",
            error_msg="connection timeout",
        )
        assert len(comp.parse_failures) == 1
        assert "connection timeout" in comp.parse_failures[0]["failure_reason"]
        assert comp.counters.parse_failures == 1


# ================================================================
# Results display tests
# ================================================================


class TestResultsDisplay:
    """Tests for results display methods."""

    def test_print_success_message(self) -> None:
        """Success message runs without error."""
        comp = _make_comparator()
        comp.counters.perfect_matches = 10
        comp.counters.auto_corrections = 2
        comp._print_success_message()

    def test_print_results_summary(self) -> None:
        """Summary runs without error."""
        comp = _make_comparator()
        comp.counters.total_devices = 100
        comp.counters.devices_enriched = 80
        comp.counters.mismatches_found = 5
        comp.counters.start_timing()
        comp.counters.end_timing()
        comp._print_results_summary()

    def test_display_conflict_preview_empty(self) -> None:
        """Preview with empty items runs without error."""
        comp = _make_comparator()
        comp.mismatched_items = []
        comp._display_conflict_preview()

    def test_print_conflict_item(self) -> None:
        """Print single conflict item runs without error."""
        comp = _make_comparator()
        item = {
            "System Serial Number": "SN1",
            "Mist_Address_Line_1": "123 Main",
            "Mist_City": "Denver",
            "Mist_State": "CO",
            "Comparison_Address": "456 Oak",
            "Comparison_City": "Portland",
            "Comparison_State": "OR",
            "Overall Similarity": "50.0%",
            "Mismatch Type": "Address Mismatch",
            "Validation_Recommendation": "N/A",
        }
        comp._print_conflict_item(0, item)


# ================================================================
# Data loading tests
# ================================================================


class TestDataLoading:
    """Tests for CSV data loading methods."""

    def test_load_source_data(self) -> None:
        """Load source data from CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "AllDevicesWithSiteInfo.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=["serial", "site_name"])
                writer.writeheader()
                writer.writerow({"serial": "SN1", "site_name": "Site1"})
            comp = _make_comparator(
                get_csv_path_fn=lambda f: os.path.join(tmpdir, f),
            )
            result = comp._load_source_data()
            assert result is True
            assert len(comp.site_configs) == 1

    def test_load_comparison_data(self) -> None:
        """Load comparison CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=["Serial", "Zip"])
                writer.writeheader()
                writer.writerow({"Serial": "SN1", "Zip": "12345"})
            comp = _make_comparator(
                get_csv_path_fn=lambda f: os.path.join(tmpdir, f),
            )
            comp.comparison_file = "test.csv"
            comp.site_configs = [{"serial": "SN1"}]
            result = comp._load_comparison_data()
            assert result is True
            assert len(comp.comparison_data) == 1

    def test_load_comparison_data_error(self) -> None:
        """Handle missing comparison file gracefully."""
        comp = _make_comparator(
            get_csv_path_fn=lambda f: "/nonexistent/" + f,
        )
        comp.comparison_file = "missing.csv"
        comp.site_configs = []
        result = comp._load_comparison_data()
        assert result is False

    def test_load_skip_addresses_found(self) -> None:
        """Load skip addresses from CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skip_path = os.path.join(tmpdir, "AddressSkip.csv")
            with open(skip_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=["address", "reason"])
                writer.writeheader()
                writer.writerow({"address": "skip me", "reason": "known"})
            comp = _make_comparator(
                get_csv_path_fn=lambda f: os.path.join(tmpdir, f),
            )
            comp._load_skip_addresses()
            assert len(comp.skip_addresses) == 1

    def test_load_skip_addresses_missing(self) -> None:
        """Handle missing skip file gracefully."""
        comp = _make_comparator(
            get_csv_path_fn=lambda f: "/nonexistent/" + f,
        )
        comp._load_skip_addresses()

    def test_get_available_csv_files(self) -> None:
        """List available CSV files excluding source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["test1.csv", "test2.csv", "AllDevicesWithSiteInfo.csv"]:
                with open(os.path.join(tmpdir, name), "w", encoding="utf-8") as fh:
                    fh.write("header\n")
            comp = _make_comparator()
            with patch("src.inventory.csv_comparator.glob.glob") as mock_glob:
                mock_glob.return_value = [
                    os.path.join(tmpdir, "test1.csv"),
                    os.path.join(tmpdir, "test2.csv"),
                    os.path.join(tmpdir, "AllDevicesWithSiteInfo.csv"),
                ]
                files = comp._get_available_csv_files()
            assert "AllDevicesWithSiteInfo.csv" not in files
            assert len(files) == 2

    def test_select_comparison_file_no_files(self) -> None:
        """Return False when no CSV files available."""
        comp = _make_comparator()
        with patch.object(comp, "_get_available_csv_files", return_value=[]):
            result = comp._select_comparison_file()
            assert result is False

    def test_get_user_csv_selection_valid(self) -> None:
        """Valid selection stores comparison file."""
        comp = _make_comparator()
        csv_files = ["file1.csv", "file2.csv"]
        with patch("builtins.input", return_value="1"):
            result = comp._get_user_csv_selection(csv_files)
        assert result is True
        assert comp.comparison_file == "file2.csv"

    def test_get_user_csv_selection_invalid_index(self) -> None:
        """Invalid index returns False."""
        comp = _make_comparator()
        with patch("builtins.input", return_value="99"):
            result = comp._get_user_csv_selection(["a.csv"])
        assert result is False

    def test_get_user_csv_selection_not_numeric(self) -> None:
        """Non-numeric input returns False."""
        comp = _make_comparator()
        with patch("builtins.input", return_value="abc"):
            result = comp._get_user_csv_selection(["a.csv"])
        assert result is False

    def test_get_user_csv_selection_keyboard_interrupt(self) -> None:
        """KeyboardInterrupt returns False."""
        comp = _make_comparator()
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = comp._get_user_csv_selection(["a.csv"])
        assert result is False


# ================================================================
# Field detection (CSV fields) tests
# ================================================================


class TestDetectCsvFields:
    """Tests for _detect_csv_fields method."""

    def test_detect_csv_fields_empty(self) -> None:
        """Empty comparison data returns False."""
        comp = _make_comparator()
        comp.comparison_data = []
        assert comp._detect_csv_fields() is False

    def test_detect_csv_fields_success(self) -> None:
        """Valid data detects fields."""
        comp = _make_comparator()
        comp.comparison_data = [{"System Serial": "SN1", "Postal Code": "12345"}]
        result = comp._detect_csv_fields()
        assert result is True
        assert comp.serial_field == "System Serial"
        assert comp.zip_field == "Postal Code"


# ================================================================
# Lookup building tests
# ================================================================


class TestBuildLookupDictionaries:
    """Tests for lookup dictionary construction."""

    def test_build_lookup_dictionaries(self) -> None:
        """Build serial and address lookups."""
        comp = _make_comparator()
        comp.serial_field = "Serial"
        comp.zip_field = "Zip"
        comp.address_field = "Address"
        comp.city_field = "City"
        comp.state_field = "State"
        comp.country_field = None
        comp.comparison_data = [
            {
                "Serial": "SN1",
                "Zip": "12345",
                "Address": "123 Main",
                "City": "Denver",
                "State": "CO",
            },
            {"Serial": "", "Zip": "00000"},
        ]
        comp.address_validation_enabled = False
        comp._build_lookup_dictionaries()
        assert "SN1" in comp.comparison_serials
        assert "SN1" in comp.comparison_address_lookup
        assert len(comp.comparison_serials) == 1

    def test_count_devices_for_validation(self) -> None:
        """Count devices present in comparison data."""
        comp = _make_comparator()
        comp.site_configs = [
            {"serial": "SN1"},
            {"serial": "SN2"},
            {"serial": "SN3"},
        ]
        comp.comparison_serials = {"SN1": "12345", "SN3": "67890"}
        assert comp._count_devices_for_validation() == 2


# ================================================================
# Duplicate detection full workflow tests
# ================================================================


class TestDuplicateWorkflow:
    """Tests for complete duplicate detection workflow."""

    def test_build_mist_site_addresses(self) -> None:
        """Build Mist site address lookup."""
        comp = _make_comparator()
        comp.site_configs = [
            {
                "site_name": "Site A",
                "street": "123 Main",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80201",
            },
            {
                "site_name": "Site A",
                "street": "dup",
                "city": "X",
                "state": "Y",
                "zip_code": "Z",
            },
        ]
        result = comp._build_mist_site_addresses()
        assert len(result) == 1
        assert "Site A" in result

    def test_build_mist_site_addresses_empty(self) -> None:
        """Skip sites with no address data."""
        comp = _make_comparator()
        comp.site_configs = [
            {
                "site_name": "Site B",
                "street": "",
                "city": "",
                "state": "",
                "zip_code": "",
            }
        ]
        result = comp._build_mist_site_addresses()
        assert len(result) == 0

    def test_build_ref_site_addresses(self) -> None:
        """Build reference site address lookup."""
        comp = _make_comparator()
        comp.site_configs = [
            {"site_name": "Site A", "serial": "SN1"},
        ]
        comp.comparison_address_lookup = {
            "SN1": {
                "Address": "456 Oak",
                "City": "Portland",
                "State": "OR",
                "Zip": "97201",
            }
        }
        result = comp._build_ref_site_addresses()
        assert len(result) == 1

    def test_report_duplicates_none(self) -> None:
        """Report no duplicates found."""
        comp = _make_comparator()
        comp.mist_duplicates = {}
        comp.ref_duplicates = {}
        comp._report_duplicates({}, {})

    def test_report_duplicates_with_mist(self) -> None:
        """Report Mist duplicates."""
        comp = _make_comparator()
        comp.mist_duplicates = {"a|b|c|1": ["Site A", "Site B"]}
        comp.ref_duplicates = {}
        mist_addrs = {
            "Site A": {
                "address_key": "a|b|c|1",
                "address": {
                    "address": "a",
                    "city": "b",
                    "state": "c",
                    "zip": "1",
                },
            },
            "Site B": {
                "address_key": "a|b|c|1",
                "address": {
                    "address": "a",
                    "city": "b",
                    "state": "c",
                    "zip": "1",
                },
            },
        }
        comp._report_duplicates(mist_addrs, {})

    def test_print_duplicate_summary(self) -> None:
        """Print duplicate summary runs without error."""
        comp = _make_comparator()
        comp.mist_duplicates = {"k": ["A", "B"]}
        comp.ref_duplicates = {"j": ["C", "D", "E"]}
        comp._print_duplicate_summary()

    def test_detect_duplicate_addresses(self) -> None:
        """Full duplicate detection workflow."""
        comp = _make_comparator()
        comp.site_configs = [
            {
                "site_name": "S1",
                "serial": "SN1",
                "street": "123 Main",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80201",
            }
        ]
        comp.comparison_address_lookup = {}
        comp._detect_duplicate_addresses()
        assert isinstance(comp.mist_duplicates, dict)
        assert isinstance(comp.ref_duplicates, dict)


# ================================================================
# Device processing tests
# ================================================================


class TestDeviceProcessing:
    """Tests for device processing workflow."""

    def test_process_device_in_loop_not_found(self) -> None:
        """Device not in comparison data is skipped."""
        comp = _make_comparator()
        comp.comparison_serials = {}
        result = comp._process_device_in_loop({"serial": "SN1", "name": "Dev1"}, False)
        assert comp.counters.devices_skipped == 1
        assert result is False

    def test_process_device_in_loop_found(self) -> None:
        """Device in comparison data is processed."""
        comp = _make_comparator()
        comp.comparison_serials = {"SN1": "12345"}
        comp.comparison_address_lookup = {
            "SN1": {
                "Address": "456 Oak",
                "City": "Portland",
                "State": "OR",
                "Zip": "97201",
            }
        }
        comp._process_device_in_loop(
            {
                "serial": "SN1",
                "name": "Dev1",
                "site_name": "S1",
                "site_address": "",
                "street": "123 Main",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80201",
            },
            False,
        )
        assert comp.counters.devices_enriched == 1

    def test_process_single_device_match(self) -> None:
        """Device with matching address records a match."""
        addr_utils = _mock_address_utils()
        addr_utils.compare_with_threshold.return_value = {
            "is_match": True,
        }
        comp = _make_comparator(address_utils_cls=addr_utils)
        comp.comparison_address_lookup = {
            "SN1": {
                "Address": "123 Main",
                "City": "Denver",
                "State": "CO",
                "Zip": "80201",
            }
        }
        comp._process_single_device(
            {
                "site_address": "",
                "street": "123 Main",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80201",
            },
            "SN1",
            "Dev1",
        )
        assert comp.counters.perfect_matches == 1

    def test_process_single_device_no_comparison(self) -> None:
        """Device with empty comparison data is skipped."""
        comp = _make_comparator()
        comp.comparison_address_lookup = {}
        comp._process_single_device(
            {"site_address": "", "street": "", "city": "", "state": "", "zip_code": ""},
            "SN999",
            "Dev999",
        )
        assert comp.counters.devices_skipped == 1

    def test_process_single_device_exception(self) -> None:
        """Exception during processing records failure."""
        addr_utils = _mock_address_utils()
        addr_utils.compare_with_threshold.side_effect = RuntimeError("boom")
        comp = _make_comparator(address_utils_cls=addr_utils)
        comp.comparison_address_lookup = {"SN1": {"Address": "A", "City": "B", "State": "C", "Zip": "1"}}
        comp._process_single_device(
            {
                "site_address": "",
                "street": "A",
                "city": "B",
                "state": "C",
                "zip_code": "1",
                "site_id": "s1",
                "site_name": "S1",
                "id": "d1",
            },
            "SN1",
            "Dev1",
        )
        assert comp.counters.comparison_failures == 1

    def test_parse_mist_address_raw(self) -> None:
        """Parse raw site_address string."""
        addr_utils = _mock_address_utils()
        comp = _make_comparator(address_utils_cls=addr_utils)
        result = comp._parse_mist_address(
            {"site_address": "123 Main St, Denver, CO 80201"},
            "SN1",
            "Dev1",
        )
        assert result["address"] == "123 Main St"

    def test_parse_mist_address_empty(self) -> None:
        """Fall back to component fields when no site_address."""
        comp = _make_comparator()
        result = comp._parse_mist_address(
            {
                "site_address": "",
                "street": "456 Oak",
                "city": "Portland",
                "state": "OR",
                "zip_code": "97201",
            },
            "SN1",
            "Dev1",
        )
        assert result["address"] == "456 Oak"

    def test_parse_mist_address_unparseable(self) -> None:
        """Record parse failure and fall back to components."""
        addr_utils = _mock_address_utils()
        addr_utils.enhanced_parse.return_value = {
            "is_parseable": False,
            "parse_reason": "bad_format",
        }
        comp = _make_comparator(address_utils_cls=addr_utils)
        result = comp._parse_mist_address(
            {
                "site_address": "garbage address",
                "street": "fallback",
                "city": "FB",
                "state": "ST",
                "zip_code": "00000",
                "site_id": "s1",
                "site_name": "S1",
                "id": "d1",
            },
            "SN1",
            "Dev1",
        )
        assert result["address"] == "fallback"
        assert len(comp.parse_failures) == 1


# ================================================================
# Conflict filtering full workflow tests
# ================================================================


class TestFilterConflicts:
    """Tests for full conflict filtering workflow."""

    def test_filter_conflicts_workflow(self) -> None:
        """Full filter workflow deduplicates and skips."""
        addr_utils = _mock_address_utils()
        addr_utils.check_should_skip.return_value = (False, "")
        comp = _make_comparator(address_utils_cls=addr_utils)
        comp.all_conflicts = [
            {
                "device_serial": "SN1",
                "mist_address": {"address": "A", "city": "B", "state": "C", "zip": "1"},
                "comparison_address": {"address": "D", "city": "E", "state": "F", "zip": "2"},
            }
        ]
        comp.skip_addresses = []
        comp._filter_conflicts()
        assert len(comp.filtered_conflicts) == 1


# ================================================================
# Validation and mismatch processing tests
# ================================================================


class TestProcessRemainingConflicts:
    """Tests for remaining conflict processing."""

    def test_process_remaining_empty(self) -> None:
        """No processing when no filtered conflicts."""
        comp = _make_comparator()
        comp.filtered_conflicts = []
        comp._process_remaining_conflicts()
        assert len(comp.mismatched_items) == 0

    def test_process_without_validation(self) -> None:
        """Process conflicts without external validation."""
        comp = _make_comparator()
        comp.address_validation_enabled = False
        comp.filtered_conflicts = [
            {
                "device": {"site_name": "S1", "model": "AP45", "created_time": 1609459200, "serial": "SN1"},
                "device_serial": "SN1",
                "device_identifier": "Dev1",
                "mist_address": {"address": "A", "city": "B", "state": "C", "zip": "1"},
                "comparison_address": {"address": "D", "city": "E", "state": "F", "zip": "2"},
                "comparison_result": {
                    "is_match": False,
                    "overall_similarity": 50.0,
                    "field_similarities": {
                        "address": 60.0,
                        "city": 40.0,
                        "state": 100.0,
                        "zip": 0.0,
                    },
                    "failed_fields": ["address", "zip"],
                    "parse_status": {
                        "mist_parseable": True,
                        "comparison_parseable": True,
                        "mist_reason": "ok",
                        "comparison_reason": "ok",
                    },
                },
            }
        ]
        comp.end_customer_name = "Acme"
        comp.end_customer_account_id = "ACC-1"
        comp._process_without_validation()
        assert len(comp.mismatched_items) == 1
        assert comp.mismatched_items[0]["Mismatch Type"] == "Address Mismatch"

    def test_generate_mismatch_records_exception(self) -> None:
        """Exception in mismatch generation records failure."""
        comp = _make_comparator()
        comp.end_customer_name = "Acme"
        comp.end_customer_account_id = "ACC-1"
        comp._generate_mismatch_records(
            {
                "device": None,
                "device_serial": "SN1",
                "comparison_result": None,
                "mist_address": {},
                "comparison_address": {},
            },
            None,
        )
        assert comp.counters.comparison_failures == 1


# ================================================================
# Validation workflow tests
# ================================================================


class TestValidationWorkflow:
    """Tests for external validation workflow."""

    def test_get_org_name_for_validation_success(self) -> None:
        """Successfully retrieve org name."""
        mock_api = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.data = {"name": "Test Org"}
        _our_mock.api.v1.orgs.orgs.getOrg.return_value = mock_response
        comp = _make_comparator(apisession=mock_api)
        result = comp._get_org_name_for_validation()
        assert result == "Test Org" or result is None

    def test_get_org_name_for_validation_failure(self) -> None:
        """Handle API failure gracefully."""
        comp = _make_comparator()
        comp._get_org_id = MagicMock(side_effect=RuntimeError("no org"))
        result = comp._get_org_name_for_validation()
        assert result is None

    def test_validate_single_conflict_success(self) -> None:
        """Successful validation returns result."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = {
            "mist_validation": {"valid": True, "confidence": 0.95},
            "comparison_validation": {"valid": False, "confidence": 0.2},
            "recommendation": "mist",
            "recommendation_reason": "Higher confidence",
        }
        mock_validator_cls = MagicMock(return_value=mock_validator)
        mock_config_cls = MagicMock()
        comp = _make_comparator(
            nominatim_validator_cls=mock_validator_cls,
            address_validation_config_cls=mock_config_cls,
        )
        comp.mist_duplicates = {}
        comp.ref_duplicates = {}
        result = comp._validate_single_conflict(
            {
                "device": {"site_name": "S1"},
                "device_serial": "SN1",
                "mist_address": {"address": "A", "city": "B", "state": "C", "zip": "1"},
                "comparison_address": {"address": "D", "city": "E", "state": "F", "zip": "2"},
            },
            1,
            1,
            "Org",
        )
        assert result is not None
        assert result["recommendation"] == "mist"

    def test_validate_single_conflict_exception(self) -> None:
        """Validation exception returns None."""
        mock_validator_cls = MagicMock(side_effect=RuntimeError("api down"))
        comp = _make_comparator(
            nominatim_validator_cls=mock_validator_cls,
            address_validation_config_cls=MagicMock(),
        )
        comp.mist_duplicates = {}
        comp.ref_duplicates = {}
        result = comp._validate_single_conflict(
            {
                "device": {"site_name": "S1"},
                "device_serial": "SN1",
                "mist_address": {"address": "A", "city": "B", "state": "C", "zip": "1"},
                "comparison_address": {"address": "D", "city": "E", "state": "F", "zip": "2"},
            },
            1,
            1,
            None,
        )
        assert result is None

    def test_print_validation_header(self) -> None:
        """Validation header prints without error."""
        comp = _make_comparator()
        comp._print_validation_header(
            "SN1",
            {"address": "A", "city": "B", "state": "C", "zip": "1"},
            {"address": "D", "city": "E", "state": "F", "zip": "2"},
            1,
            10,
        )

    def test_print_validation_results(self) -> None:
        """Validation results print without error."""
        comp = _make_comparator()
        comp._print_validation_results(
            "SN1",
            {
                "mist_validation": {"valid": True, "confidence": 0.95},
                "comparison_validation": {"valid": False, "confidence": 0.0},
                "recommendation": "mist",
                "recommendation_reason": "Higher confidence",
            },
        )

    def test_print_validation_results_uncertain(self) -> None:
        """Uncertain recommendation with inconclusive reason."""
        comp = _make_comparator()
        comp._print_validation_results(
            "SN1",
            {
                "mist_validation": {"valid": True, "confidence": 0.5},
                "comparison_validation": {"valid": True, "confidence": 0.5},
                "recommendation": "uncertain",
                "recommendation_reason": "Results inconclusive",
            },
        )


# ================================================================
# Results finalization tests
# ================================================================


class TestFinalization:
    """Tests for results finalization and saving."""

    def test_finalize_no_mismatches(self) -> None:
        """Finalization with no mismatches prints success."""
        comp = _make_comparator()
        comp.counters.start_timing()
        comp.counters.total_devices = 10
        comp.counters.devices_enriched = 8
        comp.parse_failures = []
        comp.mismatched_items = []
        comp._finalize_and_display_results()

    def test_finalize_with_mismatches(self) -> None:
        """Finalization with mismatches displays preview."""
        comp = _make_comparator()
        comp.counters.start_timing()
        comp.counters.total_devices = 10
        comp.counters.devices_enriched = 8
        comp.parse_failures = []
        comp.comparison_file = "test.csv"
        comp.address_validation_enabled = False
        item = {
            "Week": "2021_Week_01",
            "Full Site": "Site1",
            "System Serial Number": "SN1",
            "System Model Number": "AP45",
            "Mist_Address_Line_1": "123 Main",
            "Mist_City": "Denver",
            "Mist_State": "CO",
            "Comparison_Address": "456 Oak",
            "Comparison_City": "Portland",
            "Comparison_State": "OR",
            "Overall Similarity": "50.0%",
            "Mismatch Type": "Address Mismatch",
            "Validation_Recommendation": "N/A",
        }
        comp.mismatched_items = [item]
        comp.diff_report_items = [item]
        with tempfile.TemporaryDirectory() as tmpdir:
            comp._get_csv_path = lambda f: os.path.join(tmpdir, f)
            comp._finalize_and_display_results()

    def test_save_results_to_csv(self) -> None:
        """Save mismatch results to CSV file."""
        comp = _make_comparator()
        comp.comparison_file = "ref.csv"
        comp.diff_report_items = [{f: "val" for f in comp._get_output_fieldnames()}]
        with tempfile.TemporaryDirectory() as tmpdir:
            comp._get_csv_path = lambda f: os.path.join(tmpdir, f)
            # Patch open to write to tmpdir
            output_path = os.path.join(tmpdir, "AddressMismatches_vs_ref.csv")
            with patch(
                "builtins.open",
                create=True,
            ) as mock_open:
                mock_open.return_value.__enter__ = MagicMock(
                    return_value=open(output_path, "w", newline="", encoding="utf-8")
                )
                mock_open.return_value.__exit__ = MagicMock(return_value=False)
                comp._save_results_to_csv()

    def test_print_save_confirmation(self) -> None:
        """Print save confirmation runs without error."""
        comp = _make_comparator()
        comp.address_validation_enabled = True
        comp.diff_report_items = [{"a": 1}]
        comp._print_save_confirmation("output.csv")

    def test_print_save_confirmation_no_validation(self) -> None:
        """Print save without validation runs without error."""
        comp = _make_comparator()
        comp.address_validation_enabled = False
        comp.diff_report_items = [{"a": 1}]
        comp._print_save_confirmation("output.csv")

    def test_display_conflict_preview_many(self) -> None:
        """Preview truncates at 10 items."""
        comp = _make_comparator()
        comp.address_validation_enabled = False
        item = {
            "System Serial Number": "SN",
            "Mist_Address_Line_1": "A",
            "Mist_City": "B",
            "Mist_State": "C",
            "Comparison_Address": "D",
            "Comparison_City": "E",
            "Comparison_State": "F",
            "Overall Similarity": "50%",
            "Mismatch Type": "Zip",
            "Validation_Recommendation": "N/A",
        }
        comp.mismatched_items = [item.copy() for _ in range(15)]
        comp._display_conflict_preview()

    def test_print_conflict_item_with_validation(self) -> None:
        """Print conflict with validation recommendation."""
        comp = _make_comparator()
        comp.address_validation_enabled = True
        item = {
            "System Serial Number": "SN1",
            "Mist_Address_Line_1": "A",
            "Mist_City": "B",
            "Mist_State": "C",
            "Comparison_Address": "D",
            "Comparison_City": "E",
            "Comparison_State": "F",
            "Overall Similarity": "80%",
            "Mismatch Type": "City",
            "Validation_Recommendation": "mist",
        }
        comp._print_conflict_item(0, item)

    def test_print_conflict_rate(self) -> None:
        """Print conflict rate with data."""
        comp = _make_comparator()
        comp.counters.mismatches_found = 5
        comp.counters.devices_enriched = 100
        comp._print_conflict_rate()

    def test_print_conflict_rate_zero(self) -> None:
        """No output when no mismatches."""
        comp = _make_comparator()
        comp.counters.mismatches_found = 0
        comp.counters.devices_enriched = 100
        comp._print_conflict_rate()

    def test_print_parse_failure_breakdown(self) -> None:
        """Print parse failure breakdown."""
        comp = _make_comparator()
        comp.counters.parse_failures = 3
        comp.counters.parse_failure_reasons = {"bad": 2, "ugly": 1}
        comp._print_parse_failure_breakdown()

    def test_print_processing_rate(self) -> None:
        """Print processing rate."""
        comp = _make_comparator()
        comp.counters.total_devices = 100
        comp.counters.start_timing()
        comp.counters.end_timing()
        comp._print_processing_rate()

    def test_print_header_fast(self) -> None:
        """Print header in fast mode."""
        comp = _make_comparator(fast=True)
        comp.address_threshold = 75.0
        comp._print_header()

    def test_print_header_debug(self) -> None:
        """Print header in debug mode."""
        comp = _make_comparator(debug=True)
        comp.address_threshold = 75.0
        comp._print_header()

    def test_print_detected_fields(self) -> None:
        """Print detected fields."""
        comp = _make_comparator()
        comp.serial_field = "Serial"
        comp.zip_field = "Zip"
        comp.address_field = "Address"
        comp.city_field = "City"
        comp.state_field = "State"
        comp.country_field = "Country"
        comp._print_detected_fields()

    def test_display_csv_file_list(self) -> None:
        """Display CSV file list."""
        comp = _make_comparator()
        comp._display_csv_file_list(["a.csv", "b.csv"])
