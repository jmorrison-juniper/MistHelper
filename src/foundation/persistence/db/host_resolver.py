"""Bound database DNS callers, cache results, and retain finite worker ownership."""

from __future__ import annotations

import errno
import math
import socket
import time
from collections import OrderedDict
from collections.abc import Callable, Sequence
from concurrent.futures import Future
from dataclasses import dataclass
from queue import Empty, Queue
from threading import RLock, Thread
from typing import TypeGuard

import structlog

type AddressRecord = tuple[int, int, int, str, tuple[str, int] | tuple[str, int, int, int]]
type RawSocketAddress = tuple[str, int] | tuple[str, int, int, int] | tuple[int, bytes]
type RawAddressRecord = tuple[int, int, int, str, RawSocketAddress]
type LookupKey = tuple[str, int, int, int, int]
type LookupFunction = Callable[[str, int | None, int, int], Sequence[RawAddressRecord]]

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    """Keep failed discovery distinct from resolved socket addresses."""

    addresses: tuple[AddressRecord, ...] = ()
    error: OSError | None = None

    @staticmethod
    def is_ip_address(address: RawSocketAddress) -> TypeGuard[tuple[str, int] | tuple[str, int, int, int]]:
        """Exclude non-IP socket addresses without a type cast."""
        return isinstance(address[0], str)

    @classmethod
    def from_records(cls, records: Sequence[RawAddressRecord]) -> ResolutionResult:
        """Retain only IP records that a database TCP socket can use."""
        logger.info("database_dns_addresses_check_started", checked_addresses=len(records))
        addresses: list[AddressRecord] = []
        for family, socket_type, protocol, canonical_name, address in records:
            if family in (socket.AF_INET, socket.AF_INET6) and cls.is_ip_address(address):
                addresses.append((family, socket_type, protocol, canonical_name, address))
            else:
                logger.warning("database_dns_unsupported_address", family=family, checked_addresses=1)
        error = None if addresses else socket.gaierror(socket.EAI_NONAME, "The DNS lookup returned no IP addresses.")
        logger.debug("database_dns_addresses_check_finished", checked_addresses=len(records), addresses=len(addresses))
        return cls(tuple(addresses), error)


@dataclass(frozen=True, slots=True)
class ResolverLimits:
    """Set caller, cache, and worker limits without new environment settings."""

    timeout_seconds: float = 1.0
    cache_ttl_seconds: float = 30.0
    max_workers: int = 2
    max_cache_entries: int = 128

    def __post_init__(self) -> None:
        """Reject limits that could remove a deadline or a resource bound."""
        for name, value in (
            ("timeout_seconds", self.timeout_seconds),
            ("cache_ttl_seconds", self.cache_ttl_seconds),
        ):
            if not math.isfinite(value) or value <= 0:
                logger.error("database_dns_invalid_limit", field=name, checked_limits=1)
                raise ValueError(f"{name} must be finite and greater than zero.")
        for name, count in (("max_workers", self.max_workers), ("max_cache_entries", self.max_cache_entries)):
            if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
                logger.error("database_dns_invalid_limit", field=name, checked_limits=1)
                raise ValueError(f"{name} must be a positive integer.")


class _ResolutionCache:
    """Own finite cached results and synchronized result publication."""

    def __init__(self, limits: ResolverLimits, clock: Callable[[], float]) -> None:
        """Keep cache expiry separate from the real caller wait."""
        self.limits = limits
        self.clock = clock
        self.lock = RLock()
        self.entries: OrderedDict[LookupKey, tuple[float, ResolutionResult]] = OrderedDict()

    def get(self, key: LookupKey) -> ResolutionResult | None:
        """Return only an unexpired result and update its eviction position."""
        entry = self.entries.get(key)
        if entry is None:
            return None
        expires, result = entry
        if self.clock() >= expires:
            del self.entries[key]
            return None
        self.entries.move_to_end(key)
        return result

    def remember(self, key: LookupKey, result: ResolutionResult) -> None:
        """Preserve an existing timeout expiry when a worker finishes late."""
        if self.get(key) is not None:
            return
        expires = self.clock() + self.limits.cache_ttl_seconds
        self.entries[key] = (expires, result)
        if len(self.entries) > self.limits.max_cache_entries:
            self.entries.popitem(last=False)
        logger.debug("database_dns_result_cached", cached_queries=len(self.entries), addresses=len(result.addresses))

    def publish(
        self,
        key: LookupKey,
        future: Future[ResolutionResult],
        outcome: ResolutionResult | Exception,
        cache_result: bool,
    ) -> None:
        """Publish worker errors as errors rather than successful DNS results."""
        if isinstance(outcome, Exception):
            logger.error("database_dns_worker_error", error_type=type(outcome).__name__, checked_queries=1)
            future.set_exception(outcome)
            return
        if cache_result:
            self.remember(key, outcome)
        logger.debug("database_dns_lookup_finished", hostname=ascii(key[0]), addresses=len(outcome.addresses))
        future.set_result(outcome)


class _ResolverWorkers:
    """Reuse a finite daemon pool and admit no work beyond its worker count."""

    def __init__(self, cache: _ResolutionCache, lookup: LookupFunction | None) -> None:
        """Prepare a finite handoff queue without starting unused workers."""
        self.cache = cache
        self.lookup = lookup
        self.pending: dict[LookupKey, Future[ResolutionResult]] = {}
        self.queue: Queue[tuple[LookupKey, Future[ResolutionResult]]] = Queue(cache.limits.max_workers)
        self.threads: list[Thread] = []
        self.closed = False

    def acquire(self, key: LookupKey) -> Future[ResolutionResult] | None:
        """Share an active query or admit one within the outstanding-work limit."""
        existing = self.pending.get(key)
        if existing is not None:
            return existing
        if len(self.pending) >= self.cache.limits.max_workers:
            logger.warning("database_dns_capacity_unavailable", pending_queries=len(self.pending), checked_queries=1)
            return None
        self.threads[:] = [thread for thread in self.threads if thread.is_alive()]
        if len(self.threads) < self.cache.limits.max_workers:
            thread = Thread(target=self.run, name=f"misthelper-db-dns-{id(self):x}", daemon=True)
            try:
                thread.start()
            except RuntimeError:
                logger.exception("database_dns_worker_start_failed", checked_queries=1)
                raise
            self.threads.append(thread)
        future: Future[ResolutionResult] = Future()
        self.pending[key] = future
        logger.info("database_dns_lookup_started", hostname=ascii(key[0]), family=key[1], socket_type=key[2])
        self.queue.put_nowait((key, future))
        return future

    def run(self) -> None:
        """Serve admitted queries and leave after bounded shutdown notification."""
        while True:
            try:
                key, future = self.queue.get(timeout=0.05)
            except Empty:
                with self.cache.lock:
                    if self.closed:
                        return
                continue
            try:
                self.execute(key, future)
            finally:
                self.queue.task_done()

    def execute(self, key: LookupKey, future: Future[ResolutionResult]) -> None:
        """Keep a blocked operating system call inside its existing worker slot."""
        outcome: ResolutionResult | Exception = RuntimeError("The database DNS worker stopped before its result.")
        try:
            lookup = self.lookup or socket.getaddrinfo
            outcome = ResolutionResult.from_records(lookup(key[0], None, key[1], key[2]))
            if outcome.error is not None:
                logger.warning("database_dns_empty_result", hostname=ascii(key[0]), checked_queries=1)
        except OSError as error:
            logger.warning(
                "database_dns_failed", hostname=ascii(key[0]), error_type=type(error).__name__, checked_queries=1
            )
            outcome = ResolutionResult(error=error)
        except (UnicodeError, ValueError, RuntimeError) as error:
            logger.exception("database_dns_lookup_error", hostname=ascii(key[0]), error_type=type(error).__name__)
            outcome = error
        finally:
            with self.cache.lock:
                self.pending.pop(key, None)
                self.cache.publish(key, future, outcome, not self.closed)

    def close(self, timeout: float) -> None:
        """Stop admission and join only within one finite shutdown budget."""
        with self.cache.lock:
            self.closed = True
            threads = tuple(self.threads)
        deadline = time.monotonic() + timeout
        for thread in threads:
            thread.join(max(0.0, deadline - time.monotonic()))
        remaining = sum(thread.is_alive() for thread in threads)
        logger.debug("database_dns_workers_closed", remaining_workers=remaining)
        if remaining:
            logger.warning("database_dns_shutdown_deadline", remaining_workers=remaining)


class BoundedHostResolver:
    """Cache DNS results while each caller waits at most its configured budget.

    Workers use the operating system resolver, which has no interruptible deadline.
    At most two default daemon workers and two outstanding queries exist.
    A timed-out lookup retains its slot until the operating system call finishes.
    Both positive and negative results expire after 30 monotonic seconds by default.
    """

    def __init__(
        self,
        limits: ResolverLimits | None = None,
        lookup: LookupFunction | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Own one cache and one finite worker pool for all repeated callers."""
        self.limits = limits or ResolverLimits()
        self.cache = _ResolutionCache(self.limits, clock or time.monotonic)
        self.workers = _ResolverWorkers(self.cache, lookup)

    def resolve(
        self, hostname: str, family: int = socket.AF_UNSPEC, socket_type: int = socket.SOCK_STREAM
    ) -> ResolutionResult:
        """Resolve one port-free query with fixed default protocol and flags."""
        key = (hostname, family, socket_type, 0, 0)
        logger.info("database_dns_check_started", hostname=ascii(hostname), family=family, socket_type=socket_type)
        with self.cache.lock:
            if self.workers.closed:
                logger.error("database_dns_resolver_closed", checked_queries=1)
                raise RuntimeError("The database DNS resolver is closed.")
            cached = self.cache.get(key)
            if cached is not None:
                logger.debug("database_dns_cache_hit", hostname=ascii(hostname), addresses=len(cached.addresses))
                return cached
            future = self.workers.acquire(key)
        if future is None:
            return ResolutionResult(error=OSError(errno.EBUSY, "Database DNS worker capacity is unavailable."))
        return self._wait(key, future)

    def _wait(self, key: LookupKey, future: Future[ResolutionResult]) -> ResolutionResult:
        """Cache a caller timeout without cancelling or duplicating active work."""
        try:
            return future.result(timeout=self.limits.timeout_seconds)
        except TimeoutError:
            with self.cache.lock:
                if future.done():
                    return future.result()
                result = ResolutionResult(error=TimeoutError("The database DNS lookup exceeded its caller deadline."))
                self.cache.remember(key, result)
            logger.warning(
                "database_dns_timeout",
                hostname=ascii(key[0]),
                timeout_seconds=self.limits.timeout_seconds,
                checked_queries=1,
            )
            return result

    def resource_counts(self) -> dict[str, int]:
        """Report finite worker, outstanding-work, queue, and cache counts."""
        with self.cache.lock:
            return {
                "workers": sum(thread.is_alive() for thread in self.workers.threads),
                "pending": len(self.workers.pending),
                "queued": self.workers.queue.qsize(),
                "cached": len(self.cache.entries),
            }

    def close(self, timeout: float = 1.0) -> None:
        """Stop new work without waiting indefinitely for a blocked resolver."""
        if not math.isfinite(timeout) or timeout < 0:
            logger.error("database_dns_invalid_shutdown_timeout", checked_limits=1)
            raise ValueError("The shutdown timeout must be finite and nonnegative.")
        logger.info("database_dns_shutdown_started", timeout_seconds=timeout)
        self.workers.close(timeout)


DEFAULT_RESOLVER = BoundedHostResolver()
