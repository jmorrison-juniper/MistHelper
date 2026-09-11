"""JWT authentication routes for upgrade portal.

Implements login and token continuation endpoints per SC-009.
"""

import time  # WHY: timestamp operations

import structlog  # WHY: structured logging
from flask import Blueprint, jsonify, request  # WHY: Flask framework

from upgrade_portal.audit import AuditLogger  # WHY: audit logging
from upgrade_portal.auth import JWTSessionManager  # WHY: session management

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger

# WHY: create blueprint for JWT auth routes
jwt_auth_bp = Blueprint("jwt_auth", __name__, url_prefix="/api/auth")  # WHY: blueprint definition


def create_jwt_auth_routes(app, session_manager: JWTSessionManager, audit_logger: AuditLogger = None):
    """Register JWT authentication routes with Flask app.

    Args:
        app: Flask application instance.
        session_manager: JWTSessionManager instance for token operations.
        audit_logger: AuditLogger instance for logging (optional).

    WHY: factory function for route registration with dependency injection.
    """

    # WHY: register POST endpoint for login
    @jwt_auth_bp.route("/login", methods=["POST"])  # WHY: login endpoint
    def login():
        """Authenticate user and return JWT token.

        Request body:
            {
                'username': str,
                'password': str,
                'org_id': str (optional),
                'site_id': str (optional)
            }

        Response (200):
            {
                'success': true,
                'token': 'eyJ...',
                'expires_at': timestamp,
                'warning_threshold_seconds': 30
            }

        Response (401):
            {
                'error': 'Invalid credentials'
            }

        WHY: RESTful login endpoint returning JWT.
        """
        # WHY: log login attempt
        logger.info("auth_login_attempt", remote_addr=request.remote_addr)  # WHY: pre-login log
        try:
            # WHY: extract request body
            data = request.get_json() or {}  # WHY: parse JSON
            username = data.get("username", "")  # WHY: username field
            password = data.get("password", "")  # WHY: password field
            org_id = data.get("org_id")  # WHY: optional org ID
            site_id = data.get("site_id")  # WHY: optional site ID

            # WHY: validate credentials (simplified for demo)
            # In production, validate against LDAP, database, or external auth service
            if not username or not password:  # WHY: check required fields
                # WHY: missing credentials
                logger.warning("auth_login_missing_credentials")  # WHY: missing creds log
                if audit_logger:  # WHY: if audit enabled
                    audit_logger.log_validation_error(  # WHY: log validation
                        user_id="unknown",  # WHY: unknown user
                        operation="login",  # WHY: operation type
                        error_message="missing_username_or_password",  # WHY: error detail
                        input_data={"username": username},  # WHY: input data
                    )  # WHY: log validation error
                return jsonify({"error": "username and password required"}), 400  # WHY: bad request

            # WHY: validate password (demo: accept any password)
            # Replace with actual auth mechanism
            if len(password) < 4:  # WHY: demo validation
                # WHY: invalid password
                logger.warning("auth_login_invalid_password", username=username)  # WHY: auth failure log
                if audit_logger:  # WHY: if audit enabled
                    audit_logger.log_validation_error(  # WHY: log validation
                        user_id=username,  # WHY: user identifier
                        operation="login",  # WHY: operation type
                        error_message="invalid_password",  # WHY: error detail
                    )  # WHY: log validation error
                return jsonify({"error": "invalid credentials"}), 401  # WHY: unauthorized

            # WHY: create JWT token
            user_id = username  # WHY: use username as user ID
            token = session_manager.create_token(  # WHY: create token
                user_id=user_id,  # WHY: user identifier
                org_id=org_id,  # WHY: org context
                site_id=site_id,  # WHY: site context
            )  # WHY: create JWT

            # WHY: calculate expiry time
            expires_at = int(time.time()) + session_manager.expiry_seconds  # WHY: expiry timestamp

            # WHY: log successful login
            logger.info("auth_login_success", user_id=user_id, org_id=org_id)  # WHY: login success
            if audit_logger:  # WHY: if audit enabled
                audit_logger.log_operation(  # WHY: log operation
                    operation="login_success",  # WHY: operation type
                    user_id=user_id,  # WHY: user identifier
                    details={  # WHY: operation details
                        "org_id": org_id,  # WHY: org context
                        "site_id": site_id,  # WHY: site context
                    },  # WHY: details
                    result="success",  # WHY: success status
                )  # WHY: log operation

            # WHY: return token response
            return (
                jsonify(
                    {  # WHY: success response
                        "success": True,  # WHY: success flag
                        "token": token,  # WHY: JWT token
                        "expires_at": expires_at,  # WHY: expiry timestamp
                        "warning_threshold_seconds": (
                            session_manager.WARNING_THRESHOLD_SECONDS
                        ),  # WHY: warning threshold
                    }
                ),
                200,
            )  # WHY: HTTP 200 OK

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("auth_login_exception", error=str(e))  # WHY: exception log
            if audit_logger:  # WHY: if audit enabled
                audit_logger.log_operation(  # WHY: log operation
                    operation="login_error",  # WHY: operation type
                    user_id=data.get("username", "unknown"),  # WHY: user identifier
                    result="failure",  # WHY: failure status
                    error_message=str(e),  # WHY: error detail
                )  # WHY: log operation
            return jsonify({"error": "login failed"}), 500  # WHY: server error

    # WHY: register POST endpoint for token continuation
    @jwt_auth_bp.route("/continue", methods=["POST"])  # WHY: continue/refresh endpoint
    def continue_session():
        """Refresh an expiring token to continue session.

        Request body:
            {
                'token': 'eyJ...'
            }

        Response (200):
            {
                'success': true,
                'token': 'eyJ...',
                'expires_at': timestamp,
                'warning_threshold_seconds': 30
            }

        Response (401):
            {
                'error': 'Token expired or invalid'
            }

        WHY: continuation endpoint for "continue" button flow.
        """
        # WHY: log continue attempt
        logger.info("auth_continue_attempt")  # WHY: pre-continue log
        try:
            # WHY: extract request body
            data = request.get_json() or {}  # WHY: parse JSON
            token = data.get("token", "")  # WHY: current token

            # WHY: validate token format
            if not token:  # WHY: check token present
                # WHY: missing token
                logger.warning("auth_continue_missing_token")  # WHY: missing token log
                if audit_logger:  # WHY: if audit enabled
                    audit_logger.log_validation_error(  # WHY: log validation
                        user_id="unknown",  # WHY: unknown user
                        operation="continue_session",  # WHY: operation type
                        error_message="missing_token",  # WHY: error detail
                    )  # WHY: log validation error
                return jsonify({"error": "token required"}), 400  # WHY: bad request

            # WHY: refresh token via session manager
            success, new_token, error = session_manager.refresh_token(token)  # WHY: refresh token
            if not success:  # WHY: check refresh success
                # WHY: refresh failed
                logger.warning("auth_continue_failed", error=error)  # WHY: refresh failure log
                if audit_logger:  # WHY: if audit enabled
                    audit_logger.log_operation(  # WHY: log operation
                        operation="continue_session_error",  # WHY: operation type
                        user_id="unknown",  # WHY: unknown user
                        result="failure",  # WHY: failure status
                        error_message=error,  # WHY: error detail
                    )  # WHY: log operation
                return jsonify({"error": f"token refresh failed: {error}"}), 401  # WHY: unauthorized

            # WHY: calculate expiry time
            expires_at = int(time.time()) + session_manager.expiry_seconds  # WHY: expiry timestamp

            # WHY: extract user ID from token for logging
            is_valid, payload, _ = session_manager.validate_token(new_token)  # WHY: validate new token
            user_id = payload.get("user_id") if payload else "unknown"  # WHY: extract user ID

            # WHY: log successful continuation
            logger.info("auth_continue_success", user_id=user_id)  # WHY: continue success
            if audit_logger:  # WHY: if audit enabled
                audit_logger.log_operation(  # WHY: log operation
                    operation="continue_session_success",  # WHY: operation type
                    user_id=user_id,  # WHY: user identifier
                    result="success",  # WHY: success status
                )  # WHY: log operation

            # WHY: return new token response
            return (
                jsonify(
                    {  # WHY: success response
                        "success": True,  # WHY: success flag
                        "token": new_token,  # WHY: new JWT token
                        "expires_at": expires_at,  # WHY: expiry timestamp
                        "warning_threshold_seconds": (
                            session_manager.WARNING_THRESHOLD_SECONDS
                        ),  # WHY: warning threshold
                    }
                ),
                200,
            )  # WHY: HTTP 200 OK

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("auth_continue_exception", error=str(e))  # WHY: exception log
            if audit_logger:  # WHY: if audit enabled
                audit_logger.log_operation(  # WHY: log operation
                    operation="continue_session_exception",  # WHY: operation type
                    user_id="unknown",  # WHY: unknown user
                    result="failure",  # WHY: failure status
                    error_message=str(e),  # WHY: error detail
                )  # WHY: log operation
            return jsonify({"error": "continue session failed"}), 500  # WHY: server error

    # WHY: register routes with app
    app.register_blueprint(jwt_auth_bp)  # WHY: blueprint registration
