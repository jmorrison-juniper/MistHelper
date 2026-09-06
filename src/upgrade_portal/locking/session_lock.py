"""Session locking service using Redis (T-015).

Implement per-user per-site upgrade session locking to prevent concurrent upgrades
on same site. Use Redis key format: upgrade_lock:{user_id}:{site_id}.
"""

from dataclasses import dataclass  # WHY: immutable result data structure
from datetime import datetime  # WHY: lock timestamp calculation

import redis  # WHY: Redis client for distributed locking
import structlog  # WHY: structured logging for action tracking

# WHY: module-scoped logger instance
logger = structlog.get_logger(__name__)  # WHY: structured logger


@dataclass  # WHY: immutable result data structure for lock operations
class LockResult:
    """Lock acquisition/release result."""

    acquired: bool  # WHY: whether lock was successfully acquired
    reason: str | None = None  # WHY: reason if lock was not acquired
    owner_id: str | None = None  # WHY: user ID holding the lock (if not acquired)
    acquired_at: datetime | None = None  # WHY: timestamp when lock was acquired
    lock_token: str | None = None  # WHY: unique token for lock release/extend


class SessionLockManager:
    """Session locking manager using Redis backend.

    Enforces one active session per user per site. Acquire lock on upgrade start,
    release on completion. Lock TTL 1 hour. Gracefully degrades if Redis unavailable.

    WHY: ensure only one concurrent upgrade per (user, site) pair.
    """

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        """Initialize the session lock manager with an optional Redis client."""
        # WHY: store Redis client reference
        self.redis_client = redis_client  # WHY: Redis client for key operations
        # WHY: default lock TTL in seconds (1 hour)
        self.default_ttl_seconds = 3600  # WHY: 1 hour lock timeout

    def _get_lock_key(self, user_id: str, site_id: str) -> str:
        # WHY: generate Redis key from user and site identifiers
        """Generate Redis key for user+site lock.

        Args:
            user_id: User identifier.
            site_id: Site identifier.

        Returns:
            Redis key string in format: upgrade_lock:{user_id}:{site_id}.

        WHY: consistent key naming for Redis operations.
        """
        # WHY: format key with user and site to scope lock per (user, site) pair
        lock_key = f"upgrade_lock:{user_id}:{site_id}"  # WHY: Redis key format
        # WHY: return formatted key
        return lock_key

    def _generate_lock_token(self, user_id: str) -> str:
        # WHY: generate unique token for lock verification
        """Generate unique lock token for verification during release/extend.

        Args:
            user_id: User identifier.

        Returns:
            Unique token string combining user ID and timestamp.

        WHY: token allows verification that correct holder releases lock.
        """
        # WHY: get current timestamp for uniqueness
        timestamp = datetime.utcnow().isoformat()  # WHY: ISO format timestamp
        # WHY: combine user ID with timestamp to create unique token
        token = f"{user_id}#{timestamp}"  # WHY: token format for verification
        # WHY: return generated token
        return token

    def acquire_lock(self, user_id: str, site_id: str, timeout: int = 3600) -> LockResult:
        # WHY: attempt to acquire lock for user+site pair
        """Acquire session lock for user on site.

        Args:
            user_id: User identifier.
            site_id: Site identifier.
            timeout: Lock TTL in seconds (default 3600 = 1 hour).

        Returns:
            LockResult with acquired flag, owner_id if lock held by another,
            acquired_at timestamp if successful, lock_token for release.

        WHY: acquire lock to prevent concurrent upgrades on same site.
        """
        try:
            # WHY: generate lock key from user and site
            lock_key = self._get_lock_key(user_id, site_id)  # WHY: Redis key
            # WHY: generate unique token for this lock acquisition
            lock_token = self._generate_lock_token(user_id)  # WHY: verification token

            # WHY: check if Redis client is available
            if self.redis_client is None:  # WHY: check Redis availability
                # WHY: log warning about degraded mode
                logger.warning(
                    "redis_unavailable_graceful_degradation_active",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit degraded mode
                # WHY: allow single-user operation by returning acquired lock
                return LockResult(
                    # WHY: return success even without Redis
                    acquired=True,
                    # WHY: set timestamp to current time
                    acquired_at=datetime.utcnow(),
                    # WHY: return lock token for consistency
                    lock_token=lock_token,
                )  # WHY: graceful degradation result

            # WHY: try to set Redis key if not exists (atomic SET NX operation)
            # WHY: NX flag returns True only if key was NOT already set
            lock_acquired = self.redis_client.set(
                # WHY: Redis key for this lock
                name=lock_key,
                # WHY: store lock token as value (for verification on release)
                value=lock_token,
                # WHY: set expiration time on key
                ex=timeout,
                # WHY: only set if key does not exist
                nx=True,
            )  # WHY: atomic compare-and-set operation

            # WHY: check if lock was successfully acquired
            if lock_acquired:  # WHY: lock acquired successfully
                # WHY: log successful lock acquisition
                logger.info(
                    "session_lock_acquired",
                    user_id=user_id,
                    site_id=site_id,
                    ttl_seconds=timeout,
                )  # WHY: audit lock acquisition
                # WHY: return success result with token
                return LockResult(
                    # WHY: lock was successfully acquired
                    acquired=True,
                    # WHY: set timestamp to current time
                    acquired_at=datetime.utcnow(),
                    # WHY: return lock token for later release/extend
                    lock_token=lock_token,
                )  # WHY: successful acquisition result

            else:  # WHY: lock already held by someone else
                # WHY: fetch existing lock holder's token from Redis
                existing_lock_token = self.redis_client.get(
                    # WHY: get value of lock key to identify holder
                    lock_key
                )  # WHY: fetch existing lock value
                # WHY: extract user ID from existing token (format: user_id#timestamp)
                existing_owner_id = None  # WHY: initialize owner_id as None
                # WHY: check if lock value exists
                if existing_lock_token is not None:  # WHY: lock exists
                    # WHY: decode bytes to string if needed
                    existing_lock_str = (
                        existing_lock_token.decode("utf-8")
                        if isinstance(existing_lock_token, bytes)
                        else existing_lock_token
                    )  # WHY: decode
                    # WHY: split token on '#' to extract user_id
                    owner_parts = existing_lock_str.split("#")  # WHY: parse token
                    # WHY: extract first part as owner ID
                    existing_owner_id = owner_parts[0] if owner_parts else None  # WHY: owner

                # WHY: log failed lock acquisition attempt
                logger.info(
                    "session_lock_denied_already_locked",
                    user_id=user_id,
                    site_id=site_id,
                    owner_id=existing_owner_id,
                )  # WHY: audit lock denial

                # WHY: return failure result with owner information
                return LockResult(
                    # WHY: lock was not acquired
                    acquired=False,
                    # WHY: reason for failure (lock held by another)
                    reason="locked_by_user",
                    # WHY: ID of user holding the lock
                    owner_id=existing_owner_id,
                )  # WHY: failure result

        except Exception as exc:  # WHY: catch all exceptions to ensure graceful handling
            # WHY: log exception with context
            logger.exception(
                "session_lock_acquire_exception",
                user_id=user_id,
                site_id=site_id,
                error=str(exc),
            )  # WHY: audit error state
            # WHY: return failure result due to exception
            return LockResult(
                # WHY: lock acquisition failed
                acquired=False,
                # WHY: reason for failure (exception occurred)
                reason="exception_during_acquire",
            )  # WHY: exception result

    def release_lock(self, user_id: str, site_id: str, lock_token: str) -> bool:
        # WHY: release session lock after upgrade completes or user abandons session
        """Release session lock for user on site.

        Args:
            user_id: User identifier.
            site_id: Site identifier.
            lock_token: Lock token from acquisition (must match to release).

        Returns:
            True if lock was released, False if token does not match or error.

        WHY: release lock to allow other users to start upgrades on same site.
        """
        try:
            # WHY: generate lock key from user and site
            lock_key = self._get_lock_key(user_id, site_id)  # WHY: Redis key

            # WHY: check if Redis client is available
            if self.redis_client is None:  # WHY: check Redis availability
                # WHY: log warning about degraded mode
                logger.warning(
                    "redis_unavailable_graceful_release_allowed",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit degraded mode
                # WHY: allow release without verification in degraded mode
                return True  # WHY: return success

            # WHY: fetch current lock value from Redis to verify token
            current_lock_token = self.redis_client.get(
                # WHY: get value of lock key to verify it matches
                lock_key
            )  # WHY: fetch lock value

            # WHY: check if lock exists and verify token matches
            if current_lock_token is None:  # WHY: lock does not exist
                # WHY: log warning - trying to release non-existent lock
                logger.warning(
                    "session_lock_release_not_found",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit missing lock
                # WHY: return failure - lock not found
                return False  # WHY: failure result

            # WHY: decode lock token from Redis bytes format
            current_lock_str = (
                current_lock_token.decode("utf-8") if isinstance(current_lock_token, bytes) else current_lock_token
            )  # WHY: decode bytes

            # WHY: verify provided token matches current lock token
            if current_lock_str != lock_token:  # WHY: token mismatch (lock stolen)
                # WHY: log warning - token mismatch indicates lock was stolen
                logger.warning(
                    "session_lock_release_token_mismatch",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit token mismatch
                # WHY: return failure - token does not match
                return False  # WHY: failure result

            # WHY: token matches - safe to delete the lock key
            # WHY: delete Redis key to release the lock
            self.redis_client.delete(lock_key)  # WHY: delete key to release

            # WHY: log successful lock release
            logger.info(
                "session_lock_released",
                user_id=user_id,
                site_id=site_id,
            )  # WHY: audit lock release
            # WHY: return success - lock released
            return True  # WHY: success result

        except Exception as exc:  # WHY: catch all exceptions to ensure graceful handling
            # WHY: log exception with context
            logger.exception(
                "session_lock_release_exception",
                user_id=user_id,
                site_id=site_id,
                error=str(exc),
            )  # WHY: audit error state
            # WHY: return failure - exception occurred
            return False  # WHY: failure result

    def extend_lock(self, user_id: str, site_id: str, lock_token: str) -> bool:
        # WHY: extend lock expiration time if session continues during long upgrade
        """Extend session lock expiration time.

        Args:
            user_id: User identifier.
            site_id: Site identifier.
            lock_token: Lock token from acquisition (must match to extend).

        Returns:
            True if lock TTL was extended, False if token does not match or error.

        WHY: extend lock TTL during long-running upgrades to prevent expiry.
        """
        try:
            # WHY: generate lock key from user and site
            lock_key = self._get_lock_key(user_id, site_id)  # WHY: Redis key

            # WHY: check if Redis client is available
            if self.redis_client is None:  # WHY: check Redis availability
                # WHY: log warning about degraded mode
                logger.warning(
                    "redis_unavailable_graceful_extend_allowed",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit degraded mode
                # WHY: allow extend without verification in degraded mode
                return True  # WHY: return success

            # WHY: fetch current lock value to verify token
            current_lock_token = self.redis_client.get(
                # WHY: get value of lock key to verify it matches
                lock_key
            )  # WHY: fetch lock value

            # WHY: check if lock exists
            if current_lock_token is None:  # WHY: lock does not exist
                # WHY: log warning - trying to extend non-existent lock
                logger.warning(
                    "session_lock_extend_not_found",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit missing lock
                # WHY: return failure - lock not found
                return False  # WHY: failure result

            # WHY: decode lock token from Redis bytes format
            current_lock_str = (
                current_lock_token.decode("utf-8") if isinstance(current_lock_token, bytes) else current_lock_token
            )  # WHY: decode bytes

            # WHY: verify provided token matches current lock token
            if current_lock_str != lock_token:  # WHY: token mismatch (lock stolen)
                # WHY: log warning - token mismatch indicates lock was stolen
                logger.warning(
                    "session_lock_extend_token_mismatch",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit token mismatch
                # WHY: return failure - token does not match
                return False  # WHY: failure result

            # WHY: token matches - safe to extend TTL
            # WHY: extend key expiration by resetting it with new TTL
            self.redis_client.expire(
                # WHY: key to extend
                name=lock_key,
                # WHY: new expiration time in seconds (1 hour from now)
                time=self.default_ttl_seconds,
            )  # WHY: set new expiration

            # WHY: log successful lock extension
            logger.info(
                "session_lock_extended",
                user_id=user_id,
                site_id=site_id,
                new_ttl_seconds=self.default_ttl_seconds,
            )  # WHY: audit lock extension
            # WHY: return success - lock TTL extended
            return True  # WHY: success result

        except Exception as exc:  # WHY: catch all exceptions to ensure graceful handling
            # WHY: log exception with context
            logger.exception(
                "session_lock_extend_exception",
                user_id=user_id,
                site_id=site_id,
                error=str(exc),
            )  # WHY: audit error state
            # WHY: return failure - exception occurred
            return False  # WHY: failure result

    def check_lock(self, user_id: str, site_id: str) -> bool:
        # WHY: check if lock exists for user+site pair without acquiring
        """Check if lock exists for user on site.

        Args:
            user_id: User identifier.
            site_id: Site identifier.

        Returns:
            True if lock exists (held by some user), False otherwise.

        WHY: check lock status before attempting operations.
        """
        try:
            # WHY: generate lock key from user and site
            lock_key = self._get_lock_key(user_id, site_id)  # WHY: Redis key

            # WHY: check if Redis client is available
            if self.redis_client is None:  # WHY: check Redis availability
                # WHY: log warning about degraded mode
                logger.debug(
                    "redis_unavailable_graceful_check_allowed",
                    user_id=user_id,
                    site_id=site_id,
                )  # WHY: audit degraded mode
                # WHY: return no lock in degraded mode (allow operation)
                return False  # WHY: return no lock exists

            # WHY: check if key exists in Redis using EXISTS command
            lock_exists = self.redis_client.exists(
                # WHY: check if key exists
                lock_key
            )  # WHY: EXISTS returns 0 or 1

            # WHY: convert EXISTS result (0 or 1) to boolean
            return lock_exists == 1  # WHY: return boolean lock status

        except Exception as exc:  # WHY: catch all exceptions to ensure graceful handling
            # WHY: log exception with context
            logger.exception(
                "session_lock_check_exception",
                user_id=user_id,
                site_id=site_id,
                error=str(exc),
            )  # WHY: audit error state
            # WHY: return default (no lock) on exception
            return False  # WHY: default to no lock on error
