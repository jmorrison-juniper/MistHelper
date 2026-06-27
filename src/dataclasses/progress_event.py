"""Frozen dataclasses that group TelemetryEmitter event fields.

Several ``TelemetryEmitter`` methods in ``MistHelper.py`` exceeded the 5-Item
Rule's max-5-parameter limit. These frozen dataclasses bundle the related event
fields so the ``emit_*`` method signatures stay within the limit:

- ``ProgressContext`` groups the operation identity (menu option, operation
  name, total item count) that identifies a progress event. It is shared by the
  ``progress_tick`` and ``progress_complete`` events.
- ``TestSummary`` groups the six aggregate statistics emitted once at the end of
  a ``--test`` run.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/470
"""

from __future__ import annotations  # Enable PEP 604 union syntax (str | int) on older runtimes.

from dataclasses import dataclass  # The standard library dataclass decorator.


@dataclass(frozen=True, slots=True)
class ProgressContext:
    """Operation identity shared across a single operation's progress events."""

    menu_option: str | int  # Menu option the progress event belongs to (accepts str or int form).
    operation_name: str  # Human-readable operation label (e.g. "sites", "inventory").
    total: int  # Total number of items the operation will process (the progress denominator).


@dataclass(frozen=True, slots=True)
class TestSummary:
    """The six aggregate statistics emitted once at the end of a --test run."""

    __test__ = False  # Tell pytest this is NOT a test class (it is Test-prefixed but a data carrier).

    total: int  # Total number of operations exercised in the test run.
    passed: int  # Count of operations that passed.
    failed: int  # Count of operations that failed.
    skipped: int  # Count of operations skipped (heavy / destructive / WIP).
    elapsed: float  # Wall-clock seconds the whole test run took.
    test_mode: str  # Test mode label (e.g. "systematic", "quick").
