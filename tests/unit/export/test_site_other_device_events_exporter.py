"""Tests for the site other-device event exporter."""

from __future__ import annotations  # WHY: keep annotations compatible with the project target.

import json  # WHY: encode synthetic HTTP responses without a cloud request.
import logging  # WHY: capture operator messages and private-text leaks.
import socket  # WHY: block DNS and sockets even when a mock is missing.
from typing import Any  # WHY: type the test stand-in without binding to MistHelper internals.
from unittest.mock import MagicMock, patch  # WHY: isolate the test from Mist Cloud and disk.

import mistapi  # WHY: patch the SDK operation and pagination helper.
import pytest  # WHY: exercise failure boundaries and offline fixtures.
import requests  # WHY: construct real response objects for the installed SDK.
from mistapi.__api_request import (
    APIRequest,  # WHY: inspect the real request contract without session credential loading.
)
from mistapi.__api_response import APIResponse  # WHY: status-aware doubles must use the actual SDK response type.

from src.foundation.support.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from src.operations.exporting.export import site_other_device_events_exporter as exporter_module
from src.operations.exporting.export.site_other_device_events_exporter import SiteOtherDeviceEventsExporter


@pytest.fixture(autouse=True)
def offline_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent any test from reaching DNS or a network socket."""
    for name in ("socket", "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex"):
        monkeypatch.setattr(
            socket, name, MagicMock(side_effect=AssertionError("Network access is forbidden"))
        )  # WHY: a missing request mock must fail before any external access.


@pytest.fixture
def menu(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Provide a selected site and a writer that cannot touch storage."""
    helper = _fake_mist_helper()  # WHY: isolate menu dependencies from the CLI.
    helper.SiteDeviceExporter._resolve_site_for_stats.return_value = (
        "site-1",
        "Branch",
    )  # WHY: select a synthetic site.
    monkeypatch.setattr(exporter_module, "SourceDependencyResolver", helper)  # WHY: keep output in a mock.
    return helper  # WHY: let each scenario inspect its writer and selection.


@pytest.fixture
def sdk_result(monkeypatch: pytest.MonkeyPatch) -> tuple[MagicMock, MagicMock]:
    """Replace endpoint and pagination results for boundary tests."""
    search = MagicMock(
        return_value=APIResponse(
            _http_response(200, {"results": [{"mac": "aa:bb", "timestamp": 1}], "next": "/next"}),
            "https://api.invalid/events",
        )
    )  # WHY: a real first response must prove success before the next request.
    paginate = MagicMock(
        return_value=APIResponse(_http_response(200, {"results": []}), "https://api.invalid/next")
    )  # WHY: finish pagination without adding synthetic extra records.
    monkeypatch.setattr(
        mistapi.api.v1.sites.otherdevices, "searchSiteOtherDeviceEvents", search
    )  # WHY: avoid cloud calls.
    monkeypatch.setattr(mistapi, "get_next", paginate)  # WHY: control the status-visible page boundary.
    return search, paginate  # WHY: expose both external-call boundaries.


@pytest.fixture
def transport(menu: Any, monkeypatch: pytest.MonkeyPatch) -> APIRequest:
    """Use the installed SDK with a mocked HTTP session and no credentials."""
    session = APIRequest()  # WHY: avoid APISession environment and credential loading.
    session._cloud_uri = "api.invalid"  # WHY: identify synthetic URLs without a real endpoint.
    session._session = MagicMock()  # WHY: replace HTTP, not the SDK behavior under test.
    session._session.proxies = {}  # WHY: prevent irrelevant proxy output.
    menu.apisession = session  # WHY: exercise the endpoint and pagination with the real request implementation.
    for module_name in ("mistapi.__api_request", "mistapi.__api_response"):
        monkeypatch.setattr(
            f"{module_name}.logger", MagicMock()
        )  # WHY: isolate third-party logging outside this slice.
    return session  # WHY: allow tests to supply first and subsequent HTTP results.


def _http_response(
    status: int, data: dict[str, Any] | list[Any] | None, headers: dict[str, str] | None = None
) -> requests.Response:
    """Build a real response with synthetic JSON and no authenticated request."""
    response = requests.Response()  # WHY: exercise SDK status and decoding behavior.
    response.status_code = status  # WHY: preserve HTTP success and failure semantics.
    response._content = b"" if data is None else json.dumps(data).encode("ascii")  # WHY: include empty-body failures.
    response.headers.update(headers or {})  # WHY: let real SDK headers identify subsequent list pages.
    response.request = requests.Request(
        "GET", "https://api.invalid/events"
    ).prepare()  # WHY: supply SDK header metadata.
    return response  # WHY: let the real SDK process this response.


def _fake_mist_helper() -> Any:
    """Return the collaborators used by the exporter."""
    module = MagicMock()  # WHY: provide the shared helpers without importing the CLI entrypoint.
    module.apisession = MagicMock()  # WHY: verify the SDK receives the authenticated session.
    return module  # WHY: let each test patch the lazy import with one stand-in.


def test_primary_key_strategy_uses_mac_and_timestamp() -> None:
    """The endpoint has a stable composite event key for repeatable upserts."""
    strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchSiteOtherDeviceEvents"]  # WHY: read the endpoint catalog entry.
    assert strategy["type"] == "composite_pk"  # WHY: event rows need a multi-field key.
    assert strategy["primary_key"] == ["mac", "timestamp"]  # WHY: prevent duplicate rows on repeat runs.


def test_empty_results_do_not_write_an_export(caplog: pytest.LogCaptureFixture) -> None:
    """An empty response reports no data and skips the writer."""
    fake_mh = _fake_mist_helper()  # WHY: provide the lazy module dependency.
    with (
        caplog.at_level(logging.INFO),
        patch("src.operations.exporting.export.site_other_device_events_exporter.SourceDependencyResolver", fake_mh),
    ):  # WHY: isolate the persistence helper.
        SiteOtherDeviceEventsExporter._persist_events([], "Branch")  # WHY: exercise the empty-response branch.
    fake_mh.DataExporter.write_with_format_selection.assert_not_called()  # WHY: empty responses need no file.
    assert "No other-device event data" in caplog.text  # WHY: explain why the empty response has no output.


def test_persistence_routes_flattened_rows_and_operation_name() -> None:
    """Non-empty results use the shared writer and operationId."""
    fake_mh = _fake_mist_helper()  # WHY: capture the write call without touching disk.
    rows = [{"mac": "aa:bb", "metadata": {"vendor": "Juniper"}}]  # WHY: exercise nested-field flattening.
    with patch(
        "src.operations.exporting.export.site_other_device_events_exporter.SourceDependencyResolver", fake_mh
    ):  # WHY: isolate MistHelper imports.
        SiteOtherDeviceEventsExporter._persist_events(rows, "Head Office")  # WHY: write one representative site export.
    args, kwargs = fake_mh.DataExporter.write_with_format_selection.call_args  # WHY: inspect the writer contract.
    assert args[1] == "SiteOtherDeviceEvents_Head_Office.csv"  # WHY: spaces must not reach the filename.
    assert kwargs["api_function_name"] == "searchSiteOtherDeviceEvents"  # WHY: select the endpoint PK strategy.
    assert args[0][0]["metadata_vendor"] == "Juniper"  # WHY: nested values must become tabular fields.


def test_menu_entry_resolves_site_calls_sdk_and_persists_rows() -> None:
    """The menu entry passes the selected site to the SDK and persistence path."""
    fake_mh = _fake_mist_helper()  # WHY: provide the session and site resolver.
    fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")  # WHY: select one site.
    rows = [{"mac": "aa:bb", "timestamp": "2026-09-09T00:00:00Z"}]  # WHY: represent one API event.
    with (
        patch(
            "src.operations.exporting.export.site_other_device_events_exporter.SourceDependencyResolver", fake_mh
        ),  # WHY: isolate shared CLI globals.
        patch.object(
            mistapi.api.v1.sites.otherdevices,
            "searchSiteOtherDeviceEvents",
            return_value=APIResponse(_http_response(200, {"results": rows}), "https://api.invalid/events"),
        ) as search_spy,  # WHY: avoid Mist Cloud and verify the SDK arguments.
        patch.object(SiteOtherDeviceEventsExporter, "_persist_events") as persist_spy,  # WHY: verify the handoff.
    ):
        SiteOtherDeviceEventsExporter.other_device_events()  # WHY: exercise the complete menu path.
    search_spy.assert_called_once_with(fake_mh.apisession, "site-1")  # WHY: verify SDK arguments.
    persist_spy.assert_called_once_with(rows, "Branch")  # WHY: preserve the rows and friendly site name.


class TestMenuFailureBoundaries:
    """Distinguish remote-call failures from local persistence defects."""

    @staticmethod
    @pytest.mark.parametrize("stage", ["endpoint", "pagination"])
    @pytest.mark.parametrize("exception_type", [RuntimeError, KeyError, TypeError])
    def test_external_failure_returns_without_private_logs(
        menu: Any,
        sdk_result: tuple[MagicMock, MagicMock],
        caplog: pytest.LogCaptureFixture,
        stage: str,
        exception_type: type[Exception],
    ) -> None:
        """External failures retain the menu fallback without arbitrary exception text."""
        failure = exception_type(
            "synthetic-private-token response-body\nprivate-host"
        )  # WHY: expose leaks in text and traceback.
        search, paginate = sdk_result  # WHY: select the failing external stage.
        (search if stage == "endpoint" else paginate).side_effect = failure  # WHY: test both sides of pagination.
        with caplog.at_level(logging.DEBUG):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: the established menu fallback must not raise.
        assert "synthetic-private-token" not in caplog.text  # WHY: protect arbitrary exception text.
        assert "private-host" not in caplog.text  # WHY: protect the complete multiline payload.
        assert "! Error fetching other-device event data" in caplog.text  # WHY: retain operator feedback.
        assert (
            len([record for record in caplog.records if record.levelno == logging.ERROR]) == 1
        )  # WHY: avoid duplicate errors.
        assert all(
            record.exc_info is None for record in caplog.records
        )  # WHY: a traceback can expose the same payload.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: do not write after a request failure.
        if stage == "endpoint":
            paginate.assert_not_called()  # WHY: do not paginate a failed first request.

    @pytest.mark.parametrize("stage", ["flatten", "escape", "writer"])
    def test_local_defect_propagates_without_cloud_error(
        self,
        menu: Any,
        sdk_result: tuple[MagicMock, MagicMock],
        caplog: pytest.LogCaptureFixture,
        stage: str,
    ) -> None:
        """Local defects must not become cloud failure messages."""
        failure = RuntimeError("synthetic-private-local-data")  # WHY: check exception identity and log privacy.
        target, name = {
            "flatten": (exporter_module.DataProcessingUtils, "flatten_nested_fields"),
            "escape": (exporter_module.DataProcessingUtils, "escape_multiline"),
            "writer": (menu.DataExporter, "write_with_format_selection"),
        }[
            stage
        ]  # WHY: exercise each local persistence boundary.
        with (
            patch.object(target, name, side_effect=failure),
            caplog.at_level(logging.DEBUG),
            pytest.raises(RuntimeError) as captured,
        ):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: preserve the original failure for the caller.
        assert captured.value is failure  # WHY: do not replace the local defect with a remote error.
        assert "Error fetching" not in caplog.text  # WHY: avoid a false cloud diagnosis.
        assert "synthetic-private-local-data" not in caplog.text  # WHY: do not leak the defect payload.
        if stage != "writer":
            menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: stop after a failed transform.

    @pytest.mark.parametrize("selected", [True, False])
    def test_empty_or_canceled_menu_does_not_write(
        self,
        menu: Any,
        sdk_result: tuple[MagicMock, MagicMock],
        caplog: pytest.LogCaptureFixture,
        selected: bool,
    ) -> None:
        """Empty results and canceled selection preserve the existing no-output path."""
        search, paginate = sdk_result  # WHY: observe the request boundary.
        search.return_value = APIResponse(
            _http_response(200, {"results": []}), "https://api.invalid/events"
        )  # WHY: represent a valid terminal empty search.
        if not selected:
            menu.SiteDeviceExporter._resolve_site_for_stats.return_value = None  # WHY: represent cancellation.
        with caplog.at_level(logging.INFO):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: exercise the complete menu path.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: neither case has output.
        assert (
            "No other-device event data" in caplog.text
        ) is selected  # WHY: cancellation must not report an empty search.
        assert search.call_count == int(selected)  # WHY: cancellation must not send a request.
        paginate.assert_not_called()  # WHY: cancellation and terminal empty pages must not paginate.


class TestInstalledSdkContract:
    """Exercise the complete installed SDK path without HTTP or credentials."""

    def test_two_successful_pages_reach_the_writer(self, menu: Any, transport: APIRequest) -> None:
        """The real endpoint and pagination helper preserve all successful event rows."""
        transport._session.get.side_effect = [
            _http_response(200, {"results": [{"mac": "aa:bb", "metadata": {"vendor": "Juniper"}}], "next": "/next"}),
            _http_response(200, {"results": [{"mac": "cc:dd", "timestamp": 2}]}),
        ]  # WHY: exercise the real follow-up request and transformation.
        SiteOtherDeviceEventsExporter.other_device_events()  # WHY: verify the SDK-to-writer path.
        menu.DataExporter.write_with_format_selection.assert_called_once_with(
            [{"mac": "aa:bb", "metadata_vendor": "Juniper"}, {"mac": "cc:dd", "timestamp": 2}],
            "SiteOtherDeviceEvents_Branch.csv",
            api_function_name="searchSiteOtherDeviceEvents",
        )  # WHY: preserve row order, normalization, filename, and endpoint metadata.
        assert transport._session.get.call_args_list[0].args == (
            "https://api.invalid/api/v1/sites/site-1/otherdevices/events/search",
        )  # WHY: verify the endpoint uses the selected site.
        assert transport._session.get.call_args_list[1].args == (
            "https://api.invalid/next",
        )  # WHY: verify real pagination.

    def test_malformed_followup_page_retains_fallback(
        self,
        menu: Any,
        transport: APIRequest,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A missing results field cannot produce a complete export."""
        transport._session.get.side_effect = [
            _http_response(200, {"results": [{"mac": "aa:bb"}], "next": "/next"}),
            _http_response(200, {"unexpected": "synthetic-private-response"}),
        ]  # WHY: preserve the malformed-page fallback from issue #1794.
        with caplog.at_level(logging.INFO):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: this remote shape failure must not escape.
        assert transport._session.get.call_count == 2  # WHY: prove the malformed follow-up page was processed.
        assert "! Error fetching other-device event data" in caplog.text  # WHY: preserve menu feedback.
        assert "synthetic-private-response" not in caplog.text  # WHY: protect remote data.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: reject incomplete rows.

    @staticmethod
    @pytest.mark.parametrize("stage", ["endpoint", "pagination"])
    @pytest.mark.parametrize("failure_type", [requests.exceptions.ConnectionError, requests.exceptions.Timeout])
    def test_sdk_consumes_transport_failures(
        menu: Any,
        transport: APIRequest,
        caplog: pytest.LogCaptureFixture,
        stage: str,
        failure_type: type[Exception],
    ) -> None:
        """Real transport failures return to the menu without becoming empty results."""
        failure = failure_type("synthetic-private-transport")  # WHY: test external failures without real credentials.
        responses = (
            [failure]
            if stage == "endpoint"
            else [
                _http_response(200, {"results": [{"mac": "aa:bb"}], "next": "/next"}),
                failure,
            ]
        )  # WHY: exercise failure during either HTTP request.
        transport._session.get.side_effect = responses  # WHY: retain the SDK exception handling under test.
        with caplog.at_level(logging.INFO):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: preserve the menu return for real SDK failures.
        assert transport._session.get.call_count == len(responses)  # WHY: prove the selected request failed.
        assert "synthetic-private-transport" not in caplog.text  # WHY: verify exporter logs do not add private text.
        assert "No other-device event data" not in caplog.text  # WHY: an absent HTTP response cannot prove emptiness.
        assert "! Error fetching other-device event data" in caplog.text  # WHY: report either failed request stage.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: no failed search may write here.

    @pytest.mark.parametrize("status", [403, 503])
    def test_initial_error_status_never_becomes_empty(
        self,
        menu: Any,
        transport: APIRequest,
        caplog: pytest.LogCaptureFixture,
        status: int,
    ) -> None:
        """A failed initial request must report failure without an empty-data message."""
        transport._session.get.return_value = _http_response(
            status, {"error": "synthetic-private-http-body"}
        )  # WHY: use real HTTP errors.
        with caplog.at_level(logging.INFO):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: failed requests must not reach persistence.
        assert transport._session.get.call_count == 1  # WHY: prove the SDK evaluated one error response.
        assert "No other-device event data" not in caplog.text  # WHY: a failed request cannot prove emptiness.
        assert "Error fetching" in caplog.text  # WHY: the operator must know that the export failed.
        assert f"HTTP {status}" in caplog.text  # WHY: preserve useful, safe SDK status information.
        assert "synthetic-private-http-body" not in caplog.text  # WHY: do not expose response text.
        assert "records exported" not in caplog.text  # WHY: never claim completion after a failed page.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: an error dictionary has no rows.

    @pytest.mark.parametrize("data", [[], {"results": []}, [{"mac": "aa:bb"}], {"results": [{"mac": "aa:bb"}]}])
    def test_successful_single_or_empty_page(
        self, menu: Any, transport: APIRequest, caplog: pytest.LogCaptureFixture, data: dict[str, Any] | list[Any]
    ) -> None:
        """Both successful payload shapes retain empty and single-page results."""
        transport._session.get.return_value = _http_response(200, data)  # WHY: real SDK responses carry the status.
        rows = data["results"] if isinstance(data, dict) else data  # WHY: compare both supported event shapes.
        with caplog.at_level(logging.INFO):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: exercise the full SDK-to-writer path.
        assert transport._session.get.call_count == 1  # WHY: a terminal page must not start another request.
        assert "Error fetching" not in caplog.text  # WHY: successful pages must not report failure.
        assert ("No other-device event data" in caplog.text) is (not rows)  # WHY: preserve genuine empty feedback.
        if rows:
            menu.DataExporter.write_with_format_selection.assert_called_once_with(
                rows, "SiteOtherDeviceEvents_Branch.csv", api_function_name="searchSiteOtherDeviceEvents"
            )  # WHY: preserve the output schema and endpoint metadata.
        else:
            menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: no empty output is necessary.


class TestPageStatusValidation:
    """Reject incomplete reads before any writer or completion message."""

    @staticmethod
    @pytest.mark.parametrize("shape", ["list", "results"])
    @pytest.mark.parametrize("failure_data", [None, {"error": "synthetic-private-page-body"}])
    def test_later_503_never_writes_partial_rows(
        menu: Any, transport: APIRequest, caplog: pytest.LogCaptureFixture, shape: str, failure_data: Any
    ) -> None:
        """A failed follow-up page must discard all earlier rows for either page shape."""
        first = (
            _http_response(200, [{"mac": "aa:bb"}], {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"})
            if shape == "list"
            else _http_response(200, {"results": [{"mac": "aa:bb"}], "next": "/next"})
        )  # WHY: cover header-based list paging and link-based search paging.
        transport._session.get.side_effect = [first, _http_response(503, failure_data)]  # WHY: reproduce issue #4709.
        with caplog.at_level(logging.DEBUG):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: failure must return safely without output.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: reject partial output.
        assert transport._session.get.call_count == 2  # WHY: prove the failed follow-up page was requested.
        assert "HTTP 503" in caplog.text  # WHY: report the actual failed status, including empty-body errors.
        assert "Error fetching" in caplog.text  # WHY: preserve operator failure feedback.
        assert "records exported" not in caplog.text  # WHY: do not label partial rows complete.
        assert "No other-device event data" not in caplog.text  # WHY: failure is not an empty result.
        assert "synthetic-private-page-body" not in caplog.text  # WHY: protect arbitrary response content.

    def test_successful_list_pages_preserve_all_rows(self, menu: Any, transport: APIRequest) -> None:
        """The real SDK next-page helper preserves list pagination and record order."""
        transport._session.get.side_effect = [
            _http_response(200, [{"mac": "aa:bb"}], {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"}),
            _http_response(200, [{"mac": "cc:dd"}]),
        ]  # WHY: test the same list path as the partial-export defect.
        SiteOtherDeviceEventsExporter.other_device_events()  # WHY: verify completeness before writing.
        assert transport._session.get.call_count == 2  # WHY: read both pages through the SDK.
        menu.DataExporter.write_with_format_selection.assert_called_once_with(
            [{"mac": "aa:bb"}, {"mac": "cc:dd"}],
            "SiteOtherDeviceEvents_Branch.csv",
            api_function_name="searchSiteOtherDeviceEvents",
        )  # WHY: preserve all successful rows and existing output metadata.

    @pytest.mark.parametrize("data", [None, {}, {"results": None}, {"results": "synthetic-private-malformed"}])
    def test_malformed_success_payload_does_not_write(
        self, menu: Any, transport: APIRequest, caplog: pytest.LogCaptureFixture, data: Any
    ) -> None:
        """A successful status without a valid record list cannot prove completeness."""
        transport._session.get.return_value = _http_response(200, data)  # WHY: test empty and malformed remote bodies.
        with caplog.at_level(logging.INFO):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: preserve sanitized malformed-response reporting.
        assert "Error fetching" in caplog.text  # WHY: a status alone cannot validate a missing page payload.
        assert "No other-device event data" not in caplog.text  # WHY: do not convert malformed data to empty success.
        assert "synthetic-private-malformed" not in caplog.text  # WHY: do not log arbitrary payload data.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: reject malformed output.

    def test_missing_promised_page_does_not_write(
        self, menu: Any, sdk_result: tuple[MagicMock, MagicMock], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A missing next response must discard earlier successful rows."""
        _, paginate = sdk_result  # WHY: keep a real successful first page.
        paginate.return_value = None  # WHY: a missing promised response cannot prove completion.
        with caplog.at_level(logging.INFO):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: do not write after a missing response.
        assert paginate.call_count == 1  # WHY: prove the missing response followed the first page.
        assert "HTTP unavailable" in caplog.text  # WHY: report missing status without a fabricated value.
        assert "Error fetching" in caplog.text  # WHY: the operator must know that pagination failed.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: reject incomplete output.

    @pytest.mark.parametrize("status", [None, True, "synthetic-private-status", 199, 300, 403, 503])
    def test_only_integer_success_status_can_write(
        self, menu: Any, caplog: pytest.LogCaptureFixture, status: Any
    ) -> None:
        """Missing or invalid statuses cannot prove a complete response or leak private fields."""
        response = APIResponse(None, "https://synthetic-private-url.invalid/events")  # WHY: use the native SDK shape.
        response.status_code = status  # WHY: test untrusted status values without an invented success default.
        response.data = [{"mac": "aa:bb"}]  # WHY: records alone cannot prove that the page succeeded.
        with (
            patch.object(mistapi.api.v1.sites.otherdevices, "searchSiteOtherDeviceEvents", return_value=response),
            caplog.at_level(logging.DEBUG),
        ):
            SiteOtherDeviceEventsExporter.other_device_events()  # WHY: validate the native response before any write.
        assert "Error fetching" in caplog.text  # WHY: report the failed response rather than successful rows.
        assert "synthetic-private-status" not in caplog.text  # WHY: never log a non-integer status verbatim.
        assert "synthetic-private-url" not in caplog.text  # WHY: keep response URLs out of error reporting.
        assert all(record.exc_info is None for record in caplog.records)  # WHY: do not expose hidden response data.
        menu.DataExporter.write_with_format_selection.assert_not_called()  # WHY: reject unproven success.
