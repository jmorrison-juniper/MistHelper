"""A ``time.sleep`` spy that records only the calls of one thread.

Why this module exists
----------------------
Every MistHelper module binds the clock with ``import time``. That statement
binds the one shared ``time`` module object, not a private copy. So a patch
target that looks module-scoped is global in fact::

    patch("src.api.api_fetch_utils.time.sleep")

``unittest.mock.patch`` splits that target on the last dot, resolves the shared
``time`` module, and sets ``sleep`` on it. The replacement reaches every thread
in the interpreter. A daemon thread that an earlier test left running then adds
its own interval to the record. That extra call shifts every index and breaks
every exact count.

The failure is real. Continuous integration run 31969418423 failed the pytest
gate on pull request #1820, a change that only raises the ruff version. A
foreign 30-second interval from a leaked heartbeat thread entered a sleep
record and moved the value the test read.

The repair
----------
:class:`ThreadScopedSleepSpy` records the owning thread at build time. The spy
drops a call that arrives on any other thread, so a leaked thread can no longer
change what a test observes. The spy counts the dropped calls, which lets a
test assert on the guard itself.

Usage
-----
Pass the spy to ``patch`` through ``new``, then read the same attributes a
``MagicMock`` offers::

    spy = ThreadScopedSleepSpy()
    with patch("src.api.api_fetch_utils.time.sleep", new=spy):
        APIFetchUtils.retry_one_item(...)
    spy.assert_called_once()
"""

from __future__ import annotations

import logging
import threading
from typing import Any
from unittest.mock import call

logger = logging.getLogger(__name__)  # Module logger, per issue #1793.

__all__ = ["ThreadScopedSleepSpy"]


class ThreadScopedSleepSpy:
    """Record the ``time.sleep`` calls that come from one thread.

    The spy binds the thread that builds it. It records a call from that
    thread. It drops a call from any other thread and counts the drop.
    """

    def __init__(self, name: str = "sleep") -> None:
        """Bind the calling thread as the owner of this spy.

        Args:
            name: A label for the log lines and the assertion messages.
        """
        logger.debug("Building a thread-scoped sleep spy named %s", name)  # Trace the build.
        self._name = name  # Keep the label for every message this spy raises.
        self._owner_thread_id = threading.get_ident()  # Bind the owner at build time, not at call time.
        self._calls: list[Any] = []  # Hold one mock call object for each owned call.
        self._foreign_call_count = 0  # Count the calls this spy drops.
        logger.debug("Spy %s owns thread %d", name, self._owner_thread_id)  # Record the owner.

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """Stand in for ``time.sleep`` and record the call.

        The spy never sleeps, because a unit test must not wait.
        """
        if threading.get_ident() != self._owner_thread_id:  # Reject a call from a foreign thread.
            self._foreign_call_count += 1  # Count the drop so a test can assert on the guard.
            logger.debug(
                "Spy %s dropped a foreign interval %s from thread %d",
                self._name,
                args,
                threading.get_ident(),
            )  # Name the thread that leaked, which speeds up the next diagnosis.
            return  # Drop the call. The record stays as the owning thread built it.
        self._calls.append(call(*args, **kwargs))  # Record the owned call in mock call form.

    @property
    def call_args_list(self) -> list[Any]:
        """Return the owned calls in the order the owner made them."""
        return list(self._calls)  # Copy the list, so a caller cannot edit the record.

    @property
    def call_count(self) -> int:
        """Return the count of owned calls."""
        return len(self._calls)  # The foreign calls never enter this list.

    @property
    def foreign_call_count(self) -> int:
        """Return the count of calls this spy dropped from other threads."""
        return self._foreign_call_count  # A non-zero value proves a thread leaked.

    @property
    def intervals(self) -> list[Any]:
        """Return the first positional argument of each owned call."""
        return [entry.args[0] for entry in self._calls if entry.args]  # Skip a call with no interval.

    def assert_called_once(self) -> None:
        """Fail unless the owner called the spy exactly one time."""
        if self.call_count != 1:  # Compare against the owned count only.
            raise AssertionError(f"expected {self._name} to be called once, got {self.call_count}: {self.intervals}")

    def assert_called_once_with(self, *args: Any, **kwargs: Any) -> None:
        """Fail unless the owner made exactly one call with these arguments."""
        self.assert_called_once()  # Check the count first, because it gives the clearer message.
        expected = call(*args, **kwargs)  # Build the call the caller expects.
        if self._calls[0] != expected:  # Compare the one recorded call against it.
            raise AssertionError(f"expected {self._name} call {expected}, got {self._calls[0]}")

    def assert_not_called(self) -> None:
        """Fail if the owner called the spy at all."""
        if self._calls:  # A foreign call can no longer trigger this failure.
            raise AssertionError(f"expected no {self._name} call, got {self.intervals}")

    def reset_mock(self) -> None:
        """Clear the record and the drop count, and keep the owner."""
        logger.debug("Resetting the spy %s record", self._name)  # Trace the reset.
        self._calls.clear()  # Drop the recorded calls.
        self._foreign_call_count = 0  # Drop the foreign count with them.
