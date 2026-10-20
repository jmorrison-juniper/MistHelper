"""Tests for the thread-scoped ``time.sleep`` spy.

The spy protects every sleep assertion in the suite from a leaked thread. The
tests below fail if the thread guard goes away, so they hold the guard in
place. Continuous integration run 31969418423 shows the failure the guard
prevents.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import call, patch

from tests.support.thread_scoped_sleep import ThreadScopedSleepSpy


def test_spy_records_a_call_from_the_owning_thread() -> None:
    """The owner's call reaches the record."""
    spy = ThreadScopedSleepSpy()  # Build the spy on the test thread, which becomes the owner.
    spy(0.5)  # Call it from the owner.
    assert spy.call_args_list == [call(0.5)]  # The record holds the one owned call.
    assert spy.call_count == 1  # The count agrees with the record.
    assert spy.foreign_call_count == 0  # No call was dropped.


def test_spy_drops_a_call_from_a_foreign_thread() -> None:
    """A second thread cannot enter the record."""
    spy = ThreadScopedSleepSpy()  # The test thread owns the spy.
    spy(0.5)  # Record one owned interval.
    worker = threading.Thread(target=spy, args=(30,))  # Imitate the leaked heartbeat thread.
    worker.start()  # Run the foreign call.
    worker.join(timeout=5)  # Wait for it, so the assertion reads a settled record.
    assert spy.call_args_list == [call(0.5)]  # The foreign interval never entered the record.
    assert spy.foreign_call_count == 1  # The spy counted the drop.


def test_spy_protects_an_exact_count_assertion() -> None:
    """A foreign sleep cannot break an exact-count assertion under patch."""
    spy = ThreadScopedSleepSpy()  # Own the spy on the test thread.
    with patch("time.sleep", new=spy):  # Replace the shared clock, as every suite does.
        time.sleep(0.1)  # The owner sleeps one time.
        worker = threading.Thread(target=time.sleep, args=(30,))  # A foreign thread hits the same patch.
        worker.start()  # Start it inside the patched window, which is when CI saw the leak.
        worker.join(timeout=5)  # Let it finish before the patch lifts.
    spy.assert_called_once_with(0.1)  # The exact-count assertion still holds.
    assert spy.foreign_call_count == 1  # The guard, not luck, is the reason.


def test_assert_not_called_ignores_a_foreign_thread() -> None:
    """A foreign sleep cannot fail a no-call assertion."""
    spy = ThreadScopedSleepSpy()  # Own the spy on the test thread.
    with patch("time.sleep", new=spy):  # Replace the shared clock.
        worker = threading.Thread(target=time.sleep, args=(30,))  # Only the foreign thread sleeps.
        worker.start()  # Start the foreign sleeper.
        worker.join(timeout=5)  # Wait for it to finish.
    spy.assert_not_called()  # The owner never slept, so this must pass.


def test_reset_clears_the_record_and_keeps_the_owner() -> None:
    """A reset empties the record and leaves the guard in place."""
    spy = ThreadScopedSleepSpy()  # Own the spy on the test thread.
    spy(1.0)  # Put one call in the record.
    spy.reset_mock()  # Clear it.
    assert spy.call_count == 0  # The record is empty.
    spy(2.0)  # The owner can still record after a reset.
    assert spy.intervals == [2.0]  # The owner still owns the spy.
