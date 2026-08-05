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
    (
        "wireless_client_events",
        "searchSiteWirelessClientEvents",
        "SiteWirelessClientEvents",
        ("clients", "searchSiteWirelessClientEvents"),
    ),
    ("wan_clients", "searchSiteWanClients", "SiteWanClients", ("wan_clients", "searchSiteWanClients")),
    ("device_events", "searchSiteDeviceEvents", "SiteDeviceEvents", ("devices", "searchSiteDeviceEvents")),
    ("devices", "searchSiteDevices", "SiteDevices", ("devices", "searchSiteDevices")),
    ("rogue_events", "searchSiteRogueEvents", "SiteRogueEvents", ("rogues", "searchSiteRogueEvents")),
    ("ospf_stats", "searchSiteOspfStats", "SiteOspfStats", ("stats", "searchSiteOspfStats")),
    (
        "device_last_configs",
        "searchSiteDeviceLastConfigs",
        "SiteDeviceLastConfigs",
        ("devices", "searchSiteDeviceLastConfigs"),
    ),
    (
        "device_config_history",
        "searchSiteDeviceConfigHistory",
        "SiteDeviceConfigHistory",
        ("devices", "searchSiteDeviceConfigHistory"),
    ),
    (
        "discovered_switches",
        "searchSiteDiscoveredSwitches",
        "SiteDiscoveredSwitches",
        ("stats", "searchSiteDiscoveredSwitches"),
    ),
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
    input_utils = MagicMock(name="InputUtils")  # Supplies safe_input for the zone type prompt.
    input_utils.safe_input.return_value = "zones"  # Default answer for the zone session menu.
    monkeypatch.setattr("MistHelper.InputUtils", input_utils, raising=False)

    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)
    monkeypatch.setattr("MistHelper.apisession", apisession, raising=False)
    monkeypatch.setattr("MistHelper.SiteDeviceExporter", site_device_exporter, raising=False)

    return {
        "DataProcessingUtils": data_processing,
        "mistapi": mistapi_mod,
        "DataExporter": data_exporter,
        "apisession": apisession,
        "SiteDeviceExporter": site_device_exporter,
        "InputUtils": input_utils,
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


class TestZoneSessions:
    """Menu 229 needs a zone type in the URL path, so it prompts for one.

    A wrong zone type produces a 404 rather than an empty result, so the prompt
    must reject anything outside the two values the SDK accepts.
    """

    def test_default_zone_type_is_forwarded_to_the_endpoint(self, wired: dict[str, Any]) -> None:
        """An empty answer must fall back to the common zone type."""
        wired["InputUtils"].safe_input.return_value = ""
        target = wired["mistapi"].api.v1.sites.visits.searchSiteZoneSessions
        target.return_value = [{"id": "session-1"}]

        SiteSearchExporter.zone_sessions()

        target.assert_called_once_with(wired["apisession"], "site-1", "zones")

    def test_rssizones_is_forwarded_and_named_in_the_filename(self, wired: dict[str, Any]) -> None:
        """The chosen zone type must reach the endpoint and the output filename."""
        wired["InputUtils"].safe_input.return_value = "rssizones"
        target = wired["mistapi"].api.v1.sites.visits.searchSiteZoneSessions
        target.return_value = [{"id": "session-1"}]

        SiteSearchExporter.zone_sessions()

        target.assert_called_once_with(wired["apisession"], "site-1", "rssizones")
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "session-1"}],
            "SiteZoneSessions_rssizones_HQ_Site.csv",
            api_function_name="searchSiteZoneSessions",
        )

    def test_invalid_zone_type_aborts_before_the_api_call(
        self, wired: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unsupported zone type must stop the flow instead of causing a 404."""
        wired["InputUtils"].safe_input.return_value = "floors"

        with caplog.at_level(logging.ERROR):
            SiteSearchExporter.zone_sessions()

        assert "Invalid zone type" in caplog.text
        wired["mistapi"].api.v1.sites.visits.searchSiteZoneSessions.assert_not_called()
        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_zone_type_prompt_runs_before_the_site_prompt_is_wasted(self, wired: dict[str, Any]) -> None:
        """An invalid zone type must not make the operator pick a site first."""
        wired["InputUtils"].safe_input.return_value = "bogus"

        SiteSearchExporter.zone_sessions()

        wired["SiteDeviceExporter"]._resolve_site_for_stats.assert_not_called()
