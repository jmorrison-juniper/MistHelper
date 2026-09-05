"""Upgrade runs API routes (T-004, T-005).

Implement GET /api/runs/:run_id and PATCH /api/runs/:run_id with validation.
"""

from flask import Blueprint, request, jsonify  # WHY: Flask routing and request handling
import structlog  # WHY: structured logging

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


def create_runs_routes(runs_service=None, audit_logger=None):
    """Create Flask blueprint for upgrade runs routes.

    Args:
        runs_service: UpgradeRunsService instance.
        audit_logger: AuditLogger instance (optional).

    Returns:
        Flask blueprint for registration.

    WHY: factory function for route creation with dependency injection.
    """
    # WHY: create blueprint
    runs_bp = Blueprint('runs', __name__, url_prefix='/api/runs')  # WHY: blueprint with prefix

    @runs_bp.route('/<run_id>', methods=['GET'])  # WHY: get run route
    def get_run(run_id):
        """Get upgrade run by ID.

        Path parameters:
            - run_id: Run ID to retrieve.

        Returns:
            200 OK with run data; 400/404 on error.

        WHY: endpoint for GET /api/runs/:run_id (T-004).
        """
        # WHY: log request
        logger.info("get_run_request", run_id=run_id)  # WHY: request event
        try:
            # WHY: validate run_id format
            if not run_id or not isinstance(run_id, str) or len(run_id) == 0:  # WHY: check format
                # WHY: bad request
                logger.warning("get_run_invalid_run_id", run_id=run_id)  # WHY: validation failure
                return jsonify({'error': 'run_id is required and must be non-empty'}), 400  # WHY: return error

            # WHY: check if runs service available
            if not runs_service:  # WHY: no service
                # WHY: service unavailable
                logger.error("runs_service_unavailable_get")  # WHY: service error
                return jsonify({'error': 'Runs service not available'}), 503  # WHY: return error

            # WHY: call runs service to get run
            logger.info("runs_service_get_call", run_id=run_id)  # WHY: pre-call log
            run = runs_service.get_run(run_id)  # WHY: service call
            # WHY: check if run found
            if run is None:  # WHY: if not found
                # WHY: not found
                logger.debug("run_not_found", run_id=run_id)  # WHY: not found log
                return jsonify({'error': 'Run not found'}), 404  # WHY: return error

            # WHY: log success
            logger.info("get_run_success", run_id=run_id)  # WHY: post-call log
            # WHY: return run
            return jsonify({'run': run}), 200  # WHY: return result

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("get_run_exception", run_id=run_id, error=str(e))  # WHY: exception log
            return jsonify({'error': 'Internal server error'}), 500  # WHY: return error

    @runs_bp.route('/<run_id>', methods=['PATCH'])  # WHY: update run route
    def update_run(run_id):
        """Update upgrade run.

        Path parameters:
            - run_id: Run ID to update.

        JSON body:
            - notes: Optional notes field to update.

        Returns:
            200 OK on success; 400/404 on error.

        WHY: endpoint for PATCH /api/runs/:run_id (T-004).
        """
        # WHY: log request
        logger.info("update_run_request", run_id=run_id)  # WHY: request event
        try:
            # WHY: validate run_id format
            if not run_id or not isinstance(run_id, str) or len(run_id) == 0:  # WHY: check format
                # WHY: bad request
                logger.warning("update_run_invalid_run_id", run_id=run_id)  # WHY: validation failure
                return jsonify({'error': 'run_id is required and must be non-empty'}), 400  # WHY: return error

            # WHY: parse JSON body
            data = request.get_json() or {}  # WHY: JSON parse
            # WHY: validate that updates are provided
            if not data:  # WHY: check if empty
                # WHY: bad request
                logger.warning("update_run_empty_body")  # WHY: validation failure
                return jsonify({'error': 'Request body must contain update fields'}), 400  # WHY: return error

            # WHY: validate allowed fields (T-005 validation)
            allowed_fields = ['notes', 'status']  # WHY: allowed update fields
            updates = {}  # WHY: validated updates
            for field in allowed_fields:  # WHY: iterate allowed
                if field in data:  # WHY: if present
                    updates[field] = data[field]  # WHY: add to updates

            # WHY: check if runs service available
            if not runs_service:  # WHY: no service
                # WHY: service unavailable
                logger.error("runs_service_unavailable_update")  # WHY: service error
                return jsonify({'error': 'Runs service not available'}), 503  # WHY: return error

            # WHY: call runs service to update run
            logger.info("runs_service_update_call", run_id=run_id)  # WHY: pre-call log
            success = runs_service.update_run(run_id, updates)  # WHY: service call
            # WHY: check if update succeeded
            if not success:  # WHY: if failed
                # WHY: update failed
                logger.error("runs_service_update_failed", run_id=run_id)  # WHY: update error
                return jsonify({'error': 'Failed to update run'}), 400  # WHY: return error

            # WHY: log update to audit trail
            if audit_logger:  # WHY: if audit available
                audit_logger.log_operation(  # WHY: audit log
                    operation='run_updated',  # WHY: operation type
                    details={'run_id': run_id, 'fields': list(updates.keys())},  # WHY: details
                )  # WHY: audit call

            # WHY: log success
            logger.info("update_run_success", run_id=run_id)  # WHY: post-call log
            # WHY: return success
            return jsonify({'message': 'Run updated successfully'}), 200  # WHY: return result

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("update_run_exception", run_id=run_id, error=str(e))  # WHY: exception log
            return jsonify({'error': 'Internal server error'}), 500  # WHY: return error

    @runs_bp.route('', methods=['POST'])  # WHY: create run route
    def create_run():
        """Create a new upgrade run with selected devices.

        JSON body (required):
            - user_id: User ID (non-empty string)
            - org_id: Organization ID (non-empty string)
            - site_id: Selected site ID (non-empty string, UUID format)
            - device_ids: List of device IDs (non-empty array of strings)

        Returns:
            201 Created with run_id; 400 Bad Request on validation error.

        WHY: endpoint for creating upgrade run selection (T-004, T-005).
        """
        # WHY: log request
        logger.info("create_run_request")  # WHY: request event
        try:
            # WHY: parse JSON body
            data = request.get_json() or {}  # WHY: JSON parse
            # WHY: extract and validate user_id
            user_id = data.get('user_id', '').strip()  # WHY: get user_id
            if not user_id:  # WHY: check if empty
                # WHY: validation failure
                logger.warning("create_run_validation_failed", field='user_id')  # WHY: validation log
                # WHY: log to audit if available
                if audit_logger:  # WHY: if audit available
                    audit_logger.log_validation_error(  # WHY: audit log
                        field='user_id',  # WHY: field name
                        reason='User ID is required',  # WHY: reason
                    )  # WHY: audit call
                return jsonify({'error': 'user_id is required'}), 400  # WHY: return error

            # WHY: extract and validate org_id
            org_id = data.get('org_id', '').strip()  # WHY: get org_id
            if not org_id:  # WHY: check if empty
                # WHY: validation failure
                logger.warning("create_run_validation_failed", field='org_id')  # WHY: validation log
                # WHY: log to audit if available
                if audit_logger:  # WHY: if audit available
                    audit_logger.log_validation_error(  # WHY: audit log
                        field='org_id',  # WHY: field name
                        reason='Organization ID is required',  # WHY: reason
                    )  # WHY: audit call
                return jsonify({'error': 'org_id is required'}), 400  # WHY: return error

            # WHY: extract and validate site_id
            site_id = data.get('site_id', '').strip()  # WHY: get site_id
            if not site_id:  # WHY: check if empty
                # WHY: validation failure
                logger.warning("create_run_validation_failed", field='site_id')  # WHY: validation log
                # WHY: log to audit if available
                if audit_logger:  # WHY: if audit available
                    audit_logger.log_validation_error(  # WHY: audit log
                        field='site_id',  # WHY: field name
                        reason='Site ID is required',  # WHY: reason
                    )  # WHY: audit call
                return jsonify({'error': 'site_id is required'}), 400  # WHY: return error

            # WHY: extract and validate device_ids
            device_ids = data.get('device_ids', [])  # WHY: get device_ids
            if not isinstance(device_ids, list) or len(device_ids) == 0:  # WHY: check format and non-empty
                # WHY: validation failure
                logger.warning("create_run_validation_failed", field='device_ids', reason='must be non-empty array')  # WHY: validation log
                # WHY: log to audit if available
                if audit_logger:  # WHY: if audit available
                    audit_logger.log_validation_error(  # WHY: audit log
                        field='device_ids',  # WHY: field name
                        reason='Device IDs must be a non-empty array',  # WHY: reason
                    )  # WHY: audit call
                return jsonify({'error': 'device_ids must be a non-empty array'}), 400  # WHY: return error

            # WHY: validate device_ids are strings
            for device_id in device_ids:  # WHY: iterate devices
                if not isinstance(device_id, str) or not device_id.strip():  # WHY: check type and non-empty
                    # WHY: validation failure
                    logger.warning("create_run_validation_failed", field='device_ids', reason='contains empty device_id')  # WHY: validation log
                    # WHY: log to audit if available
                    if audit_logger:  # WHY: if audit available
                        audit_logger.log_validation_error(  # WHY: audit log
                            field='device_ids',  # WHY: field name
                            reason='Each device ID must be a non-empty string',  # WHY: reason
                        )  # WHY: audit call
                    return jsonify({'error': 'Each device ID must be a non-empty string'}), 400  # WHY: return error

            # WHY: extract optional notes
            notes = data.get('notes', '').strip()  # WHY: get notes
            # WHY: check if runs service available
            if not runs_service:  # WHY: no service
                # WHY: service unavailable
                logger.error("runs_service_unavailable_create")  # WHY: service error
                return jsonify({'error': 'Runs service not available'}), 503  # WHY: return error

            # WHY: call runs service to create run
            logger.info("runs_service_create_call", user_id=user_id, site_id=site_id, device_count=len(device_ids))  # WHY: pre-call log
            run_id = runs_service.create_run(  # WHY: service call
                user_id=user_id,  # WHY: user_id param
                org_id=org_id,  # WHY: org_id param
                site_id=site_id,  # WHY: site_id param
                device_ids=device_ids,  # WHY: device_ids param
                notes=notes,  # WHY: notes param
            )  # WHY: create call

            # WHY: check if creation succeeded
            if not run_id:  # WHY: if failed
                # WHY: creation failed
                logger.error("runs_service_create_failed")  # WHY: create error
                return jsonify({'error': 'Failed to create run'}), 400  # WHY: return error

            # WHY: log creation to audit trail
            if audit_logger:  # WHY: if audit available
                audit_logger.log_capture_start(  # WHY: audit log
                    run_id=run_id,  # WHY: run_id
                    user_id=user_id,  # WHY: user_id
                    org_id=org_id,  # WHY: org_id
                    site_id=site_id,  # WHY: site_id
                    device_count=len(device_ids),  # WHY: device count
                )  # WHY: audit call

            # WHY: log success
            logger.info("create_run_success", run_id=run_id)  # WHY: post-call log
            # WHY: return created run_id with 201 status
            return jsonify({'run_id': run_id}), 201  # WHY: return result

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("create_run_exception", error=str(e))  # WHY: exception log
            return jsonify({'error': 'Internal server error'}), 500  # WHY: return error

    return runs_bp  # WHY: return blueprint
