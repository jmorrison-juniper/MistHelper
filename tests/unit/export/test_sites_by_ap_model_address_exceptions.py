"""Verify the address fallback contract without Mist calls or real site data."""

import logging
from unittest.mock import Mock

import pytest

from src.operations.exporting.export.sites_by_ap_model_exporter import SitesByAPModelExporter


class TestAddressExceptionBoundary:
    """Keep external address fallbacks and expose unexpected parsing failures."""

    @pytest.mark.parametrize(
        ("address", "expected"),
        [
            ("1 Example St, Test City, CA 90000, USA", ("1 Example St", "Test City", "CA", "90000", "USA")),
            ("1 Example St, Test City, CA\t90000, USA", ("1 Example St", "Test City", "CA", "90000", "USA")),
            ("1 Example St, Test City, CA 90000 extra, USA", ("1 Example St", "Test City", "CA", "90000", "USA")),
            ("1 Example St, Test City, CA 90000, USA, extra", ("1 Example St", "Test City", "CA", "90000", "USA")),
            (", , CA 90000, ", ("", "", "CA", "90000", "")),
        ],
    )
    def test_complete_strings_keep_existing_token_rules(
        self, address: str, expected: tuple[str, str, str, str, str]
    ) -> None:
        """Preserve exact delimiters, empty fields, and ignored extra tokens."""
        result = SitesByAPModelExporter._split_address(address)
        assert result == expected

    @pytest.mark.parametrize(
        "address",
        [
            "",
            "1 Example St",
            "1 Example St, Test City",
            "1 Example St, Test City, CA 90000",
            "1 Example St, Test City, , USA",
            "1 Example St, Test City, CA, USA",
            "1 Example St, Test City,    , USA",
            "1 Example St,Test City,CA 90000,USA",
            "1 Example St, Test City, 90000, USA",
        ],
    )
    def test_incomplete_strings_keep_the_whole_address(self, address: str, caplog: pytest.LogCaptureFixture) -> None:
        """A missing field or token must retain the original address and a diagnostic."""
        with caplog.at_level(logging.DEBUG):
            result = SitesByAPModelExporter._split_address(address)
        assert result == (address, "", "", "", "")
        assert any("Failed to split address" in record.getMessage() for record in caplog.records)

    @pytest.mark.parametrize(
        "address", [None, False, 0, 3.5, [], {}, ["synthetic"], {"synthetic": "value"}, b"synthetic"]
    )
    def test_non_string_values_remain_unchanged(self, address: object, caplog: pytest.LogCaptureFixture) -> None:
        """Preserve the fallback for absent and non-string external values without conversion."""
        with caplog.at_level(logging.DEBUG):
            result = SitesByAPModelExporter._split_address(address)
        assert result == (address, "", "", "", "")
        assert result[0] is address
        assert len(caplog.records) > 0

    @pytest.mark.parametrize(
        ("site", "expected"),
        [
            ({}, ("", "", "", "", "")),
            ({"address": None}, (None, "", "", "", "")),
            ({"address": False}, (False, "", "", "", "")),
            ({"address": 42}, (42, "", "", "", "")),
            ({"address": ["synthetic"]}, (["synthetic"], "", "", "", "")),
            ({"address": {"synthetic": "value"}}, ({"synthetic": "value"}, "", "", "", "")),
            ({"address": "1 Example St"}, ("1 Example St", "", "", "", "")),
            (
                {"address": "1 Example St, Test City, CA 90000, USA"},
                ("1 Example St", "Test City", "CA", "90000", "USA"),
            ),
        ],
    )
    def test_export_rows_preserve_external_address_values(
        self, site: dict[str, object], expected: tuple[object, str, str, str, str]
    ) -> None:
        """Exercise the site-to-row path without a cloud request or an output file."""
        rows = SitesByAPModelExporter._build_export_rows(
            [{"model": "AP41", "site_id": "synthetic-site", "mac": "000000000001"}], "AP41", {"synthetic-site": site}
        )
        assert rows == [
            {
                "site_id": "synthetic-site",
                "site_name": "",
                "ap_model": "AP41",
                "ap_count": 1,
                "address": expected[0],
                "city": expected[1],
                "state": expected[2],
                "zip": expected[3],
                "country": expected[4],
                "ap_macs": "000000000001",
            }
        ]

    @pytest.mark.parametrize("error_type", [RuntimeError, TypeError, AttributeError, NameError, IndexError])
    def test_unexpected_split_errors_propagate(self, error_type: type[Exception]) -> None:
        """A split implementation defect must not become an address fallback."""
        error = error_type("synthetic split failure")
        address = Mock(spec=str)
        address.split.side_effect = error
        with pytest.raises(error_type, match="synthetic split failure") as raised:
            SitesByAPModelExporter._split_address(address)
        assert raised.value is error

    @pytest.mark.parametrize("batch_size", [1, 100, 1000])
    def test_batch_keeps_operator_log_count_bounded(self, batch_size: int, caplog: pytest.LogCaptureFixture) -> None:
        """Address transforms must not add operator messages as an export grows."""
        with caplog.at_level(logging.DEBUG):
            results = [
                SitesByAPModelExporter._split_address("1 Example St, Test City, CA 90000, USA")
                for _ in range(batch_size)
            ]
        assert results == [("1 Example St", "Test City", "CA", "90000", "USA")] * batch_size
        assert sum(record.levelno >= logging.INFO for record in caplog.records) == 0
        assert any("Split a site address into five fields." in record.getMessage() for record in caplog.records)

    @pytest.mark.parametrize("error_type", [RuntimeError, TypeError, AttributeError, NameError, IndexError])
    def test_unexpected_state_zip_split_errors_propagate(self, error_type: type[Exception]) -> None:
        """The second split must not hide a defect as a missing address token."""
        error = error_type("synthetic state ZIP split failure")
        state_zip = Mock(spec=str)
        state_zip.split.side_effect = error
        address = Mock(spec=str)
        address.split.return_value = ["1 Example St", "Test City", state_zip, "USA"]
        with pytest.raises(error_type, match="synthetic state ZIP split failure") as raised:
            SitesByAPModelExporter._split_address(address)
        assert raised.value is error
