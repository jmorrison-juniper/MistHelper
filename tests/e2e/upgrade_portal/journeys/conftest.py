"""Fixtures of the operator journey tests (issue #3200).

Why:
    Each journey records a screenshot at every step. The recorder fixture
    builds one recorder for each page that the test opens, and it writes the
    report at teardown with the real test outcome. A failed journey therefore
    keeps its evidence, which is the moment that a reader needs it most.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator  # Type the recorder factory.
from typing import Any  # Playwright objects carry no stub types here.

import pytest

from tests.e2e.upgrade_portal.journeys.evidence import JourneyRecorder  # The one evidence recorder.

OUTCOME_ATTRIBUTE = "journey_outcome"  # The item attribute that the report hook writes.


def pytest_configure(config: pytest.Config) -> None:
    """Register the journey markers, so a run reports no unknown marker."""
    config.addinivalue_line("markers", "journey: an operator journey of issue #3200 with step evidence")
    config.addinivalue_line("markers", "fresh_server: a journey that starts a job, so it needs its own portal server")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Iterator[None]:
    """Store the outcome of the test call on the item.

    Args:
        item: The test item.
        call: The call information of the phase.

    Yields:
        Control to the next hook implementation.
    """
    outcome = yield  # Let pytest build the report first.
    report = outcome.get_result()  # The report of this phase.
    if report.when == "call":  # Only the call phase decides the journey outcome.
        expected_failure = hasattr(report, "wasxfail")  # A strict xfail marks a known product defect.
        word = ("xfailed" if report.skipped else "xpassed") if expected_failure else report.outcome  # One word.
        setattr(item, OUTCOME_ATTRIBUTE, word)  # passed, failed, skipped, xfailed, or xpassed.


@pytest.fixture
def journey_recorder(request: pytest.FixtureRequest) -> Iterator[Callable[[Any, str], JourneyRecorder]]:
    """Build a recorder for each page of the test, and write each report at teardown.

    Args:
        request: The pytest request of the test.

    Yields:
        A factory that takes a page and a label and returns a recorder.
    """
    built: list[JourneyRecorder] = []  # Every recorder of this test, in build order.

    def build(page: Any, label: str = "") -> JourneyRecorder:
        """Return a new recorder for one page."""
        name = f"{request.node.name}-{label}" if label else request.node.name  # One folder for each page.
        recorder = JourneyRecorder(page, name)  # Attach the listeners before the first step.
        built.append(recorder)  # Keep it for the teardown report.
        return recorder  # The test records its steps through this object.

    yield build  # The test runs here.
    outcome = getattr(request.node, OUTCOME_ATTRIBUTE, "unknown")  # The outcome that the hook stored.
    for recorder in built:  # Write one report for each page.
        recorder.finish(str(outcome))  # A failed journey keeps its evidence too.
