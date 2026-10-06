"""Comparison results API routes (T-014).

Implement GET /api/runs/:run_id/comparison/results and
POST /api/runs/:run_id/comparison/approve endpoints for delta review and approval.
"""

from collections.abc import Mapping  # Read stored ArangoDB rows without assuming a concrete mapping type.
from datetime import UTC, datetime  # WHY: timestamp for approval audit trail
from typing import Any  # WHY: generic type annotation, Union type

import structlog  # WHY: structured logging
from flask import (  # WHY: Flask routing and request handling.
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
)

from src.interfaces.portals.upgrade_portal.app.wiring import (
    PortalAuthenticationError,
    PortalDependencyError,
    request_dependencies,
)  # Resolve only after the signed-in route guard runs.
from src.interfaces.portals.upgrade_portal.runtime import identity  # The operator record owns route authorization.

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


def _comparison_dependencies(
    comparison_service: Any,
    audit_logger: Any,
    document_store: Any,
) -> tuple[Any, Any, Any, Any]:
    """Resolve explicit test values or the authenticated request graph."""
    service = comparison_service or current_app.config.get("COMPARISON_SERVICE")
    audit = audit_logger or current_app.config.get("AUDIT_LOGGER")
    database = document_store or current_app.config.get("DOCUMENT_STORE")
    if service is None or database is None:
        dependencies = request_dependencies()
        service = service or dependencies.services.comparison
        audit = audit or dependencies.resources.audit_logger
        database = database or dependencies.resources.database
    operator = identity.current_session()
    if operator is None:
        from src.interfaces.portals.upgrade_portal.app.wiring import PortalDependencyError

        raise PortalDependencyError("The operator session is unavailable.")
    return service, audit, database, operator


def _latest_comparison(database: Any, run_id: str) -> dict[str, Any] | None:
    """Read the latest stored comparison with a bound run identifier."""
    query = "FOR doc IN comparisons FILTER doc.run_id == @run_id " "SORT doc.timestamp DESC LIMIT 1 RETURN doc"
    rows = list(database.aql.execute(query, bind_vars={"run_id": run_id}))
    return dict(rows[0]) if rows and isinstance(rows[0], Mapping) else None


def _owned_run(run_document: Mapping[str, Any], operator: Any) -> bool:
    """Refuse a run that does not belong to the authenticated operator."""
    owner = getattr(getattr(operator, "owner", None), "actor_email", "")
    recorded = str(run_document.get("actor_email") or run_document.get("user_id") or "")
    return bool(owner and recorded and owner.casefold() == recorded.casefold())


def _update_and_verify(database: Any, collection_name: str, key: str, changes: dict[str, Any]) -> bool:
    """Write one document patch and prove every changed field by read-back."""
    collection = database.collection(collection_name)
    collection.update({"_key": key, **changes}, merge=True)
    stored = collection.get(key)
    return isinstance(stored, Mapping) and all(stored.get(name) == value for name, value in changes.items())


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
    @identity.require_session  # A comparison result belongs to one signed-in operator.
    def get_comparison_results(run_id: str) -> Response | tuple[Response, int]:
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
        active_audit_logger = audit_logger  # A dependency fault can occur before a request graph exists.
        operator = None  # A stable local prevents error handling from hiding the original fault.

        try:
            active_comparison_service, active_audit_logger, database, operator = _comparison_dependencies(
                comparison_service, audit_logger, db_router
            )  # Resolve the operator and request-owned document store.
            # WHY: validate run_id format
            if not run_id or not isinstance(run_id, str) or len(run_id) == 0:
                # WHY: bad request
                logger.warning("get_comparison_results_invalid_run_id", run_id=run_id)  # WHY: validation failure
                return (
                    jsonify({"error": "run_id is required and must be non-empty"}),
                    400,
                )  # WHY: return error

            # WHY: check if comparison service available
            if not active_comparison_service:  # WHY: no service
                # WHY: service unavailable
                logger.error("comparison_service_unavailable_get")  # WHY: service error
                return (
                    jsonify({"error": "Comparison service not available"}),
                    503,
                )  # WHY: return error

            # WHY: check if database router available
            if database is None:  # WHY: no database access
                # WHY: database unavailable
                logger.error("db_router_unavailable_get")  # WHY: database error
                return (
                    jsonify({"error": "Database service not available"}),
                    503,
                )  # WHY: return error

            # WHY: fetch run from database
            logger.info("document_store_get_run", run_id=run_id)  # WHY: pre-call log
            run_doc = database.collection("upgrade_runs").get(run_id)  # The natural run key owns this read.
            # WHY: check if run found
            if run_doc is None:  # WHY: if not found
                # WHY: not found
                logger.debug("run_not_found", run_id=run_id)  # WHY: not found log
                return (
                    jsonify({"error": "Run not found"}),
                    404,
                )  # WHY: return not found
            if not _owned_run(run_doc, operator):  # A signed-in operator cannot read another operator's run.
                return jsonify({"error": "Run not found"}), 404

            # WHY: check if comparison result already exists
            logger.info("document_store_get_comparison", run_id=run_id)  # WHY: pre-call log
            comparison_doc = _latest_comparison(database, run_id)  # The bound query reads only this run.
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

        except PortalAuthenticationError:
            return jsonify({"error": "Sign in to continue."}), 401
        except PortalDependencyError:
            return jsonify({"error": "Database service not available"}), 503
        except Exception as e:  # WHY: catch all exceptions
            # WHY: log exception
            logger.error(
                "get_comparison_results_exception",
                run_id=run_id,
                exception_type=type(e).__name__,
            )  # WHY: exception log
            # WHY: log to audit trail
            if active_audit_logger:  # WHY: check audit logger available
                # WHY: audit the failure
                active_audit_logger.log_operation(
                    operation="get_comparison_results",
                    user_id=str(getattr(getattr(operator, "owner", None), "actor_email", "")),
                    details={"run_id": run_id, "error_type": type(e).__name__},
                    result="failure",
                )  # WHY: audit operation
            # WHY: return error
            return (
                jsonify({"error": "Failed to retrieve comparison results"}),
                500,
            )  # WHY: return error

    @comparison_bp.route("/<run_id>/comparison/approve", methods=["POST"])  # WHY: approve comparison results route
    @identity.require_session  # Approval changes a stored run for one signed-in operator.
    def approve_comparison(run_id: str) -> Response | tuple[Response, int]:
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
        active_audit_logger = audit_logger  # A dependency fault can occur before a request graph exists.
        operator = None  # A stable local prevents error handling from hiding the original fault.

        try:
            active_comparison_service, active_audit_logger, database, operator = _comparison_dependencies(
                comparison_service, audit_logger, db_router
            )  # Resolve the operator and request-owned document store.
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
            if not active_comparison_service:  # WHY: no service
                # WHY: service unavailable
                logger.error("comparison_service_unavailable_approve")  # WHY: service error
                return (
                    jsonify({"error": "Comparison service not available"}),
                    503,
                )  # WHY: return error

            # WHY: check if database router available
            if database is None:  # WHY: no database access
                # WHY: database unavailable
                logger.error("db_router_unavailable_approve")  # WHY: database error
                return (
                    jsonify({"error": "Database service not available"}),
                    503,
                )  # WHY: return error

            # WHY: fetch comparison from database
            logger.info("document_store_get_comparison_for_approval", run_id=run_id)  # WHY: pre-call log
            run_doc = database.collection("upgrade_runs").get(run_id)  # The run must exist in the same store.
            if run_doc is None or not _owned_run(run_doc, operator):  # Refuse absent and foreign runs alike.
                return jsonify({"error": "Run not found"}), 404
            comparison_doc = _latest_comparison(database, run_id)  # The bound query reads this run's result.
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

            user_id = str(getattr(operator.owner, "actor_email", ""))  # Trust the signed identity, not request text.

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
                "approved_at": datetime.now(UTC).isoformat(),
            }  # WHY: approval record created

            # WHY: update comparison in database
            logger.info("db_router_update_comparison_approval", run_id=run_id)  # WHY: pre-call log
            comparison_key = str(comparison_doc.get("_key", ""))  # The stored key identifies this exact result.
            if not comparison_key or not _update_and_verify(
                database,
                "comparisons",
                comparison_key,
                {
                    "approved": True,
                    "approved_by": user_id,
                    "approved_at": approval_record["approved_at"],
                    "approval_record": approval_record,
                },
            ):  # The portal reports no approval until the store returns every field.
                return jsonify({"error": "Failed to approve comparison"}), 500

            # WHY: update run status to completed
            logger.info("db_router_update_run_status", run_id=run_id)  # WHY: pre-call log
            if not _update_and_verify(
                database,
                "upgrade_runs",
                str(run_doc.get("_key", run_id)),
                {
                    "status": "completed",
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            ):  # A failed run write cannot produce a completion response.
                return jsonify({"error": "Failed to approve comparison"}), 500

            # WHY: log approval to audit trail
            logger.debug("comparison_approval_stored", run_id=run_id, user_id=user_id)  # WHY: result summary
            if active_audit_logger:  # WHY: check audit logger available
                # WHY: audit the approval
                audit_id = active_audit_logger.log_operation(
                    operation="approve_comparison",
                    user_id=user_id,
                    details={
                        "run_id": run_id,
                        "approved_items_count": len(approved_items),
                        "rejected_items_count": len(rejected_items),
                        "approved_all": approve_all,
                    },
                    result="success",
                )  # WHY: audit operation
                if audit_id is None:  # A missing durable audit entry must remain visible.
                    return jsonify({"error": "Failed to approve comparison"}), 500

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

        except PortalAuthenticationError:
            return jsonify({"error": "Sign in to continue."}), 401
        except PortalDependencyError:
            return jsonify({"error": "Database service not available"}), 503
        except Exception as e:  # WHY: catch all exceptions
            # WHY: log exception
            logger.error(
                "approve_comparison_exception",
                run_id=run_id,
                exception_type=type(e).__name__,
            )  # WHY: exception log
            # WHY: log to audit trail
            if active_audit_logger:  # WHY: check audit logger available
                # WHY: audit the failure
                active_audit_logger.log_operation(
                    operation="approve_comparison",
                    user_id=str(getattr(getattr(operator, "owner", None), "actor_email", "")),
                    details={"run_id": run_id, "error_type": type(e).__name__},
                    result="failure",
                )  # WHY: audit operation
            # WHY: return error
            return (
                jsonify({"error": "Failed to approve comparison"}),
                500,
            )  # WHY: return error

    # WHY: return blueprint
    return comparison_bp  # WHY: return configured blueprint


comparison_bp = create_comparison_routes()  # WHY: export the blueprint that the application factory registers
