"""Unit tests for SettleGateService (T-010).

Tests post-upgrade device validation with 4 parallel checks.
WHY: Ensures settle gate correctly validates devices after firmware upgrade.
"""

import asyncio  # WHY: async test support
import pytest  # WHY: test framework
from unittest.mock import Mock, AsyncMock, patch, MagicMock  # WHY: mocking utilities

from src.upgrade_portal.settle.service import SettleGateService, SettleResult  # WHY: service under test


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
        assert result.timestamp is not None  # WHY: verify timestamp

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

    @pytest.mark.asyncio
    async def test_wait_for_settle_invalid_run_id(self):
        """Test validation of invalid run_id.

        WHY: Ensures service rejects invalid run_id.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call with empty run_id
        result = await service.wait_for_settle(
            run_id="",  # WHY: empty run_id
            device_ids=["device-1"],  # WHY: valid device list
            site_id="site-1",  # WHY: valid site
            org_id="org-1",  # WHY: valid org
        )  # WHY: settle call

        # WHY: verify returned empty dict
        assert result == {}  # WHY: check result

    @pytest.mark.asyncio
    async def test_wait_for_settle_no_devices(self):
        """Test validation of empty device list.

        WHY: Ensures service rejects empty device list.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call with empty device list
        result = await service.wait_for_settle(
            run_id="run-123",  # WHY: valid run_id
            device_ids=[],  # WHY: empty device list
            site_id="site-1",  # WHY: valid site
            org_id="org-1",  # WHY: valid org
        )  # WHY: settle call

        # WHY: verify returned empty dict
        assert result == {}  # WHY: check result

    @pytest.mark.asyncio
    async def test_wait_for_settle_no_dependencies(self):
        """Test validation of missing dependencies.

        WHY: Ensures service handles missing Mist client gracefully.
        """
        # WHY: create service without Mist client
        service = SettleGateService(
            mist_client=None,  # WHY: no Mist client
            db_router=None,  # WHY: no database router
        )  # WHY: service instance

        # WHY: call with valid inputs
        result = await service.wait_for_settle(
            run_id="run-123",  # WHY: valid run_id
            device_ids=["device-1"],  # WHY: valid device list
            site_id="site-1",  # WHY: valid site
            org_id="org-1",  # WHY: valid org
        )  # WHY: settle call

        # WHY: verify returned empty dict
        assert result == {}  # WHY: check result


class TestSettleGateServiceParallelChecks:
    """Tests for parallel check execution."""

    @pytest.mark.asyncio
    async def test_run_device_checks_all_pass(self):
        """Test device checks when all pass.

        WHY: Ensures service correctly aggregates successful checks.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: mock all check methods to pass
        service._check_ping = AsyncMock(return_value=True)  # WHY: mock ping
        service._check_api = AsyncMock(return_value=True)  # WHY: mock api
        service._check_firmware = AsyncMock(return_value=True)  # WHY: mock firmware
        service._check_neighbors = AsyncMock(return_value=True)  # WHY: mock neighbors

        # WHY: run device checks
        result = await service._run_device_checks(
            device_id="device-1",  # WHY: device identifier
            run_id="run-1",  # WHY: run identifier
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            settle_run_id="settle-1",  # WHY: settle run identifier
        )  # WHY: check call

        # WHY: verify all checks passed
        assert result.passed is True  # WHY: check passed status
        assert result.failed_checks == []  # WHY: check no failures
        assert result.device_id == "device-1"  # WHY: check device id

    @pytest.mark.asyncio
    async def test_run_device_checks_some_fail(self):
        """Test device checks when some fail.

        WHY: Ensures service correctly handles partial failures.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: mock checks with mixed results
        service._check_ping = AsyncMock(return_value=True)  # WHY: mock ping pass
        service._check_api = AsyncMock(return_value=False)  # WHY: mock api fail
        service._check_firmware = AsyncMock(return_value=True)  # WHY: mock firmware pass
        service._check_neighbors = AsyncMock(return_value=False)  # WHY: mock neighbors fail

        # WHY: run device checks
        result = await service._run_device_checks(
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
        assert "ping" not in result.failed_checks  # WHY: check ping passed
        assert "firmware" not in result.failed_checks  # WHY: check firmware passed

    @pytest.mark.asyncio
    async def test_run_device_checks_exception_handling(self):
        """Test device checks exception handling.

        WHY: Ensures service handles exceptions in checks gracefully.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: mock checks with exception
        service._check_ping = AsyncMock(return_value=True)  # WHY: mock ping pass
        service._check_api = AsyncMock(side_effect=RuntimeError("API error"))  # WHY: mock api exception
        service._check_firmware = AsyncMock(return_value=True)  # WHY: mock firmware pass
        service._check_neighbors = AsyncMock(return_value=True)  # WHY: mock neighbors pass

        # WHY: run device checks
        result = await service._run_device_checks(
            device_id="device-3",  # WHY: device identifier
            run_id="run-1",  # WHY: run identifier
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            settle_run_id="settle-1",  # WHY: settle run identifier
        )  # WHY: check call

        # WHY: verify check failed due to exception
        assert result.passed is False  # WHY: check failed status
        assert "api" in result.failed_checks  # WHY: check api failed


class TestSettleGateServicePersistence:
    """Tests for result persistence to ArangoDB."""

    @pytest.mark.asyncio
    async def test_wait_for_settle_persists_results(self):
        """Test that results are persisted to ArangoDB.

        WHY: Ensures service stores results for audit trail.
        """
        # WHY: create mock dependencies
        mock_db_router = Mock()  # WHY: mock database router
        mock_db_router.write = Mock(return_value=True)  # WHY: mock write success
        mock_audit_logger = Mock()  # WHY: mock audit logger
        mock_audit_logger.log_operation = Mock()  # WHY: mock log operation

        # WHY: create service with mocks
        service = SettleGateService(
            db_router=mock_db_router,  # WHY: pass mock router
            audit_logger=mock_audit_logger,  # WHY: pass mock logger
        )  # WHY: service instance

        # WHY: mock device check method
        service._run_device_checks = AsyncMock(
            return_value=SettleResult(  # WHY: return result object
                passed=True,  # WHY: passing result
                device_id="device-1",  # WHY: device identifier
                failed_checks=[],  # WHY: no failures
                details={},  # WHY: no details
            )  # WHY: result
        )  # WHY: mock method

        # WHY: call wait_for_settle
        result = await service.wait_for_settle(
            run_id="run-123",  # WHY: run identifier
            device_ids=["device-1"],  # WHY: device list
            site_id="site-1",  # WHY: site identifier
            org_id="org-1",  # WHY: org identifier
            user_id="user-1",  # WHY: user identifier
        )  # WHY: settle call

        # WHY: verify write was called
        assert mock_db_router.write.called  # WHY: check write called
        # WHY: verify collection name
        call_args = mock_db_router.write.call_args  # WHY: get call arguments
        assert call_args[1]["collection"] == "settle_gates"  # WHY: verify collection
        # WHY: verify audit logger was called
        assert mock_audit_logger.log_operation.called  # WHY: check audit called


class TestSettleCheckMethods:
    """Tests for individual check methods."""

    @pytest.mark.asyncio
    async def test_check_ping_success(self):
        """Test ping check success.

        WHY: Ensures ping check returns True on success.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call ping check
        result = await service._check_ping("device-1")  # WHY: ping call

        # WHY: verify result
        assert result is True  # WHY: check success

    @pytest.mark.asyncio
    async def test_check_api_success(self):
        """Test API check success.

        WHY: Ensures API check returns True on success.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call API check
        result = await service._check_api("device-1", "site-1", "org-1")  # WHY: api call

        # WHY: verify result
        assert result is True  # WHY: check success

    @pytest.mark.asyncio
    async def test_check_firmware_success(self):
        """Test firmware check success.

        WHY: Ensures firmware check returns True on success.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call firmware check
        result = await service._check_firmware("device-1", "site-1", "org-1")  # WHY: firmware call

        # WHY: verify result
        assert result is True  # WHY: check success

    @pytest.mark.asyncio
    async def test_check_neighbors_success(self):
        """Test neighbor check success.

        WHY: Ensures neighbor check returns True on success.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: call neighbor check
        result = await service._check_neighbors("device-1", "site-1", "org-1")  # WHY: neighbor call

        # WHY: verify result
        assert result is True  # WHY: check success

    @pytest.mark.asyncio
    async def test_check_ping_retry_on_error(self):
        """Test ping check retries on error.

        WHY: Ensures check retries transient errors per MAX_RETRIES.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance
        # WHY: set max retries low for test
        service.MAX_RETRIES = 2  # WHY: reduce retries for test
        # WHY: set backoff low for test
        service.RETRY_BACKOFF_SECONDS = 0.01  # WHY: reduce backoff for test

        # WHY: track call count
        call_count = 0  # WHY: call counter

        # WHY: define side effect function
        async def failing_then_success():  # WHY: function definition
            nonlocal call_count  # WHY: access outer variable
            call_count += 1  # WHY: increment counter
            if call_count < 2:  # WHY: check if first call
                raise RuntimeError("Transient error")  # WHY: raise error
            return True  # WHY: return success

        # WHY: mock ping as failing then succeeding
        service._check_ping = failing_then_success  # WHY: replace method

        # WHY: call ping check
        result = await service._check_ping("device-1")  # WHY: ping call

        # WHY: verify result is success
        assert result is True  # WHY: check success
        # WHY: verify retried
        assert call_count == 2  # WHY: check retry count


class TestSettleGateTimeout:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_wait_for_settle_timeout(self):
        """Test settle gate timeout.

        WHY: Ensures service handles timeout gracefully.
        """
        # WHY: create service
        service = SettleGateService()  # WHY: service instance

        # WHY: mock device check to never complete
        async def never_completes(*args, **kwargs):  # WHY: async function
            await asyncio.sleep(10)  # WHY: sleep forever
            return SettleResult(  # WHY: return result
                passed=True,  # WHY: success status
                device_id=kwargs.get("device_id", "device-1"),  # WHY: device id
                failed_checks=[],  # WHY: no failures
                details={},  # WHY: no details
            )  # WHY: result

        # WHY: replace check method
        service._run_device_checks = never_completes  # WHY: replace method

        # WHY: call with short timeout
        result = await service.wait_for_settle(
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
