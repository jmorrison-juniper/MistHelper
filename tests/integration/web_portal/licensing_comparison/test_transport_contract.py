"""Verify the installed Mist SDK and the shared-session transport boundary."""

from inspect import signature
from types import SimpleNamespace
from typing import Any

import pytest

import src.interfaces.portals.licensing_comparison.api as licensing_api
from src.interfaces.portals.licensing_comparison.api import MistApiRequester
from src.interfaces.portals.licensing_comparison.service import LicensingComparisonService, ServiceContext


def test_installed_sdk_exposes_supported_methods_and_page_parameters() -> None:
    """Check the installed Mist SDK methods and explicit inventory pagination."""
    assert callable(licensing_api.self_api.getSelf)  # Require session-profile access.
    assert callable(licensing_api.msp_orgs_api.listMspOrgs)  # Require MSP organization discovery.
    assert callable(licensing_api.licenses_api.getOrgLicensesSummary)  # Require license summary access.
    assert callable(licensing_api.licenses_api.getOrgLicensesBySite)  # Require site license usage.
    assert callable(licensing_api.license_types_api.listLicenseTypes)  # Require catalog bundle metadata.
    parameters = signature(licensing_api.inventory_api.getOrgInventory).parameters  # Inspect the installed SDK.
    assert "limit" in parameters  # Require the explicit page-size argument.
    assert "page" in parameters  # Require the explicit page-number argument.


def test_profile_request_uses_the_supplied_shared_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pass the portal's Mist session object directly to the installed SDK."""
    session = object()  # Use a synthetic session marker instead of credentials.
    seen_sessions: list[object] = []  # Record the SDK argument.
    monkeypatch.setattr(
        licensing_api.self_api,
        "getSelf",
        lambda actual_session: (
            seen_sessions.append(actual_session) or SimpleNamespace(status_code=200, data={"privileges": []}, next=None)
        ),
    )  # Replace the network call with a local response.
    monkeypatch.setattr(
        licensing_api.RateLimitingUtils,
        "get_rate_limited_delay",
        lambda *_arguments: (None, 0.0),
    )  # Disable real waiting during the test.
    service = LicensingComparisonService(ServiceContext(session, "org-1", "Primary", {}))  # Reuse the supplied session.
    choices, errors = service.discover_organizations()  # Read the profile through the SDK boundary.
    assert choices == [{"org_id": "org-1", "name": "Primary", "source": "direct"}]  # Keep configured access.
    assert errors == []  # The synthetic response succeeds.
    assert seen_sessions == [session]  # Pass the identical session object to Mist.


def test_transport_error_does_not_expose_exception_text(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Keep a synthetic token out of route errors and service logs."""
    monkeypatch.setattr(
        licensing_api.RateLimitingUtils,
        "get_rate_limited_delay",
        lambda *_arguments: (None, 0.0),
    )  # Disable real waiting during the test.

    def fail_with_secret() -> Any:
        """Raise a synthetic transport error that contains a secret-like value."""
        raise RuntimeError("access_token=synthetic-secret")  # Test that exception text is not copied to output.

    requester = MistApiRequester(ServiceContext(object(), "org-1", "Primary", {}))  # Use the shared API wrapper.
    result = requester.request("getSelf", "org-1", fail_with_secret)  # Exercise the transport boundary.
    assert result.error == "getSelf could not reach Mist."  # Return a generic operator-facing error.
    assert "synthetic-secret" not in caplog.text  # Do not log the exception text.
    assert "RuntimeError" in caplog.text  # Keep the safe exception type for diagnosis.
