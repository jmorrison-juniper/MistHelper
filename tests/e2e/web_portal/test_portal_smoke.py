"""Smoke tests for the MistHelper web portal.

Validates that all pages load, return correct status codes,
and contain expected data-testid markers and structural elements.
Uses the Flask test client (fast, no browser dependency).
"""


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
        response = client.get("/")  # Render the existing navigation in the portal shell.
        html = response.data.decode()  # Inspect the rendered link selectors.
        nav_links = [  # Keep stable selectors for each portal destination.
            'data-testid="nav-dashboard"',  # Preserve the home destination.
            'data-testid="nav-data"',  # Preserve the data browser destination.
            'data-testid="nav-operations"',  # Preserve the operation runner destination.
            'data-testid="nav-maps"',  # Preserve the map viewer destination.
            'data-testid="nav-licensing-comparison"',  # Expose the new comparison destination.
        ]
        for link in nav_links:  # Verify each existing and new destination.
            assert link in html, f"Missing nav link: {link}"  # Fail when the navigation omits a destination.

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


class TestLicensingComparisonPage:
    """Licensing comparison page smoke tests."""

    def test_page_shows_missing_session_state(self, client):
        """The page clearly blocks comparison when the shared session is absent."""
        response = client.get("/license-comparison")  # Request the feature through the shared Flask app.
        html = response.data.decode()  # Read the rendered unavailable state.
        assert response.status_code == 503  # Keep a missing API session explicit to the operator.
        assert 'data-testid="missing-session"' in html  # Confirm that the page names the session problem.
        assert 'data-testid="compare-button"' in html  # Confirm that the blocked control remains discoverable.

    def test_page_has_stable_feature_selectors(self, client):
        """The comparison page exposes stable selectors for its main controls."""
        response = client.get("/license-comparison")  # Render the feature for selector checks.
        html = response.data.decode()  # Inspect the stable page controls.
        expected_markers = [  # Keep selectors used by browser tests and operators.
            'data-testid="organization-select"',  # Identify the accessible organization list.
            'data-testid="comparison-table"',  # Identify the comparison results.
            'data-testid="manual-rows"',  # Identify session-only manual rows.
            'data-testid="purchased-inputs"',  # Identify purchased amount controls.
            'data-testid="csv-export"',  # Identify the explicit export action.
        ]
        for marker in expected_markers:  # Check every core feature selector.
            assert marker in html, f"Missing marker: {marker}"  # Fail when the page loses a required selector.

    def test_organization_api_reports_missing_session(self, client):
        """The organization API returns an explicit unavailable status."""
        response = client.get("/api/license-comparison/organizations")  # Request choices without a Mist session.
        assert response.status_code == 503  # Return the service-unavailable status instead of an empty success.
        assert response.get_json()["errors"]  # Include an actionable explanation in the response.
