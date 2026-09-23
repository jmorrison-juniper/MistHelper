"""Multi-site operator journeys through the upgrade capture portal (issue #3200).

Why:
    The multi-site mode is the focus of issue #3200. Each journey starts at the
    mode picker and goes as far as the stand-in server allows: the options page,
    the confirm page, the start, the progress page, and a final state. The
    stand-in cloud always reports a running job, so each journey fulfills the
    status read with the final answer that a real cloud sends at the end.

    A check that fails because of a known product defect keeps its assertion
    and carries a strict xfail with the issue number. The file then stays
    green, and the xfail turns red when a fix lands, so the fix author must
    remove the marker.
"""

from __future__ import annotations

import json  # Build the fulfilled status answers.
import re  # Match the page addresses of the multi-site flow.
from collections.abc import Callable, Sequence  # Type the helpers.
from typing import Any  # Playwright objects carry no stub types here.

import pytest

from tests.e2e.upgrade_portal.journeys.evidence import JourneyRecorder  # The evidence of each journey.

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")
expect = sync_api.expect  # The retrying assertion of Playwright.

MODE_PATH = "/select/mode"  # The first page of every journey.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site.
SITE_NAMES = ("E2E Stand-In Site", "E2E Second Stand-In Site")  # The names that the picker shows.
TARGET_VERSION = "0.15.1"  # The newer version that every stand-in model offers.
UNKNOWN_VERSION = "9.9.9"  # A version that no stand-in model offers.
FAMILIES = ("ap", "switch", "gateway")  # The three families of the options page.
VERSION_FIELDS = {  # The version control of each family.
    "ap": "org-upgrade-version",
    "switch": "org-upgrade-switch-version",
    "gateway": "org-upgrade-gateway-version",
}
FAMILY_LABELS = {"ap": "Access points", "switch": "Switches", "gateway": "Gateways"}  # The confirm page words.
COMBINATIONS = (  # Every non-empty family combination, single families first.
    ("ap",),
    ("switch",),
    ("gateway",),
    ("ap", "switch"),
    ("ap", "gateway"),
    ("switch", "gateway"),
    ("ap", "switch", "gateway"),
)
OPTIONS_URL = re.compile(r".*/upgrade/org/options$")  # The options page.
CONFIRM_URL = re.compile(r".*/upgrade/org/confirm$")  # The confirm page.
JOB_URL = re.compile(r".*/upgrade/org/jobs/[^/?#]+$")  # The progress page of one operation.
STATUS_ROUTE = re.compile(r".*/api/org-upgrades/[^/]+$")  # The status read of the progress page.
FLASH = "flash-message"  # The in-page message of a refused request.
PHASE_DEFECT = "#3223: the multi-site path never applies the canary phase rule"  # One reason for each phase case.

pytestmark = pytest.mark.journey  # Every test of this file is an operator journey.


class MultiSiteJourney:
    """Drive the multi-site pages for one operator and record each step."""

    def __init__(self, page: Any, recorder: JourneyRecorder) -> None:
        """Keep the page and the recorder.

        Args:
            page: The Playwright page of the operator.
            recorder: The evidence recorder of the page.
        """
        self.page = page  # Every step drives this page.
        self.recorder = recorder  # Every step records through this object.

    def open_options(self, site_ids: Sequence[str] = (SITE_ID, SECOND_SITE_ID)) -> None:
        """Pick the multi-site mode and the sites, and open the options page.

        Args:
            site_ids: The sites to select, in the order of the picker.
        """
        self.recorder.step("mode page", lambda: self.page.goto(MODE_PATH, wait_until="domcontentloaded"))
        self.page.get_by_test_id("mode-multi-site").check()  # The multi-site bubble.
        self.recorder.step("site page", self._continue_to_sites)  # The site picker of the organization.
        for site_id in site_ids:  # Check each requested site.
            self.page.get_by_test_id(f"site-select-{site_id}").check()  # One site box.
        self.recorder.step("sites selected")  # Record the checked boxes.
        self.recorder.step("options page", self._continue_to_options)  # The multi-site options form.

    def _continue_to_sites(self) -> None:
        """Submit the mode form and wait for the site picker."""
        self.page.get_by_test_id("mode-continue").click()  # Store the mode in the session.
        self.page.wait_for_url(re.compile(r".*/select/site$"))  # The picker follows the mode page.

    def _continue_to_options(self) -> None:
        """Submit the site form and wait for the options page."""
        self.page.get_by_test_id("multi-site-continue").click()  # Store the sites in the session.
        self.page.wait_for_url(OPTIONS_URL)  # The options page follows the picker.

    def choose_families(self, families: Sequence[str], version: str = TARGET_VERSION) -> None:
        """Select the families and fill the version of each selected family.

        Args:
            families: The families to upgrade.
            version: The version for each selected family.
        """
        for family in FAMILIES:  # Walk all three, so a cleared family stays cleared.
            box = self.page.get_by_test_id(f"org-upgrade-type-{family}")  # The family bubble.
            field = self.page.get_by_test_id(VERSION_FIELDS[family])  # The version control of the family.
            if family in families:  # A selected family needs a version.
                box.check()  # Keep or set the bubble.
                field.fill(version)  # One version for the family.
            else:  # A cleared family must not carry a version.
                box.uncheck()  # Clear the bubble.
                if field.is_visible() and field.is_enabled():  # A hidden control needs no clear.
                    field.fill("")  # Clear any saved version.
        self.recorder.step(f"families {'-'.join(families)}")  # Record the form state.

    def review(self, expect_confirm: bool = True) -> None:
        """Send the options form.

        Args:
            expect_confirm: True when the form must reach the confirm page.
        """
        self.page.get_by_test_id("org-upgrade-review").click()  # Send the form.
        if expect_confirm:  # A valid form moves to the confirm page.
            self.page.wait_for_url(CONFIRM_URL)  # The confirm page follows a valid form.
            self.recorder.step("confirm page")  # Record the plan that the operator reviews.
        else:  # A refused form stays on the options page.
            expect(self.page.get_by_test_id(FLASH)).to_be_visible()  # The refusal shows in the page.
            self.recorder.step("options refused")  # Record the refusal.

    def start(self) -> str:
        """Type the confirmation word and start the upgrade.

        Returns:
            The address of the progress page.
        """
        self.page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The exact word.
        expect(self.page.get_by_test_id("org-upgrade-start")).to_be_enabled()  # The word opens the button.
        self.recorder.step("confirmation typed")  # Record the open button.
        self.page.get_by_test_id("org-upgrade-start").click()  # Start the operation.
        self.page.wait_for_url(JOB_URL)  # The progress page of the new operation.
        self.recorder.step("progress page")  # Record the first progress view.
        return str(self.page.url)  # The caller may open the same page again.

    def fulfill_status(self, payload: dict[str, Any]) -> None:
        """Answer the status read of the progress page with a fixed body.

        Args:
            payload: The status body that a real cloud sends.
        """

        def answer(route: Any) -> None:
            """Fulfill a GET and pass every other method through."""
            if route.request.method != "GET":  # A cancel post must reach the server.
                route.continue_()  # The server answers the cancel itself.
                return  # Nothing else to do for this request.
            route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

        self.page.route(STATUS_ROUTE, answer)  # Every later status read gets this body.


def final_status(families: Sequence[str], state: str = "completed") -> dict[str, Any]:
    """Build a final status body for the selected families at both sites.

    Args:
        families: The families of the operation.
        state: The final state of every child.

    Returns:
        A status body in the shape that the progress script paints.
    """
    rows = [  # One child for each site and family.
        {
            "site_id": site_id,
            "site_name": site_name,
            "device_family": family,
            "id": f"{family}-job-{index}",
            "status": state,
            "total": 1,
            "upgraded": 1 if state == "completed" else 0,
            "failed": 1 if state == "failed" else 0,
        }
        for index, (site_id, site_name) in enumerate(zip((SITE_ID, SECOND_SITE_ID), SITE_NAMES, strict=True))
        for family in families
    ]
    total = len(rows)  # One target in each child.
    upgraded = sum(row["upgraded"] for row in rows)  # The upgraded count of the whole operation.
    failed = sum(row["failed"] for row in rows)  # The failed count of the whole operation.
    return {"status": state, "total": total, "upgraded_count": upgraded, "failed_count": failed, "site_upgrades": rows}


@pytest.fixture
def operator(firmware_operator_page: Any, journey_recorder: Callable[..., JourneyRecorder]) -> MultiSiteJourney:
    """Return a journey driver for the operator that may start a firmware write."""
    return MultiSiteJourney(firmware_operator_page, journey_recorder(firmware_operator_page))


@pytest.fixture
def reader(page: Any, journey_recorder: Callable[..., JourneyRecorder]) -> MultiSiteJourney:
    """Return a journey driver for the operator that cannot start a firmware write."""
    return MultiSiteJourney(page, journey_recorder(page))


class TestMultiSiteFamilyJourneys:
    """Each family combination goes from the mode picker to a final state."""

    @pytest.mark.parametrize("families", COMBINATIONS, ids=["-".join(item) for item in COMBINATIONS])
    @pytest.mark.fresh_server
    def test_family_combination_reaches_a_final_state(
        self, operator: MultiSiteJourney, families: tuple[str, ...]
    ) -> None:
        """One family combination reaches the confirm page, the start, and a completed state."""
        operator.open_options()  # Both sites, because the AP child names both.
        operator.choose_families(families)  # The families under test.
        operator.review()  # The confirm page shows the plan.
        firmware = operator.page.get_by_test_id("org-upgrade-firmware")  # The version line of the plan.
        for family in FAMILIES:  # Each selected family is named, and each cleared family is absent.
            if family in families:  # A selected family names its version.
                expect(firmware).to_contain_text(f"{FAMILY_LABELS[family]} {TARGET_VERSION}")
            else:  # A cleared family must not appear in the plan.
                expect(firmware).not_to_contain_text(FAMILY_LABELS[family])
        operator.start()  # The operator types the word and starts the operation.
        progress = operator.page.get_by_test_id("org-upgrade-site-progress")  # The child table.
        expect(progress).to_be_visible()  # The table shows at once.
        operator.fulfill_status(final_status(families))  # The cloud reports the end of every child.
        operator.page.get_by_test_id("org-upgrade-refresh").click()  # Read the final state now.
        expect(operator.page.locator("[data-org-upgrade-field='status']")).to_have_text("completed")  # The aggregate.
        for family in families:  # Each family shows its completed child.
            expect(progress).to_contain_text(family)  # The family column names the family.
        operator.recorder.step("final state")  # Record the end of the journey.

    @pytest.mark.xfail(strict=True, reason="#3220: a running cloud word reads as attention_required")
    @pytest.mark.fresh_server
    def test_running_operation_reads_as_running(self, operator: MultiSiteJourney) -> None:
        """A job that the cloud still runs shows a running state after the start."""
        operator.open_options()  # Both sites.
        operator.choose_families(("ap",))  # AP only, so the organization child alone runs.
        operator.review()  # The confirm page.
        operator.start()  # The stand-in cloud answers a job that still runs.
        status = operator.page.locator("[data-org-upgrade-field='status']")  # The aggregate state.
        expect(status).not_to_have_text("attention_required")  # A running job needs no attention.

    @pytest.mark.xfail(strict=True, reason="#3220: the first status read releases the site locks of a running job")
    @pytest.mark.fresh_server
    def test_running_operation_keeps_its_site_locks(self, operator: MultiSiteJourney) -> None:
        """Both sites stay locked while the cloud still runs the job."""
        operator.open_options()  # Both sites.
        operator.choose_families(("ap",))  # AP only.
        operator.review()  # The confirm page.
        operator.start()  # The progress page reads the status once.
        operator.recorder.step("site page during the job", lambda: operator.page.goto("/select/site"))
        for site_id in (SITE_ID, SECOND_SITE_ID):  # Each site of the running job.
            row = operator.page.locator("tr", has=operator.page.get_by_test_id(f"site-select-{site_id}"))
            expect(row).not_to_contain_text("Free")  # A running job holds the site.

    @pytest.mark.xfail(strict=True, reason="#3225: a completed operation still offers the cancel form")
    @pytest.mark.fresh_server
    def test_completed_operation_offers_no_cancel(self, operator: MultiSiteJourney) -> None:
        """A completed operation hides the cancel control."""
        operator.open_options()  # Both sites.
        operator.choose_families(("ap",))  # AP only.
        operator.review()  # The confirm page.
        operator.start()  # The progress page.
        operator.fulfill_status(final_status(("ap",)))  # The cloud reports the end.
        operator.page.get_by_test_id("org-upgrade-refresh").click()  # Read the end now.
        expect(operator.page.locator("[data-org-upgrade-field='status']")).to_have_text("completed")  # The end.
        operator.recorder.step("completed state")  # Record the page with the end state.
        expect(operator.page.get_by_test_id("org-upgrade-cancel-confirmation")).to_be_hidden()  # No cancel.


class TestMultiSiteOptionsJourneys:
    """The options page guides the operator and keeps each choice."""

    @pytest.mark.xfail(strict=True, reason="#3206: the refusal shows above the fold, and the page does not move to it")
    def test_default_form_refusal_is_in_view(self, reader: MultiSiteJourney) -> None:
        """A refused default form shows its message where the operator looks."""
        reader.open_options()  # Both sites.
        reader.page.get_by_test_id("org-upgrade-review").scroll_into_view_if_needed()  # The operator scrolls down.
        reader.review(expect_confirm=False)  # All families selected and no version.
        expect(reader.page.get_by_test_id(FLASH)).to_be_in_viewport()  # The message must be in view.

    @pytest.mark.xfail(strict=True, reason="#3206: the refusal names the internal field version_target")
    def test_unknown_version_names_the_control(self, reader: MultiSiteJourney) -> None:
        """An unknown version names the page control and not an internal field."""
        reader.open_options()  # Both sites.
        reader.choose_families(("ap",), UNKNOWN_VERSION)  # AP only, with a version no model offers.
        reader.review(expect_confirm=False)  # The server refuses the version.
        flash = reader.page.get_by_test_id(FLASH)  # The refusal message.
        expect(flash).not_to_contain_text("version_target")  # No internal name.
        expect(flash).to_contain_text("Access point")  # The label of the control.

    @pytest.mark.xfail(strict=True, reason="#3207: the controls of a cleared family stay visible")
    def test_cleared_families_hide_their_controls(self, reader: MultiSiteJourney) -> None:
        """AP only hides the switch, gateway, reboot, and Junos controls."""
        reader.open_options()  # Both sites.
        reader.choose_families(("ap",))  # AP only.
        for test_id in ("org-upgrade-switch-version", "org-upgrade-gateway-version", "org-upgrade-reboot-group"):
            expect(reader.page.get_by_test_id(test_id)).to_be_hidden()  # A control of a cleared family.
        expect(reader.page.get_by_test_id("org-upgrade-junos-file-action-group")).to_be_hidden()  # Junos only.

    @pytest.mark.xfail(strict=True, reason="#3221: the options page resets families, reboot, Junos action, and force")
    def test_back_from_confirm_keeps_every_choice(self, reader: MultiSiteJourney) -> None:
        """The Back link of the confirm page shows the choices that the operator made."""
        reader.open_options()  # Both sites.
        reader.choose_families(("ap", "switch"))  # Two families.
        reader.page.locator("#org-reboot-no").check()  # No reboot after the write.
        reader.page.locator("#org-junos-no").check()  # No Junos file action.
        reader.page.locator("#org-upgrade-force").check()  # Write even when the version already runs.
        reader.page.get_by_test_id("org-strategy-big_bang").check()  # One phase for every device.
        reader.review()  # The confirm page.
        reader.page.get_by_role("link", name="Back").click()  # The operator goes back to change a value.
        reader.page.wait_for_url(OPTIONS_URL)  # The options page again.
        reader.recorder.step("options after back")  # Record the restored form.
        expect(reader.page.get_by_test_id("org-upgrade-type-gateway")).not_to_be_checked()  # Gateway stays cleared.
        expect(reader.page.locator("#org-reboot-no")).to_be_checked()  # The reboot choice stays no.
        expect(reader.page.locator("#org-junos-no")).to_be_checked()  # The Junos choice stays no.
        expect(reader.page.locator("#org-upgrade-force")).to_be_checked()  # The force choice stays on.
        expect(reader.page.get_by_test_id("org-strategy-big_bang")).to_be_checked()  # The strategy stays.

    @pytest.mark.parametrize(
        ("control", "value"),
        [
            ("org-upgrade-canary-phases", "abc"),
            pytest.param(
                "org-upgrade-canary-phases", "50,10", marks=pytest.mark.xfail(strict=True, reason=PHASE_DEFECT)
            ),
            pytest.param(
                "org-upgrade-canary-phases", "10,101", marks=pytest.mark.xfail(strict=True, reason=PHASE_DEFECT)
            ),
            pytest.param(
                "org-upgrade-canary-phases", "10,50", marks=pytest.mark.xfail(strict=True, reason=PHASE_DEFECT)
            ),
            ("org-upgrade-max-failures", "150"),
            ("org-upgrade-max-failures", "-1"),
            ("org-upgrade-reboot-at", "soon"),
        ],
        ids=[
            "phases-text",
            "phases-descending",
            "phases-over-100",
            "phases-no-100",
            "max-150",
            "max-negative",
            "reboot-text",
        ],
    )
    def test_invalid_value_stays_in_the_page(self, reader: MultiSiteJourney, control: str, value: str) -> None:
        """Each invalid value shows a message in the page and keeps the options page."""
        reader.open_options()  # Both sites.
        reader.choose_families(("ap",))  # A valid family and version.
        reader.page.get_by_test_id(control).fill(value)  # The invalid value under test.
        reader.page.evaluate("() => document.querySelectorAll('input').forEach(i => i.removeAttribute('min'))")
        reader.page.evaluate("() => document.querySelectorAll('input').forEach(i => i.removeAttribute('max'))")
        reader.review(expect_confirm=False)  # The server must refuse the value.
        assert OPTIONS_URL.match(reader.page.url)  # The operator stays on the form.
        expect(reader.page.locator("body")).not_to_contain_text('{"error"')  # No raw JSON in the page.


class TestMultiSiteConfirmJourneys:
    """The confirm page shows the whole plan and guards the start."""

    @pytest.mark.xfail(strict=True, reason="#3222: the confirm page shows counts only, not the sites or the schedule")
    def test_confirm_page_names_the_sites_and_the_schedule(self, reader: MultiSiteJourney) -> None:
        """The plan names each site, the start time, and the failure limit."""
        reader.open_options()  # Both sites.
        reader.choose_families(("ap", "switch"))  # Two families.
        reader.page.get_by_test_id("org-upgrade-start-time").fill("2030-01-01T02:00")  # A future start.
        reader.page.get_by_test_id("org-upgrade-max-failures").fill("10")  # A custom failure limit.
        reader.review()  # The confirm page.
        plan = reader.page.get_by_test_id("org-upgrade-confirm")  # The plan card.
        for name in SITE_NAMES:  # The operator must read each site name.
            expect(plan).to_contain_text(name)  # One site name.
        expect(plan).to_contain_text("2030")  # The start time.
        expect(plan).to_contain_text("10")  # The failure limit.

    @pytest.mark.parametrize("word", ["confirm", "CONFIRM ", " CONFIRM", "CONFIRMED", "", "C0NFIRM"])
    def test_start_stays_closed_for_a_wrong_word(self, reader: MultiSiteJourney, word: str) -> None:
        """Only the exact word opens the start button."""
        reader.open_options()  # Both sites.
        reader.choose_families(("ap",))  # AP only.
        reader.review()  # The confirm page.
        reader.page.get_by_test_id("org-upgrade-confirmation").fill(word)  # A wrong word.
        expect(reader.page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # The start stays closed.


class TestMultiSiteSessionJourneys:
    """A change of mode clears the old multi-site choices."""

    @pytest.mark.xfail(strict=True, reason=PHASE_DEFECT)
    @pytest.mark.fresh_server
    def test_invalid_phases_follow_through_to_the_start(self, operator: MultiSiteJourney) -> None:
        """Descending canary phases must stop before the start, or the start must refuse them."""
        operator.open_options()  # Both sites.
        operator.choose_families(("ap",))  # AP only, so the organization child carries the phases.
        operator.page.get_by_test_id("org-upgrade-canary-phases").fill("50,10")  # Descending phases.
        operator.page.get_by_test_id("org-upgrade-review").click()  # Send the form.
        operator.page.wait_for_timeout(2000)  # Let the answer paint.
        operator.recorder.step("after review with descending phases")  # Record the page that the answer left.
        if CONFIRM_URL.match(operator.page.url):  # The options page accepted the phases.
            operator.page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The exact word.
            operator.page.get_by_test_id("org-upgrade-start").click()  # Try the start.
            operator.page.wait_for_timeout(3000)  # Let the answer paint.
            operator.recorder.step("after start with descending phases")  # Record the start answer.
        assert not JOB_URL.match(operator.page.url), "The portal started a job with descending canary phases."

    @pytest.mark.fresh_server
    def test_second_start_on_busy_sites_explains_the_lock(self, operator: MultiSiteJourney) -> None:
        """A start on sites that a running job holds names the running job."""
        operator.open_options()  # Both sites.
        operator.choose_families(("switch",))  # The switch child stays running, so it holds the sites.
        operator.review()  # The confirm page.
        first_job = operator.start()  # The first job holds both sites.
        operator.recorder.step("options again", lambda: operator.page.goto("/upgrade/org/options"))
        operator.choose_families(("gateway",))  # A second job on the same sites.
        operator.review()  # The confirm page of the second job.
        operator.page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The exact word.
        operator.page.get_by_test_id("org-upgrade-start").click()  # The start must refuse.
        operator.page.wait_for_timeout(3000)  # Let the refusal paint.
        operator.recorder.step("second start refused")  # Record what the operator sees.
        flash = operator.page.get_by_test_id(FLASH)  # The refusal message.
        expect(flash).to_be_visible()  # The operator must see a reason.
        expect(flash).not_to_contain_text("site_lock_wrong_run")  # No internal code.
        assert first_job  # The first job page exists for the operator to open.

    @pytest.mark.xfail(strict=True, reason="#3224: the busy-site refusal names no running job and offers no link")
    @pytest.mark.fresh_server
    def test_busy_site_refusal_links_to_the_running_job(self, operator: MultiSiteJourney) -> None:
        """A start on busy sites links to the job that holds them and closes the start button."""
        operator.open_options()  # Both sites.
        operator.choose_families(("switch",))  # The switch child stays running, so it holds the sites.
        operator.review()  # The confirm page.
        first_job = operator.start()  # The first job holds both sites.
        operator.recorder.step("options again", lambda: operator.page.goto("/upgrade/org/options"))
        operator.choose_families(("gateway",))  # A second job on the same sites.
        operator.review()  # The confirm page of the second job.
        operator.page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The exact word.
        operator.page.get_by_test_id("org-upgrade-start").click()  # The start must refuse.
        expect(operator.page.get_by_test_id(FLASH)).to_be_visible()  # The refusal shows.
        operator.recorder.step("second start refused")  # Record what the operator sees.
        job_key = first_job.rsplit("/", 1)[-1]  # The identifier of the running job.
        expect(operator.page.locator(f"a[href$='{job_key}']")).to_be_visible()  # A link to the running job.
        expect(operator.page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # No second click.

    def test_mode_change_clears_the_site_selection(self, reader: MultiSiteJourney) -> None:
        """Single-site mode and then multi-site mode shows no old site selection."""
        reader.open_options()  # Both sites are stored.
        reader.recorder.step("back to mode", lambda: reader.page.goto(MODE_PATH, wait_until="domcontentloaded"))
        reader.page.get_by_test_id("mode-single-site").check()  # Change the mode.
        reader.recorder.step("single-site site page", reader._continue_to_sites)  # The single-site picker.
        reader.recorder.step("mode again", lambda: reader.page.goto(MODE_PATH, wait_until="domcontentloaded"))
        reader.page.get_by_test_id("mode-multi-site").check()  # Back to multi-site.
        reader.recorder.step("multi-site site page again", reader._continue_to_sites)  # The picker again.
        for site_id in (SITE_ID, SECOND_SITE_ID):  # No old box stays checked.
            expect(reader.page.get_by_test_id(f"site-select-{site_id}")).not_to_be_checked()
