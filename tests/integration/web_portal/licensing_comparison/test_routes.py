"""Test feature route validation with an isolated Flask application."""

from types import SimpleNamespace

import pytest
from flask import Flask

import src.interfaces.portals.licensing_comparison.service as licensing_service
from src.interfaces.portals.licensing_comparison import licensing_comparison_bp


def make_test_app(api_session: object | None) -> Flask:
    """Build a test Flask app without loading shared portal files."""
    app = Flask(__name__)  # Keep route tests separate from the active portal.
    app.config.update(
        TESTING=True,
        SECRET_KEY="route-test-key",
        APISESSION=api_session,
        ORG_ID="org-1",
        ORG_NAME="Primary",
    )  # Supply only test settings.
    app.register_blueprint(licensing_comparison_bp)  # Mount the feature endpoints.
    return app  # Return the isolated app to one route test.


def test_compare_route_rejects_non_object_json() -> None:
    """Return a client error before reading Mist when the body is not an object."""
    app = make_test_app(None)  # Provide no Mist session.
    response = app.test_client().post(
        "/api/license-comparison", data="not-json", content_type="application/json"
    )  # Send malformed JSON to the comparison route.
    assert response.status_code == 400  # Reject malformed input at the route boundary.
    assert response.get_json() == {"error": "The request body must be a JSON object."}  # Return a clear message.


def test_organization_route_reports_a_missing_session() -> None:
    """Return service unavailable when no shared Mist session exists."""
    app = make_test_app(None)  # Model an expired or absent session.
    response = app.test_client().get(
        "/api/license-comparison/organizations"
    )  # Request organizations without a session.
    assert response.status_code == 503  # Report that the service cannot reach Mist.
    assert (
        response.get_json()["errors"][0]["error"] == "The Mist API session is unavailable."
    )  # Keep the cause visible.


def test_organization_route_returns_direct_and_msp_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return organizations from the direct context and granted MSP access."""
    monkeypatch.setattr(
        licensing_service.self_api,
        "getSelf",
        lambda _session: SimpleNamespace(status_code=200, data={"privileges": [{"msp_id": "msp-1"}]}),
    )  # Grant access to one MSP.
    monkeypatch.setattr(
        licensing_service.msp_orgs_api,
        "listMspOrgs",
        lambda _session, _msp_id: SimpleNamespace(status_code=200, data=[{"id": "org-2", "name": "Managed"}]),
    )  # Return the organizations from that grant.
    monkeypatch.setattr(
        licensing_service.RateLimitingUtils,
        "get_rate_limited_delay",
        lambda *_arguments: (None, 0.0),
    )  # Prevent real waiting.
    app = make_test_app(object())  # Give the route a synthetic shared session.
    response = app.test_client().get("/api/license-comparison/organizations")  # Request authorized choices.
    organizations = response.get_json()["organizations"]  # Read the route response.
    assert response.status_code == 200  # The discovery requests succeeded.
    assert [item["org_id"] for item in organizations] == ["org-1", "org-2"]  # Return direct and MSP organizations.


def test_compare_route_rejects_an_unauthorized_organization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject an organization ID that does not come from session access."""
    monkeypatch.setattr(
        licensing_service.self_api,
        "getSelf",
        lambda _session: SimpleNamespace(status_code=200, data={"privileges": []}),
    )  # Expose no MSP grants.
    monkeypatch.setattr(
        licensing_service.RateLimitingUtils,
        "get_rate_limited_delay",
        lambda *_arguments: (None, 0.0),
    )  # Prevent real waiting.
    app = make_test_app(object())  # Give the route one direct organization.
    response = app.test_client().post(
        "/api/license-comparison",
        json={"organization_ids": ["org-2"], "manual_rows": [], "purchased_amounts": {}},
    )  # Submit an organization outside the direct grant.
    assert response.status_code == 403  # Reject the unauthorized comparison.
    assert (
        response.get_json()["error"] == "The request includes an organization that this session cannot access."
    )  # Show the reason.


@pytest.mark.parametrize("failure_status", [400, 503])
def test_compare_route_preserves_http_4xx_and_5xx_failures(
    monkeypatch: pytest.MonkeyPatch, failure_status: int
) -> None:
    """Keep failed Mist status codes visible in partial route results."""
    monkeypatch.setattr(
        licensing_service.self_api,
        "getSelf",
        lambda _session: SimpleNamespace(status_code=200, data={"privileges": []}),
    )  # Allow only the configured direct organization.
    monkeypatch.setattr(
        licensing_service.licenses_api,
        "getOrgLicensesSummary",
        lambda _session, _org_id: SimpleNamespace(status_code=failure_status, data={"error": "synthetic"}, next=None),
    )  # Return one synthetic client or server error.
    monkeypatch.setattr(
        licensing_service.licenses_api,
        "getOrgLicensesBySite",
        lambda _session, _org_id: SimpleNamespace(status_code=200, data=[], next=None),
    )  # Return a successful site read.
    monkeypatch.setattr(
        licensing_service.inventory_api,
        "getOrgInventory",
        lambda _session, _org_id, **_keywords: SimpleNamespace(status_code=200, data=[], next=None),
    )  # Return a successful inventory read.
    monkeypatch.setattr(
        licensing_service.RateLimitingUtils,
        "get_rate_limited_delay",
        lambda *_arguments: (None, 0.0),
    )  # Prevent real waiting.
    app = make_test_app(object())  # Give the route a synthetic shared session.
    response = app.test_client().post(
        "/api/license-comparison",
        json={"organization_ids": ["org-1"], "manual_rows": [], "purchased_amounts": {}},
    )  # Run the production comparison route with synthetic Mist failures.
    result = response.get_json()["results"][0]  # Read the result for the configured organization.
    assert response.status_code == 200  # Partial data remains a valid comparison.
    assert result["request_status"] == "partial"  # Identify the endpoint failure.
    assert result["license_summary"]["status_code"] == failure_status  # Preserve the exact HTTP status.
