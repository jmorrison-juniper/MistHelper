"""Unit tests for session locking service (T-015).

Test acquire_lock(), release_lock(), extend_lock(), check_lock() with:
- Redis available scenarios
- Redis unavailable (graceful degradation)
- Token mismatch scenarios
- Lock expiry scenarios
"""

from datetime import UTC, datetime, timedelta  # WHY: timestamp comparison
from unittest.mock import Mock  # WHY: mock Redis client

import pytest  # WHY: assert propagation for errors outside the Redis contract
import redis  # WHY: build Redis driver failures for narrowed handlers

from src.upgrade_portal.locking.session_lock import (
    LockResult,
    SessionLockManager,
)  # WHY: import classes under test


class ExpiringRedisDouble:
    # WHY: test Redis TTL behavior without a Redis server
    """Store lock values and expire them through aware UTC comparisons."""

    def __init__(self) -> None:
        # WHY: start with an aware UTC clock to match the product convention
        self.now = datetime.now(UTC)  # WHY: all expiry comparisons use an aware UTC value.
        self.values: dict[str, str] = {}  # WHY: hold Redis values by key.
        self.expires_at: dict[str, datetime] = {}  # WHY: hold one expiry moment by key.

    def advance(self, seconds: int) -> None:
        # WHY: move the fake clock without sleeping
        self.now += timedelta(seconds=seconds)  # WHY: tests drive fresh and expired boundaries.

    def set(self, name: str, value: str, ex: int, nx: bool) -> bool:
        # WHY: implement the Redis SET NX EX behavior that the lock manager uses
        self._expire(name)  # WHY: remove an old value before the NX check.
        if nx and name in self.values:  # WHY: Redis refuses to overwrite an active lock.
            return False  # WHY: report that another holder still owns the key.
        timestamp = str(value).split("#", maxsplit=1)[1]  # WHY: read the stored acquisition time.
        acquired_at = datetime.fromisoformat(timestamp)  # WHY: parse the stored timestamp as callers would.
        if acquired_at.tzinfo is not None and acquired_at.utcoffset() is not None:  # WHY: accept aware UTC only.
            self.now = acquired_at  # WHY: align the Redis clock with the product acquisition time.
        self.values[name] = value  # WHY: store the lock token as Redis would.
        self.expires_at[name] = acquired_at + timedelta(seconds=ex)  # WHY: derive the expiry moment.
        return True  # WHY: Redis SET NX EX accepted the lock.

    def get(self, name: str) -> str | None:
        # WHY: implement Redis GET with expiry
        self._expire(name)  # WHY: Redis hides expired keys from reads.
        return self.values.get(name)  # WHY: return the active value or a cache miss.

    def exists(self, name: str) -> int:
        # WHY: implement Redis EXISTS with expiry
        self._expire(name)  # WHY: Redis hides expired keys from existence checks.
        return 1 if name in self.values else 0  # WHY: Redis returns an integer count.

    def delete(self, name: str) -> None:
        # WHY: implement the delete operation used by release
        self.values.pop(name, None)  # WHY: remove the stored token if it exists.
        self.expires_at.pop(name, None)  # WHY: remove the matching expiry moment.

    def expire(self, name: str, time: int) -> None:
        # WHY: implement the expire operation used by heartbeat
        self._expire(name)  # WHY: an expired key cannot receive a new TTL.
        if name in self.values:  # WHY: Redis updates only an existing key.
            self.expires_at[name] = self.now + timedelta(seconds=time)  # WHY: extend from the current clock.

    def _expire(self, name: str) -> None:
        # WHY: remove a key when the aware UTC clock passes its expiry
        expiry = self.expires_at.get(name)  # WHY: a missing expiry means no active key.
        if expiry is not None and self.now > expiry:  # WHY: this comparison fails if one side is naive.
            self.delete(name)  # WHY: expired locks must not block another operator.


class TestAcquireLockWithRedis:
    # WHY: test acquire_lock with Redis available

    def test_fresh_lock_does_not_expire_before_ttl(self) -> None:
        # WHY: prove an aware UTC lock timestamp supports the fresh-lock comparison
        """A fresh lock still blocks a repeated acquisition before its TTL ends."""
        redis_double = ExpiringRedisDouble()  # WHY: use a Redis double that compares stored timestamps.
        manager = SessionLockManager(redis_client=redis_double)  # WHY: drive the product lock manager.
        first = manager.acquire_lock("user-1", "site-1", timeout=60)  # WHY: create the stored lock.
        redis_double.advance(59)  # WHY: move the clock near, but not past, expiry.

        second = manager.acquire_lock("user-1", "site-1", timeout=60)  # WHY: test the active lock boundary.

        assert first.acquired is True  # WHY: the first operator owns the lock.
        assert manager.check_lock("user-1", "site-1") is True  # WHY: the fresh lock remains active.
        assert second.acquired is False  # WHY: the repeated acquisition must not enter early.
        assert second.owner_id == "user-1"  # WHY: the denial names the active holder.

    def test_expired_lock_allows_a_new_holder_after_ttl(self) -> None:
        # WHY: prove an aware UTC lock timestamp supports the expired-lock comparison
        """An expired lock stops blocking a repeated acquisition after its TTL ends."""
        redis_double = ExpiringRedisDouble()  # WHY: use a Redis double that compares stored timestamps.
        manager = SessionLockManager(redis_client=redis_double)  # WHY: drive the product lock manager.
        first = manager.acquire_lock("user-1", "site-1", timeout=60)  # WHY: create the stored lock.
        redis_double.advance(61)  # WHY: move the clock past expiry.

        second = manager.acquire_lock("user-1", "site-1", timeout=60)  # WHY: test the expired lock boundary.

        assert first.acquired is True  # WHY: the first operator held the original lock.
        assert manager.check_lock("user-1", "site-1") is True  # WHY: the new lock is active after reacquire.
        assert second.acquired is True  # WHY: the repeated acquisition can enter after expiry.
        assert second.owner_id is None  # WHY: the grant names no blocking holder.

    def test_acquired_at_supports_aware_expiry_math(self) -> None:
        # WHY: prove callers can subtract the returned timestamp from an aware UTC clock
        """The acquisition time uses the same aware UTC convention as expiry code."""
        manager = SessionLockManager(redis_client=None)  # WHY: degraded mode returns the timestamp directly.

        result = manager.acquire_lock("user-1", "site-1", timeout=60)  # WHY: create a lock result.

        assert result.acquired_at.utcoffset() == timedelta(0)  # WHY: the lock grant uses aware UTC.
        assert datetime.now(UTC) - result.acquired_at < timedelta(seconds=5)  # WHY: aware math must not raise.

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
        # WHY: verify lock token includes the expected owner
        assert result.lock_token.startswith("user-1#")  # WHY: verify token generated for this user.
        # WHY: verify timestamp is aware UTC
        assert result.acquired_at.utcoffset() == timedelta(0)  # WHY: verify timestamp convention.
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
        mock_redis.set.side_effect = redis.RedisError("Redis connection failed")  # WHY: raise driver error

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

    def test_acquire_lock_unexpected_error_propagates(self) -> None:
        """Acquire lock does not hide a programming fault."""
        mock_redis = Mock()  # WHY: mock Redis client
        mock_redis.set.side_effect = RuntimeError("bug")  # WHY: model a defect, not a Redis outage
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance
        with pytest.raises(RuntimeError, match="bug"):  # WHY: the narrowed handler must not swallow defects.
            manager.acquire_lock(user_id="user-1", site_id="site-1")  # WHY: drive the narrowed handler.


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
        # WHY: verify lock token is generated for this user
        assert result.lock_token.startswith("user-1#")  # WHY: verify token generated for degraded mode.
        # WHY: verify timestamp is aware UTC
        assert result.acquired_at.utcoffset() == timedelta(0)  # WHY: verify timestamp convention.


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

    def test_release_lock_redis_error_returns_false(self) -> None:
        """Release lock returns a failure signal when Redis does not answer."""
        mock_redis = Mock()  # WHY: mock Redis client
        mock_redis.get.side_effect = redis.RedisError("Redis connection failed")  # WHY: raise driver error
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance
        result = manager.release_lock("user-1", "site-1", "token")  # WHY: drive the narrowed handler.
        assert result is False  # WHY: Redis failure must not look like release success.


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

    def test_extend_lock_redis_error_returns_false(self) -> None:
        """Extend lock returns a failure signal when Redis does not answer."""
        mock_redis = Mock()  # WHY: mock Redis client
        mock_redis.get.side_effect = redis.RedisError("Redis connection failed")  # WHY: raise driver error
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance
        result = manager.extend_lock("user-1", "site-1", "token")  # WHY: drive the narrowed handler.
        assert result is False  # WHY: Redis failure must not look like renewal success.


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

    def test_check_lock_redis_error_returns_false(self) -> None:
        """Check lock returns false when Redis does not answer."""
        mock_redis = Mock()  # WHY: mock Redis client
        mock_redis.exists.side_effect = redis.RedisError("Redis connection failed")  # WHY: raise driver error
        manager = SessionLockManager(redis_client=mock_redis)  # WHY: manager instance
        result = manager.check_lock("user-1", "site-1")  # WHY: drive the narrowed handler.
        assert result is False  # WHY: read failure must keep the caller in degraded mode.


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
        # WHY: verify the token belongs to this user before using it
        assert acquired_token.startswith("user-1#")  # WHY: verify token exists and names the holder.

        # WHY: setup mock for extend (GET returns token, EXPIRE succeeds)
        mock_redis.get.return_value = acquired_token.encode("utf-8")  # WHY: return token

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
            acquired_at=datetime.now(UTC),
            # WHY: lock token
            lock_token="user-1#2026-01-01T00:00:00.000000",
        )  # WHY: create result

        # WHY: verify acquired flag
        assert result.acquired is True  # WHY: verify acquired
        # WHY: verify acquired_at is aware UTC
        assert result.acquired_at.utcoffset() == timedelta(0)  # WHY: verify timestamp convention.
        # WHY: verify lock_token names the holder
        assert result.lock_token == "user-1#2026-01-01T00:00:00.000000"  # WHY: verify token content.
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
