"""Browser tests for the multi-site section of the history page.

Why:
    Issue #3248. A multi-site upgrade had no history entry. An operator who
    closed the progress page could not find the upgrade again, because only
    the address of the job led back to it. The Runs table also showed each
    stored operation as a broken single-site row.

    The journey starts one multi-site upgrade, finds it in the history, and
    opens its progress page through the row link. A second browser proves that
    another session sees the row without the link. The journey then cancels the
    upgrade, so both stand-in sites go back for the later browser tests.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_cancel_steps import JOB_PATH, OrgCancelSteps
from tests.e2e.upgrade_portal.org_precheck_steps import OrgPrecheckSteps  # Issue #3243: the pre-check gate.

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"
HISTORY_PATH = "/history"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"
SITE_NAMES = "E2E Stand-In Site, E2E Second Stand-In Site"  # `conftest.py` fixes both names, in the site order.
DEVICE_TYPES = "Access points, Switches, Gateways"  # The three families that the options page selects.
FIRMWARE_EMAIL = "e2e.operator@juniper.net"  # The typed address of the firmware operator.


def start_operation(page: Any) -> str:
    """Start one multi-site upgrade of both stand-in sites.

    Args:
        page: The browser page of the firmware operator.

    Returns:
        The operation identifier from the address of the progress page.
    """
    page.goto(MODE_PATH, wait_until="domcontentloaded")
    page.get_by_test_id("mode-multi-site").check()
    page.get_by_test_id("mode-continue").click()
    page.wait_for_url(re.compile(r".*/select/site$"))
    page.get_by_test_id(f"site-select-{SITE_ID}").check()
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()
    page.get_by_test_id("multi-site-continue").click()
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))
    page.get_by_test_id("org-upgrade-version").fill("0.15.1")
    page.get_by_test_id("org-upgrade-switch-version").fill("0.15.1")
    page.get_by_test_id("org-upgrade-gateway-version").fill("0.15.1")
    page.get_by_test_id("org-strategy-canary").check()
    page.get_by_test_id("org-upgrade-canary-phases").fill("10,100")
    page.get_by_test_id("org-upgrade-max-failures").fill("0")
    page.get_by_test_id("org-upgrade-review").click()
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))
    OrgPrecheckSteps.take_missing(page)  # Issue #3243: each site needs a verified pre-check before the submit.
    page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")
    page.get_by_test_id("org-upgrade-start").click()
    page.wait_for_url(JOB_PATH)
    match = JOB_PATH.match(page.url)
    assert match is not None, f"The progress page address holds no operation identifier: {page.url}"
    return match.group(1)


class TestMultiSiteHistory:
    """Find a multi-site upgrade in the history and open it again."""

    def test_the_history_lists_the_operation_and_opens_its_progress_page(
        self, firmware_operator_page: Any, second_operator_page: Any, tmp_path: Path
    ) -> None:
        """The owner opens the upgrade from the history, and another session sees no link."""
        page = firmware_operator_page  # This path starts firmware, so it needs a reachable operator address.
        operation_id = start_operation(page)

        page.goto(HISTORY_PATH, wait_until="domcontentloaded")
        sync_api.expect(page.get_by_test_id("history-operation-section")).to_be_visible()
        sync_api.expect(page.get_by_test_id(f"history-operation-row-{operation_id}")).to_be_visible()
        sync_api.expect(page.get_by_test_id(f"history-operation-sites-{operation_id}")).to_have_text(SITE_NAMES)
        sync_api.expect(page.get_by_test_id(f"history-operation-types-{operation_id}")).to_have_text(DEVICE_TYPES)
        operator_cell = page.get_by_test_id(f"history-operation-operator-address-{operation_id}")
        sync_api.expect(operator_cell).to_have_text(FIRMWARE_EMAIL)
        assert page.locator("[data-testid^='history-run-row-org-run-']").count() == 0  # No broken run row.
        page.screenshot(path=str(tmp_path / "history-owner.png"), full_page=True)

        other = second_operator_page  # A second cookie jar, so a second browser session.
        other.goto(HISTORY_PATH, wait_until="domcontentloaded")
        sync_api.expect(other.get_by_test_id(f"history-operation-not-owned-{operation_id}")).to_be_visible()
        assert other.get_by_test_id(f"history-operation-open-{operation_id}").count() == 0  # No link to a refusal.
        other.screenshot(path=str(tmp_path / "history-second-operator.png"), full_page=True)

        page.get_by_test_id(f"history-operation-open-{operation_id}").click()
        page.wait_for_url(JOB_PATH)
        assert page.url.endswith(f"/upgrade/org/jobs/{operation_id}")
        sync_api.expect(page.get_by_test_id("org-upgrade-progress")).to_be_visible()
        OrgCancelSteps.cancel(page)  # Issue #3245: wait for this cancel, because each job holds its own identifier.

        page.goto(HISTORY_PATH, wait_until="domcontentloaded")
        sync_api.expect(page.get_by_test_id(f"history-operation-state-{operation_id}")).to_have_text("cancelled")
        page.screenshot(path=str(tmp_path / "history-after-cancel.png"), full_page=True)
