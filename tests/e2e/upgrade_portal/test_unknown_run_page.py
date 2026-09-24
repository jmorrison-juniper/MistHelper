"""The browser proof that an unknown run link opens the 404 error page.

Why:
    Issue #3276. Each run page read ``load_run(run_id) or {}``, so an unknown
    run ID rendered an empty "Upgrade run" page with status 200. The operator
    could not tell a mistyped link from a real run. The contract test in
    ``tests/contract/upgrade_portal/test_upgrade_routes/test_unknown_run_pages.py``
    reads the markup. Only a browser shows what the operator reads, and only a
    browser follows the link back.

What each test reads:
    Each test opens one real page of the stand-in portal and saves a screenshot
    into the pytest folder of the test. An engineer can then compare the painted
    page with the assertions.

Identifier contract:
    Every locator reads a ``data-testid`` attribute, as rule 4 of
    ``contracts/ui-testids.md`` states.
"""

from __future__ import annotations

import re  # Match the page that the link back opens.
from pathlib import Path  # Type the pytest folder that receives each screenshot.
from typing import Any  # Playwright page and response objects are free-form.

import pytest  # The test framework and its parameter helper.

# The Playwright package must exist before this module defines a browser test.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

UNKNOWN_RUN_ID = "not-a-real-run"  # The mistyped link of issue #3276.
PAGE_TEMPLATES = ("/runs/{run_id}", "/runs/{run_id}/options", "/runs/{run_id}/confirm")  # The three run pages.
NOT_FOUND_STATUS = 404  # No run holds the ID.
GATE_TIMEOUT_MS = 60000  # A cold store can need more time during a full suite.

ERROR_TITLE = "The portal found no such run"  # The heading of the error page for an unknown run.
ERROR_SENTENCE = f"The portal holds no run with the identifier {UNKNOWN_RUN_ID}."  # The sentence names the ID.
RUN_NOT_FOUND_CODE = "run_not_found"  # `contracts/http-api.md` fixes this code for every run path.
SITE_LIST_PATH = "/select/site"  # The recovery link of `error.html`.

# The site picker sends a session with no organization to the organization
# picker first, so the link back can end on either picker.
PICKER_URL_PATTERN = re.compile(r"/select/(site|org)")

# A control that writes to a run must never appear on the error page.
WRITE_CONTROL_IDS = ("upgrade-target-table", "upgrade-start-button", "stop-button")


def _open_unknown_run(page: Any, template: str) -> None:
    """Open one run page for the unknown run ID, and require the status 404.

    Args:
        page: A signed-in page of the stand-in portal.
        template: The path template of one run page.
    """
    path = template.format(run_id=UNKNOWN_RUN_ID)  # The mistyped link.
    answer = page.goto(path, wait_until="domcontentloaded", timeout=GATE_TIMEOUT_MS)  # Open the real path.
    assert answer is not None and answer.status == NOT_FOUND_STATUS, f"{path} did not answer {NOT_FOUND_STATUS}"


@pytest.mark.parametrize("template", PAGE_TEMPLATES)
def test_an_unknown_run_link_opens_the_error_page(page: Any, template: str, tmp_path: Path) -> None:
    """Prove that each run page shows the error page for an unknown run ID.

    Args:
        page: A signed-in page of the stand-in portal.
        template: The path template of one run page.
        tmp_path: The pytest folder of this test.
    """
    _open_unknown_run(page, template)  # The status must be 404 before the page reads.
    sync_api.expect(page.get_by_test_id("error-title")).to_have_text(ERROR_TITLE)  # The heading names the fault.
    message = page.get_by_test_id("error-message")  # The sentence with the signal word.
    sync_api.expect(message).to_contain_text(ERROR_SENTENCE)  # The sentence names the ID that the operator opened.
    sync_api.expect(page.get_by_test_id("error-status-code")).to_have_text(str(NOT_FOUND_STATUS))
    sync_api.expect(page.get_by_test_id("error-code")).to_have_text(RUN_NOT_FOUND_CODE)  # The stable code.
    page.screenshot(path=str(tmp_path / "unknown-run.png"), full_page=True)  # The evidence of the whole page.
    spoken = message.aria_snapshot()  # The signal word and the sentence, as a screen reader reads them.
    assert "Warning:" in spoken and ERROR_SENTENCE in spoken, f"The alert reads {spoken!r}."
    for control_id in WRITE_CONTROL_IDS:  # Each control that writes to a run.
        assert page.get_by_test_id(control_id).count() == 0, f"The error page shows {control_id}."


def test_the_error_page_link_returns_to_the_site_list(page: Any, tmp_path: Path) -> None:
    """Prove that the link of the error page opens the site list.

    Args:
        page: A signed-in page of the stand-in portal.
        tmp_path: The pytest folder of this test.
    """
    _open_unknown_run(page, PAGE_TEMPLATES[0])  # The run page of the mistyped link.
    link = page.get_by_test_id("error-site-list-link")  # The one recovery link of the page.
    sync_api.expect(link).to_have_attribute("href", SITE_LIST_PATH)  # The link names the site list.
    link.click()  # A plain press, the way an operator leaves the page.
    page.wait_for_url(PICKER_URL_PATTERN, timeout=GATE_TIMEOUT_MS)  # The picker opens.
    page.screenshot(path=str(tmp_path / "after-link.png"), full_page=True)  # The evidence of the next page.
    assert page.get_by_test_id("error-page").count() == 0, "The link opened the error page again."
