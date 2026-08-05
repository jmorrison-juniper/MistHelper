"""Unit tests for the site-scoped search exporter.

Covers specs 879, 880, 881, 882 and 897 (issues #1387, #1388, #1389, #1390 and
#1405), which are menus 215 to 219.

The five operations share one helper, so the shared behavior is tested once and
each menu entry is checked for the binding that makes it distinct.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the error-path logging.
from typing import Any  # WHY: the monkeypatched fakes carry loose typing.
from unittest.mock import MagicMock  # WHY: collaborator doubles and call assertions.

import pytest  # WHY: monkeypatch and caplog fixtures.

from src.export.site_search_exporter import SiteSearchExporter

# Each row maps a menu entry to the operationId, the filename prefix, and the
# SDK attribute chain that the entry must call.
MENU_BINDINGS = [
    ("alarms", "searchSiteAlarms", "SiteAlarms", ("alarms", "searchSiteAlarms")),
    ("assets", "searchSiteAssets", "SiteAssets", ("stats", "searchSiteAssets")),
    ("bgp_stats", "searchSiteBgpStats", "SiteBgpStats", ("stats", "searchSiteBgpStats")),
    ("calls", "searchSiteCalls", "SiteCalls", ("stats", "searchSiteCalls")),
    ("skyatp_events", "searchSiteSkyatpEvents", "SiteSkyatpEvents", ("skyatp", "searchSiteSkyatpEvents")),
]


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every collaborator the exporter reaches through.

    Returns a dict of mocks so each test can assert argument bindings and call
    counts. No network call and no real session is needed.
    """
    data_processing = MagicMock(name="DataProcessingUtils")  # Flatten and escape collaborator.
    data_processing.flatten_nested_fields.side_effect = lambda rows: rows  # Identity keeps the payload checkable.
    data_processing.escape_multiline.side_effect = lambda rows: rows  # Identity keeps the payload checkable.
    monkeypatch.setattr("src.export.site_search_exporter.DataProcessingUtils", data_processing, raising=True)

    mistapi_mod = MagicMock(name="mistapi")  # SDK double for every endpoint call.
    mistapi_mod.get_all.side_effect = lambda response, mist_session: response  # Pass the fake rows straight back.
    monkeypatch.setattr("src.export.site_search_exporter.mistapi", mistapi_mod, raising=True)

    data_exporter = MagicMock(name="DataExporter")  # write_with_format_selection is observed.
    apisession = MagicMock(name="apisession")  # Forwarded into every SDK call.
    site_device_exporter = MagicMock(name="SiteDeviceExporter")  # Supplies _resolve_site_for_stats.
    site_device_exporter._resolve_site_for_stats.return_value = ("site-1", "HQ Site")  # Default happy path.

    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)
    monkeypatch.setattr("MistHelper.apisession", apisession, raising=False)
    monkeypatch.setattr("MistHelper.SiteDeviceExporter", site_device_exporter, raising=False)

    return {
        "DataProcessingUtils": data_processing,
        "mistapi": mistapi_mod,
        "DataExporter": data_exporter,
        "apisession": apisession,
        "SiteDeviceExporter": site_device_exporter,
    }


def _sdk_target(mistapi_mod: MagicMock, chain: tuple[str, str]) -> MagicMock:
    """Return the SDK callable double that a menu entry is expected to call."""
    module_attribute, function_name = chain  # Split the module and the function halves.
    module = getattr(mistapi_mod.api.v1.sites, module_attribute)  # Walk to the SDK submodule double.
    return getattr(module, function_name)  # Return the function double itself.


class TestMenuBindings:
    """Each menu entry must reach its own SDK function and write its own file."""

    @pytest.mark.parametrize(("method", "operation", "prefix", "chain"), MENU_BINDINGS)
    def test_entry_calls_its_endpoint_and_persists(
        self, wired: dict[str, Any], method: str, operation: str, prefix: str, chain: tuple[str, str]
    ) -> None:
        """The entry must call its endpoint once and write with its own operationId."""
        target = _sdk_target(wired["mistapi"], chain)
        target.return_value = [{"id": "row-1"}]

        getattr(SiteSearchExporter, method)()

        target.assert_called_once_with(wired["apisession"], "site-1")
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "row-1"}],
            f"{prefix}_HQ_Site.csv",
            api_function_name=operation,
        )

    @pytest.mark.parametrize(("method", "operation", "prefix", "chain"), MENU_BINDINGS)
    def test_entry_aborts_when_site_resolution_returns_none(
        self, wired: dict[str, Any], method: str, operation: str, prefix: str, chain: tuple[str, str]
    ) -> None:
        """A declined site prompt must stop before any API call."""
        wired["SiteDeviceExporter"]._resolve_site_for_stats.return_value = None

        getattr(SiteSearchExporter, method)()

        _sdk_target(wired["mistapi"], chain).assert_not_called()
        wired["DataExporter"].write_with_format_selection.assert_not_called()


class TestSharedBehavior:
    """Cover the branches of the shared helper once."""

    def test_empty_result_writes_nothing(self, wired: dict[str, Any]) -> None:
        """An empty search must report the fact and skip the export."""
        wired["mistapi"].api.v1.sites.alarms.searchSiteAlarms.return_value = []

        SiteSearchExporter.alarms()

        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_api_error_is_logged_and_does_not_raise(
        self, wired: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An SDK failure must surface in the log rather than crash the menu."""
        wired["mistapi"].api.v1.sites.alarms.searchSiteAlarms.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            SiteSearchExporter.alarms()

        assert "Error fetching alarm for site" in caplog.text
        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_rows_are_flattened_and_escaped_before_the_write(self, wired: dict[str, Any]) -> None:
        """The persist step must run both CSV-safety helpers on the payload."""
        rows = [{"id": "row-1", "nested": {"a": 1}}]
        wired["mistapi"].api.v1.sites.alarms.searchSiteAlarms.return_value = rows

        SiteSearchExporter.alarms()

        wired["DataProcessingUtils"].flatten_nested_fields.assert_called_once_with(rows)
        wired["DataProcessingUtils"].escape_multiline.assert_called_once_with(rows)

    def test_pagination_helper_receives_the_response(self, wired: dict[str, Any]) -> None:
        """Every search must page through get_all rather than read one page."""
        wired["mistapi"].api.v1.sites.alarms.searchSiteAlarms.return_value = [{"id": "row-1"}]

        SiteSearchExporter.alarms()

        wired["mistapi"].get_all.assert_called_once_with(response=[{"id": "row-1"}], mist_session=wired["apisession"])
