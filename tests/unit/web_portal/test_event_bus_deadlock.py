"""Tests that the event bus never deadlocks itself through the log.

Issue #3177 recorded a permanent portal hang. The portal installs a
logging handler whose ``emit`` calls ``PortalEventBus.publish``. The bus
held its own lock while it reported a dropped event through the logging
framework, so that report re-entered ``publish`` on the same thread and
waited for a lock the thread already held.

``threading.Lock`` is not reentrant, so the wait never ended. The thread
also still held the logging handler lock, so every other thread that
wrote a log record blocked behind it. All 24 request threads stopped.

Each test below runs the dangerous path inside a worker thread with a
deadline. A deadlock shows up as a thread that never finishes, so the
tests assert on completion and never merely on a return value.
"""

import logging
import threading

import pytest

from web_portal.services.event_bus import PortalEventBus

# Seconds to wait for a path that must finish quickly. The defect never
# finishes at all, so any small value separates a pass from a deadlock.
DEADLOCK_TIMEOUT_SECONDS = 10.0


class ReentrantPublishHandler(logging.Handler):
    """A handler that publishes to the bus, matching the portal handler.

    ``_RunLogHandler.emit`` in ``web_portal/services/operation.py`` calls
    ``self._event_bus.publish(...)``. This stand-in reproduces that call
    without pulling the whole executor into the test.
    """

    def __init__(self, bus: PortalEventBus) -> None:
        """Store the bus this handler publishes into."""
        super().__init__()
        self.bus = bus  # The handler publishes every record it receives.
        self.emitted = 0  # Counts the records, so a test can prove the path ran.

    def emit(self, record: logging.LogRecord) -> None:
        """Publish the record, exactly as the portal handler does."""
        self.emitted += 1  # Record that the dangerous path ran at least once.
        self.bus.publish("log", {"run_id": "r1", "message": record.getMessage()})


@pytest.fixture
def bus():
    """Return a bus with no heartbeat thread, stopped after the test."""
    built = PortalEventBus()  # Build one bus per test, so no test shares state.
    yield built
    built.stop()  # A stop on an unstarted bus is a safe no-op.


@pytest.fixture
def publishing_handler(bus):
    """Attach a handler that publishes into the bus, and remove it after."""
    handler = ReentrantPublishHandler(bus)  # Reproduce the portal handler shape.
    bus_logger = logging.getLogger("web_portal.services.event_bus")
    bus_logger.addHandler(handler)  # The bus now logs into a handler that publishes.
    previous = bus_logger.level  # Remember the level, so the test restores it.
    bus_logger.setLevel(logging.DEBUG)  # Let every record reach the handler.
    yield handler
    bus_logger.removeHandler(handler)  # Never leave the handler on a shared logger.
    bus_logger.setLevel(previous)  # Restore the level for every later test.


def _run_with_deadline(work) -> bool:
    """Run one callable in a thread and report whether it finished in time."""
    finished = threading.Event()  # Set only when the callable returns.

    def _target():
        try:
            work()
        finally:
            finished.set()  # Signal completion even when the callable raises.

    thread = threading.Thread(target=_target, daemon=True)  # A daemon never blocks the suite.
    thread.start()
    return finished.wait(timeout=DEADLOCK_TIMEOUT_SECONDS)


def _fill_one_subscriber(bus: PortalEventBus) -> None:
    """Publish until a subscriber queue overflows and a drop is recorded."""
    # The deadlock needs a full queue, because only the eviction path reports.
    for index in range(bus.QUEUE_MAX_SIZE + 5):
        bus.publish("log", {"run_id": "r1", "message": f"filler {index}"})


def test_publishing_into_a_full_queue_never_deadlocks(bus, publishing_handler):
    """A drop report must not re-enter publish on the locked thread."""
    bus.subscribe("r1")  # One subscriber, whose queue this test fills.
    # Without the repair this call never returns, because the drop report
    # re-enters publish and waits for the lock the same thread holds.
    assert _run_with_deadline(
        lambda: _fill_one_subscriber(bus)
    ), f"publish did not finish in {DEADLOCK_TIMEOUT_SECONDS} seconds, so the bus deadlocked"


def test_the_drop_still_reaches_the_operator(bus, publishing_handler, caplog):
    """The repair keeps the warning, because a silent full queue hides a fault."""
    bus.subscribe("r1")  # One subscriber, whose queue this test fills.
    with caplog.at_level(logging.WARNING, logger="web_portal.services.event_bus"):
        assert _run_with_deadline(lambda: _fill_one_subscriber(bus))
    assert "dropped" in caplog.text  # The operator must still learn about the loss.


def test_the_drop_counters_still_rise(bus, publishing_handler):
    """The repair keeps the accounting, so the totals stay truthful."""
    bus.subscribe("r1")  # One subscriber, whose queue this test fills.
    assert _run_with_deadline(lambda: _fill_one_subscriber(bus))
    assert bus.dropped_event_count > 0  # A full queue must record every loss.


def test_a_stale_subscriber_cleanup_never_deadlocks(bus, publishing_handler):
    """The cleanup path logged inside the lock, which carries the same risk."""
    subscriber_id = bus.subscribe("r1")  # Create the subscriber the cleanup removes.
    with bus._lock:
        bus._subscribers[subscriber_id]["created_at"] = 0.0  # Age it past the cutoff.
    # Without the repair this call logs while holding the lock, and the log
    # record re-enters publish and waits for that same lock.
    assert _run_with_deadline(
        bus._cleanup_stale_subscribers
    ), f"the cleanup did not finish in {DEADLOCK_TIMEOUT_SECONDS} seconds, so the bus deadlocked"


def test_the_drop_report_leaves_the_lock_before_it_logs():
    """The source states the rule, so a later edit cannot undo it quietly."""
    import inspect

    from web_portal.services import event_bus

    source = inspect.getsource(event_bus.PortalEventBus._record_event_drop)
    # A logging call in this method is the defect itself. Catch it in the source,
    # because a future edit may add one without reproducing the full deadlock.
    assert "logger." not in source, "_record_event_drop must never call the logging framework"
    assert "_pending_drop_report" in source  # It must hand the numbers to the caller instead.
