"""Browser journeys for the recovery controls of a multi-site operation.

Why:
    Issue #3247. The single-site portal can retry the failed devices of a run,
    check an uncertain run against the running versions, and move the start
    time before the confirmation. The multi-site portal could do none of the
    three. These journeys drive each control through a real browser, from the
    progress page or the confirmation page to the next page.

    The server seeds two operations for one separate operator, because no safe
    journey can make a real child job fail. See `org_control_seeds.py`.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_control_seeds import (
    FIRST_AP_MAC,
    FIRST_SITE_ID,
    FIRST_SWITCH_MAC,
    FIRST_UNCERTAIN_ID,
    NEW_VERSION,
    RECONCILE_OPERATION_ID,
    RECONCILE_WORD,
    RETRY_OPERATION_ID,
    SECOND_AP_MAC,
    SECOND_SITE_ID,
    SECOND_SWITCH_MAC,
    SECOND_UNCERTAIN_ID,
    SITE_NAMES,
)
from tests.support.upgrade_portal_e2e.model_version_picker import ModelVersionPicker  # Verify retry targets by device.

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"  # The first page of the multi-site journey.
OPTIONS_PATH = re.compile(r".*/upgrade/org/options$")  # The multi-site options page.
CONFIRM_PATH = re.compile(r".*/upgrade/org/confirm$")  # The typed confirmation page.
SEED_TRIES = 20  # The server writes the seeds on a thread, so the first read can come too early.
SEED_PAUSE_MS = 500  # The pause between two reads of a seeded page.
FIELD_FORMAT = "%Y-%m-%dT%H:%M"  # The value format of a date and time field.
START_NOW_TEXT = "The upgrade starts at once after you confirm."  # The start line of a plan with no start time.
SUMMARY_ROWS = "[data-testid='org-upgrade-device-summary'] tbody tr"  # One row for each planned device.
CHILD_ROWS = "[data-testid='org-upgrade-site-progress'] tbody tr"  # One row for each child job.


def job_path(operation_id: str) -> str:
    """Return the progress page path of one operation."""
    return f"/upgrade/org/jobs/{operation_id}"


def child_cells(page: Any, site_name: str) -> Any:
    """Return the cells of the child row of one site on the progress page.

    Args:
        page: The browser page that shows the progress page.
        site_name: The site name that heads the child row.

    Returns:
        The cells of the row: the family, the status, Targets, Upgraded, and Failed come first.
    """
    header = page.get_by_role("rowheader", name=site_name, exact=True)  # The site name heads the row.
    return page.locator(CHILD_ROWS).filter(has=header).locator("td")  # The cells of that row only.


def open_seeded_page(page: Any, path: str, test_id: str) -> None:
    """Open one page of a seeded operation, and wait until the seed exists.

    Args:
        page: The browser page of the controls operator.
        path: The page path.
        test_id: The test identifier of the control that the seed shows.
    """
    for _ in range(SEED_TRIES):  # The seed thread can finish after the first test starts.
        page.goto(path, wait_until="domcontentloaded")
        if page.get_by_test_id(test_id).count() == 1:  # The seed exists and shows its control.
            return
        page.wait_for_timeout(SEED_PAUSE_MS)
    sync_api.expect(page.get_by_test_id(test_id)).to_be_visible()  # Report the missing control.


def start_text(field_value: str) -> str:
    """Return the start line that the confirmation page shows for one field value."""
    return f"The upgrade starts at {field_value.replace('T', ' ')} UTC."


def utc_field(hours: int) -> str:
    """Return a date and time field value in UTC, a whole number of hours from now."""
    return (datetime.now(UTC) + timedelta(hours=hours)).strftime(FIELD_FORMAT)


def open_options_of_both_sites(page: Any) -> None:
    """Choose the multi-site mode and both stand-in sites, and open the options page."""
    page.goto(MODE_PATH, wait_until="domcontentloaded")
    page.get_by_test_id("mode-multi-site").check()
    page.get_by_test_id("mode-continue").click()
    page.wait_for_url(re.compile(r".*/select/site$"))
    page.get_by_test_id(f"site-select-{FIRST_SITE_ID}").check()
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()
    page.get_by_test_id("multi-site-continue").click()
    page.wait_for_url(OPTIONS_PATH)


class TestMultiSiteRecoveryControls:
    """Drive the retry, the check, and the move of the start time through a browser."""

    def test_the_retry_plans_only_the_failed_devices(self, controls_operator_page: Any, tmp_path: Path) -> None:
        """The retry narrows the plan to the failed devices, and the clear plans every device again."""
        page = controls_operator_page  # The operator that owns the seeded operations.
        open_seeded_page(page, job_path(RETRY_OPERATION_ID), "org-upgrade-retry-controls")
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-count")).to_have_text("2")
        sync_api.expect(page.get_by_test_id(f"org-upgrade-retry-device-{FIRST_SWITCH_MAC}")).to_be_visible()
        sync_api.expect(page.get_by_test_id(f"org-upgrade-retry-device-{SECOND_AP_MAC}")).to_be_visible()
        assert page.get_by_test_id(f"org-upgrade-retry-device-{FIRST_AP_MAC}").count() == 0  # It upgraded.
        page.screenshot(path=str(tmp_path / "retry-progress.png"), full_page=True)

        page.get_by_test_id("org-upgrade-retry").click()
        page.wait_for_url(OPTIONS_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-banner")).to_contain_text(RETRY_OPERATION_ID)
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-banner-devices")).to_contain_text(FIRST_SWITCH_MAC)
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-banner-devices")).to_contain_text(SECOND_AP_MAC)
        sync_api.expect(page.locator(SUMMARY_ROWS)).to_have_count(2)  # The healthy devices stay off the plan.
        sync_api.expect(page.get_by_test_id("org-upgrade-type-ap")).to_be_checked()
        sync_api.expect(page.get_by_test_id("org-upgrade-type-switch")).to_be_checked()
        sync_api.expect(page.get_by_test_id("org-upgrade-type-gateway")).not_to_be_checked()
        targets = ModelVersionPicker(page)  # Read the narrowed retry through the actual device controls.
        targets.expect_values(
            {FIRST_SWITCH_MAC: NEW_VERSION, SECOND_AP_MAC: NEW_VERSION}
        )  # Both failed devices must keep their saved target versions.
        targets.controls(0, "gateway")  # The retry contains no gateway, so no gateway select must exist.
        targets.controls(0, mac=FIRST_AP_MAC)  # The healthy access point must not reenter the retry.
        page.screenshot(path=str(tmp_path / "retry-options.png"), full_page=True)

        page.get_by_test_id("org-upgrade-review").click()
        page.wait_for_url(CONFIRM_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_contain_text("Devices: 2")
        sync_api.expect(page.get_by_test_id("org-upgrade-firmware")).to_contain_text(
            f"E2E-AP {NEW_VERSION}"
        )  # The model summary must keep the failed access point's version.
        sync_api.expect(page.get_by_test_id("org-upgrade-firmware")).to_contain_text(
            f"E2E-SWITCH {NEW_VERSION}"
        )  # The model summary must keep the failed switch's version.
        page.screenshot(path=str(tmp_path / "retry-confirm.png"), full_page=True)

        page.goto("/upgrade/org/options", wait_until="domcontentloaded")  # The retry stays open until a clear.
        page.get_by_test_id("org-upgrade-retry-clear").click()
        page.wait_for_url(OPTIONS_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-banner")).to_have_count(0)
        sync_api.expect(page.locator(SUMMARY_ROWS)).to_have_count(6)  # Three devices at each of two sites.
        page.screenshot(path=str(tmp_path / "retry-cleared.png"), full_page=True)

    def test_a_retry_with_one_cleared_type_plans_the_other_failed_device(
        self, controls_operator_page: Any, tmp_path: Path
    ) -> None:
        """Issue #3389: the operator clears one type of a retry, and the plan keeps the other failed device."""
        page = controls_operator_page  # The operator that owns the seeded operations.
        open_seeded_page(page, job_path(RETRY_OPERATION_ID), "org-upgrade-retry-controls")
        page.get_by_test_id("org-upgrade-retry").click()
        page.wait_for_url(OPTIONS_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-banner")).to_contain_text(RETRY_OPERATION_ID)
        page.get_by_test_id("org-upgrade-type-switch").uncheck()  # The failed switch waits for a later retry.
        targets = ModelVersionPicker(page)  # Check the retry's selected and excluded rows explicitly.
        targets.expect_state(1, "ap", True)  # The one failed access point remains available.
        targets.expect_state(1, "switch", False)  # The excluded failed switch cannot send a target.
        targets.controls(0, "gateway")  # This narrowed retry has no gateway row to select.
        page.screenshot(path=str(tmp_path / "retry-one-type-options.png"), full_page=True)

        page.get_by_test_id("org-upgrade-review").click()  # The first site now holds no retry device.
        page.wait_for_url(CONFIRM_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_contain_text("Devices: 1")
        sync_api.expect(page.get_by_test_id("org-upgrade-firmware")).to_contain_text(
            f"E2E-AP {NEW_VERSION}"
        )  # The retained access point still names its model-compatible target.
        firmware = page.get_by_test_id("org-upgrade-firmware").inner_text()  # The firmware line of the plan.
        assert "E2E-SWITCH" not in firmware  # The model summary must omit the cleared switch type.
        page.screenshot(path=str(tmp_path / "retry-one-type-confirm.png"), full_page=True)

        page.goto("/upgrade/org/options", wait_until="domcontentloaded")  # The retry stays open until a clear.
        page.get_by_test_id("org-upgrade-retry-clear").click()  # Leave no retry for the next journey.
        page.wait_for_url(OPTIONS_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-retry-banner")).to_have_count(0)

    def test_the_check_proves_one_child_job_and_keeps_the_other(
        self, controls_operator_page: Any, tmp_path: Path
    ) -> None:
        """The check completes the proven child job, and it keeps the child job with no proof."""
        page = controls_operator_page  # The operator that owns the seeded operations.
        open_seeded_page(page, job_path(RECONCILE_OPERATION_ID), "org-upgrade-reconcile-controls")
        sync_api.expect(page.get_by_test_id(f"org-upgrade-reconcile-child-{FIRST_UNCERTAIN_ID}")).to_be_visible()
        sync_api.expect(page.get_by_test_id(f"org-upgrade-reconcile-child-{SECOND_UNCERTAIN_ID}")).to_be_visible()
        button = page.get_by_test_id("org-upgrade-reconcile")
        sync_api.expect(button).to_be_disabled()
        page.get_by_test_id("org-upgrade-reconcile-confirmation").fill("RECONCILE")
        sync_api.expect(button).to_be_disabled()  # The word must name the operation.
        sync_api.expect(page.locator("#org-upgrade-reconcile-hint")).to_contain_text("does not match")
        page.get_by_test_id("org-upgrade-reconcile-confirmation").fill(RECONCILE_WORD.upper())
        sync_api.expect(button).to_be_disabled()  # The identifier holds small letters, so capitals do not match.
        sync_api.expect(page.locator("#org-upgrade-reconcile-hint")).to_contain_text("same capital and small letters")
        page.screenshot(path=str(tmp_path / "reconcile-case-hint.png"), full_page=True)
        page.get_by_test_id("org-upgrade-reconcile-confirmation").fill(RECONCILE_WORD)
        sync_api.expect(button).to_be_enabled()
        page.screenshot(path=str(tmp_path / "reconcile-before.png"), full_page=True)

        button.click()
        page.wait_for_url(re.compile(rf".*{re.escape(job_path(RECONCILE_OPERATION_ID))}$"))
        sync_api.expect(page.get_by_test_id(f"org-upgrade-reconcile-child-{FIRST_UNCERTAIN_ID}")).to_have_count(0)
        evidence = page.get_by_test_id(f"org-upgrade-reconcile-evidence-{SECOND_UNCERTAIN_ID}")
        sync_api.expect(evidence).to_contain_text("The target version runs on 0 of 1 device.")  # Issue #3453.
        sync_api.expect(evidence).not_to_contain_text("devices")  # Issue #3453: one device takes the singular noun.
        sync_api.expect(page.get_by_test_id(f"org-upgrade-device-state-{FIRST_SWITCH_MAC}")).to_have_text("completed")
        sync_api.expect(page.get_by_test_id(f"org-upgrade-device-state-{SECOND_SWITCH_MAC}")).to_have_text(
            "submission_unknown"
        )
        first_cells = child_cells(page, SITE_NAMES[FIRST_SITE_ID])  # The proven child job.
        second_cells = child_cells(page, SITE_NAMES[SECOND_SITE_ID])  # The child job with no proof.
        for cells, counts in ((first_cells, ("1", "1", "0")), (second_cells, ("1", "0", "0"))):  # Issue #3457.
            for index, count in zip((2, 3, 4), counts, strict=True):  # Targets, Upgraded, and Failed.
                sync_api.expect(cells.nth(index)).to_have_text(count)
        for field, count in (("total", "2"), ("upgraded_count", "1"), ("failed_count", "0")):  # The block.
            sync_api.expect(page.locator(f"[data-org-upgrade-field='{field}']")).to_have_text(count)
        assert page.locator("[data-testid^='org-upgrade-reconcile-child-']").count() == 1  # One job keeps no proof.
        assert page.get_by_test_id("org-upgrade-reconcile-confirmation").input_value() == ""  # Type it again.
        page.screenshot(path=str(tmp_path / "reconcile-after.png"), full_page=True)

    def test_the_move_changes_the_start_time_before_the_confirmation(
        self, controls_operator_page: Any, tmp_path: Path
    ) -> None:
        """The confirmation page moves the start time, and an empty field starts the upgrade at once."""
        page = controls_operator_page  # The operator that owns the saved plan.
        open_options_of_both_sites(page)
        ModelVersionPicker(page).select(NEW_VERSION, 6)  # The reschedule must keep all six explicit device targets.
        first_start = utc_field(2)  # Two hours from now.
        page.get_by_test_id("org-upgrade-start-time").fill(first_start)
        page.get_by_test_id("org-upgrade-review").click()
        page.wait_for_url(CONFIRM_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-start-line")).to_contain_text(start_text(first_start))
        sync_api.expect(page.get_by_test_id("org-upgrade-reschedule-start")).to_have_value(first_start)
        page.screenshot(path=str(tmp_path / "reschedule-before.png"), full_page=True)

        moved_start = utc_field(3)  # One hour later than the saved start.
        page.get_by_test_id("org-upgrade-reschedule-start").fill(moved_start)
        page.get_by_test_id("org-upgrade-reschedule").click()
        page.wait_for_url(CONFIRM_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-start-line")).to_contain_text(start_text(moved_start))
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # No firmware without CONFIRM.
        assert page.get_by_test_id("org-upgrade-reschedule-start").input_value() == moved_start  # The stored start.
        page.screenshot(path=str(tmp_path / "reschedule-moved.png"), full_page=True)

        page.get_by_test_id("org-upgrade-reschedule-start").fill("")
        page.get_by_test_id("org-upgrade-reschedule").click()
        page.wait_for_url(CONFIRM_PATH)
        sync_api.expect(page.get_by_test_id("org-upgrade-start-line")).to_contain_text(START_NOW_TEXT)
        assert page.get_by_test_id("org-upgrade-reschedule-start").input_value() == ""  # No start time remains.
        page.screenshot(path=str(tmp_path / "reschedule-now.png"), full_page=True)
