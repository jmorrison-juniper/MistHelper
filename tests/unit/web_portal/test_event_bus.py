"""Unit tests for ``PortalEventBus`` heartbeat lifecycle.

Why:
    The heartbeat thread had no test and no caller for ``stop()``. It slept on
    a bare ``time.sleep(30)``, so a stop request waited for the current sleep
    to finish, and ``web_portal/app.py`` never asked it to stop at all. The
    thread therefore outlived every process that built the app.

    A leaked thread is not only an operational gap. Because it keeps calling
    ``time.sleep``, it also reaches any test that patches ``time.sleep``, which
    is how it broke the AP migration pacing gate (issue #1822).

    The second group of tests covers the dropped-event accounting. Before the
    fix for instance 3 of issue #1924, ``_enqueue_event`` discarded two events
    with no record. It removed the oldest event to free a slot, and it also
    discarded the new event when the free slot disappeared. An operator saw an
    incomplete live feed and received no indication that a gap existed.
"""

# WHY: forward-refs keep the annotations readable under pytest introspection.
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterator

import pytest

from web_portal.services.event_bus import PortalEventBus


def _fill_subscriber_queue(instance: PortalEventBus, count: int) -> None:
    """Publish ``count`` numbered events, so a bounded queue reaches its limit.

    Why:
        Each event carries a sequence number. A later assertion reads those
        numbers to prove which event the bus evicted and which one survived.
    """
    for sequence in range(count):
        instance.publish("log", {"seq": sequence})  # Publish reaches every unfiltered subscriber.


def _drain_subscriber(instance: PortalEventBus, subscriber_id: str) -> list[int]:
    """Return every sequence number that stayed in a subscriber queue.

    Why:
        A counter alone does not prove the eviction order. Reading the
        survivors proves that the bus kept the newest event. It also proves
        that the bus removed the oldest one.
    """
    survivors: list[int] = []
    while True:
        event = instance.poll(subscriber_id, timeout=0)  # A zero timeout returns None when empty.
        if event is None:
            return survivors
        survivors.append(event["data"]["seq"])  # Collect the order in which the subscriber reads.


def _drop_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return every WARNING line that reports a dropped server-sent event.

    Why:
        The bus also logs unrelated warnings. Filtering on the drop wording
        keeps the count assertions honest.
    """
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING and "dropped" in r.getMessage()]


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
    assert "dropped_events" in event["data"], "the heartbeat MUST report the dropped-event total"


def test_a_full_queue_counts_the_dropped_event(bus: PortalEventBus) -> None:
    """A publish into a full queue MUST increase the drop counter.

    Why:
        This is instance 3 of issue #1924. The old code removed the oldest
        event and kept no record, so the feed lost data with no signal.
    """
    subscriber_id = bus.subscribe()
    _fill_subscriber_queue(bus, bus.QUEUE_MAX_SIZE)  # Fill the queue to its bound.
    assert bus.dropped_event_count == 0, "a queue below its bound MUST NOT drop an event"

    bus.publish("log", {"seq": bus.QUEUE_MAX_SIZE})  # This event has no free slot.

    assert bus.dropped_event_count == 1, "the bus MUST count the event it discarded"
    stats = bus.drop_stats()
    assert stats["evicted_oldest"] == 1, f"expected one evicted event, got {stats!r}"
    assert stats["rejected_new"] == 0, f"the newest event MUST survive, got {stats!r}"
    assert len(_drain_subscriber(bus, subscriber_id)) == bus.QUEUE_MAX_SIZE, "the bound MUST hold"


def test_the_newest_event_survives_and_the_oldest_is_evicted(bus: PortalEventBus) -> None:
    """The bus MUST keep the newest event and remove the oldest one.

    Why:
        The method docstring states that intent. A counter alone does not prove
        it, so this test reads the surviving events in order.
    """
    subscriber_id = bus.subscribe()
    _fill_subscriber_queue(bus, bus.QUEUE_MAX_SIZE)
    newest = bus.QUEUE_MAX_SIZE  # The sequence number of the event that arrives last.

    bus.publish("log", {"seq": newest})

    survivors = _drain_subscriber(bus, subscriber_id)
    assert len(survivors) == bus.QUEUE_MAX_SIZE, f"the queue MUST stay at its bound, got {len(survivors)}"
    assert survivors[0] == 1, f"event 0 MUST be the evicted one, but the queue starts at {survivors[0]}"
    assert survivors[-1] == newest, f"the newest event MUST survive, but the queue ends at {survivors[-1]}"


def test_the_first_drop_reaches_the_log(bus: PortalEventBus, caplog: pytest.LogCaptureFixture) -> None:
    """The first dropped event MUST produce a WARNING line.

    Why:
        A private counter that nothing reports is not a record. The operator
        needs one immediate signal that the live feed lost data.
    """
    subscriber_id = bus.subscribe()
    _fill_subscriber_queue(bus, bus.QUEUE_MAX_SIZE)

    with caplog.at_level(logging.WARNING):
        bus.publish("log", {"seq": bus.QUEUE_MAX_SIZE})

    lines = _drop_warnings(caplog)
    assert len(lines) == 1, f"the first drop MUST log exactly one warning, got {lines!r}"
    assert "server-sent event" in lines[0], f"the warning MUST name the lost item, got {lines[0]!r}"
    assert lines[0].isascii(), f"a log line MUST stay ASCII only, got {lines[0]!r}"
    assert bus.poll(subscriber_id, timeout=0) is not None, "the subscriber MUST still hold events"


def test_a_burst_of_drops_does_not_flood_the_log(bus: PortalEventBus, caplog: pytest.LogCaptureFixture) -> None:
    """A long burst MUST log far fewer lines than it drops events.

    Why:
        A full queue overflows again on the next event. One line for each drop
        would fill the log with identical warnings, which is the noise defect
        that issue #1766 already records.
    """
    burst_size = 500  # A burst large enough that a per-drop line would be obvious.
    bus.subscribe()
    _fill_subscriber_queue(bus, bus.QUEUE_MAX_SIZE)

    with caplog.at_level(logging.WARNING):
        _fill_subscriber_queue(bus, burst_size)  # Every one of these events evicts an older event.

    lines = _drop_warnings(caplog)
    assert bus.dropped_event_count == burst_size, f"the bus MUST count all {burst_size} drops"
    # WHY: the threshold doubles after each report, so the count grows with the
    # base-2 logarithm of the burst. Ten percent is a generous ceiling.
    assert len(lines) <= burst_size // 10, f"{len(lines)} warnings for {burst_size} drops floods the log"
    assert len(lines) >= 1, "a burst MUST still leave a record of the loss"


def test_stop_reports_the_final_drop_total(bus: PortalEventBus, caplog: pytest.LogCaptureFixture) -> None:
    """``stop`` MUST report the true drop total one time.

    Why:
        The growing interval can leave the last drops unreported. The summary
        guarantees that the operator learns the real size of the gap.
    """
    bus.subscribe()
    _fill_subscriber_queue(bus, bus.QUEUE_MAX_SIZE + 3)  # Three events past the bound drop.

    with caplog.at_level(logging.WARNING):
        caplog.clear()  # Drop the per-drop records, so only the summary remains.
        bus.stop()

    lines = [line for line in _drop_warnings(caplog) if "in total" in line]
    assert len(lines) == 1, f"stop() MUST log exactly one summary, got {lines!r}"
    assert "3 server-sent event(s) in total" in lines[0], f"the summary MUST name the total, got {lines[0]!r}"
