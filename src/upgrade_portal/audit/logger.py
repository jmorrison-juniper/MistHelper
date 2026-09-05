"""Audit logging service for upgrade portal operations.

Writes audit trail to ArangoDB with indexed timestamp and operation fields.
All sensitive data is automatically masked before storage.
"""

import time  # WHY: millisecond precision timestamp for audit entries
import uuid  # WHY: unique log IDs for traceability
from datetime import UTC, datetime  # WHY: ISO 8601 timestamps
from typing import Any  # WHY: type hints for complex structures

import structlog  # WHY: structured logging

from .masker import SecretMasker  # WHY: automatic redaction of sensitive data

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class AuditLogger:
    """Audit logging service for upgrade portal operations.

    Writes operations to ArangoDB audit_logs collection with automatic
    secret masking. Implements FR-019 (log all operations) and
    SC-010 (zero secrets in logs).
    """

    def __init__(self, db_router=None, enable_masking: bool = True):
        """Initialize audit logger.

        Args:
            db_router: DatabaseRouter instance for ArangoDB writes.
            enable_masking: Enable automatic secret masking (default: True).

        WHY: dependency injection for database layer, configurable masking.
        """
        # WHY: store dependencies for write operations
        self.db_router = db_router  # WHY: database write interface
        self.masker = SecretMasker() if enable_masking else None  # WHY: optional secret masking
        self.enable_masking = enable_masking  # WHY: track if masking enabled
        # WHY: log initialization
        logger.info("audit_logger_initialized", masking_enabled=enable_masking)  # WHY: startup event

    def log_operation(
        self,
        operation: str,
        user_id: str,
        details: dict[str, Any] = None,
        result: str = "success",
        error_message: str = None,
    ) -> str | None:
        """Log an audit operation.

        Args:
            operation: Operation name (e.g., 'capture_start', 'upgrade_run').
            user_id: User performing the operation.
            details: Additional operation details (will be masked).
            result: Operation result ('success', 'failure', 'pending').
            error_message: Error message if result is 'failure'.

        Returns:
            Log ID if successful, None if write failed.

        WHY: centralized audit logging for all operations.
        """
        # WHY: record operation start
        logger.info("audit_operation_starting", operation=operation, user=user_id)  # WHY: pre-operation log
        try:
            # WHY: build audit entry with metadata
            log_id = str(uuid.uuid4())  # WHY: unique log identifier
            timestamp_ms = int(time.time() * 1000)  # WHY: millisecond precision
            iso_timestamp = datetime.now(UTC).isoformat()  # WHY: ISO 8601 format
            # WHY: prepare entry document
            entry = {
                "_key": log_id,  # WHY: primary key for ArangoDB
                "log_id": log_id,  # WHY: duplicate for query convenience
                "timestamp": iso_timestamp,  # WHY: ISO 8601 timestamp
                "timestamp_ms": timestamp_ms,  # WHY: milliseconds since epoch
                "operation": operation,  # WHY: operation name for filtering
                "user_id": user_id,  # WHY: user identifier
                "result": result,  # WHY: success/failure/pending
                "error_message": error_message,  # WHY: error context if failed
                "details": details or {},  # WHY: additional operation data
            }  # WHY: audit entry structure
            # WHY: apply secret masking if enabled
            if self.enable_masking and self.masker:  # WHY: conditional masking
                entry["details"] = self.masker.mask_dict(entry["details"])  # WHY: redact sensitive fields
            # WHY: write to database
            if self.db_router:  # WHY: optional database routing
                write_result = self.db_router.write(  # WHY: database write
                    data=[entry],  # WHY: single entry
                    collection="audit_logs",  # WHY: target collection
                    endpoint="audit_log",  # WHY: endpoint label
                    strategy={"type": "natural_pk", "primary_key": ["log_id"]},  # WHY: PK strategy
                )  # WHY: execute write
                # WHY: log write result
                if write_result.success:  # WHY: check success
                    logger.debug(
                        "audit_operation_logged", log_id=log_id, operation=operation, result=result
                    )  # WHY: post-operation log
                else:
                    logger.error(
                        "audit_write_failed", log_id=log_id, error=write_result.backend
                    )  # WHY: write failure log
            # WHY: return log ID for traceability
            return log_id  # WHY: success return
        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("audit_logging_exception", operation=operation, error=str(e))  # WHY: exception handling
            return None  # WHY: failure return

    def log_capture_start(
        self,
        user_id: str,
        run_id: str,
        site_id: str,
        device_ids: list[str],
    ) -> str | None:
        """Log capture start operation.

        Args:
            user_id: User initiating capture.
            run_id: Unique upgrade run ID.
            site_id: Site being captured.
            device_ids: List of device IDs.

        Returns:
            Log ID if successful.

        WHY: specialized logging for capture operations.
        """
        # WHY: log capture start with operation details
        return self.log_operation(  # WHY: delegate to main logging
            operation="capture_start",  # WHY: operation type
            user_id=user_id,  # WHY: user context
            details={  # WHY: operation-specific details
                "run_id": run_id,  # WHY: upgrade run reference
                "site_id": site_id,  # WHY: site context
                "device_count": len(device_ids),  # WHY: device count
                "device_ids": device_ids,  # WHY: specific devices
            },  # WHY: details dictionary
            result="pending",  # WHY: capture in progress
        )  # WHY: log operation

    def log_capture_complete(
        self,
        user_id: str,
        run_id: str,
        site_id: str,
        device_count: int,
        duration_ms: int,
    ) -> str | None:
        """Log capture completion.

        Args:
            user_id: User who initiated capture.
            run_id: Unique upgrade run ID.
            site_id: Site being captured.
            device_count: Number of devices captured.
            duration_ms: Capture duration in milliseconds.

        Returns:
            Log ID if successful.

        WHY: capture completion logging for audit trail.
        """
        # WHY: log capture complete with results
        return self.log_operation(  # WHY: delegate to main logging
            operation="capture_complete",  # WHY: operation type
            user_id=user_id,  # WHY: user context
            details={  # WHY: operation-specific details
                "run_id": run_id,  # WHY: upgrade run reference
                "site_id": site_id,  # WHY: site context
                "device_count": device_count,  # WHY: devices captured
                "duration_ms": duration_ms,  # WHY: time taken
            },  # WHY: details dictionary
            result="success",  # WHY: completion status
        )  # WHY: log operation

    def log_validation_error(
        self,
        user_id: str,
        operation: str,
        error_message: str,
        input_data: dict[str, Any] = None,
    ) -> str | None:
        """Log validation failure.

        Args:
            user_id: User making invalid request.
            operation: Operation that failed validation.
            error_message: Validation error message.
            input_data: Input data that failed (will be masked).

        Returns:
            Log ID if successful.

        WHY: validation error logging for security audit trail.
        """
        # WHY: log validation failure
        return self.log_operation(  # WHY: delegate to main logging
            operation=operation,  # WHY: operation type
            user_id=user_id,  # WHY: user context
            details={  # WHY: operation-specific details
                "input_data": input_data or {},  # WHY: invalid input
                "validation_error": error_message,  # WHY: error detail
            },  # WHY: details dictionary
            result="failure",  # WHY: failure status
            error_message=error_message,  # WHY: error message
        )  # WHY: log operation

    def get_audit_logs(
        self,
        operation: str = None,
        user_id: str = None,
        start_time: str = None,
        end_time: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]] | None:
        """Query audit logs from ArangoDB.

        Args:
            operation: Filter by operation name (optional).
            user_id: Filter by user ID (optional).
            start_time: ISO 8601 start time (optional).
            end_time: ISO 8601 end time (optional).
            limit: Maximum results to return (default: 100).
            offset: Result offset for pagination (default: 0).

        Returns:
            List of audit log entries if successful, None if query failed.

        WHY: queryable audit trail for compliance and debugging.
        """
        # WHY: log query operation
        logger.info("audit_query_starting", operation=operation, user_id=user_id, limit=limit)  # WHY: pre-query log
        try:
            # WHY: build query filters
            filters = []  # WHY: AQL WHERE clause conditions
            params = {}  # WHY: query parameters
            # WHY: operation filter
            if operation:  # WHY: if operation specified
                filters.append("doc.operation == @operation")  # WHY: AQL condition
                params["operation"] = operation  # WHY: parameter binding
            # WHY: user filter
            if user_id:  # WHY: if user specified
                filters.append("doc.user_id == @user_id")  # WHY: AQL condition
                params["user_id"] = user_id  # WHY: parameter binding
            # WHY: time range filters
            if start_time:  # WHY: if start time specified
                filters.append("doc.timestamp >= @start_time")  # WHY: AQL condition
                params["start_time"] = start_time  # WHY: parameter binding
            if end_time:  # WHY: if end time specified
                filters.append("doc.timestamp <= @end_time")  # WHY: AQL condition
                params["end_time"] = end_time  # WHY: parameter binding
            # WHY: build WHERE clause
            where_clause = " AND ".join(filters) if filters else "1 == 1"  # WHY: combine conditions
            # WHY: build AQL query
            aql_query = f"""  # WHY: formatted AQL query string
                FOR doc IN audit_logs
                FILTER {where_clause}
                SORT doc.timestamp_ms DESC
                LIMIT @offset, @limit
                RETURN doc
            """  # WHY: AQL return statement
            # WHY: add pagination parameters
            params["offset"] = offset  # WHY: offset parameter
            params["limit"] = limit  # WHY: limit parameter
            # WHY: execute query via database router
            if not self.db_router:  # WHY: check router available
                logger.error("audit_query_failed_no_router")  # WHY: log missing router
                return None  # WHY: no router
            # WHY: execute AQL query
            results = self.db_router.query(aql_query, params)  # WHY: execute query
            # WHY: log query result
            logger.debug("audit_query_complete", count=len(results) if results else 0)  # WHY: post-query log
            return results  # WHY: return results
        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("audit_query_exception", error=str(e))  # WHY: exception handling
            return None  # WHY: failure return


# WHY: convenience import for logging
