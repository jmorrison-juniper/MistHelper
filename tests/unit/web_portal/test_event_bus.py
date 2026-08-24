"""Unit tests for ``PortalEventBus`` heartbeat lifecycle.

Why:
    The heartbeat thread had no test and no caller for ``stop()``. It slept on
    a bare ``time.sleep(30)``, so a stop request waited for the current sleep
    to finish, and ``web_portal/app.py`` never asked it to stop at all. The
    thread therefore outlived every process that built the app.

    A leaked thread is not only an operational gap. Because it keeps calling
    ``time.sleep``, it also reaches any test that patches ``time.sleep``, which
    is how it broke the AP migration pacing gate (issue #1822).
"""

# WHY: forward-refs keep the annotations readable under pytest introspection.
from __future__ import annotations

import threading
import time
from collections.abc import Iterator

import pytest

from web_portal.services.event_bus import PortalEventBus


def _heartbeat_threads() -> set[threading.Thread]:
    """Return every live thread that carries the heartbeat name.

    Why:
        ``tests/e2e/conftest.py`` builds the portal app, which starts the
        module-level bus. That thread stays alive for the rest of the session,
        so a bare read of ``threading.enumerate`` finds a foreign thread. Each
        caller subtracts a baseline, so an assertion reads only its own bus.
        This is the same scoping rule the AP migration sleep spies use.
    """
    return {t for t in threading.enumerate() if t.name == "portal-heartbeat"}


@pytest.fixture
def bus() -> Iterator[PortalEventBus]:
    """Return an event bus, and stop it after the test.

    Why:
        A test that fails before its own ``stop()`` would otherwise leak the
        very thread these tests exist to prevent.
    """
    instance = PortalEventBus()
    yield instance
    instance.stop()  # WHY: idempotent, so a stopped bus tolerates this.


def test_stop_ends_the_heartbeat_thread_before_it_returns(bus: PortalEventBus) -> None:
    """``stop`` MUST NOT return while the heartbeat thread still runs.

    Why:
        The loop waits ``HEARTBEAT_INTERVAL_S`` (30) seconds between beats. A
        bool flag cannot interrupt that wait, so the thread stayed alive for
        up to 30 seconds after a stop request. An interruptible wait plus a
        join makes the stop observable.
    """
    bus.start()
    thread = bus._heartbeat_thread
    assert thread is not None, "start() MUST create a heartbeat thread"
    assert thread.is_alive(), "the heartbeat thread MUST be running after start()"

    started = time.perf_counter()
    bus.stop()
    elapsed = time.perf_counter() - started

    assert not thread.is_alive(), "stop() returned while the heartbeat thread was still running"
    # WHY: the wait is interruptible, so the stop MUST NOT approach the 30 s cadence.
    assert elapsed < 5.0, f"stop() took {elapsed:.2f} s; the heartbeat wait is not interruptible"


def test_stop_leaves_no_named_heartbeat_thread(bus: PortalEventBus) -> None:
    """No ``portal-heartbeat`` thread MUST survive a stop.

    Why:
        This is the leak that reached an unrelated test suite. Reading the
        live thread list catches an orphan that a stale handle would hide.
    """
    foreign = _heartbeat_threads()  # WHY: an earlier test can leave a bus running.

    bus.start()
    bus.stop()

    survivors = [t.name for t in _heartbeat_threads() - foreign]
    assert survivors == [], f"a heartbeat thread survived stop(): {survivors!r}"


def test_start_twice_does_not_create_a_second_thread(bus: PortalEventBus) -> None:
    """A second ``start`` MUST NOT add another heartbeat thread.

    Why:
        The old ``start`` overwrote the thread handle unconditionally. Two
        threads then published every heartbeat twice, and ``stop`` could only
        track the newer one, so the older one leaked.
    """
    foreign = _heartbeat_threads()  # WHY: only this bus's threads belong in the count.

    bus.start()
    first_thread = bus._heartbeat_thread

    bus.start()

    assert bus._heartbeat_thread is first_thread, "start() MUST be idempotent while running"
    running = _heartbeat_threads() - foreign
    assert len(running) == 1, f"expected exactly one heartbeat thread, found {len(running)}"


def test_bus_restarts_after_a_stop(bus: PortalEventBus) -> None:
    """A stopped bus MUST start again.

    Why:
        ``stop`` sets the stop event. If ``start`` did not clear it, the new
        loop would exit on its first wait and the portal would send no
        heartbeat.
    """
    bus.start()
    bus.stop()

    bus.start()

    thread = bus._heartbeat_thread
    assert thread is not None and thread.is_alive(), "the bus MUST run again after a stop"


def test_stop_drops_every_subscriber(bus: PortalEventBus) -> None:
    """``stop`` MUST clear the subscriber registry.

    Why:
        Each subscriber holds a bounded queue. Keeping them after a stop would
        hold memory for connections that can no longer be served.
    """
    bus.start()
    bus.subscribe("run-1")
    bus.subscribe("run-2")

    bus.stop()

    assert bus._count_active() == 0, "stop() MUST drop every subscriber"


def test_heartbeat_publishes_on_a_short_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loop MUST publish a heartbeat once per interval.

    Why:
        The interruptible wait must still pace the beat. This test shortens
        the cadence so the assertion stays fast and hermetic.
    """
    # WHY: a short cadence keeps the test under a second without a real 30 s wait.
    monkeypatch.setattr(PortalEventBus, "HEARTBEAT_INTERVAL_S", 0.05)
    instance = PortalEventBus()
    subscriber_id = instance.subscribe()
    instance.start()
    try:
        event = instance.poll(subscriber_id, timeout=5)
    finally:
        instance.stop()

    assert event is not None, "the heartbeat MUST reach a subscriber"
    assert event["type"] == "heartbeat", f"expected a heartbeat event, got {event['type']!r}"
    assert "active_operations" in event["data"], "the heartbeat MUST report the subscriber count"
