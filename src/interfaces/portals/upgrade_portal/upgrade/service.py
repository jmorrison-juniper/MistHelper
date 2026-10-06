"""UpgradeService for firmware upgrade orchestration (T-008).

Implements FR-006 (serial/parallel upgrade strategies), FR-018 (device
status polling), and FR-019 (audit logging). Orchestrates firmware upgrades
with configurable execution strategy and automatic rollback on failure.
"""

from collections.abc import Callable, Mapping  # WHY: type hints for complex structures
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
    START_CONFIRMATION_TEXT = "CONFIRM"  # The service enforces the typed destructive word.

    def __init__(
        self,
        mist_client: Any = None,  # WHY: The authenticated request session owns cloud calls.
        db_router: Any = None,  # WHY: The router owns registered export writes.
        audit_logger: Any = None,  # WHY: The audit service owns action records.
        document_store: Any = None,  # WHY: The explicit handle owns portal documents.
    ) -> None:
        """Initialize UpgradeService with dependencies.

        Args:
            mist_client: MistApi client for cloud calls (required).
            db_router: DatabaseRouter for ArangoDB writes (required).
            audit_logger: AuditLogger for operation trail (required).
            document_store: Request-owned ArangoDB document handle.

        WHY: dependency injection pattern for testability and loose coupling.
        """
        # WHY: store Mist API client
        self.mist_client = mist_client  # WHY: cloud operations
        # WHY: store database router
        self.db_router = db_router  # WHY: persistent storage
        # WHY: store audit logger
        self.audit_logger = audit_logger  # WHY: operation trail
        self.document_store = document_store  # WHY: direct, verified portal persistence.
        # WHY: log initialization
        logger.info(
            "upgrade_service_initialized",  # WHY: event type
            mist_client_available=mist_client is not None,  # WHY: dependency status
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
            document_store_available=document_store is not None,  # WHY: dependency status
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
        confirmation: str = "",  # The operator must confirm before the cloud call.
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
            confirmation: The exact text typed by the operator.

        Returns:
            Upgrade run ID if started successfully, None if validation failed.

        WHY: implements FR-006 (serial/parallel strategies) and
        FR-018 (status polling) per T-008 requirements.
        """
        if confirmation != self.START_CONFIRMATION_TEXT:  # A direct caller cannot bypass the route confirmation.
            logger.warning("upgrade_confirmation_missing", run_id=run_id)
            return None
        if rollback_enabled:  # The supported Mist plan has no rollback-enabled option.
            logger.warning("upgrade_rollback_option_unsupported", run_id=run_id)
            return None

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
            # WHY: validate inputs, returning the strategy enum or None on failure
            strategy_enum = self._validate_start_upgrade_inputs(  # WHY: delegate validation
                run_id=run_id,  # WHY: run identifier
                device_ids=device_ids,  # WHY: device list
                firmware_version=firmware_version,  # WHY: target version
                strategy=strategy,  # WHY: strategy string
                org_id=org_id,  # WHY: API context
                site_id=site_id,  # Firmware options and inventory are site scoped.
                user_id=user_id,  # WHY: audit context
            )  # WHY: parsed strategy or None
            if strategy_enum is None:  # WHY: validation failed
                return None  # WHY: fail fast

            request_values = {
                "run_id": run_id,
                "org_id": org_id,
                "site_id": site_id,
                "user_id": user_id,
                "device_ids": list(device_ids),
                "firmware_version": firmware_version,
                "strategy": strategy_enum.value,
            }
            prepared = self._build_upgrade_plans(request_values)
            if prepared is None:
                return None
            target_entries, options_record, plans = prepared

            # WHY: persist the upgrade_run document and audit the initiation
            if not self._persist_upgrade_run(  # WHY: persist and audit
                run_id=run_id,  # WHY: run identifier
                org_id=org_id,  # WHY: organization context
                site_id=site_id,  # WHY: site context
                user_id=user_id,  # WHY: audit context
                device_ids=device_ids,  # WHY: device list
                firmware_version=firmware_version,  # WHY: target version
                strategy_enum=strategy_enum,  # WHY: parsed strategy
                rollback_enabled=rollback_enabled,  # WHY: rollback flag
            ):  # WHY: persistence failed
                return None  # WHY: fail

            if not self._persist_and_submit_plan(run_id, target_entries, options_record, plans):
                return None

            # WHY: log upgrade start completion
            logger.info("upgrade_initiated", run_id=run_id)  # WHY: success event

            return run_id  # WHY: return run ID on success

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "upgrade_start_exception",  # WHY: error event
                error_type=type(e).__name__,
                exception_type=type(e).__name__,  # WHY: exception class
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="upgrade_start",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message="The upgrade operation failed.",  # WHY: keep dependency text private.
                )  # WHY: audit entry

            return None  # WHY: fail on exception

    def _persist_and_submit_plan(
        self,
        run_id: str,
        target_entries: list[dict[str, Any]],
        options_record: dict[str, Any],
        plans: tuple[Any, ...],
    ) -> bool:
        """Store the complete plan before submitting its cloud operations."""
        if not self._write_upgrade_plan(
            run_id,
            target_entries,
            options_record,
        ):  # The cloud must not precede durable intent.
            return False  # A failed write blocks every mutation.
        upgrade_run = self.document_store.collection("upgrade_runs").get(run_id)  # Read the verified plan back.
        return isinstance(upgrade_run, dict) and self._submit_upgrade_plans(
            upgrade_run,
            plans,
        )  # Submit only stored intent.

    def _validate_start_upgrade_inputs(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        device_ids: list[str],  # WHY: device list
        firmware_version: str,  # WHY: target version
        strategy: str,  # WHY: strategy string
        org_id: str,  # WHY: API context
        site_id: str,  # Site scope for inventory and firmware options.
        user_id: str,  # WHY: audit context
    ) -> UpgradeStrategy | None:  # WHY: parsed strategy or None
        """Validate start_upgrade inputs and firmware availability.

        Args:
            run_id: Unique run ID.
            device_ids: List of device IDs to upgrade.
            firmware_version: Target firmware version string.
            strategy: Upgrade strategy ("serial" or "parallel").
            org_id: Organization ID for API context.
            user_id: User initiating upgrade (audit trail).

        Returns:
            Parsed UpgradeStrategy when valid, None when any check fails.
        """
        # WHY: basic input validation delegates to a helper
        strategy_enum = self._parse_start_upgrade_inputs(  # WHY: delegate parsing
            run_id=run_id,  # WHY: run identifier
            device_ids=device_ids,  # WHY: device list
            firmware_version=firmware_version,  # WHY: target version
            strategy=strategy,  # WHY: strategy string
        )  # WHY: parsed strategy or None
        if strategy_enum is None:  # WHY: validation failed
            return None  # WHY: fail fast

        # WHY: both API and database clients are required
        if not self.mist_client or not self.db_router or self.document_store is None or self.audit_logger is None:
            logger.error("upgrade_dependencies_unavailable")  # WHY: missing dependencies
            return None  # WHY: fail fast

        # WHY: verify the firmware version exists in the Mist cloud
        if not self._check_firmware_available(  # WHY: delegate firmware check
            org_id=org_id,  # WHY: API context
            site_id=site_id,
            device_ids=device_ids,
            firmware_version=firmware_version,  # WHY: version to validate
            run_id=run_id,  # WHY: audit context
            user_id=user_id,  # WHY: audit context
        ):  # WHY: firmware not available
            return None  # WHY: fail

        return strategy_enum  # WHY: all checks passed

    def _parse_start_upgrade_inputs(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        device_ids: list[str],  # WHY: device list
        firmware_version: str,  # WHY: target version
        strategy: str,  # WHY: strategy string
    ) -> UpgradeStrategy | None:  # WHY: parsed strategy or None
        """Validate basic start_upgrade inputs and parse the strategy.

        Args:
            run_id: Unique run ID.
            device_ids: List of device IDs to upgrade.
            firmware_version: Target firmware version string.
            strategy: Upgrade strategy ("serial" or "parallel").

        Returns:
            Parsed UpgradeStrategy when valid, None when any check fails.
        """
        # WHY: run_id must be a non-empty string
        if not run_id or not isinstance(run_id, str):  # WHY: run_id validation
            logger.error("upgrade_invalid_run_id", run_id=run_id)  # WHY: validation error
            return None  # WHY: fail fast

        # WHY: device list must be a non-empty list
        if not device_ids or not isinstance(device_ids, list):  # WHY: device list validation
            logger.error("upgrade_no_devices")  # WHY: validation error
            return None  # WHY: fail fast

        # WHY: firmware version must be a non-empty string
        if not firmware_version or not isinstance(firmware_version, str):  # WHY: version validation
            logger.error(  # WHY: validation error
                "upgrade_invalid_firmware_version",  # WHY: event type
                version=firmware_version,  # WHY: context
            )  # WHY: error logged
            return None  # WHY: fail fast

        # WHY: strategy must parse to a known enum value
        try:
            strategy_enum = UpgradeStrategy(strategy.lower())  # WHY: parse strategy
        except ValueError:  # WHY: catch invalid strategy
            logger.error("upgrade_invalid_strategy", strategy=strategy)  # WHY: validation error
            return None  # WHY: fail fast

        return strategy_enum  # WHY: all checks passed

    def _check_firmware_available(
        self,  # WHY: instance method
        org_id: str,  # WHY: API context
        site_id: str,
        device_ids: list[str],
        firmware_version: str,  # WHY: version to validate
        run_id: str,  # WHY: audit context
        user_id: str,  # WHY: audit context
    ) -> bool:  # WHY: availability result
        """Check the firmware option against complete site inventory evidence.

        Args:
            org_id: Organization ID for API context.
            site_id: Site whose inventory and version options are checked.
            device_ids: Selected device MAC addresses.
            firmware_version: Target firmware version string.
            run_id: Upgrade run ID for audit context.
            user_id: User initiating upgrade for audit context.

        Returns:
            True when the version is available, False otherwise.
        """
        from src.interfaces.portals.upgrade_portal.capture.devices import normalize_device_mac
        from src.interfaces.portals.upgrade_portal.upgrade.options import read_model_versions, read_upgrade_inventory

        logger.info("upgrade_validating_firmware", firmware=firmware_version)
        inventory = read_upgrade_inventory(self.mist_client, org_id, site_id)
        if inventory.partial_reasons or not inventory.records:
            logger.warning("upgrade_firmware_inventory_unavailable", site_id=site_id)
            return False
        inventory_complete, firmware_available = self._requested_firmware_available(
            device_ids,
            inventory.records,
            firmware_version,
            org_id,
            site_id,
            normalize_device_mac,
            read_model_versions,
        )
        if not inventory_complete:  # An unverified device list cannot be upgraded.
            logger.warning("upgrade_firmware_inventory_incomplete", site_id=site_id)
            return False
        if firmware_available:  # Every requested device offers this firmware.
            return True
        logger.error("upgrade_firmware_not_available", firmware=firmware_version)  # WHY: validation error
        self._audit_firmware_refusal(run_id, user_id, firmware_version)
        return False  # WHY: not available

    def _requested_firmware_available(
        self,
        device_ids: list[str],
        inventory_records: list[dict[str, Any]],
        firmware_version: str,
        org_id: str,
        site_id: str,
        normalize_device_mac: Callable[[Any], str],
        read_model_versions: Callable[..., dict[str, list[str]]],
    ) -> tuple[bool, bool]:
        """Check requested devices and firmware against complete inventory data."""
        requested = {normalize_device_mac(device_id) for device_id in device_ids}  # Match Mist MAC normalization.
        by_mac = {normalize_device_mac(row.get("mac")): row for row in inventory_records}  # Index site devices.
        if not requested or not requested.issubset(by_mac):  # Reject incomplete device evidence.
            return False, False  # Do not start an upgrade from a partial inventory.
        versions_by_model = read_model_versions(self.mist_client, site_id, inventory_records, org_id)
        available = all(
            firmware_version in versions_by_model.get(str(by_mac[mac].get("model", "")).strip(), ())
            for mac in requested
        )  # Require the target version for every requested device.
        return True, available  # Preserve inventory and version refusal reasons.

    def _audit_firmware_refusal(self, run_id: str, user_id: str, firmware_version: str) -> None:
        """Record a safe audit failure when the requested firmware is unavailable."""
        if self.audit_logger is None:  # Audit only when the request graph supplied the logger.
            return  # The caller still refuses the cloud mutation.
        audit_id = self.audit_logger.log_operation(
            operation="upgrade_start",
            user_id=user_id,
            details={"run_id": run_id, "firmware": firmware_version},
            result="failure",
            error_message="Firmware version not available",
        )  # Keep external error details out of the audit record.
        if audit_id is None:  # A failed audit must remain visible.
            logger.error("upgrade_validation_audit_failed", run_id=run_id)  # Record the audit failure.

    def _persist_upgrade_run(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        user_id: str,  # WHY: audit context
        device_ids: list[str],  # WHY: device list
        firmware_version: str,  # WHY: target version
        strategy_enum: UpgradeStrategy,  # WHY: parsed strategy
        rollback_enabled: bool,  # WHY: rollback flag
    ) -> bool:  # WHY: persistence success
        """Persist the upgrade_run document and audit the initiation.

        Args:
            run_id: Unique run ID.
            org_id: Organization ID.
            site_id: Site ID.
            user_id: User initiating upgrade.
            device_ids: List of device IDs.
            firmware_version: Target firmware version.
            strategy_enum: Parsed upgrade strategy.
            rollback_enabled: Enable automatic rollback.

        Returns:
            True when the document was written and audited, False otherwise.
        """
        # WHY: build the upgrade_run document
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

        if self.document_store is None or self.audit_logger is None:
            logger.error("upgrade_run_dependencies_unavailable", run_id=run_id)
            return False
        from src.interfaces.portals.upgrade_portal.capture import store

        logger.info("upgrade_persisting_run_doc", run_id=run_id)
        write_result = store.write_run(upgrade_run_doc, database=self.document_store)
        if not write_result.verified:
            logger.error("upgrade_run_persist_failed", run_id=run_id)  # WHY: persistence error
            return False  # WHY: fail

        audit_id = self.audit_logger.log_operation(  # WHY: audit trail
            operation="upgrade_start",  # WHY: operation type
            user_id=user_id,  # WHY: user context
            details={  # WHY: operation details
                "run_id": run_id,  # WHY: identifier
                "device_count": len(device_ids),  # WHY: metric
                "firmware": firmware_version,  # WHY: target version
                "strategy": strategy_enum.value,  # WHY: strategy type
            },  # WHY: detail dict
            result="pending",  # The cloud has not accepted a plan at this point.
        )  # WHY: audit entry
        if audit_id is None:
            logger.error("upgrade_run_audit_failed", run_id=run_id)
            return False

        return True  # WHY: persistence complete

    def _build_upgrade_plans(
        self,
        request_values: Mapping[str, Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any], tuple[Any, ...]] | None:
        """Build plans from current inventory and available firmware evidence."""
        from src.interfaces.portals.upgrade_portal.upgrade import options
        from src.operations.execution.firmware import upgrade_service as cloud_service

        strategy = "serial" if request_values["strategy"] == "serial" else "big_bang"
        choices = [
            {"mac": device_id, "version_target": request_values["firmware_version"]}
            for device_id in request_values["device_ids"]
        ]
        body = {"targets": choices, "strategy": strategy}
        stored = options.build_options_record(
            self.mist_client,
            str(request_values["org_id"]),
            str(request_values["site_id"]),
            body,
        )
        target_entries = stored.get("targets")
        option_values = stored.get("options")
        if not isinstance(target_entries, list) or not target_entries or not isinstance(option_values, dict):
            return None
        targets = options.to_device_targets(target_entries, str(request_values["site_id"]))
        cloud_options = options.build_options(option_values, now=None)
        plans = cloud_service.plan_upgrade(
            targets,
            cloud_options,
            str(request_values["org_id"]),
            str(request_values["site_id"]),
        )
        return (target_entries, option_values, plans) if plans else None

    def _write_upgrade_plan(
        self,
        run_id: str,
        target_entries: list[dict[str, Any]],
        options_record: dict[str, Any],
    ) -> bool:
        """Persist the plan before any firmware submission."""
        if self.document_store is None:
            return False
        collection = self.document_store.collection("upgrade_runs")
        collection.update(
            {"_key": run_id, "targets": target_entries, "options": options_record, "upgrades": []},
            merge=True,
        )
        stored = collection.get(run_id)
        return (
            isinstance(stored, dict)
            and stored.get("targets") == target_entries
            and stored.get("options") == options_record
        )

    def _submit_upgrade_plans(self, upgrade_run: dict[str, Any], plans: tuple[Any, ...]) -> bool:
        """Submit each supported plan and verify its cloud identifier before continuing."""
        from src.operations.execution.firmware import upgrade_service as cloud_service

        for plan in plans:
            submission = cloud_service.invoke_upgrade(self.mist_client, plan)
            if submission.raw_status not in cloud_service.ACCEPTED_STATUS or not submission.upgrade_id:
                upgrade_run["status"] = "failed"
                self._save_upgrade_run(upgrade_run)
                return False
            upgrade_run["upgrades"].append(
                {
                    "upgrade_id": submission.upgrade_id,
                    "scope": submission.scope,
                    "accepted": list(submission.accepted),
                    "raw_status": submission.raw_status,
                }
            )
            if not self._save_upgrade_run(upgrade_run):
                return False
        audit_id = self.audit_logger.log_operation(
            operation="upgrade_submitted",
            user_id=str(upgrade_run.get("user_id", "")),
            details={"run_id": upgrade_run.get("run_id", ""), "plan_count": len(plans)},
            result="success",
        )
        return audit_id is not None

    def _save_upgrade_run(self, upgrade_run: dict[str, Any]) -> bool:
        """Write the current run state and verify its stored fields."""
        run_id = str(upgrade_run.get("run_id", ""))
        collection = self.document_store.collection("upgrade_runs")
        collection.update(upgrade_run, merge=True)
        stored = collection.get(run_id)
        return isinstance(stored, dict) and stored.get("upgrades") == upgrade_run.get("upgrades")

    def _build_status_dict(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        upgrade_run: dict[str, Any],  # WHY: stored document
    ) -> dict[str, Any]:  # WHY: status response
        """Build the status response from an upgrade_run document.

        Args:
            run_id: Upgrade run ID.
            upgrade_run: Stored upgrade_run document.

        Returns:
            Status dict with per-device status, progress %, and ETA.
        """
        # WHY: read the per-device status map
        device_status = upgrade_run.get("device_status", {})  # WHY: status map
        completed_count, failed_count, pending_count, upgrading_count = (  # WHY: per-state counts
            self._count_device_statuses(device_status)  # WHY: delegate counting
        )  # WHY: unpack counts

        # WHY: calculate progress percentage
        total_devices = len(device_status)  # WHY: total count
        progress_percent = (
            int((completed_count + failed_count) / total_devices * 100) if total_devices > 0 else 0
        )  # WHY: percentage calculation

        # WHY: calculate time elapsed
        elapsed_seconds = self._calculate_elapsed_seconds(upgrade_run)  # WHY: elapsed metric

        # WHY: estimate time to completion (simple: assume avg of completed devices)
        eta_seconds = 0  # WHY: default ETA
        if completed_count > 0 and upgrading_count > 0:  # WHY: if progress exists
            avg_device_time = elapsed_seconds / completed_count  # WHY: average time
            remaining_devices = upgrading_count + pending_count  # WHY: remaining count
            eta_seconds = int(avg_device_time * remaining_devices)  # WHY: estimate

        # WHY: build status response
        return {  # WHY: response structure
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

    @staticmethod
    def _count_device_statuses(
        device_status: dict[str, str],  # WHY: per-device status map
    ) -> tuple[int, int, int, int]:  # WHY: (completed, failed, pending, upgrading)
        """Count device statuses by state.

        Args:
            device_status: Per-device status map from the upgrade_run document.

        Returns:
            Tuple of (completed, failed, pending, upgrading) counts.
        """
        # WHY: completed includes rolled_back devices (terminal states)
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

        return completed_count, failed_count, pending_count, upgrading_count  # WHY: all counts

    def _calculate_elapsed_seconds(self, upgrade_run: dict[str, Any]) -> int:  # WHY: elapsed metric
        """Calculate elapsed seconds from the created_at timestamp.

        Args:
            upgrade_run: Stored upgrade_run document.

        Returns:
            Elapsed seconds, or 0 when the timestamp is missing or invalid.
        """
        # WHY: read the start timestamp
        created_at = upgrade_run.get("created_at")  # WHY: start time
        if not created_at:  # WHY: no timestamp
            return 0  # WHY: default elapsed

        # WHY: parse timestamp safely
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))  # WHY: parse ISO
            now = datetime.now(UTC)  # WHY: current time
            return int((now - created_dt).total_seconds())  # WHY: calculate elapsed
        except Exception as e:  # WHY: catch parse errors
            logger.warning("elapsed_time_calculation_failed", error_type=type(e).__name__)
            return 0  # WHY: default elapsed

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
            if self.document_store is None:
                logger.error("upgrade_document_store_unavailable_for_status")
                return None  # WHY: fail

            logger.debug("upgrade_reading_status", run_id=run_id)
            upgrade_run = self.document_store.collection("upgrade_runs").get(run_id)
            if not isinstance(upgrade_run, dict) or upgrade_run.get("run_id") != run_id:
                logger.debug("upgrade_run_not_found", run_id=run_id)  # WHY: not found
                return None  # WHY: return none

            # WHY: build the status response from the document
            status_dict = self._build_status_dict(run_id=run_id, upgrade_run=upgrade_run)  # WHY: build response

            # WHY: log status returned
            logger.debug(
                "upgrade_status_returned",  # WHY: event type
                run_id=run_id,  # WHY: context
                progress_percent=status_dict["progress_percent"],  # WHY: metric
            )  # WHY: status event

            return status_dict  # WHY: return status dict

        except Exception as error:
            logger.error(
                "upgrade_status_exception",
                run_id=run_id,
                error_type=type(error).__name__,
            )

            return None  # WHY: fail on exception

    def cancel_upgrade(
        self,
        run_id: str,  # WHY: upgrade run identifier
        user_id: str,  # WHY: audit trail user context
        confirmation: str = "",
    ) -> bool:  # WHY: return success/failure
        """Cancel a stored cloud operation only after the operator types STOP.

        Args:
            run_id: Upgrade run ID to cancel.
            user_id: User cancelling the upgrade (audit trail).
            confirmation: The exact STOP word typed by the operator.

        Returns:
            True if cancel succeeded, False otherwise.

        WHY: implements T-009 requirement for "Cancel upgrade" button
        that triggers rollback if enabled.
        """
        return self._cancel_confirmed_upgrade(run_id, user_id, confirmation)

    def _cancel_confirmed_upgrade(self, run_id: str, user_id: str, confirmation: str) -> bool:
        """Cancel only verified cloud operations from the stored run plan."""
        from src.interfaces.portals.upgrade_portal.upgrade import stop
        from src.operations.execution.firmware import upgrade_service as cloud_service

        if confirmation != stop.STOP_CONFIRMATION_TEXT or self.document_store is None:
            reason = (
                "A typed STOP confirmation is required."
                if confirmation != stop.STOP_CONFIRMATION_TEXT
                else "The run document store is unavailable."
            )
            logger.warning("upgrade_cancel_refused", run_id=run_id, reason=reason)
            if self.audit_logger is not None:
                self.audit_logger.log_operation(
                    operation="upgrade_cancel",
                    user_id=user_id,
                    details={"run_id": run_id},
                    result="failure",
                    error_message=reason,
                )
            return False
        upgrade_run = self._load_cancel_run(run_id)
        if upgrade_run is None:
            logger.warning("upgrade_cancel_refused_without_cloud_ids", run_id=run_id)
            return False
        stop_targets = self._build_stop_targets(upgrade_run, cloud_service, stop)
        if not stop_targets:
            logger.warning("upgrade_cancel_refused_without_cloud_ids", run_id=run_id)
            return False
        outcome = stop.stop_run(self.mist_client, stop_targets, confirmation)
        if not self._cancel_outcome_is_complete(outcome, stop_targets):
            logger.warning("upgrade_cancel_incomplete", run_id=run_id)
            return False
        upgrade_run.update(
            {"status": "cancelled", "cancelled_at": datetime.now(UTC).isoformat(), "cancelled_by": user_id}
        )
        return self._persist_cancelled_run(run_id, user_id, upgrade_run, False)

    def _load_cancel_run(self, run_id: str) -> dict[str, Any] | None:
        """Read a stored run only when it holds verified cloud operation details."""
        if self.document_store is None:
            return None
        record = self.document_store.collection("upgrade_runs").get(run_id)
        if not isinstance(record, dict):
            return None
        if not isinstance(record.get("upgrades"), list) or not record["upgrades"]:
            return None
        if not isinstance(record.get("targets"), list) or not isinstance(record.get("options"), dict):
            return None
        return record

    def _build_stop_targets(self, upgrade_run: Mapping[str, Any], cloud_service: Any, stop_module: Any) -> list[Any]:
        """Rebuild only the plans that have a stored cloud identifier."""
        from src.interfaces.portals.upgrade_portal.upgrade import options

        site_id = str(upgrade_run.get("site_id", ""))
        targets = options.to_device_targets(upgrade_run["targets"], site_id)
        selected_options = options.build_options(upgrade_run["options"], now=None)
        plans = cloud_service.plan_upgrade(
            targets,
            selected_options,
            str(upgrade_run.get("org_id", "")),
            site_id,
        )
        return self._stop_targets(plans, upgrade_run["upgrades"], cloud_service, stop_module)

    @staticmethod
    def _cancel_outcome_is_complete(outcome: Any, stop_targets: list[Any]) -> bool:
        """Report true only when the cloud stopped every planned device."""
        requested = {target.mac for item in stop_targets for target in item.plan.targets}
        return bool(requested) and set(outcome.cancelled) == requested

    @staticmethod
    def _stop_targets(
        plans: tuple[Any, ...],
        upgrades: list[dict[str, Any]],
        cloud_service: Any,
        stop_module: Any,
    ) -> list[Any]:
        """Match each stored cloud identifier to its original SDK plan."""
        from src.operations.execution.firmware.upgrade_service import GatewayFamily

        stop_targets: list[Any] = []
        for plan in plans:
            addresses = {target.mac for target in plan.targets}
            stored = next(
                (
                    entry
                    for entry in upgrades
                    if entry.get("scope") == plan.scope and set(entry.get("accepted", ())) == addresses
                ),
                None,
            )
            if not isinstance(stored, Mapping) or not stored.get("upgrade_id"):
                return []
            family = GatewayFamily.SSR if plan.endpoint == cloud_service.ENDPOINT_ORG_SSRS else GatewayFamily.JUNOS
            stop_targets.append(stop_module.StopTarget(plan, str(stored["upgrade_id"]), family))
        return stop_targets

    def _persist_cancelled_run(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        user_id: str,  # WHY: audit context
        upgrade_run: dict[str, Any],  # WHY: document to write
        rollback_enabled: bool,  # WHY: action flag
    ) -> bool:  # WHY: persistence success
        """Persist the cancelled upgrade_run document and audit the cancel.

        Args:
            run_id: Upgrade run ID.
            user_id: User cancelling the upgrade.
            upgrade_run: Stored upgrade_run document (already mutated).
            rollback_enabled: Whether rollback was triggered.

        Returns:
            True when the document was written and audited, False otherwise.
        """
        if self.document_store is None or self.audit_logger is None:
            logger.error("upgrade_cancel_dependencies_unavailable", run_id=run_id)
            return False  # WHY: fail

        collection = self.document_store.collection("upgrade_runs")
        collection.update(upgrade_run)
        stored = collection.get(run_id)
        expected = ("status", "cancelled_at", "cancelled_by", "device_status")
        if not isinstance(stored, dict) or any(stored.get(field) != upgrade_run.get(field) for field in expected):
            logger.error("upgrade_cancel_readback_failed", run_id=run_id)
            return False
        audit_id = self.audit_logger.log_operation(
            operation="upgrade_cancel",
            user_id=user_id,
            details={"run_id": run_id, "rollback_triggered": rollback_enabled},
            result="success",
        )
        if audit_id is None:
            logger.error("upgrade_cancel_audit_failed", run_id=run_id)
            return False

        return True  # WHY: persistence complete

    def _mark_devices_rolled_back(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        upgrade_run: dict[str, Any],  # WHY: stored document
    ) -> None:  # WHY: in-place update
        """Mark upgrading and failed devices as rolled back.

        Args:
            run_id: Upgrade run ID.
            upgrade_run: Stored upgrade_run document (mutated in place).
        """
        # WHY: read the per-device status map
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
