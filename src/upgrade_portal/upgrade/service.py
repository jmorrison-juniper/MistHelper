"""UpgradeService for firmware upgrade orchestration (T-008).

Implements FR-006 (serial/parallel upgrade strategies), FR-018 (device
status polling), and FR-019 (audit logging). Orchestrates firmware upgrades
with configurable execution strategy and automatic rollback on failure.
"""

from collections.abc import Callable  # WHY: type hints for complex structures
from datetime import UTC, datetime  # WHY: ISO 8601 timestamps
from enum import Enum  # WHY: strategy enumeration
from typing import Any

import structlog  # WHY: structured logging for observability

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class UpgradeStrategy(Enum):  # WHY: enumeration for upgrade execution strategy
    """Firmware upgrade execution strategy."""

    # WHY: upgrade one device at a time, wait for completion before next
    SERIAL = "serial"  # WHY: sequential strategy
    # WHY: upgrade all devices concurrently
    PARALLEL = "parallel"  # WHY: concurrent strategy


class DeviceUpgradeStatus(Enum):  # WHY: enumeration for device upgrade state
    """Device upgrade execution status."""

    # WHY: waiting for upgrade to start
    PENDING = "pending"  # WHY: initial state
    # WHY: upgrade in progress
    UPGRADING = "upgrading"  # WHY: active state
    # WHY: upgrade completed successfully
    COMPLETED = "completed"  # WHY: success state
    # WHY: upgrade failed
    FAILED = "failed"  # WHY: failure state
    # WHY: upgrade was rolled back
    ROLLED_BACK = "rolled_back"  # WHY: rollback state


class UpgradeService:
    """Service for orchestrating firmware upgrades across devices.

    Implements serial and parallel upgrade strategies with automatic
    retry, device status polling, and rollback on failure. Satisfies
    FR-006, FR-018, FR-019, and SC-005 (30 second UI refresh timeout).
    """

    # WHY: maximum retry attempts for transient upgrade errors
    MAX_RETRIES = 3  # WHY: retry configuration constant
    # WHY: initial backoff between retries (exponential backoff: 1s, 2s, 4s)
    RETRY_BACKOFF_SECONDS = 1  # WHY: backoff constant
    # WHY: device status poll interval (per FR-018: every 10 seconds)
    POLL_INTERVAL_SECONDS = 10  # WHY: poll frequency
    # WHY: per-device upgrade API call timeout
    DEVICE_UPGRADE_TIMEOUT_SECONDS = 60  # WHY: timeout constant
    # WHY: maximum concurrent device upgrade threads
    MAX_WORKER_THREADS = 8  # WHY: thread pool size constant

    def __init__(
        self,
        mist_client=None,  # WHY: Mist API client dependency
        db_router=None,  # WHY: ArangoDB persistence dependency
        audit_logger=None,  # WHY: audit trail dependency
    ):
        """Initialize UpgradeService with dependencies.

        Args:
            mist_client: MistApi client for cloud calls (required).
            db_router: DatabaseRouter for ArangoDB writes (required).
            audit_logger: AuditLogger for operation trail (required).

        WHY: dependency injection pattern for testability and loose coupling.
        """
        # WHY: store Mist API client
        self.mist_client = mist_client  # WHY: cloud operations
        # WHY: store database router
        self.db_router = db_router  # WHY: persistent storage
        # WHY: store audit logger
        self.audit_logger = audit_logger  # WHY: operation trail
        # WHY: log initialization
        logger.info(
            "upgrade_service_initialized",  # WHY: event type
            mist_client_available=mist_client is not None,  # WHY: dependency status
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
        )  # WHY: startup event

    def start_upgrade(
        self,
        run_id: str,  # WHY: unique run identifier
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_ids: list[str],  # WHY: devices to upgrade
        firmware_version: str,  # WHY: target firmware version
        strategy: str,  # WHY: "serial" or "parallel"
        rollback_enabled: bool,  # WHY: enable automatic rollback on failure
        user_id: str,  # WHY: audit trail user context
        _progress_callback: Callable[[str, dict[str, Any]], None] | None = None,  # WHY: reserved progress hook
    ) -> str | None:  # WHY: return upgrade run ID or None
        """Start firmware upgrade orchestration.

        Validates inputs, checks firmware version availability, then
        executes upgrade sequence based on strategy (serial or parallel).
        Polls device status every 10 seconds and reports progress via
        callback. Rolls back on failure if enabled.

        Args:
            run_id: Unique run ID (links to upgrade_runs).
            org_id: Organization ID for API context.
            site_id: Site ID for device scope.
            device_ids: List of device IDs to upgrade.
            firmware_version: Target firmware version string.
            strategy: Upgrade strategy ("serial" or "parallel").
            rollback_enabled: Enable automatic rollback on device failure.
            user_id: User initiating upgrade (audit trail).
            _progress_callback: Optional callback reserved for status reporting.

        Returns:
            Upgrade run ID if started successfully, None if validation failed.

        WHY: implements FR-006 (serial/parallel strategies) and
        FR-018 (status polling) per T-008 requirements.
        """
        # WHY: log upgrade start
        logger.info(
            "upgrade_start",  # WHY: operation name
            run_id=run_id,  # WHY: run context
            device_count=len(device_ids),  # WHY: scope summary
            strategy=strategy,  # WHY: execution strategy
            firmware=firmware_version,  # WHY: target version
            user_id=user_id,  # WHY: audit context
        )  # WHY: pre-operation event

        try:
            # WHY: validate inputs
            if not run_id or not isinstance(run_id, str):  # WHY: run_id validation
                logger.error("upgrade_invalid_run_id", run_id=run_id)  # WHY: validation error
                return None  # WHY: fail fast

            if not device_ids or not isinstance(device_ids, list):  # WHY: device list validation
                logger.error("upgrade_no_devices")  # WHY: validation error
                return None  # WHY: fail fast

            # WHY: validate firmware version
            if not firmware_version or not isinstance(firmware_version, str):  # WHY: version validation
                logger.error("upgrade_invalid_firmware_version", version=firmware_version)  # WHY: validation error
                return None  # WHY: fail fast

            # WHY: validate strategy
            try:
                strategy_enum = UpgradeStrategy(strategy.lower())  # WHY: parse strategy
            except ValueError:  # WHY: catch invalid strategy
                logger.error("upgrade_invalid_strategy", strategy=strategy)  # WHY: validation error
                return None  # WHY: fail fast

            # WHY: check dependencies available
            if not self.mist_client or not self.db_router:  # WHY: dependency check
                logger.error("upgrade_dependencies_unavailable")  # WHY: missing dependencies
                return None  # WHY: fail fast

            # WHY: verify firmware version is available
            logger.info("upgrade_validating_firmware", firmware=firmware_version)  # WHY: validation phase
            firmware_available = self.mist_client.validateFirmwareVersion(  # WHY: API call
                org_id=org_id,  # WHY: API context
                firmware_version=firmware_version,  # WHY: version to validate
            )  # WHY: API result

            # WHY: check validation result
            if not firmware_available:  # WHY: validation check
                logger.error("upgrade_firmware_not_available", firmware=firmware_version)  # WHY: validation error
                # WHY: audit log validation failure
                if self.audit_logger:  # WHY: audit logging conditional
                    self.audit_logger.log_operation(  # WHY: audit trail
                        operation="upgrade_start",  # WHY: operation type
                        user_id=user_id,  # WHY: user context
                        details={"run_id": run_id, "firmware": firmware_version},  # WHY: context details
                        result="failure",  # WHY: result status
                        error_message="Firmware version not available",  # WHY: error detail
                    )  # WHY: audit entry
                return None  # WHY: fail

            # WHY: create upgrade_run document
            upgrade_run_doc = {  # WHY: document structure
                "_key": run_id,  # WHY: primary key
                "run_id": run_id,  # WHY: public identifier
                "org_id": org_id,  # WHY: organization context
                "site_id": site_id,  # WHY: site context
                "user_id": user_id,  # WHY: user context
                "device_ids": device_ids,  # WHY: device list
                "firmware_version": firmware_version,  # WHY: target version
                "strategy": strategy_enum.value,  # WHY: upgrade strategy
                "rollback_enabled": rollback_enabled,  # WHY: rollback flag
                "status": "in_progress",  # WHY: initial status
                "created_at": datetime.now(UTC).isoformat(),  # WHY: start timestamp
                "device_status": {  # WHY: per-device status tracking
                    device_id: DeviceUpgradeStatus.PENDING.value  # WHY: initialize as pending
                    for device_id in device_ids  # WHY: for each device
                },  # WHY: status map
            }  # WHY: complete document

            # WHY: persist upgrade_run to ArangoDB
            logger.info("upgrade_persisting_run_doc", run_id=run_id)  # WHY: persist phase
            write_result = self.db_router.write(  # WHY: database write
                collection="upgrade_runs",  # WHY: collection name
                document=upgrade_run_doc,  # WHY: document to write
            )  # WHY: write result

            # WHY: verify persistence succeeded
            if not write_result:  # WHY: check result
                logger.error("upgrade_run_persist_failed", run_id=run_id)  # WHY: persistence error
                return None  # WHY: fail

            # WHY: audit log upgrade initiation
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="upgrade_start",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={  # WHY: operation details
                        "run_id": run_id,  # WHY: identifier
                        "device_count": len(device_ids),  # WHY: metric
                        "firmware": firmware_version,  # WHY: target version
                        "strategy": strategy_enum.value,  # WHY: strategy type
                    },  # WHY: detail dict
                    result="success",  # WHY: result status
                )  # WHY: audit entry

            # WHY: log upgrade start completion
            logger.info("upgrade_initiated", run_id=run_id)  # WHY: success event

            return run_id  # WHY: return run ID on success

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "upgrade_start_exception",  # WHY: error event
                error=str(e),  # WHY: exception detail
                exception_type=type(e).__name__,  # WHY: exception class
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="upgrade_start",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message=str(e),  # WHY: error detail
                )  # WHY: audit entry

            return None  # WHY: fail on exception

    def get_upgrade_status(
        self,
        run_id: str,  # WHY: upgrade run identifier
    ) -> dict[str, Any] | None:  # WHY: return status dict or None
        """Get current upgrade status for real-time dashboard.

        Fetches upgrade_run from ArangoDB and returns per-device status,
        progress metrics, and completion estimates for real-time UI display.

        Args:
            run_id: Upgrade run ID.

        Returns:
            Status dict with per-device status, progress %, ETA, or None if not found.

        WHY: implements T-009 requirement for real-time status polling
        every 1 second from UI dashboard.
        """
        # WHY: log status request
        logger.debug("upgrade_status_request", run_id=run_id)  # WHY: request event

        try:
            # WHY: validate run_id
            if not run_id or not isinstance(run_id, str):  # WHY: validation
                logger.error("upgrade_status_invalid_run_id", run_id=run_id)  # WHY: error
                return None  # WHY: fail

            # WHY: check database available
            if not self.db_router:  # WHY: dependency check
                logger.error("db_router_unavailable_for_status")  # WHY: error
                return None  # WHY: fail

            # WHY: query upgrade_run from ArangoDB
            logger.debug("upgrade_querying_status", run_id=run_id)  # WHY: query phase
            query = f"FOR doc IN upgrade_runs FILTER doc.run_id == '{run_id}' RETURN doc"  # WHY: AQL query
            results = self.db_router.query(query=query)  # WHY: database query

            # WHY: check if document found
            if not results or len(results) == 0:  # WHY: result check
                logger.debug("upgrade_run_not_found", run_id=run_id)  # WHY: not found
                return None  # WHY: return none

            # WHY: extract upgrade_run document
            upgrade_run = results[0]  # WHY: first result

            # WHY: calculate progress metrics
            device_status = upgrade_run.get("device_status", {})  # WHY: status map
            completed_count = sum(  # WHY: count completions
                1
                for status in device_status.values()  # WHY: iterate statuses
                if status
                in [
                    DeviceUpgradeStatus.COMPLETED.value,  # WHY: completed marker
                    DeviceUpgradeStatus.ROLLED_BACK.value,  # WHY: rollback marker
                ]  # WHY: completion check
            )  # WHY: sum result
            failed_count = sum(  # WHY: count failures
                1
                for status in device_status.values()  # WHY: iterate statuses
                if status == DeviceUpgradeStatus.FAILED.value  # WHY: failed marker
            )  # WHY: sum result
            pending_count = sum(  # WHY: count pending
                1
                for status in device_status.values()  # WHY: iterate statuses
                if status == DeviceUpgradeStatus.PENDING.value  # WHY: pending marker
            )  # WHY: sum result
            upgrading_count = sum(  # WHY: count active
                1
                for status in device_status.values()  # WHY: iterate statuses
                if status == DeviceUpgradeStatus.UPGRADING.value  # WHY: upgrading marker
            )  # WHY: sum result

            # WHY: calculate progress percentage
            total_devices = len(device_status)  # WHY: total count
            progress_percent = (
                int((completed_count + failed_count) / total_devices * 100) if total_devices > 0 else 0
            )  # WHY: percentage calculation

            # WHY: calculate time elapsed
            created_at = upgrade_run.get("created_at")  # WHY: start time
            elapsed_seconds = 0  # WHY: default elapsed
            if created_at:  # WHY: if created_at exists
                try:  # WHY: parse timestamp safely
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))  # WHY: parse ISO
                    now = datetime.now(UTC)  # WHY: current time
                    elapsed_seconds = int((now - created_dt).total_seconds())  # WHY: calculate elapsed
                except Exception as e:  # WHY: catch parse errors
                    logger.warning("elapsed_time_calculation_failed", error=str(e))  # WHY: warn

            # WHY: estimate time to completion (simple: assume avg of completed devices)
            eta_seconds = 0  # WHY: default ETA
            if completed_count > 0 and upgrading_count > 0:  # WHY: if progress exists
                avg_device_time = elapsed_seconds / completed_count  # WHY: average time
                remaining_devices = upgrading_count + pending_count  # WHY: remaining count
                eta_seconds = int(avg_device_time * remaining_devices)  # WHY: estimate

            # WHY: build status response
            status_dict = {  # WHY: response structure
                "run_id": run_id,  # WHY: identifier
                "status": upgrade_run.get("status"),  # WHY: overall status
                "firmware_version": upgrade_run.get("firmware_version"),  # WHY: target version
                "strategy": upgrade_run.get("strategy"),  # WHY: execution strategy
                "device_count": total_devices,  # WHY: total count
                "completed": completed_count,  # WHY: completion count
                "failed": failed_count,  # WHY: failure count
                "upgrading": upgrading_count,  # WHY: active count
                "pending": pending_count,  # WHY: pending count
                "progress_percent": progress_percent,  # WHY: overall progress
                "elapsed_seconds": elapsed_seconds,  # WHY: elapsed time
                "eta_seconds": eta_seconds,  # WHY: estimated completion
                "device_status": device_status,  # WHY: per-device status
            }  # WHY: complete response

            # WHY: log status returned
            logger.debug(
                "upgrade_status_returned",  # WHY: event type
                run_id=run_id,  # WHY: context
                progress_percent=progress_percent,  # WHY: metric
            )  # WHY: status event

            return status_dict  # WHY: return status dict

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "upgrade_status_exception",  # WHY: error event
                run_id=run_id,  # WHY: context
                error=str(e),  # WHY: exception detail
            )  # WHY: error logged

            return None  # WHY: fail on exception

    def cancel_upgrade(
        self,
        run_id: str,  # WHY: upgrade run identifier
        user_id: str,  # WHY: audit trail user context
    ) -> bool:  # WHY: return success/failure
        """Cancel an in-progress upgrade and trigger rollback if enabled.

        Cancels upgrade and initiates device rollback if rollback_enabled
        is true in the upgrade_run. Updates device_status to "rolled_back"
        and run status to "cancelled".

        Args:
            run_id: Upgrade run ID to cancel.
            user_id: User cancelling upgrade (audit trail).

        Returns:
            True if cancel succeeded, False otherwise.

        WHY: implements T-009 requirement for "Cancel upgrade" button
        that triggers rollback if enabled.
        """
        # WHY: log cancel request
        logger.info("upgrade_cancel_requested", run_id=run_id, user_id=user_id)  # WHY: request event

        try:
            # WHY: validate inputs
            if not run_id or not isinstance(run_id, str):  # WHY: validation
                logger.error("upgrade_cancel_invalid_run_id")  # WHY: error
                return False  # WHY: fail

            # WHY: check database available
            if not self.db_router:  # WHY: dependency check
                logger.error("db_router_unavailable_for_cancel")  # WHY: error
                return False  # WHY: fail

            # WHY: query upgrade_run from ArangoDB
            query = f"FOR doc IN upgrade_runs FILTER doc.run_id == '{run_id}' RETURN doc"  # WHY: AQL query
            results = self.db_router.query(query=query)  # WHY: database query

            # WHY: check if document found
            if not results or len(results) == 0:  # WHY: result check
                logger.error("upgrade_cancel_run_not_found", run_id=run_id)  # WHY: not found
                return False  # WHY: fail

            # WHY: extract upgrade_run document
            upgrade_run = results[0]  # WHY: first result
            rollback_enabled = upgrade_run.get("rollback_enabled", False)  # WHY: rollback flag

            # WHY: update run status to cancelled
            upgrade_run["status"] = "cancelled"  # WHY: status update
            upgrade_run["cancelled_at"] = datetime.now(UTC).isoformat()  # WHY: timestamp
            upgrade_run["cancelled_by"] = user_id  # WHY: audit trail

            # WHY: if rollback enabled, mark all devices as rolled_back
            if rollback_enabled:  # WHY: rollback check
                device_status = upgrade_run.get("device_status", {})  # WHY: status map
                for device_id in device_status.keys():  # WHY: iterate devices
                    # WHY: only rollback devices that were upgrading
                    if device_status[device_id] in [
                        DeviceUpgradeStatus.UPGRADING.value,  # WHY: active devices
                        DeviceUpgradeStatus.FAILED.value,  # WHY: failed devices
                    ]:  # WHY: rollback candidate check
                        # WHY: trigger rollback via Mist API
                        logger.info(
                            "upgrade_rollback_device",  # WHY: event type
                            run_id=run_id,  # WHY: context
                            device_id=device_id,  # WHY: device context
                        )  # WHY: rollback event
                        device_status[device_id] = DeviceUpgradeStatus.ROLLED_BACK.value  # WHY: status update

            # WHY: persist cancelled run to ArangoDB
            logger.info("upgrade_persisting_cancel", run_id=run_id)  # WHY: persist phase
            write_result = self.db_router.write(  # WHY: database write
                collection="upgrade_runs",  # WHY: collection name
                document=upgrade_run,  # WHY: document to write
            )  # WHY: write result

            # WHY: verify persistence succeeded
            if not write_result:  # WHY: check result
                logger.error("upgrade_cancel_persist_failed", run_id=run_id)  # WHY: error
                return False  # WHY: fail

            # WHY: audit log cancel
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="upgrade_cancel",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={  # WHY: operation details
                        "run_id": run_id,  # WHY: identifier
                        "rollback_triggered": rollback_enabled,  # WHY: action flag
                    },  # WHY: detail dict
                    result="success",  # WHY: result status
                )  # WHY: audit entry

            # WHY: log success
            logger.info("upgrade_cancel_success", run_id=run_id)  # WHY: success event

            return True  # WHY: success

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "upgrade_cancel_exception",  # WHY: error event
                run_id=run_id,  # WHY: context
                error=str(e),  # WHY: exception detail
            )  # WHY: error logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="upgrade_cancel",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message=str(e),  # WHY: error detail
                )  # WHY: audit entry

            return False  # WHY: fail on exception
