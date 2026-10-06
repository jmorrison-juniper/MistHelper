"""Prove authentication and required storage refusals stop before service work."""

from __future__ import annotations  # Keep annotations independent from import order.

from unittest.mock import Mock  # Count forbidden cancellation calls.

import pytest  # The test runner restores every fake boundary.

from src.interfaces.portals.upgrade_portal.runtime import identity  # Use the real registry and cookie checks.
from tests.integration.upgrade_portal.issue_3834.test_default_provider import ProviderDoubles

CAPTURE_BODY = {  # A valid request reaches dependency resolution before capture work.
    "device_ids": ["001122334455"],
    "org_id": "00000000-0000-0000-0000-0000000000aa",
    "site_id": "00000000-0000-0000-0000-0000000000bb",
}


def test_missing_owner_is_refused_before_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unsigned request cannot open a store or reach a Mist method."""
    harness = ProviderDoubles()  # Track every production-boundary substitute.
    harness.install(monkeypatch)  # The fakes remain idle when authentication fails.
    application = harness.create_app()  # Normal startup stores provider rules only.
    client = application.test_client()  # One browser holds the CSRF session token.
    token = client.get("/_test/csrf-token").get_json()["token"]  # The real CSRF extension signs this value.
    response = client.post(
        "/api/runs/run-3834/capture/start",
        json=CAPTURE_BODY,
        headers={"X-CSRFToken": token},
    )  # The endpoint guard runs before request dependency construction.
    assert response.status_code == 401  # Missing identity keeps the established refusal status.
    assert harness.clients == []  # Authentication failure opens no document client.
    assert harness.sessions == []  # Authentication failure makes no cloud call.


def test_missing_cloud_session_is_refused_before_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """A registry record without a usable cloud session receives an auth refusal."""
    harness = ProviderDoubles()  # Keep all external resources fake.
    harness.install(monkeypatch)  # Standalone production storage remains unreachable.
    application = harness.create_app()  # The factory does not construct request dependencies.
    client, owner = harness.signed_client(application, "operator.two@example.invalid")
    record = identity.SESSION_REGISTRY.get(owner.key)  # Resolve the real registered operator record.
    assert record is not None  # The helper registered this owner in the process registry.
    record.cloud_session = None  # Model a stale registry record without an SDK session.
    token = client.get("/_test/csrf-token").get_json()["token"]  # Preserve the active CSRF guard.
    try:  # Remove the fake operator record after the route response.
        response = client.post(
            "/api/runs/run-3834/capture/start",
            json=CAPTURE_BODY,
            headers={"X-CSRFToken": token},
        )
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # The process registry outlives the test client.
    assert response.status_code == 401  # The provider refuses before a storage constructor runs.
    assert harness.clients == []  # No database handle exists for an unauthenticated request.


def test_standalone_storage_returns_503_before_cloud_work(monkeypatch: pytest.MonkeyPatch) -> None:
    """A CSV-only configuration cannot support the required durable capture."""
    harness = ProviderDoubles()  # Count the constructors and session methods.
    harness.install(monkeypatch, standalone=True)  # The config reader reports standalone storage.
    application = harness.create_app()  # Default startup still opens no service dependency.
    client, owner = harness.signed_client(application, "operator.three@example.invalid")
    token = client.get("/_test/csrf-token").get_json()["token"]  # The storage refusal follows CSRF validation.
    try:  # Exercise the registered route with a real signed browser session.
        response = client.post(
            "/api/runs/run-3834/capture/start",
            json=CAPTURE_BODY,
            headers={"X-CSRFToken": token},
        )
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # The process registry outlives the test client.
    assert response.status_code == 503  # Required storage refuses service work.
    assert harness.clients == []  # Standalone mode stops before opening ArangoDB.
    assert harness.sessions[0].get.call_count == 0  # Storage refusal makes no Mist read.
    assert harness.sessions[0].post.call_count == 0  # Storage refusal makes no Mist mutation.
    assert b"fake-arango-password" not in response.data  # Configuration text never reaches the operator.


def test_csrf_refusal_stops_before_provider_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing CSRF token cannot construct a service graph."""
    harness = ProviderDoubles()  # Count every fake production resource.
    harness.install(monkeypatch)  # Only fake storage boundaries can open.
    application = harness.create_app()  # The production CSRF policy stays enabled.
    client, owner = harness.signed_client(application, "operator.four@example.invalid")
    try:  # Omit the token deliberately to exercise the real CSRF refusal.
        response = client.post("/api/runs/run-3834/capture/start", json=CAPTURE_BODY)
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # Remove the signed owner after the request.
    assert response.status_code == 400  # CSRF refuses before the service route runs.
    assert harness.clients == []  # The refused request opens no document store.


def test_upgrade_cancel_refuses_a_run_without_verified_operation_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    """The registered cancel service sends no SDK request for a run without cloud IDs."""
    import mistapi.api.v1.sites.devices as devices_api  # The only site cancellation endpoint.

    harness = ProviderDoubles()  # Track every request-owned resource.
    harness.install(monkeypatch)  # The request cannot reach a production store.
    application = harness.create_app()
    client, owner = harness.signed_client(application, "operator.six@corp.local")
    cancel_call = Mock(name="cancelSiteDeviceUpgrade")  # The run has no operation to cancel.
    monkeypatch.setattr(devices_api, "cancelSiteDeviceUpgrade", cancel_call)
    csrf = client.get("/_test/csrf-token").get_json()["token"]  # Keep the production CSRF check active.
    try:  # Remove the registered owner after the refusal.
        response = client.post(
            "/api/runs/run-without-cloud-id/upgrade/cancel",
            json={"confirm": "STOP"},
            headers={"X-CSRFToken": csrf},
        )
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test client.
    assert response.status_code == 500  # The service reports that no verified cancel occurred.
    cancel_call.assert_not_called()  # No stored cloud ID means no Mist cancellation call.
