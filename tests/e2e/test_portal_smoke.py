"""Smoke tests for the MistHelper web portal.

Validates that all pages load, return correct status codes,
and contain expected data-testid markers and structural elements.
Uses the Flask test client (fast, no browser dependency).
"""


class TestDashboardPage:
    """Dashboard (/) page smoke tests."""

    def test_dashboard_loads(self, client):
        """Dashboard returns 200 and contains the page title."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Dashboard' in html

    def test_dashboard_has_testid_markers(self, client):
        """Dashboard contains required data-testid attributes."""
        response = client.get('/')
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
            assert marker in html, f'Missing marker: {marker}'

    def test_dashboard_has_nav_links(self, client):
        """Dashboard navbar has all navigation links."""
        response = client.get('/')
        html = response.data.decode()
        nav_links = [
            'data-testid="nav-dashboard"',
            'data-testid="nav-data"',
            'data-testid="nav-operations"',
            'data-testid="nav-maps"',
        ]
        for link in nav_links:
            assert link in html, f'Missing nav link: {link}'

    def test_dashboard_has_quick_links(self, client):
        """Dashboard has quick-link cards to other pages."""
        response = client.get('/')
        html = response.data.decode()
        quick_links = [
            'data-testid="link-data-browser"',
            'data-testid="link-operations"',
            'data-testid="link-map-viewer"',
        ]
        for link in quick_links:
            assert link in html, f'Missing quick link: {link}'


class TestDataBrowserPage:
    """Data Browser (/data) page smoke tests."""

    def test_data_browser_loads(self, client):
        """Data browser returns 200."""
        response = client.get('/data')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Data Browser' in html

    def test_data_browser_has_testid_markers(self, client):
        """Data browser contains required data-testid attributes."""
        response = client.get('/data')
        html = response.data.decode()
        expected_markers = [
            'data-testid="file-search"',
            'data-testid="file-table"',
        ]
        for marker in expected_markers:
            assert marker in html, f'Missing marker: {marker}'


class TestOperationsPage:
    """Operations (/operations) page smoke tests."""

    def test_operations_loads(self, client):
        """Operations page returns 200."""
        response = client.get('/operations')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Operations' in html

    def test_operations_has_testid_markers(self, client):
        """Operations page contains required data-testid attributes."""
        response = client.get('/operations')
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
            assert marker in html, f'Missing marker: {marker}'


class TestMapViewerPage:
    """Map Viewer (/maps) page smoke tests."""

    def test_maps_loads(self, client):
        """Map viewer returns 200."""
        response = client.get('/maps')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Map Viewer' in html

    def test_maps_has_testid_markers(self, client):
        """Map viewer contains required data-testid attributes."""
        response = client.get('/maps')
        html = response.data.decode()
        expected_markers = [
            'data-testid="site-select"',
            'data-testid="map-select"',
            'data-testid="map-container"',
        ]
        for marker in expected_markers:
            assert marker in html, f'Missing marker: {marker}'


class TestHealthEndpoint:
    """Health check endpoint tests."""

    def test_health_returns_json(self, client):
        """Health endpoint returns 200 with JSON."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'


class TestAPIEndpoints:
    """API endpoint smoke tests."""

    def test_data_files_api(self, client):
        """Data files API returns JSON list."""
        response = client.get('/api/data/files')
        assert response.status_code == 200
        data = response.get_json()
        assert 'files' in data

    def test_operations_list_api(self, client):
        """Operations list API returns categorized operations."""
        response = client.get('/api/operations/list')
        assert response.status_code == 200
        data = response.get_json()
        assert 'categories' in data

    def test_themes_api(self, client):
        """Themes API returns available themes."""
        response = client.get('/api/themes')
        assert response.status_code == 200
        data = response.get_json()
        assert 'themes' in data
