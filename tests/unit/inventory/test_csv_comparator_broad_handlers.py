"""Tests for the narrowed CSV comparator handlers from issue #2750."""

from __future__ import annotations  # WHY: keep annotations lazy for the test module.

from unittest.mock import MagicMock  # WHY: inject collaborator failures without live files or network.

import pytest  # WHY: assert that unexpected exceptions now propagate.
import requests  # WHY: model expected connection, timeout, and HTTP failures.

from src.inventory.csv_comparator import (  # WHY: build the comparator with real dataclasses.
    ComparatorDependencies,
    ComparatorFlags,
    InventoryCSVComparator,
)


def _make_comparator(**overrides: object) -> InventoryCSVComparator:
    """Create a comparator with default mocked dependencies."""
    flags = ComparatorFlags(  # WHY: default flags disable external validation and fast mode.
        fast=False,
        address_check=False,
        debug=False,
        skip_ssl_verify=True,
    )
    deps = ComparatorDependencies(  # WHY: each collaborator stays local to this unit test.
        apisession=MagicMock(),
        get_csv_path_fn=overrides.get("get_csv_path_fn", lambda filename: f"data/{filename}"),
        check_and_generate_csv_fn=MagicMock(),
        create_parse_failures_csv_fn=MagicMock(),
        devices_with_site_info_fn=MagicMock(return_value=[]),
        get_org_id_fn=MagicMock(return_value="test-org-id"),
        get_device_identifier_fn=lambda device, **_kwargs: device.get("name", device.get("serial", "unknown")),
        address_utils_cls=MagicMock(),
        nominatim_validator_cls=MagicMock,
        address_validation_config_cls=MagicMock,
    )
    return InventoryCSVComparator(flags=flags, deps=deps)  # WHY: return the real unit under test.


class TestNarrowedCsvComparatorExceptions:
    """Prove narrowed CSV comparator handlers expose unexpected faults."""

    def test_load_comparison_data_unexpected_error_propagates(self) -> None:
        """A path resolver coding fault must not look like a missing comparison file."""
        comp = _make_comparator(get_csv_path_fn=MagicMock(side_effect=TypeError("bad path resolver")))
        comp.comparison_file = "comparison.csv"  # Set the selected file before the load call.
        with pytest.raises(TypeError, match="bad path resolver"):
            comp._load_comparison_data()  # The narrowed handler must not swallow TypeError.

    def test_load_skip_addresses_unexpected_error_propagates(self) -> None:
        """A path resolver coding fault must not look like an optional skip-list failure."""
        comp = _make_comparator(get_csv_path_fn=MagicMock(side_effect=TypeError("bad skip path")))
        with pytest.raises(TypeError, match="bad skip path"):
            comp._load_skip_addresses()  # The narrowed handler must not swallow TypeError.

    def test_get_org_name_unexpected_error_propagates(self) -> None:
        """A resolver coding fault must not look like a missing optional organization hint."""
        comp = _make_comparator()  # Build the comparator with default injected dependencies.
        comp._get_org_id = MagicMock(side_effect=ValueError("bad org resolver"))  # Model an unexpected fault.
        with pytest.raises(ValueError, match="bad org resolver"):
            comp._get_org_name_for_validation()  # The narrowed handler must not swallow ValueError.

    def test_kept_broad_device_error_logs_exception_type(self, caplog: pytest.LogCaptureFixture) -> None:
        """The kept-broad per-device handler must log the exception type."""
        comp = _make_comparator()  # Build the comparator with default injected dependencies.
        comp.comparison_serials = {"SN1": "12345"}  # Force the device through comparison processing.
        comp._compare_and_record = MagicMock(side_effect=RuntimeError("bad row"))  # Model one bad device row.
        with caplog.at_level("WARNING"):
            comp._process_single_device({"serial": "SN1", "site_address": "1 Main"}, "SN1", "AP-1")
        assert "RuntimeError" in caplog.text  # Broad handler must include the exception type.
        assert comp.counters.comparison_failures == 1  # The batch continues with a failure signal.

    @pytest.mark.parametrize(
        "exception",
        [
            requests.ConnectionError("offline"),
            requests.Timeout("slow"),
        ],
    )
    def test_org_name_request_failures_return_none(self, exception: requests.RequestException) -> None:
        """Expected request failures must remove only the optional organization hint."""
        comp = _make_comparator()  # Build the comparator with default injected dependencies.
        comp._get_org_id = MagicMock(side_effect=exception)  # Model the expected request failure.
        result = comp._get_org_name_for_validation()  # The narrowed handler should catch requests failures.
        assert result is None  # The caller continues without the optional organization hint.

    def test_org_name_http_4xx_failure_returns_none(self) -> None:
        """An HTTP 404 request failure must remove only the optional organization hint."""
        error = requests.HTTPError("HTTP 404")  # Model a 4xx cloud failure from requests.
        error.response = MagicMock(status_code=404)  # Attach the HTTP 4xx status for the analyzer and reader.
        comp = _make_comparator()  # Build the comparator with default injected dependencies.
        comp._get_org_id = MagicMock(side_effect=error)  # Model the expected HTTP 4xx request failure.
        result = comp._get_org_name_for_validation()  # The narrowed handler should catch requests failures.
        assert result is None  # The caller continues without the optional organization hint.

    def test_org_name_http_5xx_failure_returns_none(self) -> None:
        """An HTTP 503 request failure must remove only the optional organization hint."""
        error = requests.HTTPError("HTTP 503")  # Model a 5xx cloud failure from requests.
        error.response = MagicMock(status_code=503)  # Attach the HTTP 5xx status for the analyzer and reader.
        comp = _make_comparator()  # Build the comparator with default injected dependencies.
        comp._get_org_id = MagicMock(side_effect=error)  # Model the expected HTTP 5xx request failure.
        result = comp._get_org_name_for_validation()  # The narrowed handler should catch requests failures.
        assert result is None  # The caller continues without the optional organization hint.
