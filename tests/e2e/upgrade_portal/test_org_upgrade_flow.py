"""Browser tests for the organization multi-site upgrade workflow."""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_precheck_steps import OrgPrecheckSteps  # Issue #3243: the pre-check gate.

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"
UPGRADE_ID = "44444444-4444-4444-4444-444444444444"
# WHY: Issue #3249. `conftest.py` fixes these values. The cloud job lists the
# first-site AP as upgraded and the second-site AP as failed. The first site
# runs the new version, and the second site still runs the old version.
FIRST_SITE_AP_MAC = "000000000001"
FIRST_SITE_SWITCH_MAC = "000000000003"
SECOND_SITE_AP_MAC = "000000000101"
SECOND_SITE_SWITCH_MAC = "000000000103"
FIRMWARE_EMAIL = "e2e.operator@juniper.net"  # The typed address of the firmware operator.
CLOUD_ACCOUNT = "e2e.operator@example.invalid"  # The Mist account that the self-read seam answers.
LISTED_FAILURE = "The cloud lists this device as failed."  # The reason when the child holds no error text.


def expect_device(page: Any, mac: str, cells: dict[str, str]) -> None:
    """Require the text of each named cell of one device row.

    Args:
        page: The browser page.
        mac: The MAC address that keys the row.
        cells: The cell name, such as "state", and the text that the cell must hold.
    """
    sync_api.expect(page.get_by_test_id(f"org-upgrade-device-row-{mac}")).to_be_visible()  # One row per device.
    for name, text in cells.items():  # Read each cell that the poll can change.
        sync_api.expect(page.get_by_test_id(f"org-upgrade-device-{name}-{mac}")).to_have_text(text)


class TestOrganizationUpgradeBrowserFlow:
    """Drive the organization mode from site selection through cancellation."""

    def test_a_refused_option_set_stays_in_the_page(self, page: Any) -> None:
        """A refused organization request shows an error inside the page."""
        page.goto(MODE_PATH, wait_until="domcontentloaded")
        page.get_by_test_id("mode-multi-site").check()
        page.get_by_test_id("mode-continue").click()
        page.wait_for_url(re.compile(r".*/select/site$"))
        page.get_by_test_id(f"site-select-{SITE_ID}").check()
        page.get_by_test_id("multi-site-continue").click()
        page.wait_for_url(re.compile(r".*/upgrade/org/options$"))

        for family in ("ap", "switch", "gateway"):
            sync_api.expect(page.get_by_test_id(f"org-upgrade-type-{family}")).to_be_checked()
        page.get_by_test_id("org-upgrade-version").fill("")
        page.get_by_test_id("org-upgrade-switch-version").fill("")
        page.get_by_test_id("org-upgrade-gateway-version").fill("")
        page.get_by_test_id("org-upgrade-review").click()

        sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text("device type")
        sync_api.expect(page.get_by_test_id("org-upgrade-options")).to_be_visible()
        assert page.url.endswith("/upgrade/org/options")

    def test_multisite_options_confirmation_progress_and_cancel(self, firmware_operator_page: Any) -> None:
        """The browser completes every organization page without a live Mist call."""
        page = firmware_operator_page  # This path starts firmware, so it needs a reachable operator address.
        page.goto(MODE_PATH, wait_until="domcontentloaded")
        page.get_by_test_id("mode-multi-site").check()
        page.get_by_test_id("mode-continue").click()
        page.wait_for_url(re.compile(r".*/select/site$"))

        page.get_by_test_id(f"site-select-{SITE_ID}").check()
        page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()
        page.get_by_test_id("multi-site-continue").click()
        page.wait_for_url(re.compile(r".*/upgrade/org/options$"))
        sync_api.expect(page.get_by_test_id("org-upgrade-options")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-type-ap")).to_be_checked()
        sync_api.expect(page.get_by_test_id("org-upgrade-type-switch")).to_be_checked()
        sync_api.expect(page.get_by_test_id("org-upgrade-type-gateway")).to_be_checked()

        page.get_by_test_id("org-upgrade-version").fill("0.15.1")
        page.get_by_test_id("org-upgrade-switch-version").fill("0.15.1")
        page.get_by_test_id("org-upgrade-gateway-version").fill("0.15.1")
        page.get_by_test_id("org-strategy-canary").check()
        page.get_by_test_id("org-upgrade-canary-phases").fill("10,100")
        page.get_by_test_id("org-upgrade-max-failures").fill("0")
        page.get_by_test_id("org-upgrade-review").click()
        page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-firmware")).to_contain_text("Access points 0.15.1")
        sync_api.expect(page.get_by_test_id("org-upgrade-firmware")).to_contain_text("Switches 0.15.1")
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()

        OrgPrecheckSteps.take_missing(page)  # Issue #3243: each site needs a verified pre-check before the submit.
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # The word is still missing.
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_enabled()
        page.get_by_test_id("org-upgrade-start").click()
        page.wait_for_url(re.compile(r".*/upgrade/org/jobs/org-run-[0-9a-f]+$"))
        sync_api.expect(page.get_by_test_id("org-upgrade-progress")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("switch")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("gateway")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("Cancellation")

        # WHY: Issue #3249. The page shows one row for each device of each site,
        # with the version after, the version check, and the failure reason.
        sync_api.expect(page.get_by_test_id("org-upgrade-device-table")).to_be_visible()
        device_rows = page.locator("[data-org-upgrade-devices] tr[data-testid^='org-upgrade-device-row-']")
        assert device_rows.count() == 6  # One access point, one switch, and one gateway at each of two sites.
        expect_device(
            page,
            FIRST_SITE_AP_MAC,
            {"state": "upgraded", "version-after": "0.15.1", "version-check": "Version matches", "failure": ""},
        )
        expect_device(
            page,
            SECOND_SITE_AP_MAC,
            {
                "state": "failed",
                "version-after": "0.14.29216",
                "version-check": "Version mismatch",
                "failure": LISTED_FAILURE,
            },
        )
        expect_device(page, FIRST_SITE_SWITCH_MAC, {"state": "pending", "version-check": "Awaiting version"})
        expect_device(page, SECOND_SITE_SWITCH_MAC, {"state": "pending", "version-check": "Awaiting version"})
        sync_api.expect(page.get_by_test_id("org-upgrade-operator-address")).to_have_text(FIRMWARE_EMAIL)
        sync_api.expect(page.get_by_test_id("org-upgrade-cloud-account")).to_have_text(CLOUD_ACCOUNT)
        sync_api.expect(page.get_by_test_id("org-upgrade-last-update-age")).not_to_have_text("unknown")
        cancel_input = page.get_by_test_id("org-upgrade-cancel-confirmation")
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_disabled()
        cancel_input.fill("CAN")

        def updated_status(route: Any) -> None:
            if route.request.method != "GET":
                route.continue_()
                return
            payload = {
                "upgrade_id": UPGRADE_ID,
                "status": "running",  # Issue #3225: only an operation that can still change keeps the cancel.
                "cancel_allowed": True,  # The server sends this flag with every status answer.
                "current_phase": 2,
                "total": 4,
                "upgraded_count": 3,
                "failed_count": 1,
                "site_upgrades": [
                    {
                        "site_id": SITE_ID,
                        "id": "55555555-5555-5555-5555-555555555555",
                        "status": "completed",
                        "total": 2,
                        "upgraded": 2,
                        "failed": 0,
                        "cancellation_text": "Status: requested. The cancel was accepted. Cancelled: 001122334455.",
                    },
                    {
                        "site_id": SECOND_SITE_ID,
                        "id": "66666666-6666-6666-6666-666666666666",
                        "status": "failed",
                        "total": 2,
                        "upgraded": 1,
                        "failed": 1,
                        "cancellation_text": "Status: unavailable. No cancellation is available.",
                    },
                ],
            }  # Issue #3225: the server builds each Cancellation text, and the page prints it as sent.
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(payload),
            )

        page.route(re.compile(r".*/api/org-upgrades/[^/]+$"), updated_status)
        page.get_by_test_id("org-upgrade-refresh").click()
        sync_api.expect(cancel_input).to_have_value("CAN")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("completed")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("failed")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("Cancelled: 001122334455.")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text(
            "No cancellation is available."
        )
        cancel_input.fill("CANCEL")
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_enabled()
        page.get_by_test_id("org-upgrade-cancel").click()
        page.wait_for_url(re.compile(r".*/upgrade/org/jobs/org-run-[0-9a-f]+$"))
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("requested")
        # WHY: Issue #3220. The portal keeps both sites until the cloud reports
        # every child as ended. The route above answered each status read in the
        # browser, so the server never read the cancelled job. A reload reads it,
        # as the 30-second poll of a real page does, and the sites go back.
        page.unroute(re.compile(r".*/api/org-upgrades/[^/]+$"))  # Let the server answer from now on.
        page.reload(wait_until="domcontentloaded")  # The job page reads every child again.
        status = page.locator("[data-org-upgrade-field='status']")  # The aggregate state.
        sync_api.expect(status).to_have_text("cancelled")  # Every child ended on the cancel.
        # WHY: Issue #3225. A cancelled operation is final, so the page renders
        # no cancel form. The note names the final state instead.
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-controls")).to_have_count(0)  # No form renders.
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-closed")).to_contain_text(
            "The operation is final: cancelled."
        )  # The operator reads why the cancel is gone.
        # WHY: Issue #3249. A cancelled child is final, so the table reads the
        # version that each device runs now. The first site runs the new
        # version, and the second site still runs the old version.
        expect_device(page, FIRST_SITE_SWITCH_MAC, {"state": "cancelled", "version-check": "Version matches"})
        expect_device(page, SECOND_SITE_SWITCH_MAC, {"state": "cancelled", "version-check": "Version mismatch"})
