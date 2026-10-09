"""Tests for the shared SDK HTTP response status gate."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from src.operations.exporting.export.endpoint_family_exporter import (
    _SITE_DETAIL_OPS,
    EndpointFamilyExporter,
)
from src.operations.exporting.export.http_response_status import http_failure


def test_missing_status_keeps_the_existing_path(caplog: pytest.LogCaptureFixture) -> None:
    """A response without a status must keep compatibility with existing response doubles."""
    response = object()
    with caplog.at_level(logging.DEBUG):
        assert http_failure(response, "getSelf") is False
    assert "no integer status" in caplog.text


def test_magicmock_status_keeps_the_existing_path(caplog: pytest.LogCaptureFixture) -> None:
    """A non-integer mock status must not enter numeric comparison."""
    response = MagicMock()
    with caplog.at_level(logging.DEBUG):
        assert http_failure(response, "getSelf") is False
    assert "no integer status" in caplog.text


@pytest.mark.parametrize("status_code", [200, 204, 299])
def test_success_status_keeps_the_existing_path(status_code: int) -> None:
    """Every 2xx status proves that the exporter may inspect the payload."""
    response = MagicMock(status_code=status_code)
    assert http_failure(response, "exportSiteDevices") is False


@pytest.mark.parametrize("status_code", [301, 400, 404, 503])
def test_non_success_status_reports_the_endpoint(status_code: int, caplog: pytest.LogCaptureFixture) -> None:
    """A non-2xx status must stop payload interpretation and name the request path."""
    response = MagicMock(status_code=status_code, url="/api/v1/sites/site-one/devices")
    with caplog.at_level(logging.DEBUG):
        assert http_failure(response, "exportSiteDevices") is True
    assert f"! Error fetching exportSiteDevices: HTTP {status_code} from /api/v1/sites/site-one/devices" in caplog.text


def test_error_body_without_results_is_not_an_empty_success(caplog: pytest.LogCaptureFixture) -> None:
    """An HTTP error body without results must use the failure wording."""
    response = MagicMock(
        status_code=401,
        url="/api/v1/sites/site-one/devices",
        data={"detail": "unauthorized"},
    )
    with caplog.at_level(logging.INFO):
        assert http_failure(response, "exportSiteDevices") is True
    assert "no exportSiteDevices data" not in caplog.text.lower()
    assert "Error fetching exportSiteDevices: HTTP 401" in caplog.text


def test_endpoint_family_run_rejects_an_http_error_body_before_empty_result_handling(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A real SDK error response must not become a successful empty export."""
    fake = MagicMock()
    fake.apisession = MagicMock()
    response = MagicMock(
        status_code=401,
        url="/api/v1/sites/site-one/devices",
        data={"detail": "unauthorized"},
    )
    callable_obj = MagicMock(return_value=response)
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch.object(EndpointFamilyExporter, "_resolve", return_value=callable_obj),
        patch.object(
            EndpointFamilyExporter,
            "_collect_arguments",
            return_value=MagicMock(values=("site-one",), label="site-one"),
        ),
        patch("src.operations.exporting.export.endpoint_family_exporter.mistapi.get_all") as get_all,
        caplog.at_level(logging.INFO),
    ):
        get_all.return_value = response.data
        EndpointFamilyExporter._run(_SITE_DETAIL_OPS[0])
    get_all.assert_not_called()
    fake.DataExporter.write_with_format_selection.assert_not_called()
    assert "Error fetching exportSiteDevices: HTTP 401" in caplog.text
