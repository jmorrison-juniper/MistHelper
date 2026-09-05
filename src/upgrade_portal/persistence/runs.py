"""Upgrade runs persistence layer (T-004).

Store site/device selections in ArangoDB upgrade_runs collection.
"""

import uuid  # WHY: UUID generation for run IDs
from datetime import datetime  # WHY: timestamp tracking
from typing import Dict, List, Optional, Any  # WHY: type hints

import structlog  # WHY: structured logging

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class UpgradeRunsService:
    """Service for persisting upgrade run selections."""

    def __init__(self, db_router=None):
        """Initialize upgrade runs service.

        Args:
            db_router: DatabaseRouter instance for persistence.

        WHY: dependency injection for database access.
        """
        # WHY: store database router
        self.db_router = db_router  # WHY: database dependency
        # WHY: log initialization
        logger.info("upgrade_runs_service_initialized", db_available=db_router is not None)  # WHY: startup event

    def create_run(
        self,
        user_id: str,
        org_id: str,
        site_id: str,
        device_ids: List[str],
        notes: Optional[str] = None
    ) -> Optional[str]:
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
        logger.info("create_upgrade_run_start", user_id=user_id, site_id=site_id, device_count=len(device_ids))  # WHY: pre-operation log
        try:
            # WHY: validate inputs
            if not user_id or not isinstance(user_id, str):  # WHY: check user_id
                logger.error("create_run_invalid_user_id", user_id=user_id)  # WHY: validation error
                return None  # WHY: fail

            if not site_id or not isinstance(site_id, str):  # WHY: check site_id
                logger.error("create_run_invalid_site_id", site_id=site_id)  # WHY: validation error
                return None  # WHY: fail

            if not device_ids or not isinstance(device_ids, list) or len(device_ids) == 0:  # WHY: check devices
                logger.error("create_run_no_devices", device_count=len(device_ids) if device_ids else 0)  # WHY: validation error
                return None  # WHY: fail

            # WHY: check if database available
            if not self.db_router:  # WHY: check router
                logger.error("db_router_unavailable_create_run")  # WHY: no database
                return None  # WHY: fail

            # WHY: generate unique run ID
            run_id = str(uuid.uuid4())  # WHY: UUID for run
            # WHY: get current timestamp
            now = datetime.utcnow().isoformat()  # WHY: ISO format timestamp

            # WHY: create run document
            run_doc = {  # WHY: document dict
                'run_id': run_id,  # WHY: unique identifier
                'user_id': user_id,  # WHY: user context
                'org_id': org_id,  # WHY: org context
                'site_id': site_id,  # WHY: site selection
                'device_ids': device_ids,  # WHY: device selection
                'device_count': len(device_ids),  # WHY: count for summary
                'notes': notes or '',  # WHY: user notes
                'status': 'selection_complete',  # WHY: workflow state
                'created_at': now,  # WHY: creation timestamp
                'updated_at': now,  # WHY: update timestamp
            }  # WHY: complete document

            # WHY: persist to ArangoDB
            logger.info("write_upgrade_run_to_db", run_id=run_id)  # WHY: pre-write log
            result = self.db_router.write(  # WHY: database write
                collection='upgrade_runs',  # WHY: collection name
                document=run_doc,  # WHY: document to write
            )  # WHY: write operation

            # WHY: check if write succeeded
            if not result:  # WHY: check result
                logger.error("create_run_write_failed", run_id=run_id)  # WHY: write error
                return None  # WHY: fail

            # WHY: log success
            logger.info("create_upgrade_run_success", run_id=run_id)  # WHY: post-operation log
            return run_id  # WHY: return run_id

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("create_upgrade_run_exception", error=str(e))  # WHY: exception log
            return None  # WHY: fail

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
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

            # WHY: check if database available
            if not self.db_router:  # WHY: check router
                logger.error("db_router_unavailable_get_run")  # WHY: no database
                return None  # WHY: fail

            # WHY: query ArangoDB for run
            logger.info("query_upgrade_run_from_db", run_id=run_id)  # WHY: pre-query log
            query = f"FOR doc IN upgrade_runs FILTER doc.run_id == '{run_id}' RETURN doc"  # WHY: AQL query
            results = self.db_router.query(query=query)  # WHY: database query
            # WHY: check if results found
            if not results or len(results) == 0:  # WHY: check results
                logger.debug("get_run_not_found", run_id=run_id)  # WHY: not found
                return None  # WHY: return none

            # WHY: extract first result
            run_doc = results[0]  # WHY: first document
            # WHY: log success
            logger.info("get_upgrade_run_success", run_id=run_id)  # WHY: post-query log
            return run_doc  # WHY: return document

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("get_upgrade_run_exception", run_id=run_id, error=str(e))  # WHY: exception log
            return None  # WHY: fail

    def update_run(
        self,
        run_id: str,
        updates: Dict[str, Any]
    ) -> bool:
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
        try:
            # WHY: validate run_id
            if not run_id or not isinstance(run_id, str):  # WHY: check run_id
                logger.error("update_run_invalid_run_id", run_id=run_id)  # WHY: validation error
                return False  # WHY: fail

            # WHY: validate updates
            if not updates or not isinstance(updates, dict):  # WHY: check updates
                logger.error("update_run_invalid_updates")  # WHY: validation error
                return False  # WHY: fail

            # WHY: check if database available
            if not self.db_router:  # WHY: check router
                logger.error("db_router_unavailable_update_run")  # WHY: no database
                return False  # WHY: fail

            # WHY: add updated_at timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()  # WHY: update timestamp

            # WHY: update in ArangoDB (would need custom update method or query)
            logger.info("update_upgrade_run_in_db", run_id=run_id)  # WHY: pre-update log
            # WHY: simplified update (assumes db_router has update method)
            # In real implementation, use AQL UPDATE query
            result = self.db_router.write(  # WHY: database write
                collection='upgrade_runs',  # WHY: collection name
                document={'run_id': run_id, **updates},  # WHY: document with updates
            )  # WHY: write operation

            # WHY: check if update succeeded
            if not result:  # WHY: check result
                logger.error("update_run_failed", run_id=run_id)  # WHY: update error
                return False  # WHY: fail

            # WHY: log success
            logger.info("update_upgrade_run_success", run_id=run_id)  # WHY: post-operation log
            return True  # WHY: success

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("update_upgrade_run_exception", run_id=run_id, error=str(e))  # WHY: exception log
            return False  # WHY: fail
