"""Browser journey for the poll of a stored capture.

Why:
    Issue #3378. The capture page asks the status endpoint every 3 seconds, and
    it stops when the state holds a finished word. After a restart, the endpoint
    reads the stored capture. It used to send the content word `complete` as
    the state, so the page never stopped, and each request read the whole
    capture document from the store again.

    The seed `e2e-capture-stored-poll-0001` holds the shipped shape: the content
    word `complete` and the lifecycle word `verified`. No live progress record
    exists for it, so its page reads the stored path, as a page does after a
    restart. The journey counts the status requests over three poll intervals.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

from tests.e2e.upgrade_portal.conftest import STORED_POLL_CAPTURE_ID

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

CAPTURE_PATH = f"/captures/{STORED_POLL_CAPTURE_ID}"  # The page of the stored capture.
STATUS_PATH = f"/api/captures/{STORED_POLL_CAPTURE_ID}/status"  # The endpoint that the page polls.
STATE_CELL = '[data-testid="capture-progress"] [data-capture-field="state"]'  # The state word of the panel.
POLL_WINDOW_MS = 10_000  # Three poll intervals of 3 seconds, and one second more for a slow machine.
FINISHED_WORD = "verified"  # The word that the live path sends after a matching read-back.


class StatusRequestLog:
    """Count the status requests that one page sends for the stored capture."""

    def __init__(self, page: Any) -> None:
        """Start to count the status requests of the page.

        Args:
            page: The browser page that the journey drives.
        """
        self.count = 0  # No request went out before the journey opened the page.
        page.on("request", self.record)  # Playwright calls the recorder for each request of the page.

    def record(self, request: Any) -> None:
        """Count one request when it reads the status of the stored capture.

        Args:
            request: One network request of the browser page.
        """
        if request.method == "GET" and urlsplit(request.url).path == STATUS_PATH:  # The poll target alone.
            self.count += 1  # One more read of the stored capture.


def is_status_answer(response: Any) -> bool:
    """Return True for the answer of the status endpoint of the stored capture.

    Args:
        response: One network answer of the browser page.
    """
    return urlsplit(response.url).path == STATUS_PATH  # The first answer paints the panel.


class TestStoredCapturePoll:
    """Open a stored capture in the shipped shape and watch the poll."""

    def test_the_page_of_a_stored_capture_reads_the_status_once(self, page: Any, tmp_path: Path) -> None:
        """The first answer ends the poll, so no further request reads the store."""
        log = StatusRequestLog(page)  # Count each status request from the first one.
        logger.info("Open the page of the stored capture %s", STORED_POLL_CAPTURE_ID)  # Log before the open.
        with page.expect_response(is_status_answer) as first:  # The page reads the status once at the start.
            page.goto(CAPTURE_PATH, wait_until="domcontentloaded")  # The operator opens the stored capture.
        assert first.value.status == 200, f"The status read answered {first.value.status}."  # The store answered.
        sent = first.value.json().get("state")  # The word that the page painted first.
        logger.debug("The status answer holds the state %s", sent)  # Log after the read.
        page.screenshot(path=str(tmp_path / "stored-poll-01-opened.png"), full_page=True)

        page.wait_for_timeout(POLL_WINDOW_MS)  # Give a poll that did not stop three chances to send.
        page.screenshot(path=str(tmp_path / "stored-poll-02-after-window.png"), full_page=True)
        counted = f"The page sent {log.count} status requests in {POLL_WINDOW_MS} ms. The first held {sent!r}."
        assert log.count == 1, counted  # One read of the store, and no poll after it.
        assert sent == FINISHED_WORD, f"The stored status sent {sent!r}."  # The rule of the live path.
        sync_api.expect(page.locator(STATE_CELL)).to_have_text(FINISHED_WORD)  # The panel reads the end word.
        sync_api.expect(page.get_by_test_id("capture-verified-badge")).to_have_text("Verified")  # The read-back.
        sync_api.expect(page.get_by_test_id("capture-progress-percent")).to_have_text("100%")  # The whole bar.
        logger.debug("The stored capture page sent %s status request", log.count)  # Log after the last step.
