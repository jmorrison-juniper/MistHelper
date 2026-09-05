"""Test Phase 2 service wiring for CaptureService and UpgradeService.

Why:
    Phase 2 (T-006 through T-009) introduces CaptureService and UpgradeService
    that are wired into Flask config by wiring.install_seams(). These tests verify:
    - install_seams() calls _install_capture_service() and _install_upgrade_service()
    - Services are installed into Flask config with correct seam keys
    - The wiring handles missing modules gracefully (no socket opened at import)
    - Services are available for route handlers to fetch from current_app.config

    These tests use unittest.mock and pytest to verify the wiring logic without
    requiring real Mist API, ArangoDB, or any network connectivity.
"""

import logging  # The tests verify logging behavior.
from typing import Any  # Config values are free-form.
from unittest.mock import MagicMock, patch  # Mock modules and Flask config.

import pytest  # The test framework of the project.
from flask import Flask  # The Flask application for config injection.

from src.upgrade_portal.app import factory, wiring  # The units under test.
from src.upgrade_portal.runtime import identity  # Needed for SessionOwner fixture.


logger = logging.getLogger(__name__)

CAPTURE_SERVICE_KEY = "CAPTURE_SERVICE"  # Must match wiring.py constant
UPGRADE_SERVICE_KEY = "UPGRADE_SERVICE"  # Must match wiring.py constant
RUN_ID = "test-run-001"  # A test run identifier
ORG_ID = "test-org-001"  # A test organization identifier


class TestServiceWiring:
    """Test that Phase 2 services are wired into Flask config on app startup."""

    @pytest.fixture
    def app(self) -> Flask:
        """Create a test Flask application.

        Why:
            Each test needs an isolated Flask application instance so config
            changes don't leak between tests. The app is created with
            factory.create_app() which initializes all blueprints.

        Yields:
            A Flask application instance with test configuration.
        """
        # WHY: Create app using the factory function
        app = factory.create_app()  # Create Flask application instance
        app.config["TESTING"] = True  # Enable testing mode
        yield app

    def test_install_seams_calls_service_installers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """install_seams() should call _install_capture_service and _install_upgrade_service.

        Why:
            The wiring module's install_seams function is the single place where
            services are registered into Flask config. This test verifies that
            the new Phase 2 service installers are called during setup.
        """
        # WHY: Create a mock app to track config setdefault calls
        mock_app = MagicMock()  # Create a mock Flask application
        
        # WHY: Mock the helper functions to verify they're called
        mock_capture_installer = MagicMock()  # Mock capture service installer
        mock_upgrade_installer = MagicMock()  # Mock upgrade service installer
        
        # WHY: Mock prepare_storage to avoid database calls in this test
        mock_prepare_storage = MagicMock()  # Mock storage preparation function
        
        # WHY: Patch the installer functions to use our mocks
        monkeypatch.setattr(
            wiring, "_install_capture_service", mock_capture_installer
        )  # Replace capture installer
        monkeypatch.setattr(
            wiring, "_install_upgrade_service", mock_upgrade_installer
        )  # Replace upgrade installer
        monkeypatch.setattr(wiring, "prepare_storage", mock_prepare_storage)  # Replace storage prep
        
        # WHY: Call install_seams to trigger service installation
        wiring.install_seams(mock_app)  # This should call our mocked installers
        
        # WHY: Verify both capture and upgrade service installers were called with the app
        mock_capture_installer.assert_called_once_with(mock_app)  # Capture installer called
        mock_upgrade_installer.assert_called_once_with(mock_app)  # Upgrade installer called

    def test_capture_service_key_constant_matches_routes(self) -> None:
        """Verify CAPTURE_SERVICE_KEY constant matches the routes module.

        Why:
            The seam key must be identical in wiring.py and routes/capture.py
            so route handlers can fetch the service from Flask config using the
            same key that wiring uses to install it. A mismatch breaks injection.
        """
        # WHY: Import the capture routes module to check its constant
        from src.upgrade_portal.app.routes import capture  # Import routes module
        
        # WHY: Verify the seam key constants match between wiring and routes
        assert (
            wiring.CAPTURE_SERVICE_KEY == capture.CAPTURE_SERVICE_KEY
        )  # Keys must match for injection

    def test_upgrade_service_key_constant_matches_routes(self) -> None:
        """Verify UPGRADE_SERVICE_KEY constant matches the routes module.

        Why:
            The seam key must be identical in wiring.py and routes/upgrade.py
            so route handlers can fetch the service from Flask config using the
            same key that wiring uses to install it. A mismatch breaks injection.
        """
        # WHY: Import the upgrade routes module to check its constant
        from src.upgrade_portal.app.routes import upgrade  # Import routes module
        
        # WHY: Verify the seam key constants match between wiring and routes
        assert (
            wiring.UPGRADE_SERVICE_KEY == upgrade.UPGRADE_SERVICE_KEY
        )  # Keys must match for injection

    def test_capture_service_module_constant_is_defined(self) -> None:
        """Verify CAPTURE_SERVICE_MODULE constant is defined in wiring.py.

        Why:
            The _install_capture_service function loads the CaptureService
            class from CAPTURE_SERVICE_MODULE. The constant must be defined
            and point to the correct module path.
        """
        # WHY: Check that the module path constant is defined
        assert hasattr(wiring, "CAPTURE_SERVICE_MODULE")  # Constant exists
        # WHY: Verify the module path is correct
        assert "capture" in wiring.CAPTURE_SERVICE_MODULE.lower()  # Path mentions capture
        assert "service" in wiring.CAPTURE_SERVICE_MODULE.lower()  # Path mentions service

    def test_upgrade_service_module_constant_is_defined(self) -> None:
        """Verify UPGRADE_SERVICE_MODULE constant is defined in wiring.py.

        Why:
            The _install_upgrade_service function loads the UpgradeService
            class from UPGRADE_SERVICE_MODULE. The constant must be defined
            and point to the correct module path.
        """
        # WHY: Check that the module path constant is defined
        assert hasattr(wiring, "UPGRADE_SERVICE_MODULE")  # Constant exists
        # WHY: Verify the module path is correct
        assert "upgrade" in wiring.UPGRADE_SERVICE_MODULE.lower()  # Path mentions upgrade
        assert "service" in wiring.UPGRADE_SERVICE_MODULE.lower()  # Path mentions service

    def test_install_capture_service_gracefully_handles_missing_module(
        self, app: Flask, caplog: pytest.LogCaptureFixture
    ) -> None:
        """_install_capture_service should not crash if capture module is missing.

        Why:
            In a degraded deployment or early phase, the capture service module
            might not exist. The wiring should log a warning and continue rather
            than crashing, so the portal can still serve read-only pages.
        """
        # WHY: Call the installer function directly with a real app
        with caplog.at_level(logging.WARNING):  # Capture warning logs
            # WHY: Patch load_module to return None (simulate missing module)
            with patch.object(
                wiring, "load_module", return_value=None
            ):  # Make load_module fail
                wiring._install_capture_service(app)  # Call installer with missing module
        
        # WHY: Verify a warning was logged about missing module
        assert "capture" in caplog.text.lower()  # Log mentions capture
        assert "absent" in caplog.text.lower() or "missing" in caplog.text.lower()  # Log mentions missing
        
        # WHY: Verify the service was NOT added to Flask config (no substitute installed)
        assert app.config.get(CAPTURE_SERVICE_KEY) is None  # No service in config

    def test_install_upgrade_service_gracefully_handles_missing_module(
        self, app: Flask, caplog: pytest.LogCaptureFixture
    ) -> None:
        """_install_upgrade_service should not crash if upgrade module is missing.

        Why:
            In a degraded deployment or early phase, the upgrade service module
            might not exist. The wiring should log a warning and continue rather
            than crashing, so the portal can still serve read-only pages.
        """
        # WHY: Call the installer function directly with a real app
        with caplog.at_level(logging.WARNING):  # Capture warning logs
            # WHY: Patch load_module to return None (simulate missing module)
            with patch.object(
                wiring, "load_module", return_value=None
            ):  # Make load_module fail
                wiring._install_upgrade_service(app)  # Call installer with missing module
        
        # WHY: Verify a warning was logged about missing module
        assert "upgrade" in caplog.text.lower()  # Log mentions upgrade
        assert "absent" in caplog.text.lower() or "missing" in caplog.text.lower()  # Log mentions missing
        
        # WHY: Verify the service was NOT added to Flask config (no substitute installed)
        assert app.config.get(UPGRADE_SERVICE_KEY) is None  # No service in config
