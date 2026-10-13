"""Smoke tests for the MistHelper web portal.

Validates that all pages load, return correct status codes,
and contain expected data-testid markers and structural elements.
Uses the Flask test client (fast, no browser dependency).
"""

from typing import Any

from tests.e2e.web_portal.test_operations_panel_workflow import portal_url as portal_url


class TestDashboardPage:
    """Dashboard (/) page smoke tests."""

    def test_dashboard_loads(self, client):
        """Dashboard returns 200 and contains the page title."""
        response = client.get("/")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Dashboard" in html

    def test_dashboard_has_testid_markers(self, client):
        """Dashboard contains required data-testid attributes."""
        response = client.get("/")
        html = response.data.decode()
        expected_markers = [
            'data-testid="portal-navbar"',
            'data-testid="dashboard-title"',
            'data-testid="summary-cards"',
            'data-testid="card-file-count"',
            'data-testid="card-status"',
            'data-testid="quick-links"',
        ]
        for marker in expected_markers:
            assert marker in html, f"Missing marker: {marker}"

    def test_dashboard_has_nav_links(self, client):
        """Dashboard navbar has all navigation links."""
        response = client.get("/")
        html = response.data.decode()
        nav_links = [
            'data-testid="nav-dashboard"',
            'data-testid="nav-data"',
            'data-testid="nav-operations"',
            'data-testid="nav-maps"',
        ]
        for link in nav_links:
            assert link in html, f"Missing nav link: {link}"

    def test_dashboard_has_quick_links(self, client):
        """Dashboard has quick-link cards to other pages."""
        response = client.get("/")
        html = response.data.decode()
        quick_links = [
            'data-testid="link-data-browser"',
            'data-testid="link-operations"',
            'data-testid="link-map-viewer"',
        ]
        for link in quick_links:
            assert link in html, f"Missing quick link: {link}"

    def test_wan_dashboard_navigation_and_page_shell(self, client, page: Any, portal_url: str) -> None:
        """WAN dashboard navigation and the read-only page render in the shared portal."""
        navigation = client.get("/")  # Read the shared portal navigation.
        response = client.get("/wan-dashboard")  # Render the integrated dashboard page.
        html = response.data.decode()  # Inspect the server-rendered contract.
        assert navigation.status_code == 200
        assert 'data-testid="wan-dashboard-tab"' in navigation.data.decode()
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Content-Security-Policy"]
        assert "MistCircuitStats" in html
        assert 'data-testid="wan-gateway-table"' in html
        assert 'data-testid="wan-site-filter"' in html
        assert 'data-testid="wan-gateway-search"' in html
        assert 'data-testid="wan-port-details"' in html
        assert 'id="wan-active-port-count"' in html
        assert "External IP" in html
        assert "Uptime" in html
        assert 'data-testid="wan-traffic-range"' in html
        assert '<option value="7d" selected>7 days</option>' in html
        assert 'id="wan-chart-rate"' in html
        assert 'id="wan-chart-data"' in html
        assert "Data transferred per interval" in html
        assert 'data-testid="wan-insights-range"' in html
        assert 'id="wan-peer-modal"' in html
        assert 'data-testid="wan-gateway-export"' in html
        assert 'data-testid="wan-port-export"' in html
        assert 'data-testid="wan-status"' in html
        gateways = [
            {
                "device_id": "gateway-1",
                "site_id": "site-a",
                "site_name": "Demo Seattle",
                "name": "demo-seattle-edge",
                "model": "SSR120",
                "status": "connected",
                "ip": "198.51.100.1",
                "uptime": 259200,
                "wan_port_count": 2,
                "ports": [{"port_id": "wan0", "up": True, "enabled": True}],
            },
            {
                "device_id": "gateway-2",
                "site_id": "site-b",
                "site_name": "Demo Austin",
                "name": "demo-austin-edge",
                "model": "SSR120",
                "status": "connected",
                "ip": "198.51.100.2",
                "uptime": 345600,
                "wan_port_count": 2,
                "ports": [{"port_id": "wan0", "up": True, "enabled": True}],
            },
            {
                "device_id": "gateway-3",
                "site_id": "site-a",
                "site_name": "Demo Seattle",
                "name": "demo-seattle-lab",
                "model": "SSR120",
                "status": "connected",
                "ip": "198.51.100.3",
                "uptime": 432000,
                "wan_port_count": 2,
                "ports": [{"port_id": "wan0", "up": True, "enabled": True}],
            },
        ]  # Supply the same three-gateway, six-port fixture used by the local comparison.
        overview_calls = 0  # Separate the first successful response from the refresh limit.

        def overview(route: Any) -> None:
            nonlocal overview_calls  # Keep the refresh counter local to this browser journey.
            overview_calls += 1  # Count each overview request before choosing its response.
            if overview_calls == 1:  # The first page load supplies the complete synthetic list.
                route.fulfill(json={"status": "ok", "data": gateways, "notice": None})
                return
            route.fulfill(status=429, json={"status": "rate_limited", "data": [], "notice": "Mist rate limit reached."})

        page.route("**/wan-dashboard/api/overview", overview)  # Keep the browser away from live Mist.
        page.route(
            "**/wan-dashboard/api/gateways/gateway-1/ports",
            lambda route: route.fulfill(
                json={
                    "status": "ok",
                    "notice": None,
                    "data": {
                        "ports": [
                            {
                                "port_id": "wan0",
                                "name": "WAN 0",
                                "up": True,
                                "enabled": True,
                                "rx_bytes": 1048576,
                                "tx_bytes": 524288,
                            }
                        ],
                        "peers_by_port": {
                            "wan0": [
                                {
                                    "up": True,
                                    "is_active": True,
                                    "peer_router_name": "peer-a",
                                    "latency": 12.3,
                                    "loss": 0.1,
                                    "mos": 4.2,
                                }
                            ]
                        },
                    },
                }
            ),
        )  # Return one gateway detail and one VPN peer path.
        traffic_requests: list[str] = []  # Record the selected traffic windows.

        def traffic(route: Any) -> None:
            traffic_requests.append(route.request.url)  # Keep the requested range for the browser assertion.
            route.fulfill(
                json={
                    "status": "ok",
                    "notice": None,
                    "data": [
                        {"timestamp": 1, "rx_bps": 1000000, "tx_bps": 500000},
                        {"timestamp": 601, "rx_bps": 2000000, "tx_bps": 1000000},
                    ],
                }
            )  # Supply two samples so both traffic charts render.

        insight_requests: list[str] = []  # Record the selected insight windows.

        def insights(route: Any) -> None:
            insight_requests.append(route.request.url)  # Keep the requested range for the browser assertion.
            route.fulfill(
                json={
                    "status": "ok",
                    "notice": None,
                    "data": {
                        "hourly": [
                            {
                                "timestamp": 1,
                                "rx_bps": 1000,
                                "max_rx_bps": 2000,
                                "tx_bps": 500,
                                "max_tx_bps": 1000,
                                "avg_jitter_ms": 1,
                                "avg_latency_ms": 12,
                                "avg_loss_pct": 0.1,
                            }
                        ],
                        "application_health": {
                            "summary_pct": 98,
                            "threshold_pct": 99,
                            "impacted_interfaces": [{"interface_name": "WAN 0"}],
                            "trend": [{"timestamp": 1, "pct": 98}],
                        },
                    },
                }
            )  # Supply a complete synthetic insight response.

        page.route("**/traffic?range=*", traffic)  # Intercept chart reads in the local browser.
        page.route("**/insights?range=*", insights)  # Intercept insight reads in the local browser.
        page.route(
            "**/api/gateways/export*",
            lambda route: route.fulfill(
                status=200,
                content_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="wan-gateways.csv"'},
                body="gateway,name\ngateway-1,demo-seattle-edge\n",
            ),
        )  # Return one synthetic gateway export.
        page.route(
            "**/hourly/export*",
            lambda route: route.fulfill(
                status=200,
                content_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="wan-hourly.csv"'},
                body="timestamp,rx_bps,tx_bps\n1,1000,500\n",
            ),
        )  # Return one synthetic hourly export.
        page.goto(portal_url, wait_until="networkidle")  # Open the shared portal before its WAN tab.
        page.get_by_test_id("wan-dashboard-tab").click()  # Use the visible navigation action.
        rows = page.get_by_test_id("wan-gateway-row")  # Select only actual gateway rows.
        rows.nth(2).wait_for()  # Wait until all three API records reach the page.
        assert rows.count() == 3  # Confirm the complete synthetic result set.
        page.get_by_test_id("wan-site-filter").select_option("site-a")  # Filter by the first site.
        assert rows.count() == 2  # Keep both gateways from the selected site.
        page.get_by_test_id("wan-gateway-search").fill("lab")  # Search across the filtered rows.
        assert rows.count() == 1  # Keep only the matching gateway.
        page.get_by_test_id("wan-gateway-search").fill("missing")  # Exercise the empty result state.
        assert page.locator("#wan-empty-state").is_visible()  # Tell the operator when no rows match.
        page.get_by_test_id("wan-gateway-search").fill("")  # Clear the search before refreshing.
        page.get_by_test_id("wan-site-filter").select_option("")  # Restore the full organization list.
        with page.expect_download():  # Verify the gateway export starts a browser download.
            page.get_by_test_id("wan-gateway-export").click()  # Download the selected gateway table.
        page.get_by_role("button", name="Refresh data").click()  # Trigger the synthetic rate-limit response.
        page.get_by_test_id("wan-status").get_by_text("Mist rate limit reached.").wait_for()  # Expose the API limit.
        assert rows.count() == 3  # Preserve the last successful gateway rows after the limit.
        rows.first.get_by_role("button", name="Details").click()  # Expand the first gateway.
        page.get_by_role("button", name="Peer paths (1)").wait_for()  # Wait for the detail response.
        page.get_by_role("button", name="Peer paths (1)").click()  # Open its VPN path view.
        assert "peer-a" in page.locator("#wan-peer-modal").inner_text()  # Show the returned peer details.
        page.get_by_role("button", name="Close VPN peer paths").click()  # Return to the port detail row.
        page.get_by_role("button", name="Traffic", exact=True).click()  # Open the traffic chart.
        page.get_by_test_id("wan-traffic-range").select_option("1h")  # Select the ten-minute chart range.
        page.locator("#wan-chart-rate svg").wait_for()  # Wait for the browser to render the rate chart.
        assert traffic_requests[-1].endswith("range=1h")  # Prove the selected range reaches the API.
        page.get_by_role("button", name="Close traffic chart").click()  # Return to the gateway details.
        page.get_by_role("button", name="Insights", exact=True).click()  # Open the WAN Insights view.
        page.get_by_text("Application Health", exact=True).wait_for()  # Wait for the SLE summary metric.
        page.get_by_test_id("wan-insights-range").select_option("7d")  # Select the longest insight period.
        page.get_by_text("Impacted: WAN 0").wait_for()  # Show the impacted interface name.
        assert insight_requests[-1].endswith("range=7d")  # Prove the selected range reaches the API.
        with page.expect_download():  # Verify the hourly export starts a browser download.
            page.get_by_test_id("wan-port-export").click()  # Download the selected hourly metrics.


class TestDataBrowserPage:
    """Data Browser (/data) page smoke tests."""

    def test_data_browser_loads(self, client):
        """Data browser returns 200."""
        response = client.get("/data")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Data Browser" in html

    def test_data_browser_has_testid_markers(self, client):
        """Data browser contains required data-testid attributes."""
        response = client.get("/data")
        html = response.data.decode()
        expected_markers = [
            'data-testid="file-search"',
            'data-testid="file-table"',
        ]
        for marker in expected_markers:
            assert marker in html, f"Missing marker: {marker}"


class TestOperationsPage:
    """Operations (/operations) page smoke tests."""

    def test_operations_loads(self, client):
        """Operations page returns 200."""
        response = client.get("/operations")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Operations" in html

    def test_operations_has_testid_markers(self, client):
        """Operations page contains required data-testid attributes."""
        response = client.get("/operations")
        html = response.data.decode()
        expected_markers = [
            'data-testid="op-search"',
            'data-testid="operation-accordion"',
            'data-testid="run-btn"',
            'data-testid="stop-btn"',
            'data-testid="execution-panel"',
            'data-testid="log-viewer"',
        ]
        for marker in expected_markers:
            assert marker in html, f"Missing marker: {marker}"


class TestMapViewerPage:
    """Map Viewer (/maps) page smoke tests."""

    def test_maps_loads(self, client):
        """Map viewer returns 200."""
        response = client.get("/maps")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Map Viewer" in html

    def test_maps_has_testid_markers(self, client):
        """Map viewer contains required data-testid attributes."""
        response = client.get("/maps")
        html = response.data.decode()
        expected_markers = [
            'data-testid="site-select"',
            'data-testid="map-select"',
            'data-testid="map-container"',
        ]
        for marker in expected_markers:
            assert marker in html, f"Missing marker: {marker}"


class TestHealthEndpoint:
    """Health check endpoint tests."""

    def test_health_returns_json(self, client):
        """Health endpoint returns 200 with JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"


class TestAPIEndpoints:
    """API endpoint smoke tests."""

    def test_data_files_api(self, client):
        """Data files API returns JSON list."""
        response = client.get("/api/data/files")
        assert response.status_code == 200
        data = response.get_json()
        assert "files" in data

    def test_operations_list_api(self, client):
        """Operations list API returns categorized operations."""
        response = client.get("/api/operations/list")
        assert response.status_code == 200
        data = response.get_json()
        assert "categories" in data

    def test_themes_api(self, client):
        """Themes API returns available themes."""
        response = client.get("/api/themes")
        assert response.status_code == 200
        data = response.get_json()
        assert "themes" in data
