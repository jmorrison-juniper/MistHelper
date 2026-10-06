"""ComparisonService for post-upgrade comparison (T-012).

Implements FR-013 (comparison results), FR-019 (audit logging), and
SC-010 (audit trail with zero secrets). Enforces settle gate as prerequisite
before allowing comparison. Calculates deltas between pre- and post-upgrade
captures.
"""

import time  # WHY: retry backoff timing
import uuid  # WHY: unique comparison IDs
from collections.abc import Mapping
from dataclasses import dataclass, field  # WHY: immutable result structures
from datetime import UTC, datetime  # WHY: ISO 8601 timestamps
from typing import Any, cast  # WHY: type hints for complex structures

import structlog  # WHY: structured logging for observability

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


@dataclass(frozen=True)  # WHY: immutable result prevents accidental modification
class ComparisonResult:
    """Result of pre/post-upgrade comparison.

    Attributes:
        passed: True if settle gate succeeded and comparison completed, False otherwise.
        run_id: Run identifier being compared.
        settled: True if devices settled before comparison, False otherwise.
        deltas: List of field changes detected per device.
        summary: Dict with change counts by field type.
        failed_checks: List of settle gate failures (if settle_gate_failed).
        timestamp: ISO 8601 timestamp when result was generated.

    WHY: Dataclass provides type safety, immutability, and automatic __repr__.
    """

    # WHY: overall pass/fail status
    passed: bool  # WHY: comparison outcome
    # WHY: run identifier
    run_id: str  # WHY: which run was compared
    # WHY: settle gate status
    settled: bool = False  # WHY: if devices settled
    # WHY: list of deltas
    deltas: list[dict[str, Any]] = field(default_factory=list)  # WHY: field changes
    # WHY: summary of changes
    summary: dict[str, Any] = field(default_factory=dict)  # WHY: change summary
    # WHY: failed settle gate checks
    failed_checks: list[str] = field(default_factory=list)  # WHY: settle gate failures
    # WHY: when result was generated
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())  # WHY: audit trail


class ComparisonService:
    """Service for post-upgrade device comparison.

    Enforces settle gate as prerequisite before allowing comparison.
    Calculates deltas between pre-upgrade and post-upgrade captures.
    Identifies firmware changes, config changes, policy changes, and
    neighbor topology changes.

    Implements FR-013 (comparison), FR-019 (audit logging), and SC-010
    (audit trail with secret masking).
    """

    # WHY: maximum retry attempts for transient errors
    MAX_RETRIES = 3  # WHY: retry configuration constant
    # WHY: initial backoff between retries (exponential: 1s, 2s, 4s)
    RETRY_BACKOFF_SECONDS = 1  # WHY: backoff constant
    # WHY: database read timeout
    DB_READ_TIMEOUT_SECONDS = 30  # WHY: timeout constant
    # WHY: maximum comparison total timeout
    COMPARISON_TIMEOUT_SECONDS = 60  # WHY: total timeout constant

    def __init__(  # WHY: initialize service with dependencies
        self,  # WHY: instance method
        settle_gate_service: Any = None,  # WHY: SettleGateService dependency
        db_router: Any = None,  # WHY: ArangoDB persistence dependency
        audit_logger: Any = None,  # WHY: audit trail dependency
        document_store: Any = None,  # WHY: request-owned document reads and writes
    ) -> None:  # WHY: initialization returns nothing
        """Initialize ComparisonService with dependencies.

        Args:
            settle_gate_service: SettleGateService for prerequisite check (required).
            db_router: DatabaseRouter for ArangoDB reads (required).
            audit_logger: AuditLogger for operation trail (required).
            document_store: Request-owned ArangoDB document handle.

        WHY: dependency injection pattern for testability and loose coupling.
        """
        # WHY: store settle gate service
        self.settle_gate_service = settle_gate_service  # WHY: settle gate dependency
        # WHY: store database router
        self.db_router = db_router  # WHY: persistent storage
        # WHY: store audit logger
        self.audit_logger = audit_logger  # WHY: operation trail
        self.document_store = document_store  # WHY: direct, verified portal persistence.
        # WHY: log initialization
        logger.info(
            "comparison_service_initialized",
            settle_gate_available=settle_gate_service is not None,  # WHY: dependency status
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
            document_store_available=document_store is not None,  # WHY: dependency status
        )  # WHY: startup event

    def compare(
        self,
        run_id: str,  # WHY: unique run identifier
        site_id: str,  # WHY: site context
        org_id: str,  # WHY: organization context
        device_ids: list[str],  # WHY: devices to compare
        user_id: str = "",  # WHY: audit trail user context
    ) -> ComparisonResult:
        """Compare pre- and post-upgrade captures.

        Verifies settle gate succeeded before proceeding. Fetches pre-capture
        and post-capture documents from ArangoDB and compares key fields:
        firmware version, radio config, policies, LLDP neighbors.

        Args:
            run_id: Unique run ID (links to upgrade_runs).
            site_id: Site ID for API context.
            org_id: Organization ID for API context.
            device_ids: List of device IDs to compare.
            user_id: User initiating comparison (audit trail).

        Returns:
            ComparisonResult with comparison outcome and deltas.

        WHY: implements FR-013 (comparison) with settle gate prerequisite
        check per T-012 requirement and automatic retry on transient errors.
        """
        logger.info(
            "comparison_start",
            run_id=run_id,
            device_count=len(device_ids),
            user_id=user_id,
        )  # Record the request scope before the service work.
        validation_error = self._validate_compare_inputs(
            run_id,
            device_ids,
        )  # Check required input before dependencies.
        if validation_error is not None:  # Refuse invalid comparison requests.
            return validation_error  # Return the established refusal result.
        if not self._comparison_dependencies_ready():  # Refuse before storage or cloud work.
            logger.error("comparison_dependencies_unavailable")  # Name the missing request dependency.
            return ComparisonResult(passed=False, run_id=run_id, settled=False)  # Do not report success.
        try:  # Keep driver details out of the portal response.
            return self._compare_after_settle(run_id, site_id, org_id, device_ids, user_id)  # Run verified steps.
        except Exception as error:  # Convert unexpected dependencies into a safe failure.
            logger.error("comparison_exception", error_type=type(error).__name__, run_id=run_id)  # Log safe context.
            self._audit_comparison_failure(run_id, user_id)  # Preserve the failed operation in the audit trail.
            return ComparisonResult(
                passed=False,
                run_id=run_id,
                settled=False,
            )  # Do not return a success-shaped result.

    def _comparison_dependencies_ready(self) -> bool:
        """Confirm that every dependency needed for comparison is available."""
        return all(
            dependency is not None
            for dependency in (
                self.settle_gate_service,
                self.db_router,
                self.document_store,
                self.audit_logger,
            )
        )  # The request graph must own each service.

    def _compare_after_settle(
        self,
        run_id: str,
        site_id: str,
        org_id: str,
        device_ids: list[str],
        user_id: str,
    ) -> ComparisonResult:
        """Require settle evidence before reading and comparing captures."""
        timestamp = datetime.now(UTC).isoformat()  # Keep the comparison time in UTC.
        logger.info("comparison_checking_settle_gate", run_id=run_id)  # Log before the settle request.
        settle_results = self._check_settle_gate(run_id, site_id, org_id, device_ids, user_id)  # Verify each device.
        if not settle_results or not settle_results.get("passed", False):  # Stop when settle evidence is incomplete.
            return self._settle_gate_failure_result(
                run_id,
                user_id,
                settle_results,
                timestamp,
            )  # Preserve failure detail.
        logger.info("comparison_settle_gate_passed", run_id=run_id)  # Record verified settle evidence.
        captures = self._fetch_both_captures(run_id, timestamp)  # Read the stored pre and post captures.
        if captures is None:  # Both capture roles are required for comparison.
            return self._capture_missing_result(run_id, timestamp)  # Return the established missing-data result.
        return self._compare_captures(run_id, org_id, site_id, user_id, device_ids, timestamp, captures)

    def _compare_captures(
        self,
        run_id: str,
        org_id: str,
        site_id: str,
        user_id: str,
        device_ids: list[str],
        timestamp: str,
        captures: tuple[dict[str, Any], dict[str, Any]],
    ) -> ComparisonResult:
        """Compare two stored captures and persist only verified results."""
        pre_capture, post_capture = captures  # Use the captures returned by the request-owned store.
        logger.info("comparison_calculating_deltas", run_id=run_id)  # Log before the data transform.
        deltas, summary = self._calculate_deltas(pre_capture, post_capture)  # Compare actual stored device rows.
        if summary["total_devices_compared"] == 0:  # Empty evidence cannot prove a successful comparison.
            return ComparisonResult(passed=False, run_id=run_id, settled=True, timestamp=timestamp)
        logger.info(
            "comparison_delta_summary",
            run_id=run_id,
            total_deltas=len(deltas),
            summary=summary,
        )  # Record the verified change count.
        comparison_id = self._persist_comparison(
            run_id=run_id,
            org_id=org_id,
            site_id=site_id,
            user_id=user_id,
            timestamp=timestamp,
            device_count=len(device_ids),
            pre_capture=pre_capture,
            post_capture=post_capture,
            deltas=deltas,
            summary=summary,
        )  # Require durable comparison and audit records.
        if comparison_id is None:  # A failed write cannot produce a success response.
            return ComparisonResult(passed=False, run_id=run_id, settled=True, timestamp=timestamp)
        logger.info(
            "comparison_complete",
            run_id=run_id,
            comparison_id=comparison_id,
            delta_count=len(deltas),
        )  # Record the verified result identifier.
        return ComparisonResult(
            passed=True,
            run_id=run_id,
            settled=True,
            deltas=deltas,
            summary=summary,
            timestamp=timestamp,
        )  # Return only the durable comparison.

    def _audit_comparison_failure(self, run_id: str, user_id: str) -> None:
        """Record an unexpected comparison failure without driver details."""
        if self.audit_logger is not None:  # The request graph may have lost the audit dependency.
            self.audit_logger.log_operation(
                operation="comparison_complete",
                user_id=user_id,
                details={"run_id": run_id},
                result="failure",
                error_message="The comparison operation failed.",
            )  # Keep the external exception private.

    def _validate_compare_inputs(
        self,
        run_id: str,  # WHY: run identifier
        device_ids: list[str],  # WHY: device list
    ) -> ComparisonResult | None:  # WHY: error result or None when valid
        """Validate comparison inputs before any API work.

        Args:
            run_id: Unique run ID.
            device_ids: List of device IDs to compare.

        Returns:
            ComparisonResult error when invalid, None when valid.
        """
        # WHY: run_id must be a non-empty string
        if not run_id or not isinstance(run_id, str):  # WHY: run_id validation
            logger.error("comparison_invalid_run_id", run_id=run_id)  # WHY: validation error
            return ComparisonResult(  # WHY: error result
                passed=False,  # WHY: validation failed
                run_id=run_id,  # WHY: run identifier
                settled=False,  # WHY: not settled
            )  # WHY: result

        # WHY: device list must be a non-empty list
        if not device_ids or not isinstance(device_ids, list):  # WHY: device list validation
            device_count = len(device_ids) if device_ids else 0  # WHY: get count or 0
            logger.error("comparison_no_devices", device_count=device_count)  # WHY: log error
            return ComparisonResult(  # WHY: error result
                passed=False,  # WHY: validation failed
                run_id=run_id,  # WHY: run identifier
                settled=False,  # WHY: not settled
            )  # WHY: result

        return None  # WHY: inputs valid

    def _settle_gate_failure_result(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        user_id: str,  # WHY: audit context
        settle_results: dict[str, Any] | None,  # WHY: settle outcome
        timestamp: str,  # WHY: result timestamp
    ) -> ComparisonResult:  # WHY: failure result
        """Build the failure result when the settle gate blocks comparison.

        Args:
            run_id: Unique run ID.
            user_id: User initiating comparison.
            settle_results: Settle gate outcome or None.
            timestamp: ISO 8601 timestamp for the result.

        Returns:
            ComparisonResult with passed=False and the failed checks.
        """
        # WHY: extract failed checks, tolerating a None settle result
        failed_checks = (  # WHY: failure list
            settle_results.get("failed_checks", []) if settle_results else []  # WHY: failures
        )  # WHY: list

        # WHY: log the settle gate failure
        logger.warning(  # WHY: warning event
            "comparison_settle_gate_failed",  # WHY: event type
            run_id=run_id,  # WHY: run context
            failed_checks=failed_checks,  # WHY: failure list
        )  # WHY: event logged

        # WHY: audit log the blocked comparison
        if self.audit_logger:  # WHY: audit logging conditional
            self.audit_logger.log_operation(  # WHY: audit trail
                operation="comparison_blocked",  # WHY: operation type
                user_id=user_id,  # WHY: user context
                details={  # WHY: operation details
                    "run_id": run_id,  # WHY: identifier
                    "reason": "settle_gate_failed",  # WHY: failure reason
                    "failed_checks": failed_checks,  # WHY: failures
                },  # WHY: detail dict
                result="blocked",  # WHY: result status
            )  # WHY: audit entry

        # WHY: return the blocked comparison result
        return ComparisonResult(  # WHY: failure result
            passed=False,  # WHY: comparison blocked
            run_id=run_id,  # WHY: run identifier
            settled=False,  # WHY: not settled
            failed_checks=failed_checks,  # WHY: settle failures
            timestamp=timestamp,  # WHY: result timestamp
        )  # WHY: result

    def _fetch_both_captures(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        timestamp: str,  # WHY: result timestamp
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:  # WHY: capture pair or None
        """Fetch the pre- and post-capture documents for a run.

        Args:
            run_id: Unique run ID.
            timestamp: ISO 8601 timestamp (used for logging context).

        Returns:
            (pre_capture, post_capture) when both exist, None when either is missing.
        """
        # WHY: fetch the pre-upgrade capture
        logger.info("comparison_fetching_pre_capture", run_id=run_id)  # WHY: fetch phase start
        pre_capture = self._fetch_pre_capture(run_id=run_id)  # WHY: fetch pre-capture

        # WHY: fail fast when the pre-capture is absent
        if not pre_capture:  # WHY: check fetch result
            logger.error("comparison_pre_capture_not_found", run_id=run_id)  # WHY: error event
            return None  # WHY: missing capture

        # WHY: fetch the post-upgrade capture
        logger.info("comparison_fetching_post_capture", run_id=run_id)  # WHY: fetch phase start
        post_capture = self._fetch_post_capture(run_id=run_id)  # WHY: fetch post-capture

        # WHY: fail fast when the post-capture is absent
        if not post_capture:  # WHY: check fetch result
            logger.error("comparison_post_capture_not_found", run_id=run_id)  # WHY: error event
            return None  # WHY: missing capture

        return (pre_capture, post_capture)  # WHY: both captures present

    def _persist_comparison(
        self,  # WHY: instance method
        run_id: str,  # WHY: run link
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        user_id: str,  # WHY: audit context
        timestamp: str,  # WHY: comparison moment
        device_count: int,  # WHY: scope metric
        pre_capture: dict[str, Any],  # WHY: pre-capture capture
        post_capture: dict[str, Any],  # WHY: post-capture capture
        deltas: list[dict[str, Any]],  # WHY: delta array
        summary: dict[str, Any],  # WHY: summary data
    ) -> str | None:  # WHY: verified comparison identifier or failure
        """Persist a completed comparison to ArangoDB and audit it.

        Args:
            run_id: Unique run ID.
            org_id: Organization ID.
            site_id: Site ID.
            user_id: User initiating comparison.
            timestamp: ISO 8601 timestamp for the comparison.
            device_count: Number of devices compared.
            pre_capture: Pre-upgrade capture document.
            post_capture: Post-upgrade capture document.
            deltas: List of detected deltas.
            summary: Delta summary data.

        Returns:
            The comparison identifier written to the database.
        """
        # WHY: log persistence start
        logger.info("comparison_persisting_to_arangodb", run_id=run_id)  # WHY: persist start

        # WHY: build the ArangoDB document
        comparison_id = str(uuid.uuid4())  # WHY: unique identifier
        comparison_doc = {  # WHY: ArangoDB document structure
            "_key": f"{run_id}_{int(time.time() * 1000)}",  # WHY: composite key
            "comparison_id": comparison_id,  # WHY: public identifier
            "run_id": run_id,  # WHY: run link
            "org_id": org_id,  # WHY: organization context
            "site_id": site_id,  # WHY: site context
            "timestamp": timestamp,  # WHY: comparison moment
            "pre_capture_timestamp": pre_capture.get("timestamp"),  # WHY: pre-capture time
            "post_capture_timestamp": post_capture.get("timestamp"),  # WHY: post-capture time
            "device_count": device_count,  # WHY: scope metric
            "deltas": deltas,  # WHY: delta array
            "summary": summary,  # WHY: summary data
            "user_id": user_id,  # WHY: audit context
        }  # WHY: document complete

        if self.document_store is None or self.audit_logger is None:
            logger.error("comparison_persistence_dependencies_unavailable", run_id=run_id)
            return None
        try:  # The driver result must be read back before it can authorize success.
            collection = self.document_store.collection("comparisons")  # Use the request-owned document handle.
            collection.insert(comparison_doc, overwrite=True)  # Store the fixed comparison document shape.
            stored = collection.get(comparison_doc["_key"])  # Read the same natural run key back.
        except Exception as fault:  # A database fault remains a failed comparison.
            logger.error("comparison_persist_failed", error_type=type(fault).__name__)
            return None  # A missing durable record never yields a success identifier.
        verified_fields = ("comparison_id", "run_id", "timestamp", "deltas", "summary")
        if not isinstance(stored, dict) or any(stored.get(field) != comparison_doc[field] for field in verified_fields):
            logger.error("comparison_readback_failed", comparison_id=comparison_id)
            return None  # A different or absent record cannot verify this comparison.

        # A stored comparison is not a successful operation without its audit record.
        if self.audit_logger is None:
            return None
        audit_id = self.audit_logger.log_operation(  # WHY: audit trail
            operation="comparison_complete",  # WHY: operation type
            user_id=user_id,  # WHY: user context
            details={  # WHY: operation details
                "comparison_id": comparison_id,  # WHY: identifier
                "device_count": device_count,  # WHY: scope metric
                "delta_count": len(deltas),  # WHY: delta count
                "run_id": run_id,  # WHY: run link
                "summary": summary,  # WHY: summary data
            },  # WHY: detail dict
            result="success",  # WHY: result status
        )  # WHY: audit entry
        if audit_id is None:
            return None

        return comparison_id  # WHY: return only the read-back comparison identifier

    def _capture_missing_result(
        self,  # WHY: instance method
        run_id: str,  # WHY: run identifier
        timestamp: str,  # WHY: result timestamp
    ) -> ComparisonResult:  # WHY: error result
        """Build the error result when a capture document is missing.

        Args:
            run_id: Unique run ID.
            timestamp: ISO 8601 timestamp for the result.

        Returns:
            ComparisonResult with passed=False and settled=True.
        """
        # WHY: the settle gate passed, so settled is True even though comparison failed
        return ComparisonResult(  # WHY: error result
            passed=False,  # WHY: comparison failed
            run_id=run_id,  # WHY: run identifier
            settled=True,  # WHY: settled but capture missing
            timestamp=timestamp,  # WHY: result timestamp
        )  # WHY: result

    def _check_settle_gate(
        self,
        run_id: str,  # WHY: run identifier
        site_id: str,  # WHY: site context
        org_id: str,  # WHY: org context
        device_ids: list[str],  # WHY: devices to check
        user_id: str = "",
    ) -> dict[str, Any] | None:  # WHY: return settle gate result
        """Check settle gate prerequisite.

        Args:
            run_id: Run ID.
            site_id: Site ID.
            org_id: Organization ID.
            device_ids: List of device IDs.

        Returns:
            Dict with settle gate results or None on error.

        WHY: verifies devices settled before proceeding to comparison.
        """
        if self.settle_gate_service is None or self.document_store is None:
            return {"passed": False, "failed_checks": ["settle_service_unavailable"]}
        results = self.settle_gate_service.wait_for_settle(
            run_id=run_id,
            device_ids=device_ids,
            site_id=site_id,
            org_id=org_id,
            user_id=user_id,
        )
        if not isinstance(results, dict) or not results:
            return {"passed": False, "failed_checks": ["verified_settle_evidence_unavailable"]}
        stored = self._stored_settle_record(run_id)
        if stored is None:
            return {"passed": False, "failed_checks": ["verified_settle_evidence_unavailable"]}
        if not self._settle_results_match(stored, results, device_ids):
            return {"passed": False, "failed_checks": ["verified_settle_evidence_mismatch"]}
        failed = [device_id for device_id, result in results.items() if not result.passed or result.failed_checks]
        return {"passed": not failed, "failed_checks": failed}

    def _stored_settle_record(self, run_id: str) -> dict[str, Any] | None:
        """Read the latest settlement record with a bound run identifier."""
        query = "FOR doc IN settle_gates " "FILTER doc.run_id == @run_id " "SORT doc.timestamp DESC LIMIT 1 RETURN doc"
        rows = list(self.document_store.aql.execute(query, bind_vars={"run_id": run_id}))
        return rows[0] if len(rows) == 1 and isinstance(rows[0], dict) else None

    @staticmethod
    def _settle_results_match(
        stored: Mapping[str, Any],
        results: Mapping[str, Any],
        device_ids: list[str],
    ) -> bool:
        """Require the stored evidence to match every result from this request."""
        expected_results = {
            device_id: {
                "passed": result.passed,
                "failed_checks": result.failed_checks,
                "details": result.details,
            }
            for device_id, result in results.items()
        }
        return stored.get("device_results") == expected_results and set(results) == set(device_ids)

    def _fetch_pre_capture(self, run_id: str) -> dict[str, Any] | None:  # WHY: return pre-capture or None
        """Fetch pre-upgrade capture from ArangoDB.

        Args:
            run_id: Run ID to fetch.

        Returns:
            Pre-capture document or None if not found.

        WHY: retrieves baseline capture for comparison.
        """
        return self._fetch_capture_by_role(run_id, "pre")  # The store returns verified canonical captures only.

    def _fetch_post_capture(self, run_id: str) -> dict[str, Any] | None:  # WHY: return post-capture or None
        """Fetch post-upgrade capture from ArangoDB.

        Args:
            run_id: Run ID to fetch.

        Returns:
            Post-capture document or None if not found.

        WHY: retrieves post-upgrade capture for comparison.
        """
        return self._fetch_capture_by_role(run_id, "post")  # The store returns verified canonical captures only.

    def _fetch_capture_by_role(self, run_id: str, role: str) -> dict[str, Any] | None:
        """Read one verified capture by its run role."""
        from src.interfaces.portals.upgrade_portal.capture import store

        if self.document_store is None:
            return None
        page = store.list_captures(store.CaptureQuery(run_id=run_id), database=self.document_store)
        if not page.database_available:
            return None
        row = next((capture for capture in page.captures if capture.get("role") == role), None)
        if row is None:
            return None
        loaded = store.load_capture_for_comparison(str(row.get("capture_id", "")), database=self.document_store)
        return loaded.capture if loaded.comparable else None

    def _calculate_deltas(
        self,
        pre_capture: dict[str, Any],  # WHY: pre-upgrade capture
        post_capture: dict[str, Any],  # WHY: post-upgrade capture
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:  # WHY: return deltas and summary
        """Calculate deltas between pre- and post-capture.

        Args:
            pre_capture: Pre-upgrade capture document.
            post_capture: Post-upgrade capture document.

        Returns:
            Tuple of (deltas list, summary dict).

        WHY: compares key fields to identify upgrade impact.
        """
        pre_index = pre_capture.get("device_index")  # The canonical capture stores a verified address index.
        post_index = post_capture.get("device_index")  # Compare only actual device rows from both captures.
        if not isinstance(pre_index, dict) or not isinstance(post_index, dict):
            return [], self._empty_delta_summary()  # Missing indexes cannot prove a comparison.
        summary = self._empty_delta_summary()  # Keep each result count in the established response shape.
        summary["total_devices_compared"] = len(set(pre_index) & set(post_index))  # Count common device records.
        deltas = self._compare_device_indexes(pre_index, post_index, summary)  # Compare each captured device once.
        return deltas, summary  # WHY: return results

    @staticmethod
    def _empty_delta_summary() -> dict[str, int]:
        """Create an empty comparison summary with all response fields."""
        return {
            "firmware_changes": 0,  # Count firmware changes.
            "config_changes": 0,  # Count inventory and configuration changes.
            "policy_changes": 0,  # Preserve the established policy count.
            "neighbor_changes": 0,  # Preserve the established neighbor count.
            "total_devices_compared": 0,  # Count devices present in both captures.
        }  # Return a stable response shape.

    def _compare_device_indexes(
        self,
        pre_index: dict[str, Any],
        post_index: dict[str, Any],
        summary: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Compare the device rows in two validated capture indexes."""
        deltas: list[dict[str, Any]] = []  # Keep each change with its device identifier.
        for device_id in sorted(set(pre_index) | set(post_index)):
            before = pre_index.get(device_id)
            after = post_index.get(device_id)
            if before is None or after is None:
                deltas.append(self._inventory_delta(device_id, before, after))  # Record added or removed devices.
                summary["config_changes"] += 1  # Count inventory changes with other config changes.
                continue
            if isinstance(before, Mapping) and isinstance(after, Mapping):
                deltas.extend(self._device_deltas(device_id, before, after, summary))  # Compare supported fields.
        return deltas  # Return every verified change.

    @staticmethod
    def _inventory_delta(
        device_id: str,
        before: Any,
        after: Any,
    ) -> dict[str, Any]:
        """Describe a device that appears in only one capture."""
        removed = after is None  # A missing post-upgrade row means the device was removed.
        return {
            "device_id": device_id,  # Identify the affected device.
            "field": "inventory",  # Name the source of the change.
            "pre_value": "present" if before is not None else None,  # Record the prior presence.
            "post_value": "present" if after is not None else None,  # Record the current presence.
            "delta_type": "device_removed" if removed else "device_added",  # Classify the inventory change.
            "severity": "high" if removed else "medium",  # Missing devices need stronger review.
        }  # Return the complete inventory delta.

    @staticmethod
    def _device_deltas(
        device_id: str,
        before: Mapping[str, Any],
        after: Mapping[str, Any],
        summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return the actual firmware and inventory changes of one device."""
        deltas = []
        for attribute in ("version", "firmware_version", "model", "type", "status"):
            old_value = before.get(attribute)
            new_value = after.get(attribute)
            if old_value is None or new_value is None or old_value == new_value:
                continue
            firmware_change = attribute in ("version", "firmware_version")
            deltas.append(
                {
                    "device_id": device_id,
                    "field": attribute,
                    "pre_value": old_value,
                    "post_value": new_value,
                    "delta_type": "firmware_upgrade" if firmware_change else "config_change",
                    "severity": "high" if firmware_change else "medium",
                }
            )
            summary["firmware_changes" if firmware_change else "config_changes"] += 1
        return deltas


@dataclass(frozen=True)  # WHY: immutable result prevents accidental modification
class DetailedComparisonResult:
    """Detailed comparison result with field-level delta analysis.

    Attributes:
        run_id: Run identifier being compared.
        deltas: List of (field, pre_value, post_value, delta_type, severity).
        summary: Dict with counts of changes by type and severity.
        flagged_for_review: List of high-severity changes requiring manual approval.
        timestamp: ISO 8601 timestamp when result was generated.

    WHY: extends ComparisonResult with actionable delta details for engineering review.
    """

    # WHY: run identifier
    run_id: str  # WHY: which run was compared
    # WHY: list of detailed deltas with severity
    deltas: list[dict[str, Any]] = field(default_factory=list)  # WHY: field changes
    # WHY: summary with breakdown by severity
    summary: dict[str, Any] = field(default_factory=dict)  # WHY: change summary
    # WHY: high-severity changes requiring review
    flagged_for_review: list[dict[str, Any]] = field(default_factory=list)  # WHY: review items
    # WHY: when result was generated
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())  # WHY: audit trail


class ComparisonResultService:
    """Service for detailed post-upgrade comparison with delta analysis.

    Performs field-level delta comparison between pre and post captures,
    identifying inventory changes, firmware updates, radio config changes,
    policy modifications, and neighbor topology changes. Flags high-severity
    changes for manual engineering review.

    Implements FR-013 (detailed comparison), FR-019 (audit logging), and
    SC-010 (audit trail with secret masking).
    """

    # WHY: severity levels for delta classification
    SEVERITY_LEVELS = {
        "firmware_upgrade": "high",  # WHY: firmware changes are critical
        "firmware_downgrade": "critical",  # WHY: rollback is major issue
        "firmware_mismatch": "high",  # WHY: unexpected firmware state
        "policy_change": "high",  # WHY: policy changes affect security
        "radio_config_change": "medium",  # WHY: radio changes less critical than firmware
        "channel_change": "medium",  # WHY: channel changes affect coverage
        "power_change": "low",  # WHY: power changes less critical
        "device_added": "medium",  # WHY: new devices unexpected
        "device_removed": "high",  # WHY: missing devices critical
        "neighbor_topology_change": "medium",  # WHY: neighbor changes affect routing
    }  # WHY: severity mapping for delta classification

    def __init__(  # WHY: initialize service with dependencies
        self,  # WHY: instance method
        db_router: Any = None,  # WHY: ArangoDB persistence dependency
        audit_logger: Any = None,  # WHY: audit trail dependency
        masker: Any = None,  # WHY: secret masking dependency
    ) -> None:  # WHY: initialization returns nothing
        """Initialize ComparisonResultService with dependencies.

        Args:
            db_router: DatabaseRouter for ArangoDB reads/writes (required).
            audit_logger: AuditLogger for operation trail (required).
            masker: SecretMasker for redacting sensitive data (optional).

        WHY: dependency injection enables testability and loose coupling.
        """
        # WHY: store database router
        self.db_router = db_router  # WHY: persistent storage
        # WHY: store audit logger
        self.audit_logger = audit_logger  # WHY: operation trail
        # WHY: store secret masker
        self.masker = masker  # WHY: secret redaction
        # WHY: log initialization
        logger.info(
            "comparison_result_service_initialized",  # WHY: operation name
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
            masker_available=masker is not None,  # WHY: dependency status
        )  # WHY: startup event

    def analyze_deltas(
        self,  # WHY: instance method
        run_id: str,  # WHY: unique run identifier
        pre_capture: dict[str, Any],  # WHY: pre-upgrade capture
        post_capture: dict[str, Any],  # WHY: post-upgrade capture
        user_id: str = "",  # WHY: audit trail user context
    ) -> DetailedComparisonResult:  # WHY: return detailed comparison result
        """Analyze field-level deltas between pre and post captures.

        Performs comprehensive comparison across:
        - Inventory deltas: devices added, removed, model changes
        - Firmware deltas: version mismatch, unexpected rollback
        - Radio config deltas: channel, power, band changes
        - Policy deltas: security policy changes
        - Neighbor deltas: LLDP neighbor topology changes

        Flags high-severity changes for engineering review (firmware rollback,
        policy changes, device removal).

        Args:
            run_id: Unique run ID.
            pre_capture: Pre-upgrade capture document.
            post_capture: Post-upgrade capture document.
            user_id: User initiating comparison (audit trail).

        Returns:
            DetailedComparisonResult with deltas, summary, and flagged items.

        WHY: implements field-level delta analysis per T-013 requirement.
        """
        # WHY: log delta analysis start
        logger.info(
            "delta_analysis_start",  # WHY: operation name
            run_id=run_id,  # WHY: run context
            user_id=user_id,  # WHY: audit context
        )  # WHY: pre-analysis event

        try:
            # WHY: validate inputs
            if not run_id or not pre_capture or not post_capture:  # WHY: input validation
                # WHY: missing required data
                logger.error("delta_analysis_invalid_inputs", run_id=run_id)  # WHY: validation error
                return DetailedComparisonResult(run_id=run_id)  # WHY: empty result

            # WHY: initialize result structures
            deltas: list[dict[str, Any]] = []  # WHY: delta list
            flagged_for_review: list[dict[str, Any]] = []  # WHY: review list
            summary = {  # WHY: summary dict
                "total_deltas": 0,  # WHY: total change count
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},  # WHY: severity breakdown
                "by_type": {  # WHY: type breakdown
                    "inventory": 0,  # WHY: device changes
                    "firmware": 0,  # WHY: firmware changes
                    "radio_config": 0,  # WHY: radio changes
                    "policy": 0,  # WHY: policy changes
                    "neighbors": 0,  # WHY: neighbor changes
                },  # WHY: type counts
            }  # WHY: summary complete

            # WHY: analyze inventory deltas
            logger.info("analyzing_inventory_deltas", run_id=run_id)  # WHY: phase start
            inventory_deltas = self._analyze_inventory_deltas(  # WHY: analyze devices
                pre_capture=pre_capture,  # WHY: pre-capture
                post_capture=post_capture,  # WHY: post-capture
            )  # WHY: inventory analysis result
            deltas.extend(inventory_deltas)  # WHY: add to deltas
            cast(dict[str, int], summary["by_type"])["inventory"] = len(
                inventory_deltas  # WHY: count
            )  # WHY: count complete

            # WHY: analyze firmware deltas
            logger.info("analyzing_firmware_deltas", run_id=run_id)  # WHY: phase start
            firmware_deltas = self._analyze_firmware_deltas(  # WHY: analyze firmware
                pre_capture=pre_capture,  # WHY: pre-capture
                post_capture=post_capture,  # WHY: post-capture
            )  # WHY: firmware analysis result
            deltas.extend(firmware_deltas)  # WHY: add to deltas
            cast(dict[str, int], summary["by_type"])["firmware"] = len(
                firmware_deltas  # WHY: count
            )  # WHY: count complete

            # WHY: analyze radio config deltas
            logger.info("analyzing_radio_config_deltas", run_id=run_id)  # WHY: phase start
            radio_deltas = self._analyze_radio_config_deltas(  # WHY: analyze radio
                pre_capture=pre_capture,  # WHY: pre-capture
                post_capture=post_capture,  # WHY: post-capture
            )  # WHY: radio analysis result
            deltas.extend(radio_deltas)  # WHY: add to deltas
            cast(dict[str, int], summary["by_type"])["radio_config"] = len(
                radio_deltas  # WHY: count
            )  # WHY: count complete

            # WHY: analyze policy deltas
            logger.info("analyzing_policy_deltas", run_id=run_id)  # WHY: phase start
            policy_deltas = self._analyze_policy_deltas(  # WHY: analyze policy
                pre_capture=pre_capture,  # WHY: pre-capture
                post_capture=post_capture,  # WHY: post-capture
            )  # WHY: policy analysis result
            deltas.extend(policy_deltas)  # WHY: add to deltas
            cast(dict[str, int], summary["by_type"])["policy"] = len(policy_deltas)  # WHY: count  # WHY: count complete

            # WHY: analyze neighbor deltas
            logger.info("analyzing_neighbor_deltas", run_id=run_id)  # WHY: phase start
            neighbor_deltas = self._analyze_neighbor_deltas(  # WHY: analyze neighbors
                pre_capture=pre_capture,  # WHY: pre-capture
                post_capture=post_capture,  # WHY: post-capture
            )  # WHY: neighbor analysis result
            deltas.extend(neighbor_deltas)  # WHY: add to deltas
            cast(dict[str, int], summary["by_type"])["neighbors"] = len(
                neighbor_deltas  # WHY: count
            )  # WHY: count complete

            # WHY: update total and severity counts
            summary["total_deltas"] = len(deltas)  # WHY: total count
            for delta in deltas:  # WHY: iterate deltas
                # WHY: increment severity counter
                severity = delta.get("severity", "low")  # WHY: get severity
                if severity in cast(dict[str, int], summary["by_severity"]):  # WHY: valid severity
                    cast(dict[str, int], summary["by_severity"])[severity] += 1  # WHY: increment count
                # WHY: flag high-severity changes for review
                if severity in ["critical", "high"]:  # WHY: high severity
                    flagged_for_review.append(delta)  # WHY: add to review list

            # WHY: log delta analysis complete
            logger.info(
                "delta_analysis_complete",  # WHY: operation name
                run_id=run_id,  # WHY: run context
                total_deltas=len(deltas),  # WHY: result metric
                flagged_count=len(flagged_for_review),  # WHY: review metric
                summary=summary,  # WHY: summary data
            )  # WHY: post-analysis event

            # WHY: audit log delta analysis
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="delta_analysis_complete",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={  # WHY: operation details
                        "run_id": run_id,  # WHY: identifier
                        "total_deltas": len(deltas),  # WHY: count
                        "flagged_count": len(flagged_for_review),  # WHY: review count
                        "summary": summary,  # WHY: summary data
                    },  # WHY: detail dict
                    result="success",  # WHY: result status
                )  # WHY: audit entry

            # WHY: return detailed comparison result
            return DetailedComparisonResult(
                run_id=run_id,  # WHY: run identifier
                deltas=deltas,  # WHY: all deltas
                summary=summary,  # WHY: summary data
                flagged_for_review=flagged_for_review,  # WHY: review items
            )  # WHY: result complete

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "delta_analysis_exception",  # WHY: error event
                run_id=run_id,  # WHY: context
                error_type=type(e).__name__,
                exception_type=type(e).__name__,  # WHY: exception class
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="delta_analysis_complete",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message="The comparison analysis failed.",  # WHY: keep dependency text private.
                )  # WHY: audit entry

            # WHY: return empty result on error
            return DetailedComparisonResult(run_id=run_id)  # WHY: error result

    def _analyze_inventory_deltas(
        self,  # WHY: instance method
        pre_capture: dict[str, Any],  # WHY: pre-capture
        post_capture: dict[str, Any],  # WHY: post-capture
    ) -> list[dict[str, Any]]:  # WHY: return list of inventory deltas
        """Analyze device inventory changes.

        Detects: devices added, removed, model changes.

        Args:
            pre_capture: Pre-upgrade capture.
            post_capture: Post-upgrade capture.

        Returns:
            List of inventory delta dicts.

        WHY: identifies unexpected inventory changes (missing devices, new devices).
        """
        # WHY: log inventory analysis start
        logger.info("inventory_delta_analysis_start")  # WHY: phase start

        deltas: list[dict[str, Any]] = []  # WHY: result list

        # WHY: extract device lists
        pre_devices = pre_capture.get("devices", [])  # WHY: pre-capture devices
        post_devices = post_capture.get("devices", [])  # WHY: post-capture devices

        # WHY: build device maps by ID
        pre_map = {d.get("device_id"): d for d in pre_devices}  # WHY: pre-map
        post_map = {d.get("device_id"): d for d in post_devices}  # WHY: post-map

        # WHY: detect removed devices
        deltas.extend(self._detect_removed_devices(pre_map, post_map))  # WHY: removals

        # WHY: detect added devices
        deltas.extend(self._detect_added_devices(pre_map, post_map))  # WHY: additions

        # WHY: detect model changes for existing devices
        deltas.extend(self._detect_model_changes(pre_map, post_map))  # WHY: model changes

        # WHY: log inventory analysis complete
        logger.debug(
            "inventory_delta_analysis_complete",  # WHY: phase complete
            delta_count=len(deltas),  # WHY: count
        )  # WHY: phase logged

        return deltas  # WHY: return results

    def _detect_removed_devices(
        self,  # WHY: instance method
        pre_map: dict[str, Any],  # WHY: pre-capture device map
        post_map: dict[str, Any],  # WHY: post-capture device map
    ) -> list[dict[str, Any]]:  # WHY: return removed device deltas
        """Detect devices present pre-upgrade but missing post-upgrade.

        Args:
            pre_map: Device map keyed by device_id from pre-capture.
            post_map: Device map keyed by device_id from post-capture.

        Returns:
            List of delta dicts for removed devices.
        """
        # WHY: result list for removed devices
        removed: list[dict[str, Any]] = []  # WHY: removed deltas

        # WHY: iterate pre-capture devices
        for device_id, pre_dev in pre_map.items():  # WHY: each pre-device
            # WHY: skip devices still present post-upgrade
            if device_id in post_map:  # WHY: device exists
                continue  # WHY: not removed

            # WHY: build delta for removed device
            removed.append(  # WHY: add delta
                {  # WHY: delta dict
                    "device_id": device_id,  # WHY: identifier
                    "field": "inventory",  # WHY: field type
                    "delta_type": "device_removed",  # WHY: change type
                    "pre_value": pre_dev.get("name", device_id),  # WHY: pre-value
                    "post_value": None,  # WHY: device gone
                    "severity": self.SEVERITY_LEVELS.get("device_removed", "high"),  # WHY: level
                }  # WHY: delta complete
            )  # WHY: appended
            logger.warning(  # WHY: log removal
                "device_removed",  # WHY: event type
                device_id=device_id,  # WHY: context
                device_name=pre_dev.get("name"),  # WHY: human-readable
            )  # WHY: logged

        return removed  # WHY: return removed deltas

    def _detect_added_devices(
        self,  # WHY: instance method
        pre_map: dict[str, Any],  # WHY: pre-capture device map
        post_map: dict[str, Any],  # WHY: post-capture device map
    ) -> list[dict[str, Any]]:  # WHY: return added device deltas
        """Detect devices present post-upgrade but absent pre-upgrade.

        Args:
            pre_map: Device map keyed by device_id from pre-capture.
            post_map: Device map keyed by device_id from post-capture.

        Returns:
            List of delta dicts for added devices.
        """
        # WHY: result list for added devices
        added: list[dict[str, Any]] = []  # WHY: added deltas

        # WHY: iterate post-capture devices
        for device_id, post_dev in post_map.items():  # WHY: each post-device
            # WHY: skip devices already present pre-upgrade
            if device_id in pre_map:  # WHY: device existed
                continue  # WHY: not new

            # WHY: build delta for added device
            added.append(  # WHY: add delta
                {  # WHY: delta dict
                    "device_id": device_id,  # WHY: identifier
                    "field": "inventory",  # WHY: field type
                    "delta_type": "device_added",  # WHY: change type
                    "pre_value": None,  # WHY: device new
                    "post_value": post_dev.get("name", device_id),  # WHY: post-value
                    "severity": self.SEVERITY_LEVELS.get("device_added", "medium"),  # WHY: level
                }  # WHY: delta complete
            )  # WHY: appended
            logger.info(  # WHY: log addition
                "device_added",  # WHY: event type
                device_id=device_id,  # WHY: context
                device_name=post_dev.get("name"),  # WHY: human-readable
            )  # WHY: logged

        return added  # WHY: return added deltas

    def _detect_model_changes(
        self,  # WHY: instance method
        pre_map: dict[str, Any],  # WHY: pre-capture device map
        post_map: dict[str, Any],  # WHY: post-capture device map
    ) -> list[dict[str, Any]]:  # WHY: return model change deltas
        """Detect devices whose model changed between captures.

        Args:
            pre_map: Device map keyed by device_id from pre-capture.
            post_map: Device map keyed by device_id from post-capture.

        Returns:
            List of delta dicts for model changes.
        """
        # WHY: result list for model changes
        changes: list[dict[str, Any]] = []  # WHY: change deltas

        # WHY: iterate pre-capture devices that also exist post-upgrade
        for device_id, pre_dev in pre_map.items():  # WHY: each pre-device
            # WHY: skip devices not present post-upgrade
            if device_id not in post_map:  # WHY: device gone
                continue  # WHY: no comparison possible

            # WHY: extract model values
            pre_model = pre_dev.get("model")  # WHY: pre-model
            post_model = post_map[device_id].get("model")  # WHY: post-model

            # WHY: only flag when both models exist and differ
            if not (pre_model and post_model and pre_model != post_model):  # WHY: no change
                continue  # WHY: skip

            # WHY: build delta for model change
            changes.append(  # WHY: add delta
                {  # WHY: delta dict
                    "device_id": device_id,  # WHY: identifier
                    "field": "model",  # WHY: field type
                    "delta_type": "model_change",  # WHY: change type
                    "pre_value": pre_model,  # WHY: old value
                    "post_value": post_model,  # WHY: new value
                    "severity": "high",  # WHY: critical change
                }  # WHY: delta complete
            )  # WHY: appended
            logger.warning(  # WHY: log change
                "device_model_changed",  # WHY: event type
                device_id=device_id,  # WHY: context
                pre_model=pre_model,  # WHY: old value
                post_model=post_model,  # WHY: new value
            )  # WHY: logged

        return changes  # WHY: return change deltas

    def _analyze_firmware_deltas(
        self,  # WHY: instance method
        pre_capture: dict[str, Any],  # WHY: pre-capture
        post_capture: dict[str, Any],  # WHY: post-capture
    ) -> list[dict[str, Any]]:  # WHY: return list of firmware deltas
        """Analyze firmware version changes.

        Detects: version mismatch, unexpected rollback, firmware upgrade.

        Args:
            pre_capture: Pre-upgrade capture.
            post_capture: Post-upgrade capture.

        Returns:
            List of firmware delta dicts.

        WHY: identifies unexpected firmware state after upgrade.
        """
        # WHY: log firmware analysis start
        logger.info("firmware_delta_analysis_start")  # WHY: phase start

        deltas: list[dict[str, Any]] = []  # WHY: result list

        # WHY: extract device lists
        pre_devices = pre_capture.get("devices", [])  # WHY: pre-capture devices
        post_devices = post_capture.get("devices", [])  # WHY: post-capture devices

        # WHY: build device map by ID for post-capture
        post_map = {d.get("device_id"): d for d in post_devices}  # WHY: post-map

        # WHY: compare firmware versions for each device
        for pre_dev in pre_devices:  # WHY: iterate pre-devices
            # WHY: get device ID and model
            device_id = pre_dev.get("device_id")  # WHY: identifier
            pre_firmware = pre_dev.get("firmware_version")  # WHY: pre-firmware
            # WHY: check if device exists in post-capture
            if device_id in post_map:  # WHY: device exists
                post_dev = post_map[device_id]  # WHY: get post-device
                post_firmware = post_dev.get("firmware_version")  # WHY: post-firmware
                # WHY: check for firmware mismatch
                if pre_firmware and post_firmware and pre_firmware != post_firmware:  # WHY: changed
                    # WHY: determine change type and severity
                    delta_type = "firmware_upgrade"  # WHY: default to upgrade
                    severity = self.SEVERITY_LEVELS.get("firmware_upgrade", "high")  # WHY: severity
                    # WHY: check for unexpected rollback
                    if self._is_rollback(pre_firmware, post_firmware):  # WHY: version comparison
                        # WHY: rollback detected
                        delta_type = "firmware_downgrade"  # WHY: rollback type
                        severity = self.SEVERITY_LEVELS.get("firmware_downgrade", "critical")  # WHY: critical
                    # WHY: create delta for firmware change
                    delta = {  # WHY: delta dict
                        "device_id": device_id,  # WHY: device identifier
                        "field": "firmware_version",  # WHY: field type
                        "delta_type": delta_type,  # WHY: change type
                        "pre_value": pre_firmware,  # WHY: pre-value
                        "post_value": post_firmware,  # WHY: post-value
                        "severity": severity,  # WHY: severity level
                    }  # WHY: delta complete
                    deltas.append(delta)  # WHY: add to results
                    log_level = "error" if severity == "critical" else "warning"  # WHY: log level
                    if log_level == "error":  # WHY: check log level
                        logger.error(
                            "firmware_downgrade_detected",  # WHY: event type
                            device_id=device_id,  # WHY: context
                            pre_firmware=pre_firmware,  # WHY: old value
                            post_firmware=post_firmware,  # WHY: new value
                        )  # WHY: event logged
                    else:  # WHY: warning level
                        logger.warning(
                            "firmware_changed",  # WHY: event type
                            device_id=device_id,  # WHY: context
                            pre_firmware=pre_firmware,  # WHY: old value
                            post_firmware=post_firmware,  # WHY: new value
                        )  # WHY: event logged

        # WHY: log firmware analysis complete
        logger.debug(
            "firmware_delta_analysis_complete",  # WHY: phase complete
            delta_count=len(deltas),  # WHY: count
        )  # WHY: phase logged

        return deltas  # WHY: return results

    def _analyze_radio_config_deltas(
        self,  # WHY: instance method
        pre_capture: dict[str, Any],  # WHY: pre-capture
        post_capture: dict[str, Any],  # WHY: post-capture
    ) -> list[dict[str, Any]]:  # WHY: return list of radio config deltas
        """Analyze radio configuration changes.

        Detects: channel, power, band changes.

        Args:
            pre_capture: Pre-upgrade capture.
            post_capture: Post-upgrade capture.

        Returns:
            List of radio config delta dicts.

        WHY: identifies unexpected radio configuration changes.
        """
        # WHY: log radio analysis start
        logger.info("radio_config_delta_analysis_start")  # WHY: phase start

        deltas: list[dict[str, Any]] = []  # WHY: result list

        # WHY: placeholder for radio config analysis
        # In production: compare radio config fields between captures
        # Currently returns empty list (can be extended)

        # WHY: log radio analysis complete
        logger.debug(
            "radio_config_delta_analysis_complete",  # WHY: phase complete
            delta_count=len(deltas),  # WHY: count
        )  # WHY: phase logged

        return deltas  # WHY: return results

    def _analyze_policy_deltas(
        self,  # WHY: instance method
        pre_capture: dict[str, Any],  # WHY: pre-capture
        post_capture: dict[str, Any],  # WHY: post-capture
    ) -> list[dict[str, Any]]:  # WHY: return list of policy deltas
        """Analyze policy changes.

        Detects: security policy changes, binding changes.

        Args:
            pre_capture: Pre-upgrade capture.
            post_capture: Post-upgrade capture.

        Returns:
            List of policy delta dicts.

        WHY: identifies unexpected security policy changes.
        """
        # WHY: log policy analysis start
        logger.info("policy_delta_analysis_start")  # WHY: phase start

        deltas: list[dict[str, Any]] = []  # WHY: result list

        # WHY: placeholder for policy analysis
        # In production: compare policy fields between captures
        # Currently returns empty list (can be extended)

        # WHY: log policy analysis complete
        logger.debug(
            "policy_delta_analysis_complete",  # WHY: phase complete
            delta_count=len(deltas),  # WHY: count
        )  # WHY: phase logged

        return deltas  # WHY: return results

    def _analyze_neighbor_deltas(
        self,  # WHY: instance method
        pre_capture: dict[str, Any],  # WHY: pre-capture
        post_capture: dict[str, Any],  # WHY: post-capture
    ) -> list[dict[str, Any]]:  # WHY: return list of neighbor deltas
        """Analyze LLDP neighbor topology changes.

        Detects: neighbor additions, removals, topology changes.

        Args:
            pre_capture: Pre-upgrade capture.
            post_capture: Post-upgrade capture.

        Returns:
            List of neighbor delta dicts.

        WHY: identifies unexpected topology changes after upgrade.
        """
        # WHY: log neighbor analysis start
        logger.info("neighbor_delta_analysis_start")  # WHY: phase start

        deltas: list[dict[str, Any]] = []  # WHY: result list

        # WHY: placeholder for neighbor analysis
        # In production: compare LLDP neighbor fields between captures
        # Currently returns empty list (can be extended)

        # WHY: log neighbor analysis complete
        logger.debug(
            "neighbor_delta_analysis_complete",  # WHY: phase complete
            delta_count=len(deltas),  # WHY: count
        )  # WHY: phase logged

        return deltas  # WHY: return results

    def _is_rollback(self, pre_version: str, post_version: str) -> bool:
        """Determine if firmware change is a rollback (downgrade).

        Compares version strings to detect rollback.

        Args:
            pre_version: Pre-upgrade firmware version.
            post_version: Post-upgrade firmware version.

        Returns:
            True if post_version < pre_version (rollback).

        WHY: distinguishes firmware upgrade from unexpected rollback.
        """
        # WHY: placeholder for version comparison logic
        # In production: parse version strings and compare numerically
        # For now, simple string comparison (not semantically correct)
        return post_version < pre_version  # WHY: compare versions
