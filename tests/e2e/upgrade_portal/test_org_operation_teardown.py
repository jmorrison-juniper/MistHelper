"""Browser journeys for issue #3518: the teardown ends each operation that a test left live.

Why:
    A multi-site journey that failed before its cancel left its operation
    live. The operation held both stand-in sites, so a later test on the same
    server could fail. On 2026-09-28, the start step failed while the page
    still showed the confirmation page. The old teardown read the page address
    only, so it cancelled nothing.

    These journeys stop the page before the progress page opens, as that run
    did. The release must then end the operation from the Start answer alone.
    A second start then proves that both stand-in sites went back.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each step of the journey.
from pathlib import Path  # Build the path of each screenshot.
from typing import Any  # Playwright objects carry no stable static type here.

import pytest  # Skip the module when Playwright is not installed.

from tests.e2e.upgrade_portal.org_cancel_steps import JOB_PATH, RELOAD_TIMEOUT_MS, OrgCancelSteps
from tests.e2e.upgrade_portal.test_org_start_double_click import (  # The steps of the multi-site forms.
    CONFIRM_PAGE,
    START_ANSWER_TIMEOUT_MS,
    OrgFormSteps,
    OrgStartSteps,
)
from tests.support.upgrade_portal_e2e.org_operations import (  # Issue #3518: the rules under test.
    OrgOperationLedger,
    OrgOperationRelease,
)

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="Playwright is not installed."
)  # The journeys need Playwright.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

STATUS_FIELD = "[data-org-upgrade-field='status']"  # The state of the operation on the progress page.


class HeldStartSteps:
    """Start an operation, and keep the page on the confirmation page."""

    @staticmethod
    def start_and_hold(page: Any) -> tuple[str, Any]:
        """Start the operation, hold the progress page request, and return the id and the held route.

        Why:
            On 2026-09-28, the progress page request reached the server 15.15
            seconds after the start. The page still showed the confirmation
            page when the step failed. A held route makes the same state with
            no long wait.

        Args:
            page: The browser page on the confirmation page.

        Returns:
            The operation id that the held progress page names, and the held route of the progress page.
        """
        held: list[Any] = []  # The progress page request waits here for the test.
        page.route(JOB_PATH, lambda route: held.append(route), times=1)  # Hold the first progress page request.
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The typed word opens the start button.
        logger.info("Start the multi-site operation, and hold its progress page")  # Log before the start.
        with page.expect_response(  # Keep the real server answer of the Start request.
            OrgStartSteps.is_start_answer, timeout=START_ANSWER_TIMEOUT_MS
        ) as started:
            page.get_by_test_id("org-upgrade-start").click()  # The page script sends the Start request.
        status = started.value.status  # The HTTP status of the Start answer.
        assert status == 200, f"The portal refused the Start request with HTTP {status}"  # Name the refusal.
        route = OrgStartSteps.wait_for_hold(page, held)  # The page keeps the confirmation page now.
        match = JOB_PATH.match(route.request.url)  # The journey reads the id with its own rule, not the tap rule.
        assert match is not None, f"The script opened no progress page: {route.request.url}"  # A defect.
        operation_id = str(match.group(1))  # The first group holds the operation id.
        logger.debug("The portal started %s, and the progress page waits", operation_id)  # Log after the start.
        return operation_id, route  # The test decides when the progress page opens.


class TestTheTeardownEndsEachOperation:
    """Prove that the release ends each operation that a test left live."""

    def test_the_release_ends_an_operation_that_the_page_never_showed(
        self, firmware_operator_page: Any, org_operation_ledger: OrgOperationLedger, tmp_path: Path
    ) -> None:
        """The release ends the operation from the Start answer alone (US1 scenarios 1, 2, and 3)."""
        page = firmware_operator_page  # The operator who holds the firmware role.
        OrgFormSteps.open_confirm(page)  # Build one confirmed plan, and take its pre-checks.
        operation_id, route = HeldStartSteps.start_and_hold(page)  # The portal started the operation.
        assert CONFIRM_PAGE.match(page.url), page.url  # The page still shows the confirmation page.
        assert org_operation_ledger.operations == (operation_id,)  # FR-001: the tap read the Start answer.
        # No screenshot here: Chromium paints no frame while a route holds the navigation, so a screenshot times out.
        assert OrgOperationRelease.end_for(page, org_operation_ledger) == 1  # FR-003: one cancel.
        route.continue_()  # The progress page opens now.
        page.wait_for_url(JOB_PATH, timeout=RELOAD_TIMEOUT_MS)  # The page shows the progress page.
        sync_api.expect(page.locator(STATUS_FIELD)).to_have_text("cancelled")  # SC-001: no live operation.
        page.screenshot(path=str(tmp_path / "3518-teardown-cancelled.png"), full_page=True)  # Visual proof.
        assert OrgOperationRelease.end_for(page, org_operation_ledger) == 0  # US1 scenario 2: no second cancel.

    def test_a_new_start_works_after_the_release(
        self, firmware_operator_page: Any, org_operation_ledger: OrgOperationLedger
    ) -> None:
        """The release frees both stand-in sites, so the next start works (SC-001)."""
        page = firmware_operator_page  # The operator who holds the firmware role.
        OrgFormSteps.open_confirm(page)  # Build one confirmed plan, and take its pre-checks.
        first_id = OrgFormSteps.start(page)  # The first operation holds both stand-in sites.
        assert OrgOperationRelease.end_for(page, org_operation_ledger) == 1  # The release ends it.
        OrgFormSteps.open_confirm(page)  # A held site would refuse this plan.
        second_id = OrgFormSteps.start(page)  # The second start needs both sites free.
        assert second_id != first_id  # Each start makes a new operation.
        assert org_operation_ledger.operations == (first_id, second_id)  # FR-001: the ledger keeps the order.
        OrgCancelSteps.cancel(page)  # Free both sites for the next journey.
