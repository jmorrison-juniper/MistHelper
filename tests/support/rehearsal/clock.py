"""The one time source of a rehearsal run.

Why:
    ``contracts/rehearsal-clock.md`` names four time seats in the shipped code.
    A rehearsal fills all four with one object, so the phase deadline and the
    device wait never disagree by a single second.

    The harness patches no ``time`` module. A process wide patch reaches a
    thread that another test started, and
    ``tests/unit/device/test_ap_profile_migration_manager.py`` records that
    exact fault. An injected seat reaches the run under test and nothing else.
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime

logger = logging.getLogger(__name__)  # The module logger, so each move carries this name.

# WHY: A fixed start keeps every run the same on every worker. The value is
# 2026-01-01T00:00:00Z, which is far from a leap second and far from an epoch
# rollover, so no reading of the suite depends on the day that the suite ran.
START_EPOCH_SECONDS: float = 1767225600.0


class RehearsalClock:
    """A driven clock that fills the four time seats of the shipped code.

    Why:
        The settle gate waits 60 seconds and an access point waits 120 seconds.
        A real wait would cost the suite more than its whole budget. This clock
        moves on demand, so a 60 second window costs no real time at all.

    Attributes:
        None that a caller reads. Every member is private behind a method.
    """

    def __init__(self, start: float = START_EPOCH_SECONDS) -> None:
        """Create one clock at a fixed reading.

        Args:
            start: The first reading in epoch seconds.
        """
        self._reading = float(start)  # The current reading, in epoch seconds, as the gate reads it.
        self._guard = threading.Lock()  # Protects the reading, because the driver runs on its own thread.
        self._sleeps: list[float] = []  # Each interval the poll loop asked for, so a test can read the cadence.

    def now(self) -> float:
        """Return the present reading in epoch seconds.

        Why:
            ``SettleGate`` compares this value against the ``last_seen`` field
            of a statistics record, and that field also holds epoch seconds.

        Returns:
            The reading as a float.
        """
        with self._guard:  # The test thread reads while the driver thread writes.
            return self._reading  # A float copy leaves the caller nothing to mutate.

    def sleep(self, seconds: float) -> None:
        """Move the reading forward and record the interval.

        Why:
            The phase gate sleeps one poll interval between rounds. The
            rehearsal must move the same distance and wait no real time.

        Args:
            seconds: The interval that the caller asked to wait.
        """
        logger.info("Rehearsal clock sleeps %s seconds", seconds)  # The action, before it happens.
        step = max(0.0, float(seconds))  # A negative interval would move the reading backwards.
        with self._guard:  # One writer at a time keeps the reading whole.
            self._reading += step  # The sleep lands as a move and costs no real time.
            self._sleeps.append(step)  # The record proves the cadence of the poll loop.
            reading = self._reading  # Read inside the lock, so the log line matches the move.
        logger.debug("Rehearsal clock reads %s after the sleep", reading)  # The result of the action.

    def advance(self, seconds: float) -> None:
        """Move the reading forward with no sleep record.

        Why:
            A test places the start of a run before the driver runs. That move
            is not a poll round, so it must not enter the sleep record.

        Args:
            seconds: The distance to move.
        """
        logger.info("Rehearsal clock advances %s seconds", seconds)  # The action, before it happens.
        step = max(0.0, float(seconds))  # Rule 4 of the contract forbids a backwards move.
        with self._guard:  # The same guard, because the driver thread may read at this moment.
            self._reading += step  # The move lands with no entry in the sleep record.
            reading = self._reading  # Read inside the lock, so the log line matches the move.
        logger.debug("Rehearsal clock reads %s after the advance", reading)  # The result of the action.

    def now_text(self) -> str:
        """Return the present reading as an ISO stamp in UTC.

        Why:
            ``RunDriverDeps.clock`` needs the ``Clock`` protocol of
            ``driver.py:244``. That protocol declares this one method, and the
            run record stamps every phase with it.

        Returns:
            The reading as ISO 8601 text in UTC.
        """
        stamp = datetime.fromtimestamp(self.now(), tz=UTC).isoformat()  # One reading, rendered two ways.
        logger.debug("Rehearsal clock renders the stamp %s", stamp)  # The rendered result of the read.
        return stamp  # The driver writes this text into the run record.

    def sleeps(self) -> tuple[float, ...]:
        """Return every interval that a caller passed to ``sleep``.

        Why:
            The cadence test reads this record and proves that the poll loop
            asked for the shipped poll interval and for nothing else.

        Returns:
            The recorded intervals in the order that the callers asked for them.
        """
        with self._guard:  # The driver thread appends while the test thread reads.
            return tuple(self._sleeps)  # A tuple copy leaves the record safe from the caller.
