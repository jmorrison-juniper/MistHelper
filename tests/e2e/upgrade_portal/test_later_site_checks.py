"""Browser journeys for the later site checks after a site read that lost a page.

Why:
    Issue #3439. Each later site check read the site list again, and it took a
    missing site as proof that the site left the organization. A site read that
    lost a page cannot give that proof, so the portal showed "site not found"
    for a site that exists. The old options save also stored a plan with no
    site. Each later check now refuses with the status 503 and the code
    site_list_incomplete, and it changes no state.

    These journeys drive a real browser through both modes. The cloud session
    of the later-check operator answers both pages of each site read. A request
    with the lose-page header loses page two, which holds the site West. Each
    journey opens a page with a whole read, turns the fault on, presses one
    control, and reads the refusal. It then turns the fault off and proves the
    recovery. A screenshot records each state for a visual review, and a timing
    file records the time of each refusal. No journey sends a firmware request.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.later_check_seeds import (
    LOSE_PAGE_HEADER,
    LOSE_PAGE_VALUE,
    NORTH_ID,
    NORTH_NAME,
    RETRY_OPERATION_ID,
    SITE_DEVICES,
    WEST_AP_MAC,
    WEST_ID,
    WEST_NAME,
)

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)  # The journey steps reach the pytest log.

MODE_PATH = "/select/mode"  # The mode chooser, where each picker journey starts.
PICKER_PATH = re.compile(r".*/select/site$")  # The site picker.
WEST_PAGE_PATH = re.compile(rf".*/select/site/{WEST_ID}$")  # The inventory page of the site of page two.
CAPTURE_PAGE_PATH = re.compile(rf".*/captures/new\?site_id={WEST_ID}.*")  # The first capture page of that site.
OPTIONS_PATH = re.compile(r".*/upgrade/org/options$")  # The multi-site options page.
CONFIRM_PATH = re.compile(r".*/upgrade/org/confirm$")  # The multi-site confirm page.
RETRY_PAGE = f"/upgrade/org/jobs/{RETRY_OPERATION_ID}"  # The progress page of the seeded settled operation.
REFUSAL_TITLE = "The portal did not read the complete site list"  # The heading of the refusal page.
REFUSAL_MESSAGE = (  # The one sentence of every later check refusal.
    "The portal did not read the complete site list, so it cannot check your site choice. Try again."
)
REFUSAL_CODE = "site_list_incomplete"  # The stable code that a support request quotes.
REFUSAL_STATUS = 503  # The status of every later check refusal.
CAUTION_PREFIX = '"Caution: "'  # The value that `portal.css` gives the prefix of a caution.
WARNING_PREFIX = '"Warning: "'  # The value that `portal.css` gives the prefix of a script refusal.
PREFIX_SCRIPT = "(node) => getComputedStyle(node, '::before').content"  # Read the prefix of one message.
IN_VIEW_SCRIPT = (  # True when the whole element sits inside the visible part of the page.
    "(node) => { const box = node.getBoundingClientRect(); return box.top >= 0 && box.bottom <= innerHeight; }"
)
SITE_ROW_SELECTOR = '[data-testid^="site-row-"]'  # One table row for each site of the picker.
WHOLE_ROWS = 3  # A whole site read holds the two sites of page one and the site of page two.
LOST_ROWS = 2  # A lost page two leaves the two sites of page one.
TARGET_VERSION = "0.15.1"  # The newer version that the stand-in cloud offers for every model.
DEVICE_TYPES = ("ap", "switch", "gateway")  # The three device types of the multi-site form.
VERSION_FIELD_IDS = ("org-upgrade-version", "org-upgrade-switch-version", "org-upgrade-gateway-version")
FETCH_SCRIPT = """async (path) => {
    const answer = await fetch(path, {headers: {Accept: "application/json"}});
    return {status: answer.status, body: await answer.json()};
}"""  # The browser reads one answer with its own session cookies and its extra headers.
REFUSAL_BUDGET_MS = 5000  # A refusal costs one site read on loopback, so it must answer well inside this time.
LOCK_SETTLE_MS = 4000  # The lock take is one round trip on loopback.
SEED_TRIES = 20  # The server writes the seeds on a thread, so the first read can come too early.
SEED_PAUSE_MS = 500  # The pause between two reads of a seeded page.
EVIDENCE_DIRECTORY = (  # The evidence folder of these journeys.
    Path(__file__).parents[3] / "data" / "test-artifacts" / "upgrade-portal-journeys" / "later-site-checks"
)
TIMING_FILE = EVIDENCE_DIRECTORY / "timings.json"  # The time of each refusal, in milliseconds.


class JourneyEvidence:
    """Switch the lost page, and record the screenshots and the timings of a journey."""

    @staticmethod
    def lose_page(page: Any, lost: bool) -> None:
        """Turn the lost page two of each site read on or off for each later request.

        Args:
            page: The browser page.
            lost: True to lose page two, False to read both pages.
        """
        logger.info("Set the lost page switch to %s", lost)  # Record the step before the change.
        page.set_extra_http_headers({LOSE_PAGE_HEADER: LOSE_PAGE_VALUE} if lost else {})  # Each later request.
        logger.debug("The lost page switch is %s", lost)  # Record the result of the step.

    @staticmethod
    def screenshot(page: Any, name: str, full_page: bool = True) -> Path:
        """Save one journey screenshot.

        Args:
            page: The browser page.
            name: The file name of the screenshot.
            full_page: True for the whole page, False for the visible part only.

        Returns:
            The path of the saved file.
        """
        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep the evidence under the repository data tree.
        path = EVIDENCE_DIRECTORY / name  # One stable file name for each page state.
        logger.info("Save the screenshot %s", path.name)  # Record the capture before it runs.
        page.screenshot(path=str(path), full_page=full_page)  # The visible part shows what the operator sees.
        logger.debug("Saved the screenshot %s", path.name)  # Record the capture after it ends.
        return path  # The caller proves that the file exists.

    @staticmethod
    def record_timing(step: str, started: float) -> float:
        """Store the time of one step in the timing file, and prove the budget.

        Args:
            step: The name of the step.
            started: The `time.perf_counter` value at the start of the step.

        Returns:
            The time of the step, in milliseconds.
        """
        elapsed = (time.perf_counter() - started) * 1000  # The time from the press to the refusal.
        logger.info("The step %s took %.1f ms", step, elapsed)  # Record the result for the performance review.
        EVIDENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)  # The timing file sits beside the screenshots.
        timings = json.loads(TIMING_FILE.read_text("utf-8")) if TIMING_FILE.exists() else {}  # Earlier steps.
        timings[step] = round(elapsed, 1)  # One value for each step. A new run replaces the old value.
        TIMING_FILE.write_text(json.dumps(timings, indent=2, sort_keys=True), "utf-8")  # Keep the file readable.
        assert elapsed < REFUSAL_BUDGET_MS  # A slow refusal is a performance defect.
        return elapsed  # The caller can log the value again.


class PickerSteps:
    """Drive the site picker, and read the two kinds of refusal."""

    @staticmethod
    def open_the_picker(page: Any, mode_control: str, rows: int) -> None:
        """Choose one mode, open the site picker, and count its rows.

        Args:
            page: The browser page.
            mode_control: The test identifier of the mode choice.
            rows: The count of site rows that the picker must show.
        """
        logger.info("Open the site picker with the mode control %s", mode_control)  # Record the step first.
        page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode chooser with a signed session.
        page.get_by_test_id(mode_control).check()  # Choose the mode of this journey.
        page.get_by_test_id("mode-continue").click()  # Move to the site picker.
        page.wait_for_url(PICKER_PATH)  # Wait until the site picker owns the page.
        sync_api.expect(page.locator(SITE_ROW_SELECTOR)).to_have_count(rows)  # The rows of the read.
        logger.debug("The site picker shows %s row(s)", rows)  # Record the result of the step.

    @staticmethod
    def check_sites(page: Any, site_ids: tuple[str, ...]) -> None:
        """Check the box of each named site on the multi-site picker.

        Args:
            page: The browser page, on the multi-site picker.
            site_ids: The sites to select, in the picker order.
        """
        logger.info("Select %s site(s) on the multi-site picker", len(site_ids))  # Record the step first.
        for site_id in site_ids:  # One box for each site.
            page.get_by_test_id(f"site-select-{site_id}").check()  # A checked box stays checked.
        logger.debug("Selected %s site(s)", len(site_ids))  # Record the result of the step.

    @staticmethod
    def assert_the_refusal_page(page: Any) -> None:
        """Prove that the page is the refusal page of a lost page.

        Args:
            page: The browser page, on the error page of a page request.
        """
        logger.info("Read the refusal page of the lost page")  # Record the step before the reads.
        sync_api.expect(page.get_by_test_id("error-title")).to_have_text(REFUSAL_TITLE)  # The cause in words.
        sync_api.expect(page.get_by_test_id("error-message")).to_contain_text(REFUSAL_MESSAGE)  # The instruction.
        sync_api.expect(page.get_by_test_id("error-status-code")).to_have_text(str(REFUSAL_STATUS))  # The status.
        sync_api.expect(page.get_by_test_id("error-code")).to_have_text(REFUSAL_CODE)  # The support code.
        sync_api.expect(page.get_by_test_id("error-back-link")).to_have_count(0)  # A reload repeats the check.
        sync_api.expect(page.get_by_test_id("error-site-list-link")).to_be_visible()  # The way back to the list.
        logger.debug("The refusal page names the lost page")  # Record the result of the step.

    @staticmethod
    def assert_the_caution_flash(page: Any) -> None:
        """Prove that the picker shows the refusal sentence as a Caution message.

        Args:
            page: The browser page, on the site picker after a refused choice.
        """
        logger.info("Read the Caution message of the refused site choice")  # Record the step before the reads.
        flash = page.get_by_test_id("flash-message").locator(".flash-item.flash-warning")  # The server message.
        sync_api.expect(flash).to_have_text(REFUSAL_MESSAGE)  # The instruction to try again.
        assert flash.evaluate(PREFIX_SCRIPT) == CAUTION_PREFIX  # A second try recovers, so Caution.
        logger.debug("The picker shows the Caution message")  # Record the result of the step.

    @staticmethod
    def assert_the_script_refusal(page: Any) -> None:
        """Prove that the page script shows the refusal sentence in the page.

        Why:
            The multi-site forms send their fields as JSON, so a refusal never
            opens a new page. The script paints each refused request with the
            prefix "Warning:", and this change keeps that rule (spec, Out of
            Scope).

        Args:
            page: The browser page, on the page of the refused form.
        """
        logger.info("Read the script message of the refused form")  # Record the step before the reads.
        flash = page.get_by_test_id("flash-message").locator(".flash-item.flash-danger")  # The script message.
        sync_api.expect(flash).to_have_text(REFUSAL_MESSAGE)  # The instruction to try again.
        assert flash.evaluate(PREFIX_SCRIPT) == WARNING_PREFIX  # The prefix rule of every script refusal.
        logger.debug("The page shows the script message")  # Record the result of the step.


class PlanSteps:
    """Drive the multi-site plan, the capture page, and the seeded recovery page."""

    @staticmethod
    def open_the_options_page(page: Any, site_ids: tuple[str, ...]) -> None:
        """Choose the multi-site mode and the named sites, and open the options page.

        Args:
            page: The browser page.
            site_ids: The sites of the plan.
        """
        PickerSteps.open_the_picker(page, "mode-multi-site", WHOLE_ROWS)  # A whole read shows all three sites.
        PickerSteps.check_sites(page, site_ids)  # Select the sites of this journey.
        page.get_by_test_id("multi-site-continue").click()  # Store the site set.
        page.wait_for_url(OPTIONS_PATH)  # The whole read accepts the site set.

    @staticmethod
    def fill_the_plan(page: Any) -> None:
        """Check each device type, type one version for each type, and choose the serial strategy.

        Args:
            page: The browser page, on the multi-site options form.
        """
        logger.info("Fill the multi-site plan")  # Record the step before the first control changes.
        for device_type in DEVICE_TYPES:  # A checked type shows its version field.
            page.get_by_test_id(f"org-upgrade-type-{device_type}").check()  # A checked box stays checked.
        for field_id in VERSION_FIELD_IDS:  # Each selected site holds one device of each type.
            page.get_by_test_id(field_id).fill(TARGET_VERSION)  # The newer version of every stand-in model.
        page.get_by_test_id("org-strategy-serial").check()  # One site at a time.
        logger.debug("The multi-site plan holds %s device type(s)", len(DEVICE_TYPES))  # Record the result.

    @staticmethod
    def take_the_site(page: Any) -> None:
        """Take the site lock on the capture page, so the start control is live.

        Why:
            FR-072 gives one site to one operator. One press takes a free site.
            A site that a lock already holds opens the confirmation box, and
            the page names the word that the box needs.

        Args:
            page: The browser page, on the capture page.
        """
        start = page.get_by_test_id("capture-start-button")  # The control that needs the lock.
        take = page.get_by_test_id("lock-take-button")  # The control that takes the site.
        if take.count() == 1 and take.is_visible():  # This browser does not hold the site yet.
            take.click()  # One press takes a free site.
        field = page.get_by_test_id("lock-confirm-input")  # The box of a takeover.
        if field.count() == 1 and field.is_visible():  # A lock already held the site.
            field.fill(str(field.get_attribute("data-confirm-word") or "CONFIRM"))  # The word that the page names.
            page.get_by_test_id("lock-confirm-submit").click()  # Send the typed word.
        sync_api.expect(start).to_be_enabled(timeout=LOCK_SETTLE_MS)  # This browser holds the site.

    @staticmethod
    def open_seeded_page(page: Any, path: str, test_id: str) -> None:
        """Open one page of a seeded operation, and wait until the seed exists.

        Args:
            page: The browser page of the later-check operator.
            path: The page path.
            test_id: The test identifier of the control that the seed shows.
        """
        for _ in range(SEED_TRIES):  # The seed thread can finish after the first test starts.
            page.goto(path, wait_until="domcontentloaded")  # Read the page again.
            if page.get_by_test_id(test_id).count() == 1:  # The seed exists and shows its control.
                return  # The journey can go on.
            page.wait_for_timeout(SEED_PAUSE_MS)  # Give the seed thread time to write.
        sync_api.expect(page.get_by_test_id(test_id)).to_be_visible()  # Report the missing control.


class TestSingleSiteLaterChecks:
    """Drive the single-site checks that read the site list after the pick."""

    def test_the_inventory_page_refuses_after_a_lost_page_and_a_reload_recovers(
        self, later_check_operator_page: Any
    ) -> None:
        """The inventory page of the site of page two refuses, and a reload with a whole read opens it."""
        page = later_check_operator_page  # The separate operator, so no other journey sees the lost page.
        PickerSteps.open_the_picker(page, "mode-single-site", WHOLE_ROWS)  # The whole read shows West.
        assert JourneyEvidence.screenshot(page, "single-site-picker-whole.png").exists()  # All three sites.
        JourneyEvidence.lose_page(page, True)  # The next read of the site list loses West.
        started = time.perf_counter()  # The timing starts at the press.
        with page.expect_response(lambda answer: answer.request.is_navigation_request()) as opened:
            page.get_by_test_id(f"site-open-{WEST_ID}").click()  # Open the site of page two.
        assert opened.value.status == REFUSAL_STATUS  # The page states the cause, and never "not found".
        PickerSteps.assert_the_refusal_page(page)  # A page request gets no link back.
        JourneyEvidence.record_timing("single-site-inventory-page", started)  # The refusal answers at once.
        assert JourneyEvidence.screenshot(page, "single-site-inventory-refused.png").exists()  # The refusal.
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.
        page.reload(wait_until="domcontentloaded")  # The instruction of the refusal.
        page.wait_for_url(WEST_PAGE_PATH)  # The same address now opens the page.
        sync_api.expect(page.get_by_test_id("inventory-table")).to_be_visible()  # The device list of West.
        assert JourneyEvidence.screenshot(page, "single-site-inventory-recovered.png").exists()  # The recovery.

    def test_the_inventory_answer_refuses_a_lost_site_and_keeps_a_kept_site(
        self, later_check_operator_page: Any
    ) -> None:
        """The inventory answer of West refuses with 503, and the answer of a site of page one stays 200."""
        page = later_check_operator_page  # The separate operator, so no other journey sees the lost page.
        page.goto(MODE_PATH, wait_until="domcontentloaded")  # A portal page, so the read carries the session.
        JourneyEvidence.lose_page(page, True)  # Each read of the site list loses West.
        started = time.perf_counter()  # The timing starts at the read.
        lost = page.evaluate(FETCH_SCRIPT, f"/api/sites/{WEST_ID}/inventory")  # The read that a script sends.
        JourneyEvidence.record_timing("single-site-inventory-answer", started)  # The refusal answers at once.
        assert lost["status"] == REFUSAL_STATUS  # The site may exist, so the answer is never 404.
        assert lost["body"]["error"] == {"code": REFUSAL_CODE, "message": REFUSAL_MESSAGE}  # The envelope.
        kept = page.evaluate(FETCH_SCRIPT, f"/api/sites/{NORTH_ID}/inventory")  # A site of page one.
        assert kept["status"] == 200  # The kept page holds the site, so the check passes (FR-006).
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.
        whole = page.evaluate(FETCH_SCRIPT, f"/api/sites/{WEST_ID}/inventory")  # The same read again.
        assert whole["status"] == 200  # A second try with a whole read recovers.
        assert len(whole["body"]["devices"]) == SITE_DEVICES  # The device list of West.

    def test_the_capture_start_refuses_after_a_lost_page_and_names_the_cause(
        self, later_check_operator_page: Any
    ) -> None:
        """The capture start of West refuses, the region names the cause, and the control stays live."""
        page = later_check_operator_page  # The separate operator, so no other journey sees the lost page.
        PickerSteps.open_the_picker(page, "mode-single-site", WHOLE_ROWS)  # The whole read shows West.
        page.get_by_test_id(f"site-open-{WEST_ID}").click()  # Open the inventory page of West.
        page.wait_for_url(WEST_PAGE_PATH)  # The whole read accepts the site.
        page.get_by_test_id("site-capture-link").click()  # The only forward step out of the inventory page.
        page.wait_for_url(CAPTURE_PAGE_PATH)  # The first capture page of West.
        PlanSteps.take_the_site(page)  # FR-072: the start needs the site lock.
        start = page.get_by_test_id("capture-start-button")  # The control that starts the capture.
        label = start.inner_text()  # The label before the press.
        JourneyEvidence.lose_page(page, True)  # The next read of the site list loses West.
        started = time.perf_counter()  # The timing starts at the press.
        start.click()  # The script posts the start, and the site check runs first.
        sync_api.expect(page.get_by_test_id("capture-error")).to_have_text(REFUSAL_MESSAGE)  # The cause.
        JourneyEvidence.record_timing("single-site-capture-start", started)  # The refusal answers at once.
        sync_api.expect(start).to_be_enabled()  # The operator can press the control again.
        sync_api.expect(start).to_have_text(label)  # The label returns to its first text.
        state = page.locator('[data-capture-field="state"]').first.inner_text()  # The state after the refusal.
        logger.info("The capture state after the refusal reads %s", state)  # Evidence for the visual review.
        in_view = page.get_by_test_id("capture-error").evaluate(IN_VIEW_SCRIPT)  # Where the operator looks.
        logger.info("The capture refusal is in the visible part of the page: %s", in_view)  # Evidence.
        assert JourneyEvidence.screenshot(page, "single-site-capture-refused.png").exists()  # The refusal.
        assert JourneyEvidence.screenshot(page, "single-site-capture-refused-visible.png", False).exists()
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.


class TestMultiSiteLaterChecks:
    """Drive the multi-site checks that read the site list after the choice."""

    def test_the_site_choice_refuses_after_a_lost_page_and_a_second_try_recovers(
        self, later_check_operator_page: Any
    ) -> None:
        """A choice that holds West returns to the picker with a Caution message, and a second try works."""
        page = later_check_operator_page  # The separate operator, so no other journey sees the lost page.
        PickerSteps.open_the_picker(page, "mode-multi-site", WHOLE_ROWS)  # The whole read shows West.
        PickerSteps.check_sites(page, (NORTH_ID, WEST_ID))  # One site of each page.
        assert JourneyEvidence.screenshot(page, "multi-site-choice-whole.png").exists()  # The two boxes.
        JourneyEvidence.lose_page(page, True)  # The check of the choice loses West.
        started = time.perf_counter()  # The timing starts at the press.
        page.get_by_test_id("multi-site-continue").click()  # Store the site set.
        PickerSteps.assert_the_caution_flash(page)  # The picker names the cause and the next step.
        JourneyEvidence.record_timing("multi-site-choice", started)  # The refusal answers at once.
        sync_api.expect(page.locator(SITE_ROW_SELECTOR)).to_have_count(LOST_ROWS)  # This read also lost West.
        sync_api.expect(page.get_by_test_id("site-list-partial")).to_be_visible()  # The note of issue #3438.
        assert JourneyEvidence.screenshot(page, "multi-site-choice-refused.png").exists()  # The refusal.
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.
        page.reload(wait_until="domcontentloaded")  # The instruction of the message.
        sync_api.expect(page.locator(SITE_ROW_SELECTOR)).to_have_count(WHOLE_ROWS)  # West is back.
        PickerSteps.check_sites(page, (NORTH_ID, WEST_ID))  # The same choice again.
        page.get_by_test_id("multi-site-continue").click()  # The second try.
        page.wait_for_url(OPTIONS_PATH)  # The whole read accepts the choice.
        summary = page.get_by_test_id("org-upgrade-site-summary")  # The table of the selected sites.
        sync_api.expect(summary).to_contain_text(NORTH_NAME)  # The site of page one.
        sync_api.expect(summary).to_contain_text(WEST_NAME)  # The site of page two.
        assert JourneyEvidence.screenshot(page, "multi-site-choice-recovered.png").exists()  # The recovery.

    def test_the_options_page_and_the_save_refuse_after_a_lost_page(self, later_check_operator_page: Any) -> None:
        """The options page and the save of a plan for West refuse, and a later save reaches the confirm page."""
        page = later_check_operator_page  # The separate operator, so no other journey sees the lost page.
        PlanSteps.open_the_options_page(page, (WEST_ID,))  # A plan for the site of page two.
        JourneyEvidence.lose_page(page, True)  # The next read of the site list loses West.
        started = time.perf_counter()  # The timing starts at the reload.
        page.reload(wait_until="domcontentloaded")  # The options page reads the site list again.
        PickerSteps.assert_the_refusal_page(page)  # A page request gets no link back.
        JourneyEvidence.record_timing("multi-site-options-page", started)  # The refusal answers at once.
        assert JourneyEvidence.screenshot(page, "multi-site-options-refused.png").exists()  # The refusal.
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.
        page.reload(wait_until="domcontentloaded")  # The instruction of the refusal.
        PlanSteps.fill_the_plan(page)  # Type the plan of the operator.
        JourneyEvidence.lose_page(page, True)  # The save reads the site list again, and loses West.
        started = time.perf_counter()  # The timing starts at the press.
        page.get_by_test_id("org-upgrade-review").click()  # The script posts the fields of the save as JSON.
        PickerSteps.assert_the_script_refusal(page)  # The options page names the cause (US3, scenario 2).
        JourneyEvidence.record_timing("multi-site-options-save", started)  # The refusal answers at once.
        assert OPTIONS_PATH.match(page.url)  # A refused save opens no new page.
        sync_api.expect(page.get_by_test_id("org-upgrade-version")).to_have_value(TARGET_VERSION)  # Kept value.
        sync_api.expect(page.get_by_test_id("org-upgrade-review")).to_be_enabled()  # The form opens again.
        assert JourneyEvidence.screenshot(page, "multi-site-save-refused.png").exists()  # The refusal.
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.
        page.get_by_test_id("org-upgrade-review").click()  # The second try of the same typed plan.
        page.wait_for_url(CONFIRM_PATH)  # The whole read accepts the plan.
        sync_api.expect(page.get_by_test_id(f"org-upgrade-precheck-row-{WEST_ID}")).to_contain_text(WEST_NAME)
        assert JourneyEvidence.screenshot(page, "multi-site-save-recovered.png").exists()  # The recovery.

    def test_the_confirm_page_and_the_pre_check_refuse_after_a_lost_page(self, later_check_operator_page: Any) -> None:
        """The confirm page and the pre-check start of West refuse, and the card names the cause."""
        page = later_check_operator_page  # The separate operator, so no other journey sees the lost page.
        PlanSteps.open_the_options_page(page, (WEST_ID,))  # A plan for the site of page two.
        PlanSteps.fill_the_plan(page)  # Type the plan of the operator.
        page.get_by_test_id("org-upgrade-review").click()  # Save the plan with a whole read.
        page.wait_for_url(CONFIRM_PATH)  # The confirm page of the plan.
        JourneyEvidence.lose_page(page, True)  # The next read of the site list loses West.
        started = time.perf_counter()  # The timing starts at the reload.
        page.reload(wait_until="domcontentloaded")  # The confirm page reads the site list again.
        PickerSteps.assert_the_refusal_page(page)  # A page request gets no link back.
        JourneyEvidence.record_timing("multi-site-confirm-page", started)  # The refusal answers at once.
        assert JourneyEvidence.screenshot(page, "multi-site-confirm-refused.png").exists()  # The refusal.
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.
        page.reload(wait_until="domcontentloaded")  # The instruction of the refusal.
        page.wait_for_url(CONFIRM_PATH)  # The same address now opens the page.
        JourneyEvidence.lose_page(page, True)  # The pre-check start reads the site list again, and loses West.
        started = time.perf_counter()  # The timing starts at the press.
        page.get_by_test_id("org-upgrade-precheck-missing").click()  # The script posts the start of West.
        sync_api.expect(page.get_by_test_id("org-upgrade-precheck-error")).to_have_text(REFUSAL_MESSAGE)
        JourneyEvidence.record_timing("multi-site-precheck-start", started)  # The refusal answers at once.
        sync_api.expect(page.get_by_test_id("org-upgrade-precheck-missing")).to_be_enabled()  # A second try.
        state = page.get_by_test_id(f"org-upgrade-precheck-state-{WEST_ID}").inner_text()  # After the refusal.
        logger.info("The pre-check state of West after the refusal reads %s", state)  # Evidence for the review.
        in_view = page.get_by_test_id("org-upgrade-precheck-error").evaluate(IN_VIEW_SCRIPT)  # Where it shows.
        logger.info("The pre-check refusal is in the visible part of the page: %s", in_view)  # Evidence.
        assert JourneyEvidence.screenshot(page, "multi-site-precheck-refused.png").exists()  # The refusal.
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.

    def test_the_retry_refuses_after_a_lost_page_and_a_second_try_opens_the_plan(
        self, later_check_operator_page: Any
    ) -> None:
        """The retry of the failed access point of West refuses in the page, and a second try opens the plan."""
        page = later_check_operator_page  # The separate operator, so no other journey sees the lost page.
        PlanSteps.open_seeded_page(page, RETRY_PAGE, "org-upgrade-retry-controls")  # The settled operation.
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-count")).to_have_text("1")  # One failed device.
        sync_api.expect(page.get_by_test_id(f"org-upgrade-retry-device-{WEST_AP_MAC}")).to_be_visible()
        assert JourneyEvidence.screenshot(page, "multi-site-retry-progress.png").exists()  # The retry control.
        JourneyEvidence.lose_page(page, True)  # The retry reads the site list again, and loses West.
        started = time.perf_counter()  # The timing starts at the press.
        page.get_by_test_id("org-upgrade-retry").click()  # The script posts the retry as JSON.
        PickerSteps.assert_the_script_refusal(page)  # The progress page names the cause (US3, scenario 5).
        JourneyEvidence.record_timing("multi-site-retry", started)  # The refusal answers at once.
        assert page.url.endswith(RETRY_PAGE)  # A refused retry opens no new page.
        sync_api.expect(page.get_by_test_id("org-upgrade-retry")).to_be_enabled()  # The form opens again.
        assert JourneyEvidence.screenshot(page, "multi-site-retry-refused.png").exists()  # The refusal.
        JourneyEvidence.lose_page(page, False)  # The cloud answers both pages again.
        page.get_by_test_id("org-upgrade-retry").click()  # The second try of the retry.
        page.wait_for_url(OPTIONS_PATH)  # The whole read accepts the retry.
        banner = page.get_by_test_id("org-upgrade-retry-banner-devices")  # The devices of the retry.
        sync_api.expect(banner).to_contain_text(WEST_AP_MAC)  # The failed access point of West.
        assert JourneyEvidence.screenshot(page, "multi-site-retry-recovered.png").exists()  # The recovery.
