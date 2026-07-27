"""Lightweight per-phase wall-clock timing for the address audit (diagnostic only).

The Tier-3 resolve loop can spend 12-20 seconds per site, and it was not obvious
where that time went. :class:`PhaseTimer` accumulates wall-clock time under named
phases so the audit can log a breakdown at the end of a run (for example human-like
typing versus Nominatim rate-limit versus politeness delay versus suite-grace waits),
turning "it feels slow" into an actionable measurement.

This is deliberately tiny and dependency-free: a dict of ``label -> [count,
total_seconds]`` plus a context manager. It never raises and adds negligible
overhead, so it can stay always-on rather than behind a debug flag.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import time  # High-resolution wall-clock via perf_counter.
from collections.abc import Iterator  # Return type for the context manager.
from contextlib import contextmanager  # Build the phase() timing context manager.


class PhaseTimer:  # WHY: single-purpose timing container for audit phases
    """Accumulate wall-clock time per named phase to expose the slow stages."""

    def __init__(self) -> None:  # WHY: initialize empty phase table
        """Initialize an empty phase table."""
        self._phases: dict[str, list[float]] = {}  # label -> [count, total_seconds].

    @contextmanager
    def phase(self, label: str) -> Iterator[None]:  # WHY: context manager for timing a block
        """Time the wrapped block, adding its wall-clock duration to ``label``."""
        start = time.perf_counter()  # High-resolution start stamp.
        try:
            yield  # Run the caller's timed block.
        finally:
            self.add(label, time.perf_counter() - start)  # Always record, even if the block raised.

    def add(self, label: str, seconds: float) -> None:  # WHY: manual timing entry
        """Add a single ``seconds`` occurrence to ``label`` (safe for manual timing)."""
        slot = self._phases.setdefault(label, [0.0, 0.0])  # [count, total]. Created on first use.
        slot[0] += 1.0  # One more occurrence of this phase.
        slot[1] += max(0.0, seconds)  # Accumulate a non-negative duration (guards clock skew).

    def total(self, label: str) -> float:  # WHY: read accumulated seconds for a phase
        """Return the accumulated seconds for ``label`` (0.0 when never timed)."""
        return self._phases.get(label, [0.0, 0.0])[1]  # Total component, or zero.

    def is_empty(self) -> bool:  # WHY: cheap check before printing summary
        """Return True when no phase has been timed yet."""
        return not self._phases  # Empty table -> nothing to report.

    def summary(self) -> str:  # WHY: human-readable breakdown for end-of-run log
        """Return a human-readable breakdown sorted by total time (slowest first)."""
        if not self._phases:  # Nothing was timed this run.
            return "  (no timings recorded)"  # Explicit empty marker.
        rows = sorted(self._phases.items(), key=lambda item: item[1][1], reverse=True)  # Slowest phase first.
        width = max(len(label) for label, _ in rows)  # Align the label column to the longest label.
        lines = []  # Accumulate one formatted line per phase.
        for label, (count, total_s) in rows:  # Walk phases in slow-to-fast order.
            avg = total_s / count if count else 0.0  # Mean seconds per occurrence.
            lines.append(  # WHY: aligned single line per phase
                f"  {label:<{width}}  total={total_s:8.2f}s  n={int(count):4d}  avg={avg:6.2f}s"
            )
        return "\n".join(lines)  # One multi-line block for a single log call.
