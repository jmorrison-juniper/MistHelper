"""Controlled DNS results and clocks for tests without network access."""

from __future__ import annotations

import socket
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Condition, Event, Lock
from unittest.mock import MagicMock

import pytest

from src.foundation.persistence.db.support import host_resolver
from src.foundation.persistence.db.support.host_resolver import BoundedHostResolver, ResolverLimits

type AddressRecord = tuple[int, int, int, str, tuple[str, int] | tuple[str, int, int, int]]


class ControlledResolver:
    """Record queries and return only configured results."""

    def __init__(self) -> None:
        """Prepare an unavailable default and explicit worker controls."""
        self.calls: list[tuple[str, int | None, int, int]] = []
        self.answers: dict[str, list[AddressRecord] | Exception] = {}
        self.blocked_hosts: set[str] = set()
        self.release = Event()
        self.condition = Condition()

    def __call__(self, hostname: str, port: int | None, family: int = 0, socket_type: int = 0) -> list[AddressRecord]:
        """Record the actual query before an optional controlled wait."""
        with self.condition:
            self.calls.append((hostname, port, family, socket_type))
            self.condition.notify_all()
        if hostname in self.blocked_hosts:
            if not self.release.wait(10):
                raise TimeoutError("The controlled DNS lookup did not receive its release.")
        answer = self.answers.get(hostname, socket.gaierror(socket.EAI_NONAME, "Controlled DNS failure."))
        if isinstance(answer, Exception):
            raise answer
        return list(answer)

    def wait_for_calls(self, count: int, timeout: float = 1.0) -> bool:
        """Wait for an exact test milestone without repeated status reads."""
        with self.condition:
            return self.condition.wait_for(lambda: len(self.calls) >= count, timeout)

    @staticmethod
    def addresses(address: str = "192.0.2.10") -> list[AddressRecord]:
        """Build numeric test addresses without invoking a resolver."""
        if ":" in address:
            return [(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 0, 0, 7))]
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 0))]


class ControlledClock:
    """Advance cache time without changing real caller deadlines."""

    def __init__(self, initial: float = 100.0) -> None:
        """Use a separate monotonic domain for cache assertions."""
        self.current = initial
        self.lock = Lock()

    def __call__(self) -> float:
        """Return the controlled cache time."""
        with self.lock:
            return self.current

    def advance(self, seconds: float) -> None:
        """Move only cache time while worker waits use the real clock."""
        with self.lock:
            self.current += seconds


class ResolverHarness:
    """Own controlled resolver instances and prove complete helper cleanup."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Replace only the application resolver, not the global socket API."""
        self.monkeypatch = monkeypatch
        self.lookup = ControlledResolver()
        self.clock = ControlledClock()
        self.instances: list[tuple[BoundedHostResolver, ControlledResolver]] = []
        self.create(shared=True)

    def create(
        self,
        limits: ResolverLimits | None = None,
        lookup: ControlledResolver | None = None,
        clock: ControlledClock | None = None,
        *,
        shared: bool = False,
    ) -> BoundedHostResolver:
        """Register each test-owned pool before a controlled caller uses it."""
        controlled_lookup = lookup or self.lookup
        resolver = BoundedHostResolver(limits=limits, lookup=controlled_lookup, clock=clock or self.clock)
        self.instances.append((resolver, controlled_lookup))
        if shared:
            self.monkeypatch.setattr(host_resolver, "DEFAULT_RESOLVER", resolver)
        return resolver

    def drain(self, resolver: BoundedHostResolver) -> None:
        """Release blocked lookups and wait only for already admitted results."""
        with resolver.cache.lock:
            pending = tuple(resolver.workers.pending.values())
        for _owned, lookup in self.instances:
            lookup.release.set()
        for future in pending:
            future.result(timeout=1)
        assert resolver.resource_counts()["pending"] == 0
        assert resolver.resource_counts()["queued"] == 0

    def close(self) -> None:
        """Release every fake and prove that no worker or queued job remains."""
        for _resolver, lookup in self.instances:
            lookup.release.set()
        for resolver, _lookup in self.instances:
            resolver.close(timeout=1)
            counts = resolver.resource_counts()
            assert counts["workers"] == 0, counts
            assert counts["pending"] == 0, counts
            assert counts["queued"] == 0, counts


class ControlledSockets:
    """Record numeric TCP targets without creating a real socket."""

    def __init__(self, failures: list[Exception | None] | None = None, delay: float = 0.0) -> None:
        """Set explicit connection outcomes and an optional real bounded delay."""
        self.failures = failures or []
        self.delay = delay
        self.calls: list[tuple[int, int, int]] = []
        self.connections: list[MagicMock] = []
        self.targets: list[tuple[str, int] | tuple[str, int, int, int]] = []

    def __call__(self, family: int, socket_type: int, protocol: int) -> MagicMock:
        """Provide the context and methods that the real socket exposes."""
        self.calls.append((family, socket_type, protocol))
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.__exit__.return_value = False
        connection.connect.side_effect = self.connect
        self.connections.append(connection)
        return connection

    def connect(self, endpoint: tuple[str, int] | tuple[str, int, int, int]) -> None:
        """Respect the supplied socket budget before a configured failure."""
        index = len(self.targets)
        self.targets.append(endpoint)
        budget = self.connections[-1].settimeout.call_args.args[0]
        if self.delay:
            time.sleep(min(self.delay, budget))
        if index < len(self.failures) and self.failures[index] is not None:
            raise self.failures[index]


class ControlledPreflightCall:
    """Measure a native preflight and release the controlled blocked lookup."""

    def __init__(self, lookup: ControlledResolver) -> None:
        """Keep the release specific to the test-owned resolver."""
        self.lookup = lookup

    def measure(self, action: Callable[[], None]) -> tuple[ConnectionError | None, float, bool]:
        """Stop an unbounded baseline caller without abandoning its helper."""
        failure: ConnectionError | None = None
        completed = True
        with ThreadPoolExecutor(max_workers=1) as caller:
            started = time.monotonic()
            future = caller.submit(action)
            try:
                future.result(timeout=1.3)
            except ConnectionError as error:
                failure = error
            except TimeoutError:
                completed = False
            finally:
                elapsed = time.monotonic() - started
                self.lookup.release.set()
            try:
                future.result(timeout=1)
            except ConnectionError as error:
                failure = error
        return failure, elapsed, completed
