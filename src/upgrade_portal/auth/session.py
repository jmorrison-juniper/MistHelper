"""JWT-based session management for upgrade portal.

Implements stateless sessions with 5-minute inactivity timeout
and 30-second expiry warnings per SC-009.
"""

import jwt  # WHY: JWT token generation and validation
import time  # WHY: timestamp calculations for expiry
from datetime import datetime, timedelta, timezone  # WHY: timestamp handling
from functools import wraps  # WHY: decorator for protected routes
from typing import Any, Dict, Optional, Tuple  # WHY: type hints

import structlog  # WHY: structured logging

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class JWTSessionManager:
    """Manages JWT-based stateless sessions with inactivity timeout."""

    # WHY: configurable constants for token behavior
    DEFAULT_EXPIRY_SECONDS = 300  # WHY: 5 minutes per SC-009
    WARNING_THRESHOLD_SECONDS = 30  # WHY: warn 30 seconds before expiry
    ALGORITHM = 'HS256'  # WHY: HMAC SHA-256 for token signing

    def __init__(self, secret_key: str, expiry_seconds: int = DEFAULT_EXPIRY_SECONDS):
        """Initialize JWT session manager.

        Args:
            secret_key: Secret key for token signing (should be from config).
            expiry_seconds: Token expiry time in seconds (default: 300 = 5 min).

        WHY: configure token behavior and signing key.
        """
        # WHY: store configuration
        self.secret_key = secret_key  # WHY: key for token signing
        self.expiry_seconds = expiry_seconds  # WHY: token lifetime
        # WHY: log initialization
        logger.info("jwt_session_manager_initialized", expiry_seconds=expiry_seconds)  # WHY: startup event

    def create_token(
        self,
        user_id: str,
        org_id: str = None,
        site_id: str = None,
        additional_claims: Dict[str, Any] = None,
    ) -> str:
        """Create a JWT token for a user.

        Args:
            user_id: Unique user identifier.
            org_id: Organization ID (optional).
            site_id: Site ID (optional).
            additional_claims: Additional JWT claims to include.

        Returns:
            Signed JWT token string.

        WHY: create tokens with user context and metadata.
        """
        # WHY: log token creation
        logger.info("jwt_token_creating", user_id=user_id)  # WHY: pre-creation log
        try:
            # WHY: calculate expiry timestamp
            now = datetime.now(timezone.utc)  # WHY: current time in UTC
            expiry_time = now + timedelta(seconds=self.expiry_seconds)  # WHY: token expiry
            # WHY: build token payload
            payload = {  # WHY: JWT claims
                'user_id': user_id,  # WHY: user identifier
                'issued_at': int(now.timestamp()),  # WHY: token issued time
                'expires_at': int(expiry_time.timestamp()),  # WHY: token expiry time
                'iat': int(now.timestamp()),  # WHY: standard JWT issued-at claim
                'exp': int(expiry_time.timestamp()),  # WHY: standard JWT expiry claim
            }  # WHY: payload dictionary
            # WHY: add optional organization/site context
            if org_id:  # WHY: if org provided
                payload['org_id'] = org_id  # WHY: org context
            if site_id:  # WHY: if site provided
                payload['site_id'] = site_id  # WHY: site context
            # WHY: add additional claims
            if additional_claims:  # WHY: if extra claims provided
                payload.update(additional_claims)  # WHY: merge claims
            # WHY: sign token
            token = jwt.encode(  # WHY: create JWT
                payload,  # WHY: payload to encode
                self.secret_key,  # WHY: signing key
                algorithm=self.ALGORITHM,  # WHY: HS256
            )  # WHY: encode operation
            # WHY: log successful creation
            logger.debug("jwt_token_created", user_id=user_id, expires_at=expiry_time.isoformat())  # WHY: post-creation log
            return token  # WHY: return token string

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("jwt_token_creation_failed", user_id=user_id, error=str(e))  # WHY: exception handling
            raise  # WHY: re-raise exception

    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validate a JWT token.

        Args:
            token: JWT token string to validate.

        Returns:
            Tuple of (is_valid, payload, error_message).
            If valid: (True, payload_dict, None)
            If invalid: (False, None, error_reason)

        WHY: token validation with comprehensive error reporting.
        """
        # WHY: log validation attempt
        logger.info("jwt_token_validating")  # WHY: pre-validation log
        try:
            # WHY: decode and verify token
            payload = jwt.decode(  # WHY: verify and decode
                token,  # WHY: token string
                self.secret_key,  # WHY: signing key
                algorithms=[self.ALGORITHM],  # WHY: HS256
            )  # WHY: decode operation
            # WHY: verify expiry
            current_time = int(time.time())  # WHY: current timestamp
            if payload['exp'] < current_time:  # WHY: check expiry
                # WHY: token is expired
                logger.warning("jwt_token_expired", user_id=payload.get('user_id'))  # WHY: expiry log
                return False, None, 'token_expired'  # WHY: expired error
            # WHY: log successful validation
            logger.debug("jwt_token_valid", user_id=payload.get('user_id'))  # WHY: validation success
            return True, payload, None  # WHY: valid token

        except jwt.ExpiredSignatureError:
            # WHY: token signature is expired
            logger.warning("jwt_token_signature_expired")  # WHY: expiry log
            return False, None, 'token_expired'  # WHY: expired error

        except jwt.InvalidSignatureError:
            # WHY: token signature is invalid
            logger.warning("jwt_token_invalid_signature")  # WHY: signature error log
            return False, None, 'invalid_signature'  # WHY: signature error

        except jwt.InvalidTokenError as e:
            # WHY: generic token error
            logger.warning("jwt_token_invalid", error=str(e))  # WHY: error log
            return False, None, 'invalid_token'  # WHY: invalid error

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("jwt_token_validation_exception", error=str(e))  # WHY: exception log
            return False, None, 'validation_error'  # WHY: error return

    def should_warn_expiry(self, token: str) -> bool:
        """Check if token is close to expiry and should trigger warning.

        Args:
            token: JWT token string to check.

        Returns:
            True if token expires within WARNING_THRESHOLD_SECONDS.

        WHY: determine if client should show expiry warning.
        """
        # WHY: validate token first
        is_valid, payload, _ = self.validate_token(token)  # WHY: validate
        if not is_valid or not payload:  # WHY: check validity
            return False  # WHY: invalid token, no warning needed
        # WHY: calculate time until expiry
        current_time = int(time.time())  # WHY: current timestamp
        expiry_time = payload['exp']  # WHY: expiry timestamp
        time_until_expiry = expiry_time - current_time  # WHY: seconds until expiry
        # WHY: return warning threshold check
        should_warn = 0 < time_until_expiry <= self.WARNING_THRESHOLD_SECONDS  # WHY: within threshold
        if should_warn:  # WHY: if warning needed
            logger.debug("jwt_token_expiry_warning", seconds_until_expiry=time_until_expiry)  # WHY: warning log
        return should_warn  # WHY: return result

    def refresh_token(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Refresh an expiring token by extending its expiry time.

        This implements the "continue" flow per SC-009 where users can
        extend their session without re-authenticating.

        Args:
            token: Current JWT token to refresh.

        Returns:
            Tuple of (success, new_token, error_message).
            If successful: (True, new_token_string, None)
            If failed: (False, None, error_reason)

        WHY: allow users to continue session without re-login.
        """
        # WHY: log refresh attempt
        logger.info("jwt_token_refresh_attempt")  # WHY: pre-refresh log
        try:
            # WHY: validate existing token
            is_valid, payload, error = self.validate_token(token)  # WHY: validate
            if not is_valid:  # WHY: check validity
                # WHY: if token is only slightly expired, allow refresh
                if error == 'token_expired':  # WHY: check expiry error
                    try:
                        # WHY: decode without verification to allow grace period
                        payload = jwt.decode(  # WHY: decode
                            token,  # WHY: token string
                            self.secret_key,  # WHY: signing key
                            algorithms=[self.ALGORITHM],  # WHY: HS256
                            options={'verify_exp': False},  # WHY: skip expiry check for grace period
                        )  # WHY: decode without expiry validation
                        # WHY: check grace period (5 minutes after expiry)
                        grace_period = 300  # WHY: 5 minutes grace
                        time_since_expiry = int(time.time()) - payload['exp']  # WHY: time since expiry
                        if time_since_expiry > grace_period:  # WHY: check grace period
                            # WHY: beyond grace period
                            logger.warning("jwt_token_grace_period_expired", seconds_elapsed=time_since_expiry)  # WHY: grace log
                            return False, None, 'token_expired'  # WHY: expired error
                    except Exception as e:
                        # WHY: grace period decode failed
                        logger.warning("jwt_token_grace_period_decode_failed", error=str(e))  # WHY: error log
                        return False, None, error  # WHY: error return
                else:
                    # WHY: other validation error
                    logger.warning("jwt_token_refresh_validation_failed", error=error)  # WHY: error log
                    return False, None, error  # WHY: error return
            # WHY: create new token with same claims
            user_id = payload.get('user_id')  # WHY: extract user ID
            org_id = payload.get('org_id')  # WHY: extract org ID
            site_id = payload.get('site_id')  # WHY: extract site ID
            # WHY: create new token
            new_token = self.create_token(  # WHY: create token
                user_id=user_id,  # WHY: same user
                org_id=org_id,  # WHY: same org
                site_id=site_id,  # WHY: same site
                additional_claims={  # WHY: preserve custom claims
                    k: v for k, v in payload.items()  # WHY: copy existing claims
                    if k not in ['issued_at', 'expires_at', 'iat', 'exp']  # WHY: exclude time claims
                },  # WHY: additional claims
            )  # WHY: create new token
            # WHY: log successful refresh
            logger.info("jwt_token_refreshed", user_id=user_id)  # WHY: refresh success
            return True, new_token, None  # WHY: success return

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("jwt_token_refresh_exception", error=str(e))  # WHY: exception log
            return False, None, 'refresh_error'  # WHY: error return


def require_token(session_manager: JWTSessionManager):
    """Decorator to require valid JWT token on protected routes.

    Args:
        session_manager: JWTSessionManager instance for validation.

    Returns:
        Decorator function for route handlers.

    WHY: reusable decorator for protecting endpoints.
    """
    # WHY: define decorator
    def decorator(f):  # WHY: decorator function
        @wraps(f)  # WHY: preserve original function metadata
        def decorated_function(*args, **kwargs):  # WHY: wrapper function
            # WHY: extract token from Authorization header
            from flask import request, jsonify  # WHY: Flask utilities
            # WHY: get Authorization header
            auth_header = request.headers.get('Authorization', '')  # WHY: extract header
            if not auth_header.startswith('Bearer '):  # WHY: check format
                # WHY: missing or invalid authorization
                logger.warning("jwt_token_missing")  # WHY: missing token log
                return jsonify({'error': 'Missing or invalid Authorization header'}), 401  # WHY: unauthorized
            # WHY: extract token
            token = auth_header[7:]  # WHY: remove 'Bearer ' prefix
            # WHY: validate token
            is_valid, payload, error = session_manager.validate_token(token)  # WHY: validate
            if not is_valid:  # WHY: check validity
                # WHY: invalid or expired token
                logger.warning("jwt_token_validation_failed", error=error)  # WHY: failure log
                return jsonify({'error': f'Invalid token: {error}'}), 401  # WHY: unauthorized
            # WHY: attach payload to request context
            request.user_id = payload.get('user_id')  # WHY: user ID
            request.org_id = payload.get('org_id')  # WHY: org ID
            request.site_id = payload.get('site_id')  # WHY: site ID
            request.jwt_payload = payload  # WHY: full payload
            # WHY: call original function
            return f(*args, **kwargs)  # WHY: invoke handler
        # WHY: return decorated function
        return decorated_function  # WHY: return wrapper
    # WHY: return decorator
    return decorator  # WHY: return decorator
