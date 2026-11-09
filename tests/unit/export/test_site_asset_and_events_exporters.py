"""Unit tests for the site asset, application list, and system event exporters.

Covers specs 666, 667, 668, 670 and 898 (issues #1416, #1417, #1418, #1419, #1406).

Each exporter is exercised through its public menu entry point. The collaborators
that the exporters reach lazily through ``SourceDependencyResolver``
are monkeypatched, so no network call and no real session is needed.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the error-path logging.
from typing import Any  # WHY: the monkeypatched fakes carry loose typing.
from unittest.mock import MagicMock  # WHY: collaborator doubles and call assertions.

import pytest  # WHY: monkeypatch and caplog fixtures.

from src.operations.exporting.export import (
    org_site_exporter as org_site_mod,
)  # WHY: patch the product guest exporter module.
from src.operations.exporting.export.org_site_exporter import OrgSiteExporter  # WHY: drive the real guest exporter.
from src.operations.exporting.export.org_site_exporter import OrgSiteExporter as FailureModeOrgSiteExporter
from src.operations.exporting.export.site_application_list_exporter import SiteApplicationListExporter
from src.operations.exporting.export.site_asset_exporter import SiteAssetExporter
from src.operations.exporting.export.site_system_events_exporter import SiteSystemEventsExporter


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every collaborator the three exporters reach through.

    Returns a dict of mocks so each test can assert argument bindings and call
    counts. Both the module-scope imports and the lazy MistHelper attributes are
    intercepted.
    """
    mocks: dict[str, Any] = {}

    for module_path in (
        "src.operations.exporting.export.site_asset_exporter",
        "src.operations.exporting.export.site_application_list_exporter",
        "src.operations.exporting.export.site_system_events_exporter",
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
        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
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

        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
        api.api.v1.sites.stats.getSiteAssetsOfInterest.assert_not_called()
        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_empty_result_writes_nothing(self, wired: dict[str, Any]) -> None:
        """An empty page must report the fact and skip the export."""
        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
        api.api.v1.sites.stats.getSiteAssetsOfInterest.return_value = []

        SiteAssetExporter.assets_of_interest()

        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_api_error_is_logged_and_does_not_raise(
        self, wired: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An SDK failure must surface in the log rather than crash the menu."""
        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
        api.api.v1.sites.stats.getSiteAssetsOfInterest.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            SiteAssetExporter.assets_of_interest()

        assert "Error fetching assets of interest" in caplog.text
        wired["DataExporter"].write_with_format_selection.assert_not_called()


def test_current_guests_http_429_reports_status_and_skips_success(
    wired: dict[str, Any], caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 429 current-guest response must report the status and skip export."""
    fake_mh = MagicMock()  # WHY: OrgSiteExporter resolves dependencies through its source resolver.
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: fixed org id for the call.
    fake_mh.apisession = wired["apisession"]  # WHY: reuse the API session double.
    fake_mh.DataExporter = wired["DataExporter"]  # WHY: observe that no export occurs.
    response = MagicMock(status_code=429, data=[{"guest": "ignored"}])  # WHY: failed data is untrustworthy.
    get_all_mock = MagicMock()  # WHY: prove success pagination is skipped.
    caplog.set_level(logging.ERROR, logger=org_site_mod.logger.name)  # WHY: capture the product status log.
    monkeypatch.setattr(org_site_mod, "SourceDependencyResolver", fake_mh)  # WHY: route dependencies.
    monkeypatch.setattr(
        org_site_mod.mistapi.api.v1.orgs.guests,
        "searchOrgGuestAuthorization",
        MagicMock(return_value=response),
    )  # WHY: return the rate-limit response.
    monkeypatch.setattr(org_site_mod.mistapi, "get_all", get_all_mock)  # WHY: observe pagination.
    OrgSiteExporter.current_guests()  # WHY: drive the product 4xx status path.
    assert "HTTP 429" in caplog.text  # WHY: the operator must see the exact rate-limit status.
    assert "current guest users" in caplog.text  # WHY: the log must name the failed data set.
    get_all_mock.assert_not_called()  # WHY: pagination must not run on failed status.
    wired["DataExporter"].write_with_format_selection.assert_not_called()  # WHY: no false empty export.


def test_current_guests_http_503_reports_status_and_skips_success(
    wired: dict[str, Any], caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 503 current-guest response must report the status and skip export."""
    fake_mh = MagicMock()  # WHY: OrgSiteExporter resolves dependencies through its source resolver.
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: fixed org id for the call.
    fake_mh.apisession = wired["apisession"]  # WHY: reuse the API session double.
    fake_mh.DataExporter = wired["DataExporter"]  # WHY: observe that no export occurs.
    response = MagicMock(status_code=503, data=[{"guest": "ignored"}])  # WHY: failed data is not trustworthy.
    get_all_mock = MagicMock()  # WHY: prove success pagination is skipped.
    caplog.set_level(logging.ERROR, logger=org_site_mod.logger.name)  # WHY: capture the product status log.
    monkeypatch.setattr(org_site_mod, "SourceDependencyResolver", fake_mh)  # WHY: route dependencies.
    monkeypatch.setattr(
        org_site_mod.mistapi.api.v1.orgs.guests,
        "searchOrgGuestAuthorization",
        MagicMock(return_value=response),
    )  # WHY: return the server-error response.
    monkeypatch.setattr(org_site_mod.mistapi, "get_all", get_all_mock)  # WHY: observe pagination.
    FailureModeOrgSiteExporter.current_guests()  # WHY: drive the real src 5xx status path.
    assert "HTTP 503" in caplog.text  # WHY: the operator must see the exact server failure.
    assert "current guest users" in caplog.text  # WHY: the log must name the failed data set.
    get_all_mock.assert_not_called()  # WHY: pagination must not run on failed status.
    wired["DataExporter"].write_with_format_selection.assert_not_called()  # WHY: no false empty export.


class TestAssetFilterAndAsset:
    """Cover menus 211 and 212, which are the two get-by-id operations."""

    def test_asset_filter_happy_path(self, wired: dict[str, Any]) -> None:
        """The filter detail must be fetched by identifier and written once."""
        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
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
        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
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

        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
        api.api.v1.sites.assets.getSiteAsset.assert_not_called()
        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_response_data_attribute_is_preferred(self, wired: dict[str, Any]) -> None:
        """A response object carrying .data must be unwrapped before normalizing."""
        api = wired["api:src.operations.exporting.export.site_asset_exporter"]
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
        api = wired["api:src.operations.exporting.export.site_application_list_exporter"]
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
        api = wired["api:src.operations.exporting.export.site_application_list_exporter"]
        api.api.v1.sites.wxtags.getSiteApplicationList.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            SiteApplicationListExporter.application_list()

        assert "Error fetching the application list" in caplog.text


class TestSystemEvents:
    """Cover menu 214, which is searchSiteSystemEvents."""

    def test_happy_path_persists_rows(self, wired: dict[str, Any]) -> None:
        """The event search must be fetched, paged, and written once."""
        api = wired["api:src.operations.exporting.export.site_system_events_exporter"]
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
        api = wired["api:src.operations.exporting.export.site_system_events_exporter"]
        api.api.v1.sites.events.searchSiteSystemEvents.return_value = []

        SiteSystemEventsExporter.system_events()

        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_aborts_when_site_resolution_returns_none(self, wired: dict[str, Any]) -> None:
        """A declined site prompt must stop before any API call."""
        wired["SiteDeviceExporter"]._resolve_site_for_stats.return_value = None

        SiteSystemEventsExporter.system_events()

        api = wired["api:src.operations.exporting.export.site_system_events_exporter"]
        api.api.v1.sites.events.searchSiteSystemEvents.assert_not_called()


class TestSiteWriteOutcomes:
    """Keep persistence results consistent through both site menu operations."""

    @pytest.fixture(
        params=[
            ("applications", False),
            ("applications", True),
            ("system-events", False),
            ("system-events", True),
        ],
        ids=["applications-direct", "applications-menu", "system-events-direct", "system-events-menu"],
    )
    def write_case(self, wired: dict[str, Any], request: pytest.FixtureRequest) -> dict[str, Any]:
        """Supply synthetic rows through the persistence method or the menu."""
        applications, through_menu = request.param  # Select the reserved exporter and its entry point.
        exporter = SiteApplicationListExporter if applications == "applications" else SiteSystemEventsExporter
        module_path = exporter.__module__  # Reuse the existing collaborator isolation for this source module.
        api = wired[f"api:{module_path}"].api.v1.sites  # Keep SDK calls inside the existing mock tree.
        endpoint = "getSiteApplicationList" if applications == "applications" else "searchSiteSystemEvents"
        rows = [{"id": "synthetic"}]  # Use no production identifiers or records.
        sdk_module = api.wxtags if applications == "applications" else api.events  # Preserve endpoint routing.
        getattr(sdk_module, endpoint).return_value = rows  # Feed the menu the same rows as the direct method.
        persist = getattr(
            exporter, "_persist_applications" if applications == "applications" else "_persist_system_events"
        )
        menu = getattr(exporter, "application_list" if applications == "applications" else "system_events")
        return {
            "invoke": menu if through_menu else lambda: persist(rows, "HQ Site"),
            "through_menu": through_menu,
            "rows": rows,
            "endpoint": endpoint,
            "filename": f"{exporter.__name__.removesuffix('Exporter')}_HQ_Site.csv",
            "writer": wired["DataExporter"].write_with_format_selection,
            "processing": wired[f"dp:{module_path}"],
        }

    def test_failed_write_reports_error_without_success(
        self, write_case: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed writer must not produce either persistence success message."""
        write_case["writer"].return_value = False  # Exercise the reported defect with a real Boolean result.
        with caplog.at_level(logging.DEBUG):  # Capture the persistence trace as well as operator notices.
            result = write_case["invoke"]()  # Exercise the direct method and the menu integration independently.
        assert result is None  # Preserve the existing public and private return contracts.
        write_case["writer"].assert_called_once_with(
            write_case["rows"], write_case["filename"], api_function_name=write_case["endpoint"]
        )
        errors = [record.message for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(errors) == 1  # Report one failure rather than a success or duplicate error.
        assert write_case["filename"] in errors[0]  # Identify the output that the writer could not save.
        assert write_case["endpoint"] in errors[0]  # Identify the operation that failed.
        assert "persisted" not in caplog.text  # Reject a false persistence trace.
        assert " exported " not in caplog.text  # Reject a false operator success notice.

    def test_successful_write_preserves_transforms_and_messages(
        self, write_case: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A successful writer must receive sanitized rows and retain both notices."""
        write_case["writer"].return_value = True  # Require an explicit successful writer result.
        processing = write_case["processing"]  # Observe both existing row transformations.
        processing.flatten_nested_fields.side_effect = None  # Replace the fixture's identity transformation.
        processing.flatten_nested_fields.return_value = [{"flat": "synthetic"}]  # Distinguish the flatten result.
        processing.escape_multiline.side_effect = None  # Replace the fixture's identity escaping.
        processing.escape_multiline.return_value = [{"safe": "synthetic"}]  # Distinguish the writer payload.
        with caplog.at_level(logging.DEBUG):  # Retain evidence for both success messages.
            result = write_case["invoke"]()  # Exercise the same successful result through both entry points.
        assert result is None  # Do not expose the writer result as a new return value.
        processing.flatten_nested_fields.assert_called_once_with(write_case["rows"])
        processing.escape_multiline.assert_called_once_with([{"flat": "synthetic"}])
        write_case["writer"].assert_called_once_with(
            [{"safe": "synthetic"}], write_case["filename"], api_function_name=write_case["endpoint"]
        )
        assert f"{write_case['endpoint']} persisted 1 rows to {write_case['filename']}" in caplog.text
        kind = "application" if write_case["endpoint"] == "getSiteApplicationList" else "system event"
        assert f"! 1 {kind} records exported to {write_case['filename']}" in caplog.text
        assert not any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_empty_rows_preserve_notice_without_writing(
        self, write_case: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An empty response must still stop before transformation or persistence."""
        write_case["rows"].clear()  # Feed both entry points an empty synthetic response.
        with caplog.at_level(logging.DEBUG):  # Detect an accidental success or error notice.
            result = write_case["invoke"]()  # Exercise the existing early return.
        assert result is None  # Preserve the empty-result return contract.
        write_case["writer"].assert_not_called()  # Never persist an empty result.
        write_case["processing"].flatten_nested_fields.assert_not_called()  # Preserve the early return boundary.
        write_case["processing"].escape_multiline.assert_not_called()  # Do not sanitize missing rows.
        kind = "application" if write_case["endpoint"] == "getSiteApplicationList" else "system event"
        assert f"! No {kind} data found for this site" in caplog.text  # Keep the existing empty notice.
        assert "persisted" not in caplog.text  # Do not report a persistence operation.
        assert " exported " not in caplog.text  # Do not report a successful export.
        assert not any(record.levelno >= logging.ERROR for record in caplog.records)

    def test_writer_exception_keeps_existing_boundary(
        self, write_case: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Direct calls must propagate exceptions while menus retain their handlers."""
        failure = RuntimeError("synthetic writer failure")  # Use a fixed error with no production details.
        write_case["writer"].side_effect = failure  # Fail only the mocked persistence operation.
        with caplog.at_level(logging.DEBUG):  # Reject success messages after the exception.
            if write_case["through_menu"]:  # Menu handlers already convert exceptions into operator errors.
                assert write_case["invoke"]() is None  # Preserve the menu return contract.
                assert "synthetic writer failure" in caplog.text  # Retain the existing failure context.
                assert any(record.levelno >= logging.ERROR for record in caplog.records)
            else:  # Private persistence methods must not swallow a writer exception.
                with pytest.raises(RuntimeError, match="synthetic writer failure") as raised:
                    write_case["invoke"]()  # Exercise the unchanged exception boundary.
                assert raised.value is failure  # Preserve the exact exception rather than replace it.
        write_case["writer"].assert_called_once_with(
            write_case["rows"], write_case["filename"], api_function_name=write_case["endpoint"]
        )
        assert "persisted" not in caplog.text  # An exception must never claim persistence.
        assert " exported " not in caplog.text  # An exception must never claim export success.
