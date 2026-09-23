from __future__ import annotations

import re  # Match dynamic progress addresses that include a run identifier.
import time  # Measure each browser step for the journey evidence.
from pathlib import Path  # Keep screenshots under the assigned artifact folder.
from typing import Any  # Playwright page objects have no local stub type.

import pytest  # Use xfail markers for known parity gaps.

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")  # Skip without Playwright.
expect = sync_api.expect  # Use Playwright retrying assertions for rendered controls.

MODE_PATH = "/select/mode"  # The shared entry page of the portal.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site.
PREPARED_RUN_ID = "e2e-prepared-run-0001"  # The seeded single-site run with options and confirmation.
START_READY_RUN_ID = "e2e-start-ready-run-0001"  # The seeded single-site run that can start.
TARGET_VERSION = "0.15.1"  # The version that every stand-in model offers.
REPO_ROOT = Path(__file__).parents[4]  # Tests change the working directory, so artifact paths must be absolute.
SHOTS = REPO_ROOT / "data/test-artifacts/upgrade-portal-journeys/upj-parity"  # Required screenshot directory.
OK_STATUS = 200  # A rendered page answers this status.
ACCEPTED_STATUS = 202  # A start request answers this status.

pytestmark = pytest.mark.journey  # The journey conftest runs this file only when explicitly requested.


def _release_locks(page: Any) -> None:
    """Release locks that site selection can create during one parity test."""
    for site_id in (SITE_ID, SECOND_SITE_ID):  # Try both stand-in sites after each multi-site visit.
        try:  # A missing lock is acceptable, because the next test still needs cleanup.
            page.request.delete(f"/api/sites/{site_id}/lock")  # Release only locks owned by this browser session.
        except Exception:  # The assertion under test must remain the reported result.
            pass  # The server expires an unreleased test lock after its lease.


def _watch(page: Any) -> dict[str, list[str]]:
    """Collect browser errors so a failed parity step keeps its evidence."""
    events: dict[str, list[str]] = {"console": [], "pageerror": [], "requestfailed": [], "http": []}  # Store text only.
    page.on("console", lambda message: events["console"].append(message.text))  # Keep console messages.
    page.on("pageerror", lambda error: events["pageerror"].append(str(error)))  # Keep script errors.
    page.on("requestfailed", lambda request: events["requestfailed"].append(request.url))  # Keep failed requests.
    page.on(
        "response", lambda response: events["http"].append(response.url) if response.status >= 400 else None
    )  # Keep bad responses.
    return events  # The caller can assert that the page stayed quiet.


def _shot(page: Any, journey: str, step: int, name: str) -> None:
    """Save one full-page screenshot in the assigned folder."""
    SHOTS.mkdir(parents=True, exist_ok=True)  # Create only the assigned artifact folder.
    page.screenshot(path=str(SHOTS / f"{journey}-{step:02d}-{name}.png"), full_page=True)  # Capture visible evidence.


def _open(page: Any, path: str, journey: str, step: int, name: str) -> None:
    """Open one page and capture it."""
    started = time.perf_counter()  # Measure the step before navigation.
    answer = page.goto(path, wait_until="domcontentloaded")  # Open the portal page under test.
    elapsed = time.perf_counter() - started  # Keep a timing value for debugging failures.
    page.evaluate("performance.getEntriesByType('navigation').map(entry => entry.duration)")  # Read navigation timing.
    assert elapsed >= 0  # Prove the timing path ran without changing test behavior.
    assert (
        answer is not None and answer.status == OK_STATUS
    ), f"{path} answered {answer and answer.status}."  # Require render.
    _shot(page, journey, step, name)  # Save the evidence after the page settled.


def _open_multi_options(page: Any, journey: str, step: int) -> int:
    """Open the multi-site options page with both stand-in sites selected."""
    _open(page, MODE_PATH, journey, step, "mode")  # Record the mode picker.
    page.get_by_test_id("mode-multi-site").check()  # Select the multi-site mode.
    page.get_by_test_id("mode-continue").click()  # Continue to the site picker.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker renders.
    _shot(page, journey, step + 1, "sites")  # Record the unchecked site picker.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select the first stand-in site.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # Select the second stand-in site.
    page.get_by_test_id("multi-site-continue").click()  # Continue to the organization options page.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait until the options page renders.
    _shot(page, journey, step + 2, "org-options")  # Record the multi-site options page.
    return step + 3  # Tell the caller the next screenshot number.


def _fill_multi_options(page: Any) -> None:
    """Fill all multi-site family versions with the stand-in target version."""
    page.get_by_test_id("org-upgrade-version").fill(TARGET_VERSION)  # Set the AP target.
    page.get_by_test_id("org-upgrade-switch-version").fill(TARGET_VERSION)  # Set the switch target.
    page.get_by_test_id("org-upgrade-gateway-version").fill(TARGET_VERSION)  # Set the gateway target.
    page.get_by_test_id("org-strategy-canary").check()  # Use the staged strategy shared by both modes.
    page.get_by_test_id("org-upgrade-canary-phases").fill("1,10,50,100")  # Set explicit phases.
    page.get_by_test_id("org-upgrade-max-failures").fill("5")  # Set the visible failure threshold.


@pytest.mark.xfail(
    strict=True,
    reason=(
        "#3204 #3205 #3209 (P-10, P-19, P-21, P-22, P-23, P-24): "
        "multi-site options lack per-device and advanced controls"
    ),
)
def test_options_page_pair_has_the_same_main_controls(page: Any) -> None:
    """The options pages must expose the same controls before a firmware write."""
    events = _watch(page)  # Collect browser evidence for this page pair.
    try:  # Release locks even when a parity assertion fails.
        _open(page, f"/runs/{PREPARED_RUN_ID}/options", "options", 1, "single-options")  # Single options.
        single_controls = {  # Read controls that single-site mode exposes.
            "per_device": page.get_by_test_id("upgrade-target-table").is_visible(),  # Per-device target rows.
            "stable": page.get_by_test_id("upgrade-stable-version-group").is_visible(),  # Stable version choice.
            "p2p": page.get_by_test_id("upgrade-p2p-group").is_visible(),  # AP peer-to-peer controls.
            "rrm": page.get_by_test_id("upgrade-rrm-first-batch-percentage-field").is_visible(),  # RRM details.
            "ssr": page.get_by_test_id("upgrade-ssr-channel-field").count() == 1,  # SSR release train.
        }
        _open_multi_options(page, "options", 2)  # Multi-site options.
        multi_controls = {  # Read the counterpart controls in multi-site mode.
            "per_device": page.get_by_test_id("upgrade-target-table").count() == 1,  # Expected per-device rows.
            "stable": page.get_by_test_id("upgrade-stable-version-group").count() == 1,  # Expected stable choice.
            "p2p": page.get_by_test_id("upgrade-p2p-group").count() == 1,  # Expected AP peer-to-peer controls.
            "rrm": page.get_by_test_id("upgrade-rrm-first-batch-percentage-field").count()
            == 1,  # Expected RRM details.
            "ssr": page.get_by_test_id("upgrade-ssr-channel-field").count() == 1,  # Expected SSR release train.
        }
        assert events == {"console": [], "pageerror": [], "requestfailed": [], "http": []}  # No browser fault.
        assert multi_controls == single_controls  # Known gap: multi-site lacks several controls.
    finally:  # Cleanup must run after the known failure.
        _release_locks(page)  # Release locks for the next browser journey.


@pytest.mark.xfail(
    strict=True, reason="#3243 #3222 (P-27, P-28): multi-site confirm omits pre-check, warnings, and advanced summary"
)
def test_confirm_page_pair_has_the_same_review_content(page: Any) -> None:
    """The confirm pages must show the same safety review before the typed word."""
    events = _watch(page)  # Collect browser evidence for this page pair.
    try:  # Release locks even when the parity assertion fails.
        _open(page, f"/runs/{PREPARED_RUN_ID}/confirm", "confirm", 1, "single-confirm")  # Single confirm page.
        single_review = {  # Read safety review sections in single-site mode.
            "precheck": page.get_by_text("Pre-check capture").count() > 0,  # Pre-check gate is visible.
            "warnings": page.get_by_test_id("upgrade-warning-list").is_visible(),  # Plan warnings are visible.
            "advanced": page.get_by_test_id("upgrade-advanced-summary").is_visible(),  # Advanced summary is visible.
            "confirm": page.get_by_test_id("upgrade-confirm-input").is_visible(),  # Typed confirmation exists.
        }
        next_step = _open_multi_options(page, "confirm", 2)  # Open multi-site options first.
        _fill_multi_options(page)  # Fill all required multi-site fields.
        page.get_by_test_id("org-upgrade-review").click()  # Submit the multi-site options form.
        page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # Wait for multi-site confirm.
        _shot(page, "confirm", next_step, "org-confirm")  # Record the multi-site confirm page.
        multi_review = {  # Read counterpart sections in multi-site mode.
            "precheck": page.get_by_text("Pre-check capture").count() > 0,  # Expected pre-check gate.
            "warnings": page.get_by_test_id("upgrade-warning-list").count() == 1,  # Expected warnings.
            "advanced": page.get_by_test_id("upgrade-advanced-summary").count() == 1,  # Expected advanced summary.
            "confirm": page.get_by_test_id("org-upgrade-confirmation").is_visible(),  # Typed confirmation exists.
        }
        assert events == {"console": [], "pageerror": [], "requestfailed": [], "http": []}  # No browser fault.
        assert multi_review == single_review  # Known gap: multi-site confirm is shorter.
    finally:  # Cleanup must run after the known failure.
        _release_locks(page)  # Release locks for the next browser journey.


@pytest.mark.fresh_server
@pytest.mark.xfail(
    strict=True,
    reason="#3244 to #3249 (P-38 to P-47, P-50): multi-site progress lacks run controls",
)
def test_progress_page_pair_has_the_same_run_controls(firmware_operator_page: Any) -> None:
    """The progress pages must show the same device detail and recovery controls."""
    page = firmware_operator_page  # Use the operator that may start firmware writes.
    events = _watch(page)  # Collect browser evidence for this page pair.
    try:  # Release locks even when the parity assertion fails.
        _open(page, f"/runs/{START_READY_RUN_ID}/confirm", "progress", 1, "single-confirm")  # Open start gate.
        page.get_by_test_id("upgrade-confirm-input").fill("CONFIRM")  # Type the required word.
        expect(page.get_by_test_id("upgrade-start-button")).to_be_enabled()  # Wait for the gate to open.
        with page.expect_response(
            lambda response: response.url.endswith(f"/api/runs/{START_READY_RUN_ID}/start")
        ) as start_event:  # Watch the start call.
            page.get_by_test_id("upgrade-start-button").click()  # Start the seeded single-site run.
        assert start_event.value.status == ACCEPTED_STATUS  # Prove the single-site run started.
        page.wait_for_url(re.compile(rf".*/runs/{START_READY_RUN_ID}$"))  # Wait for the run page.
        _shot(page, "progress", 2, "single-progress")  # Record the single-site progress page.
        single_progress = {  # Read single-site progress and recovery controls.
            "phases": page.get_by_test_id("upgrade-phase-gateways").is_visible(),  # Cascade phases exist.
            "devices": page.get_by_test_id("upgrade-run-table").is_visible(),  # Per-device table exists.
            "captures": page.get_by_text("Post-check capture").count() > 0,  # Capture fields exist.
            "mist_account": page.get_by_test_id("upgrade-cloud-account").is_visible(),  # Mist account is visible.
            "stop": page.get_by_test_id("stop-open-button").count() == 1,  # Stop control can exist.
        }
        next_step = _open_multi_options(page, "progress", 3)  # Open multi-site options.
        _fill_multi_options(page)  # Fill all required family versions.
        page.get_by_test_id("org-upgrade-review").click()  # Move to confirm.
        page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # Wait for the confirm page.
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # Type the required word.
        expect(page.get_by_test_id("org-upgrade-start")).to_be_enabled()  # Wait for the gate to open.
        page.get_by_test_id("org-upgrade-start").click()  # Start the aggregate operation.
        page.wait_for_url(re.compile(r".*/upgrade/org/jobs/[^/?#]+$"))  # Wait for multi-site progress.
        _shot(page, "progress", next_step, "org-progress")  # Record the multi-site progress page.
        multi_progress = {  # Read counterpart controls in multi-site mode.
            "phases": page.get_by_test_id("upgrade-phase-gateways").count() == 1,  # Expected cascade phases.
            "devices": page.get_by_test_id("upgrade-run-table").count() == 1,  # Expected per-device table.
            "captures": page.get_by_text("Post-check capture").count() > 0,  # Expected capture fields.
            "mist_account": page.get_by_test_id("upgrade-cloud-account").count() == 1,  # Expected account label.
            "stop": page.get_by_test_id("stop-open-button").count() == 1,  # Expected stop control.
        }
        assert events == {"console": [], "pageerror": [], "requestfailed": [], "http": []}  # No browser fault.
        assert multi_progress == single_progress  # Known gap: multi-site progress is site-level only.
    finally:  # Cleanup must run after the known failure.
        _release_locks(page)  # Release locks for any following journey.
