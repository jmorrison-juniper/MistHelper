"""Browser journeys for the cascade phase card of a multi-site operation.

Why:
    Issue #3245. A single-site run page shows each cascade phase until the
    devices of that phase settle. The multi-site progress page showed the child
    job states only, so the page could read "completed" while the devices still
    rebooted. These journeys start a real multi-site upgrade of both stand-in
    sites, and they read the phase card in a real browser.

    The browser server replaces the watch thread with a scripted starter. Each
    page read and each poll moves the watch one step. Each answer shows the
    state from before its own step, so each Refresh press shows one more step.
    The 30-second poll of the page can add a step too. The journeys therefore
    require an order that only moves forward, and not an exact count of steps.

    Each journey ends with a cancel and a reload, so both stand-in sites go
    back for the later browser tests.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_cancel_steps import JOB_PATH, OrgCancelSteps
from tests.e2e.upgrade_portal.org_precheck_steps import OrgPrecheckSteps  # Issue #3243: the pre-check gate.

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="Playwright is not installed."
)  # The test needs Playwright.

MODE_PATH = "/select/mode"  # The first page of the multi-site journey.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site of `conftest.py`.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site of `conftest.py`.
PHASE_NAMES = ("gateways", "switches", "aps", "clients")  # The cascade order of the single-site driver.
PHASE_LABELS = {
    "gateways": "Gateways",
    "switches": "Switches",
    "aps": "Access points",
    "clients": "Wireless clients",
}  # The page shows these names.
PHASE_RANK = {"pending": 0, "waiting": 1, "settled": 2, "skipped": 2, "failed": 2}  # A phase only moves forward.
WATCH_RANK = {"Not started": 0, "Active": 1, "Finished": 2, "Stopped": 2}  # The watch only moves forward.
ENDED_COUNT = re.compile(r"^(\d+ of \d+ settled|All settled)$")  # The count sentence of an ended phase.
REFRESH_LIMIT = 10  # Four phases need five steps. The limit leaves room for the automatic poll.
PAINT_TRIES = 20  # The paint follows the answer in the same task, so a few short reads find it.
PAINT_PAUSE_MS = 100  # The pause between two reads of the painted card.


def start_operation(page: Any) -> str:
    """Start one multi-site upgrade of the three device families at both stand-in sites.

    Args:
        page: The browser page of the firmware operator.

    Returns:
        The operation identifier from the address of the progress page.
    """
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # The journey starts at mode choice.
    page.get_by_test_id("mode-multi-site").check()  # The operator selects many sites.
    page.get_by_test_id("mode-continue").click()  # The page must advance.
    page.wait_for_url(re.compile(r".*/select/site$"))  # The site page must open.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # The plan includes the first site.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # The plan includes the second site.
    page.get_by_test_id("multi-site-continue").click()  # The selected sites must persist.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # The options page must open.
    page.get_by_test_id("org-upgrade-version").fill("0.15.1")  # The access point version is fixed.
    page.get_by_test_id("org-upgrade-switch-version").fill("0.15.1")  # The switch version is fixed.
    page.get_by_test_id("org-upgrade-gateway-version").fill("0.15.1")  # The gateway version is fixed.
    page.get_by_test_id("org-upgrade-review").click()  # The review page must use the plan.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # The confirm page must open.
    OrgPrecheckSteps.take_missing(page)  # Issue #3243: each site needs a verified pre-check before the submit.
    page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The operator confirms the write.
    page.get_by_test_id("org-upgrade-start").click()  # The page starts the operation.
    page.wait_for_url(JOB_PATH)  # The progress page must open.
    match = JOB_PATH.match(page.url)  # The address carries the operation key.
    assert match is not None, f"The progress page address holds no operation identifier: {page.url}"  # The key exists.
    return match.group(1)  # The caller polls this operation.


def phase_snapshot(page: Any) -> dict[str, Any]:
    """Return the watch label, the four phase states and counts, the current phase, and the poll rule.

    Args:
        page: The browser page on the progress page of the operation.

    Returns:
        The values that an operator reads on the phase card.
    """
    card = page.get_by_test_id("org-upgrade-phases")  # The phase card of the operation.
    return {  # The caller compares one painted card.
        "watch": card.get_by_test_id("org-upgrade-phase-watch-state").inner_text().strip(),
        "states": tuple(card.get_by_test_id(f"org-upgrade-phase-{name}").inner_text().strip() for name in PHASE_NAMES),
        "counts": tuple(
            card.get_by_test_id(f"org-upgrade-phase-progress-{name}").inner_text().strip() for name in PHASE_NAMES
        ),
        "current": page.locator("[data-org-upgrade-field='current_phase']").inner_text().strip(),
        "active": page.locator("[data-org-upgrade-region]").get_attribute("data-phase-active"),
    }


def refreshed_snapshot(page: Any, previous: dict[str, Any]) -> dict[str, Any]:
    """Press Refresh, wait for the status answer, and return the painted card.

    Args:
        page: The browser page on the progress page of the operation.
        previous: The card before the press.

    Returns:
        The first painted card that differs from the previous card, or the last card read.
    """
    with page.expect_response(
        lambda answer: "/api/org-upgrades/" in answer.url and answer.request.method == "GET"
    ):  # The refresh must reach the poll.
        page.get_by_test_id("org-upgrade-refresh").click()  # The operator asks for the next step.
    current = phase_snapshot(page)  # The first paint can already change.
    for _ in range(PAINT_TRIES):  # The paint runs after the answer arrives.
        if current != previous:  # A changed card proves the paint finished.
            return current  # The caller checks the new order.
        page.wait_for_timeout(PAINT_PAUSE_MS)  # The browser needs time to paint.
        current = phase_snapshot(page)  # The next read can show the paint.
    return current  # The step did not change the card, and the caller checks the order.


def require_cascade_order(snapshot: dict[str, Any]) -> None:
    """Require that no phase moves ahead of an earlier phase, and that the current phase names the wait.

    Args:
        snapshot: One painted card.
    """
    ranks = [PHASE_RANK[state] for state in snapshot["states"]]  # An unknown state fails with its name.
    assert ranks == sorted(
        ranks, reverse=True
    ), f"A phase moved ahead of an earlier phase: {snapshot}"  # The cascade order holds.
    waiting = [
        name for name, state in zip(PHASE_NAMES, snapshot["states"], strict=True) if state == "waiting"
    ]  # The active phase, if any.
    assert len(waiting) <= 1, f"More than one phase waits: {snapshot}"  # Only one phase can wait.
    assert snapshot["current"] == (
        PHASE_LABELS[waiting[0]] if waiting else "Not reported"
    ), snapshot  # The label names the wait.


def require_forward_step(previous: dict[str, Any], current: dict[str, Any]) -> None:
    """Require that the watch and each phase only move forward between two cards.

    Args:
        previous: The card before the step.
        current: The card after the step.
    """
    assert (
        WATCH_RANK[current["watch"]] >= WATCH_RANK[previous["watch"]]
    ), f"The watch moved back: {current}"  # The watch never moves back.
    for name, before, after in zip(
        PHASE_NAMES, previous["states"], current["states"], strict=True
    ):  # Each phase has one step.
        assert (
            PHASE_RANK[after] >= PHASE_RANK[before]
        ), f"The {name} phase moved back: {previous} -> {current}"  # The phase never moves back.


class TestMultiSitePhaseCascade:
    """Follow the cascade phases of one multi-site operation in a real browser."""

    def test_the_phase_card_follows_each_phase_to_the_end(self, firmware_operator_page: Any, tmp_path: Path) -> None:
        """The card shows each phase end in the cascade order, and the watch ends as "Finished"."""
        page = firmware_operator_page  # This path starts firmware, so it needs a reachable operator address.
        start_operation(page)  # The test needs one running operation.
        sync_api.expect(page.get_by_test_id("org-upgrade-phases")).to_be_visible()  # The phase card appears.
        seen = [phase_snapshot(page)]  # The first card, before any Refresh press.
        require_cascade_order(seen[0])  # The first card obeys the cascade.
        page.screenshot(path=str(tmp_path / "phase-step-0.png"), full_page=True)  # The artifact records the start.
        for step in range(1, REFRESH_LIMIT + 1):  # Each press shows one more step.
            if seen[-1]["watch"] == "Finished":  # The watch no longer needs a refresh.
                break  # The final card is ready.
            seen.append(refreshed_snapshot(page, seen[-1]))  # The next card follows one poll.
            require_cascade_order(seen[-1])  # The new card obeys the cascade.
            require_forward_step(seen[-2], seen[-1])  # The new card only moves forward.
            page.screenshot(
                path=str(tmp_path / f"phase-step-{step}.png"), full_page=True
            )  # The artifact records the step.
        final = seen[-1]  # The card after the last press.
        assert final["watch"] == "Finished", f"The watch did not end: {seen}"  # The watch reached the end.
        assert all(state in ("settled", "skipped") for state in final["states"]), final  # Every phase ended.
        assert all(ENDED_COUNT.match(count) for count in final["counts"]), final  # Every count shows an end.
        assert final["active"] == "false"  # The watch ended, so the poll rule reads the job state only.
        assert {state for card in seen for state in card["states"]} >= {"waiting", "settled"}  # The card moved.
        OrgCancelSteps.cancel(page)  # Both stand-in sites go back for the later tests.

    def test_a_cancel_stops_the_phase_watch(self, firmware_operator_page: Any, tmp_path: Path) -> None:
        """A cancel writes the "Stopped" watch state, and no phase waits after the stop."""
        page = firmware_operator_page  # This path starts firmware, so it needs a reachable operator address.
        start_operation(page)  # The test needs one running operation.
        sync_api.expect(page.get_by_test_id("org-upgrade-phases")).to_be_visible()  # The phase card appears.
        before = phase_snapshot(page)  # The card of the running watch.
        assert before["watch"] == "Active", before  # The cancel starts during the watch.
        page.screenshot(
            path=str(tmp_path / "cancel-watch-before.png"), full_page=True
        )  # The artifact records the start.
        OrgCancelSteps.cancel(page)  # The script reload takes the stop step, and the helper reload shows it.
        sync_api.expect(page.get_by_test_id("org-upgrade-phase-watch-state")).to_have_text(
            "Stopped"
        )  # The page shows the stop.
        after = phase_snapshot(page)  # The card after the stop.
        for name, was, now in zip(PHASE_NAMES, before["states"], after["states"], strict=True):  # Keep each end.
            assert (
                PHASE_RANK[was] < 2 or now == was
            ), f"The stop changed the ended {name} phase: {after}"  # Ended phases stay stable.
        assert "waiting" not in after["states"] and after["current"] == "Not reported", after  # The reset rule.
        assert after["active"] == "false"  # The watch ended, so the poll rule reads the job state only.
        page.screenshot(path=str(tmp_path / "cancel-watch-after.png"), full_page=True)  # The artifact records the stop.
