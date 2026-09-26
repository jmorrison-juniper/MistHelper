"""Browser journeys for a site whose inventory read stops after the first page.

Why:
    Issue #3424. A site inventory read can stop after the first page. The
    options page then showed the devices of that page as a complete table, and
    the save planned those devices only. The devices of the lost pages stayed
    on the old firmware, and no record named them. These journeys drive a real
    browser through the Caution banner and the refusal of both modes. A
    screenshot records each page for a visual review. The stand-in cloud of
    the browser fixtures answers every read, so no journey sends a firmware
    request.

    The multi-site journey comes first, because pytest keeps the file order.
    The single-site journey creates a run, and that run holds the short-read
    site. The multi-site journey therefore reads the site before a run holds it.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.short_read_seeds import (
    SHORT_SITE_DEVICE_COUNT,
    SHORT_SITE_ID,
    SHORT_SITE_NAME,
)

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)  # The journey steps reach the pytest log.

MODE_PATH = "/select/mode"  # The mode chooser, where each journey starts.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site, which holds one device of each type.
SITE_NAME = "E2E Stand-In Site"  # The name of the first site, which the banner must not name.
TARGET_VERSION = "0.15.1"  # The newer version that the stand-in cloud offers for every model.
DEVICE_TYPES = ("ap", "switch", "gateway")  # The three device types of the multi-site form.
VERSION_FIELD_IDS = ("org-upgrade-version", "org-upgrade-switch-version", "org-upgrade-gateway-version")
CHOSEN_STRATEGY = "serial"  # Neither the form default nor the service default, so a reset shows on the page.
ORG_BANNER_ID = "org-upgrade-partial-inventory"  # The Caution banner of the multi-site options page.
SITE_BANNER_ID = "upgrade-partial-inventory"  # The Caution banner of the single-site options page.
FLASH_ID = "flash-message"  # The shared message region of the layout.
ORG_REFUSAL_TEXT = f"The portal did not read the complete device list at these sites: {SHORT_SITE_NAME}."
SITE_REFUSAL_TEXT = (  # The text of `options.PARTIAL_INVENTORY_MESSAGE`, which the single-site save answers.
    "The portal did not read the complete device list of this site. Reload this page. Then save the options again."
)
RUNS_API_TEMPLATE = "/api/sites/{site_id}/runs"  # The contract path that creates one run for one site.
OPTIONS_PAGE_TEMPLATE = "/runs/{run_id}/options"  # The single-site options page of one run.
OPTIONS_API_SUFFIX = "/options"  # `POST /api/runs/<run_id>/options` is the one writer of the device plan.
CSRF_META_ID = "csrf-meta"  # `layout.html` publishes the token under this identifier.
CSRF_HEADER = "X-CSRFToken"  # `portal.js` sends the token under this header name.
CREATED_STATUS = 201  # The contract answer for a new run.
CONFLICT_STATUS = 409  # FR-037: one live run already holds the site.
BAD_REQUEST_STATUS = 400  # The answer of a refused option save.
BAD_OPTION_CODE = "bad_option"  # The code of every refused single-site option save.
UPGRADE_RUNNING_CODE = "upgrade_already_running"  # The code that FR-037 answers on a second create call.
TYPE_VERSION_SELECT_IDS = (  # One version control for each device type of the single-site page.
    "upgrade-version-select-ap",
    "upgrade-version-select-switch",
    "upgrade-version-select-gateway",
)
OFFERED_VERSION_INDEX = 1  # The entry at 0 is the empty prompt, so the first offered version sits at 1.
OPTIONS_SAVE_ID = "upgrade-options-save-button"  # The save control of the single-site page.
TARGET_ROW_SELECTOR = '[data-testid^="upgrade-target-row-"]'  # One table row for each device that the read kept.
KEPT_DEVICE_COUNT = 3  # The short read keeps one device of each type, which is less than the site list count.
SAVE_TIMEOUT_MS = 10000  # The save call reads the stand-in inventory, which may wait on a busy workstation.
SCREENSHOT_DIRECTORY = (  # The evidence folder of these journeys.
    Path(__file__).parents[3] / "data" / "test-artifacts" / "upgrade-portal-journeys" / "short-inventory-read"
)


def save_screenshot(page: Any, name: str) -> Path:
    """Save one journey screenshot.

    Args:
        page: The browser page.
        name: The file name of the screenshot.

    Returns:
        The path of the saved file.
    """
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep the evidence under the repository data tree.
    path = SCREENSHOT_DIRECTORY / name  # One stable file name for each page state.
    logger.info("Save the screenshot %s", path.name)  # Record the capture before it runs.
    page.screenshot(path=str(path), full_page=True)  # Capture the full page for the visual review.
    logger.debug("Saved the screenshot %s", path.name)  # Record the capture after it ends.
    return path  # The caller proves that the file exists.


def open_the_site_picker(page: Any) -> None:
    """Choose the multi-site mode and open the site picker.

    Args:
        page: The browser page.
    """
    logger.info("Open the multi-site picker")  # Record the step before the first request.
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode chooser with a signed session.
    page.get_by_test_id("mode-multi-site").check()  # Choose the multi-site mode.
    page.get_by_test_id("mode-continue").click()  # Move to the site picker.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.
    logger.debug("The multi-site picker owns the page")  # Record the result of the step.


def continue_to_the_options(page: Any) -> None:
    """Send the site choice and wait for the multi-site options form.

    Args:
        page: The browser page.
    """
    logger.info("Send the site choice")  # Record the step before the click.
    page.get_by_test_id("multi-site-continue").click()  # Store the site set.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait until the form script is ready.
    logger.debug("The multi-site options form owns the page")  # Record the result of the step.


def fill_the_plan(page: Any) -> None:
    """Check each device type, type one version for each type, and choose the serial strategy.

    Args:
        page: The browser page.
    """
    logger.info("Fill the multi-site plan")  # Record the step before the first control changes.
    for device_type in DEVICE_TYPES:  # A checked type shows its version field.
        page.get_by_test_id(f"org-upgrade-type-{device_type}").check()  # A checked box stays checked.
    for field_id in VERSION_FIELD_IDS:  # Each selected site holds one device of each type.
        page.get_by_test_id(field_id).fill(TARGET_VERSION)  # The newer version of every stand-in model.
    page.get_by_test_id(f"org-strategy-{CHOSEN_STRATEGY}").check()  # A choice that a reset would lose.
    logger.debug("The multi-site plan holds %s device type(s)", len(DEVICE_TYPES))  # Record the result.


def create_the_short_site_run(page: Any) -> str:
    """Create one run for the short-read site, or open the live run that holds it.

    Why:
        FR-037 allows one live run for each site. A second pass of this
        journey against the same server meets 409, and the refusal names the
        run to open. The journey follows that instruction.

    Args:
        page: The browser page, on a portal page that publishes the token.

    Returns:
        The key of the run of the short-read site.

    Raises:
        AssertionError: If the create call answers any status other than 201
            and 409, or if a 409 names no run.
    """
    path = RUNS_API_TEMPLATE.format(site_id=SHORT_SITE_ID)  # The contract path of the short-read site.
    token = str(page.get_by_test_id(CSRF_META_ID).get_attribute("content") or "")  # The token of the page.
    headers = {CSRF_HEADER: token, "Content-Type": "application/json"}  # The headers that `portal.js` sends.
    logger.info("Create a run for the short-read site")  # Record the call before it runs.
    answer = page.request.post(path, headers=headers, data="{}")  # The documented create call.
    logger.debug("The create call answered %s", answer.status)  # Record the status after the call.
    body = json.loads(answer.text())  # Both accepted answers carry a JSON body.
    if answer.status == CONFLICT_STATUS:  # A live run already holds the site, and the refusal names it.
        error = body.get("error", {})  # The error envelope of the refusal.
        assert error.get("code") == UPGRADE_RUNNING_CODE, f"{path} answered 409 with {error.get('code')!r}."
        named = str(error.get("details", {}).get("run_id", ""))  # The run that the refusal names.
        assert named, f"{path} answered 409 and named no run to open."
        return named  # Open the live run, as the refusal instructs.
    assert answer.status == CREATED_STATUS, f"{path} answered {answer.status}. The contract fixes 201."
    return str(body["run_id"])  # The key of the run that this call created.


def choose_one_version_for_each_type(page: Any) -> int:
    """Pick the first offered version in each type control of the single-site page.

    Args:
        page: The browser page, on the single-site options page.

    Returns:
        The count of type controls that took a version.
    """
    logger.info("Choose one version for each device type")  # Record the step before the first pick.
    chosen = 0  # No control has taken a version yet.
    for test_id in TYPE_VERSION_SELECT_IDS:  # One control for each device type.
        picker = page.get_by_test_id(test_id)  # The contract fixes this identifier.
        if picker.locator("option").count() > OFFERED_VERSION_INDEX:  # The empty prompt, then each version.
            picker.select_option(index=OFFERED_VERSION_INDEX)  # The first offered version is the newest one.
            chosen += 1  # This device type now holds a version.
    logger.debug("%s type control(s) took a version", chosen)  # Record the result of the step.
    return chosen  # Zero means the page offered no version at all.


def is_options_save(answer: Any) -> bool:
    """Tell whether one response answers the option save call.

    Args:
        answer: The Playwright response object.

    Returns:
        True when the response answers a POST to the option save endpoint.
    """
    return str(answer.request.method) == "POST" and str(answer.url).endswith(OPTIONS_API_SUFFIX)


def test_the_multi_site_page_names_the_short_site_and_refuses_the_save(short_read_operator_page: Any) -> None:
    """The banner and the refusal name the short-read site, and the plan saves after the operator clears it."""
    page = short_read_operator_page  # The separate operator, so no other journey sees the short-read site.
    open_the_site_picker(page)  # Choose the multi-site mode.
    short_row = page.get_by_test_id(f"site-row-{SHORT_SITE_ID}")  # The last row of the picker.
    sync_api.expect(short_row.locator("td.cell-number")).to_have_text(str(SHORT_SITE_DEVICE_COUNT))  # Five devices.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select a site that the cloud reads in full.
    page.get_by_test_id(f"site-select-{SHORT_SITE_ID}").check()  # Select the site whose read stops early.
    assert save_screenshot(page, "multi-site-picker.png").exists()  # The two selected sites.
    continue_to_the_options(page)  # Open the shared options form.
    banner = page.get_by_test_id(ORG_BANNER_ID)  # The Caution banner of the multi-site form.
    sync_api.expect(banner).to_be_visible()  # The operator sees the gap before the plan.
    sync_api.expect(banner).to_contain_text(SHORT_SITE_NAME)  # The banner names the short-read site.
    sync_api.expect(banner).not_to_contain_text(SITE_NAME)  # The complete site stays out of the banner.
    assert save_screenshot(page, "multi-site-banner.png").exists()  # The banner above the form.
    fill_the_plan(page)  # Type the plan of the operator.
    page.get_by_test_id("org-upgrade-review").click()  # Try to save the plan.
    flash = page.get_by_test_id(FLASH_ID)  # The shared message region of the layout.
    sync_api.expect(flash).to_contain_text(ORG_REFUSAL_TEXT)  # The refusal names the short-read site.
    sync_api.expect(flash).not_to_contain_text(SHORT_SITE_ID)  # The site name replaces the identifier.
    assert re.search(r".*/upgrade/org/options$", page.url)  # The page stays on the form, so no plan exists.
    assert save_screenshot(page, "multi-site-refusal.png").exists()  # The refusal on the form.
    page.get_by_test_id("nav-sites").click()  # Go back to the Sites page to clear the short-read site.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.
    short_box = page.get_by_test_id(f"site-select-{SHORT_SITE_ID}")  # The box of the short-read site.
    sync_api.expect(short_box).to_be_checked()  # The picker keeps the stored site set.
    short_box.uncheck()  # Clear the short-read site. A later reload can read it in full.
    continue_to_the_options(page)  # Open the form again with one site.
    sync_api.expect(page.get_by_test_id(ORG_BANNER_ID)).to_have_count(0)  # A complete read shows no banner.
    fill_the_plan(page)  # The refused save stored no options, so the operator types the plan again.
    page.get_by_test_id("org-upgrade-review").click()  # Save the plan.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # The save accepted the plan.
    confirm = page.get_by_test_id("org-upgrade-confirm")  # The summary card of the confirm page.
    sync_api.expect(confirm).to_contain_text(f"Strategy: {CHOSEN_STRATEGY}")  # The choice, not a default.
    sync_api.expect(confirm).to_contain_text("Sites: 1")  # The plan covers the one site with a complete read.
    sync_api.expect(page.get_by_test_id(f"org-upgrade-precheck-row-{SHORT_SITE_ID}")).to_have_count(0)  # No row.
    assert save_screenshot(page, "multi-site-recovered-confirm.png").exists()  # The summary before the typed word.


def test_the_single_site_page_shows_the_banner_and_refuses_the_save(short_read_operator_page: Any) -> None:
    """The single-site page shows the banner, and the save of the short read answers 400 with the reload text."""
    page = short_read_operator_page  # The separate operator, so no other journey sees the short-read site.
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # A portal page publishes the token in its head.
    run_id = create_the_short_site_run(page)  # One run of the short-read site.
    page.goto(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id), wait_until="domcontentloaded")  # The options page.
    banner = page.get_by_test_id(SITE_BANNER_ID)  # The Caution banner of the single-site page.
    sync_api.expect(banner).to_be_visible()  # The operator sees the gap before the plan.
    sync_api.expect(banner).to_contain_text("Reload this page before you save the options.")  # The repair.
    sync_api.expect(page.locator(TARGET_ROW_SELECTOR)).to_have_count(KEPT_DEVICE_COUNT)  # The rows that the read kept.
    assert KEPT_DEVICE_COUNT < SHORT_SITE_DEVICE_COUNT  # The table holds fewer rows than the site list count.
    assert save_screenshot(page, "single-site-banner.png").exists()  # The banner above the device table.
    assert choose_one_version_for_each_type(page) == len(TYPE_VERSION_SELECT_IDS)  # Each type takes a version.
    logger.info("Save the options of the run %s", run_id)  # Record the save call before the click.
    with page.expect_response(is_options_save, timeout=SAVE_TIMEOUT_MS) as event:  # Catch the save answer.
        page.get_by_test_id(OPTIONS_SAVE_ID).click()  # The control that the operator clicks.
    answer = event.value  # The answer of the one writer of the plan.
    logger.debug("The options save answered %s", answer.status)  # Record the status after the call.
    assert answer.status == BAD_REQUEST_STATUS, f"The save answered {answer.status}. A short read answers 400."
    error = json.loads(answer.text()).get("error", {})  # The error envelope of the refusal.
    assert error.get("code") == BAD_OPTION_CODE  # The spec keeps the code of every refused option.
    assert error.get("message") == SITE_REFUSAL_TEXT  # The reload text, not the text of a bad option.
    sync_api.expect(page.get_by_test_id(FLASH_ID)).to_contain_text(SITE_REFUSAL_TEXT)  # The page shows the text.
    assert page.url.endswith(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id))  # The page stays, so no plan exists.
    assert save_screenshot(page, "single-site-refusal.png").exists()  # The refusal above the device table.
