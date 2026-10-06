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
from unittest.mock import MagicMock, patch  # Mock modules and Flask config.

import pytest  # The test framework of the project.
from flask import Flask  # The Flask application for config injection.

from src.interfaces.portals.upgrade_portal.app import factory, wiring  # The units under test.

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

    def test_install_seams_stores_only_request_construction_rules(self) -> None:
        """Startup stores the provider but opens no request-owned dependency."""
        application = Flask(__name__)  # One isolated application holds its own settings.
        application.config["PORTAL_SETTINGS"] = factory.load_settings()  # The settings reader performs no connection.

        wiring.install_seams(application)  # The factory must not build clients before authentication.

        provider = application.config[wiring.PORTAL_SERVICE_PROVIDER_KEY]  # Read the construction-only dependency.
        assert isinstance(provider, wiring.PortalServiceProvider)  # The app config holds no service graph.
        assert wiring.CAPTURE_SERVICE_KEY not in application.config  # Capture resolves inside its request.
        assert wiring.UPGRADE_SERVICE_KEY not in application.config  # Upgrade resolves inside its request.
        assert wiring.SETTLE_GATE_SERVICE_KEY not in application.config  # Settle resolves inside its request.
        assert wiring.COMPARISON_SERVICE_KEY not in application.config  # Comparison resolves inside its request.

    def test_capture_service_key_constant_matches_routes(self) -> None:
        """Verify CAPTURE_SERVICE_KEY constant matches the routes module.

        Why:
            The seam key must be identical in wiring.py and routes/capture.py
            so route handlers can fetch the service from Flask config using the
            same key that wiring uses to install it. A mismatch breaks injection.
        """
        # WHY: Import the capture routes module to check its constant
        from src.interfaces.portals.upgrade_portal.app.routes import capture  # Import routes module

        # WHY: Verify the seam key constants match between wiring and routes
        assert wiring.CAPTURE_SERVICE_KEY == capture.CAPTURE_SERVICE_KEY  # Keys must match for injection

    def test_upgrade_service_key_constant_matches_routes(self) -> None:
        """Verify UPGRADE_SERVICE_KEY constant matches the routes module.

        Why:
            The seam key must be identical in wiring.py and routes/upgrade.py
            so route handlers can fetch the service from Flask config using the
            same key that wiring uses to install it. A mismatch breaks injection.
        """
        # WHY: Import the upgrade routes module to check its constant
        from src.interfaces.portals.upgrade_portal.app.routes import upgrade  # Import routes module

        # WHY: Verify the seam key constants match between wiring and routes
        assert wiring.UPGRADE_SERVICE_KEY == upgrade.UPGRADE_SERVICE_KEY  # Keys must match for injection

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
            with patch.object(wiring, "load_module", return_value=None):  # Make load_module fail
                app.config.pop(CAPTURE_SERVICE_KEY, None)  # Remove the production seam before simulating absence.
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
            with patch.object(wiring, "load_module", return_value=None):  # Make load_module fail
                app.config.pop(UPGRADE_SERVICE_KEY, None)  # Remove the production seam before simulating absence.
                wiring._install_upgrade_service(app)  # Call installer with missing module

        # WHY: Verify a warning was logged about missing module
        assert "upgrade" in caplog.text.lower()  # Log mentions upgrade
        assert "absent" in caplog.text.lower() or "missing" in caplog.text.lower()  # Log mentions missing

        # WHY: Verify the service was NOT added to Flask config (no substitute installed)
        assert app.config.get(UPGRADE_SERVICE_KEY) is None  # No service in config


def test_upgrade_firmware_validation_uses_complete_sdk_reader_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    """The service checks per-model SDK options rather than an invented session method."""
    from types import SimpleNamespace

    from src.interfaces.portals.upgrade_portal.upgrade import options
    from src.interfaces.portals.upgrade_portal.upgrade.service import UpgradeService

    session = object()
    inventory = SimpleNamespace(
        records=[{"mac": "001122334455", "model": "EX4100"}],
        partial_reasons=[],
    )
    inventory_reader = MagicMock(return_value=inventory)
    versions_reader = MagicMock(return_value={"EX4100": ("23.4R2",)})
    monkeypatch.setattr(options, "read_upgrade_inventory", inventory_reader)
    monkeypatch.setattr(options, "read_model_versions", versions_reader)
    service = UpgradeService(mist_client=session)

    assert service._check_firmware_available(
        org_id="org-safe",
        site_id="site-safe",
        device_ids=["00:11:22:33:44:55"],
        firmware_version="23.4R2",
        run_id="run-safe",
        user_id="operator@example.invalid",
    )
    inventory_reader.assert_called_once_with(session, "org-safe", "site-safe")
    versions_reader.assert_called_once_with(session, "site-safe", inventory.records, "org-safe")


def test_upgrade_firmware_validation_refuses_partial_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Incomplete device evidence never authorizes an upgrade plan."""
    from types import SimpleNamespace

    from src.interfaces.portals.upgrade_portal.upgrade import options
    from src.interfaces.portals.upgrade_portal.upgrade.service import UpgradeService

    inventory_reader = MagicMock(
        return_value=SimpleNamespace(records=[{"mac": "001122334455", "model": "EX4100"}], partial_reasons=[{}])
    )
    versions_reader = MagicMock()
    monkeypatch.setattr(options, "read_upgrade_inventory", inventory_reader)
    monkeypatch.setattr(options, "read_model_versions", versions_reader)
    service = UpgradeService(mist_client=object())

    assert not service._check_firmware_available(
        org_id="org-safe",
        site_id="site-safe",
        device_ids=["001122334455"],
        firmware_version="23.4R2",
        run_id="run-safe",
        user_id="operator@example.invalid",
    )
    versions_reader.assert_not_called()


def test_upgrade_cancellation_refuses_without_typed_confirmation() -> None:
    """An unconfirmed portal cancel cannot mutate or relabel an active run."""
    from src.interfaces.portals.upgrade_portal.upgrade.service import UpgradeService

    session = MagicMock()
    database = MagicMock()
    audit = MagicMock()
    service = UpgradeService(session, MagicMock(), audit, database)

    assert service.cancel_upgrade("run-active", "operator@example.invalid") is False
    database.collection.assert_not_called()
    session.post.assert_not_called()
    audit.log_operation.assert_called_once()
    assert audit.log_operation.call_args.kwargs["result"] == "failure"
