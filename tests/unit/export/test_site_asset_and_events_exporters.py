"""Unit tests for the site asset, application list, and system event exporters.

Covers specs 666, 667, 668, 670 and 898 (issues #1416, #1417, #1418, #1419, #1406).

Each exporter is exercised through its public menu entry point. The collaborators
that the exporters reach lazily through ``importlib.import_module("MistHelper")``
are monkeypatched, so no network call and no real session is needed.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the error-path logging.
from typing import Any  # WHY: the monkeypatched fakes carry loose typing.
from unittest.mock import MagicMock  # WHY: collaborator doubles and call assertions.

import pytest  # WHY: monkeypatch and caplog fixtures.

from src.export.site_application_list_exporter import SiteApplicationListExporter
from src.export.site_asset_exporter import SiteAssetExporter
from src.export.site_system_events_exporter import SiteSystemEventsExporter


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every collaborator the three exporters reach through.

    Returns a dict of mocks so each test can assert argument bindings and call
    counts. Both the module-scope imports and the lazy MistHelper attributes are
    intercepted.
    """
    mocks: dict[str, Any] = {}

    for module_path in (
        "src.export.site_asset_exporter",
        "src.export.site_application_list_exporter",
        "src.export.site_system_events_exporter",
    ):
        data_processing = MagicMock(name=f"DataProcessingUtils[{module_path}]")  # Flatten and escape collaborator.
        data_processing.flatten_nested_fields.side_effect = lambda rows: rows  # Identity keeps the payload checkable.
        data_processing.escape_multiline.side_effect = lambda rows: rows  # Identity keeps the payload checkable.
        monkeypatch.setattr(f"{module_path}.DataProcessingUtils", data_processing, raising=True)
        mocks[f"dp:{module_path}"] = data_processing

        mistapi_mod = MagicMock(name=f"mistapi[{module_path}]")  # SDK double for the endpoint calls.
        mistapi_mod.get_all.side_effect = lambda response, mist_session: response  # Pass the fake rows straight back.
        monkeypatch.setattr(f"{module_path}.mistapi", mistapi_mod, raising=True)
        mocks[f"api:{module_path}"] = mistapi_mod

    data_exporter = MagicMock(name="DataExporter")  # write_with_format_selection is observed.
    apisession = MagicMock(name="apisession")  # Forwarded into every SDK call.
    site_device_exporter = MagicMock(name="SiteDeviceExporter")  # Supplies _resolve_site_for_stats.
    site_device_exporter._resolve_site_for_stats.return_value = ("site-1", "HQ Site")  # Default happy path.
    input_utils = MagicMock(name="InputUtils")  # Supplies safe_input for the get-by-id prompts.
    input_utils.safe_input.return_value = "asset-42"  # Default identifier for the prompt paths.

    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)
    monkeypatch.setattr("MistHelper.apisession", apisession, raising=False)
    monkeypatch.setattr("MistHelper.SiteDeviceExporter", site_device_exporter, raising=False)
    monkeypatch.setattr("MistHelper.InputUtils", input_utils, raising=False)

    mocks.update(
        {
            "DataExporter": data_exporter,
            "apisession": apisession,
            "SiteDeviceExporter": site_device_exporter,
            "InputUtils": input_utils,
        }
    )
    return mocks


class TestNormalizePayload:
    """Cover every branch of the shared get-by-id payload normalizer."""

    def test_none_returns_empty_list(self) -> None:
        """A missing body must produce no rows."""
        assert SiteAssetExporter._normalize_payload(None) == []

    def test_dict_is_wrapped_in_a_list(self) -> None:
        """A single object must become a one-row list."""
        assert SiteAssetExporter._normalize_payload({"id": "a1"}) == [{"id": "a1"}]

    def test_list_keeps_only_dict_rows(self) -> None:
        """Non-dict entries must be dropped so the exporter stays uniform."""
        payload = [{"id": "a1"}, "not-a-dict", {"id": "a2"}]
        assert SiteAssetExporter._normalize_payload(payload) == [{"id": "a1"}, {"id": "a2"}]

    def test_unexpected_type_warns_and_returns_empty(self, caplog: pytest.LogCaptureFixture) -> None:
        """An unsupported payload type must warn rather than raise."""
        with caplog.at_level(logging.WARNING):
            assert SiteAssetExporter._normalize_payload(42) == []
        assert "Unexpected payload type" in caplog.text


class TestAssetsOfInterest:
    """Cover menu 210, which is getSiteAssetsOfInterest."""

    def test_happy_path_fetches_pages_and_persists(self, wired: dict[str, Any]) -> None:
        """The exporter must call the SDK, page the rows, and write them once."""
        api = wired["api:src.export.site_asset_exporter"]
        api.api.v1.sites.stats.getSiteAssetsOfInterest.return_value = [{"mac": "aa:bb"}]

        SiteAssetExporter.assets_of_interest()

        api.api.v1.sites.stats.getSiteAssetsOfInterest.assert_called_once_with(wired["apisession"], "site-1")
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"mac": "aa:bb"}],
            "SiteAssetsOfInterest_HQ_Site.csv",
            api_function_name="getSiteAssetsOfInterest",
        )

    def test_aborts_when_site_resolution_returns_none(self, wired: dict[str, Any]) -> None:
        """A declined site prompt must stop before any API call."""
        wired["SiteDeviceExporter"]._resolve_site_for_stats.return_value = None

        SiteAssetExporter.assets_of_interest()

        api = wired["api:src.export.site_asset_exporter"]
        api.api.v1.sites.stats.getSiteAssetsOfInterest.assert_not_called()
        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_empty_result_writes_nothing(self, wired: dict[str, Any]) -> None:
        """An empty page must report the fact and skip the export."""
        api = wired["api:src.export.site_asset_exporter"]
        api.api.v1.sites.stats.getSiteAssetsOfInterest.return_value = []

        SiteAssetExporter.assets_of_interest()

        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_api_error_is_logged_and_does_not_raise(
        self, wired: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An SDK failure must surface in the log rather than crash the menu."""
        api = wired["api:src.export.site_asset_exporter"]
        api.api.v1.sites.stats.getSiteAssetsOfInterest.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            SiteAssetExporter.assets_of_interest()

        assert "Error fetching assets of interest" in caplog.text
        wired["DataExporter"].write_with_format_selection.assert_not_called()


class TestAssetFilterAndAsset:
    """Cover menus 211 and 212, which are the two get-by-id operations."""

    def test_asset_filter_happy_path(self, wired: dict[str, Any]) -> None:
        """The filter detail must be fetched by identifier and written once."""
        api = wired["api:src.export.site_asset_exporter"]
        api.api.v1.sites.assetfilters.getSiteAssetFilter.return_value = {"id": "af-1"}

        SiteAssetExporter.asset_filter()

        api.api.v1.sites.assetfilters.getSiteAssetFilter.assert_called_once_with(
            wired["apisession"], "site-1", "asset-42"
        )
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "af-1"}],
            "SiteAssetFilter_HQ_Site_asset_42.csv",
            api_function_name="getSiteAssetFilter",
        )

    def test_asset_happy_path(self, wired: dict[str, Any]) -> None:
        """The asset detail must be fetched by identifier and written once."""
        api = wired["api:src.export.site_asset_exporter"]
        api.api.v1.sites.assets.getSiteAsset.return_value = {"id": "as-1"}

        SiteAssetExporter.asset()

        api.api.v1.sites.assets.getSiteAsset.assert_called_once_with(wired["apisession"], "site-1", "asset-42")
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "as-1"}],
            "SiteAsset_HQ_Site_asset_42.csv",
            api_function_name="getSiteAsset",
        )

    def test_blank_identifier_aborts_before_the_api_call(self, wired: dict[str, Any]) -> None:
        """An empty identifier must stop the flow before the SDK is reached."""
        wired["InputUtils"].safe_input.return_value = "   "

        SiteAssetExporter.asset()

        api = wired["api:src.export.site_asset_exporter"]
        api.api.v1.sites.assets.getSiteAsset.assert_not_called()
        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_response_data_attribute_is_preferred(self, wired: dict[str, Any]) -> None:
        """A response object carrying .data must be unwrapped before normalizing."""
        api = wired["api:src.export.site_asset_exporter"]
        response = MagicMock()
        response.data = {"id": "as-9"}
        api.api.v1.sites.assets.getSiteAsset.return_value = response

        SiteAssetExporter.asset()

        written_rows = wired["DataExporter"].write_with_format_selection.call_args[0][0]
        assert written_rows == [{"id": "as-9"}]


class TestApplicationList:
    """Cover menu 213, which is getSiteApplicationList."""

    def test_happy_path_persists_rows(self, wired: dict[str, Any]) -> None:
        """The application list must be fetched and written once."""
        api = wired["api:src.export.site_application_list_exporter"]
        api.api.v1.sites.wxtags.getSiteApplicationList.return_value = [{"app_id": "ssh"}]

        SiteApplicationListExporter.application_list()

        api.api.v1.sites.wxtags.getSiteApplicationList.assert_called_once_with(wired["apisession"], "site-1")
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"app_id": "ssh"}],
            "SiteApplicationList_HQ_Site.csv",
            api_function_name="getSiteApplicationList",
        )

    def test_api_error_is_logged_and_does_not_raise(
        self, wired: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An SDK failure must surface in the log rather than crash the menu."""
        api = wired["api:src.export.site_application_list_exporter"]
        api.api.v1.sites.wxtags.getSiteApplicationList.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            SiteApplicationListExporter.application_list()

        assert "Error fetching the application list" in caplog.text


class TestSystemEvents:
    """Cover menu 214, which is searchSiteSystemEvents."""

    def test_happy_path_persists_rows(self, wired: dict[str, Any]) -> None:
        """The event search must be fetched, paged, and written once."""
        api = wired["api:src.export.site_system_events_exporter"]
        api.api.v1.sites.events.searchSiteSystemEvents.return_value = [{"type": "AP_CONFIG_CHANGED"}]

        SiteSystemEventsExporter.system_events()

        api.api.v1.sites.events.searchSiteSystemEvents.assert_called_once_with(wired["apisession"], "site-1")
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"type": "AP_CONFIG_CHANGED"}],
            "SiteSystemEvents_HQ_Site.csv",
            api_function_name="searchSiteSystemEvents",
        )

    def test_empty_result_writes_nothing(self, wired: dict[str, Any]) -> None:
        """An empty search must report the fact and skip the export."""
        api = wired["api:src.export.site_system_events_exporter"]
        api.api.v1.sites.events.searchSiteSystemEvents.return_value = []

        SiteSystemEventsExporter.system_events()

        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_aborts_when_site_resolution_returns_none(self, wired: dict[str, Any]) -> None:
        """A declined site prompt must stop before any API call."""
        wired["SiteDeviceExporter"]._resolve_site_for_stats.return_value = None

        SiteSystemEventsExporter.system_events()

        api = wired["api:src.export.site_system_events_exporter"]
        api.api.v1.sites.events.searchSiteSystemEvents.assert_not_called()
