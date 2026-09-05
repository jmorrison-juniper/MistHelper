"""Unit tests for session locking service (T-015).

Test acquire_lock(), release_lock(), extend_lock(), check_lock() with:
- Redis available scenarios
- Redis unavailable (graceful degradation)
- Token mismatch scenarios
- Lock expiry scenarios
"""

from datetime import datetime  # WHY: timestamp comparison
from unittest.mock import Mock  # WHY: mock Redis client

from src.upgrade_portal.locking.session_lock import (
    LockResult,
    SessionLockManager,
)  # WHY: import classes under test


class TestAcquireLockWithRedis:
    # WHY: test acquire_lock with Redis available

    def test_acquire_lock_success(self) -> None:
        # WHY: verify successful lock acquisition when Redis available
        """Acquire lock succeeds when key not already set."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup mock to return True (key not exists, set successful)
        mock_redis.set.return_value = True  # WHY: SET NX returns True

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: acquire lock for user and site
        result = manager.acquire_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock timeout in seconds
            timeout=3600,
        )  # WHY: acquire lock

        # WHY: verify lock was acquired
        assert result.acquired is True  # WHY: verify acquired flag
        # WHY: verify lock token is not None
        assert result.lock_token is not None  # WHY: verify token generated
        # WHY: verify timestamp is set
        assert result.acquired_at is not None  # WHY: verify timestamp set
        # WHY: verify no failure reason
        assert result.reason is None  # WHY: verify no reason for failure
        # WHY: verify Redis SET was called with correct parameters
        mock_redis.set.assert_called_once()  # WHY: verify Redis called

    def test_acquire_lock_already_locked(self) -> None:
        # WHY: verify lock denied when already locked by another user
        """Acquire lock fails when key already exists."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup mock to return False (key already exists)
        mock_redis.set.return_value = False  # WHY: SET NX returns False
        # WHY: setup mock to return existing lock token
        existing_token = "other-user#2026-01-01T00:00:00.000000"  # WHY: existing token
        # WHY: setup GET to return existing token
        mock_redis.get.return_value = existing_token.encode("utf-8")  # WHY: return token

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: acquire lock for user and site
        result = manager.acquire_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
        )  # WHY: acquire lock

        # WHY: verify lock was not acquired
        assert result.acquired is False  # WHY: verify acquired flag is False
        # WHY: verify reason for failure
        assert result.reason == "locked_by_user"  # WHY: verify failure reason
        # WHY: verify owner ID extracted from token
        assert result.owner_id == "other-user"  # WHY: verify owner ID
        # WHY: verify no lock token returned
        assert result.lock_token is None  # WHY: verify no token returned

    def test_acquire_lock_redis_exception(self) -> None:
        # WHY: verify graceful handling of Redis exceptions
        """Acquire lock fails gracefully on Redis exception."""
        # WHY: create mock Redis client that raises exception
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup mock to raise exception on SET
        mock_redis.set.side_effect = Exception("Redis connection failed")  # WHY: raise error

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: acquire lock for user and site
        result = manager.acquire_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
        )  # WHY: acquire lock

        # WHY: verify lock was not acquired
        assert result.acquired is False  # WHY: verify acquired flag is False
        # WHY: verify reason for failure
        assert result.reason == "exception_during_acquire"  # WHY: verify failure reason


class TestAcquireLockWithoutRedis:
    # WHY: test acquire_lock with Redis unavailable (graceful degradation)

    def test_acquire_lock_no_redis_degraded(self) -> None:
        # WHY: verify graceful degradation when Redis unavailable
        """Acquire lock succeeds in degraded mode when Redis unavailable."""
        # WHY: create SessionLockManager without Redis
        manager = SessionLockManager(redis_client=None)  # WHY: manager without Redis

        # WHY: acquire lock for user and site
        result = manager.acquire_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
        )  # WHY: acquire lock

        # WHY: verify lock was acquired in degraded mode
        assert result.acquired is True  # WHY: verify acquired flag
        # WHY: verify lock token is generated
        assert result.lock_token is not None  # WHY: verify token generated
        # WHY: verify timestamp is set
        assert result.acquired_at is not None  # WHY: verify timestamp set


class TestReleaseLockWithRedis:
    # WHY: test release_lock with Redis available

    def test_release_lock_success(self) -> None:
        # WHY: verify successful lock release when token matches
        """Release lock succeeds when token matches."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup lock token for this lock
        lock_token = "user-1#2026-01-01T00:00:00.000000"  # WHY: lock token
        # WHY: setup GET to return current lock token
        mock_redis.get.return_value = lock_token.encode("utf-8")  # WHY: return token

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: release lock for user and site
        result = manager.release_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock token to verify
            lock_token=lock_token,
        )  # WHY: release lock

        # WHY: verify release succeeded
        assert result is True  # WHY: verify success
        # WHY: verify DELETE was called
        mock_redis.delete.assert_called_once()  # WHY: verify delete called

    def test_release_lock_token_mismatch(self) -> None:
        # WHY: verify release fails when token does not match
        """Release lock fails when token does not match."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup existing lock token in Redis
        existing_token = "other-user#2026-01-01T00:00:00.000000"  # WHY: existing token
        # WHY: setup GET to return existing token
        mock_redis.get.return_value = existing_token.encode("utf-8")  # WHY: return token
        # WHY: setup different lock token for release attempt
        wrong_token = "user-1#2026-01-01T00:00:00.000000"  # WHY: wrong token

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: release lock with wrong token
        result = manager.release_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: wrong lock token
            lock_token=wrong_token,
        )  # WHY: release lock

        # WHY: verify release failed
        assert result is False  # WHY: verify failure
        # WHY: verify DELETE was not called
        mock_redis.delete.assert_not_called()  # WHY: verify delete not called

    def test_release_lock_not_found(self) -> None:
        # WHY: verify release fails when lock does not exist
        """Release lock fails when lock not found."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup GET to return None (lock not found)
        mock_redis.get.return_value = None  # WHY: lock not found

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: release lock
        result = manager.release_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock token
            lock_token="some-token",
        )  # WHY: release lock

        # WHY: verify release failed
        assert result is False  # WHY: verify failure


class TestReleaseLockWithoutRedis:
    # WHY: test release_lock with Redis unavailable

    def test_release_lock_no_redis_degraded(self) -> None:
        # WHY: verify graceful degradation when Redis unavailable
        """Release lock succeeds in degraded mode when Redis unavailable."""
        # WHY: create SessionLockManager without Redis
        manager = SessionLockManager(redis_client=None)  # WHY: manager without Redis

        # WHY: release lock
        result = manager.release_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock token
            lock_token="some-token",
        )  # WHY: release lock

        # WHY: verify release succeeded in degraded mode
        assert result is True  # WHY: verify success


class TestExtendLockWithRedis:
    # WHY: test extend_lock with Redis available

    def test_extend_lock_success(self) -> None:
        # WHY: verify successful lock extension when token matches
        """Extend lock succeeds when token matches."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup lock token for this lock
        lock_token = "user-1#2026-01-01T00:00:00.000000"  # WHY: lock token
        # WHY: setup GET to return current lock token
        mock_redis.get.return_value = lock_token.encode("utf-8")  # WHY: return token

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: extend lock for user and site
        result = manager.extend_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock token to verify
            lock_token=lock_token,
        )  # WHY: extend lock

        # WHY: verify extend succeeded
        assert result is True  # WHY: verify success
        # WHY: verify EXPIRE was called
        mock_redis.expire.assert_called_once()  # WHY: verify expire called

    def test_extend_lock_token_mismatch(self) -> None:
        # WHY: verify extend fails when token does not match
        """Extend lock fails when token does not match."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup existing lock token in Redis
        existing_token = "other-user#2026-01-01T00:00:00.000000"  # WHY: existing token
        # WHY: setup GET to return existing token
        mock_redis.get.return_value = existing_token.encode("utf-8")  # WHY: return token
        # WHY: setup different lock token for extend attempt
        wrong_token = "user-1#2026-01-01T00:00:00.000000"  # WHY: wrong token

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: extend lock with wrong token
        result = manager.extend_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: wrong lock token
            lock_token=wrong_token,
        )  # WHY: extend lock

        # WHY: verify extend failed
        assert result is False  # WHY: verify failure
        # WHY: verify EXPIRE was not called
        mock_redis.expire.assert_not_called()  # WHY: verify expire not called


class TestExtendLockWithoutRedis:
    # WHY: test extend_lock with Redis unavailable

    def test_extend_lock_no_redis_degraded(self) -> None:
        # WHY: verify graceful degradation when Redis unavailable
        """Extend lock succeeds in degraded mode when Redis unavailable."""
        # WHY: create SessionLockManager without Redis
        manager = SessionLockManager(redis_client=None)  # WHY: manager without Redis

        # WHY: extend lock
        result = manager.extend_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock token
            lock_token="some-token",
        )  # WHY: extend lock

        # WHY: verify extend succeeded in degraded mode
        assert result is True  # WHY: verify success


class TestCheckLockWithRedis:
    # WHY: test check_lock with Redis available

    def test_check_lock_exists(self) -> None:
        # WHY: verify check returns True when lock exists
        """Check lock returns True when lock exists."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup EXISTS to return 1 (key exists)
        mock_redis.exists.return_value = 1  # WHY: key exists

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: check if lock exists
        result = manager.check_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
        )  # WHY: check lock

        # WHY: verify lock exists
        assert result is True  # WHY: verify exists

    def test_check_lock_not_exists(self) -> None:
        # WHY: verify check returns False when lock does not exist
        """Check lock returns False when lock does not exist."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup EXISTS to return 0 (key does not exist)
        mock_redis.exists.return_value = 0  # WHY: key does not exist

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: check if lock exists
        result = manager.check_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
        )  # WHY: check lock

        # WHY: verify lock does not exist
        assert result is False  # WHY: verify not exists


class TestCheckLockWithoutRedis:
    # WHY: test check_lock with Redis unavailable

    def test_check_lock_no_redis_degraded(self) -> None:
        # WHY: verify check returns False when Redis unavailable (allow operation)
        """Check lock returns False in degraded mode when Redis unavailable."""
        # WHY: create SessionLockManager without Redis
        manager = SessionLockManager(redis_client=None)  # WHY: manager without Redis

        # WHY: check if lock exists
        result = manager.check_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
        )  # WHY: check lock

        # WHY: verify no lock in degraded mode
        assert result is False  # WHY: verify no lock (allow operation)


class TestSessionLockManagerIntegration:
    # WHY: integration tests for complete lock lifecycle

    def test_lock_lifecycle(self) -> None:
        # WHY: verify complete acquire -> extend -> release lifecycle
        """Test complete lock lifecycle: acquire, extend, release."""
        # WHY: create mock Redis client
        mock_redis = Mock()  # WHY: mock Redis client
        # WHY: setup mock for acquire (SET NX returns True)
        mock_redis.set.return_value = True  # WHY: SET NX succeeds

        # WHY: create SessionLockManager with mock Redis
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance

        # WHY: acquire lock
        acquire_result = manager.acquire_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
        )  # WHY: acquire lock
        # WHY: verify acquire succeeded
        assert acquire_result.acquired is True  # WHY: verify acquired
        # WHY: get lock token from result
        acquired_token = acquire_result.lock_token  # WHY: token from acquire
        # WHY: verify token is not None before using
        assert acquired_token is not None  # WHY: verify token exists

        # WHY: setup mock for extend (GET returns token, EXPIRE succeeds)
        mock_redis.get.return_value = acquired_token.encode(
            "utf-8"
        )  # WHY: return token

        # WHY: extend lock
        extend_result = manager.extend_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock token from acquire
            lock_token=acquired_token,
        )  # WHY: extend lock
        # WHY: verify extend succeeded
        assert extend_result is True  # WHY: verify extended

        # WHY: release lock
        release_result = manager.release_lock(
            # WHY: user identifier
            user_id="user-1",
            # WHY: site identifier
            site_id="site-1",
            # WHY: lock token from acquire
            lock_token=acquired_token,
        )  # WHY: release lock
        # WHY: verify release succeeded
        assert release_result is True  # WHY: verify released


class TestLockResultDataclass:
    # WHY: test LockResult dataclass

    def test_lock_result_successful(self) -> None:
        # WHY: verify LockResult can represent successful acquisition
        """LockResult represents successful lock acquisition."""
        # WHY: create successful LockResult
        result = LockResult(
            # WHY: lock acquired
            acquired=True,
            # WHY: timestamp of acquisition
            acquired_at=datetime.utcnow(),
            # WHY: lock token
            lock_token="user-1#2026-01-01T00:00:00.000000",
        )  # WHY: create result

        # WHY: verify acquired flag
        assert result.acquired is True  # WHY: verify acquired
        # WHY: verify acquired_at is set
        assert result.acquired_at is not None  # WHY: verify timestamp
        # WHY: verify lock_token is set
        assert result.lock_token is not None  # WHY: verify token
        # WHY: verify reason is None for success
        assert result.reason is None  # WHY: verify no reason
        # WHY: verify owner_id is None for success
        assert result.owner_id is None  # WHY: verify no owner

    def test_lock_result_failure(self) -> None:
        # WHY: verify LockResult can represent failed acquisition
        """LockResult represents failed lock acquisition."""
        # WHY: create failed LockResult
        result = LockResult(
            # WHY: lock not acquired
            acquired=False,
            # WHY: reason for failure
            reason="locked_by_user",
            # WHY: user holding the lock
            owner_id="other-user",
        )  # WHY: create result

        # WHY: verify acquired flag
        assert result.acquired is False  # WHY: verify not acquired
        # WHY: verify reason is set
        assert result.reason == "locked_by_user"  # WHY: verify reason
        # WHY: verify owner_id is set
        assert result.owner_id == "other-user"  # WHY: verify owner
        # WHY: verify lock_token is None for failure
        assert result.lock_token is None  # WHY: verify no token
