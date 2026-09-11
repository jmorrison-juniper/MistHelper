"""Prove stale age behavior in the isolated browser portal.

Why:
    These tests use the process-owned E2E server. They submit no firmware and
    they call no cloud write.
"""

from __future__ import annotations  # Keep annotations independent from import order.

from datetime import UTC, datetime, timedelta  # Build one old display timestamp.
from typing import Any  # Playwright supplies its page with a runtime type.

import pytest  # Skip collection only when the Playwright package is absent.

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")  # Browser API.

FAILED_RUN_ID = "e2e-failed-run-0001"  # Use the isolated terminal run that the server process seeds.
HISTORY_PATH = "/history"  # Open the real history route.
RUN_PATH = f"/runs/{FAILED_RUN_ID}"  # Open the real run page for the same record.
SEED_TRIES = 20  # Bound the wait for the asynchronous process-owned seed.
SEED_PAUSE_MILLISECONDS = 500  # Give the seed thread a short interval between reads.
VIEWPORT_WIDTHS = (360, 768, 1280)  # Cover each width that the UI contract requires.


def _open_seeded_page(page: Any, path: str, test_id: str) -> Any:  # Wait for one process-owned seeded run page.
    """Open a page after the isolated server stores its seeded run."""
    locator = page.get_by_test_id(test_id)  # Build the exact contract selector once.
    for _attempt in range(SEED_TRIES):  # The seed can finish after the server starts listening.
        answer = page.goto(path)  # Read only the isolated portal route.
        assert answer is not None and answer.ok  # A route fault must not become a skip.
        locator = page.get_by_test_id(test_id)  # Refresh the locator after page navigation.
        if locator.count() == 1:  # The process-owned run is now visible.
            return locator  # Give the test the exact contract element.
        page.wait_for_timeout(SEED_PAUSE_MILLISECONDS)  # Let the seed thread complete.
    pytest.fail(f"The isolated portal did not show {test_id}.")  # Report a missing seed as a test failure.


class TestStaleBrowserViews:  # Group browser assertions for the two stale view surfaces.
    """Verify unknown age, display updates, and responsive age content."""

    def test_history_and_run_pages_fail_closed_for_missing_time(self, page: Any) -> None:
        """A seeded run with no update time shows unknown and no stale badge."""
        history_age = _open_seeded_page(page, HISTORY_PATH, f"history-run-age-{FAILED_RUN_ID}")  # History age.
        sync_api.expect(history_age).to_have_text("unknown")  # Show the required safe age text.
        assert page.get_by_test_id(f"history-run-stale-{FAILED_RUN_ID}").count() == 0  # Show no stale badge.
        run_age = _open_seeded_page(page, RUN_PATH, "run-last-update-age")  # Open the same run page.
        sync_api.expect(run_age).to_have_text("unknown")  # Keep both pages in agreement.
        assert page.get_by_test_id("run-stale-badge").count() == 0  # Keep terminal and unknown state safe.

    def test_browser_age_update_changes_text_only(self, page: Any) -> None:
        """The browser updates age text and does not create stale eligibility."""
        age = _open_seeded_page(page, RUN_PATH, "run-last-update-age")  # Open one real server-rendered age field.
        old_time = datetime.now(tz=UTC) - timedelta(days=1, hours=1)  # Build an old display value only.
        age.evaluate(  # Replace only the display timestamp after the server decision.
            "(element, value) => element.setAttribute('data-age-updated-at', value)", old_time.isoformat()
        )
        page.evaluate(  # Ask the shipped listener to refresh the display from one browser clock.
            "document.dispatchEvent(new Event('upgrade-portal-refresh-run-ages'))"
        )
        sync_api.expect(age).to_have_text("1d 1h")  # Show the updated short age text.
        assert page.get_by_test_id("run-stale-badge").count() == 0  # JavaScript must not create eligibility.

    @pytest.mark.parametrize("width", VIEWPORT_WIDTHS)  # Verify every responsive width in the UI contract.
    def test_run_age_remains_usable_at_required_widths(self, page: Any, width: int) -> None:
        """The run age remains visible and inside each required viewport."""
        page.set_viewport_size({"width": width, "height": 900})  # Apply the exact contract width.
        age = _open_seeded_page(page, RUN_PATH, "run-last-update-age")  # Open the real responsive run page.
        sync_api.expect(age).to_be_visible()  # Keep the age available to an operator.
        box = age.bounding_box()  # Read the rendered position after the responsive rules apply.
        assert box is not None  # A visible age must have a layout box.
        assert box["x"] >= 0  # Keep the left edge inside the viewport.
        assert box["x"] + box["width"] <= width  # Keep the right edge inside the viewport.
