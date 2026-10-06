"""Upgrade runs persistence layer (T-004).

Store site/device selections in ArangoDB upgrade_runs collection.
"""

import uuid  # WHY: UUID generation for run IDs
from datetime import UTC, datetime  # WHY: timestamp tracking
from typing import Any  # WHY: type hints

import structlog  # WHY: structured logging

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class UpgradeRunsService:
    """Service for persisting upgrade run selections."""

    def __init__(self, db_router=None, document_store=None):
        """Initialize upgrade runs service.

        Args:
            db_router: DatabaseRouter instance for persistence.
            document_store: Request-owned Arango handle for document operations.

        WHY: dependency injection for database access.
        """
        # WHY: store database router
        self.db_router = db_router  # WHY: database dependency
        self.document_store = document_store  # The router does not expose document collection methods.
        # WHY: log initialization
        logger.info("upgrade_runs_service_initialized", db_available=db_router is not None)  # WHY: startup event

    def _validate_create_run_inputs(self, user_id: str, site_id: str, device_ids: list[str]) -> str | None:
        """Validate create_run inputs and log the first failure.

        Args:
            user_id: User ID who initiated the run.
            site_id: Selected site ID.
            device_ids: List of selected device IDs.

        Returns:
            Error event name if invalid, None if all inputs are valid.

        WHY: keeps create_run under the complexity limit by moving
        validation into one place.
        """
        input_error = self._validate_create_values(user_id, site_id, device_ids)  # Validate user selections first.
        if input_error is not None:  # Reject invalid values before checking or writing storage.
            return input_error  # Preserve the first validation error.
        if self.db_router is None:  # The service requires the configured router.
            logger.error("db_router_unavailable_create_run")  # Name the missing database dependency.
            return "no_db_router"  # Refuse before a write.
        if self.document_store is None:  # The run document needs direct, verified persistence.
            logger.error("document_store_unavailable_create_run")  # Name the missing collection handle.
            return "no_document_store"  # Refuse before a write.
        return None  # All input and dependency checks passed.

    @staticmethod
    def _validate_create_values(user_id: str, site_id: str, device_ids: list[str]) -> str | None:
        """Return the first invalid user, site, or device selection."""
        if not user_id or not isinstance(user_id, str):  # Require an operator identity.
            logger.error("create_run_invalid_user_id", user_id=user_id)  # Record the validation failure.
            return "invalid_user_id"  # Stop at the first invalid field.
        if not site_id or not isinstance(site_id, str):  # Require a site selection.
            logger.error("create_run_invalid_site_id", site_id=site_id)  # Record the validation failure.
            return "invalid_site_id"  # Stop at the first invalid field.
        if not device_ids or not isinstance(device_ids, list):  # Require at least one device.
            logger.error("create_run_no_devices", device_count=len(device_ids) if device_ids else 0)  # Record failure.
            return "no_devices"  # Stop before storage access.
        return None  # The user selections are valid.

    def create_run(
        self, user_id: str, org_id: str, site_id: str, device_ids: list[str], notes: str | None = None
    ) -> str | None:
        """Create a new upgrade run with selected devices.

        Args:
            user_id: User ID who initiated the run.
            org_id: Organization ID.
            site_id: Selected site ID.
            device_ids: List of selected device IDs (minimum 1 required).
            notes: Optional user notes for the run.

        Returns:
            Run ID if successful, None if failed.

        WHY: persist selection state to ArangoDB (T-004 requirement).
        """
        # WHY: log operation start
        logger.info(
            "create_upgrade_run_start", user_id=user_id, site_id=site_id, device_count=len(device_ids)
        )  # WHY: pre-operation log
        # WHY: validate inputs before any write
        validation_error = self._validate_create_run_inputs(user_id, site_id, device_ids)  # WHY: input check
        if validation_error:  # WHY: fail fast on invalid input
            return None  # WHY: reject invalid run

        try:
            # WHY: generate unique run ID
            run_id = str(uuid.uuid4())  # WHY: UUID for run
            # WHY: get current timestamp
            now = datetime.now(UTC).isoformat()  # WHY: Store an aware UTC timestamp for database reads.

            # WHY: create run document
            run_doc = {  # WHY: document dict
                "_key": run_id,  # The natural run ID is the Arango document key.
                "run_id": run_id,  # WHY: unique identifier
                "user_id": user_id,  # WHY: user context
                "org_id": org_id,  # WHY: org context
                "site_id": site_id,  # WHY: site selection
                "device_ids": device_ids,  # WHY: device selection
                "device_count": len(device_ids),  # WHY: count for summary
                "notes": notes or "",  # WHY: user notes
                "status": "selection_complete",  # WHY: workflow state
                "created_at": now,  # WHY: creation timestamp
                "updated_at": now,  # WHY: update timestamp
            }  # WHY: complete document

            if self.document_store is None:
                logger.error("document_store_unavailable_create_run", run_id=run_id)
                return None
            logger.info("write_upgrade_run_to_db", run_id=run_id)
            collection = self.document_store.collection("upgrade_runs")
            collection.insert(run_doc)
            stored = collection.get(run_id)
            if not isinstance(stored, dict) or any(stored.get(key) != value for key, value in run_doc.items()):
                logger.error("create_run_write_failed", run_id=run_id)  # WHY: write error
                return None  # WHY: fail

            # WHY: log success
            logger.info("create_upgrade_run_success", run_id=run_id)  # WHY: post-operation log
            return run_id  # WHY: return run_id

        except Exception as error:
            logger.error("create_upgrade_run_exception", error_type=type(error).__name__)
            return None  # WHY: fail

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get upgrade run by ID.

        Args:
            run_id: Run ID to retrieve.

        Returns:
            Run document if found, None otherwise.

        WHY: read endpoint for GET /api/runs/:run_id (T-004).
        """
        # WHY: log operation start
        logger.info("get_upgrade_run_start", run_id=run_id)  # WHY: pre-operation log
        try:
            # WHY: validate run_id
            if not run_id or not isinstance(run_id, str):  # WHY: check run_id
                logger.error("get_run_invalid_run_id", run_id=run_id)  # WHY: validation error
                return None  # WHY: fail

            if self.document_store is None:
                logger.error("document_store_unavailable_get_run")
                return None  # WHY: fail

            logger.info("query_upgrade_run_from_db", run_id=run_id)
            run_doc = self.document_store.collection("upgrade_runs").get(run_id)
            if not isinstance(run_doc, dict) or run_doc.get("run_id") != run_id:
                logger.debug("get_run_not_found", run_id=run_id)  # WHY: not found
                return None  # WHY: return none

            # WHY: log success
            logger.info("get_upgrade_run_success", run_id=run_id)  # WHY: post-query log
            return run_doc  # WHY: return document

        except Exception as error:
            logger.error("get_upgrade_run_exception", run_id=run_id, error_type=type(error).__name__)
            return None  # WHY: fail

    def update_run(self, run_id: str, updates: dict[str, Any]) -> bool:
        """Update upgrade run.

        Args:
            run_id: Run ID to update.
            updates: Dictionary of fields to update.

        Returns:
            True if successful, False otherwise.

        WHY: update endpoint for PATCH /api/runs/:run_id (T-004).
        """
        # WHY: log operation start
        logger.info("update_upgrade_run_start", run_id=run_id)  # WHY: pre-operation log
        if not self._validate_update_inputs(run_id, updates):  # Reject invalid updates before storage access.
            return False  # The validator records the first failure.
        if self.document_store is None:  # Direct collection access is required for read-back.
            logger.error("document_store_unavailable_update_run")  # Name the missing dependency.
            return False  # Do not report an update without durable storage.
        try:
            return self._persist_update(run_id, updates)  # Write and verify the requested fields.
        except Exception as error:
            logger.error("update_upgrade_run_exception", run_id=run_id, error_type=type(error).__name__)
            return False  # WHY: fail

    @staticmethod
    def _validate_update_inputs(run_id: str, updates: dict[str, Any]) -> bool:
        """Validate the run key and the allowed update fields."""
        if not run_id or not isinstance(run_id, str):  # Require a stable document key.
            logger.error("update_run_invalid_run_id", run_id=run_id)  # Record the invalid key.
            return False  # Refuse before collection access.
        if not updates or not isinstance(updates, dict):  # Require a nonempty update.
            logger.error("update_run_invalid_updates")  # Record the invalid update.
            return False  # Refuse before collection access.
        if any(field not in {"notes", "status"} for field in updates):  # Restrict changes to supported fields.
            logger.error("update_run_unsupported_field", run_id=run_id)  # Record the unsupported change.
            return False  # Keep other document fields immutable.
        return True  # The requested update has a supported shape.

    def _persist_update(self, run_id: str, updates: dict[str, Any]) -> bool:
        """Write one supported update and confirm its stored values."""
        collection = self.document_store.collection("upgrade_runs")  # Use the request-owned document handle.
        existing = collection.get(run_id)  # Confirm the run exists before mutation.
        if not isinstance(existing, dict) or existing.get("run_id") != run_id:  # Refuse a missing or mismatched record.
            logger.error("update_run_not_found", run_id=run_id)  # Record the missing run.
            return False  # Do not create a new record through update.
        patch = {**updates, "updated_at": datetime.now(UTC).isoformat()}  # Record the UTC update time.
        logger.info("update_upgrade_run_in_db", run_id=run_id)  # Log before the database write.
        collection.update({"_key": run_id, **patch})  # Use the supported document collection interface.
        stored = collection.get(run_id)  # Read the saved document back.
        if not isinstance(stored, dict) or any(stored.get(key) != value for key, value in patch.items()):
            logger.error("update_run_failed", run_id=run_id)  # Report an unverified update.
            return False  # Do not report success without read-back.
        logger.info("update_upgrade_run_success", run_id=run_id)  # Record the verified result.
        return True  # Every requested field is stored.
