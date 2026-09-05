"""JWT-based session management for upgrade portal.

Implements stateless sessions with 5-minute inactivity timeout
and 30-second expiry warnings per SC-009.
"""

import time  # WHY: timestamp calculations for expiry
from dataclasses import dataclass  # WHY: immutable data structures
from datetime import (  # WHY: timestamp handling
    UTC,
    datetime,
    timedelta,
)  # WHY: timestamp types
from functools import wraps  # WHY: decorator for protected routes
from typing import Any  # WHY: type hints

import jwt  # WHY: JWT token generation and validation
import structlog  # WHY: structured logging

logger = structlog.get_logger(__name__)  # WHY: module-scoped logger


class JWTSessionManager:
    """Manages JWT-based stateless sessions with inactivity timeout."""

    # WHY: configurable constants for token behavior
    DEFAULT_EXPIRY_SECONDS = 300  # WHY: 5 minutes per SC-009
    WARNING_THRESHOLD_SECONDS = 30  # WHY: warn 30 seconds before expiry
    ALGORITHM = "HS256"  # WHY: HMAC SHA-256 for token signing

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
        additional_claims: dict[str, Any] = None,
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
            now = datetime.now(UTC)  # WHY: current time in UTC
            expiry_time = now + timedelta(seconds=self.expiry_seconds)  # WHY: token expiry
            # WHY: build token payload
            payload = {  # WHY: JWT claims
                "user_id": user_id,  # WHY: user identifier
                "issued_at": int(now.timestamp()),  # WHY: token issued time
                "expires_at": int(expiry_time.timestamp()),  # WHY: token expiry time
                "iat": int(now.timestamp()),  # WHY: standard JWT issued-at claim
                "exp": int(expiry_time.timestamp()),  # WHY: standard JWT expiry claim
            }  # WHY: payload dictionary
            # WHY: add optional organization/site context
            if org_id:  # WHY: if org provided
                payload["org_id"] = org_id  # WHY: org context
            if site_id:  # WHY: if site provided
                payload["site_id"] = site_id  # WHY: site context
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
            logger.debug(
                "jwt_token_created", user_id=user_id, expires_at=expiry_time.isoformat()
            )  # WHY: post-creation log
            return token  # WHY: return token string

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("jwt_token_creation_failed", user_id=user_id, error=str(e))  # WHY: exception handling
            raise  # WHY: re-raise exception

    def validate_token(self, token: str) -> tuple[bool, dict[str, Any] | None, str | None]:
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
            if payload["exp"] < current_time:  # WHY: check expiry
                # WHY: token is expired
                logger.warning("jwt_token_expired", user_id=payload.get("user_id"))  # WHY: expiry log
                return False, None, "token_expired"  # WHY: expired error
            # WHY: log successful validation
            logger.debug("jwt_token_valid", user_id=payload.get("user_id"))  # WHY: validation success
            return True, payload, None  # WHY: valid token

        except jwt.ExpiredSignatureError:
            # WHY: token signature is expired
            logger.warning("jwt_token_signature_expired")  # WHY: expiry log
            return False, None, "token_expired"  # WHY: expired error

        except jwt.InvalidSignatureError:
            # WHY: token signature is invalid
            logger.warning("jwt_token_invalid_signature")  # WHY: signature error log
            return False, None, "invalid_signature"  # WHY: signature error

        except jwt.InvalidTokenError as e:
            # WHY: generic token error
            logger.warning("jwt_token_invalid", error=str(e))  # WHY: error log
            return False, None, "invalid_token"  # WHY: invalid error

        except Exception as e:
            # WHY: catch unexpected exceptions
            logger.error("jwt_token_validation_exception", error=str(e))  # WHY: exception log
            return False, None, "validation_error"  # WHY: error return

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
        expiry_time = payload["exp"]  # WHY: expiry timestamp
        time_until_expiry = expiry_time - current_time  # WHY: seconds until expiry
        # WHY: return warning threshold check
        should_warn = 0 < time_until_expiry <= self.WARNING_THRESHOLD_SECONDS  # WHY: within threshold
        if should_warn:  # WHY: if warning needed
            logger.debug("jwt_token_expiry_warning", seconds_until_expiry=time_until_expiry)  # WHY: warning log
        return should_warn  # WHY: return result

    def refresh_token(self, token: str) -> tuple[bool, str | None, str | None]:
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
                if error == "token_expired":  # WHY: check expiry error
                    try:
                        # WHY: decode without verification to allow grace period
                        payload = jwt.decode(  # WHY: decode
                            token,  # WHY: token string
                            self.secret_key,  # WHY: signing key
                            algorithms=[self.ALGORITHM],  # WHY: HS256
                            options={"verify_exp": False},  # WHY: skip expiry check for grace period
                        )  # WHY: decode without expiry validation
                        # WHY: check grace period (5 minutes after expiry)
                        grace_period = 300  # WHY: 5 minutes grace
                        time_since_expiry = int(time.time()) - payload["exp"]  # WHY: time since expiry
                        if time_since_expiry > grace_period:  # WHY: check grace period
                            # WHY: beyond grace period
                            logger.warning(
                                "jwt_token_grace_period_expired", seconds_elapsed=time_since_expiry
                            )  # WHY: grace log
                            return False, None, "token_expired"  # WHY: expired error
                    except Exception as e:
                        # WHY: grace period decode failed
                        logger.warning("jwt_token_grace_period_decode_failed", error=str(e))  # WHY: error log
                        return False, None, error  # WHY: error return
                else:
                    # WHY: other validation error
                    logger.warning("jwt_token_refresh_validation_failed", error=error)  # WHY: error log
                    return False, None, error  # WHY: error return
            # WHY: create new token with same claims
            user_id = payload.get("user_id")  # WHY: extract user ID
            org_id = payload.get("org_id")  # WHY: extract org ID
            site_id = payload.get("site_id")  # WHY: extract site ID
            # WHY: create new token
            new_token = self.create_token(  # WHY: create token
                user_id=user_id,  # WHY: same user
                org_id=org_id,  # WHY: same org
                site_id=site_id,  # WHY: same site
                additional_claims={  # WHY: preserve custom claims
                    k: v
                    for k, v in payload.items()  # WHY: copy existing claims
                    if k not in ["issued_at", "expires_at", "iat", "exp"]  # WHY: exclude time claims
                },  # WHY: additional claims
            )  # WHY: create new token
            # WHY: log successful refresh
            logger.info("jwt_token_refreshed", user_id=user_id)  # WHY: refresh success
            return True, new_token, None  # WHY: success return

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error("jwt_token_refresh_exception", error=str(e))  # WHY: exception log
            return False, None, "refresh_error"  # WHY: error return


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
            from flask import jsonify, request  # WHY: Flask utilities

            # WHY: get Authorization header
            auth_header = request.headers.get("Authorization", "")  # WHY: extract header
            if not auth_header.startswith("Bearer "):  # WHY: check format
                # WHY: missing or invalid authorization
                logger.warning("jwt_token_missing")  # WHY: missing token log
                return jsonify({"error": "Missing or invalid Authorization header"}), 401  # WHY: unauthorized
            # WHY: extract token
            token = auth_header[7:]  # WHY: remove 'Bearer ' prefix
            # WHY: validate token
            is_valid, payload, error = session_manager.validate_token(token)  # WHY: validate
            if not is_valid:  # WHY: check validity
                # WHY: invalid or expired token
                logger.warning("jwt_token_validation_failed", error=error)  # WHY: failure log
                return jsonify({"error": f"Invalid token: {error}"}), 401  # WHY: unauthorized
            # WHY: attach payload to request context
            request.user_id = payload.get("user_id")  # WHY: user ID
            request.org_id = payload.get("org_id")  # WHY: org ID
            request.site_id = payload.get("site_id")  # WHY: site ID
            request.jwt_payload = payload  # WHY: full payload
            # WHY: call original function
            return f(*args, **kwargs)  # WHY: invoke handler

        # WHY: return decorated function
        return decorated_function  # WHY: return wrapper

    # WHY: return decorator
    return decorator  # WHY: return decorator


@dataclass  # WHY: immutable pause state for serialization
class PauseState:
    """Pause state for session timeout handling."""

    # WHY: upgrade run identifier
    run_id: str  # WHY: run ID
    # WHY: timestamp when session was paused
    pause_timestamp: datetime  # WHY: pause time
    # WHY: user who initiated the pause
    paused_by_user: str  # WHY: user ID
    # WHY: current phase of upgrade
    current_phase: str  # WHY: phase name
    # WHY: total number of devices to upgrade
    device_count: int  # WHY: device total
    # WHY: number of devices already upgraded
    completed_count: int  # WHY: completed count
    # WHY: index of device currently being upgraded
    current_device_id: str | None = None  # WHY: current device
    # WHY: index of next device to upgrade
    next_device_index: int = 0  # WHY: next device index
    # WHY: list of device IDs that failed upgrade
    failed_devices: list[str] | None = None  # WHY: failed device list
    # WHY: additional upgrade service state (serialized)
    service_state: dict[str, Any] | None = None  # WHY: service state


@dataclass  # WHY: immutable resume result for response
class ResumeResult:
    """Resume session result."""

    # WHY: whether resume was successful
    resumed: bool  # WHY: success flag
    # WHY: reason if resume failed
    reason: str | None = None  # WHY: failure reason
    # WHY: device index to resume from
    from_device: int | None = None  # WHY: resume position
    # WHY: total device count for context
    device_count: int | None = None  # WHY: device total
    # WHY: current upgrade phase
    current_phase: str | None = None  # WHY: phase name


class PauseResumeManager:
    """Manages pause/resume for upgrade sessions during timeout.

    Implements FR-014 (24 hour pause limit) and SC-010 (pause/resume flow).
    Captures upgrade progress state to ArangoDB and restores on resume.
    """

    # WHY: maximum pause duration per FR-014
    MAX_PAUSE_HOURS = 24  # WHY: 24 hour limit

    def __init__(self, db_router: Any = None) -> None:  # WHY: ArangoDB dependency injection
        """Initialize pause/resume manager.

        Args:
            db_router: DatabaseRouter for ArangoDB persistence.

        WHY: dependency injection for database access.
        """
        # WHY: store database router reference
        self.db_router = db_router  # WHY: database dependency

    def pause_session(self, run_id: str) -> PauseState:
        """Pause upgrade session and capture current progress state.

        Stores upgrade progress to ArangoDB upgrade_runs.pause_state field
        to enable resuming after token expiry or inactivity timeout.

        Args:
            run_id: Upgrade run identifier to pause.

        Returns:
            PauseState object with captured progress state.

        WHY: capture progress for resume and audit trail.
        """
        # WHY: log pause attempt
        logger.info("upgrade_session_pause_start", run_id=run_id)  # WHY: start log
        try:
            # WHY: fetch current upgrade run from database
            upgrade_run = self.db_router.read(  # WHY: read from database
                "upgrade_runs",  # WHY: collection name
                run_id,  # WHY: document ID
            )  # WHY: fetch operation
            # WHY: verify run exists
            if not upgrade_run:  # WHY: check existence
                # WHY: run not found
                logger.error("upgrade_run_not_found_for_pause", run_id=run_id)  # WHY: error log
                raise ValueError(f"Upgrade run {run_id} not found")  # WHY: raise error

            # WHY: create pause state from current run status
            pause_state = PauseState(  # WHY: construct pause state
                run_id=run_id,  # WHY: run identifier
                pause_timestamp=datetime.now(UTC),  # WHY: current time
                paused_by_user=upgrade_run.get("initiated_by", "unknown"),  # WHY: user context
                current_phase=upgrade_run.get("phase", "idle"),  # WHY: phase
                device_count=len(upgrade_run.get("device_statuses", [])),  # WHY: device count
                completed_count=len(
                    [d for d in upgrade_run.get("device_statuses", []) if d.get("status") == "completed"]
                ),  # WHY: completed devices
                current_device_id=upgrade_run.get("current_device_id"),  # WHY: active device
                next_device_index=upgrade_run.get("next_device_index", 0),  # WHY: next device
                failed_devices=upgrade_run.get("failed_devices", []),  # WHY: failed list
                service_state={  # WHY: upgrade service state snapshot
                    "strategy": upgrade_run.get("upgrade_strategy"),  # WHY: strategy
                    "retry_count": upgrade_run.get("retry_count", 0),  # WHY: retry count
                    "start_time": upgrade_run.get("start_time"),  # WHY: start time
                    "last_poll_time": upgrade_run.get("last_poll_time"),  # WHY: poll time
                },  # WHY: service state dict
            )  # WHY: pause state creation

            # WHY: store pause state to database
            update_data = {"pause_state": pause_state.__dict__}  # WHY: serialize state
            # WHY: update document with pause state
            self.db_router.update(  # WHY: update database
                "upgrade_runs",  # WHY: collection name
                run_id,  # WHY: document ID
                update_data,  # WHY: update dict
            )  # WHY: update operation
            # WHY: log successful pause
            logger.info(
                "upgrade_session_paused",
                run_id=run_id,
                device_count=pause_state.device_count,
                completed_count=pause_state.completed_count,
            )  # WHY: success log
            return pause_state  # WHY: return pause state

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error(
                "upgrade_session_pause_failed",
                run_id=run_id,
                error=str(e),
            )  # WHY: exception log
            raise  # WHY: re-raise exception

    def resume_session(self, run_id: str, new_token: str) -> ResumeResult:
        """Resume paused upgrade session from captured state.

        Fetches pause_state from ArangoDB and restores upgrade service state.
        Verifies pause is within 24 hour limit (FR-014). Recalculates device
        index and phase from captured state.

        Args:
            run_id: Upgrade run identifier to resume.
            new_token: New JWT token after session timeout.

        Returns:
            ResumeResult with resume status and position.

        WHY: restore progress and allow user to continue without losing state.
        """
        # WHY: log resume attempt
        logger.info("upgrade_session_resume_start", run_id=run_id)  # WHY: start log
        try:
            # WHY: fetch upgrade run with pause state
            upgrade_run = self.db_router.read(  # WHY: read from database
                "upgrade_runs",  # WHY: collection name
                run_id,  # WHY: document ID
            )  # WHY: fetch operation
            # WHY: verify run exists
            if not upgrade_run:  # WHY: check existence
                # WHY: run not found
                logger.error("upgrade_run_not_found_for_resume", run_id=run_id)  # WHY: error log
                return ResumeResult(  # WHY: return failure
                    resumed=False,  # WHY: failure flag
                    reason="run_not_found",  # WHY: reason
                )  # WHY: return result

            # WHY: extract pause state from database
            pause_state_dict = upgrade_run.get("pause_state")  # WHY: get state
            # WHY: verify pause state exists
            if not pause_state_dict:  # WHY: check pause state
                # WHY: no pause state found
                logger.warning("no_pause_state_for_resume", run_id=run_id)  # WHY: warning log
                return ResumeResult(  # WHY: return failure
                    resumed=False,  # WHY: failure flag
                    reason="no_pause_state",  # WHY: reason
                )  # WHY: return result

            # WHY: verify pause is within 24 hour limit (FR-014)
            pause_time_str = pause_state_dict.get("pause_timestamp")  # WHY: get timestamp
            # WHY: parse pause timestamp
            pause_time = datetime.fromisoformat(pause_time_str)  # WHY: parse ISO time
            # WHY: calculate hours since pause
            hours_since_pause = (datetime.now(UTC) - pause_time).total_seconds() / 3600  # WHY: calculate duration
            # WHY: check if within limit
            if hours_since_pause > self.MAX_PAUSE_HOURS:  # WHY: check limit
                # WHY: pause exceeded time limit
                logger.warning(
                    "pause_session_expired",
                    run_id=run_id,
                    hours_since_pause=hours_since_pause,
                )  # WHY: expiry log
                return ResumeResult(  # WHY: return failure
                    resumed=False,  # WHY: failure flag
                    reason="pause_expired",  # WHY: reason
                )  # WHY: return result

            # WHY: restore upgrade service state from captured state
            # WHY: note: service_state reserved for future use (device status restoration)
            # WHY: calculate from_device index
            from_device = pause_state_dict.get("next_device_index", 0)  # WHY: resume point
            # WHY: get device count for context
            device_count = pause_state_dict.get("device_count", 0)  # WHY: device count
            # WHY: get current phase
            current_phase = pause_state_dict.get("current_phase", "resuming")  # WHY: phase

            # WHY: update run document to clear pause state and mark resuming
            update_data = {  # WHY: update dict
                "pause_state": None,  # WHY: clear pause state
                "resumed_at": datetime.now(UTC).isoformat(),  # WHY: resume time
                "last_token": new_token,  # WHY: new token
            }  # WHY: update fields
            # WHY: update database
            self.db_router.update(  # WHY: update operation
                "upgrade_runs",  # WHY: collection name
                run_id,  # WHY: document ID
                update_data,  # WHY: update dict
            )  # WHY: update operation
            # WHY: log successful resume
            logger.info(
                "upgrade_session_resumed",
                run_id=run_id,
                from_device=from_device,
                device_count=device_count,
                hours_since_pause=hours_since_pause,
            )  # WHY: success log
            # WHY: return success result
            return ResumeResult(  # WHY: return result
                resumed=True,  # WHY: success flag
                from_device=from_device,  # WHY: resume position
                device_count=device_count,  # WHY: device count
                current_phase=current_phase,  # WHY: phase name
            )  # WHY: return result

        except Exception as e:
            # WHY: catch and log exceptions
            logger.error(
                "upgrade_session_resume_failed",
                run_id=run_id,
                error=str(e),
            )  # WHY: exception log
            # WHY: return error result
            return ResumeResult(  # WHY: return result
                resumed=False,  # WHY: failure flag
                reason=f"resume_error: {str(e)}",  # WHY: error message
            )  # WHY: return result
