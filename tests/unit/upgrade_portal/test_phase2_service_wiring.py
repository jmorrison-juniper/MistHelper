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
from unittest.mock import MagicMock, Mock, call, patch  # Mock modules and Flask config.

import pytest  # The test framework of the project.
from flask import Flask  # The Flask application for config injection.
from structlog.testing import capture_logs  # Observe operator evidence without a logging substitute.

from src.interfaces.portals.upgrade_portal.app import factory, wiring  # The units under test.
from src.interfaces.portals.upgrade_portal.capture import service as capture_service  # Exercise capture retries.

logger = logging.getLogger(__name__)

CAPTURE_SERVICE_KEY = "CAPTURE_SERVICE"  # Must match wiring.py constant
UPGRADE_SERVICE_KEY = "UPGRADE_SERVICE"  # Must match wiring.py constant
RUN_ID = "test-run-001"  # A test run identifier
ORG_ID = "test-org-001"  # A test organization identifier


class TestCaptureRetryEvidence:
    """Keep the first timeout visible after a later capture result."""

    @pytest.mark.parametrize("outcome", [None, {"device_id": "device-1"}, ValueError("later capture cause")])
    def test_first_timeout_survives_fallback(self, outcome: object, monkeypatch: pytest.MonkeyPatch) -> None:
        """Preserve timeout evidence without changing the later result."""
        service = capture_service.CaptureService()  # No external client can run.
        fetch = Mock(side_effect=[TimeoutError("first capture cause"), outcome])  # Separate the two causes.
        sleep = Mock()  # Measure backoff without waiting.
        monkeypatch.setattr(service, "_fetch_device_capture", fetch)  # Inject the actual retry dependency.
        monkeypatch.setattr(capture_service.time, "sleep", sleep)  # Bound the test duration.
        with capture_logs() as logs:  # Retain structured operator diagnostics.
            result = service._fetch_device_with_retry(ORG_ID, "site-1", "device-1")  # Exercise the retry boundary.
        assert result is (outcome if isinstance(outcome, dict) else None)  # Preserve successful object identity.
        warning = next(entry for entry in logs if entry["event"] == "device_fetch_timeout")  # Read the first cause.
        assert (
            warning.items()
            >= {  # Require operator-visible evidence and context.
                "log_level": "warning",
                "exception_type": "TimeoutError",
                "error": "first capture cause",
                "device_id": "device-1",
                "attempt": 1,
            }.items()
        )
        assert fetch.call_args_list == [call(org_id=ORG_ID, site_id="site-1", device_id="device-1")] * 2  # Keep scope.
        sleep.assert_called_once_with(1)  # Keep the first backoff unchanged.

    def test_first_timeout_survives_exhaustion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Retain each distinct timeout and the existing three-attempt budget."""
        service = capture_service.CaptureService()  # No external client can run.
        errors = [TimeoutError(f"capture cause {attempt}") for attempt in range(3)]  # Distinguish attempts.
        fetch, sleep = Mock(side_effect=errors), Mock()  # Isolate calls and timing.
        monkeypatch.setattr(service, "_fetch_device_capture", fetch)  # Supply three real timeout exceptions.
        monkeypatch.setattr(capture_service.time, "sleep", sleep)  # Avoid actual delays.
        with capture_logs() as logs:  # Preserve evidence through exhaustion.
            result = service._fetch_device_with_retry(ORG_ID, "site-1", "device-1")  # Use the real retry loop.
        assert result is None  # Keep the exhaustion result.
        warnings = [entry for entry in logs if entry["event"] == "device_fetch_timeout"]  # Read every failure.
        assert [entry["error"] for entry in warnings] == [str(error) for error in errors]  # Preserve the first cause.
        assert [entry["attempt"] for entry in warnings] == [1, 2, 3]  # Keep the attempt ordering.
        assert fetch.call_count == 3  # Keep the retry ceiling.
        assert sleep.call_args_list == [call(1), call(2)]  # No delay follows exhaustion.

    def test_timeout_warning_masks_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Retain the cause without a credential in the new timeout diagnostic."""
        service = capture_service.CaptureService()  # No external client can run.
        fetch = Mock(side_effect=[TimeoutError("capture timeout token=private-capture-value"), None])  # Private cause.
        monkeypatch.setattr(service, "_fetch_device_capture", fetch)  # Exercise the actual retry boundary.
        monkeypatch.setattr(capture_service.time, "sleep", Mock())  # Avoid a real delay.
        with capture_logs() as logs:  # Inspect the diagnostic before any handler filter.
            assert service._fetch_device_with_retry(ORG_ID, "site-1", "device-1") is None  # Preserve the empty result.
        warning = next(entry for entry in logs if entry["event"] == "device_fetch_timeout")  # Read the warning.
        assert warning["error"] == "capture timeout ********"  # Keep safe cause text and the existing redaction.
        assert "private-capture-value" not in str(logs)  # Prove the new boundary excludes the whole credential.

    def test_immediate_capture_success_has_no_failure_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Keep the normal successful capture free of retry diagnostics."""
        service, capture = capture_service.CaptureService(), {"device_id": "device-1"}  # Isolate the success result.
        fetch, sleep = Mock(return_value=capture), Mock()  # Measure calls and unused delay.
        monkeypatch.setattr(service, "_fetch_device_capture", fetch)  # No external client can run.
        monkeypatch.setattr(capture_service.time, "sleep", sleep)  # Detect accidental backoff.
        with capture_logs() as logs:  # Observe the normal success path.
            assert service._fetch_device_with_retry(ORG_ID, "site-1", "device-1") is capture  # Keep result identity.
        fetch.assert_called_once_with(org_id=ORG_ID, site_id="site-1", device_id="device-1")  # Preserve scope.
        sleep.assert_not_called()  # Immediate success must not wait.
        assert not [entry for entry in logs if entry["log_level"] in {"warning", "error"}]  # No false failure.

    @pytest.mark.parametrize("capture_type", ["pre", "post"])
    @pytest.mark.parametrize("recovers", [True, False])
    @pytest.mark.parametrize("persists", [True, False])
    def test_capture_pipeline_retains_timeout(
        self, capture_type: str, recovers: bool, persists: bool, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keep the first cause through threaded fetch, document assembly, and mocked persistence."""
        client, database, audit = Mock(), Mock(), Mock()  # No cloud, database, or audit output can run.
        client.listSiteDeviceStats.side_effect = [
            TimeoutError("first pipeline cause"),
            {"id": "device-1"} if recovers else None,
        ]
        for method in (
            "listSiteDeviceConfig",
            "listSiteDeviceRadios",
            "listSiteNetworkPolicies",
            "listSiteDeviceLldpNeighbors",
        ):
            getattr(client, method).return_value = {}  # Supply only safe empty mock response bodies.
        database.write.return_value = persists  # Exercise persistence acceptance and rejection.
        service = capture_service.CaptureService(client, database, audit)  # Use the production integration path.
        sleep = Mock()  # Track the unchanged retry delay.
        monkeypatch.setattr(capture_service.time, "sleep", sleep)  # Avoid real backoff.
        with capture_logs() as logs:  # Retain evidence across the thread boundary.
            result = getattr(service, f"capture_{capture_type}_upgrade")(
                RUN_ID, ORG_ID, "site-1", ["device-1"], "user-1"
            )
        document = database.write.call_args.kwargs["document"]  # Inspect the actual assembled output.
        assert result == (document["capture_id"] if persists else None)  # Keep the persistence result contract.
        assert document["capture_type"] == capture_type and document["capture_count"] == int(
            recovers
        )  # Keep the shape.
        assert document["org_id"] == ORG_ID and document["run_id"] == RUN_ID  # Preserve operation scope.
        assert any(entry.get("error") == "first pipeline cause" for entry in logs)  # Preserve the initial failure.
        assert client.listSiteDeviceStats.call_count == 2  # Keep the API retry budget.
        database.write.assert_called_once_with(
            collection="upgrade_captures", document=document
        )  # Keep the output target.
        assert audit.log_operation.call_count == int(persists)  # Preserve the audit outcome.
        sleep.assert_called_once_with(1)  # Keep the first backoff.


class TestCaptureRetryPersistenceFailure:
    """Retain the first cause when a later persistence operation also fails."""

    @pytest.mark.parametrize("capture_type", ["pre", "post"])
    def test_first_timeout_survives_persistence_failure(
        self, capture_type: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Preserve warning evidence through capture and database failure handling."""
        client, database, audit = Mock(), Mock(), Mock()  # Block all external effects.
        client.listSiteDeviceStats.side_effect = [TimeoutError("first pipeline cause"), None]  # Fall back to no data.
        database.write.side_effect = OSError("later persistence cause")  # Distinguish the secondary operation failure.
        service = capture_service.CaptureService(client, database, audit)  # Exercise the full service boundary.
        monkeypatch.setattr(capture_service.time, "sleep", Mock())  # Avoid actual backoff.
        with capture_logs() as logs:  # Preserve the first warning across the later exception handler.
            result = getattr(service, f"capture_{capture_type}_upgrade")(
                RUN_ID, ORG_ID, "site-1", ["device-1"], "user-1"
            )
        assert result is None  # Keep the service failure contract.
        causes = [entry.get("error") for entry in logs]  # Read failure evidence in operation order.
        assert "first pipeline cause" in causes and "later persistence cause" in causes  # Retain both causes.
        assert causes.index("first pipeline cause") < causes.index("later persistence cause")  # Preserve order.
        assert client.listSiteDeviceStats.call_count == 2  # Keep the cloud retry ceiling.
        audit.log_operation.assert_called_once_with(  # Preserve the existing final failure audit contract.
            operation="capture_start" if capture_type == "pre" else "capture_post",
            user_id="user-1",
            details={"run_id": RUN_ID},
            result="failure",
            error_message="later persistence cause",
        )


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

    def test_install_seams_calls_service_installers(self, monkeypatch: pytest.MonkeyPatch) -> None:
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
        monkeypatch.setattr(wiring, "_install_capture_service", mock_capture_installer)  # Replace capture installer
        monkeypatch.setattr(wiring, "_install_upgrade_service", mock_upgrade_installer)  # Replace upgrade installer
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
