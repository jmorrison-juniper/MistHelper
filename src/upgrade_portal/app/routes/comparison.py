"""Comparison results API routes (T-014).

Implement GET /api/runs/:run_id/comparison/results and
POST /api/runs/:run_id/comparison/approve endpoints for delta review and approval.
"""

from datetime import datetime  # WHY: timestamp for approval audit trail
from typing import Any, Union  # WHY: generic type annotation, Union type

import structlog  # WHY: structured logging
from flask import Blueprint, jsonify, request, Response  # WHY: Flask routing, request handling, HTML rendering

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


def create_comparison_routes(
    comparison_service: Any = None, audit_logger: Any = None, db_router: Any = None
) -> Blueprint:
    # WHY: factory function for route creation with dependency injection
    """Create Flask blueprint for comparison results routes.

    Args:
        comparison_service: ComparisonResultService instance.
        audit_logger: AuditLogger instance (optional).
        db_router: DatabaseRouter instance for persistence.

    Returns:
        Flask blueprint for registration.

    WHY: factory function for route creation with dependency injection.
    """
    # WHY: create blueprint
    comparison_bp = Blueprint("comparison", __name__, url_prefix="/api/runs")  # WHY: blueprint with prefix

    @comparison_bp.route("/<run_id>/comparison/results", methods=["GET"])  # WHY: get comparison results route
    def get_comparison_results(run_id: str) -> Union[Response, tuple[Response, int]]:
        # WHY: docstring for endpoint
        """Get comparison results for upgrade run.

        Path parameters:
            - run_id: Run ID to retrieve results for.

        Returns:
            200 OK with DetailedComparisonResult JSON; 400/404 on error.

        WHY: endpoint for GET /api/runs/:run_id/comparison/results (T-014).
        """
        # WHY: log request
        logger.info("get_comparison_results_request", run_id=run_id)  # WHY: request event

        try:
            # WHY: validate run_id format
            if not run_id or not isinstance(run_id, str) or len(run_id) == 0:
                # WHY: bad request
                logger.warning("get_comparison_results_invalid_run_id", run_id=run_id)  # WHY: validation failure
                return (
                    jsonify({"error": "run_id is required and must be non-empty"}),
                    400,
                )  # WHY: return error

            # WHY: check if comparison service available
            if not comparison_service:  # WHY: no service
                # WHY: service unavailable
                logger.error("comparison_service_unavailable_get")  # WHY: service error
                return (
                    jsonify({"error": "Comparison service not available"}),
                    503,
                )  # WHY: return error

            # WHY: check if database router available
            if not db_router:  # WHY: no database access
                # WHY: database unavailable
                logger.error("db_router_unavailable_get")  # WHY: database error
                return (
                    jsonify({"error": "Database service not available"}),
                    503,
                )  # WHY: return error

            # WHY: fetch run from database
            logger.info("db_router_get_run_call", run_id=run_id)  # WHY: pre-call log
            run_doc = db_router.get_run(run_id)  # WHY: database call to fetch run
            # WHY: check if run found
            if run_doc is None:  # WHY: if not found
                # WHY: not found
                logger.debug("run_not_found", run_id=run_id)  # WHY: not found log
                return (
                    jsonify({"error": "Run not found"}),
                    404,
                )  # WHY: return not found

            # WHY: check if comparison result already exists
            logger.info("db_router_get_comparison_call", run_id=run_id)  # WHY: pre-call log
            comparison_doc = db_router.get_comparison(run_id)  # WHY: database call to fetch comparison
            # WHY: check if comparison exists
            if comparison_doc is None:  # WHY: if not found
                # WHY: not found
                logger.debug("comparison_not_found", run_id=run_id)  # WHY: not found log
                return (
                    jsonify({"error": "Comparison results not found"}),
                    404,
                )  # WHY: return not found

            # WHY: convert database document to JSON-serializable dict
            logger.debug("comparison_results_fetched", run_id=run_id)  # WHY: result summary
            result_dict = {
                # WHY: run identifier
                "run_id": comparison_doc.get("run_id", ""),
                # WHY: list of deltas
                "deltas": comparison_doc.get("deltas", []),
                # WHY: summary statistics
                "summary": comparison_doc.get("summary", {}),
                # WHY: flagged items for review
                "flagged_for_review": comparison_doc.get("flagged_for_review", []),
                # WHY: result timestamp
                "timestamp": comparison_doc.get("timestamp", ""),
                # WHY: approval status
                "approved": comparison_doc.get("approved", False),
                # WHY: engineer who approved
                "approved_by": comparison_doc.get("approved_by", ""),
                # WHY: approval timestamp
                "approved_at": comparison_doc.get("approved_at", ""),
            }  # WHY: result dict created

            # WHY: return result
            logger.info("get_comparison_results_success", run_id=run_id)  # WHY: success log
            return jsonify(result_dict), 200  # WHY: return success

        except Exception as e:  # WHY: catch all exceptions
            # WHY: log exception
            logger.error(
                "get_comparison_results_exception",
                run_id=run_id,
                exception_type=type(e).__name__,
            )  # WHY: exception log
            # WHY: log to audit trail
            if audit_logger:  # WHY: check audit logger available
                # WHY: audit the failure
                audit_logger.log_operation(
                    operation="get_comparison_results",
                    user_id="system",
                    run_id=run_id,
                    success=False,
                    details={"error": str(e)},
                )  # WHY: audit operation
            # WHY: return error
            return (
                jsonify({"error": "Failed to retrieve comparison results"}),
                500,
            )  # WHY: return error

    @comparison_bp.route("/<run_id>/comparison/approve", methods=["POST"])  # WHY: approve comparison results route
    def approve_comparison(run_id: str) -> Union[Response, tuple[Response, int]]:
        # WHY: docstring for endpoint
        """Approve comparison results and mark run as complete.

        Path parameters:
            - run_id: Run ID to approve.

        Request body:
            {
                "approved_items": ["delta_1", "delta_2"],
                "rejected_items": ["delta_3"],
                "engineer_notes": "All devices upgraded successfully",
                "approve_all": false
            }

        Returns:
            200 OK with approval confirmation; 400/404 on error.

        WHY: endpoint for POST /api/runs/:run_id/comparison/approve (T-014).
        """
        # WHY: log request
        logger.info("approve_comparison_request", run_id=run_id)  # WHY: request event

        try:
            # WHY: validate run_id format
            if not run_id or not isinstance(run_id, str) or len(run_id) == 0:
                # WHY: bad request
                logger.warning("approve_comparison_invalid_run_id", run_id=run_id)  # WHY: validation failure
                return (
                    jsonify({"error": "run_id is required and must be non-empty"}),
                    400,
                )  # WHY: return error

            # WHY: parse request body
            data = request.get_json()  # WHY: parse JSON request
            # WHY: check if body provided
            if not data:  # WHY: no body
                # WHY: bad request
                logger.warning("approve_comparison_no_body", run_id=run_id)  # WHY: validation failure
                return (
                    jsonify({"error": "Request body required"}),
                    400,
                )  # WHY: return error

            # WHY: extract approval data
            approved_items = data.get("approved_items", [])  # WHY: approved
            rejected_items = data.get("rejected_items", [])  # WHY: rejected
            engineer_notes = data.get("engineer_notes", "")  # WHY: notes
            approve_all = data.get("approve_all", False)  # WHY: approve all flag

            # WHY: validate approval data
            if (
                not isinstance(approved_items, list)
                or not isinstance(rejected_items, list)
                or not isinstance(approve_all, bool)
            ):
                # WHY: bad request
                logger.warning("approve_comparison_invalid_data", run_id=run_id)  # WHY: validation failure
                return (
                    jsonify({"error": "Invalid approval data"}),
                    400,
                )  # WHY: return error

            # WHY: check if comparison service available
            if not comparison_service:  # WHY: no service
                # WHY: service unavailable
                logger.error("comparison_service_unavailable_approve")  # WHY: service error
                return (
                    jsonify({"error": "Comparison service not available"}),
                    503,
                )  # WHY: return error

            # WHY: check if database router available
            if not db_router:  # WHY: no database access
                # WHY: database unavailable
                logger.error("db_router_unavailable_approve")  # WHY: database error
                return (
                    jsonify({"error": "Database service not available"}),
                    503,
                )  # WHY: return error

            # WHY: fetch comparison from database
            logger.info("db_router_get_comparison_for_approval", run_id=run_id)  # WHY: pre-call log
            comparison_doc = db_router.get_comparison(run_id)  # WHY: database call to fetch comparison
            # WHY: check if comparison exists
            if comparison_doc is None:  # WHY: if not found
                # WHY: not found
                logger.debug("comparison_not_found_for_approval", run_id=run_id)  # WHY: not found log
                return (
                    jsonify({"error": "Comparison results not found"}),
                    404,
                )  # WHY: return not found

            # WHY: check if already approved
            if comparison_doc.get("approved"):  # WHY: if already approved
                # WHY: already approved
                logger.warning("comparison_already_approved", run_id=run_id)  # WHY: already approved
                return (
                    jsonify({"error": "Comparison already approved"}),
                    400,
                )  # WHY: return error

            # WHY: get current user from token (would be extracted from JWT middleware)
            user_id = request.headers.get("X-User-ID", "anonymous")  # WHY: extract user from headers

            # WHY: create approval record
            approval_record = {
                # WHY: run identifier
                "run_id": run_id,
                # WHY: approved items list
                "approved_items": approved_items,
                # WHY: rejected items list
                "rejected_items": rejected_items,
                # WHY: engineer notes
                "engineer_notes": engineer_notes,
                # WHY: approve all flag
                "approve_all": approve_all,
                # WHY: approved by user
                "approved_by": user_id,
                # WHY: approval timestamp
                "approved_at": datetime.utcnow().isoformat(),
            }  # WHY: approval record created

            # WHY: update comparison in database
            logger.info("db_router_update_comparison_approval", run_id=run_id)  # WHY: pre-call log
            db_router.update_comparison(
                run_id,
                {
                    "approved": True,
                    "approved_by": user_id,
                    "approved_at": approval_record["approved_at"],
                    "approval_record": approval_record,
                },
            )  # WHY: database call to update comparison

            # WHY: update run status to completed
            logger.info("db_router_update_run_status", run_id=run_id)  # WHY: pre-call log
            db_router.update_run(
                run_id,
                {
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                },
            )  # WHY: database call to update run

            # WHY: log approval to audit trail
            logger.debug("comparison_approval_stored", run_id=run_id, user_id=user_id)  # WHY: result summary
            if audit_logger:  # WHY: check audit logger available
                # WHY: audit the approval
                audit_logger.log_operation(
                    operation="approve_comparison",
                    user_id=user_id,
                    run_id=run_id,
                    success=True,
                    details={
                        "approved_items_count": len(approved_items),
                        "rejected_items_count": len(rejected_items),
                        "approved_all": approve_all,
                    },
                )  # WHY: audit operation

            # WHY: return approval confirmation
            logger.info("approve_comparison_success", run_id=run_id, user_id=user_id)  # WHY: success log
            return (
                jsonify(
                    {
                        "message": "Comparison approved successfully",
                        "run_id": run_id,
                        "approved_at": approval_record["approved_at"],
                    }
                ),
                200,
            )  # WHY: return success

        except Exception as e:  # WHY: catch all exceptions
            # WHY: log exception
            logger.error(
                "approve_comparison_exception",
                run_id=run_id,
                exception_type=type(e).__name__,
            )  # WHY: exception log
            # WHY: log to audit trail
            if audit_logger:  # WHY: check audit logger available
                # WHY: audit the failure
                audit_logger.log_operation(
                    operation="approve_comparison",
                    user_id="system",
                    run_id=run_id,
                    success=False,
                    details={"error": str(e)},
                )  # WHY: audit operation
            # WHY: return error
            return (
                jsonify({"error": "Failed to approve comparison"}),
                500,
            )  # WHY: return error

    # WHY: return blueprint
    return comparison_bp  # WHY: return configured blueprint
