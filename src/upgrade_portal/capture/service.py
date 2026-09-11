"""CaptureService for pre-upgrade and post-upgrade captures (T-006, T-011).

Implements FR-001 (pre-upgrade capture), FR-016 (post-upgrade capture),
and FR-019 (audit logging). Fetches device state from Mist API and persists
to ArangoDB with automatic retry on transient errors.
"""

import time  # WHY: retry backoff and timing measurements
import uuid  # WHY: unique capture IDs
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
        mist_client=None,  # WHY: Mist API client dependency
        db_router=None,  # WHY: ArangoDB persistence dependency
        audit_logger=None,  # WHY: audit trail dependency
    ):
        """Initialize CaptureService with dependencies.

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
            "capture_service_initialized",
            mist_client_available=mist_client is not None,  # WHY: dependency status
            db_available=db_router is not None,  # WHY: dependency status
            audit_available=audit_logger is not None,  # WHY: dependency status
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
                error=str(e),  # WHY: exception detail
                exception_type=type(e).__name__,  # WHY: exception class
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="capture_start",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message=str(e),  # WHY: error detail
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
        # WHY: persist to ArangoDB
        logger.info("capture_persisting_to_arangodb", capture_id=capture_id)  # WHY: persist start
        write_result = self.db_router.write(  # WHY: database write operation
            collection="upgrade_captures",  # WHY: collection name
            document=capture_doc,  # WHY: document to write
        )  # WHY: write operation result

        # WHY: verify persistence succeeded
        if not write_result:  # WHY: check write result
            logger.error("capture_persist_failed", capture_id=capture_id)  # WHY: persistence error
            return False  # WHY: persistence failed

        # WHY: audit log capture completion
        if self.audit_logger:  # WHY: audit logging conditional
            self.audit_logger.log_operation(  # WHY: audit trail
                operation="capture_start" if capture_type == "pre" else "capture_post",  # WHY: operation type
                user_id=capture_doc.get("user_id", ""),  # WHY: user context from document
                details={  # WHY: operation details
                    "capture_id": capture_id,  # WHY: identifier
                    "capture_type": capture_type,  # WHY: type marker
                    "device_count": device_count,  # WHY: metric
                    "run_id": run_id,  # WHY: run link
                },  # WHY: detail dict
                result="success",  # WHY: result status
            )  # WHY: audit entry

        return True  # WHY: persistence succeeded

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
                error=str(e),  # WHY: exception detail
                exception_type=type(e).__name__,  # WHY: exception class
            )  # WHY: exception logged

            # WHY: audit log failure
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="capture_post",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={"run_id": run_id},  # WHY: context details
                    result="failure",  # WHY: result status
                    error_message=str(e),  # WHY: error detail
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
                        error=str(e),  # WHY: exception detail
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
                    error=str(e),  # WHY: exception detail
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
        # WHY: client availability check
        if not self.mist_client:  # WHY: dependency check
            logger.error("mist_client_unavailable")  # WHY: dependency error
            return None  # WHY: fail

        # WHY: call Mist API to get device stats
        device_stats = self.mist_client.listSiteDeviceStats(  # WHY: API call
            org_id=org_id,  # WHY: API context
            site_id=site_id,  # WHY: API scope
            device_id=device_id,  # WHY: device identifier
        )  # WHY: API result

        # WHY: check if API returned data
        if not device_stats:  # WHY: empty response check
            logger.warning(
                "device_stats_empty",  # WHY: event type
                device_id=device_id,  # WHY: device context
            )  # WHY: warning event
            return None  # WHY: return None on empty

        # WHY: fetch device configuration
        device_config = self.mist_client.listSiteDeviceConfig(  # WHY: API call
            org_id=org_id,  # WHY: API context
            site_id=site_id,  # WHY: API scope
            device_id=device_id,  # WHY: device identifier
        )  # WHY: API result

        # WHY: fetch radio settings
        radio_settings = self.mist_client.listSiteDeviceRadios(  # WHY: API call
            org_id=org_id,  # WHY: API context
            site_id=site_id,  # WHY: API scope
            device_id=device_id,  # WHY: device identifier
        )  # WHY: API result

        # WHY: fetch security policies
        policies = self.mist_client.listSiteNetworkPolicies(  # WHY: API call
            org_id=org_id,  # WHY: API context
            site_id=site_id,  # WHY: API scope
        )  # WHY: API result

        # WHY: fetch LLDP neighbors
        lldp_neighbors = self.mist_client.listSiteDeviceLldpNeighbors(  # WHY: API call
            org_id=org_id,  # WHY: API context
            site_id=site_id,  # WHY: API scope
            device_id=device_id,  # WHY: device identifier
        )  # WHY: API result

        # WHY: build capture dict
        capture = {  # WHY: capture structure
            "device_id": device_id,  # WHY: device identifier
            "device_stats": device_stats or {},  # WHY: stats data
            "device_config": device_config or {},  # WHY: config data
            "radio_settings": radio_settings or {},  # WHY: radio data
            "policies": policies or {},  # WHY: policy data
            "lldp_neighbors": lldp_neighbors or {},  # WHY: neighbor data
            "fetch_timestamp": datetime.now(UTC).isoformat(),  # WHY: fetch time
        }  # WHY: complete capture

        # WHY: log successful fetch
        logger.debug(
            "device_capture_fetched",  # WHY: event type
            device_id=device_id,  # WHY: device context
        )  # WHY: success event

        return capture  # WHY: return capture

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
