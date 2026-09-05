"""CaptureService for pre-upgrade and post-upgrade snapshots (T-006, T-011).

Implements FR-001 (pre-upgrade capture), FR-016 (post-upgrade capture),
and FR-019 (audit logging). Fetches device state from Mist API and persists
to ArangoDB with automatic retry on transient errors.
"""

import logging  # WHY: structured operation logging
import time  # WHY: retry backoff and timing measurements
import uuid  # WHY: unique capture IDs
from datetime import datetime, timezone  # WHY: ISO 8601 timestamps
from typing import Any, Dict, List, Optional  # WHY: type hints for complex structures
from concurrent.futures import ThreadPoolExecutor, as_completed  # WHY: parallel device fetches

import structlog  # WHY: structured logging for observability

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class CaptureService:
    """Service for capturing device state snapshots before and after upgrades.

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
        run_id: str,  # WHY: unique run identifier for linking snapshots
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_ids: List[str],  # WHY: devices to capture
        user_id: str,  # WHY: audit trail user context
    ) -> Optional[str]:
        """Capture pre-upgrade device state snapshot.

        Fetches device configuration, radio settings, security policies,
        LLDP neighbors, and client counts from Mist API. Stores snapshot
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
            # WHY: validate inputs
            if not run_id or not isinstance(run_id, str):  # WHY: run_id validation
                logger.error("capture_invalid_run_id", run_id=run_id)  # WHY: validation error
                return None  # WHY: fail fast

            if not device_ids or not isinstance(device_ids, list):  # WHY: device list validation
                logger.error("capture_no_devices", device_count=len(device_ids) if device_ids else 0)  # WHY: validation error
                return None  # WHY: fail fast

            # WHY: check dependencies available
            if not self.mist_client or not self.db_router:  # WHY: dependency check
                logger.error("capture_dependencies_unavailable")  # WHY: missing dependencies
                return None  # WHY: fail fast

            # WHY: generate unique capture ID
            capture_id = str(uuid.uuid4())  # WHY: unique identifier
            # WHY: get current timestamp
            timestamp = datetime.now(timezone.utc).isoformat()  # WHY: ISO 8601 format

            # WHY: fetch device snapshots in parallel with retry
            logger.info("capture_fetching_devices", device_count=len(device_ids))  # WHY: fetch phase start
            device_snapshots = self._fetch_device_snapshots(  # WHY: parallel fetch operation
                org_id=org_id,  # WHY: API context
                site_id=site_id,  # WHY: API scope
                device_ids=device_ids,  # WHY: devices to fetch
            )  # WHY: fetch result

            # WHY: log fetch completion
            logger.info(
                "capture_fetch_complete",  # WHY: operation milestone
                device_count=len(device_snapshots),  # WHY: completion metric
            )  # WHY: fetch complete event

            # WHY: build capture document
            capture_doc = {  # WHY: ArangoDB document structure
                "_key": f"{run_id}_pre_{int(time.time() * 1000)}",  # WHY: composite primary key
                "capture_id": capture_id,  # WHY: public identifier
                "run_id": run_id,  # WHY: link to upgrade run
                "org_id": org_id,  # WHY: organization context
                "site_id": site_id,  # WHY: site context
                "capture_type": "pre",  # WHY: pre-upgrade marker
                "timestamp": timestamp,  # WHY: capture moment
                "device_snapshots": device_snapshots,  # WHY: snapshot array
                "snapshot_count": len(device_snapshots),  # WHY: summary metric
                "user_id": user_id,  # WHY: audit context
            }  # WHY: complete document

            # WHY: persist to ArangoDB
            logger.info("capture_persisting_to_arangodb", capture_id=capture_id)  # WHY: persist start
            write_result = self.db_router.write(  # WHY: database write operation
                collection="upgrade_captures",  # WHY: collection name
                document=capture_doc,  # WHY: document to write
            )  # WHY: write operation result

            # WHY: verify persistence succeeded
            if not write_result:  # WHY: check write result
                logger.error("capture_persist_failed", capture_id=capture_id)  # WHY: persistence error
                return None  # WHY: fail fast

            # WHY: audit log capture completion
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="capture_start",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={  # WHY: operation details
                        "capture_id": capture_id,  # WHY: identifier
                        "capture_type": "pre",  # WHY: type marker
                        "device_count": len(device_snapshots),  # WHY: metric
                        "run_id": run_id,  # WHY: run link
                    },  # WHY: detail dict
                    result="success",  # WHY: result status
                )  # WHY: audit entry

            # WHY: log success
            logger.info(
                "capture_pre_upgrade_success",  # WHY: operation name
                capture_id=capture_id,  # WHY: result identifier
                device_count=len(device_snapshots),  # WHY: result metric
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

    def capture_post_upgrade(
        self,
        run_id: str,  # WHY: unique run identifier for linking snapshots
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_ids: List[str],  # WHY: devices to capture
        user_id: str,  # WHY: audit trail user context
    ) -> Optional[str]:
        """Capture post-upgrade device state snapshot.

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
            # WHY: validate inputs
            if not run_id or not isinstance(run_id, str):  # WHY: run_id validation
                logger.error("capture_invalid_run_id", run_id=run_id)  # WHY: validation error
                return None  # WHY: fail fast

            if not device_ids or not isinstance(device_ids, list):  # WHY: device list validation
                logger.error("capture_no_devices", device_count=len(device_ids) if device_ids else 0)  # WHY: validation error
                return None  # WHY: fail fast

            # WHY: check dependencies available
            if not self.mist_client or not self.db_router:  # WHY: dependency check
                logger.error("capture_dependencies_unavailable")  # WHY: missing dependencies
                return None  # WHY: fail fast

            # WHY: generate unique capture ID
            capture_id = str(uuid.uuid4())  # WHY: unique identifier
            # WHY: get current timestamp
            timestamp = datetime.now(timezone.utc).isoformat()  # WHY: ISO 8601 format

            # WHY: fetch device snapshots in parallel with retry
            logger.info("capture_fetching_devices", device_count=len(device_ids))  # WHY: fetch phase start
            device_snapshots = self._fetch_device_snapshots(  # WHY: parallel fetch operation
                org_id=org_id,  # WHY: API context
                site_id=site_id,  # WHY: API scope
                device_ids=device_ids,  # WHY: devices to fetch
            )  # WHY: fetch result

            # WHY: log fetch completion
            logger.info(
                "capture_fetch_complete",  # WHY: operation milestone
                device_count=len(device_snapshots),  # WHY: completion metric
            )  # WHY: fetch complete event

            # WHY: build capture document
            capture_doc = {  # WHY: ArangoDB document structure
                "_key": f"{run_id}_post_{int(time.time() * 1000)}",  # WHY: composite primary key
                "capture_id": capture_id,  # WHY: public identifier
                "run_id": run_id,  # WHY: link to upgrade run
                "org_id": org_id,  # WHY: organization context
                "site_id": site_id,  # WHY: site context
                "capture_type": "post",  # WHY: post-upgrade marker
                "timestamp": timestamp,  # WHY: capture moment
                "device_snapshots": device_snapshots,  # WHY: snapshot array
                "snapshot_count": len(device_snapshots),  # WHY: summary metric
                "user_id": user_id,  # WHY: audit context
            }  # WHY: complete document

            # WHY: persist to ArangoDB
            logger.info("capture_persisting_to_arangodb", capture_id=capture_id)  # WHY: persist start
            write_result = self.db_router.write(  # WHY: database write operation
                collection="upgrade_captures",  # WHY: collection name
                document=capture_doc,  # WHY: document to write
            )  # WHY: write operation result

            # WHY: verify persistence succeeded
            if not write_result:  # WHY: check write result
                logger.error("capture_persist_failed", capture_id=capture_id)  # WHY: persistence error
                return None  # WHY: fail fast

            # WHY: audit log capture completion
            if self.audit_logger:  # WHY: audit logging conditional
                self.audit_logger.log_operation(  # WHY: audit trail
                    operation="capture_post",  # WHY: operation type
                    user_id=user_id,  # WHY: user context
                    details={  # WHY: operation details
                        "capture_id": capture_id,  # WHY: identifier
                        "capture_type": "post",  # WHY: type marker
                        "device_count": len(device_snapshots),  # WHY: metric
                        "run_id": run_id,  # WHY: run link
                    },  # WHY: detail dict
                    result="success",  # WHY: result status
                )  # WHY: audit entry

            # WHY: log success
            logger.info(
                "capture_post_upgrade_success",  # WHY: operation name
                capture_id=capture_id,  # WHY: result identifier
                device_count=len(device_snapshots),  # WHY: result metric
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

    def _fetch_device_snapshots(
        self,
        org_id: str,  # WHY: organization context for API calls
        site_id: str,  # WHY: site context for API calls
        device_ids: List[str],  # WHY: devices to fetch
    ) -> List[Dict[str, Any]]:  # WHY: return array of snapshots
        """Fetch device snapshots in parallel with automatic retry.

        Uses ThreadPoolExecutor to fetch multiple devices concurrently,
        with exponential backoff retry on transient errors. Timeout per
        device prevents indefinite hangs on slow API responses.

        Args:
            org_id: Organization ID for API context.
            site_id: Site ID for API scope.
            device_ids: List of device IDs to fetch.

        Returns:
            List of device snapshot dicts (successful fetches only).

        WHY: implements parallel fetch with retry per SC-002
        (multi-threaded capture) and timeout handling.
        """
        # WHY: initialize results array
        snapshots = []  # WHY: accumulator for results

        # WHY: log fetch start
        logger.info(
            "device_snapshot_fetch_start",  # WHY: operation name
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
                    snapshot = future.result(timeout=self.DEVICE_API_TIMEOUT_SECONDS)  # WHY: fetch result with timeout
                    # WHY: check if fetch succeeded
                    if snapshot:  # WHY: success check
                        snapshots.append(snapshot)  # WHY: add to results
                        # WHY: log successful fetch
                        logger.debug(
                            "device_snapshot_fetch_success",  # WHY: event type
                            device_id=device_id,  # WHY: device context
                        )  # WHY: success event
                    else:  # WHY: fetch returned None
                        # WHY: log fetch failure
                        logger.warning(
                            "device_snapshot_fetch_returned_none",  # WHY: event type
                            device_id=device_id,  # WHY: device context
                        )  # WHY: fetch warning

                except TimeoutError:  # WHY: catch timeout exceptions
                    # WHY: log timeout
                    logger.warning(
                        "device_snapshot_fetch_timeout",  # WHY: event type
                        device_id=device_id,  # WHY: device context
                        timeout_seconds=self.DEVICE_API_TIMEOUT_SECONDS,  # WHY: timeout value
                    )  # WHY: timeout event

                except Exception as e:  # WHY: catch other exceptions
                    # WHY: log fetch exception
                    logger.error(
                        "device_snapshot_fetch_exception",  # WHY: event type
                        device_id=device_id,  # WHY: device context
                        error=str(e),  # WHY: exception detail
                    )  # WHY: error event

        # WHY: log fetch completion
        logger.info(
            "device_snapshot_fetch_complete",  # WHY: operation name
            requested=len(device_ids),  # WHY: requested count
            fetched=len(snapshots),  # WHY: success count
        )  # WHY: completion event

        return snapshots  # WHY: return collected snapshots

    def _fetch_device_with_retry(
        self,
        org_id: str,  # WHY: organization context
        site_id: str,  # WHY: site context
        device_id: str,  # WHY: device identifier
    ) -> Optional[Dict[str, Any]]:  # WHY: return device snapshot or None
        """Fetch single device snapshot with exponential backoff retry.

        Attempts to fetch device state from Mist API. On transient errors
        (timeout, rate limit), retries up to MAX_RETRIES with exponential
        backoff. Permanent errors (404, auth) fail immediately.

        Args:
            org_id: Organization ID for API context.
            site_id: Site ID for API scope.
            device_id: Device ID to fetch.

        Returns:
            Device snapshot dict if successful, None if all retries exhausted.

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
                    "device_snapshot_fetch_attempt",  # WHY: event type
                    device_id=device_id,  # WHY: device context
                    attempt=attempt + 1,  # WHY: attempt number (1-indexed)
                    max_attempts=self.MAX_RETRIES,  # WHY: limit for logging
                )  # WHY: attempt event

                # WHY: fetch device inventory from Mist API
                if not self.mist_client:  # WHY: client availability check
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

                # WHY: build snapshot dict
                snapshot = {  # WHY: snapshot structure
                    "device_id": device_id,  # WHY: device identifier
                    "device_stats": device_stats or {},  # WHY: stats data
                    "device_config": device_config or {},  # WHY: config data
                    "radio_settings": radio_settings or {},  # WHY: radio data
                    "policies": policies or {},  # WHY: policy data
                    "lldp_neighbors": lldp_neighbors or {},  # WHY: neighbor data
                    "fetch_timestamp": datetime.now(timezone.utc).isoformat(),  # WHY: fetch time
                }  # WHY: complete snapshot

                # WHY: log successful fetch
                logger.debug(
                    "device_snapshot_fetched",  # WHY: event type
                    device_id=device_id,  # WHY: device context
                )  # WHY: success event

                return snapshot  # WHY: return snapshot on success

            except TimeoutError:  # WHY: catch timeout errors
                # WHY: log timeout
                logger.warning(
                    "device_fetch_timeout",  # WHY: event type
                    device_id=device_id,  # WHY: device context
                    attempt=attempt + 1,  # WHY: attempt number
                )  # WHY: timeout event

                # WHY: increment retry counter
                attempt += 1  # WHY: next attempt

                # WHY: check if retries remain
                if attempt < self.MAX_RETRIES:  # WHY: retry check
                    # WHY: calculate exponential backoff
                    backoff = self.RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))  # WHY: backoff calculation
                    # WHY: log retry plan
                    logger.info(
                        "device_fetch_retrying",  # WHY: event type
                        device_id=device_id,  # WHY: device context
                        backoff_seconds=backoff,  # WHY: backoff time
                    )  # WHY: retry event
                    # WHY: sleep before retry
                    time.sleep(backoff)  # WHY: backoff delay
                else:  # WHY: retries exhausted
                    # WHY: log retry exhaustion
                    logger.error(
                        "device_fetch_retries_exhausted",  # WHY: event type
                        device_id=device_id,  # WHY: device context
                        attempts=self.MAX_RETRIES,  # WHY: total attempts
                    )  # WHY: error event
                    return None  # WHY: fail after retries

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
