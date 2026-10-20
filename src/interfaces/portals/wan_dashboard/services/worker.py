"""Run one fail-closed WAN snapshot worker inside the existing portal process."""

from __future__ import annotations

import atexit
import json
import logging
import os
import re
import secrets
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import redis
import requests
from flask.blueprints import BlueprintSetupState

from src.interfaces.portals.wan_dashboard.services import (
    RedisDashboardCache,
    WanDashboardService,
    WanDataNormalizer,
)

logger = logging.getLogger(__name__)  # Keep worker records under one module name.


@dataclass(frozen=True, slots=True)
class WorkerSettings:
    """Hold positive refresh timing values after explicit operator configuration."""

    interval_seconds: int
    lease_seconds: int

    ENABLED_KEY = "WAN_DASHBOARD_REFRESH_ENABLED"
    LOAD_TEST_APPROVED_KEY = "WAN_DASHBOARD_LOAD_TEST_APPROVED"
    INTERVAL_KEY = "WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS"
    LEASE_KEY = "WAN_DASHBOARD_WORKER_LEASE_SECONDS"

    @classmethod
    def from_sources(cls, config: Mapping[str, Any], environment: Mapping[str, str]) -> WorkerSettings | None:
        """Return settings only after approval, enablement, and valid timing values."""
        approved = config.get(cls.LOAD_TEST_APPROVED_KEY, environment.get(cls.LOAD_TEST_APPROVED_KEY, "false"))
        enabled = config.get(cls.ENABLED_KEY, environment.get(cls.ENABLED_KEY, "false"))
        if not cls._is_true(approved) or not cls._is_true(enabled):
            return None  # Missing or false configuration keeps all collection disabled.
        interval = cls._positive_integer(config.get(cls.INTERVAL_KEY, environment.get(cls.INTERVAL_KEY)))
        lease = cls._positive_integer(config.get(cls.LEASE_KEY, environment.get(cls.LEASE_KEY)))
        if interval is None or lease is None:
            return None  # Incomplete or invalid timing values fail closed.
        return cls(interval, lease)  # Keep validated values immutable for this process.

    @staticmethod
    def _is_true(value: object) -> bool:
        """Accept only an explicit boolean true or the text true."""
        return value is True or isinstance(value, str) and value.strip().lower() == "true"

    @staticmethod
    def _positive_integer(value: object) -> int | None:
        """Parse one positive integer without exposing a bad configuration value."""
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            return None  # Reject booleans, decimals, and other coercible values.
        if isinstance(value, str) and not re.fullmatch(r"[0-9]+", value.strip()):
            return None  # Accept only a plain positive integer from process configuration.
        try:
            parsed = int(value)  # Configuration arrives as text from the process environment.
        except (TypeError, ValueError):
            return None  # Reject missing or malformed values.
        return parsed if parsed > 0 else None  # Zero and negative timing values are invalid.


class RedisWorkerStore:
    """Keep one lease, coalesced queue bit, status, and atomic snapshot value in Redis."""

    STALE_TTL = WanDashboardService.STALE_TTL
    TAKE_QUEUE_SCRIPT = "local value=redis.call('GET',KEYS[1]); redis.call('DEL',KEYS[1]); return value"
    RENEW_SCRIPT = (
        "if redis.call('GET',KEYS[1]) == ARGV[1] then return redis.call('EXPIRE',KEYS[1],ARGV[2]) end return 0"
    )
    RELEASE_SCRIPT = "if redis.call('GET',KEYS[1]) == ARGV[1] then return redis.call('DEL',KEYS[1]) end return 0"
    STATE_SCRIPT = (
        "if redis.call('GET',KEYS[1]) ~= ARGV[1] then return 0 end "
        "return redis.call('SET',KEYS[2],ARGV[2],'EX',ARGV[3])"
    )
    PUBLISH_SCRIPT = (
        "if redis.call('GET',KEYS[1]) ~= ARGV[1] then return 0 end "
        "redis.call('SET',KEYS[2],ARGV[2],'EX',ARGV[3]); "
        "return redis.call('SET',KEYS[3],ARGV[4],'EX',ARGV[5])"
    )

    def __init__(self, client: Any, org_id: str) -> None:
        """Scope all worker coordination keys to the existing dashboard namespace."""
        prefix = WanDashboardService.CACHE_PREFIX  # Reuse the approved feature key prefix.
        self._client = client  # Share the existing Redis connection with the portal.
        self._lease_key = prefix + "worker:lease:" + org_id  # Elect one collector across Gunicorn processes.
        self._queue_key = prefix + "worker:queue:" + org_id  # One Redis bit represents one pending refresh.
        self._status_key = prefix + "worker:status:" + org_id  # Store safe progress for every portal process.
        self._snapshot_key = prefix + "overview:" + org_id + ":last-success"  # Reuse the canonical snapshot key.

    def acquire(self, token: str, lease_seconds: int) -> bool:
        """Acquire the worker lease only when no other process owns it."""
        try:
            return bool(self._client.set(self._lease_key, token, nx=True, ex=lease_seconds))
        except (redis.RedisError, OSError, TimeoutError):
            logger.warning("wan dashboard worker could not acquire its Redis lease")
            return False

    def renew(self, token: str, lease_seconds: int) -> bool:
        """Renew the lease only while Redis still records this process token."""
        try:
            return bool(self._client.eval(self.RENEW_SCRIPT, 1, self._lease_key, token, lease_seconds))
        except (redis.RedisError, OSError, TimeoutError):
            logger.warning("wan dashboard worker could not renew its Redis lease")
            return False

    def release(self, token: str) -> bool:
        """Release only the lease that contains this process token."""
        try:
            return bool(self._client.eval(self.RELEASE_SCRIPT, 1, self._lease_key, token))
        except (redis.RedisError, OSError, TimeoutError):
            logger.warning("wan dashboard worker could not release its Redis lease")
            return False

    def enqueue(self) -> str:
        """Set one expiring queue bit and coalesce every request that follows it."""
        try:
            queued = self._client.set(self._queue_key, "1", nx=True, ex=self.STALE_TTL)
        except (redis.RedisError, OSError, TimeoutError):
            logger.warning("wan dashboard refresh queue is unavailable")
            return "unavailable"
        return "queued" if queued else "coalesced"  # One pending key represents any number of requests.

    def take_queued(self) -> bool | None:
        """Atomically consume the pending refresh bit without losing a new request."""
        try:
            return bool(self._client.eval(self.TAKE_QUEUE_SCRIPT, 1, self._queue_key))
        except (redis.RedisError, OSError, TimeoutError):
            logger.warning("wan dashboard refresh queue could not be read")
            return None

    def has_queued(self) -> bool | None:
        """Read the pending queue state without consuming an operator request."""
        try:
            return bool(self._client.exists(self._queue_key))
        except (redis.RedisError, OSError, TimeoutError):
            logger.warning("wan dashboard refresh queue state is unavailable")
            return None

    def read_status(self) -> dict[str, Any] | None:
        """Return safe worker state or None when Redis cannot answer."""
        try:
            value = self._client.get(self._status_key)  # Read one bounded status record.
            return json.loads(value) if value else None  # JSON decoding rejects malformed status.
        except (redis.RedisError, OSError, TimeoutError, TypeError, ValueError):
            logger.warning("wan dashboard refresh status is unavailable")
            return None

    def write_status(self, token: str, state: dict[str, Any]) -> bool:
        """Write progress only while this process still owns the lease."""
        try:
            payload = json.dumps(state, allow_nan=False, separators=(",", ":"))
            result = self._client.eval(
                self.STATE_SCRIPT, 2, self._lease_key, self._status_key, token, payload, self.STALE_TTL
            )
        except (redis.RedisError, OSError, TimeoutError, TypeError, ValueError):
            logger.warning("wan dashboard refresh status could not be saved")
            return False
        return bool(result)  # A lost lease prevents the status update.

    def publish_snapshot(self, token: str, snapshot: dict[str, Any], state: dict[str, Any]) -> bool | None:
        """Publish one complete snapshot and its status while the lease remains valid."""
        try:
            snapshot_json = json.dumps(snapshot, allow_nan=False, separators=(",", ":"))
            state_json = json.dumps(state, allow_nan=False, separators=(",", ":"))
            result = self._client.eval(
                self.PUBLISH_SCRIPT,
                3,
                self._lease_key,
                self._snapshot_key,
                self._status_key,
                token,
                snapshot_json,
                self.STALE_TTL,
                state_json,
                self.STALE_TTL,
            )
        except (redis.RedisError, OSError, TimeoutError, TypeError, ValueError):
            logger.error("wan dashboard complete snapshot could not be published")
            return None  # Distinguish a Redis fault from a lease owned by another process.
        return bool(result)  # A worker without its lease cannot publish.


class WanDashboardWorker:
    """Collect complete WAN snapshots from one Redis-elected Gunicorn process."""

    EXTENSION_KEY = "wan_dashboard_worker"
    SERVICE_EXTENSION_KEY = "wan_dashboard_service"
    DISABLED_STATUS_KEY = "wan_dashboard_worker_status"
    POLL_SECONDS = 1
    HEARTBEAT_DIVISOR = 3
    STATE_FIELDS = (
        "status",
        "current_phase",
        "completed_pages",
        "requested_at",
        "started_at",
        "finished_at",
        "last_complete_at",
        "next_scheduled_at",
        "safe_error",
        "stale",
        "queued_follow_up",
    )

    def __init__(
        self,
        service: WanDashboardService,
        store: RedisWorkerStore,
        settings: WorkerSettings,
    ) -> None:
        """Bind the existing service, Redis coordinator, and validated timings."""
        self._service = service  # Reuse the shared SDK session and dashboard normalizers.
        self._store = store  # Coordinate every Gunicorn process through one Redis client.
        self._settings = settings  # Timing values exist only after explicit valid configuration.
        self._stop = threading.Event()  # Let process shutdown stop the daemon loop.
        self._state_guard = threading.Lock()  # Protect the local status fallback from route threads.
        self._state = self._initial_state("idle")  # Keep a safe status while Redis is unavailable.
        self._thread: threading.Thread | None = None  # Start no thread until blueprint registration completes.

    @classmethod
    def register_blueprint(cls, state: BlueprintSetupState) -> None:
        """Start a configured worker when Flask registers the existing dashboard blueprint."""
        app = state.app  # The app receives the blueprint and owns the worker lifecycle.
        settings = WorkerSettings.from_sources(app.config, os.environ)
        if settings is None:  # No timing value or enable flag is supplied before load approval.
            app.extensions[cls.DISABLED_STATUS_KEY] = cls._initial_state("disabled")
            logger.info("wan dashboard refresh worker remains disabled")
            return
        session = app.config.get("APISESSION")  # Reuse the MistHelper session already in app.config.
        org_id = app.config.get("ORG_ID")  # Keep collection scoped to the active organization.
        if session is None or not isinstance(org_id, str) or not WanDataNormalizer.identifier(org_id):
            app.extensions[cls.DISABLED_STATUS_KEY] = cls._initial_state("disabled")
            logger.warning("wan dashboard refresh worker lacks its Mist session or organization")
            return
        from src.interfaces.portals.upgrade_portal.runtime.lock import connect_lock_store

        client = connect_lock_store()  # Reuse the Redis service already used by the upgrade portal.
        if client is None:  # A worker without Redis cannot elect one collector or publish safely.
            app.extensions[cls.DISABLED_STATUS_KEY] = cls._initial_state("unavailable")
            logger.warning("wan dashboard refresh worker remains stopped because Redis is unavailable")
            return
        cache = RedisDashboardCache(client)  # Keep dashboard reads and worker writes on the same cache.
        service = WanDashboardService(session, org_id, cache=cache)  # Use only the shared Mist session.
        app.extensions[cls.SERVICE_EXTENSION_KEY] = service  # Share its local snapshot fallback with read routes.
        worker = cls(service, RedisWorkerStore(client, org_id), settings)  # Bind one process-local worker loop.
        app.extensions[cls.EXTENSION_KEY] = worker  # Expose queue and status methods to dashboard routes.
        worker.start()  # Every Gunicorn process competes for the same Redis lease.
        atexit.register(worker.stop)  # Stop the thread when this web process exits.

    @staticmethod
    def disabled_status() -> dict[str, Any]:
        """Return the safe default state for an unconfigured worker."""
        return WanDashboardWorker._initial_state("disabled")  # No timing or production approval is assumed.

    @staticmethod
    def _initial_state(status: str) -> dict[str, Any]:
        """Build a safe status envelope before any refresh has run."""
        return {
            "status": status,
            "current_phase": None,
            "completed_pages": {},
            "requested_at": None,
            "started_at": None,
            "finished_at": None,
            "last_complete_at": None,
            "next_scheduled_at": None,
            "safe_error": None,
            "stale": status != "complete",
            "queued_follow_up": False,
        }  # Never place credentials, API responses, or operator text in status.

    def start(self) -> None:
        """Start one daemon thread in this Gunicorn process."""
        if self._thread is not None and self._thread.is_alive():
            return  # A repeated blueprint callback cannot start a second local thread.
        self._thread = threading.Thread(target=self._run, name="wan-dashboard-refresh", daemon=True)
        self._thread.start()  # The Redis lease selects only one active collector across processes.

    def stop(self) -> None:
        """Stop the worker loop and wait briefly for the current action to finish."""
        self._stop.set()  # Prevent the next queue or scheduled refresh.
        if self._thread is not None:
            self._thread.join(timeout=self._settings.lease_seconds)  # Bound process shutdown by the configured lease.

    def status(self) -> dict[str, Any]:
        """Return shared status or this process's safe fallback when Redis is down."""
        shared = self._store.read_status()  # Prefer the status shared by the active worker.
        queued = self._store.has_queued()  # Observe the pending request without consuming it.
        state = shared if shared is not None else self._local_state()  # Keep the view useful during Redis outage.
        result = {key: state.get(key) for key in self.STATE_FIELDS}  # Expose only defined status fields.
        if shared is None:
            result["status"] = "stale" if result["last_complete_at"] else "unavailable"
            result["stale"] = True
            result["safe_error"] = "redis_unavailable"
        result["queued_follow_up"] = bool(result["queued_follow_up"] or queued)
        if queued and result["status"] != "running":
            result["status"] = "queued"  # Show an idle worker's pending request as queued.
        result["redis_available"] = shared is not None  # Distinguish local fallback status from shared status.
        return result  # Keep status JSON safe and bounded.

    def enqueue(self) -> str:
        """Queue one refresh without making a Mist request in the route."""
        outcome = self._store.enqueue()  # Redis coalesces all requests into one pending follow-up.
        if outcome == "queued":  # Keep a local notice when the shared queue has one item.
            self._set_local_field("requested_at", self._now())  # Record only the request time.
        return outcome  # The route maps unavailable queue state to an explicit error.

    def _run(self) -> None:
        """Acquire a distributed lease and process due or queued refreshes."""
        while not self._stop.is_set():  # The thread remains active only while its web process is alive.
            token = secrets.token_urlsafe(32)  # Use a random ownership proof that never enters logs.
            if not self._store.acquire(token, self._settings.lease_seconds):
                self._stop.wait(self.POLL_SECONDS)  # Retry after one bounded coordination pause.
                continue
            try:
                self._serve_lease(token)  # Keep the lease while one run and its coalesced follow-up finish.
            finally:
                self._store.release(token)  # Release only this process's token.

    def _serve_lease(self, token: str) -> None:
        """Process one active refresh and at most one coalesced follow-up."""
        while not self._stop.is_set():  # Continue only while this process can serve work.
            queued = self._store.take_queued()  # Atomically consume the one pending request bit.
            if queued is None:  # Redis failure blocks every collection attempt.
                return
            state = self._store.read_status() or self._local_state()  # Read shared schedule and recovery state.
            if not queued and not self._refresh_is_due(state):  # Avoid duplicate schedules across Gunicorn workers.
                return
            if not self._run_refresh(token):  # Stop after a lease, API, or Redis failure.
                return

    def _refresh_is_due(self, state: dict[str, Any]) -> bool:
        """Check the shared next-run time and recover an abandoned running state."""
        if state.get("status") == "running":  # The previous lease expired during a refresh.
            return True  # Recover immediately without trusting its incomplete data.
        next_run = state.get("next_scheduled_at")  # Every worker reads the same persisted schedule.
        if not isinstance(next_run, str):  # No completed run exists yet.
            return True  # The first configured run starts immediately.
        return self._parse_timestamp(next_run) <= datetime.now(UTC)  # Compare only parsed UTC values.

    def _run_refresh(self, token: str) -> bool:
        """Refresh all four bulk reads and publish only after complete validation."""
        lost = threading.Event()  # A failed heartbeat prevents all later requests and publication.
        heartbeat_stop = threading.Event()  # End renewal when collection and publication finish.
        heartbeat = threading.Thread(
            target=self._renew_lease, args=(token, lost, heartbeat_stop), daemon=True
        )  # Renew while one SDK request may take longer than the lease.
        heartbeat.start()  # Keep exclusive collection ownership during blocking SDK calls.
        try:
            self._begin_refresh(token, lost)  # Publish the running state before the first Mist request.
            snapshot, failure = self._service.collect_worker_snapshot(
                lambda phase, count: self._record_progress(token, lost, phase, count),
                lambda: self._check_lease(token, lost),
            )  # Use only the four existing bulk SDK reads and shared pagination.
            if failure or snapshot is None:  # A failed or incomplete dataset cannot replace prior data.
                return self._finish_failed(token, lost, failure or "incomplete_snapshot")
            if not self._check_lease(token, lost):  # Recheck ownership after the last SDK page.
                return self._finish_failed(token, lost, "worker_lease_lost")
            return self._publish_complete(token, lost, snapshot)  # Atomically replace one full snapshot value.
        except (OSError, TimeoutError, TypeError, ValueError, requests.RequestException, redis.RedisError) as error:
            logger.error("wan dashboard refresh failed (%s)", type(error).__name__)  # Exclude exception text.
            return self._finish_failed(token, lost, "worker_error")
        finally:
            heartbeat_stop.set()  # Stop the lease thread after each refresh outcome.
            heartbeat.join(timeout=max(1.0, self._settings.lease_seconds))  # Bound heartbeat shutdown.

    def _begin_refresh(self, token: str, lost: threading.Event) -> None:
        """Publish a safe running state and preserve the last complete timestamp."""
        previous = self._store.read_status() or self._local_state()  # Keep last-success evidence across runs.
        state = self._initial_state("running")  # Start a new result without reusing old progress.
        state.update(
            started_at=self._now(),
            last_complete_at=previous.get("last_complete_at"),
            next_scheduled_at=self._schedule_time(),
        )  # Preserve the prior snapshot time and establish one shared next-run time.
        self._set_state(state)  # Keep local progress available during a Redis outage.
        if not self._store.write_status(token, state):  # A lost lease stops before the first API request.
            lost.set()

    def _record_progress(self, token: str, lost: threading.Event, phase: str, count: int) -> None:
        """Store the active bulk-read phase and its completed page count."""
        if lost.is_set():  # Do not report progress after the lease has failed.
            return
        state = self._local_state()  # Keep the state update local before Redis confirms it.
        pages = dict(state["completed_pages"])  # Avoid mutating a dictionary held by another route thread.
        pages[phase] = count  # Count only the fully validated pages from this read.
        state.update(current_phase=phase, completed_pages=pages, status="running")
        self._set_state(state)  # Make a process-local progress result available to the status route.
        if not self._store.write_status(token, state):  # Do not continue collection after a state write failure.
            lost.set()

    def _publish_complete(self, token: str, lost: threading.Event, snapshot: dict[str, Any]) -> bool:
        """Write the complete overview and success state under the current lease."""
        finished = self._now()  # Record one UTC completion time for data and status.
        state = self._local_state()  # Preserve all completed page counts.
        state.update(
            status="complete",
            current_phase=None,
            finished_at=finished,
            last_complete_at=snapshot["collected_at"],
            next_scheduled_at=self._schedule_time(),
            safe_error=None,
            stale=False,
        )  # Mark the view current only after all pages passed.
        if lost.is_set():
            return self._finish_failed(token, lost, "worker_lease_lost")
        published = self._store.publish_snapshot(token, snapshot, state)
        if published is None:
            return self._finish_failed(token, lost, "redis_unavailable")
        if not published:
            return self._finish_failed(token, lost, "worker_lease_lost")
        self._service.remember_worker_snapshot(snapshot)  # Keep one bounded local outage fallback.
        self._set_state(state)  # Update the local status only after Redis publication succeeds.
        logger.info("wan dashboard refresh completed")  # Record the successful snapshot action.
        logger.debug("wan dashboard refresh completed with %s overview rows", len(snapshot["data"]))
        return True

    def _finish_failed(self, token: str, lost: threading.Event, failure: str) -> bool:
        """Keep the prior snapshot and publish a safe stale failure state."""
        state = self._local_state()  # Retain validated page counts for operator diagnosis.
        state.update(
            status="failed",
            current_phase=state.get("current_phase"),
            finished_at=self._now(),
            next_scheduled_at=self._schedule_time(),
            safe_error=self._safe_error(failure),
            stale=True,
        )  # Keep the last complete timestamp and never expose response bodies.
        self._set_state(state)  # Retain a local status if Redis also failed.
        if not lost.is_set():  # A lease owner may write status but never data after failure.
            self._store.write_status(token, state)
        logger.warning("wan dashboard refresh stopped with status %s", state["safe_error"])
        return False

    def _renew_lease(self, token: str, lost: threading.Event, stop: threading.Event) -> None:
        """Renew the Redis lease while the current refresh is active."""
        delay = max(0.2, self._settings.lease_seconds / self.HEARTBEAT_DIVISOR)
        while not stop.wait(delay):  # Sleep only while the current run still needs ownership.
            if not self._store.renew(token, self._settings.lease_seconds):
                lost.set()  # Stop page collection after one failed renewal.
                return

    def _check_lease(self, token: str, lost: threading.Event) -> bool:
        """Renew the lease before each SDK page and reject a lost owner."""
        if lost.is_set() or not self._store.renew(token, self._settings.lease_seconds):
            lost.set()  # Prevent the next Mist request and all snapshot publication.
            return False
        return True

    def _schedule_time(self) -> str:
        """Return the next configured refresh time in ISO 8601 UTC."""
        next_run = datetime.now(UTC) + timedelta(seconds=self._settings.interval_seconds)
        return next_run.isoformat()  # Keep the schedule shared and independent of local clocks.

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        """Parse one stored schedule value and fail closed on malformed state."""
        try:
            parsed = datetime.fromisoformat(value)  # Read the stored ISO 8601 UTC timestamp.
        except ValueError:
            return datetime.min.replace(tzinfo=UTC)  # Invalid state causes one safe refresh attempt.
        if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
            return datetime.min.replace(tzinfo=UTC)  # Reject timezone-naive or non-UTC schedules.
        return parsed  # Use only a timezone-aware UTC time.

    def _set_state(self, state: dict[str, Any]) -> None:
        """Replace local status under a lock for concurrent route reads."""
        with self._state_guard:  # Prevent the route from reading a changing progress dictionary.
            self._state = dict(state)  # Keep each snapshot independent from later updates.

    def _local_state(self) -> dict[str, Any]:
        """Return a copy of the process-local refresh status."""
        with self._state_guard:  # Protect shared in-memory state.
            return dict(self._state)  # Do not expose the worker's mutable status dictionary.

    def _set_local_field(self, name: str, value: Any) -> None:
        """Update one safe local status field under the state lock."""
        with self._state_guard:  # Keep request and worker state updates atomic.
            self._state[name] = value  # Store only values defined by the status contract.

    @staticmethod
    def _safe_error(failure: str) -> str:
        """Allow only bounded internal failure codes in the operator response."""
        allowed = {
            "rate_limited",
            "worker_lease_lost",
            "incomplete_snapshot",
            "malformed_response",
            "repeated_page",
            "worker_error",
            "redis_unavailable",
        }  # Do not return exception messages, URLs, tokens, or raw API response text.
        return failure if failure in allowed or re.fullmatch(r"http_(?:[0-9]{3}|unknown)", failure) else "worker_error"

    @staticmethod
    def _now() -> str:
        """Return the current UTC timestamp in ISO 8601 form."""
        return datetime.now(UTC).isoformat()  # Keep all status timestamps explicit.
