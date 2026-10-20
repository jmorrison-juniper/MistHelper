"""Test fail-closed configuration, Redis election, and snapshot publication."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
import redis
import requests

from src.interfaces.portals.wan_dashboard.services.worker import (
    RedisWorkerStore,
    WanDashboardWorker,
    WorkerSettings,
)


class MemoryRedis:
    """Model only the Redis commands used by the worker store."""

    def __init__(self) -> None:
        """Create one shared in-memory key set for worker tests."""
        self.values: dict[str, str] = {}  # Share values across simulated Gunicorn workers.
        self.fail_reads = False  # Allow tests to model a Redis outage.
        self.fail_publish = False  # Allow tests to model a failed atomic snapshot write.

    def set(self, key: str, value: str, *, nx: bool = False, ex: int | None = None) -> bool:
        """Store a value and support atomic create-only leases and queue bits."""
        if nx and key in self.values:  # Preserve an existing lease or queued follow-up.
            return False  # Match Redis SET NX when the key already exists.
        self.values[key] = value  # Keep the synthetic value in shared memory.
        return True  # Match a successful Redis SET response.

    def get(self, key: str) -> str | None:
        """Return one value unless the test models an outage."""
        if self.fail_reads:  # Surface the same failure type as the Redis client.
            raise redis.RedisError("synthetic redis failure")  # Do not contact a Redis server.
        return self.values.get(key)  # Return only the requested key.

    def exists(self, key: str) -> int:
        """Return whether one key exists."""
        if self.fail_reads:  # Keep status reads unavailable during the outage test.
            raise redis.RedisError("synthetic redis failure")  # Do not hide the outage.
        return int(key in self.values)  # Match Redis EXISTS truthiness.

    def delete(self, key: str) -> int:
        """Delete one key and return the number of removed values."""
        return int(self.values.pop(key, None) is not None)  # Match Redis DEL result shape.

    def expire(self, key: str, seconds: int) -> int:
        """Confirm that a present key can receive a renewed expiry."""
        return int(key in self.values)  # Expiry timing is outside this in-memory test.

    def eval(self, script: str, key_count: int, *arguments: Any) -> Any:
        """Apply the worker's token-checked atomic Redis scripts."""
        keys = arguments[:key_count]  # Separate Redis keys from script values.
        values = arguments[key_count:]  # Keep each script argument in its declared order.
        if script == RedisWorkerStore.TAKE_QUEUE_SCRIPT:
            queued = self.get(keys[0])  # Read the single pending queue bit.
            self.delete(keys[0])  # Consume it atomically in this fake.
            return queued  # Preserve empty and present queue states.
        if script == RedisWorkerStore.RENEW_SCRIPT:
            return self._token_action(keys[0], values[0], "renew", values[1])
        if script == RedisWorkerStore.RELEASE_SCRIPT:
            return self._token_action(keys[0], values[0], "release")
        if script == RedisWorkerStore.STATE_SCRIPT:
            return self._write_state(keys[0], keys[1], values[0], values[1])
        if script == RedisWorkerStore.PUBLISH_SCRIPT:
            return self._publish(keys, values)
        return 0  # Unknown scripts fail closed.

    def _token_action(self, key: str, token: str, action: str, lease: int = 0) -> int:
        """Renew or release a lease only when its token matches."""
        if self.values.get(key) != token:  # Reject a stale worker token.
            return 0  # The caller must stop collection after this result.
        if action == "release":  # Remove only this worker's lease.
            return self.delete(key)  # Return the Redis DEL result.
        return self.expire(key, lease)  # Match the Redis EXPIRE result.

    def _write_state(self, lease_key: str, state_key: str, token: str, payload: str) -> int:
        """Save progress only while the caller owns the lease."""
        if self.values.get(lease_key) != token:  # Reject a stale process.
            return 0  # Do not overwrite another worker's status.
        self.values[state_key] = payload  # Store the synthetic JSON status.
        return 1  # Match a successful Redis SET response.

    def _publish(self, keys: tuple[str, ...], values: tuple[Any, ...]) -> int:
        """Write a snapshot and status together only for the lease owner."""
        if self.fail_publish:  # Model a write failure without breaking status reads.
            raise redis.RedisError("synthetic redis failure")  # Keep the failure local to this fake.
        lease_key, snapshot_key, state_key = keys  # Read the three keys used by the Lua script.
        token, snapshot, _snapshot_ttl, state, _state_ttl = values  # Read values in script order.
        if self.values.get(lease_key) != token:  # Reject a worker that lost its lease.
            return 0  # Keep both existing snapshot and status unchanged.
        self.values[snapshot_key] = snapshot  # Store the complete synthetic snapshot.
        self.values[state_key] = state  # Store its matching completion state.
        return 1  # Match a successful atomic publish.


class TestWorkerSettings:
    """Prove worker configuration stays disabled without load approval."""

    def test_missing_approval_or_timing_keeps_worker_disabled(self) -> None:
        """Missing approval, enablement, or timing cannot start collection."""
        values = {"WAN_DASHBOARD_REFRESH_ENABLED": "true"}  # Supply only the ordinary enable flag.
        assert WorkerSettings.from_sources(values, {}) is None  # Require load-test approval first.
        values["WAN_DASHBOARD_LOAD_TEST_APPROVED"] = "true"  # Add explicit load-test approval.
        assert WorkerSettings.from_sources(values, {}) is None  # Require both unselected timing values.

    def test_invalid_timing_values_fail_closed(self) -> None:
        """Zero, negative, decimal, and boolean timing values are rejected."""
        base = {  # Keep configuration values local and synthetic.
            "WAN_DASHBOARD_LOAD_TEST_APPROVED": "true",
            "WAN_DASHBOARD_REFRESH_ENABLED": "true",
            "WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS": "0",
            "WAN_DASHBOARD_WORKER_LEASE_SECONDS": "30",
        }
        assert WorkerSettings.from_sources(base, {}) is None  # Reject zero interval.
        base["WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS"] = "60.5"  # Model a decimal environment value.
        assert WorkerSettings.from_sources(base, {}) is None  # Reject coercible non-integer timing.

    def test_positive_timing_values_require_both_approval_flags(self) -> None:
        """Only explicit approval and valid positive timing create worker settings."""
        values = {  # Use arbitrary values only in an isolated unit test.
            "WAN_DASHBOARD_LOAD_TEST_APPROVED": "true",
            "WAN_DASHBOARD_REFRESH_ENABLED": "true",
            "WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS": "60",
            "WAN_DASHBOARD_WORKER_LEASE_SECONDS": "30",
        }
        settings = WorkerSettings.from_sources(values, {})  # Parse the complete test configuration.
        assert settings == WorkerSettings(60, 30)  # Preserve valid settings without setting production values.


class TestRedisWorkerStore:
    """Prove worker election, queue coalescing, and atomic publication."""

    def test_lease_elects_one_worker_and_checks_ownership(self) -> None:
        """One worker owns the lease until it releases its matching token."""
        client = MemoryRedis()  # Share keys between two simulated process stores.
        first = RedisWorkerStore(client, "org-a")  # Model the first Gunicorn process.
        second = RedisWorkerStore(client, "org-a")  # Model a competing Gunicorn process.
        assert first.acquire("worker-a", 30)  # The first process becomes the collector.
        assert not second.acquire("worker-b", 30)  # The second process cannot collect concurrently.
        assert not second.renew("worker-b", 30)  # A different token cannot renew the lease.
        assert first.release("worker-a")  # The owner releases only its own lease.
        assert second.acquire("worker-b", 30)  # The next process can then become the collector.

    def test_queue_coalesces_requests_into_one_follow_up(self) -> None:
        """Repeated Refresh requests create one pending queue bit."""
        store = RedisWorkerStore(MemoryRedis(), "org-a")  # Use one local queue.
        assert store.enqueue() == "queued"  # The first request creates the pending bit.
        assert store.enqueue() == "coalesced"  # Later requests share the same follow-up.
        assert store.take_queued() is True  # The worker consumes one pending follow-up.
        assert store.take_queued() is False  # No duplicate work remains.

    def test_refresh_during_active_run_produces_one_follow_up(self) -> None:
        """Requests during one run coalesce into exactly one later collection."""
        client = MemoryRedis()  # Share the lease and queue between worker actions.
        store = RedisWorkerStore(client, "org-a")  # Use one organization-scoped worker store.
        assert store.acquire("worker-a", 30)  # Give one process sole collection ownership.
        assert store.enqueue() == "queued"  # Start the first refresh from the shared queue.
        snapshot = {
            "schema_version": 1,
            "org_id": "org-a",
            "collected_at": "2026-10-20T12:00:00+00:00",
            "data": [],
        }  # Keep the result complete and fictional.
        service = MagicMock()  # Replace all Mist access with a deterministic callback.
        collection_count = 0  # Count only calls made by the elected worker.

        def enqueue_follow_up(_progress: Any, _lease_is_valid: Any) -> tuple[dict[str, Any], None]:
            """Add one queue request while the first collection remains active."""
            nonlocal collection_count  # Keep the count local to this test.
            collection_count += 1  # Identify the active run and its single follow-up.
            if collection_count == 1:
                store.enqueue()  # Model the operator request during the active refresh.
            return snapshot, None  # Keep the first complete snapshot synthetic.

        service.collect_worker_snapshot.side_effect = enqueue_follow_up  # Queue one request during the active run.
        worker = WanDashboardWorker(service, store, WorkerSettings(3600, 30))  # Avoid a timed third run.

        worker._serve_lease("worker-a")  # Run the first refresh and its single pending follow-up.

        assert service.collect_worker_snapshot.call_count == 2  # Never run concurrent or duplicate work.
        assert store.take_queued() is False  # Leave no additional work after the follow-up.

    def test_snapshot_publish_requires_the_current_lease(self) -> None:
        """A stale process cannot replace a complete snapshot."""
        client = MemoryRedis()  # Keep the snapshot and lease local.
        store = RedisWorkerStore(client, "org-a")  # Use the production key and script contract.
        snapshot = {"schema_version": 1, "org_id": "org-a", "collected_at": "2026-10-20T12:00:00+00:00", "data": []}
        state = WanDashboardWorker.disabled_status()  # Provide a bounded status envelope.
        assert not store.publish_snapshot("stale-worker", snapshot, state)  # Reject an absent lease.


class TestWanDashboardWorker:
    """Prove failures preserve complete data and outage status stays stale."""

    def test_failed_refresh_preserves_the_last_complete_snapshot(self) -> None:
        """An API failure marks the prior snapshot stale without publishing partial rows."""
        client = MemoryRedis()  # Keep cache and status keys in one synthetic Redis store.
        store = RedisWorkerStore(client, "org-a")  # Use the real key namespace.
        assert store.acquire("worker-a", 30)  # Give the test worker exclusive publication rights.
        snapshot_key = "wan-dashboard:v1:overview:org-a:last-success"  # Use the canonical overview key.
        prior = '{"schema_version":1,"org_id":"org-a","data":[{"device_id":"old"}]}'  # Preserve one prior value.
        client.values[snapshot_key] = prior  # Seed the last complete snapshot.
        service = MagicMock()  # Keep Mist collection offline.
        service.collect_worker_snapshot.return_value = (None, "http_429")  # Model a rate-limited page.
        worker = WanDashboardWorker(service, store, WorkerSettings(60, 30))  # Configure a local worker.

        completed = worker._run_refresh("worker-a")  # Run one controlled collection attempt.

        status = store.read_status()  # Read the worker result from shared Redis.
        assert not completed  # A failed read must not report success.
        assert client.values[snapshot_key] == prior  # Keep the last complete snapshot unchanged.
        assert status is not None and status["status"] == "failed"  # Expose the failed refresh state.
        assert status["safe_error"] == "http_429"  # Keep the rate-limit status safe and specific.
        assert status["stale"] is True  # Mark the retained snapshot stale.
        service.remember_worker_snapshot.assert_not_called()  # Do not remember incomplete data.

    def test_redis_publish_failure_preserves_the_last_complete_snapshot(self) -> None:
        """A Redis write failure leaves the prior snapshot intact and marks it stale."""
        client = MemoryRedis()  # Keep the cache and status local.
        store = RedisWorkerStore(client, "org-a")  # Use the production key contract.
        assert store.acquire("worker-a", 30)  # Give the worker an active lease.
        snapshot_key = "wan-dashboard:v1:overview:org-a:last-success"  # Use the canonical overview key.
        prior = '{"schema_version":1,"org_id":"org-a","data":[{"device_id":"old"}]}'  # Keep one complete value.
        client.values[snapshot_key] = prior  # Seed the prior published snapshot.
        client.fail_publish = True  # Fail only the atomic publish command.
        service = MagicMock()  # Keep collection offline.
        service.collect_worker_snapshot.return_value = (
            {"schema_version": 1, "org_id": "org-a", "collected_at": "2026-10-20T12:00:00+00:00", "data": []},
            None,
        )  # Model a complete result before Redis fails.
        worker = WanDashboardWorker(service, store, WorkerSettings(60, 30))  # Bind local test dependencies.

        completed = worker._run_refresh("worker-a")  # Attempt one atomic snapshot update.

        status = store.read_status()  # Read the failure state from the still-available status key.
        assert not completed  # A failed Redis write is not a completed refresh.
        assert client.values[snapshot_key] == prior  # Preserve the last complete snapshot.
        assert status is not None and status["safe_error"] == "redis_unavailable"  # Report a safe Redis error.
        assert status["stale"] is True  # Mark the retained snapshot stale.

    def test_redis_outage_marks_local_complete_status_stale(self) -> None:
        """A Redis outage reports a stale local snapshot without Mist access."""
        client = MemoryRedis()  # Use one store that can fail reads.
        service = MagicMock()  # No method on the Mist service is needed for status.
        worker = WanDashboardWorker(service, RedisWorkerStore(client, "org-a"), WorkerSettings(60, 30))
        worker._set_state(  # Seed one earlier complete local status.
            {
                **WanDashboardWorker.disabled_status(),
                "status": "complete",
                "last_complete_at": "2026-10-20T12:00:00+00:00",
                "stale": False,
            }
        )
        client.fail_reads = True  # Model a Redis connection failure.

        result = worker.status()  # Read status without calling the Mist service.

        assert result["status"] == "stale"  # Never present local data as current during Redis loss.
        assert result["safe_error"] == "redis_unavailable"  # Give a safe reason for the stale state.
        assert result["redis_available"] is False  # Distinguish the local status fallback.
        service.collect_worker_snapshot.assert_not_called()  # Status reads never call Mist.

    def test_complete_refresh_publishes_snapshot_and_status_together(self) -> None:
        """A valid complete snapshot updates Redis and the process-local fallback."""
        client = MemoryRedis()  # Keep all shared state synthetic.
        store = RedisWorkerStore(client, "org-a")  # Use the real atomic publish script.
        assert store.acquire("worker-a", 30)  # Grant this worker the lease.
        snapshot = {
            "schema_version": 1,
            "org_id": "org-a",
            "collected_at": "2026-10-20T12:00:00+00:00",
            "data": [{"device_id": "gw-a"}],
        }  # Keep the test data fictional and complete.
        service = MagicMock()  # Avoid SDK access during this worker-state test.
        service.collect_worker_snapshot.return_value = (snapshot, None)  # Model four successful bulk reads.
        worker = WanDashboardWorker(service, store, WorkerSettings(60, 30))  # Bind the fake service and store.

        completed = worker._run_refresh("worker-a")  # Run one complete refresh.

        stored = json.loads(client.values["wan-dashboard:v1:overview:org-a:last-success"])
        state = store.read_status()  # Read the status written in the same Redis script.
        assert completed is True  # The complete run succeeds.
        assert stored == snapshot  # Publish the full snapshot without partial rows.
        assert state is not None and state["status"] == "complete"  # Publish matching completion state.
        service.remember_worker_snapshot.assert_called_once_with(snapshot)  # Preserve the bounded local fallback.


def create_worker_with_prior_snapshot() -> tuple[MemoryRedis, RedisWorkerStore, MagicMock, WanDashboardWorker, str]:
    """Build one leased worker with a complete synthetic snapshot."""
    client = MemoryRedis()  # Keep all failure-path data local.
    store = RedisWorkerStore(client, "org-a")  # Use the production Redis key names.
    store.acquire("worker-a", 30)  # Give this worker sole publication rights.
    snapshot_key = "wan-dashboard:v1:overview:org-a:last-success"  # Reuse the canonical cache key.
    prior = '{"schema_version":1,"org_id":"org-a","data":[{"device_id":"old"}]}'  # Keep prior data complete.
    client.values[snapshot_key] = prior  # Seed the result that failures must preserve.
    service = MagicMock()  # Keep every test independent from Mist.
    worker = WanDashboardWorker(service, store, WorkerSettings(60, 30))  # Bind local test dependencies.
    return client, store, service, worker, snapshot_key  # Give each test the same safe baseline.


class TestWorkerFailureModes:
    """Prove transport, HTTP, and body failures preserve the last complete snapshot."""

    @pytest.mark.parametrize("status_code", [429, 503], ids=["http-4xx", "http-5xx"])
    def test_http_status_failure_preserves_prior_snapshot(self, status_code: int) -> None:
        """Client and server status failures never publish a replacement snapshot."""
        client, store, service, worker, snapshot_key = create_worker_with_prior_snapshot()
        service.collect_worker_snapshot.return_value = (None, f"http_{status_code}")  # Model a failed API read.

        completed = worker._run_refresh("worker-a")  # Run one failed collection without any network request.

        status = store.read_status()  # Read the safe failure state from synthetic Redis.
        assert completed is False  # A failed page cannot report a complete run.
        assert client.values[snapshot_key].endswith('"data":[{"device_id":"old"}]}')  # Keep the prior rows.
        assert status is not None and status["safe_error"] == f"http_{status_code}"  # Preserve the status family.

    @pytest.mark.parametrize(
        "transport_error",
        [requests.ConnectionError, requests.Timeout],
        ids=["connection-error", "timeout"],
    )
    def test_transport_failure_preserves_prior_snapshot(self, transport_error: type[Exception]) -> None:
        """Connection errors and timeouts leave the complete cache unchanged."""
        client, store, service, worker, snapshot_key = create_worker_with_prior_snapshot()
        service.collect_worker_snapshot.side_effect = transport_error("synthetic transport failure")

        completed = worker._run_refresh("worker-a")  # Let the worker map a transport failure safely.

        status = store.read_status()  # Read the safe failure state from synthetic Redis.
        assert completed is False  # A transport failure cannot report a complete run.
        assert client.values[snapshot_key].endswith('"data":[{"device_id":"old"}]}')  # Keep the prior rows.
        assert status is not None and status["safe_error"] == "worker_error"  # Do not expose exception text.

    @pytest.mark.parametrize("response_body", [b"", "{"], ids=["empty-body", "malformed-json"])
    def test_invalid_json_body_preserves_prior_snapshot(self, response_body: bytes | str) -> None:
        """An empty body or malformed JSON cannot replace the complete cache."""
        with pytest.raises(json.JSONDecodeError) as parse_error:
            json.loads(response_body)  # Model the Mist SDK failing to decode the response body.
        client, store, service, worker, snapshot_key = create_worker_with_prior_snapshot()
        service.collect_worker_snapshot.side_effect = parse_error.value  # Raise the SDK decode failure.

        completed = worker._run_refresh("worker-a")  # Let the worker handle the failed collection.

        status = store.read_status()  # Read the safe failure state from synthetic Redis.
        assert completed is False  # Invalid response data cannot report a complete run.
        assert client.values[snapshot_key].endswith('"data":[{"device_id":"old"}]}')  # Keep the prior rows.
        assert status is not None and status["safe_error"] == "worker_error"  # Hide parser details.
