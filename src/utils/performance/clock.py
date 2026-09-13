"""Nanosecond clocks for performance measurement.

The module gives one wall clock and one process CPU clock. Both clocks return
integer nanoseconds, because a float second loses resolution on a short span.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from types import TracebackType
from typing import Literal


@dataclass(frozen=True, slots=True)
class Elapsed:
    """Hold the measured cost of one boundary."""

    wall_ns: int  # Elapsed wall-clock nanoseconds, which include any waiting.
    cpu_ns: int  # Process CPU nanoseconds, which exclude any waiting.


class Stopwatch:
    """Measure one boundary with the wall clock and the process CPU clock.

    The class reads each clock once on entry and once on exit. It never reads a
    clock inside a loop, because that cost would enter the measurement.
    """

    __slots__ = ("_wall_start", "_cpu_start", "_elapsed", "_measure_cpu")

    def __init__(self, measure_cpu: bool = True) -> None:
        """Prepare the clock readings and the result holder.

        Why:
            The CPU clock costs more than the wall clock on Windows, so the
            level decides whether this stopwatch reads it at all.

        Args:
            measure_cpu: True to read the CPU clock beside the wall clock.
        """
        self._wall_start = 0  # Wall reading taken when the boundary starts.
        self._cpu_start = 0  # CPU reading taken when the boundary starts.
        self._elapsed: Elapsed | None = None  # Result, which the exit path sets once.
        self._measure_cpu = measure_cpu  # On Windows the CPU clock is the costly call.

    def __enter__(self) -> Stopwatch:
        """Read the selected clocks once, so one span costs at most two calls."""
        if self._measure_cpu:  # Read the CPU clock only when the level asked for it.
            self._cpu_start = time.process_time_ns()  # Read CPU first, before the work.
        self._wall_start = time.perf_counter_ns()  # Read wall last, closest to the work.
        return self  # Give the caller the handle that later holds the result.

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Read the selected clocks once and keep the result. Never hide an exception."""
        wall_end = time.perf_counter_ns()  # Read wall first, closest to the work.
        cpu_ns = 0  # Stays zero when this level does not measure process CPU time.
        if self._measure_cpu:  # Read the CPU clock only when the level asked for it.
            cpu_ns = max(0, time.process_time_ns() - self._cpu_start)  # Clamp the value.
        self._elapsed = Elapsed(
            wall_ns=max(0, wall_end - self._wall_start),  # Clamp, a clock can repeat a value.
            cpu_ns=cpu_ns,  # Report the measured CPU cost, or zero when it is not measured.
        )
        return False  # Return False so the original exception keeps propagating.

    @property
    def elapsed(self) -> Elapsed:
        """Return the measured cost, or zero when the span never ran."""
        if self._elapsed is None:  # Guard, because a caller can read before the exit runs.
            return Elapsed(wall_ns=0, cpu_ns=0)  # Report zero rather than raise inside a metric.
        return self._elapsed  # Return the frozen record, which the caller cannot mutate.
