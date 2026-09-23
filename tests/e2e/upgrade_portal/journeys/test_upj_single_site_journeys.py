"""Single-site operator journeys for the parity comparison of issue #3200.

Why:
    The parity matrix compares each single-site page with its multi-site
    counterpart. These journeys record each single-site stage with the same
    recorder that the multi-site journeys use, so a reader can put the two
    screenshots of one stage side by side.

    The stand-in server seeds single-site runs in states that no safe browser
    journey can create, such as a failed run or a stopped run. The journeys
    open those seeded runs directly.
"""

from __future__ import annotations

import re  # Match the page addresses of the single-site flow.
from collections.abc import Callable  # Type the recorder factory.
from typing import Any  # Playwright objects carry no stub types here.

import pytest

from tests.e2e.upgrade_portal.journeys.evidence import JourneyRecorder  # The evidence of each journey.

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")
expect = sync_api.expect  # The retrying assertion of Playwright.

MODE_PATH = "/select/mode"  # The first page of every journey.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site.
PREPARED_RUN_ID = "e2e-prepared-run-0001"  # The seeded run that waits for its confirmation.
START_READY_RUN_ID = "e2e-start-ready-run-0001"  # The seeded run that a firmware operator may start.
FAILED_RUN_ID = "e2e-failed-run-0001"  # The seeded run that already failed.
STOPPED_RUN_ID = "e2e-stopped-run-0001"  # The seeded run that the operator stopped.
LIFECYCLE_RUN_ID = "e2e-lifecycle-run-0001"  # The seeded run with the reschedule and cancel controls.
PRE_CAPTURE_ID = "e2e-capture-pre-0001"  # The seeded pre-check capture.
POST_CAPTURE_ID = "e2e-capture-post-0001"  # The seeded post-check capture.
OK_STATUS = 200  # The status of a page that rendered.

pytestmark = pytest.mark.journey  # Every test of this file is an operator journey.


def visit(page: Any, recorder: JourneyRecorder, path: str, name: str) -> None:
    """Open one path, record it, and require a rendered page.

    Args:
        page: The Playwright page.
        recorder: The evidence recorder of the page.
        path: The path to open.
        name: The step name.
    """
    answers: list[Any] = []  # The answer of the navigation.
    recorder.step(name, lambda: answers.append(page.goto(path, wait_until="domcontentloaded")))
    answer = answers[0]  # One navigation, one answer.
    assert answer is not None and answer.status == OK_STATUS, f"{path} answered {answer and answer.status}"


@pytest.fixture
def reader(page: Any, journey_recorder: Callable[..., JourneyRecorder]) -> tuple[Any, JourneyRecorder]:
    """Return the read-only operator page and its recorder."""
    return page, journey_recorder(page)


@pytest.fixture
def operator(
    firmware_operator_page: Any, journey_recorder: Callable[..., JourneyRecorder]
) -> tuple[Any, JourneyRecorder]:
    """Return the firmware operator page and its recorder."""
    return firmware_operator_page, journey_recorder(firmware_operator_page)


class TestSingleSiteJourneys:
    """Record each single-site stage for the parity comparison."""

    def test_selection_reaches_the_capture_page(self, reader: tuple[Any, JourneyRecorder]) -> None:
        """The mode, the site, the inventory, and the capture page render in order."""
        page, recorder = reader  # The read-only operator.
        visit(page, recorder, MODE_PATH, "mode page")  # The mode picker.
        page.get_by_test_id("mode-single-site").check()  # The single-site bubble.
        recorder.step("site page", lambda: self._continue(page))  # The site picker.
        visit(page, recorder, f"/select/site/{SITE_ID}", "inventory page")  # The device list of one site.
        expect(page.get_by_role("link", name="Go to the capture page")).to_be_visible()  # The next step.
        recorder.step("capture page", lambda: page.get_by_role("link", name="Go to the capture page").click())
        expect(page.locator("h1")).to_be_visible()  # The capture page rendered.
        assert "/captures/" in page.url  # The journey ended on the capture page.

    @staticmethod
    def _continue(page: Any) -> None:
        """Submit the mode form and wait for the site picker."""
        page.get_by_test_id("mode-continue").click()  # Store the mode in the session.
        page.wait_for_url(re.compile(r".*/select/site$"))  # The picker follows the mode page.

    def test_options_and_confirm_pages_of_a_prepared_run(self, reader: tuple[Any, JourneyRecorder]) -> None:
        """The options page and the confirm page of one run render with their controls."""
        page, recorder = reader  # The read-only operator.
        visit(page, recorder, f"/runs/{PREPARED_RUN_ID}", "prepared run page")  # The run before the start.
        visit(page, recorder, f"/runs/{PREPARED_RUN_ID}/options", "options page")  # The per-device choices.
        visit(page, recorder, f"/runs/{PREPARED_RUN_ID}/confirm", "confirm page")  # The typed confirmation.
        expect(page.get_by_test_id("upgrade-start-button")).to_be_disabled()  # Closed before the word.
        assert page.get_by_test_id("upgrade-start-button").is_disabled() is True  # The same rule as a comparison.

    @pytest.mark.fresh_server
    def test_start_reaches_the_progress_page(self, operator: tuple[Any, JourneyRecorder]) -> None:
        """A firmware operator starts a ready run and reads the progress page."""
        page, recorder = operator  # The operator that may start firmware.
        visit(page, recorder, f"/runs/{START_READY_RUN_ID}/confirm", "confirm page")  # The typed confirmation.
        page.get_by_test_id("upgrade-confirm-input").fill("CONFIRM")  # The exact word.
        expect(page.get_by_test_id("upgrade-start-button")).to_be_enabled()  # The word opens the button.
        recorder.step("start", lambda: page.get_by_test_id("upgrade-start-button").click())  # Start the run.
        page.wait_for_url(re.compile(rf".*/runs/{START_READY_RUN_ID}$"))  # The progress page of the run.
        recorder.step("progress page")  # Record the first progress view.
        assert page.url.endswith(f"/runs/{START_READY_RUN_ID}")  # The journey ended on the run page.

    @pytest.mark.parametrize("run_id", [FAILED_RUN_ID, STOPPED_RUN_ID, LIFECYCLE_RUN_ID])
    def test_run_page_of_each_seeded_state(self, reader: tuple[Any, JourneyRecorder], run_id: str) -> None:
        """Each seeded run state renders its run page."""
        page, recorder = reader  # The read-only operator.
        visit(page, recorder, f"/runs/{run_id}", f"run page {run_id}")  # The run in its seeded state.
        assert page.url.endswith(f"/runs/{run_id}")  # The run page of that state rendered.

    def test_history_and_comparison_pages(self, reader: tuple[Any, JourneyRecorder]) -> None:
        """The history page and the comparison of the seeded captures render."""
        page, recorder = reader  # The read-only operator.
        visit(page, recorder, "/history", "history page")  # Every stored capture and run.
        visit(page, recorder, f"/compare?before={PRE_CAPTURE_ID}&after={POST_CAPTURE_ID}", "comparison page")
        visit(page, recorder, f"/captures/{PRE_CAPTURE_ID}", "pre-check capture page")  # One capture.
        assert page.url.endswith(f"/captures/{PRE_CAPTURE_ID}")  # The journey ended on the capture page.
