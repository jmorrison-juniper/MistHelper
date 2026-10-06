"""SettleGateService for post-upgrade device validation (T-010).

Implements FR-012 (settle gate), FR-019 (audit logging), and SC-010
(audit trail with zero secrets). Verifies devices are ready after upgrade
by running parallel checks: ping, API, firmware version, LLDP neighbors.
"""

import time  # WHY: retry backoff timing
import uuid  # WHY: unique settle gate run IDs
from concurrent.futures import ThreadPoolExecutor  # WHY: parallel device checks with timeout management
from dataclasses import dataclass, field  # WHY: immutable result structures
from datetime import UTC, datetime  # WHY: ISO 8601 timestamps
from typing import Any  # WHY: type hints for complex structures

import structlog  # WHY: structured logging for observability

from src.interfaces.portals.upgrade_portal.capture.devices import normalize_device_mac, read_device_statistics
from src.operations.execution.firmware.running_version import RunningFirmwareVersionResolver

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
    settle_run_id: str = ""  # The verified stored document that contains this evidence.


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
        document_store: Any = None,  # WHY: request-owned document reads and writes
    ) -> None:  # WHY: initialization returns nothing
        """Initialize SettleGateService with dependencies.

        Args:
            mist_client: MistApi client for cloud calls (required).
            db_router: DatabaseRouter for ArangoDB writes (required).
            audit_logger: AuditLogger for operation trail (required).
            document_store: Request-owned ArangoDB document handle.

        WHY: dependency injection pattern for testability and loose coupling.
        """
        # WHY: store Mist API client
        self.mist_client = mist_client  # WHY: cloud data source
        # WHY: store database router
        self.db_router = db_router  # WHY: persistent storage
        # WHY: store audit logger
        self.audit_logger = audit_logger  # WHY: operation trail
        self.document_store = document_store  # WHY: direct, verified portal persistence.
        # WHY: log initialization
        logger.info(
            "settle_gate_service_initialized",
            mist_client_available=mist_client is not None,  # WHY: dependency status
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
            document_store_available=document_store is not None,  # WHY: dependency status
        )  # WHY: startup event

    def wait_for_settle(
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

            # WHY: create check callables for parallel execution
            check_tasks = self._create_check_tasks(
                device_ids, run_id, site_id, org_id, settle_run_id
            )  # WHY: schedule device checks

            # WHY: execute all checks concurrently with timeout
            try:
                # WHY: run all checks in a thread pool and collect results with timeout
                with ThreadPoolExecutor(max_workers=self.MAX_WORKER_THREADS) as pool:  # WHY: bounded worker pool
                    futures = [pool.submit(check) for check in check_tasks]  # WHY: submit each device check
                    results = [  # WHY: collect results with timeout
                        future.result(timeout=timeout)  # WHY: per-future timeout
                        for future in futures  # WHY: each submitted check
                    ]  # WHY: ordered result list
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
            if settle_doc is None:  # A failed durable write or audit cannot produce a passing gate.
                return {}

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
                error_type=type(e).__name__,  # WHY: safe exception class only
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
                    error_message="The settle operation failed.",  # WHY: no dependency text reaches the audit record.
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
        if not self.mist_client or not self.db_router or self.document_store is None:
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
    ) -> dict[str, Any] | None:
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
        try:  # The driver acknowledgement does not prove the document was stored.
            collection = self.document_store.collection("settle_gates")
            collection.insert(settle_doc, overwrite=True)
            stored = collection.get(settle_doc["_key"])
        except Exception as fault:  # Keep the driver text out of the log and result.
            logger.error("settle_persist_failed", error_type=type(fault).__name__)
            return None
        if not self._settle_document_matches(stored, settle_doc, settle_run_id):
            return None
        if not self._audit_settle_results(settle_run_id, user_id, settle_doc, device_results):
            return None
        return settle_doc

    @staticmethod
    def _settle_document_matches(
        stored: Any,
        settle_doc: dict[str, Any],
        settle_run_id: str,
    ) -> bool:
        """Confirm that the settle document contains every required stored field."""
        expected_fields = (
            "settle_run_id",
            "run_id",
            "org_id",
            "site_id",
            "device_results",
            "device_count",
            "passed_count",
            "failed_count",
        )  # These fields prove the stored check result and its scope.
        matches = isinstance(stored, dict) and all(
            stored.get(field) == settle_doc[field] for field in expected_fields
        )  # Compare the actual document with the planned result.
        if not matches:  # A write acknowledgement cannot replace a verified read-back.
            logger.error("settle_readback_failed", settle_run_id=settle_run_id)
        return matches  # Only a matching document can support a success response.

    def _audit_settle_results(
        self,
        settle_run_id: str,
        user_id: str,
        settle_doc: dict[str, Any],
        device_results: dict[str, SettleResult],
    ) -> bool:
        """Write the completion audit record for the stored settle result."""
        if self.audit_logger is None:
            logger.error("settle_audit_unavailable", settle_run_id=settle_run_id)
            return False
        audit_id = self.audit_logger.log_operation(
            operation="settle_gate_complete",
            user_id=user_id,
            details={"settle_run_id": settle_run_id, "device_count": len(device_results)},
            result="success" if settle_doc["failed_count"] == 0 else "partial",
        )
        return audit_id is not None  # An audit failure blocks completion.

    def _create_check_tasks(
        self,
        device_ids: list[str],
        run_id: str,
        site_id: str,
        org_id: str,
        settle_run_id: str,
    ) -> list[Any]:
        """Create one validation task for each device."""
        # WHY: return callables so the thread pool runs each device check
        # WHY: a lambda per device keeps the bound arguments for that device
        return [
            lambda device_id=device_id: self._run_device_checks(  # WHY: one task per device
                device_id=device_id,  # WHY: device identifier
                run_id=run_id,  # WHY: run context
                site_id=site_id,  # WHY: site context
                org_id=org_id,  # WHY: org context
                settle_run_id=settle_run_id,  # WHY: settle run identifier
            )  # WHY: task callable
            for device_id in device_ids  # WHY: one task per device
        ]  # WHY: task list complete

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
                    error_type=type(result).__name__,
                )
                device_results[device_id] = SettleResult(
                    passed=False,
                    device_id=device_id,
                    failed_checks=["exception"],
                    details={"error_type": type(result).__name__},
                    timestamp=timestamp,
                )
            else:
                device_results[device_id] = result
        return device_results

    def _run_device_checks(
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

        check_results = self._execute_device_checks(device_id, run_id, site_id, org_id)  # Run every supported check.
        result = self._summarize_device_checks(device_id, settle_run_id, check_results)  # Collect verified outcomes.
        logger.debug(
            "settle_device_checks_complete",
            device_id=device_id,
            passed=result.passed,
            failed_checks=result.failed_checks,
        )  # Record the final device status.
        return result  # Return the evidence used by the settle gate.

    def _execute_device_checks(
        self,
        device_id: str,
        run_id: str,
        site_id: str,
        org_id: str,
    ) -> list[Any]:
        """Run each device check and retain exceptions as failed evidence."""
        check_tasks = [
            lambda: self._check_ping(device_id),
            lambda: self._check_api(device_id, site_id, org_id),
            lambda: self._check_firmware(device_id, site_id, org_id, run_id),
            lambda: self._check_neighbors(device_id, site_id, org_id),
        ]  # Bind the request scope to every check.
        check_results = []
        for check in check_tasks:
            try:
                check_results.append(check())
            except Exception as check_error:
                check_results.append(check_error)
        return check_results

    def _summarize_device_checks(
        self,
        device_id: str,
        settle_run_id: str,
        check_results: list[Any],
    ) -> SettleResult:
        """Convert device check results into one settle result."""
        check_names = ("ping", "api", "firmware", "neighbors")
        failed_checks = []
        details = {}
        for check_name, result in zip(check_names, check_results, strict=True):
            check_details, passed = self._check_result_details(device_id, check_name, result)
            details[check_name] = check_details
            if not passed:
                failed_checks.append(check_name)
        return SettleResult(
            passed=not failed_checks,
            device_id=device_id,
            failed_checks=failed_checks,
            details=details,
            settle_run_id=settle_run_id,
        )

    @staticmethod
    def _check_result_details(device_id: str, check_name: str, result: Any) -> tuple[dict[str, str], bool]:
        """Describe a successful, failed, or unsupported settle check."""
        if isinstance(result, Exception):
            logger.warning(
                "settle_check_failed",
                device_id=device_id,
                check_name=check_name,
                error_type=type(result).__name__,
            )  # Log the exception type without exposing driver text.
            return {"status": "failed", "error_type": type(result).__name__}, False
        if result:
            return {"status": "passed"}, True
        unavailable_reason = {
            "ping": "icmp_not_supported",
            "neighbors": "neighbor_reachability_not_supported",
        }.get(check_name)
        if unavailable_reason:
            return {"status": "unavailable", "reason": unavailable_reason}, False
        return {"status": "failed"}, False

    def _check_ping(self, device_id: str) -> bool:
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

                # WHY: run one ping attempt so the retry loop can wrap it
                return self._ping_once(device_id)  # WHY: single attempt

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_ping_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error_type=type(e).__name__,
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                time.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail

    def _ping_once(self, device_id: str) -> bool:
        """Run one ping attempt for a device.

        Args:
            device_id: Device ID to ping.

        Returns:
            True if the device responds.

        WHY: a single attempt the retry loop can wrap and test.
        """
        logger.warning("settle_ping_unavailable", device_id=device_id)
        return False  # No supported ICMP reader exists in this portal.

    def _check_api(self, device_id: str, site_id: str, org_id: str) -> bool:
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

                reading = read_device_statistics(self.mist_client, site_id)
                if reading.partial_reasons:
                    return False
                wanted = normalize_device_mac(device_id)
                return any(normalize_device_mac(row.get("mac")) == wanted for row in reading.records)

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_api_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error_type=type(e).__name__,
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                time.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail

    def _check_firmware(self, device_id: str, site_id: str, org_id: str, run_id: str) -> bool:
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

                run = self.document_store.collection("upgrade_runs").get(run_id)
                target_version = str(run.get("firmware_version", "")) if isinstance(run, dict) else ""
                if not target_version:
                    return False
                readings = RunningFirmwareVersionResolver(self.mist_client).fetch_site_running_versions(site_id)
                running_by_mac = {
                    normalize_device_mac(key): version for key, version in readings.items() if normalize_device_mac(key)
                }
                return running_by_mac.get(normalize_device_mac(device_id), "") == target_version

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_firmware_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error_type=type(e).__name__,
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                time.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail

    def _check_neighbors(self, device_id: str, site_id: str, org_id: str) -> bool:
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

                logger.warning("settle_neighbor_reachability_unavailable", device_id=device_id)
                return False  # Mist reports neighbors but does not prove their reachability.

            except Exception as e:  # WHY: catch errors
                # WHY: log attempt error
                logger.debug(
                    "settle_neighbors_error",  # WHY: debug event
                    device_id=device_id,  # WHY: device identifier
                    attempt=attempt + 1,  # WHY: attempt number
                    error_type=type(e).__name__,
                )  # WHY: error logged

                # WHY: if last attempt, raise exception
                if attempt == self.MAX_RETRIES - 1:  # WHY: check last attempt
                    raise  # WHY: propagate exception
                # WHY: wait before retry with exponential backoff
                time.sleep(self.RETRY_BACKOFF_SECONDS * (2**attempt))  # WHY: backoff sleep

        # WHY: should not reach here
        return False  # WHY: default fail
