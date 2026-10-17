"""Refresh WAN snapshots from one Redis-elected portal worker."""

from __future__ import annotations

import logging
import secrets
import sqlite3
from threading import Event, Thread

import redis
from arango.exceptions import ArangoError
from redis.exceptions import RedisError
from requests.exceptions import RequestException

from src.interfaces.portals.wan_performance.collection.live_service import LiveService

logger = logging.getLogger(__name__)


class WorkerLease:
    """Coordinate one refresh owner across portal worker processes."""

    LEASE_KEY = "misthelper:wan:v1:worker:{org_id}"
    LEASE_SECONDS = 600
    RENEW_SCRIPT = """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('EXPIRE', KEYS[1], ARGV[2])
    end
    return 0
    """
    RELEASE_SCRIPT = """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('DEL', KEYS[1])
    end
    return 0
    """

    def __init__(self, client: redis.Redis, org_id: str) -> None:
        """Store the configured Redis client and one opaque ownership token."""
        self.client = client
        self.key = self.LEASE_KEY.format(org_id=org_id)
        self.token = secrets.token_hex(32)
        self.owned = False

    def acquire(self) -> bool:
        """Claim the shared worker lease without replacing another process."""
        logger.info("Attempt WAN background worker election.")
        try:
            self.owned = bool(self.client.set(self.key, self.token, nx=True, ex=self.LEASE_SECONDS))
        except RedisError:
            logger.exception("WAN background worker election failed.")
            self.owned = False
        logger.debug("WAN background worker election owned=%s.", self.owned)
        return self.owned

    def renew(self) -> bool:
        """Keep the same process as owner while its bounded refresh loop runs."""
        if not self.owned:
            return False
        logger.info("Renew the WAN background worker lease.")
        try:
            self.owned = self.client.eval(self.RENEW_SCRIPT, 1, self.key, self.token, self.LEASE_SECONDS) == 1
        except RedisError:
            logger.exception("WAN background worker lease renewal failed.")
            self.owned = False
        logger.debug("WAN background worker lease renewed=%s.", self.owned)
        return self.owned

    def release(self) -> None:
        """Remove only the lease that still belongs to this process."""
        if not self.owned:
            return
        logger.info("Release the WAN background worker lease.")
        try:
            self.client.eval(self.RELEASE_SCRIPT, 1, self.key, self.token)
        except RedisError:
            logger.exception("WAN background worker lease release failed.")
        finally:
            self.owned = False
        logger.debug("WAN background worker lease release completed.")


class WanBackgroundRefreshWorker:
    """Run read-only refreshes under shared admission and a distributed lease."""

    REFRESH_INTERVAL_SECONDS = 300
    RETRY_INTERVAL_SECONDS = 10
    STOP_TIMEOUT_SECONDS = 65
    REFRESH_ERRORS = (
        ArangoError,
        ConnectionError,
        KeyError,
        OSError,
        RedisError,
        RequestException,
        sqlite3.Error,
        TypeError,
        ValueError,
    )

    def __init__(self, service: LiveService) -> None:
        """Use the same service, store, and Mist session as the live portal."""
        self.service = service
        self.stop_event = Event()
        self.lease = WorkerLease(service.store.client, service.org_id)
        self.thread: Thread | None = None

    def start(self) -> None:
        """Start one daemon thread for this application process."""
        if self.thread is not None and self.thread.is_alive():
            return
        logger.info("Start the WAN background refresh worker.")
        self.thread = Thread(target=self._run, name="wan-background-refresh", daemon=True)
        self.thread.start()
        logger.debug("WAN background refresh worker started.")

    def stop(self) -> None:
        """Request worker shutdown and wait for the bounded API timeout."""
        logger.info("Stop the WAN background refresh worker.")
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=self.STOP_TIMEOUT_SECONDS)
        if self.thread is not None and self.thread.is_alive():
            logger.warning("WAN worker still owns its expiring lease during shutdown.")
        logger.debug("WAN background refresh worker shutdown requested.")

    def _run(self) -> None:
        """Refresh only as the Redis-elected process and release ownership on exit."""
        try:
            while not self.stop_event.is_set():
                acquired = self.lease.renew() if self.lease.owned else self.lease.acquire()
                if acquired:
                    self._refresh()
                    self.lease.renew()
                delay = self.REFRESH_INTERVAL_SECONDS if acquired else self.RETRY_INTERVAL_SECONDS
                if self.stop_event.wait(delay):
                    break
        finally:
            self.lease.release()

    def _refresh(self) -> None:
        """Use the existing service so cooldown and request admission remain shared."""
        logger.info("Run the scheduled read-only WAN snapshot refresh.")
        try:
            self.service.refresh()
        except self.REFRESH_ERRORS:
            logger.exception("The scheduled WAN snapshot refresh failed.")
            return
        logger.debug("Scheduled WAN snapshot refresh completed.")
