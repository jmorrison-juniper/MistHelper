"""Browser journeys for issue #3242: one click sends one multi-site request.

Why:
    The multi-site forms did not close while a request was in flight. A double
    click on Review, on Start, or on Cancel sent two requests. A second tab got
    a bare refusal that named no job. These journeys drive a real browser
    through the durable multi-site path, and they count the POST requests that
    the page sends.

    Each journey that starts an operation ends with a cancel, so both stand-in
    sites go back for the later browser tests. The fixture of this file also
    cancels an operation that a failed step left running.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import json  # Build the body of the simulated lock store refusal.
import re  # Match the address of each page of the journey.
from collections.abc import Iterator  # The fixture yields one page.
from pathlib import Path  # Build the path of each screenshot.
from typing import Any  # Playwright objects carry no stable static type here.
from urllib.parse import urlsplit  # Read the path of each request address.

import pytest  # Supplies the fixture that cleans up after a failed journey.

from src.upgrade_portal.app.routes.upgrade import LOCK_STORE_DOWN_CODE, LOCK_STORE_DOWN_MESSAGE
from tests.e2e.upgrade_portal.org_cancel_steps import JOB_PATH, RELOAD_TIMEOUT_MS, OrgCancelSteps
from tests.e2e.upgrade_portal.org_precheck_steps import OrgPrecheckSteps  # Issue #3243: the pre-check gate.

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="Playwright is not installed."
)  # The journeys need Playwright.

MODE_PATH = "/select/mode"  # The first page of the multi-site journey.
SITE_PAGE = re.compile(r".*/select/site$")  # The site selection page.
OPTIONS_PAGE = re.compile(r".*/upgrade/org/options$")  # The options page.
CONFIRM_PAGE = re.compile(r".*/upgrade/org/confirm$")  # The confirmation page.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site of `conftest.py`.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site of `conftest.py`.
OPTIONS_API = "/api/org-upgrades/options"  # The Review request of the options form.
SUBMIT_API = "/api/org-upgrades"  # The Start request of the confirmation form.
CANCEL_SUFFIX = "/cancel"  # The end of the Cancel request path. The path also holds the operation id.
SUBMIT_ROUTE = "**/api/org-upgrades"  # The route pattern that holds the first Start request.
OPTIONS_FORM = "form[action='/api/org-upgrades/options']"  # The options form.
START_FORM = "form[action='/api/org-upgrades']"  # The confirmation form.
FORM_STATE = "data-org-form-state"  # The attribute that marks a closed form.
REPLAY_SENTENCE = "This confirmed request already started a multi-site upgrade."  # The FR-004 sentence.
ENDED_STATES = ("cancelled", "completed", "failed")  # An operation in these states holds no site.
HOLD_TRIES = 100  # The bound on the wait for the held request.
HOLD_PAUSE_MS = 50  # The pause between two checks of the held request.


class OrgRequestLog:
    """Count the POST requests that one page sends."""

    def __init__(self, page: Any) -> None:
        """Start to record the path of each POST request of the page.

        Args:
            page: The browser page that the journey drives.
        """
        self.paths: list[str] = []  # One entry for each POST request, in the order of the requests.
        page.on("request", self.record)  # Playwright calls the recorder for each request of the page.

    def record(self, request: Any) -> None:
        """Keep the path of one POST request.

        Args:
            request: One network request of the browser page.
        """
        if request.method == "POST":  # A GET read does not change the server state.
            self.paths.append(urlsplit(request.url).path)  # Keep the path only, with no query.

    def count(self, path: str) -> int:
        """Return how many POST requests went to the exact path.

        Args:
            path: The request path to count.
        """
        return sum(1 for sent in self.paths if sent == path)  # Match the full path only.

    def count_suffix(self, suffix: str) -> int:
        """Return how many POST requests went to a path that ends with the suffix.

        Args:
            suffix: The end of the request path to count.
        """
        return sum(1 for sent in self.paths if sent.endswith(suffix))  # The cancel path holds the operation id.


class OrgFormSteps:
    """Drive the multi-site forms of the capture portal."""

    @staticmethod
    def open_options(page: Any) -> None:
        """Select both stand-in sites, and fill the options form with one version for each family.

        Args:
            page: The browser page of the firmware operator.
        """
        page.goto(MODE_PATH, wait_until="domcontentloaded")  # The journey starts at mode choice.
        page.get_by_test_id("mode-multi-site").check()  # The operator selects many sites.
        page.get_by_test_id("mode-continue").click()  # The page must advance.
        page.wait_for_url(SITE_PAGE)  # The site page must open.
        page.get_by_test_id(f"site-select-{SITE_ID}").check()  # The plan includes the first site.
        page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # The plan includes the second site.
        page.get_by_test_id("multi-site-continue").click()  # The selected sites must persist.
        page.wait_for_url(OPTIONS_PAGE)  # The options page must open.
        page.get_by_test_id("org-upgrade-version").fill("0.15.1")  # The access point version is fixed.
        page.get_by_test_id("org-upgrade-switch-version").fill("0.15.1")  # The switch version is fixed.
        page.get_by_test_id("org-upgrade-gateway-version").fill("0.15.1")  # The gateway version is fixed.

    @staticmethod
    def open_confirm(page: Any) -> None:
        """Send one Review request, and take the pre-checks that the start needs.

        Args:
            page: The browser page of the firmware operator.
        """
        OrgFormSteps.open_options(page)  # Build the plan of both stand-in sites.
        page.get_by_test_id("org-upgrade-review").click()  # One click sends one Review request.
        page.wait_for_url(CONFIRM_PAGE)  # The confirmation page must open.
        OrgPrecheckSteps.take_missing(page)  # Issue #3243: each site needs a verified pre-check.

    @staticmethod
    def start(page: Any) -> str:
        """Type the word, start the operation, and return the operation id.

        Args:
            page: The browser page on the confirmation page.
        """
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The typed word opens the start button.
        page.get_by_test_id("org-upgrade-start").click()  # One click sends one Start request.
        page.wait_for_url(JOB_PATH, timeout=RELOAD_TIMEOUT_MS)  # The progress page must open.
        return OrgFormSteps.operation_id(page)  # The progress page address holds the operation id.

    @staticmethod
    def operation_id(page: Any) -> str:
        """Return the operation id that the address of the progress page holds.

        Args:
            page: The browser page on the progress page.
        """
        match = JOB_PATH.match(page.url)  # The progress page address ends with the operation id.
        assert match is not None, f"The page is not a progress page: {page.url}"  # Any other page is a defect.
        return str(match.group(1))  # The first group holds the operation id.

    @staticmethod
    def is_start_answer(answer: Any) -> bool:
        """Return True for the answer to the Start request.

        Args:
            answer: One network answer of the browser page.
        """
        return answer.request.method == "POST" and urlsplit(answer.url).path == SUBMIT_API  # The start only.


class OrgJourneyCleanup:
    """Hold the steps that free both stand-in sites after a journey."""

    @staticmethod
    def wait_for_hold(page: Any, held: list[Any]) -> Any:
        """Return the held Start request after the route handler stored it.

        Args:
            page: The browser page that sent the request.
            held: The list that the route handler fills.
        """
        for _ in range(HOLD_TRIES):  # The dispatch loop of Playwright runs the handler.
            if held:  # The request waits for the test now.
                return held[0]  # The test decides the answer.
            page.wait_for_timeout(HOLD_PAUSE_MS)  # Let the dispatch loop run the handler.
        raise AssertionError("The Start request did not reach the route.")

    @staticmethod
    def cancel_if_running(page: Any) -> None:
        """Cancel the operation of the progress page when a failed step left it running.

        Args:
            page: The browser page of the journey.
        """
        if page.is_closed() or JOB_PATH.match(page.url) is None:  # No progress page, so no site stays locked.
            return
        page.reload(wait_until="domcontentloaded")  # Read the newest state of the operation.
        status = page.locator("[data-org-upgrade-field='status']").inner_text().strip()  # The shown state.
        if status not in ENDED_STATES:  # A running operation holds both sites.
            OrgCancelSteps.cancel(page)  # Free both sites for the next journey.


@pytest.fixture
def operator_page(firmware_operator_page: Any) -> Iterator[Any]:
    """Yield the firmware operator page, and cancel an operation that a failed step left running.

    Args:
        firmware_operator_page: The browser page of the operator who can start firmware.
    """
    yield firmware_operator_page  # The journey drives this page.
    OrgJourneyCleanup.cancel_if_running(firmware_operator_page)  # A failed journey must not lock the next one.


class TestOrgFormsSendOneRequest:
    """Prove that each multi-site form sends one request for one operator action."""

    def test_a_double_click_sends_one_request_for_each_form(self, operator_page: Any, tmp_path: Path) -> None:
        """A double click on Review, on Start, and on Cancel sends one request each (US1)."""
        page = operator_page  # The operator who holds the firmware role.
        requests = OrgRequestLog(page)  # Count each POST request that the page sends.
        OrgFormSteps.open_options(page)  # Fill the options form of both stand-in sites.
        page.get_by_test_id("org-upgrade-review").dblclick()  # The second click must send nothing.
        page.wait_for_url(CONFIRM_PAGE)  # The first Review request opens the confirmation page.
        assert requests.count(OPTIONS_API) == 1  # FR-001: one Review request.
        OrgPrecheckSteps.take_missing(page)  # Issue #3243: each site needs a verified pre-check.
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The typed word opens the start button.
        page.get_by_test_id("org-upgrade-start").dblclick()  # The second click must send nothing.
        page.wait_for_url(JOB_PATH, timeout=RELOAD_TIMEOUT_MS)  # The first Start request opens the progress page.
        page.screenshot(path=str(tmp_path / "3242-after-start-double-click.png"), full_page=True)  # Visual proof.
        assert requests.count(SUBMIT_API) == 1  # FR-001: one Start request, so no refusal hides the start.
        page.get_by_test_id("org-upgrade-cancel-confirmation").fill("CANCEL")  # The typed word opens Cancel.
        with page.expect_event("load", timeout=RELOAD_TIMEOUT_MS):  # The script reloads after the answer.
            page.get_by_test_id("org-upgrade-cancel").dblclick()  # The second click must send nothing.
        page.reload(wait_until="domcontentloaded")  # The server reads every child job again.
        sync_api.expect(page.locator("[data-org-upgrade-field='status']")).to_have_text("cancelled")  # One cancel.
        assert requests.count_suffix(CANCEL_SUFFIX) == 1  # FR-001: one Cancel request.

    def test_a_second_tab_links_to_the_operation_that_runs(self, operator_page: Any, tmp_path: Path) -> None:
        """A second tab gets a refusal that links to the running operation (US2)."""
        page = operator_page  # Tab A of the operator.
        OrgFormSteps.open_confirm(page)  # Build one confirmed plan, and take its pre-checks.
        second = page.context.new_page()  # Tab B shares the session cookie of tab A.
        second.goto(page.url, wait_until="domcontentloaded")  # Tab B opens the same confirmation page.
        OrgPrecheckSteps.wait_until_ready(second)  # The server paints the field of tab B unlocked.
        operation_id = OrgFormSteps.start(page)  # Tab A starts the operation.
        second.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # Tab B types the word too.
        with second.expect_response(OrgFormSteps.is_start_answer) as refused:  # Keep the real server answer.
            second.get_by_test_id("org-upgrade-start").click()  # Tab B sends the same confirmed plan.
        assert refused.value.status == 409  # The durable record refuses the second start.
        link = second.get_by_test_id("org-upgrade-job-link")  # FR-005: the refusal links to the operation.
        sync_api.expect(link).to_have_attribute("href", f"/upgrade/org/jobs/{operation_id}")  # The same operation.
        sync_api.expect(link).to_have_text(operation_id)  # The link text names the operation.
        sync_api.expect(link).to_be_focused()  # FR-006: a keyboard user lands on the link.
        flash = second.locator(".flash-item")  # The one refusal of tab B.
        sync_api.expect(flash).to_contain_text(REPLAY_SENTENCE)  # FR-004: plain words.
        sync_api.expect(flash).to_contain_text(f"Open its progress page: {operation_id}.")  # One whole sentence.
        sync_api.expect(second.get_by_test_id("org-upgrade-start")).to_be_disabled()  # FR-007: no second try.
        sync_api.expect(second.get_by_test_id("org-upgrade-confirmation")).to_be_disabled()  # The field closes.
        sync_api.expect(second.get_by_test_id("org-upgrade-confirmation")).to_have_value("")  # The word clears.
        second.screenshot(path=str(tmp_path / "3242-second-tab-refusal.png"), full_page=True)  # Visual proof.
        link.click()  # The operator follows the link.
        second.wait_for_url(JOB_PATH)  # The link opens a progress page.
        assert OrgFormSteps.operation_id(second) == operation_id  # Tab B now shows the operation of tab A.
        second.close()  # Close tab B before tab A cancels.
        OrgCancelSteps.cancel(page)  # Free both sites for the next journey.

    def test_a_retryable_refusal_opens_the_form_again(self, operator_page: Any, tmp_path: Path) -> None:
        """The form closes while the request runs, and a refusal that started nothing opens it again (US3)."""
        page = operator_page  # The operator who holds the firmware role.
        OrgFormSteps.open_confirm(page)  # Build one confirmed plan, and take its pre-checks.
        requests = OrgRequestLog(page)  # Count the held Start request and the retry.
        held: list[Any] = []  # The first Start request waits here for the test.
        page.route(SUBMIT_ROUTE, lambda route: held.append(route), times=1)  # Hold only the first Start request.
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The typed word opens the start button.
        page.get_by_test_id("org-upgrade-start").click()  # The request now waits in the route.
        route = OrgJourneyCleanup.wait_for_hold(page, held)  # The request is in flight now.
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # FR-001: closed in flight.
        sync_api.expect(page.get_by_test_id("org-upgrade-confirmation")).to_be_disabled()  # The field closes too.
        sync_api.expect(page.locator(START_FORM)).to_have_attribute(FORM_STATE, "sending")  # FR-002: one state.
        page.screenshot(path=str(tmp_path / "3242-start-in-flight.png"), full_page=True)  # Visual proof.
        fault = {"error": {"code": LOCK_STORE_DOWN_CODE, "message": LOCK_STORE_DOWN_MESSAGE}}  # The 503 body.
        route.fulfill(status=503, content_type="application/json", body=json.dumps(fault))  # Nothing started.
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_enabled()  # FR-003: the operator can retry.
        sync_api.expect(page.get_by_test_id("org-upgrade-confirmation")).to_have_value("CONFIRM")  # The word stays.
        sync_api.expect(page.get_by_test_id("org-upgrade-job-link")).to_have_count(0)  # No operation to link.
        sync_api.expect(page.locator(".flash-item")).to_contain_text(LOCK_STORE_DOWN_MESSAGE)  # The plain cause.
        page.screenshot(path=str(tmp_path / "3242-retryable-refusal.png"), full_page=True)  # Visual proof.
        page.get_by_test_id("org-upgrade-start").click()  # The retry reaches the real server.
        page.wait_for_url(JOB_PATH, timeout=RELOAD_TIMEOUT_MS)  # The retry opens the progress page.
        assert requests.count(SUBMIT_API) == 2  # FR-003: the held request and exactly one retry.
        OrgCancelSteps.cancel(page)  # Free both sites for the next journey.

    def test_a_restored_page_opens_its_forms_again(self, operator_page: Any) -> None:
        """A page that the browser restores from its cache loads again, so no form stays closed (FR-009)."""
        page = operator_page  # The operator who holds the firmware role.
        OrgFormSteps.open_options(page)  # Show the options form.
        page.evaluate("window.misthelperIssue3242 = 'kept'")  # A new document removes this marker.
        page.locator(OPTIONS_FORM).evaluate(f"form => form.setAttribute('{FORM_STATE}', 'sending')")  # Closed.
        with page.expect_event("load", timeout=RELOAD_TIMEOUT_MS):  # The restore handler loads the page again.
            page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
        assert page.evaluate("window.misthelperIssue3242 === undefined")  # A new document replaced the old one.
        sync_api.expect(page.locator(f"form[{FORM_STATE}]")).to_have_count(0)  # No closed form remains.
        sync_api.expect(page.get_by_test_id("org-upgrade-review")).to_be_enabled()  # Review works again.
