"""Native mistapi response regression tests for WiFi client export."""

from __future__ import annotations  # WHY: keep annotations compatible with the project typing configuration.

import json  # WHY: construct the native SDK parse failure that the exporter must detect.
from unittest.mock import MagicMock  # WHY: isolate endpoint and pagination calls.

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
    mistapi_module.get_all.assert_not_called()  # WHY: rejected responses must never reach pagination.


def test_native_valid_empty_wifi_response_reaches_pagination() -> None:
    """A native empty JSON result must retain the existing empty-result path."""
    response = _native_response(200, "[]", [])  # WHY: model a valid empty answer from the real SDK.
    exporter, endpoint, mistapi_module = _build_exporter(response)  # WHY: isolate the production fetch seam.
    mistapi_module.get_all.return_value = []  # WHY: pagination resolves the valid empty page to no rows.

    results = exporter._fetch_paginated(endpoint, "site-1", "wireless clients")  # WHY: exercise the response guard.

    assert results == []  # WHY: valid empty data remains an empty result, not a failure.
    mistapi_module.get_all.assert_called_once_with(  # WHY: pagination remains active.
        response=response,
        mist_session=exporter.apisession,
    )
