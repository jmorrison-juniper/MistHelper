"""Audit logging API routes for upgrade portal.

Implements GET /api/audit endpoint for querying audit logs with
optional filtering by operation, user, and time range.
"""

from datetime import datetime, timezone  # WHY: timestamp handling
from typing import Dict  # WHY: type hints

from flask import Blueprint, jsonify, request  # WHY: Flask framework

import structlog  # WHY: structured logging

from upgrade_portal.audit import AuditLogger  # WHY: audit logging service

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger

# WHY: create blueprint for audit routes
audit_bp = Blueprint('audit', __name__, url_prefix='/api')  # WHY: blueprint definition


def create_audit_routes(app, audit_logger: AuditLogger):
    """Register audit routes with Flask app.

    Args:
        app: Flask application instance.
        audit_logger: AuditLogger instance for log queries.

    WHY: factory function for route registration with dependency injection.
    """
    # WHY: register GET endpoint for audit log queries
    @audit_bp.route('/audit', methods=['GET'])  # WHY: query endpoint
    def get_audit_logs():
        """Query audit logs with optional filtering.

        Query Parameters:
            operation (str, optional): Filter by operation name.
            user_id (str, optional): Filter by user ID.
            start_time (str, optional): ISO 8601 start timestamp.
            end_time (str, optional): ISO 8601 end timestamp.
            limit (int, optional): Max results (default: 100, max: 1000).
            offset (int, optional): Result offset for pagination (default: 0).

        Returns:
            JSON response with audit log entries or error message.

        WHY: RESTful endpoint for audit trail queries.
        """
        # WHY: log audit query start
        logger.info("audit_query_received", path=request.path, query_params=dict(request.args))  # WHY: pre-query log
        try:
            # WHY: extract query parameters
            operation = request.args.get('operation')  # WHY: filter by operation
            user_id = request.args.get('user_id')  # WHY: filter by user
            start_time = request.args.get('start_time')  # WHY: start time filter
            end_time = request.args.get('end_time')  # WHY: end time filter
            # WHY: parse and validate pagination parameters
            limit = min(int(request.args.get('limit', 100)), 1000)  # WHY: limit with cap
            offset = max(int(request.args.get('offset', 0)), 0)  # WHY: offset non-negative
            # WHY: validate limit is positive
            if limit <= 0:  # WHY: check limit validity
                logger.warning("audit_query_invalid_limit", limit=limit)  # WHY: log invalid limit
                return jsonify({'error': 'limit must be positive'}), 400  # WHY: return error

            # WHY: call audit logger to query logs
            logs = audit_logger.get_audit_logs(  # WHY: query logs
                operation=operation,  # WHY: operation filter
                user_id=user_id,  # WHY: user filter
                start_time=start_time,  # WHY: time range start
                end_time=end_time,  # WHY: time range end
                limit=limit,  # WHY: result limit
                offset=offset,  # WHY: result offset
            )  # WHY: execute query

            # WHY: handle query failure
            if logs is None:  # WHY: check for failure
                logger.error("audit_query_failed_logger")  # WHY: log query failure
                return jsonify({'error': 'audit log query failed'}), 500  # WHY: return server error

            # WHY: log successful query
            logger.debug("audit_query_success", count=len(logs))  # WHY: post-query log
            # WHY: return query results
            return jsonify({  # WHY: success response
                'success': True,  # WHY: success flag
                'count': len(logs),  # WHY: result count
                'limit': limit,  # WHY: pagination limit
                'offset': offset,  # WHY: pagination offset
                'entries': logs,  # WHY: audit entries
            }), 200  # WHY: HTTP 200 OK

        except ValueError as e:
            # WHY: catch invalid parameter values
            logger.warning("audit_query_invalid_param", error=str(e))  # WHY: log invalid param
            return jsonify({'error': 'invalid parameter'}), 400  # WHY: avoid exposing exception details to the client

        except Exception as e:
            # WHY: catch all other exceptions
            logger.error("audit_query_exception", error=str(e))  # WHY: log exception
            return jsonify({'error': 'internal server error'}), 500  # WHY: return server error

    # WHY: register GET endpoint for operation summary
    @audit_bp.route('/audit/operations', methods=['GET'])  # WHY: operations list endpoint
    def get_audit_operations():
        """Get list of unique operations in audit log.

        Returns:
            JSON response with list of operation names and counts.

        WHY: endpoint to discover available operations for filtering.
        """
        # WHY: log audit operations request
        logger.info("audit_operations_requested")  # WHY: pre-request log
        try:
            # WHY: build AQL query for operation summary
            aql_query = """  # WHY: formatted AQL query string
                FOR doc IN audit_logs
                COLLECT op = doc.operation WITH COUNT INTO cnt
                SORT op
                RETURN {
                    'operation': op,
                    'count': cnt
                }
            """  # WHY: AQL aggregation

            # WHY: execute query via audit logger's database router
            if not audit_logger.db_router:  # WHY: check router available
                logger.error("audit_operations_failed_no_router")  # WHY: log missing router
                return jsonify({'error': 'database unavailable'}), 503  # WHY: return service unavailable

            # WHY: execute AQL query
            results = audit_logger.db_router.query(aql_query, {})  # WHY: execute query
            # WHY: log successful query
            logger.debug("audit_operations_success", count=len(results) if results else 0)  # WHY: post-query log
            # WHY: return operation summary
            return jsonify({  # WHY: success response
                'success': True,  # WHY: success flag
                'operations': results or [],  # WHY: operation list
            }), 200  # WHY: HTTP 200 OK

        except Exception as e:
            # WHY: catch all exceptions
            logger.error("audit_operations_exception", error=str(e))  # WHY: log exception
            return jsonify({'error': 'internal server error'}), 500  # WHY: return server error

    # WHY: register routes with app
    app.register_blueprint(audit_bp)  # WHY: blueprint registration
