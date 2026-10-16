"""Test the WAN dashboard routes with local service responses."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from flask import Flask, render_template
from flask.testing import FlaskClient

from src.interfaces.portals.upgrade_portal.runtime import lock
from src.interfaces.portals.wan_dashboard.routes import WanDashboardService, wan_dashboard_bp


class FakeDashboardService:
    """Return fixed data and record route arguments."""

    def __init__(self) -> None:
        """Create predictable local responses for route tests."""
        self.overview_filters: dict[str, object] = {}  # Record the filters sent by the route.
        self.traffic_selection: tuple[str, str, str] | None = None  # Record one chart request.

    def get_overview(self, **filters: object) -> dict[str, object]:
        """Return one successful synthetic overview."""
        self.overview_filters = filters  # Preserve the supplied filters for the route assertion.
        return {"status": "ok", "data": [{"device_id": "gw-a"}], "notice": None}  # Return local rows.

    def get_gateway_ports(self, gateway_id: str) -> dict[str, object]:
        """Return one successful synthetic gateway result."""
        return {"status": "ok", "data": [{"gateway_id": gateway_id}], "notice": None}  # Echo local input.

    def get_traffic(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, object]:
        """Return one successful synthetic traffic response."""
        self.traffic_selection = (gateway_id, port_id, time_range)  # Record the URL-decoded source selection.
        return {"status": "ok", "data": [], "range": time_range, "notice": None}  # Keep result shape stable.

    def get_insights(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, object]:
        """Return one successful synthetic insight response."""
        return {"status": "ok", "data": [], "range": time_range, "notice": None}  # Keep result shape stable.

    def export_gateways(self, **filters: object) -> dict[str, object]:
        """Return one selected gateway row for a CSV request."""
        self.overview_filters = filters  # Reuse the filter record for export checks.
        return {"status": "ok", "data": [{"device_id": "gw-a", "name": "Gateway A"}]}  # Keep rows synthetic.

    def get_hourly_export(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, object]:
        """Return the source's hourly export response shape."""
        return {
            "status": "ok",
            "data": {
                "site_name": "Site A",
                "gateway_hostname": gateway_id,
                "hourly": [{"timestamp": 1, "hour_iso": "1970-01-01T00:00:00Z"}],
                "range": time_range,
                "port_id": port_id,
            },
        }  # Supply one row with UTC time.


def build_client(service: FakeDashboardService) -> tuple[FlaskClient, Flask]:
    """Build a local Flask client around the feature blueprint."""
    template_folder = Path(__file__).resolve().parents[4] / "web_portal" / "templates"
    app = Flask(__name__, template_folder=str(template_folder))  # Resolve the shared portal base template.
    app.config.update(
        TESTING=True,
        WAN_DASHBOARD_SERVICE=service,
        PORTAL={"title": "MistHelper", "theme": "magenta", "accent_color": "#e20074", "logo_url": ""},
    )  # Inject only local page configuration.
    app.context_processor(
        lambda: {
            "csrf_token": lambda: "local-test-token",
            "portal_title": "MistHelper",
            "portal_logo": "",
            "portal_accent": "#e20074",
            "portal_theme": "magenta",
            "available_themes": [],
        }
    )  # Supply branding without loading portal services.
    for endpoint in (
        "dashboard.dashboard",
        "data.data_browser",
        "operations.operations_page",
        "maps.maps_page",
        "websockets.page",
    ):
        app.add_url_rule("/", endpoint=endpoint, view_func=lambda: "")
    app.register_blueprint(wan_dashboard_bp)  # Exercise the production feature routes.
    return app.test_client(), app  # Keep the app available for access-control checks.


def test_isolated_portal_hides_dashboard_navigation_without_its_route() -> None:
    """The shared template renders when the isolated app lacks the dashboard route."""
    template_folder = (
        Path(__file__).resolve().parents[4] / "web_portal" / "templates"
    )  # Locate the shared portal templates.
    app = Flask(__name__, template_folder=str(template_folder))  # Render the production base template.
    app.config["PORTAL"] = {
        "title": "MistHelper",
        "theme": "magenta",
        "accent_color": "#e20074",
        "logo_url": "",
    }  # Supply the portal branding required by the layout.
    for endpoint in (
        "dashboard.dashboard",
        "data.data_browser",
        "operations.operations_page",
        "maps.maps_page",
        "websockets.page",
    ):
        app.add_url_rule("/", endpoint=endpoint, view_func=lambda: "")  # Stub unrelated portal links.
    app.add_url_rule(
        "/websockets",
        endpoint="isolated_websockets_page",
        view_func=lambda: render_template("base.html"),
    )  # Render the layout from a page without the feature blueprint.
    app.context_processor(
        lambda: {
            "csrf_token": lambda: "local-test-token",
            "portal_title": "MistHelper",
            "portal_logo": "",
            "portal_accent": "#e20074",
            "portal_theme": "magenta",
            "available_themes": [],
        }
    )  # Supply the portal context without loading shared services.

    response = app.test_client().get("/websockets")  # Render the layout in isolation.

    assert response.status_code == 200  # The shared layout must render successfully.
    assert b'data-testid="wan-dashboard-tab"' not in response.data  # Hide navigation without its registered route.


class TestOverviewRoutes:
    """Prove that overview inputs and errors are handled explicitly."""

    def test_overview_passes_valid_filters_to_the_service(self) -> None:
        """Valid query filters reach the service unchanged."""
        service = FakeDashboardService()  # Build one local service stub.
        client, _app = build_client(service)  # Register the production routes.

        response = client.get("/wan-dashboard/api/overview?site_id=site-a&search=gw")  # Send safe filters.

        assert response.status_code == 200  # A valid overview request succeeds.
        assert response.get_json()["status"] == "ok"  # Preserve explicit result status.
        assert service.overview_filters == {"site_id": "site-a", "gateway_id": None, "search": "gw"}  # Keep filters.

    def test_unknown_gateway_is_not_authorized(self) -> None:
        """A service access failure does not disclose gateway data."""
        service = FakeDashboardService()  # Build a local service stub.
        service.get_gateway_ports = lambda _gateway_id: {  # Model an unauthorized gateway.
            "status": "forbidden",
            "data": [],
            "notice": "Gateway is not in the active organization.",
        }
        client, _app = build_client(service)  # Register the production routes.

        response = client.get("/wan-dashboard/api/gateways/not-in-org/ports")  # Request a foreign identifier.

        assert response.status_code == 404  # Do not confirm a foreign gateway exists.
        assert response.get_json()["status"] == "forbidden"  # Preserve the access result.

    def test_invalid_time_range_is_rejected_before_service_call(self) -> None:
        """Unsupported traffic ranges receive an input error."""
        service = FakeDashboardService()  # Build a local service stub.
        client, _app = build_client(service)  # Register the production routes.

        response = client.get("/wan-dashboard/api/gateways/gw-a/ports/wan0/traffic?range=30d")  # Use invalid range.

        assert response.status_code == 400  # Reject an unsupported range.
        assert response.get_json()["status"] == "invalid"  # Identify an input error.

    def test_api_session_absence_returns_service_unavailable(self) -> None:
        """The route does not treat a missing shared Mist session as empty data."""
        client, app = build_client(FakeDashboardService())  # Build a local service client.
        app.config.pop("WAN_DASHBOARD_SERVICE")  # Require the route to resolve the shared session.
        app.config["APISESSION"] = None  # Model an unavailable Mist session.

        response = client.get("/wan-dashboard/api/overview")  # Request live data without credentials.

        assert response.status_code == 503  # Report unavailable service state.
        assert response.get_json()["status"] == "error"  # Do not return success with no rows.

    def test_invalid_overview_filters_are_rejected_before_service_call(self) -> None:
        """Unsafe and overlong filter values do not reach the service."""
        service = FakeDashboardService()  # Keep the call record local.
        client, _app = build_client(service)  # Register the production routes.

        invalid_identifier = client.get("/wan-dashboard/api/overview?site_id=../site-a")
        long_search = client.get(f"/wan-dashboard/api/overview?search={'x' * 121}")

        assert invalid_identifier.status_code == 400  # Reject unsafe identifiers.
        assert long_search.status_code == 400  # Reject unbounded search text.
        assert service.overview_filters == {}  # Do not call the service on invalid input.

    def test_error_state_maps_to_bad_gateway(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed data service response stays an explicit HTTP error."""
        service = FakeDashboardService()  # Keep this response isolated from Mist.
        monkeypatch.setattr(
            service,
            "get_overview",
            lambda **_filters: {"status": "error", "data": [], "notice": "Synthetic failure."},
        )  # Supply a service failure envelope.
        client, _app = build_client(service)  # Register the production route.

        response = client.get("/wan-dashboard/api/overview")

        assert response.status_code == 502  # Do not report a failed upstream read as success.
        assert response.get_json()["status"] == "error"  # Preserve the failure state.

    def test_shared_service_is_created_once_and_reused(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The route caches one service per portal worker and reuses shared dependencies."""
        client, app = build_client(FakeDashboardService())  # Create an isolated portal app.
        app.config.pop("WAN_DASHBOARD_SERVICE")  # Exercise production dependency resolution.
        app.config["APISESSION"] = object()  # Supply a local placeholder for the shared Mist session.
        app.config["ORG_ID"] = "org-local"  # Supply a local organization identifier.
        cache = object()  # Keep Redis connection creation observable without a server.
        monkeypatch.setattr(lock, "connect_lock_store", lambda: cache)  # Reuse the local cache object.
        monkeypatch.setattr(
            WanDashboardService,
            "get_overview",
            MagicMock(return_value={"status": "ok", "data": [], "notice": None}),
        )  # Prevent external SDK calls in the provider test.

        first = client.get("/wan-dashboard/api/overview")  # Build and store the shared feature service.
        stored_service = app.extensions["wan_dashboard_service"]  # Read the worker-local service.
        second = client.get("/wan-dashboard/api/overview")  # Reuse the existing feature service.

        assert first.status_code == 200  # The shared dependencies allow the first read.
        assert second.status_code == 200  # The stored service supports later reads.
        assert app.extensions["wan_dashboard_service"] is stored_service  # Keep one worker-local service.

    def test_missing_organization_identifier_returns_service_unavailable(self) -> None:
        """The route rejects an incomplete shared session configuration."""
        client, app = build_client(FakeDashboardService())  # Build a local portal client.
        app.config.pop("WAN_DASHBOARD_SERVICE")  # Exercise production dependency resolution.
        app.config["APISESSION"] = object()  # Supply a session without an organization.
        app.config["ORG_ID"] = " "  # Model invalid active-organization configuration.

        response = client.get("/wan-dashboard/api/overview")

        assert response.status_code == 503  # Report a missing shared dependency.
        assert response.get_json()["status"] == "error"  # Keep the state explicit.

    def test_rate_limit_keeps_its_http_status_and_notice(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A service rate limit is not converted into an empty successful response."""
        service = FakeDashboardService()  # Keep this response independent from Mist.
        monkeypatch.setattr(
            service,
            "get_overview",
            lambda **_filters: {
                "status": "rate_limited",
                "data": [{"device_id": "gw-a"}],
                "notice": "Mist rate limit reached.",
            },
        )  # Provide a fixed rate-limit envelope.
        client, _app = build_client(service)  # Register the production route.

        response = client.get("/wan-dashboard/api/overview")  # Request the synthetic rate-limited result.

        assert response.status_code == 429  # Preserve the rate-limit HTTP code.
        assert response.get_json()["status"] == "rate_limited"  # Preserve the explicit service state.

    def test_encoded_port_identifier_reaches_the_service_decoded(self) -> None:
        """Port names with slashes use the path converter without changing the value."""
        service = FakeDashboardService()  # Record the decoded route parameters.
        client, _app = build_client(service)  # Register the production route.

        response = client.get("/wan-dashboard/api/gateways/gw-a/ports/wan%2F0/traffic?range=1h")

        assert response.status_code == 200  # The route accepts an encoded port name.
        assert service.traffic_selection == ("gw-a", "wan/0", "1h")  # Preserve the source port identifier.

    def test_documented_traffic_and_insight_ranges_are_accepted(self) -> None:
        """The route supports every traffic and WAN Insights range from the source."""
        client, _app = build_client(FakeDashboardService())  # Register local route dependencies.
        for time_range in ("1h", "6h", "24h", "7d"):
            traffic = client.get(
                f"/wan-dashboard/api/gateways/gw-a/ports/wan0/traffic?range={time_range}"
            )  # Exercise each supported traffic range.
            assert traffic.status_code == 200  # Accept the documented traffic range.
        for time_range in ("1h", "6h", "24h", "3d", "7d"):
            insights = client.get(
                f"/wan-dashboard/api/gateways/gw-a/ports/wan0/insights?range={time_range}"
            )  # Exercise each supported insights range.
            assert insights.status_code == 200  # Accept the documented WAN Insights range.

    def test_malformed_identifiers_are_rejected(self) -> None:
        """Malformed gateway and port path values fail before the service call."""
        service = FakeDashboardService()  # Keep service calls observable.
        client, _app = build_client(service)  # Register the production routes.

        invalid_gateway = client.get("/wan-dashboard/api/gateways/contains%20space/ports")
        invalid_port = client.get("/wan-dashboard/api/gateways/gw-a/ports/wan0!/traffic")

        assert invalid_gateway.status_code == 400  # Reject a path-traversal identifier.
        assert invalid_port.status_code == 400  # Reject control characters in a port identifier.
        assert service.traffic_selection is None  # Stop before live data collection.

    def test_export_filter_and_hourly_range_errors_are_explicit(self) -> None:
        """Exports reject the same unsafe selection and range values as JSON reads."""
        service = FakeDashboardService()  # Keep export calls local.
        client, _app = build_client(service)  # Register the production routes.

        invalid_filter = client.get(f"/wan-dashboard/api/gateways/export?search={'x' * 121}")
        invalid_range = client.get("/wan-dashboard/api/gateways/gw-a/ports/wan0/hourly/export?range=30d")

        assert invalid_filter.status_code == 400  # Reject an unsafe export selection.
        assert invalid_range.status_code == 400  # Reject an unsupported hourly range.
        assert service.overview_filters == {}  # Do not create an export from invalid input.


class TestPortalPage:
    """Prove that the integrated page renders in the shared shell."""

    def test_page_uses_the_dashboard_template_and_stable_markers(self) -> None:
        """The page renders source workflows with stable browser selectors."""
        service = FakeDashboardService()  # Build a local service stub.
        client, _app = build_client(service)  # Register the feature blueprint.

        response = client.get("/wan-dashboard")  # Render the dashboard page.
        html = response.get_data(as_text=True)  # Read HTML for stable marker assertions.

        assert response.status_code == 200  # The page is available without a live cloud call.
        assert "MistCircuitStats" in html  # Preserve the source feature name.
        assert 'data-testid="wan-gateway-table"' in html  # Expose the overview table selector.
        assert 'data-testid="wan-traffic-range"' in html  # Expose traffic range controls.
        assert 'data-testid="wan-insights-range"' in html  # Expose WAN Insights controls.
