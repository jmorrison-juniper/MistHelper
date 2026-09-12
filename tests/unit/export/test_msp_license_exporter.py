"""Tests for ``MSPLicenseExporter``, the menu 238 entry point (issue #1260).

Why:
    The exporter owns one prompt, one Mist API call, two row builders, and two
    writes. Each part holds a guard that keeps the menu alive when the MSP has
    no license, when the body is malformed, or when the network fails. This
    module covers every one of those paths. Every Mist call is mocked, so no
    test reaches the live cloud.
"""

from __future__ import annotations

import importlib
from typing import Any
from unittest.mock import MagicMock, patch

import mistapi
import pytest

from src.export.msp_license_exporter import MSPLicenseExporter
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from src.utils.input_utils import InputUtils

# One realistic body, trimmed to the fields the exporter reads.
_PAYLOAD: dict[str, Any] = {
    "entitled": {"SUB-MAN": 10, "SUB-VNA": 4},
    "fully_loaded": {"SUB-MAN": 12},
    "summary": {"SUB-MAN": 7},
    "usages": {"SUB-MAN": 3},
    "licenses": [
        {"id": "lic-1", "org_id": "org-1", "subscription_id": "MAN-1", "type": "SUB-MAN", "quantity": 10},
        {"id": "lic-2", "org_id": "org-2", "subscription_id": "VNA-1", "type": "SUB-VNA", "quantity": 4},
    ],
    "amendments": [
        {"id": "amd-1", "subscription_id": "MAN-1", "type": "SUB-MAN", "quantity": -1},
    ],
}


@pytest.fixture
def fake_mh() -> Any:
    """Return a MistHelper stand-in holding every collaborator the exporter reads.

    Why:
        The exporter resolves ``apisession``, ``InputUtils``, and ``DataExporter``
        through a lazy ``importlib.import_module("MistHelper")`` call. One stub
        covers all three and records what the exporter wrote.
    """
    module = MagicMock()  # WHY: a MagicMock auto-creates each attribute the exporter reads.
    module.apisession = MagicMock()  # WHY: the SDK call receives this as its first argument.
    return module


class TestFetch:
    """Cover ``_fetch``, which owns the SDK call and normalizes the body."""

    def test_passes_the_session_and_the_identifier_positionally(self, fake_mh: Any) -> None:
        """The SDK contract is exactly two positional arguments, session first."""
        sdk_callable = MagicMock(return_value=MagicMock(data=_PAYLOAD))  # WHY: stand in for the SDK function.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(mistapi.api.v1.msps.licenses, "listMspLicenses", sdk_callable),
        ):
            assert MSPLicenseExporter._fetch("msp-1") == _PAYLOAD
        sdk_callable.assert_called_once_with(fake_mh.apisession, "msp-1")

    @pytest.mark.parametrize("body", [None, [], "unexpected"])
    def test_returns_an_empty_dict_for_a_non_dict_body(self, fake_mh: Any, body: Any) -> None:
        """A null body or a list body means the MSP holds no license record."""
        sdk_callable = MagicMock(return_value=MagicMock(data=body))  # WHY: drive the non-dict guard.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(mistapi.api.v1.msps.licenses, "listMspLicenses", sdk_callable),
        ):
            assert MSPLicenseExporter._fetch("msp-1") == {}


class TestBuildSummaryRow:
    """Cover ``_build_summary_row``, which keeps the counters and drops the arrays."""

    def test_leads_with_the_msp_id_primary_key(self) -> None:
        """``msp_id`` is the declared primary key, so every row must carry it."""
        row = MSPLicenseExporter._build_summary_row("msp-1", _PAYLOAD)  # WHY: run the happy path.
        assert row["msp_id"] == "msp-1"

    def test_flattens_each_counter_map_into_columns(self) -> None:
        """A counter map must become one column for each license type."""
        row = MSPLicenseExporter._build_summary_row("msp-1", _PAYLOAD)  # WHY: run the happy path.
        assert row["entitled_SUB-MAN"] == 10  # WHY: the flatten helper joins the keys with an underscore.
        assert row["usages_SUB-MAN"] == 3

    def test_drops_the_record_arrays(self) -> None:
        """The detail file owns the arrays, so the summary row must not repeat them."""
        row = MSPLicenseExporter._build_summary_row("msp-1", _PAYLOAD)  # WHY: run the happy path.
        assert not [key for key in row if key.startswith(("licenses", "amendments"))]


class TestBuildDetailRows:
    """Cover ``_build_detail_rows``, which merges two arrays into one row set."""

    def test_emits_one_row_for_each_subscription_and_amendment(self) -> None:
        """Two subscriptions and one amendment must produce three rows."""
        rows = MSPLicenseExporter._build_detail_rows("msp-1", _PAYLOAD)  # WHY: run the happy path.
        assert len(rows) == 3

    def test_tags_each_row_with_its_record_type_and_msp(self) -> None:
        """The ``record_type`` column is what separates the two kinds in one table."""
        rows = MSPLicenseExporter._build_detail_rows("msp-1", _PAYLOAD)  # WHY: run the happy path.
        assert [row["record_type"] for row in rows] == ["license", "license", "amendment"]
        assert {row["msp_id"] for row in rows} == {"msp-1"}

    def test_keeps_the_record_id_as_the_primary_key(self) -> None:
        """``id`` is the declared primary key, so a repeat run must upsert."""
        rows = MSPLicenseExporter._build_detail_rows("msp-1", _PAYLOAD)  # WHY: run the happy path.
        assert [row["id"] for row in rows] == ["lic-1", "lic-2", "amd-1"]

    def test_returns_no_row_for_an_empty_payload(self) -> None:
        """An MSP with no license is legitimate and must not raise."""
        assert MSPLicenseExporter._build_detail_rows("msp-1", {}) == []

    def test_skips_a_non_list_array_field(self, caplog: Any) -> None:
        """A malformed body must be reported, not raised into the menu loop."""
        caplog.set_level("WARNING")  # WHY: the guard reports the malformed field at WARNING level.
        rows = MSPLicenseExporter._build_detail_rows("msp-1", {"licenses": {"id": "lic-1"}})
        assert rows == []
        assert "non-list licenses field" in caplog.text

    def test_skips_a_non_dict_entry(self, caplog: Any) -> None:
        """One bad entry must not discard the entries beside it."""
        caplog.set_level("WARNING")  # WHY: the guard reports the skipped entry at WARNING level.
        rows = MSPLicenseExporter._build_detail_rows("msp-1", {"licenses": ["oops", {"id": "lic-1"}]})
        assert [row["id"] for row in rows] == ["lic-1"]
        assert "non-dict entry" in caplog.text


class TestPersist:
    """Cover ``_persist``, which owns the write and the empty-result notice."""

    def test_writes_nothing_when_there_is_no_row(self, fake_mh: Any) -> None:
        """An empty result must report plainly instead of writing an empty file."""
        with patch.object(importlib, "import_module", return_value=fake_mh):
            MSPLicenseExporter._persist([], "x.csv", "listMspLicenses", "license summary")
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_routes_the_write_through_the_declared_api_function_name(self, fake_mh: Any) -> None:
        """The api_function_name is what selects the primary-key strategy."""
        with patch.object(importlib, "import_module", return_value=fake_mh):
            MSPLicenseExporter._persist([{"msp_id": "msp-1"}], "x.csv", "listMspLicenses", "license summary")
        _, kwargs = fake_mh.DataExporter.write_with_format_selection.call_args  # WHY: read the routing key.
        assert kwargs["api_function_name"] == "listMspLicenses"


class TestLicensesEntryPoint:
    """Cover ``licenses``, the menu 238 entry point."""

    def test_aborts_before_any_api_call_when_the_operator_declines(self, fake_mh: Any) -> None:
        """No MSP identifier means no API call and no write."""
        sdk_callable = MagicMock()  # WHY: assert the SDK is never reached.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(InputUtils, "prompt_msp_id", return_value=None),
            patch.object(mistapi.api.v1.msps.licenses, "listMspLicenses", sdk_callable),
        ):
            MSPLicenseExporter.licenses()
        sdk_callable.assert_not_called()
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_writes_a_summary_file_and_a_detail_file(self, fake_mh: Any) -> None:
        """One API call must produce exactly two writes with distinct names."""
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(InputUtils, "prompt_msp_id", return_value="msp-1"),
            patch.object(MSPLicenseExporter, "_fetch", return_value=_PAYLOAD),
        ):
            MSPLicenseExporter.licenses()
        written = [call.args[1] for call in fake_mh.DataExporter.write_with_format_selection.call_args_list]
        assert written == ["MSPLicenses_msp-1_summary.csv", "MSPLicenses_msp-1_details.csv"]

    def test_writes_nothing_when_the_msp_holds_no_license(self, fake_mh: Any) -> None:
        """An empty body must produce no summary row and no detail row."""
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(InputUtils, "prompt_msp_id", return_value="msp-1"),
            patch.object(MSPLicenseExporter, "_fetch", return_value={}),
        ):
            MSPLicenseExporter.licenses()
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_swallows_an_sdk_error_so_the_menu_survives(self, fake_mh: Any, caplog: Any) -> None:
        """A network or SDK failure must be logged, not raised into the menu loop."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(InputUtils, "prompt_msp_id", return_value="msp-1"),
            patch.object(MSPLicenseExporter, "_fetch", side_effect=RuntimeError("connection reset")),
        ):
            MSPLicenseExporter.licenses()  # WHY: the menu loop must keep running.
        assert "connection reset" in caplog.text


class TestPrimaryKeyStrategies:
    """Guard the two strategy entries the exporter routes through."""

    @pytest.mark.parametrize(
        ("api_function_name", "expected_key"),
        [("listMspLicenses", ["msp_id"]), ("listMspLicensesDetails", ["id"])],
    )
    def test_each_write_target_declares_a_natural_primary_key(self, api_function_name: str, expected_key: Any) -> None:
        """A natural key is what makes a repeat run upsert instead of duplicate."""
        entry = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_function_name]  # WHY: the router reads this table.
        assert entry["type"] == "natural_pk"
        assert entry["primary_key"] == expected_key


class TestMenuRegistration:
    """Guard the menu wiring, which is what makes the exporter reachable."""

    def test_menu_238_calls_the_exporter_and_is_interactive_safe(self) -> None:
        """Menu 238 must route to the exporter and must skip the automated --test run."""
        import MistHelper  # WHY: menu_actions is the authoritative runtime mapping.
        from src.utils.operation_registry import OperationRegistry

        assert MistHelper.menu_actions["238"][0] is MSPLicenseExporter.licenses
        assert OperationRegistry.get("238")["category"] == "interactive_safe"
