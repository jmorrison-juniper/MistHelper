"""Native mistapi response regression tests for WiFi client export."""

from __future__ import annotations  # WHY: keep annotations compatible with the project typing configuration.

import json  # WHY: construct the native SDK parse failure that the exporter must detect.
from pathlib import Path  # WHY: annotate temporary paths used by end-to-end exporter tests.
from unittest.mock import MagicMock  # WHY: isolate endpoint and pagination calls.

import mistapi  # WHY: exercise the installed SDK page method without live requests.
import pytest  # WHY: parameterize native empty and failed HTTP responses.
from mistapi.__api_response import APIResponse  # WHY: verify the actual SDK response shape.

from src.operations.exporting.export.wifi_clients_exporter import (
    WifiClientsExporter,  # WHY: exercise the production response boundary.
)


def _native_response(status_code: int, body: str, parsed_body: object) -> APIResponse:
    """Build a native mistapi response without a live HTTP request."""
    transport = MagicMock()  # WHY: provide only the requests.Response fields APIResponse reads.
    transport.status_code = status_code  # WHY: preserve the controlled HTTP result.
    transport.text = body  # WHY: preserve the raw body used by response-integrity checks.
    transport.headers = {}  # WHY: satisfy native pagination-header access.
    transport.url = "https://api.mist.com/api/v1/sites/site-1/clients"  # WHY: provide a valid API URL shape.
    if isinstance(parsed_body, BaseException):  # WHY: make malformed JSON follow the SDK swallowed-error path.
        transport.json.side_effect = parsed_body  # WHY: APIResponse catches the parse exception internally.
    else:
        transport.json.return_value = parsed_body  # WHY: preserve valid JSON or native error payload parsing.
    return APIResponse(response=transport, url=transport.url)  # WHY: construct the real SDK response object.


def _build_exporter(response: APIResponse) -> tuple[WifiClientsExporter, MagicMock, MagicMock]:
    """Build an exporter whose first endpoint returns the native response."""
    mistapi_module = MagicMock()  # WHY: isolate pagination and API module calls.
    endpoint = MagicMock(return_value=response)  # WHY: inject the native response at the production boundary.
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClients = endpoint  # WHY: bind the first WiFi endpoint.
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions = (
        MagicMock()
    )  # WHY: keep the second endpoint inert.
    exporter = WifiClientsExporter(
        cache_utils=MagicMock(),  # WHY: no cache behavior is needed for this boundary test.
        org_site_exporter=MagicMock(),  # WHY: no organization lookup is needed for this boundary test.
        prompt_utils=MagicMock(),  # WHY: the test invokes the private fetch seam directly.
        file_path_utils=MagicMock(),  # WHY: no filesystem output is needed for this boundary test.
        data_processing_utils=MagicMock(),  # WHY: no records reach processing after rejection.
        data_exporter=MagicMock(),  # WHY: no output backend call is expected.
        mistapi_module=mistapi_module,  # WHY: inject the controlled SDK module.
        apisession=MagicMock(),  # WHY: no live authenticated session is needed.
    )
    return exporter, endpoint, mistapi_module


class _ControlledSession:
    """Return one controlled native page or raise a transport error for the SDK page method."""

    def __init__(self, answer: APIResponse | BaseException) -> None:
        """Store the one planned later-page outcome."""
        self.answer = answer  # WHY: the session returns or raises only the selected offline outcome.
        self.links: list[str] = []  # WHY: tests verify that the SDK requested the page link once.

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> APIResponse:
        """Record the SDK page link, then return the controlled response or raise its failure."""
        self.links.append(uri)  # WHY: prove the actual SDK page method used the native next link.
        if query:  # WHY: a page link carries its query string.
            raise AssertionError("The SDK must not pass a separate query for a page link.")
        if isinstance(self.answer, BaseException):  # WHY: model transport failures without opening a socket.
            raise self.answer  # WHY: make the SDK page method observe the planned failure.
        return self.answer  # WHY: return the native response for later-page validation.


@pytest.mark.parametrize(
    ("status_code", "body", "parsed_body", "expected_text"),
    [
        (200, "", json.JSONDecodeError("empty", "", 0), "empty body"),  # WHY: reproduce HTTP 200 with no body.
        (  # WHY: reproduce a malformed JSON body.
            200,
            "not JSON",
            json.JSONDecodeError("malformed", "not JSON", 0),
            "did not parse",
        ),
        (403, '{"error":"denied"}', {"error": "denied"}, "HTTP 403"),  # WHY: reproduce a refused request.
        (503, '{"error":"down"}', {"error": "down"}, "HTTP 503"),  # WHY: reproduce a service failure.
    ],
)
def test_native_wifi_response_failure_is_rejected(
    status_code: int,
    body: str,
    parsed_body: object,
    expected_text: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The exporter must reject every native response that cannot prove valid WiFi data."""
    response = _native_response(status_code, body, parsed_body)  # WHY: use the real mistapi response parser.
    exporter, endpoint, mistapi_module = _build_exporter(response)  # WHY: isolate the production fetch seam.

    with caplog.at_level("ERROR"), pytest.raises((RuntimeError, ValueError)):
        exporter._fetch_paginated(endpoint, "site-1", "wireless clients")  # WHY: validate before SDK pagination.

    assert any(expected_text in record.getMessage() for record in caplog.records)  # WHY: preserve failure evidence.
    mistapi_module.get_next.assert_not_called()  # WHY: rejected first pages must never reach pagination.


def test_native_valid_empty_wifi_response_reaches_pagination() -> None:
    """A native empty JSON result must retain the existing empty-result path."""
    response = _native_response(200, "[]", [])  # WHY: model a valid empty answer from the real SDK.
    exporter, endpoint, mistapi_module = _build_exporter(response)  # WHY: isolate the production fetch seam.

    results = exporter._fetch_paginated(endpoint, "site-1", "wireless clients")  # WHY: exercise the response guard.

    assert results.records == []  # WHY: valid empty data remains an empty result, not a failure.
    assert not results.is_partial  # WHY: a single successful empty page is complete.
    mistapi_module.get_next.assert_not_called()  # WHY: a response without a next link needs no further request.


@pytest.mark.parametrize("status_code", [403, 503])
def test_native_later_http_failure_is_rejected(
    status_code: int,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A later native HTTP error cannot produce a complete or valid-empty WiFi export."""
    first = _native_response(  # WHY: provide one successful page that links to the controlled later page.
        200,
        json.dumps({"results": [{"mac": "aa:bb"}], "next": "/api/v1/sites/site-1/clients?page=2"}),
        {"results": [{"mac": "aa:bb"}], "next": "/api/v1/sites/site-1/clients?page=2"},
    )
    later = _native_response(
        status_code,
        '{"error":"controlled-secret-sentinel"}',
        {"error": "controlled-secret-sentinel"},
    )  # WHY: model a native HTTP error page without a live cloud request.
    exporter, endpoint, mistapi_module = _build_exporter(first)  # WHY: keep endpoint calls offline and explicit.
    session = _ControlledSession(later)  # WHY: route the SDK request to the planned failed page.
    exporter.apisession = session  # WHY: preserve the session reference used by both endpoint and SDK calls.
    mistapi_module.get_next = mistapi.get_next  # WHY: exercise the real SDK's authenticated page dispatch.
    site_list_path = tmp_path / "SiteList.csv"  # WHY: satisfy the real export entry point without cloud data.
    site_list_path.write_text("id,name\nsite-1,Lab Site\n", encoding="utf-8")  # WHY: keep site lookup local.
    output_path = tmp_path / "SiteWiFiClients.CSV"  # WHY: detect success-shaped output.
    exporter.file_path_utils.get_csv_path.side_effect = [
        str(site_list_path),
        str(output_path),
    ]  # WHY: separate the SiteList lookup path from the forbidden output path.

    with caplog.at_level("ERROR"):
        exporter.execute(site_id="site-1")  # WHY: exercise the top-level failure and output path.

    assert not output_path.exists()  # WHY: a failed later page must not create placeholder output.
    exporter.data_exporter.write_with_format_selection.assert_not_called()  # WHY: no success-shaped backend output.
    assert any(  # WHY: preserve the failed HTTP status in the operator-visible error.
        f"HTTP {status_code}" in record.getMessage() for record in caplog.records
    )
    assert "controlled-secret-sentinel" not in caplog.text  # WHY: response bodies must not leak into logs.
    assert endpoint.call_count == 1  # WHY: reject the failed page before requesting another first page.
    assert session.links == ["/api/v1/sites/site-1/clients?page=2"]  # WHY: the SDK followed only the planned link.


def test_native_later_timeout_exports_retained_rows_as_partial(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A later native SDK timeout retains earlier rows and reports a partial export."""
    first = _native_response(  # WHY: provide one successful client page with a later-page link.
        200,
        json.dumps({"results": [{"mac": "aa:bb"}], "next": "/api/v1/sites/site-1/clients?page=2"}),
        {"results": [{"mac": "aa:bb"}], "next": "/api/v1/sites/site-1/clients?page=2"},
    )
    exporter, endpoint, mistapi_module = _build_exporter(first)  # WHY: keep the endpoint request offline.
    timeout_detail = "controlled-secret-sentinel"  # WHY: detect accidental logging of a transport detail.
    session = _ControlledSession(TimeoutError(timeout_detail))  # WHY: stop only the later page.
    exporter.apisession = session  # WHY: give the SDK its offline controlled session.
    mistapi_module.get_next = mistapi.get_next  # WHY: exercise actual SDK page dispatch with the controlled session.
    empty_sessions = _native_response(200, "[]", [])  # WHY: complete the companion dataset with a valid empty page.
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions.return_value = empty_sessions
    site_list_path = tmp_path / "SiteList.csv"  # WHY: satisfy the real export entry point without cloud data.
    site_list_path.write_text("id,name\nsite-1,Lab Site\n", encoding="utf-8")  # WHY: keep site lookup local.
    exporter.file_path_utils.get_csv_path.return_value = str(site_list_path)
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda rows: rows
    exporter.data_processing_utils.escape_multiline.side_effect = lambda rows: rows

    with caplog.at_level("WARNING"):
        exporter.execute(site_id="site-1")  # WHY: verify the complete pipeline retains the first page.

    exporter.data_exporter.write_with_format_selection.assert_called_once()
    written_rows = exporter.data_exporter.write_with_format_selection.call_args.args[0]
    assert any(row.get("mac") == "aa:bb" for row in written_rows)  # WHY: prove the first-page record was retained.
    assert "WiFi data partially exported" in caplog.text  # WHY: the operator must not see a complete-success notice.
    assert "WiFi data exported to" not in caplog.text  # WHY: partial output must not carry the full-success label.
    assert timeout_detail not in caplog.text  # WHY: transport exception details can contain credentials.
    assert endpoint.call_count == 1  # WHY: one first-page endpoint call starts this sequence.
    assert session.links == ["/api/v1/sites/site-1/clients?page=2"]  # WHY: the SDK followed only the planned link.
