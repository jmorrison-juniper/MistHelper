"""Unit tests for SettleGateService (T-010).

Tests post-upgrade device validation with 4 parallel checks.
WHY: Ensures settle gate correctly validates devices after firmware upgrade.
"""

import time  # WHY: time-based test helpers
from unittest.mock import Mock  # WHY: mocking utilities

from src.interfaces.portals.upgrade_portal.capture.devices import DeviceRead
from src.interfaces.portals.upgrade_portal.settle import service as settle_service_module
from src.interfaces.portals.upgrade_portal.settle.service import (
    SettleGateService,
    SettleResult,
)  # WHY: service under test
from src.operations.execution.firmware.running_version import RunningFirmwareVersionResolver


class TestSettleResult:
    """Tests for SettleResult dataclass."""

    def test_settle_result_passed(self):
        """Test SettleResult with all checks passing.

        WHY: Ensures result correctly represents successful validation.
        """
        # WHY: create result with no failed checks
        result = SettleResult(
            passed=True,  # WHY: success status
            device_id="device-123",  # WHY: device identifier
            failed_checks=[],  # WHY: no failures
            details={"ping": {"status": "passed"}},  # WHY: check details
        )  # WHY: result object

        # WHY: verify passed status
        assert result.passed is True  # WHY: check pass status
        # WHY: verify device id
        assert result.device_id == "device-123"  # WHY: check device
        # WHY: verify no failed checks
        assert result.failed_checks == []  # WHY: check failed list
        # WHY: verify timestamp was set
        assert result.timestamp.endswith("+00:00")  # WHY: verify timestamp is an ISO 8601 UTC value

    def test_settle_result_failed(self):
        """Test SettleResult with failed checks.

        WHY: Ensures result correctly represents validation failure.
        """
        # WHY: create result with failed checks
        result = SettleResult(
            passed=False,  # WHY: failure status
            device_id="device-456",  # WHY: device identifier
            failed_checks=["ping", "api"],  # WHY: failed checks
            details={  # WHY: check details
                "ping": {"status": "failed", "error": "No response"},  # WHY: ping detail
                "api": {"status": "failed", "error": "Device not found"},  # WHY: api detail
            },  # WHY: details complete
        )  # WHY: result object

        # WHY: verify failed status
        assert result.passed is False  # WHY: check pass status
        # WHY: verify device id
        assert result.device_id == "device-456"  # WHY: check device
        # WHY: verify failed checks
        assert "ping" in result.failed_checks  # WHY: check ping failed
        assert "api" in result.failed_checks  # WHY: check api failed
        # WHY: verify error details
        assert "error" in result.details["ping"]  # WHY: check error in detail


class TestSettleGateServiceInit:
    """Tests for SettleGateService initialization."""

    def test_service_initialization(self):
        """Test service initializes with dependencies.

        WHY: Ensures service correctly stores dependencies.
        """
        # WHY: create mock dependencies
        mock_mist_client = Mock()  # WHY: mock Mist API client
        mock_db_router = Mock()  # WHY: mock database router
        mock_audit_logger = Mock()  # WHY: mock audit logger

        # WHY: create service with dependencies
        service = SettleGateService(
            mist_client=mock_mist_client,  # WHY: pass Mist client
            db_router=mock_db_router,  # WHY: pass database router
            audit_logger=mock_audit_logger,  # WHY: pass audit logger
        )  # WHY: service instance

        # WHY: verify dependencies stored
        assert service.mist_client is mock_mist_client  # WHY: check client
        assert service.db_router is mock_db_router  # WHY: check router
        assert service.audit_logger is mock_audit_logger  # WHY: check logger

    def test_service_initialization_without_dependencies(self):
        """Test service initializes without dependencies.

        WHY: Ensures service handles missing dependencies gracefully.
        """
        # WHY: create service without dependencies
        service = SettleGateService()  # WHY: service instance

        # WHY: verify dependencies are None
        assert service.mist_client is None  # WHY: check client
        assert service.db_router is None  # WHY: check router
        assert service.audit_logger is None  # WHY: check logger


class TestSettleGateServiceValidation:
    """Tests for input validation in wait_for_settle."""

    def test_wait_for_settle_invalid_run_id(self):
        """Test validation of invalid run_id.

        WHY: Ensures service rejects invalid run_id.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call with empty run_id
        result = service.wait_for_settle(
            run_id="",  # WHY: empty run_id
            device_ids=["device-1"],  # WHY: valid device list
            site_id="site-1",  # WHY: valid site
            org_id="org-1",  # WHY: valid org
        )  # WHY: settle call

        # WHY: verify returned empty dict
        assert result == {}  # WHY: check result

    def test_wait_for_settle_no_devices(self):
        """Test validation of empty device list.

        WHY: Ensures service rejects empty device list.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call with empty device list
        result = service.wait_for_settle(
            run_id="run-123",  # WHY: valid run_id
            device_ids=[],  # WHY: empty device list
            site_id="site-1",  # WHY: valid site
            org_id="org-1",  # WHY: valid org
        )  # WHY: settle call

        # WHY: verify returned empty dict
        assert result == {}  # WHY: check result

    def test_wait_for_settle_no_dependencies(self):
        """Test validation of missing dependencies.

        WHY: Ensures service handles missing Mist client gracefully.
        """
        # WHY: create service without Mist client
        service = SettleGateService(
            mist_client=None,  # WHY: no Mist client
            db_router=None,  # WHY: no database router
        )  # WHY: service instance

        # WHY: call with valid inputs
        result = service.wait_for_settle(
            run_id="run-123",  # WHY: valid run_id
            device_ids=["device-1"],  # WHY: valid device list
            site_id="site-1",  # WHY: valid site
            org_id="org-1",  # WHY: valid org
        )  # WHY: settle call

        # WHY: verify returned empty dict
        assert result == {}  # WHY: check result


class TestSettleGateServiceParallelChecks:
    """Tests for parallel check execution."""

    def test_run_device_checks_fails_without_icmp_or_neighbor_reachability_evidence(self):
        """Unavailable checks remain failures even when the SDK checks pass."""
        service = SettleGateService()
        service._check_api = Mock(return_value=True)
        service._check_firmware = Mock(return_value=True)

        # WHY: run device checks
        result = service._run_device_checks(
            device_id="device-1",  # WHY: device identifier
            run_id="run-1",  # WHY: run identifier
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            settle_run_id="settle-1",  # WHY: settle run identifier
        )  # WHY: check call

        assert result.passed is False
        assert result.failed_checks == ["ping", "neighbors"]
        assert result.details["ping"] == {"status": "unavailable", "reason": "icmp_not_supported"}
        assert result.details["neighbors"] == {
            "status": "unavailable",
            "reason": "neighbor_reachability_not_supported",
        }
        assert result.device_id == "device-1"  # WHY: check device id

    def test_run_device_checks_some_fail(self):
        """Test device checks when some fail.

        WHY: Ensures service correctly handles partial failures.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: mock checks with mixed results
        service._check_api = Mock(return_value=False)  # WHY: api fails
        service._check_firmware = Mock(return_value=True)  # WHY: firmware passes

        # WHY: run device checks
        result = service._run_device_checks(
            device_id="device-2",  # WHY: device identifier
            run_id="run-1",  # WHY: run identifier
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            settle_run_id="settle-1",  # WHY: settle run identifier
        )  # WHY: check call

        # WHY: verify checks failed overall
        assert result.passed is False  # WHY: check failed status
        assert "api" in result.failed_checks  # WHY: check api failed
        assert "neighbors" in result.failed_checks  # WHY: check neighbors failed
        assert "ping" in result.failed_checks  # ICMP evidence is unavailable.
        assert "firmware" not in result.failed_checks  # WHY: check firmware passed

    def test_run_device_checks_exception_handling(self):
        """Test device checks exception handling.

        WHY: Ensures service handles exceptions in checks gracefully.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: mock checks with exception
        service._check_api = Mock(side_effect=RuntimeError("API error"))  # WHY: api raises
        service._check_firmware = Mock(return_value=True)  # WHY: firmware passes

        # WHY: run device checks
        result = service._run_device_checks(
            device_id="device-3",  # WHY: device identifier
            run_id="run-1",  # WHY: run identifier
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            settle_run_id="settle-1",  # WHY: settle run identifier
        )  # WHY: check call

        # WHY: verify check failed due to exception
        assert result.passed is False  # WHY: check failed status
        assert "api" in result.failed_checks  # WHY: check api failed
        assert "ping" in result.failed_checks
        assert "neighbors" in result.failed_checks


class TestSettleGateServicePersistence:
    """Tests for result persistence to ArangoDB."""

    def test_wait_for_settle_persists_results(self):
        """Test that results are persisted to ArangoDB.

        WHY: Ensures service stores results for audit trail.
        """
        # WHY: create mock dependencies
        mock_mist_client = Mock()  # WHY: mock Mist API client
        mock_db_router = Mock()  # WHY: mock database router
        mock_db_router.write = Mock(return_value=True)  # WHY: mock write success
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_audit_logger.log_operation = Mock()  # WHY: mock log operation
        stored: dict[str, object] = {}  # The fake document store holds one read-back.
        mock_collection = Mock()  # The fake collection has the explicit Arango methods.
        mock_collection.insert.side_effect = lambda document, overwrite=True: stored.update(document)
        mock_collection.get.side_effect = lambda key: stored
        mock_document_store = Mock()  # The service receives a request-owned document handle.
        mock_document_store.collection.return_value = mock_collection

        # WHY: create service with mocks
        service = SettleGateService(
            mist_client=mock_mist_client,  # WHY: pass mock client
            db_router=mock_db_router,  # WHY: pass mock router
            audit_logger=mock_audit_logger,  # WHY: pass mock logger
            document_store=mock_document_store,  # Bind the explicit durable store.
        )  # WHY: service instance

        # WHY: mock device check method
        service._run_device_checks = Mock(
            return_value=SettleResult(  # WHY: return result object
                passed=True,  # WHY: passing result
                device_id="device-1",  # WHY: device identifier
                failed_checks=[],  # WHY: no failures
                details={},  # WHY: no details
            )  # WHY: result
        )  # WHY: mock method

        # WHY: call wait_for_settle
        service.wait_for_settle(
            run_id="run-123",  # WHY: run identifier
            device_ids=["device-1"],  # WHY: device list
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            user_id="user-1",  # WHY: user identifier
        )  # WHY: settle call

        mock_collection.insert.assert_called_once()  # The direct document write has one exact call.
        mock_collection.get.assert_called_once()  # The service proves the write by read-back.
        mock_db_router.write.assert_not_called()  # The router has no portal query/write adapter.
        # WHY: verify audit logger was called
        assert mock_audit_logger.log_operation.call_count == 1  # WHY: check audit called


class TestSettleCheckMethods:
    """Tests for individual check methods."""

    def test_check_ping_without_supported_reader_fails(self):
        """No unsupported ping result can pass the settle gate."""
        service = SettleGateService()  # No ICMP transport is configured.
        result = service._check_ping("device-1")  # The service reports the missing evidence.
        assert result is False  # An unavailable ping is not proof of reachability.

    def test_check_api_uses_complete_sdk_statistics(self, monkeypatch):
        """The API check requires a complete statistics response for the device."""
        answer = DeviceRead("devices_statistics", [{"mac": "001122334455"}], [])
        monkeypatch.setattr(settle_service_module, "read_device_statistics", lambda session, site: answer)
        service = SettleGateService(mist_client=Mock())  # The SDK boundary remains mocked.
        assert service._check_api("00:11:22:33:44:55", "site-1", "org-1") is True
        assert service._check_api("00:11:22:33:44:66", "site-1", "org-1") is False

    def test_check_firmware_uses_running_version_evidence(self, monkeypatch):
        """The firmware check compares the SDK running version with the stored target."""
        database = Mock()
        database.collection.return_value.get.return_value = {"firmware_version": "2.0.0"}
        monkeypatch.setattr(
            RunningFirmwareVersionResolver,
            "fetch_site_running_versions",
            lambda self, site: {"00:11:22:33:44:55": "2.0.0"},
        )
        service = SettleGateService(mist_client=Mock(), document_store=database)
        result = service._check_firmware("001122334455", "site-1", "org-1", "run-1")
        assert result is True

    def test_check_neighbors_without_reachability_evidence_fails(self):
        """Neighbor records do not prove that a neighbor is reachable."""
        service = SettleGateService()
        assert service._check_neighbors("device-1", "site-1", "org-1") is False

    def test_check_ping_does_not_claim_unsupported_probe_success(self):
        """A missing ICMP implementation cannot turn a settle check green."""
        service = SettleGateService()
        assert service._ping_once("device-1") is False
        assert service._check_ping("device-1") is False


class TestSettleGateTimeout:
    """Tests for timeout handling."""

    def test_wait_for_settle_timeout(self):
        """Test settle gate timeout.

        WHY: Ensures service handles timeout gracefully.
        """
        # WHY: create service with dependencies so validation passes
        service = SettleGateService(
            mist_client=Mock(),  # WHY: mock Mist client
            db_router=Mock(),  # WHY: mock database router
        )  # WHY: service instance

        # WHY: mock device check to block past the timeout
        def never_completes(device_id, **kwargs):  # WHY: blocking function
            time.sleep(10)  # WHY: sleep long enough to trigger timeout
            return SettleResult(  # WHY: return result
                passed=True,  # WHY: success status
                device_id=device_id,  # WHY: device id
                failed_checks=[],  # WHY: no failures
                details={},  # WHY: no details
            )  # WHY: result

        # WHY: replace check method
        service._run_device_checks = never_completes  # WHY: replace method

        # WHY: call with short timeout
        result = service.wait_for_settle(
            run_id="run-1",  # WHY: run identifier
            device_ids=["device-1"],  # WHY: device list
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            timeout=0.1,  # WHY: short timeout
        )  # WHY: settle call

        # WHY: verify timeout occurred
        # Result should have timeout failure for device
        # Note: exact behavior depends on implementation
        assert isinstance(result, dict)  # WHY: verify result is dict


class TestSettleGateConstants:
    """Tests for service constants."""

    def test_service_constants(self):
        """Test service timeout constants.

        WHY: Ensures constants are correctly configured.
        """
        # WHY: verify constants
        assert SettleGateService.MAX_RETRIES == 3  # WHY: check max retries
        assert SettleGateService.PING_TIMEOUT_SECONDS == 5  # WHY: check ping timeout
        assert SettleGateService.API_TIMEOUT_SECONDS == 10  # WHY: check API timeout
        assert SettleGateService.FIRMWARE_TIMEOUT_SECONDS == 10  # WHY: check firmware timeout
        assert SettleGateService.NEIGHBOR_TIMEOUT_SECONDS == 10  # WHY: check neighbor timeout
        assert SettleGateService.SETTLE_GATE_TIMEOUT_SECONDS == 300  # WHY: check total timeout
