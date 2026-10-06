"""CaptureService for pre-upgrade and post-upgrade captures (T-006, T-011).

Implements FR-001 (pre-upgrade capture), FR-016 (post-upgrade capture),
and FR-019 (audit logging). Fetches device state from Mist API and persists
to ArangoDB with automatic retry on transient errors.
"""

import time  # WHY: retry backoff and timing measurements
import uuid  # WHY: unique capture IDs
from collections.abc import Mapping  # WHY: accept canonical capture request records.
from concurrent.futures import ThreadPoolExecutor, as_completed  # WHY: parallel device fetches
from datetime import UTC, datetime  # WHY: ISO 8601 timestamps
from typing import Any  # WHY: type hints for complex structures

import structlog  # WHY: structured logging for observability

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class CaptureService:
    """Service for capturing device state captures before and after upgrades.

    Implements parallel API calls with automatic retry, timeout handling,
    and persistent storage to ArangoDB. Satisfies FR-001, FR-016, FR-019,
    and SC-010 (audit logging with zero secrets).
    """

    # WHY: maximum retry attempts for transient errors (API timeouts, rate limits)
    MAX_RETRIES = 3  # WHY: retry configuration constant
    # WHY: initial backoff between retries (exponential backoff: 1s, 2s, 4s)
    RETRY_BACKOFF_SECONDS = 1  # WHY: backoff constant
    # WHY: per-device API call timeout to prevent hanging
    DEVICE_API_TIMEOUT_SECONDS = 30  # WHY: timeout constant
    # WHY: maximum concurrent device fetch threads (per SC-003: reasonable concurrency)
    MAX_WORKER_THREADS = 8  # WHY: thread pool size constant

    def __init__(
        self,
        mist_client: Any = None,  # WHY: The authenticated request session owns cloud calls.
        db_router: Any = None,  # WHY: The router owns registered export writes.
        audit_logger: Any = None,  # WHY: The audit service owns action records.
        document_store: Any = None,  # WHY: The explicit handle owns portal documents.
    ) -> None:
        """Initialize CaptureService with dependencies.

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
            "capture_service_initialized",
            mist_client_available=mist_client is not None,  # WHY: dependency status
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
            document_store_available=document_store is not None,  # WHY: dependency status
        )  # WHY: startup event

    def capture_pre_upgrade(
        self,
        run_id: str,  # WHY: unique run identifier for linking captures
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_ids: list[str],  # WHY: devices to capture
        user_id: str,  # WHY: audit trail user context
    ) -> str | None:
        """Capture pre-upgrade device state capture.

        Fetches device configuration, radio settings, security policies,
        LLDP neighbors, and client counts from Mist API. Stores capture
        to ArangoDB with composite key (run_id, capture_type="pre", timestamp).

        Args:
            run_id: Unique run ID (links to upgrade_runs).
            org_id: Organization ID for API context.
            site_id: Site ID for device scope.
            device_ids: List of device IDs to capture.
            user_id: User initiating capture (audit trail).

        Returns:
            Capture ID if successful, None if failed.

        WHY: implements FR-001 (pre-upgrade capture) with automatic retry
        and persistent storage per SC-004 (ArangoDB primary storage).
        """
        return self._capture_site(
            {
                "run_id": run_id,
                "org_id": org_id,
                "site_id": site_id,
                "device_ids": device_ids,
                "user_id": user_id,
                "capture_type": "pre",
            }
        )
        # WHY: log capture start
        logger.info(
            "capture_pre_upgrade_start",  # WHY: operation name
            run_id=run_id,  # WHY: run context
            device_count=len(device_ids),  # WHY: scope summary
            user_id=user_id,  # WHY: audit context
        )  # WHY: pre-operation event

        try:
            # WHY: validate inputs and dependencies before any work
            if self._validate_capture_inputs(run_id, device_ids):  # WHY: shared validation helper
                return None  # WHY: fail fast on invalid input

            # WHY: generate unique capture ID
            capture_id = str(uuid.uuid4())  # WHY: unique identifier
            # WHY: get current timestamp
            timestamp = datetime.now(UTC).isoformat()  # WHY: ISO 8601 format

            # WHY: fetch device captures in parallel with retry
            logger.info("capture_fetching_devices", device_count=len(device_ids))  # WHY: fetch phase start
            device_captures = self._fetch_device_captures(  # WHY: parallel fetch operation
                org_id=org_id,  # WHY: API context
                site_id=site_id,  # WHY: API scope
                device_ids=device_ids,  # WHY: devices to fetch
            )  # WHY: fetch result

            # WHY: log fetch completion
            logger.info(
                "capture_fetch_complete",  # WHY: operation milestone
                device_count=len(device_captures),  # WHY: completion metric
            )  # WHY: fetch complete event

            # WHY: build the capture document with the call context
            capture_doc = self._build_capture_doc(  # WHY: shared document builder
                run_id=run_id,  # WHY: run link
                capture_id=capture_id,  # WHY: public identifier
                capture_type="pre",  # WHY: pre-upgrade marker
                timestamp=timestamp,  # WHY: capture moment
                device_captures=device_captures,  # WHY: capture array
            )  # WHY: document ready for context fields
            capture_doc["org_id"] = org_id  # WHY: organization context
            capture_doc["site_id"] = site_id  # WHY: site context
            capture_doc["user_id"] = user_id  # WHY: audit context

            # WHY: persist the capture document
            if not self._persist_capture(  # WHY: persist phase
                capture_doc=capture_doc,  # WHY: document to write
                capture_id=capture_id,  # WHY: public identifier
                capture_type="pre",  # WHY: pre-upgrade marker
                device_count=len(device_captures),  # WHY: summary metric
                run_id=run_id,  # WHY: run link
            ):  # WHY: persist result
                return None  # WHY: fail fast on persistence error

            # WHY: log success
            logger.info(
                "capture_pre_upgrade_success",  # WHY: operation name
                capture_id=capture_id,  # WHY: result identifier
                device_count=len(device_captures),  # WHY: result metric
            )  # WHY: success event

            return capture_id  # WHY: return capture ID on success

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "capture_pre_upgrade_exception",  # WHY: error event
                error_type=type(e).__name__,
                exception_type=type(e).__name__,  # WHY: exception class
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="capture_start",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message="The capture operation failed.",  # WHY: keep dependency text private.
                )  # WHY: audit entry

            return None  # WHY: fail on exception

    def _validate_capture_inputs(
        self,
        run_id: str,  # WHY: run identifier to validate
        device_ids: list[str],  # WHY: device list to validate
    ) -> bool:  # WHY: True when validation failed
        """Validate capture inputs and dependencies.

        Args:
            run_id: Run ID to validate.
            device_ids: Device list to validate.

        Returns:
            True when validation failed, False when inputs are valid.

        WHY: shared validation keeps capture_pre_upgrade and
        capture_post_upgrade under the complexity limit.
        """
        # WHY: validate run_id
        if not run_id or not isinstance(run_id, str):  # WHY: run_id validation
            logger.error("capture_invalid_run_id", run_id=run_id)  # WHY: validation error
            return True  # WHY: validation failed

        # WHY: validate device list
        if not device_ids or not isinstance(device_ids, list):  # WHY: device list validation
            logger.error(
                "capture_no_devices", device_count=len(device_ids) if device_ids else 0
            )  # WHY: validation error
            return True  # WHY: validation failed

        # WHY: check dependencies available
        if not self.mist_client or not self.db_router:  # WHY: dependency check
            logger.error("capture_dependencies_unavailable")  # WHY: missing dependencies
            return True  # WHY: validation failed

        return False  # WHY: inputs are valid

    def _build_capture_doc(
        self,
        run_id: str,  # WHY: run link
        capture_id: str,  # WHY: public identifier
        capture_type: str,  # WHY: pre or post marker
        timestamp: str,  # WHY: capture moment
        device_captures: list[dict[str, Any]],  # WHY: capture array
    ) -> dict[str, Any]:  # WHY: return the ArangoDB document
        """Build the ArangoDB capture document for a pre or post capture.

        Args:
            run_id: Run ID that links the capture.
            capture_id: Public capture identifier.
            capture_type: "pre" or "post" marker.
            timestamp: ISO 8601 capture moment.
            device_captures: Array of device capture dicts.

        Returns:
            The document dict ready for the persistence step.

        WHY: shared document construction keeps both capture methods under
        the complexity limit while writing the same document shape.
        """
        # WHY: build capture document
        capture_doc = {  # WHY: ArangoDB document structure
            "_key": f"{run_id}_{capture_type}_{int(time.time() * 1000)}",  # WHY: composite primary key
            "capture_id": capture_id,  # WHY: public identifier
            "run_id": run_id,  # WHY: link to upgrade run
            "capture_type": capture_type,  # WHY: capture type marker
            "timestamp": timestamp,  # WHY: capture moment
            "device_captures": device_captures,  # WHY: capture array
            "capture_count": len(device_captures),  # WHY: summary metric
        }  # WHY: complete document
        return capture_doc  # WHY: hand document to the persist step

    def _persist_capture(
        self,
        capture_doc: dict[str, Any],  # WHY: document to write
        capture_id: str,  # WHY: public identifier
        capture_type: str,  # WHY: pre or post marker
        device_count: int,  # WHY: summary metric for the audit entry
        run_id: str,  # WHY: run link for the audit entry
    ) -> bool:  # WHY: True when persistence succeeded
        """Persist a capture document and audit-log the operation.

        Args:
            capture_doc: Document built by _build_capture_doc.
            capture_id: Public capture identifier.
            capture_type: "pre" or "post" marker.
            device_count: Number of devices in the capture.
            run_id: Run ID that links the capture.

        Returns:
            True when the capture persisted, False when the write failed.

        WHY: shared persistence keeps both capture methods under the
        complexity limit while preserving the exact log and audit order.
        """
        if self.document_store is None:
            logger.error("capture_document_store_unavailable", capture_id=capture_id)
            return False  # WHY: persistence failed

        from src.interfaces.portals.upgrade_portal.capture import store

        result = store.write_capture(capture_doc, database=self.document_store)
        if not result.verified or not result.comparable or self.audit_logger is None:
            logger.error("capture_persist_failed", capture_id=capture_id, reason=result.reason)
            return False
        audit_id = self.audit_logger.log_operation(
            operation="capture_start" if capture_type == "pre" else "capture_post",
            user_id=capture_doc.get("user_id", ""),
            details={
                "capture_id": capture_id,
                "capture_type": capture_type,
                "device_count": device_count,
                "run_id": run_id,
            },
            result="success",
        )
        return audit_id is not None

    def capture_post_upgrade(
        self,
        run_id: str,  # WHY: unique run identifier for linking captures
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_ids: list[str],  # WHY: devices to capture
        user_id: str,  # WHY: audit trail user context
    ) -> str | None:
        """Capture post-upgrade device state capture.

        Identical to capture_pre_upgrade but stores with capture_type="post".
        Captures device state after firmware upgrade and network settle.

        Args:
            run_id: Unique run ID (links to upgrade_runs).
            org_id: Organization ID for API context.
            site_id: Site ID for device scope.
            device_ids: List of device IDs to capture.
            user_id: User initiating capture (audit trail).

        Returns:
            Capture ID if successful, None if failed.

        WHY: implements FR-016 (post-upgrade capture) and T-011 requirement.
        """
        return self._capture_site(
            {
                "run_id": run_id,
                "org_id": org_id,
                "site_id": site_id,
                "device_ids": device_ids,
                "user_id": user_id,
                "capture_type": "post",
            }
        )
        # WHY: log capture start
        logger.info(
            "capture_post_upgrade_start",  # WHY: operation name
            run_id=run_id,  # WHY: run context
            device_count=len(device_ids),  # WHY: scope summary
            user_id=user_id,  # WHY: audit context
        )  # WHY: pre-operation event

        try:
            # WHY: validate inputs and dependencies before any work
            if self._validate_capture_inputs(run_id, device_ids):  # WHY: shared validation helper
                return None  # WHY: fail fast on invalid input

            # WHY: generate unique capture ID
            capture_id = str(uuid.uuid4())  # WHY: unique identifier
            # WHY: get current timestamp
            timestamp = datetime.now(UTC).isoformat()  # WHY: ISO 8601 format

            # WHY: fetch device captures in parallel with retry
            logger.info("capture_fetching_devices", device_count=len(device_ids))  # WHY: fetch phase start
            device_captures = self._fetch_device_captures(  # WHY: parallel fetch operation
                org_id=org_id,  # WHY: API context
                site_id=site_id,  # WHY: API scope
                device_ids=device_ids,  # WHY: devices to fetch
            )  # WHY: fetch result

            # WHY: log fetch completion
            logger.info(
                "capture_fetch_complete",  # WHY: operation milestone
                device_count=len(device_captures),  # WHY: completion metric
            )  # WHY: fetch complete event

            # WHY: build the capture document with the call context
            capture_doc = self._build_capture_doc(  # WHY: shared document builder
                run_id=run_id,  # WHY: run link
                capture_id=capture_id,  # WHY: public identifier
                capture_type="post",  # WHY: post-upgrade marker
                timestamp=timestamp,  # WHY: capture moment
                device_captures=device_captures,  # WHY: capture array
            )  # WHY: document ready for context fields
            capture_doc["org_id"] = org_id  # WHY: organization context
            capture_doc["site_id"] = site_id  # WHY: site context
            capture_doc["user_id"] = user_id  # WHY: audit context

            # WHY: persist the capture document
            if not self._persist_capture(  # WHY: persist phase
                capture_doc=capture_doc,  # WHY: document to write
                capture_id=capture_id,  # WHY: public identifier
                capture_type="post",  # WHY: post-upgrade marker
                device_count=len(device_captures),  # WHY: summary metric
                run_id=run_id,  # WHY: run link
            ):  # WHY: persist result
                return None  # WHY: fail fast on persistence error

            # WHY: log success
            logger.info(
                "capture_post_upgrade_success",  # WHY: operation name
                capture_id=capture_id,  # WHY: result identifier
                device_count=len(device_captures),  # WHY: result metric
            )  # WHY: success event

            return capture_id  # WHY: return capture ID on success

        except Exception as e:  # WHY: catch unexpected exceptions
            # WHY: log exception
            logger.error(
                "capture_post_upgrade_exception",  # WHY: error event
                error_type=type(e).__name__,
                exception_type=type(e).__name__,  # WHY: exception class
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="capture_post",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message="The capture operation failed.",  # WHY: keep dependency text private.
                )  # WHY: audit entry

            return None  # WHY: fail on exception

    def _fetch_device_captures(
        self,
        org_id: str,  # WHY: organization context for API calls
        site_id: str,  # WHY: site context for API calls
        device_ids: list[str],  # WHY: devices to fetch
    ) -> list[dict[str, Any]]:  # WHY: return array of captures
        """Fetch device captures in parallel with automatic retry.

        Uses ThreadPoolExecutor to fetch multiple devices concurrently,
        with exponential backoff retry on transient errors. Timeout per
        device prevents indefinite hangs on slow API responses.

        Args:
            org_id: Organization ID for API context.
            site_id: Site ID for API scope.
            device_ids: List of device IDs to fetch.

        Returns:
            List of device capture dicts (successful fetches only).

        WHY: implements parallel fetch with retry per SC-002
        (multi-threaded capture) and timeout handling.
        """
        # WHY: initialize results array
        captures = []  # WHY: accumulator for results

        # WHY: log fetch start
        logger.info(
            "device_capture_fetch_start",  # WHY: operation name
            device_count=len(device_ids),  # WHY: scope metric
        )  # WHY: operation start

        # WHY: create thread pool for parallel fetches
        with ThreadPoolExecutor(max_workers=self.MAX_WORKER_THREADS) as executor:  # WHY: thread pool context
            # WHY: submit fetch task for each device
            future_to_device = {
                executor.submit(  # WHY: submit async task
                    self._fetch_device_with_retry,  # WHY: task function
                    org_id=org_id,  # WHY: API context
                    site_id=site_id,  # WHY: API scope
                    device_id=device_id,  # WHY: device identifier
                ): device_id  # WHY: map future to device_id
                for device_id in device_ids  # WHY: iterate devices
            }  # WHY: future map

            # WHY: collect results as tasks complete
            for future in as_completed(future_to_device):  # WHY: iterate completions
                # WHY: get device_id from mapping
                device_id = future_to_device[future]  # WHY: device context

                try:
                    # WHY: get result with exception handling
                    capture = future.result(timeout=self.DEVICE_API_TIMEOUT_SECONDS)  # WHY: fetch result with timeout
                    # WHY: check if fetch succeeded
                    if capture:  # WHY: success check
                        captures.append(capture)  # WHY: add to results
                        # WHY: log successful fetch
                        logger.debug(
                            "device_capture_fetch_success",  # WHY: event type
                            device_id=device_id,  # WHY: device context
                        )  # WHY: success event
                    else:  # WHY: fetch returned None
                        # WHY: log fetch failure
                        logger.warning(
                            "device_capture_fetch_returned_none",  # WHY: event type
                            device_id=device_id,  # WHY: device context
                        )  # WHY: fetch warning

                except TimeoutError:  # WHY: catch timeout exceptions
                    # WHY: log timeout
                    logger.warning(
                        "device_capture_fetch_timeout",  # WHY: event type
                        device_id=device_id,  # WHY: device context
                        timeout_seconds=self.DEVICE_API_TIMEOUT_SECONDS,  # WHY: timeout value
                    )  # WHY: timeout event

                except Exception as e:  # WHY: catch other exceptions
                    # WHY: log fetch exception
                    logger.error(
                        "device_capture_fetch_exception",  # WHY: event type
                        device_id=device_id,  # WHY: device context
                        error_type=type(e).__name__,
                    )  # WHY: error event

        # WHY: log fetch completion
        logger.info(
            "device_capture_fetch_complete",  # WHY: operation name
            requested=len(device_ids),  # WHY: requested count
            fetched=len(captures),  # WHY: success count
        )  # WHY: completion event

        return captures  # WHY: return collected captures

    def _fetch_device_with_retry(
        self,
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_id: str,  # WHY: device identifier
    ) -> dict[str, Any] | None:  # WHY: return device capture or None
        """Fetch single device capture with exponential backoff retry.

        Attempts to fetch device state from Mist API. On transient errors
        (timeout, rate limit), retries up to MAX_RETRIES with exponential
        backoff. Permanent errors (404, auth) fail immediately.

        Args:
            org_id: Organization ID for API context.
            site_id: Site ID for API scope.
            device_id: Device ID to fetch.

        Returns:
            Device capture dict if successful, None if all retries exhausted.

        WHY: implements retry logic per T-006 requirement
        (retry up to 3 times on API timeout).
        """
        # WHY: initialize retry counter
        attempt = 0  # WHY: attempt counter

        # WHY: retry loop
        while attempt < self.MAX_RETRIES:  # WHY: retry limit
            try:
                # WHY: log fetch attempt
                logger.debug(
                    "device_capture_fetch_attempt",  # WHY: event type
                    device_id=device_id,  # WHY: device context
                    attempt=attempt + 1,  # WHY: attempt number (1-indexed)
                    max_attempts=self.MAX_RETRIES,  # WHY: limit for logging
                )  # WHY: attempt event

                # WHY: fetch all device data in one helper
                capture = self._fetch_device_capture(  # WHY: delegate fetch
                    org_id=org_id,  # WHY: API context
                    site_id=site_id,  # WHY: API scope
                    device_id=device_id,  # WHY: device identifier
                )  # WHY: capture result

                # WHY: fail fast on empty response
                if capture is None:  # WHY: empty check
                    return None  # WHY: no data

                return capture  # WHY: return capture on success

            except TimeoutError:  # WHY: catch timeout errors
                # WHY: compute backoff or signal exhaustion
                backoff = self._timeout_backoff(  # WHY: delegate timeout handling
                    attempt=attempt,  # WHY: current attempt
                    device_id=device_id,  # WHY: device context
                )  # WHY: backoff result

                # WHY: increment retry counter
                attempt += 1  # WHY: next attempt

                # WHY: stop when retries are exhausted
                if backoff is None:  # WHY: exhaustion check
                    return None  # WHY: fail after retries

                # WHY: sleep before retry
                time.sleep(backoff)  # WHY: backoff delay

            except Exception as e:  # WHY: catch other exceptions
                # WHY: log exception
                logger.error(
                    "device_fetch_exception",  # WHY: event type
                    device_id=device_id,  # WHY: device context
                    error_type=type(e).__name__,
                    exception_type=type(e).__name__,  # WHY: exception class
                )  # WHY: error event

                return None  # WHY: fail on exception

        return None  # WHY: fail if all retries exhausted

    def _fetch_device_capture(
        self,
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_id: str,  # WHY: device identifier
    ) -> dict[str, Any] | None:  # WHY: return device capture or None
        """Fetch all device data from Mist API in a single pass.

        Args:
            org_id: Organization ID for API context.
            site_id: Site ID for API scope.
            device_id: Device ID to fetch.

        Returns:
            Device capture dict if successful, None if data is empty.
        """
        from src.interfaces.portals.upgrade_portal.capture.devices import normalize_device_mac, read_device_statistics

        if self.mist_client is None:
            return None
        reading = read_device_statistics(self.mist_client, site_id)
        if reading.partial_reasons:
            return None
        wanted = normalize_device_mac(device_id)
        row = next((entry for entry in reading.records if normalize_device_mac(entry.get("mac")) == wanted), None)
        if row is None:
            return None
        return {"device_id": wanted, "device_stats": dict(row), "fetch_timestamp": datetime.now(UTC).isoformat()}

    def _capture_site(self, request: Mapping[str, Any]) -> str | None:
        """Assemble, persist, and verify one canonical site capture."""
        if self._validate_capture_inputs(str(request.get("run_id", "")), list(request.get("device_ids", []))):
            return None
        if self.document_store is None:
            logger.error("capture_document_store_unavailable")
            return None
        try:
            from src.interfaces.portals.upgrade_portal.capture import assembly, collector, store

            run_id = str(request["run_id"])
            ordinal = 1 if request.get("capture_type") == "pre" else 2
            capture_id = assembly.capture_key(run_id, ordinal)
            job = self._capture_job(request, capture_id, ordinal)
            resources = self._capture_resources(collector, store)
            document = collector.build_document(job, self.mist_client, resources)
            if not self._requested_devices_present(request, document):
                return None
            collector.store_capture(capture_id, document, resources)
            loaded = store.load_capture_for_comparison(capture_id, database=self.document_store)
            if not loaded.comparable or self.audit_logger is None:
                return None
            audit_id = self.audit_logger.log_operation(
                operation="capture_start",
                user_id=str(request.get("user_id", "")),
                details={"run_id": run_id, "capture_id": capture_id, "capture_type": request.get("capture_type")},
                result="success",
            )
            return capture_id if audit_id is not None else None
        except Exception as fault:
            logger.error("capture_site_failed", error_type=type(fault).__name__)
            return None

    @staticmethod
    def _capture_job(request: Mapping[str, Any], capture_id: str, ordinal: int) -> dict[str, Any]:
        """Build the request-free job record required by the existing collector."""
        return {
            "capture_id": capture_id,
            "run_id": str(request.get("run_id", "")),
            "ordinal": ordinal,
            "actor_email": str(request.get("user_id", "")),
            "org_id": str(request.get("org_id", "")),
            "site_id": str(request.get("site_id", "")),
            "tier": 3,
        }

    def _capture_resources(self, collector: Any, store: Any) -> Any:
        """Bind the canonical store to this request's document handle."""
        capture_store = collector.CaptureStore(
            write=lambda document: store.write_capture(document, database=self.document_store),
            read_back=lambda capture_id: store.load_capture_for_comparison(capture_id, database=self.document_store),
        )
        return collector.CaptureResources(
            session=self.mist_client,
            store=capture_store,
            report=lambda capture_id, changes: logger.debug(
                "capture_progress_recorded", capture_id=capture_id, fields=len(changes)
            ),
        )

    @staticmethod
    def _requested_devices_present(request: Mapping[str, Any], document: Mapping[str, Any]) -> bool:
        """Require every requested address in the canonical site capture."""
        from src.interfaces.portals.upgrade_portal.capture.devices import normalize_device_mac

        index = document.get("device_index")
        if not isinstance(index, Mapping) or not index:
            return False
        requested = {normalize_device_mac(device_id) for device_id in request.get("device_ids", [])}
        return bool(requested) and requested.issubset(index.keys())

    def _timeout_backoff(
        self,
        attempt: int,  # WHY: current attempt index
        device_id: str,  # WHY: device context
    ) -> float | None:  # WHY: backoff seconds or None when exhausted
        """Compute the backoff delay for a timed-out fetch attempt.

        Args:
            attempt: Zero-based attempt index that just failed.
            device_id: Device ID for log context.

        Returns:
            Backoff seconds to sleep, or None when retries are exhausted.
        """
        # WHY: log timeout
        logger.warning(
            "device_fetch_timeout",  # WHY: event type
            device_id=device_id,  # WHY: device context
            attempt=attempt + 1,  # WHY: attempt number
        )  # WHY: timeout event

        # WHY: check if retries remain
        if attempt + 1 < self.MAX_RETRIES:  # WHY: retry check
            # WHY: calculate exponential backoff
            backoff = self.RETRY_BACKOFF_SECONDS * (2**attempt)  # WHY: backoff calculation
            # WHY: log retry plan
            logger.info(
                "device_fetch_retrying",  # WHY: event type
                device_id=device_id,  # WHY: device context
                backoff_seconds=backoff,  # WHY: backoff time
            )  # WHY: retry event
            return backoff  # WHY: sleep this long before retry

        # WHY: log retry exhaustion
        logger.error(
            "device_fetch_retries_exhausted",  # WHY: event type
            device_id=device_id,  # WHY: device context
            attempts=self.MAX_RETRIES,  # WHY: total attempts
        )  # WHY: error event
        return None  # WHY: no more retries
