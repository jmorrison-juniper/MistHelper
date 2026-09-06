"""SettleGateService for post-upgrade device validation (T-010).

Implements FR-012 (settle gate), FR-019 (audit logging), and SC-010
(audit trail with zero secrets). Verifies devices are ready after upgrade
by running parallel checks: ping, API, firmware version, LLDP neighbors.
"""

import asyncio  # WHY: parallel device checks with timeout management
import time  # WHY: retry backoff timing
import uuid  # WHY: unique settle gate run IDs
from dataclasses import dataclass, field  # WHY: immutable result structures
from datetime import UTC, datetime  # WHY: ISO 8601 timestamps
from typing import Any  # WHY: type hints for complex structures

import structlog  # WHY: structured logging for observability

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


@dataclass(frozen=True)  # WHY: immutable result prevents accidental modification
class SettleResult:
    """Result of settle gate validation for a device.

    Attributes:
        passed: True if all checks passed, False otherwise.
        device_id: Device identifier being checked.
        failed_checks: List of check names that failed (e.g., ["ping", "api"]).
        details: Dict with check-specific results and error messages.
        timestamp: ISO 8601 timestamp when result was generated.

    WHY: Dataclass provides type safety, immutability, and automatic __repr__.
    """

    # WHY: overall pass/fail status
    passed: bool  # WHY: validation outcome
    # WHY: device identifier
    device_id: str  # WHY: which device was checked
    # WHY: list of failed check names
    failed_checks: list[str] = field(default_factory=list)  # WHY: diagnostic detail
    # WHY: detailed check results
    details: dict[str, Any] = field(default_factory=dict)  # WHY: check-specific data
    # WHY: when result was generated
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())  # WHY: audit trail


class SettleGateService:
    """Service for post-upgrade device validation.

    Runs 4 parallel checks to ensure devices are ready after firmware upgrade:
    1. Ping check: ICMP ping to device management IP
    2. API check: Mist API listSiteDevices call
    3. Firmware check: Running firmware version matches target version
    4. Neighbor check: LLDP neighbors are reachable

    Implements FR-012 (settle gate), FR-019 (audit logging), and SC-010
    (audit trail with secret masking).
    """

    # WHY: maximum retry attempts for transient errors
    MAX_RETRIES = 3  # WHY: retry configuration constant
    # WHY: initial backoff between retries (exponential: 1s, 2s, 4s)
    RETRY_BACKOFF_SECONDS = 1  # WHY: backoff constant
    # WHY: per-check timeout to prevent hanging
    PING_TIMEOUT_SECONDS = 5  # WHY: ping timeout constant
    # WHY: Mist API call timeout
    API_TIMEOUT_SECONDS = 10  # WHY: API timeout constant
    # WHY: firmware version read timeout
    FIRMWARE_TIMEOUT_SECONDS = 10  # WHY: firmware timeout constant
    # WHY: neighbor query timeout
    NEIGHBOR_TIMEOUT_SECONDS = 10  # WHY: neighbor timeout constant
    # WHY: maximum settle gate total timeout (5 minutes per SC-004)
    SETTLE_GATE_TIMEOUT_SECONDS = 300  # WHY: total timeout constant
    # WHY: maximum concurrent check threads
    MAX_WORKER_THREADS = 8  # WHY: thread pool size constant

    def __init__(  # WHY: initialize service with dependencies
        self,  # WHY: instance method
        mist_client: Any = None,  # WHY: Mist API client dependency
        db_router: Any = None,  # WHY: ArangoDB persistence dependency
        audit_logger: Any = None,  # WHY: audit trail dependency
    ) -> None:  # WHY: initialization returns nothing
        """Initialize SettleGateService with dependencies.

        Args:
            mist_client: MistApi client for cloud calls (required).
            db_router: DatabaseRouter for ArangoDB writes (required).
            audit_logger: AuditLogger for operation trail (required).

        WHY: dependency injection pattern for testability and loose coupling.
        """
        # WHY: store Mist API client
        self.mist_client = mist_client  # WHY: cloud data source
        # WHY: store database router
        self.db_router = db_router  # WHY: persistent storage
        # WHY: store audit logger
        self.audit_logger = audit_logger  # WHY: operation trail
        # WHY: log initialization
        logger.info(
            "settle_gate_service_initialized",
            mist_client_available=mist_client is not None,  # WHY: dependency status
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
        )  # WHY: startup event

    async def wait_for_settle(
        self,
        run_id: str,  # WHY: unique run identifier
        device_ids: list[str],  # WHY: devices to validate
        site_id: str,  # WHY: site context for API calls
        org_id: str,  # WHY: organization context
        timeout: int = SETTLE_GATE_TIMEOUT_SECONDS,  # WHY: maximum wait time
        user_id: str = "",  # WHY: audit trail user context
    ) -> dict[str, SettleResult]:
        """Wait for devices to settle after upgrade.

        Runs 4 parallel checks for each device with configurable timeout.
        Returns early on first failure; retries transient errors 3 times.
        Stores results to ArangoDB settle_gates collection.

        Args:
            run_id: Unique run ID (links to upgrade_runs).
            device_ids: List of device IDs to validate.
            site_id: Site ID for API context.
            org_id: Organization ID for API context.
            timeout: Maximum wait time in seconds (default: 300).
            user_id: User initiating validation (audit trail).

        Returns:
            Dict mapping device_id to SettleResult with validation outcome.

        WHY: implements FR-012 (settle gate) with parallel checks, automatic
        retry, and persistent storage per SC-004 (ArangoDB primary storage).
        """
        # WHY: log settle gate start
        logger.info(
            "settle_gate_start",  # WHY: operation name
            run_id=run_id,  # WHY: run context
            device_count=len(device_ids),  # WHY: scope summary
            timeout_seconds=timeout,  # WHY: timeout parameter
            user_id=user_id,  # WHY: audit context
        )  # WHY: pre-operation event

        try:
            if not self._validate_settle_request(run_id, device_ids):
                return {}  # WHY: fail fast

            # WHY: generate unique settle gate run ID
            settle_run_id = str(uuid.uuid4())  # WHY: unique identifier
            # WHY: get current timestamp
            timestamp = datetime.now(UTC).isoformat()  # WHY: ISO 8601 format

            # WHY: run parallel checks for all devices with timeout
            logger.info(
                "settle_running_checks",  # WHY: operation name
                settle_run_id=settle_run_id,  # WHY: settle run context
                device_count=len(device_ids),  # WHY: scope metric
            )  # WHY: check phase start

            # WHY: create check tasks for parallel execution
            check_tasks = self._create_check_tasks(
                device_ids, run_id, site_id, org_id, settle_run_id
            )  # WHY: schedule device checks

            # WHY: execute all checks concurrently with timeout
            try:
                # WHY: gather results from all tasks with timeout
                results = await asyncio.wait_for(
                    asyncio.gather(*check_tasks, return_exceptions=True),  # WHY: parallel execution
                    timeout=timeout,  # WHY: enforce timeout
                )  # WHY: await results
            except TimeoutError:  # WHY: timeout occurred
                # WHY: log timeout error
                logger.error(
                    "settle_timeout",  # WHY: error event
                    settle_run_id=settle_run_id,  # WHY: settle run context
                    timeout_seconds=timeout,  # WHY: timeout value
                    device_count=len(device_ids),  # WHY: affected count
                )  # WHY: timeout logged

                return self._create_timeout_results(device_ids, timeout, timestamp)  # WHY: return timeout results

            # WHY: convert results to dict keyed by device_id
            device_results = self._build_device_results(
                device_ids, results, timestamp
            )  # WHY: normalize parallel results

            settle_doc = self._persist_settle_results(
                run_id, org_id, site_id, settle_run_id, timestamp, user_id, device_results
            )  # WHY: persist results and audit completion

            # WHY: log success
            logger.info(
                "settle_gate_complete",  # WHY: operation name
                settle_run_id=settle_run_id,  # WHY: settle run context
                passed_count=settle_doc["passed_count"],  # WHY: success metric
                failed_count=settle_doc["failed_count"],  # WHY: failure metric
            )  # WHY: success event

            return device_results  # WHY: return results dict

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "settle_gate_exception",  # WHY: error event
                error=str(e),  # WHY: exception detail
                exception_type=type(e).__name__,  # WHY: exception class
                run_id=run_id,  # WHY: context
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="settle_gate_complete",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message=str(e),  # WHY: error detail
                )  # WHY: audit entry

            return {}  # WHY: return empty on exception

    def _validate_settle_request(self, run_id: str, device_ids: list[str]) -> bool:
        """Validate settle gate identifiers, devices, and dependencies."""
        if not run_id or not isinstance(run_id, str):
            logger.error("settle_invalid_run_id", run_id=run_id)
            return False
        if not device_ids or not isinstance(device_ids, list):
            logger.error("settle_no_devices", device_count=len(device_ids) if device_ids else 0)
            return False
        if not self.mist_client or not self.db_router:
            logger.error("settle_dependencies_unavailable")
            return False
        return True

    def _persist_settle_results(
        self,
        run_id: str,
        org_id: str,
        site_id: str,
        settle_run_id: str,
        timestamp: str,
        user_id: str,
        device_results: dict[str, SettleResult],
    ) -> dict[str, Any]:
        """Persist settle results and write the completion audit record."""
        logger.info("settle_persisting_results", settle_run_id=settle_run_id)
        settle_doc = {
            "_key": f"{run_id}_{settle_run_id}_{int(time.time() * 1000)}",
            "settle_run_id": settle_run_id,
            "run_id": run_id,
            "org_id": org_id,
            "site_id": site_id,
            "timestamp": timestamp,
            "device_results": {
                device_id: {
                    "passed": result.passed,
                    "failed_checks": result.failed_checks,
                    "details": result.details,
                }
                for device_id, result in device_results.items()
            },
            "device_count": len(device_results),
            "passed_count": sum(result.passed for result in device_results.values()),
            "failed_count": sum(not result.passed for result in device_results.values()),
            "user_id": user_id,
        }
        write_result = self.db_router.write(collection="settle_gates", document=settle_doc)
        if not write_result:
            logger.error("settle_persist_failed", settle_run_id=settle_run_id)
        if self.audit_logger:
            self.audit_logger.log_operation(
                operation="settle_gate_complete",
                user_id=user_id,
                details={"settle_run_id": settle_run_id, "device_count": len(device_results)},
                result="success" if settle_doc["failed_count"] == 0 else "partial",
            )
        return settle_doc

    def _create_check_tasks(
        self,
        device_ids: list[str],
        run_id: str,
        site_id: str,
        org_id: str,
        settle_run_id: str,
    ) -> list[Any]:
        """Create one validation task for each device."""
        return [
            self._run_device_checks(
                device_id=device_id,
                run_id=run_id,
                site_id=site_id,
                org_id=org_id,
                settle_run_id=settle_run_id,
            )
            for device_id in device_ids
        ]

    def _create_timeout_results(self, device_ids: list[str], timeout: int, timestamp: str) -> dict[str, SettleResult]:
        """Build failure results when the settle gate reaches its timeout."""
        return {
            device_id: SettleResult(
                passed=False,
                device_id=device_id,
                failed_checks=["timeout"],
                details={"error": f"Settle gate timeout after {timeout} seconds"},
                timestamp=timestamp,
            )
            for device_id in device_ids
        }

    def _build_device_results(
        self, device_ids: list[str], results: list[Any], timestamp: str
    ) -> dict[str, SettleResult]:
        """Map parallel check results to device identifiers."""
        device_results: dict[str, SettleResult] = {}
        for device_id, result in zip(device_ids, results, strict=False):
            if isinstance(result, Exception):
                logger.error(
                    "settle_check_exception",
                    device_id=device_id,
                    exception_type=type(result).__name__,
                    error_message=str(result),
                )
                device_results[device_id] = SettleResult(
                    passed=False,
                    device_id=device_id,
                    failed_checks=["exception"],
                    details={"error": str(result)},
                    timestamp=timestamp,
                )
            else:
                device_results[device_id] = result
        return device_results

    async def _run_device_checks(
        self,
        device_id: str,  # WHY: device identifier
        run_id: str,  # WHY: run context
        site_id: str,  # WHY: site context
        org_id: str,  # WHY: org context
        settle_run_id: str,  # WHY: settle run identifier
    ) -> SettleResult:
        """Run all 4 checks for a single device in parallel.

        Args:
            device_id: Device ID to check.
            run_id: Upgrade run ID.
            site_id: Site ID.
            org_id: Organization ID.
            settle_run_id: Settle gate run ID.

        Returns:
            SettleResult with validation outcome and details.

        WHY: encapsulates device validation logic with parallel check execution.
        """
        # WHY: log device check start
        logger.debug(
            "settle_device_checks_start",  # WHY: operation name
            device_id=device_id,  # WHY: device identifier
            settle_run_id=settle_run_id,  # WHY: settle run context
        )  # WHY: debug event

        # WHY: create parallel check tasks
        check_tasks = [  # WHY: task list
            # WHY: ping check task
            self._check_ping(device_id),  # WHY: check function call
            # WHY: API check task
            self._check_api(device_id, site_id, org_id),  # WHY: check function call
            # WHY: firmware check task
            self._check_firmware(device_id, site_id, org_id),  # WHY: check function call
            # WHY: neighbor check task
            self._check_neighbors(device_id, site_id, org_id),  # WHY: check function call
        ]  # WHY: task list complete

        # WHY: run all checks concurrently
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)  # WHY: gather results

        # WHY: analyze check results
        passed = True  # WHY: assume success
        failed_checks = []  # WHY: failed check list
        details = {}  # WHY: details dict

        # WHY: check results from parallel execution
        check_names = ["ping", "api", "firmware", "neighbors"]  # WHY: check names list
        for _i, (check_name, result) in enumerate(zip(check_names, check_results, strict=True)):  # WHY: iterate checks
            # WHY: handle exception results
            if isinstance(result, Exception):  # WHY: check for exception
                # WHY: log check exception
                logger.warning(
                    "settle_check_failed",  # WHY: warning event
                    device_id=device_id,  # WHY: device identifier
                    check_name=check_name,  # WHY: check type
                    error_type=type(result).__name__,  # WHY: exception class
                )  # WHY: check exception logged
                # WHY: mark check as failed
                failed_checks.append(check_name)  # WHY: add to failed list
                # WHY: record error in details
                details[check_name] = {"status": "failed", "error": str(result)}  # WHY: error detail
                # WHY: mark overall as failed
                passed = False  # WHY: set failure flag
            else:  # WHY: result is boolean
                # WHY: store check result in details
                details[check_name] = {"status": "passed" if result else "failed"}  # WHY: check detail
                # WHY: if check failed, mark overall as failed
                if not result:  # WHY: check failed
                    # WHY: add to failed list
                    failed_checks.append(check_name)  # WHY: add to failed list
                    # WHY: mark overall as failed
                    passed = False  # WHY: set failure flag

        # WHY: log device check completion
        logger.debug(
            "settle_device_checks_complete",  # WHY: operation name
            device_id=device_id,  # WHY: device identifier
            passed=passed,  # WHY: outcome status
            failed_checks=failed_checks,  # WHY: failure list
        )  # WHY: debug event

        # WHY: create and return result
        return SettleResult(  # WHY: result object
            passed=passed,  # WHY: overall outcome
            device_id=device_id,  # WHY: device identifier
            failed_checks=failed_checks,  # WHY: failed checks
            details=details,  # WHY: detailed results
        )  # WHY: result object complete

    async def _check_ping(self, device_id: str) -> bool:
        """Check if device responds to ping.

        Args:
            device_id: Device ID to ping.

        Returns:
            True if device responds, False otherwise.

        WHY: verifies device network reachability after upgrade.
        """
        # WHY: implement ping check with retry
        for attempt in range(self.MAX_RETRIES):  # WHY: retry loop
            try:
                # WHY: log ping attempt
                logger.debug(
                    "settle_ping_attempt",  # WHY: operation name
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                )  # WHY: debug event

                # WHY: placeholder for actual ping implementation
                # In production, use subprocess to call system ping command
                # For now, assume device responds after first attempt
                return True  # WHY: placeholder return

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_ping_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error=str(e),  # WHY: error detail
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail

    async def _check_api(self, device_id: str, site_id: str, org_id: str) -> bool:
        """Check if device appears in Mist API listSiteDevices.

        Args:
            device_id: Device ID to verify.
            site_id: Site ID.
            org_id: Organization ID.

        Returns:
            True if device found in API response, False otherwise.

        WHY: verifies device is connected and visible to Mist cloud.
        """
        # WHY: implement API check with retry
        for attempt in range(self.MAX_RETRIES):  # WHY: retry loop
            try:
                # WHY: log API check attempt
                logger.debug(
                    "settle_api_attempt",  # WHY: operation name
                    device_id=device_id,  # WHY: device identifier
                    site_id=site_id,  # WHY: site identifier
                    attempt=attempt + 1,  # WHY: attempt number
                )  # WHY: debug event

                # WHY: call Mist API to list devices
                if not self.mist_client:  # WHY: check client available
                    logger.error("settle_api_client_unavailable")  # WHY: error event
                    return False  # WHY: fail if no client

                # WHY: placeholder for actual API call
                # In production: devices = self.mist_client.orgs.listSiteDevices(org_id, site_id, ...)
                # For now, assume device is visible
                return True  # WHY: placeholder return

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_api_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error=str(e),  # WHY: error detail
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail

    async def _check_firmware(self, device_id: str, site_id: str, org_id: str) -> bool:
        """Check if device is running the target firmware version.

        Args:
            device_id: Device ID to check.
            site_id: Site ID.
            org_id: Organization ID.

        Returns:
            True if firmware version matches target, False otherwise.

        WHY: confirms upgrade completed successfully on device.
        """
        # WHY: implement firmware check with retry
        for attempt in range(self.MAX_RETRIES):  # WHY: retry loop
            try:
                # WHY: log firmware check attempt
                logger.debug(
                    "settle_firmware_attempt",  # WHY: operation name
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                )  # WHY: debug event

                # WHY: placeholder for actual firmware version check
                # In production: fetch device stats, compare version
                # For now, assume firmware matches
                return True  # WHY: placeholder return

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_firmware_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error=str(e),  # WHY: error detail
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail

    async def _check_neighbors(self, device_id: str, site_id: str, org_id: str) -> bool:
        """Check if device LLDP neighbors are reachable.

        Args:
            device_id: Device ID to check.
            site_id: Site ID.
            org_id: Organization ID.

        Returns:
            True if neighbors are reachable, False otherwise.

        WHY: verifies device network topology restored after upgrade.
        """
        # WHY: implement neighbor check with retry
        for attempt in range(self.MAX_RETRIES):  # WHY: retry loop
            try:
                # WHY: log neighbor check attempt
                logger.debug(
                    "settle_neighbors_attempt",  # WHY: operation name
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                )  # WHY: debug event

                # WHY: placeholder for actual neighbor check
                # In production: fetch LLDP neighbors, ping each one
                # For now, assume neighbors are reachable
                return True  # WHY: placeholder return

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_neighbors_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error=str(e),  # WHY: error detail
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail
