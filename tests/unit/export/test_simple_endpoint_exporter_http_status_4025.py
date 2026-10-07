"""HTTP status handling tests for the simple endpoint exporter (issue #4025).

Issue #4025 reports that menus 260 and 261 return HTTP 404 for
``getOrgApplicationList`` and ``listSiteApps``. Measurement showed the SDK route
is correct and the 404 comes from the Mist cloud. The defect is that
``SimpleEndpointExporter._run`` never reads ``response.status_code``, so the
Mist SDK error body becomes an empty row list and the operator reads
``! No <operation> data found``. That wording is the same text a genuine empty
organization produces, so an upstream failure is indistinguishable from a real
empty result.

These tests prove the two cases stay distinct. A real empty success keeps the
no-data wording. A non-2xx status produces an error line that names the status
and the URL, writes nothing, and never claims the endpoint had no data.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.operations.exporting.export.simple_endpoint_exporter import (
    SimpleEndpointExporter,
    _SimpleEndpointOp,
)

# The two operations issue #4025 names. Both are real, published SDK routes.
ORG_APPLICATION_LIST = _SimpleEndpointOp("getOrgApplicationList", "mistapi.api.v1.orgs.wxtags")
SITE_APPS = _SimpleEndpointOp("listSiteApps", "mistapi.api.v1.sites.apps")


def _fake_mist_helper() -> Any:
    """Build a MistHelper stand-in that records exporter calls."""
    module = MagicMock()  # The exporter reads apisession and DataExporter from this resolver.
    module.apisession = MagicMock()  # The SDK call receives this session object.
    return module


class _StubResponse:
    """Stand in for a mistapi APIResponse without raising on an error status.

    The real ``mistapi.__api_response.APIResponse`` stores the parsed error body
    in ``data`` and records the status code. It does not raise for a 4xx or a
    5xx answer, so the exporter must read the status itself.
    """

    def __init__(self, status_code: int | None, data: Any, url: str) -> None:
        """Record the fields the exporter and the SDK pagination helper read."""
        self.status_code = status_code  # The HTTP status the exporter must inspect.
        self.data = data  # The parsed JSON body, which holds an error for a 4xx answer.
        self.url = url  # The request URL, so an error line can name the failed path.
        self.next: str | None = None  # No further page exists for an error or a single page.
        self.raw_data = ""  # The SDK keeps the unparsed body, which these tests do not use.
        self.headers: dict[str, str] = {}  # The SDK records response headers.
        self.proxy_error = False  # A proxy failure is a separate SDK condition.


def _run_with_response(operation: _SimpleEndpointOp, response: Any, identifier: str, label: str) -> Any:
    """Execute one exporter operation against a stubbed SDK response."""
    fake = _fake_mist_helper()  # Build the resolver stand-in for this one run.
    callable_obj = MagicMock(return_value=response)  # The SDK function returns the stubbed response.
    with (
        patch("src.operations.exporting.export.simple_endpoint_exporter.SourceDependencyResolver", fake),
        patch.object(SimpleEndpointExporter, "_resolve", return_value=callable_obj),
    ):
        SimpleEndpointExporter._run(operation, identifier, label)  # Drive the real production path.
    return fake  # Return the resolver so a caller can read the exporter calls.


def test_run_logs_an_error_line_for_a_404_response(caplog: pytest.LogCaptureFixture) -> None:
    """A 404 answer must produce an operator-visible error line."""
    response = _StubResponse(404, {"detail": "Not Found"}, "/api/v1/orgs/org-one/wxtags/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert "Error fetching getOrgApplicationList" in caplog.text


def test_run_names_the_status_code_for_a_404_response(caplog: pytest.LogCaptureFixture) -> None:
    """The error line must name the status, so the operator can act on it."""
    response = _StubResponse(404, {"detail": "Not Found"}, "/api/v1/orgs/org-one/wxtags/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert "HTTP 404" in caplog.text


def test_run_names_the_url_for_a_404_response(caplog: pytest.LogCaptureFixture) -> None:
    """The error line must name the failed path, so the operator can verify it."""
    response = _StubResponse(404, {"detail": "Not Found"}, "/api/v1/orgs/org-one/wxtags/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert "/api/v1/orgs/org-one/wxtags/apps" in caplog.text


def test_run_does_not_claim_no_data_for_a_404_response(caplog: pytest.LogCaptureFixture) -> None:
    """A 404 must never read as a genuine empty result."""
    response = _StubResponse(404, {"detail": "Not Found"}, "/api/v1/orgs/org-one/wxtags/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert "No getOrgApplicationList data found" not in caplog.text


def test_run_writes_no_rows_for_a_404_response() -> None:
    """A 404 must not create an export file."""
    response = _StubResponse(404, {"detail": "Not Found"}, "/api/v1/orgs/org-one/wxtags/apps")
    fake = _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert fake.DataExporter.write_with_format_selection.call_count == 0


def test_run_logs_an_error_line_for_a_site_404_response(caplog: pytest.LogCaptureFixture) -> None:
    """Menu 261 must report the site endpoint failure the same way."""
    response = _StubResponse(404, {"detail": "Not Found"}, "/api/v1/sites/site-one/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(SITE_APPS, response, "site-one", "Site One")
    assert "Error fetching listSiteApps" in caplog.text


def test_run_does_not_claim_no_data_for_a_site_404_response(caplog: pytest.LogCaptureFixture) -> None:
    """Menu 261 must not present the site 404 as an empty site."""
    response = _StubResponse(404, {"detail": "Not Found"}, "/api/v1/sites/site-one/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(SITE_APPS, response, "site-one", "Site One")
    assert "No listSiteApps data found" not in caplog.text


def test_run_logs_an_error_line_for_a_500_response(caplog: pytest.LogCaptureFixture) -> None:
    """A server failure must report as an error, not as an empty result."""
    response = _StubResponse(500, {"detail": "Internal Server Error"}, "/api/v1/sites/site-one/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(SITE_APPS, response, "site-one", "Site One")
    assert "HTTP 500" in caplog.text


def test_run_reports_no_data_for_an_empty_successful_response(caplog: pytest.LogCaptureFixture) -> None:
    """A real empty 200 answer must keep the established no-data wording."""
    response = _StubResponse(200, [], "/api/v1/orgs/org-one/wxtags/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert "No getOrgApplicationList data found" in caplog.text


def test_run_logs_no_error_line_for_an_empty_successful_response(caplog: pytest.LogCaptureFixture) -> None:
    """A real empty 200 answer must not report a failure."""
    response = _StubResponse(200, [], "/api/v1/orgs/org-one/wxtags/apps")
    with caplog.at_level(logging.INFO):
        _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert "Error fetching" not in caplog.text


def test_run_persists_rows_for_a_successful_response() -> None:
    """A 200 answer with rows must still reach the shared exporter."""
    response = _StubResponse(200, [{"name": "zoom"}], "/api/v1/orgs/org-one/wxtags/apps")
    fake = _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert fake.DataExporter.write_with_format_selection.call_count == 1


def test_run_persists_rows_when_the_response_reports_no_status() -> None:
    """A response object without a usable status must not block the export."""
    response = _StubResponse(None, [{"name": "zoom"}], "/api/v1/orgs/org-one/wxtags/apps")
    fake = _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert fake.DataExporter.write_with_format_selection.call_count == 1


def test_run_persists_rows_for_a_mock_response_without_an_integer_status() -> None:
    """A test double whose status is not a whole number must not read as a failure."""
    response = MagicMock()  # A bare mock reports a MagicMock status, not an int.
    response.data = [{"name": "zoom"}]  # Give the mock a real page of rows to persist.
    response.next = None  # Stop the SDK pagination helper after the first page.
    fake = _run_with_response(ORG_APPLICATION_LIST, response, "org-one", "org-one")
    assert fake.DataExporter.write_with_format_selection.call_count == 1
