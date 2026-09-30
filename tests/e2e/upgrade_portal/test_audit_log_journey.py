"""Browser journey of issue #3498: the lock audit trail of the test portal stays inside its own run.

Why:
    Issue #3498. The test portal wrote each site lock action to the checkout
    trail. In the main checkout, that file is the production audit trail, and
    the production container mounts it. The Audit log card of a new session
    also showed the records of an earlier session.

    This journey drives the lock banner of the capture start page. The operator
    takes the site and releases it. The journey then reads the Audit log card
    of the site and of the history with no site. It reads the trail of the run
    from the parent process, and it proves that the checkout trail holds no
    line of the journey site.

    The journey site is a key that no other journey and no seed uses. A take by
    the operator who already holds a site writes no take row, and a lock that
    another journey left behind refuses the take. A site of its own keeps both
    cases away from this journey. The site is not in the site list, so no count
    of the site list changes.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from src.upgrade_portal.runtime.identity import email_digest
from tests.e2e.upgrade_portal.conftest import STAND_IN_EMAIL
from tests.support.upgrade_portal_e2e.records.audit import AuditTrailIsolation

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

JOURNEY_SITE_ID = "34983498-3498-3498-3498-349834983498"  # A site key that no other journey and no seed uses.
CAPTURE_START_PATH = f"/captures/new?site_id={JOURNEY_SITE_ID}"  # The capture start page shows the lock banner.
SITE_HISTORY_PATH = f"/history?site_id={JOURNEY_SITE_ID}"  # The history of the journey site alone.
EVERY_SITE_HISTORY_PATH = "/history"  # The history with no site.
LOCK_BANNER_ID = "lock-banner"  # `contracts/ui-testids.md` fixes the banner name.
LOCK_TAKE_BUTTON_ID = "lock-take-button"  # The control that takes a free site.
LOCK_RELEASE_BUTTON_ID = "lock-release-button"  # The control that gives the site back.
LOCK_STATE_ATTRIBUTE = "data-lock-state"  # The banner publishes its state, and `portal.js` rewrites it.
AUDIT_TABLE_ID = "history-audit-table"  # The table of the Audit log card.
AUDIT_ROW_SELECTOR = "[data-testid^='history-audit-row-']"  # One row for each lock action, newest first.
AUDIT_ROWS_SCRIPT = """
rows => rows.map(row => {
  const cells = row.querySelectorAll(':scope > td');
  const action = row.querySelector("[data-testid^='history-audit-action-']");
  return [cells[0].innerText.trim(), action.innerText.trim(), cells[2].innerText.trim()];
})
"""  # One read gives the site, the action, and the operator of each row, so a long card needs no round trip each.
GATE_TIMEOUT_MS = 5000  # The pages are server rendered, and each lock answer arrives from the stand-in store.
SCREENSHOT_DIRECTORY = (  # The evidence folder of this journey.
    Path(__file__).parents[3] / "test-artifacts" / "upgrade-portal-journeys" / "audit-log"
)


def save_screenshot(page: Any, name: str) -> Path:
    """Save one journey screenshot.

    Args:
        page: The browser page.
        name: The file name of the screenshot.

    Returns:
        The path of the saved file.
    """
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep evidence outside the production data tree.
    path = SCREENSHOT_DIRECTORY / name  # One stable file name for each page state.
    logger.info("Save the journey screenshot %s", name)  # Log before the file write.
    page.screenshot(path=str(path), full_page=True)  # Capture the full page for the visual review.
    logger.debug("Saved the journey screenshot %s", path)  # Log after the file write.
    return path  # The caller may prove that the file exists.


def press_and_wait(page: Any, control_id: str, state: str) -> str:
    """Press one control of the lock banner, and wait for the banner to reach a state.

    Args:
        page: The browser page.
        control_id: The test identifier of the control.
        state: The banner state that the answer must give.

    Returns:
        The state that the banner then publishes.
    """
    logger.info("Press %s and wait for the banner state %s", control_id, state)  # Log before the press.
    page.get_by_test_id(control_id).click()  # The press that an operator makes.
    banner = page.get_by_test_id(LOCK_BANNER_ID)  # The banner of the page.
    sync_api.expect(banner).to_have_attribute(LOCK_STATE_ATTRIBUTE, state, timeout=GATE_TIMEOUT_MS)
    logger.debug("The banner reached the state %s", state)  # Log after the answer.
    return str(banner.get_attribute(LOCK_STATE_ATTRIBUTE))  # The state that the page shows now.


def take_and_release(page: Any) -> list[str]:
    """Take the journey site from the capture start page, and release it.

    Args:
        page: The browser page of the operator.

    Returns:
        The banner state before the take, after the take, and after the release.
    """
    logger.info("Open the capture start page of the journey site")  # Log before the page read.
    page.goto(CAPTURE_START_PATH)  # The page that the site picker opens for a capture.
    banner = page.get_by_test_id(LOCK_BANNER_ID)  # The banner of the journey site.
    sync_api.expect(banner).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The page must show the banner first.
    states = [str(banner.get_attribute(LOCK_STATE_ATTRIBUTE))]  # No operator holds the journey site yet.
    save_screenshot(page, "capture-banner-free.png")  # The banner before the take.
    states.append(press_and_wait(page, LOCK_TAKE_BUTTON_ID, "held"))  # The take writes one take row.
    save_screenshot(page, "capture-banner-held.png")  # The banner of the holder.
    states.append(press_and_wait(page, LOCK_RELEASE_BUTTON_ID, "free"))  # The release writes one release row.
    save_screenshot(page, "capture-banner-released.png")  # The banner after the release.
    logger.debug("The banner states were %s", states)  # Log after the journey step.
    return states  # The caller compares the three states.


def read_audit_card(page: Any, path: str, screenshot: str) -> list[list[str]]:
    """Open one history page, and read the site, the action, and the operator of each audit row.

    Args:
        page: The browser page.
        path: The history address.
        screenshot: The file name of the screenshot.

    Returns:
        One list of three texts for each audit row, newest first.
    """
    logger.info("Read the Audit log card of %s", path)  # Log before the page read.
    page.goto(path)  # The history page renders the card on the server.
    table = page.get_by_test_id(AUDIT_TABLE_ID)  # The table of the Audit log card.
    sync_api.expect(table).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The card must render before the read.
    table.scroll_into_view_if_needed()  # The card sits below the run and capture tables.
    save_screenshot(page, screenshot)  # The card as the operator reads it.
    rows: list[list[str]] = page.locator(AUDIT_ROW_SELECTOR).evaluate_all(AUDIT_ROWS_SCRIPT)
    logger.debug("The Audit log card of %s holds %s row(s)", path, len(rows))  # Log after the read.
    return rows  # The caller compares the rows of the journey site.


def journey_trail_facts(isolation: AuditTrailIsolation) -> tuple[list[list[str]], int]:
    """Read the lock actions of the journey site in the run trail and in the checkout trail.

    Args:
        isolation: The isolation of this run, from the checkout audit trail guard.

    Returns:
        The action and the operator of each run trail record of the journey site,
        and the count of checkout trail lines that name the journey site.
    """
    logger.info("Read the journey site records of the run trail")  # Log before the file reads.
    run_lines = isolation.run_trail.read_text(encoding="utf-8").splitlines() if isolation.run_trail.exists() else []
    records = [json.loads(line) for line in run_lines if JOURNEY_SITE_ID in line]  # Oldest first, as written.
    actions = [[str(record["action"]), str(record["actor_email"])] for record in records]
    checkout = isolation.checkout_trail  # The trail that the production portal writes.
    checkout_lines = checkout.read_text(encoding="utf-8").splitlines() if checkout.exists() else []
    leaked = sum(1 for line in checkout_lines if JOURNEY_SITE_ID in line)  # A site key never appears by chance.
    logger.debug("The run trail holds %s journey record(s), and the checkout trail %s", len(actions), leaked)
    return actions, leaked  # The caller compares both facts.


def test_the_audit_log_shows_the_take_and_the_release_of_this_run(
    page: Any, checkout_audit_trail_guard: AuditTrailIsolation
) -> None:
    """The take and the release of the journey site reach the Audit log card and the run trail only.

    Why:
        User Stories 1 and 2 of issue #3498. The Audit log card of the site must
        show exactly the two actions of this run, newest first. The Operator
        column must show the digest of the operator and never the address. The
        run trail must hold the two actions, and the checkout trail must hold
        none of them.

    Args:
        page: The browser page of the operator that every test drives.
        checkout_audit_trail_guard: The isolation of this run.
    """
    digest = email_digest(STAND_IN_EMAIL)  # The one form of the address that the portal displays.
    states = take_and_release(page)  # The two presses of the operator.
    site_rows = read_audit_card(page, SITE_HISTORY_PATH, "history-site-audit-log.png")
    every_rows = read_audit_card(page, EVERY_SITE_HISTORY_PATH, "history-every-site-audit-log.png")
    run_actions, leaked = journey_trail_facts(checkout_audit_trail_guard)
    observed = {
        "banner states": states,
        "site page rows": site_rows,
        "every site page rows of the journey site": [row for row in every_rows if row[0] == JOURNEY_SITE_ID],
        "run trail records of the journey site": run_actions,
        "checkout trail lines of the journey site": leaked,
    }
    expected = {
        "banner states": ["free", "held", "free"],
        "site page rows": [[JOURNEY_SITE_ID, "release", digest], [JOURNEY_SITE_ID, "take", digest]],
        "every site page rows of the journey site": [
            [JOURNEY_SITE_ID, "release", digest],
            [JOURNEY_SITE_ID, "take", digest],
        ],
        "run trail records of the journey site": [["take", STAND_IN_EMAIL], ["release", STAND_IN_EMAIL]],
        "checkout trail lines of the journey site": 0,
    }
    assert observed == expected
