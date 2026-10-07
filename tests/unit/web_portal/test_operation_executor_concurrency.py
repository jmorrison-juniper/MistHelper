"""Prove that concurrent first requests share one operation executor."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import Any

import pytest

from web_portal.routes import operations as operations_routes
from web_portal.services import operation as operation_service

CALLER_COUNT = 8  # Eight callers make the empty-state race visible without a large test pool.
FUTURE_TIMEOUT_SECONDS = 5.0  # A fixed bound makes a synchronization regression fail instead of hang.


class FirstReadBarrierConfig(dict[str, Any]):
    """Make each caller observe one empty executor slot before later reads."""

    def __init__(self, barrier: threading.Barrier) -> None:
        """Store the shared barrier and per-thread read state."""
        super().__init__(MENU_ACTIONS={}, APISESSION=None, ORG_ID="test-org", EVENT_BUS=None)
        self._barrier = barrier  # Coordinate only each caller's first executor read.
        self._local = threading.local()  # Keep later reads from waiting on the first-read barrier.
        self._control_first_reads = True  # Limit forced empty reads to the concurrent race phase.

    def get(self, key: str, default: Any = None) -> Any:
        """Return an empty first executor read, then use the stored mapping value."""
        if key == "OPERATION_EXECUTOR" and self._control_first_reads:  # Control reads only during the forced race.
            read_count = getattr(self._local, "executor_read_count", 0)  # Read this caller's prior access count.
            self._local.executor_read_count = read_count + 1  # Mark the access before the barrier can release.
            if read_count == 0:  # Force every caller through the same initial empty observation.
                self._barrier.wait(timeout=FUTURE_TIMEOUT_SECONDS)  # Release callers only when all are ready.
                return None  # Model the uninitialized application configuration.
        return super().get(key, default)  # Later reads observe the executor that the winner stored.

    def stop_controlling_first_reads(self) -> None:
        """Let later callers use the normal initialized fast path."""
        self._control_first_reads = False  # The race proof is complete, so no later caller waits on the barrier.


def test_get_executor_constructs_once_under_forced_race(monkeypatch: pytest.MonkeyPatch) -> None:
    """Concurrent first callers construct and receive one executor."""
    barrier = threading.Barrier(CALLER_COUNT)  # Hold each first read until every caller observes no executor.
    config = FirstReadBarrierConfig(barrier)  # Use controlled reads without a real Flask request context.
    constructed: list[object] = []  # Count each constructor call and retain its unique marker.

    def build_executor(**_dependencies: Any) -> object:
        """Return one unique marker for each constructor call."""
        marker = object()  # A unique object makes duplicate construction visible through identity checks.
        constructed.append(marker)  # Record the call before the accessor stores its result.
        return marker  # Avoid a real worker pool in this synchronization test.

    fake_app = SimpleNamespace(config=config)  # Supply only the application configuration that the accessor reads.
    monkeypatch.setattr(operations_routes, "current_app", fake_app)  # Remove Flask context from the focused test.
    monkeypatch.setattr(operation_service, "OperationExecutor", build_executor)  # Count controlled constructions.

    with ThreadPoolExecutor(max_workers=CALLER_COUNT) as pool:  # Give every caller its own test worker.
        futures = [pool.submit(operations_routes._get_executor) for _ in range(CALLER_COUNT)]  # Start together.
        results = [future.result(timeout=FUTURE_TIMEOUT_SECONDS) for future in futures]  # Bound every caller.

    assert len(constructed) == 1, f"constructed executor count: {len(constructed)}"
    assert all(result is constructed[0] for result in results)  # Every caller must receive the stored executor.
    config.stop_controlling_first_reads()  # Exercise the ordinary fast path after the forced race ends.
    assert operations_routes._get_executor() is constructed[0]  # The initialized fast path must reuse it.
    assert len(constructed) == 1, f"later access constructed executor count: {len(constructed)}"
    print(f"Executor race guard checked {CALLER_COUNT} callers and constructed {len(constructed)} executor.")
