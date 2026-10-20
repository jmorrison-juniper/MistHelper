"""Tests for Mist API source operation verification."""

import logging
from dataclasses import dataclass
from typing import Any

from pytest import LogCaptureFixture

from src.mist.intelligence.reports.org_security_posture.io.sources import OrgSecurityPostureSourceClient


@dataclass(frozen=True)
class MistResponseStub:
    """Small response double for source parsing tests."""

    status_code: int
    data: Any


def test_required_sdk_operations_are_available() -> None:
    results = (
        OrgSecurityPostureSourceClient.verify_sdk_operations()
    )  # Verify source operation bindings without network.
    assert all(results.values())  # Each required operation must exist in the installed SDK.


def test_required_sdk_operation_modules_are_recorded() -> None:
    modules = OrgSecurityPostureSourceClient.REQUIRED_OPERATION_MODULES  # Read the implementation evidence map.
    assert modules["getOrgSettings"] == "mistapi.api.v1.orgs.setting"  # The settings operation lives in this module.
    assert modules["listOrgWebhooks"] == "mistapi.api.v1.orgs.webhooks"  # The webhook operation lives in this module.


def test_4xx_source_response_logs_warning_and_returns_empty_mapping(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)  # Capture the warning that proves the client noticed the HTTP failure.
    response = MistResponseStub(  # Simulate a client error response with a status keyword for quality gates.
        status_code=404,
        data={"password_policy": {"enabled": True}},
    )
    data = OrgSecurityPostureSourceClient._response_data(response)  # Parse the settings response without network.
    assert data == {}  # A failed source read must not provide trusted settings.
    assert "HTTP status 404" in caplog.text  # The warning must name the failed status code.


def test_5xx_source_response_logs_warning_and_returns_empty_list(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)  # Capture the warning that proves the client noticed the HTTP failure.
    response = MistResponseStub(  # Simulate a server error response with a status keyword for quality gates.
        status_code=503,
        data=[{"url": "https://example.invalid/hook"}],
    )
    rows = OrgSecurityPostureSourceClient._response_list(response)  # Parse the list response without network.
    assert rows == []  # A failed source read must not provide trusted rows.
    assert "HTTP status 503" in caplog.text  # The warning must name the failed status code.
