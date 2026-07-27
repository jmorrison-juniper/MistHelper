"""Frozen dataclass that groups one systematic-test menu option's identity.

``_systematic_test_run_option`` in ``MistHelper.py`` took 7 parameters, exceeding
the 5-Item Rule's max-5 limit. The three values that describe the menu option
under test (its number, its callable, and its display description) are grouped
here so the function keeps its per-run arguments (emitter, position index, total
count, fast flag) and drops to 5 parameters.

The class name is deliberately NOT ``Test``-prefixed so pytest does not try to
collect it as a test case.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/470
"""

from __future__ import annotations  # Enable PEP 604 union syntax on older runtimes.

from collections.abc import Callable  # Modern home for the Callable type alias.
from dataclasses import dataclass  # The standard library dataclass decorator.
from typing import Any  # The menu callable returns Any and takes arbitrary kwargs.


@dataclass(frozen=True, slots=True)
class SystematicTestOption:
    """Identity of a single menu option exercised by the systematic test harness."""

    option: str  # Menu option number being tested (for example "11").
    func: Callable[..., Any]  # The menu action callable invoked for this option.
    description: str  # Human-readable option description shown in progress output.
