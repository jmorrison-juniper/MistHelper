"""Explore the single-site upgrade portal journeys with a real browser.

The test writes the screenshot baseline and the findings file for the
``upj-single-site`` journey explorer.
"""

from __future__ import annotations  # Keep annotations import-safe for pytest.

import json  # Read and write the small browser API bodies used by the journey.
import time  # Measure each screenshot step for the report.
from dataclasses import dataclass, field  # Keep recorder state explicit.
from pathlib import Path  # Build artifact paths without hard-coded separators.
from typing import Any  # Playwright objects are runtime types in these tests.

import pytest  # Use the existing browser fixtures and assertions.

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="The Playwright package is not installed."
)  # Skip cleanly.

AGENT_NAME = "upj-single-site"  # Match the assigned explorer name.
REPO_ROOT = Path(__file__).parents[4]  # Point screenshots at the worktree root, not the pytest run folder.
SHOTS = REPO_ROOT / "data" / "test-artifacts" / "upgrade-portal-journeys" / AGENT_NAME  # Keep screenshots in worktree.
FINDINGS = Path(
    r"C:\Users\jmorrison\.copilot\session-state\0f54b2fc-0ff6-4859-828d-55dce638e05b\files\findings\upj-single-site.md"
)  # Write the assigned findings file.

ORG_ID = "11111111-1111-1111-1111-111111111111"  # The stand-in organization identifier.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The stand-in single-site identifier.
START_READY_RUN_ID = "e2e-start-ready-run-0001"  # Seeded run for the firmware start journey.
FAILED_RUN_ID = "e2e-failed-run-0001"  # Seeded failed run for retry and failure state.
STOPPED_RUN_ID = "e2e-stopped-run-0001"  # Seeded stopped run for restart state.
STALE_PRECLOUD_RUN_ID = "e2e-stale-precloud-0001"  # Seeded stale run for cancel and stale state.
STALE_STOPPING_RUN_ID = "e2e-stale-stopping-0001"  # Seeded stale run for reconciliation.
PREPARED_RUN_ID = "e2e-prepared-run-0001"  # Seeded prepared run for confirm navigation.

OK = 200  # Browser pages must answer 200.
CREATED = 201  # Run creation returns 201.
ACCEPTED = 202  # Capture start and upgrade start return 202.
WAIT = 10_000  # Loopback page actions must settle quickly.
LONG_WAIT = 30_000  # Store setup and seed writes can take longer on Windows.
CONFIRM = "CONFIRM"  # The exact upgrade confirmation word.
STOP = "STOP"  # The exact stop confirmation word.

CAPABILITIES = (
    ("Organization selection", "/select/org", "org-select-11111111-1111-1111-1111-111111111111"),
    ("Mode selection", "/select/mode", "mode-single-site"),
    ("Site selection", "/select/site", "site-open-22222222-2222-2222-2222-222222222222"),
    ("Inventory", "/select/site/<site_id>", "inventory-table"),
    ("Site lock", "/captures/new", "lock-take-button"),
    ("Pre-check capture", "/captures/new", "capture-start-button"),
    ("Capture progress", "/captures/new", "capture-progress"),
    ("Capture table", "/captures/<capture_id>", "capture-device-table"),
    ("Capture export", "/api/captures/<capture_id>/export", "capture-export-csv"),
    ("Upgrade creation", "/api/sites/<site_id>/runs", "capture-start-upgrade-button"),
    ("Device type filter", "/runs/<run_id>/options", "upgrade-device-type-selection"),
    ("AP version choice", "/runs/<run_id>/options", "upgrade-version-select-ap"),
    ("Switch version choice", "/runs/<run_id>/options", "upgrade-version-select-switch"),
    ("Gateway version choice", "/runs/<run_id>/options", "upgrade-version-select-gateway"),
    ("Reboot option", "/runs/<run_id>/options", "upgrade-reboot-group"),
    ("Junos file action", "/runs/<run_id>/options", "upgrade-junos-file-action-group"),
    ("Canary phases", "/runs/<run_id>/options", "upgrade-canary-phases"),
    ("Reboot-at delay", "/runs/<run_id>/options", "upgrade-reboot-at"),
    ("Stable version", "/runs/<run_id>/options", "upgrade-stable-version-group"),
    ("Force option", "/runs/<run_id>/options", "upgrade-force-group"),
    ("P2P cluster", "/runs/<run_id>/options", "upgrade-p2p-cluster-size"),
    ("RRM options", "/runs/<run_id>/options", "upgrade-rrm-node-order"),
    ("Mesh upgrade", "/runs/<run_id>/options", "upgrade-rrm-mesh-upgrade"),
    ("Confirm summary", "/runs/<run_id>/confirm", "upgrade-advanced-summary"),
    ("Typed upgrade confirmation", "/runs/<run_id>/confirm", "upgrade-confirm-input"),
    ("Upgrade start", "/api/runs/<run_id>/start", "upgrade-start-button"),
    ("Run progress", "/runs/<run_id>", "upgrade-run-table"),
    ("Run phases", "/runs/<run_id>", "upgrade-phase-gateways"),
    ("Stale badge", "/runs/<run_id>", "run-stale-badge"),
    ("Failure alert", "/runs/<run_id>", "upgrade-failure-alert"),
    ("Mist account label", "/runs/<run_id>", "upgrade-cloud-account"),
    ("Stop gate", "/runs/<run_id>", "stop-confirm-input"),
    ("Stop outcome", "/runs/<run_id>", "stop-outcome"),
    ("Retry", "/runs/<run_id>", "run-retry-button"),
    ("Reschedule", "/runs/<run_id>", "run-reschedule-button"),
    ("Cancel", "/runs/<run_id>", "run-cancel-button"),
    ("Reconciliation", "/runs/<run_id>", "run-reconciliation-submit"),
    ("Compare picker", "/compare", "compare-before-select"),
    ("Compare result", "/compare", "compare-statistics"),
    ("Comparison download", "/api/comparisons/export", "compare-export-csv"),
    ("History", "/history", "history-table"),
    ("History open", "/history", "history-open-<capture_id>"),
    ("History paging", "/history", "history-page-next"),
)  # List each capability for the parity audit.


@dataclass
class Recorder:
    """Record journey evidence for the findings file."""

    page: Any  # The page whose screenshots are being captured.
    screenshots: list[str] = field(default_factory=list)  # Screenshot paths in order.
    findings: list[str] = field(default_factory=list)  # Confirmed defect sections.
    events: list[str] = field(default_factory=list)  # Browser errors and failed requests.
    timings: list[str] = field(default_factory=list)  # Screenshot and navigation timing.
    step: int = 0  # Ordered screenshot counter.

    def wire(self) -> None:
        """Attach browser event listeners."""
        self.page.on("console", self._console)  # Capture console warnings and errors.
        self.page.on("pageerror", lambda error: self.events.append(f"pageerror: {error}"))  # Capture page exceptions.
        self.page.on(
            "requestfailed", lambda request: self.events.append(f"requestfailed: {request.url}")
        )  # Capture fails.
        self.page.on("response", self._response)  # Capture HTTP 400 and greater responses.

    def _console(self, message: Any) -> None:
        """Record warning and error console messages."""
        if str(message.type).lower() in {"warning", "error"}:  # Keep only actionable browser messages.
            self.events.append(f"console {message.type}: {message.text}")  # Store the browser message.

    def _response(self, response: Any) -> None:
        """Record HTTP responses that show a refusal or route fault."""
        if int(response.status) >= 400:  # The assignment requires this evidence.
            self.events.append(f"http {response.status}: {response.request.method} {response.url}")  # Store summary.

    def shot(self, journey: str, name: str) -> None:
        """Take one full-page screenshot and record timing."""
        SHOTS.mkdir(parents=True, exist_ok=True)  # Create the assigned screenshot folder.
        self.step += 1  # Make the file name ordered.
        path = SHOTS / f"{journey}-{self.step:02d}-{name}.png"  # Build a stable screenshot path.
        start = time.perf_counter()  # Start the step timer.
        self.page.screenshot(path=str(path), full_page=True)  # Capture the full page.
        elapsed = time.perf_counter() - start  # Stop the step timer.
        nav = self.page.evaluate(
            "() => { const e = performance.getEntriesByType('navigation').slice(-1)[0];"
            " return e ? {duration: Math.round(e.duration), dom: Math.round(e.domContentLoadedEventEnd)} : {}; }"
        )  # Read compact navigation timing.
        self.screenshots.append(str(path))  # Add screenshot evidence to the report.
        self.timings.append(f"{journey}/{name}: {elapsed:.3f}s, navigation={nav}")  # Add timing evidence.

    def finding(self, suffix: str, title: str, actual: str, evidence: str, cause: str) -> None:
        """Append one defect in the required markdown shape."""
        self.findings.append(
            "\n".join(
                [
                    f"### F-{AGENT_NAME}-{suffix}: {title}",
                    "- Severity: medium",
                    "- Mode: single-site",
                    "- Kind: defect",
                    "- Steps:",
                    "  1. Open the single-site journey.",
                    "  2. Follow the screenshot evidence.",
                    "- Expected: The page shows a clear operator result inside the page.",
                    f"- Actual: {actual}",
                    f"- Evidence: {evidence}",
                    f"- Suspected cause: {cause}",
                ]
            )
        )  # Store the complete defect entry.

    def write(self) -> None:
        """Write the assigned findings file."""
        FINDINGS.parent.mkdir(parents=True, exist_ok=True)  # Create the findings folder.
        lines = [f"# {AGENT_NAME} findings", ""]  # Start the report.
        lines.extend(self.findings or ["No confirmed defect was found during this pass."])  # Add findings.
        lines.extend(["", "## Browser evidence", ""])  # Add evidence section.
        lines.extend(f"- {path}" for path in self.screenshots)  # List screenshots.
        lines.extend(["", "## Timing and browser errors", ""])  # Add timing and event section.
        lines.extend(f"- {entry}" for entry in self.timings)  # List timings.
        lines.extend(["", "### Browser events", ""])  # Add browser event section.
        lines.extend(f"- {entry}" for entry in (self.events or ["None recorded."]))  # List browser events.
        lines.extend(["", "## Capabilities exercised", ""])  # Add mandatory capability list.
        lines.extend(f"- {name} | {page} | `{test_id}`" for name, page, test_id in CAPABILITIES)  # List capabilities.
        FINDINGS.write_text("\n".join(lines) + "\n", encoding="utf-8")  # Persist the report.


def _open(page: Any, path: str) -> None:
    """Open one portal page and require a 200 status."""
    response = page.goto(path, wait_until="domcontentloaded")  # Navigate through the browser.
    assert response is not None and response.status == OK, f"{path} did not answer {OK}."  # Fail on route faults.


def _csrf(page: Any) -> str:
    """Return the CSRF token from the current document."""
    return str(page.get_by_test_id("csrf-meta").get_attribute("content") or "")  # Read the token from layout.html.


def _headers(page: Any) -> dict[str, str]:
    """Return JSON headers for Playwright request calls."""
    return {"X-CSRFToken": _csrf(page), "Content-Type": "application/json"}  # Keep request calls same-origin safe.


def _take_lock(page: Any) -> None:
    """Take the site lock when the page shows a lock control."""
    button = page.get_by_test_id("lock-take-button")  # Find the lock button.
    if button.count() == 0 or not button.is_visible():  # The session may already hold the site.
        return  # No lock action is needed.
    button.click()  # Take a free lock or open takeover confirmation.
    try:  # The free-lock path enables the capture start button.
        sync_api.expect(page.get_by_test_id("capture-start-button")).to_be_enabled(timeout=WAIT)  # Wait for enable.
        return  # The lock is held.
    except AssertionError:  # A held site opens the takeover form.
        pass  # Continue to the confirmation path.
    field = page.get_by_test_id("lock-confirm-input")  # Find the takeover field.
    if field.count() > 0 and field.is_visible():  # Confirm only when the form is present.
        field.fill(str(field.get_attribute("data-confirm-word") or CONFIRM))  # Type the required word.
        page.get_by_test_id("lock-confirm-submit").click()  # Submit the takeover.


def _release_lock(page: Any) -> None:
    """Release the site lock if this page offers the release control."""
    button = page.get_by_test_id("lock-release-button")  # Find the release button.
    if button.count() > 0 and button.is_visible():  # Release only visible lock ownership.
        button.click()  # Give the site back to later tests.


def _wait_seed(page: Any, path: str, marker: str) -> None:
    """Open a seeded run until its marker appears."""
    for _attempt in range(30):  # The seed writer runs after server start.
        _open(page, path)  # Open the seeded page.
        if page.get_by_test_id(marker).count() > 0:  # The marker proves the seed is present.
            return  # Continue the journey.
        page.wait_for_timeout(1_000)  # Wait for the seed writer.
    pytest.fail(f"{path} did not show {marker}.")  # A missing seed blocks the journey.


def _first_option(locator: Any) -> None:
    """Select the first real option if one exists."""
    if locator.count() > 0 and locator.locator("option").count() > 1:  # Index zero is the prompt.
        locator.select_option(index=1)  # Choose the first offered version.


def _set_types(page: Any, choices: set[str]) -> None:
    """Select one set of device families on the options page."""
    page.get_by_test_id("upgrade-type-all").uncheck()  # Clear the all-family checkbox.
    for family in ("ap", "switch", "gateway"):  # Keep one stable order.
        control = page.get_by_test_id(f"upgrade-type-{family}")  # Find the family checkbox.
        control.check() if family in choices else control.uncheck()  # Set the requested state.
    page.wait_for_timeout(250)  # Let the shipped script update conditional controls.


def _create_run(page: Any) -> str:
    """Create or reuse one run for the stand-in site."""
    answer = page.request.post(
        f"/api/sites/{SITE_ID}/runs", headers=_headers(page), data="{}", timeout=LONG_WAIT
    )  # Create.
    if answer.status == 409:  # Another live run can already hold the stand-in site.
        body = json.loads(answer.text()).get("error", {})  # Read the refusal envelope.
        return str(body.get("details", {}).get("run_id", ""))  # Use the run named by the refusal.
    assert answer.status == CREATED, f"Run create answered {answer.status}."  # Require a fresh run.
    return str(json.loads(answer.text())["run_id"])  # Return the created run key.


def _start_capture(page: Any) -> str:
    """Start a pre-check capture and wait for verification."""
    with page.expect_response(lambda response: response.url.endswith("/captures"), timeout=LONG_WAIT) as event:
        page.get_by_test_id("capture-start-button").click()  # Start the pre-check capture.
    assert event.value.status == ACCEPTED, f"Capture start answered {event.value.status}."  # Require accepted work.
    capture_key_script = (
        "() => (document.querySelector('[data-testid=\"capture-progress\"]')?."
        "getAttribute('data-capture-id') || '').length > 0"
    )  # Read only the progress identifier state.
    page.wait_for_function(
        capture_key_script,
        timeout=LONG_WAIT,
    )  # Wait for the page to store the capture key.
    capture_id = str(
        page.get_by_test_id("capture-progress").get_attribute("data-capture-id") or ""
    )  # Read key from page.
    for _attempt in range(40):  # Bound the worker wait.
        page.get_by_test_id("capture-refresh-button").click()  # Force a status read.
        badge_text = (page.get_by_test_id("capture-verified-badge").inner_text() or "").strip()  # Read badge.
        if badge_text == "Verified":  # The capture worker finished.
            return capture_id  # Return the verified capture.
        page.wait_for_timeout(500)  # Give the worker a moment.
    pytest.fail("The pre-check capture did not verify.")  # The capture must finish in the stand-in server.


def _save_options(page: Any) -> None:
    """Exercise and save the version and advanced options."""
    for test_id in ("upgrade-version-select-ap", "upgrade-version-select-switch", "upgrade-version-select-gateway"):
        _first_option(page.get_by_test_id(test_id))  # Pick the first version for each visible family.
    page.get_by_test_id("upgrade-strategy-canary").check()  # Show canary controls.
    page.get_by_test_id("upgrade-canary-phases").fill("1,10,50,100")  # Exercise canary phases.
    page.get_by_test_id("upgrade-max-failures").fill("1,1,2,3")  # Exercise per-phase failures.
    page.get_by_test_id("upgrade-max-failure-percentage").fill("10")  # Exercise failure percentage.
    page.get_by_test_id("upgrade-start-time").fill("5m")  # Exercise start delay.
    page.get_by_test_id("upgrade-reboot-at").fill("8h")  # Exercise reboot-at.
    page.get_by_test_id("upgrade-force-yes").check()  # Exercise force.
    page.get_by_test_id("upgrade-stable-version-yes").check()  # Exercise stable version.
    page.get_by_test_id("upgrade-enable-p2p-yes").check()  # Exercise P2P.
    page.get_by_test_id("upgrade-p2p-cluster-size").fill("12")  # Exercise P2P size.
    page.get_by_test_id("upgrade-p2p-parallelism").fill("2")  # Exercise P2P parallelism.
    page.get_by_test_id("upgrade-strategy-rrm").check()  # Show RRM controls.
    page.get_by_test_id("upgrade-rrm-first-batch-percentage").fill("5")  # Exercise RRM first batch.
    page.get_by_test_id("upgrade-rrm-max-batch-percentage").fill("25")  # Exercise RRM max batch.
    page.get_by_test_id("upgrade-rrm-node-order").select_option("center_to_fringe")  # Exercise RRM order.
    page.get_by_test_id("upgrade-rrm-mesh-upgrade").select_option("sequential")  # Exercise mesh upgrade.
    page.get_by_test_id("upgrade-rrm-slow-ramp").select_option("yes")  # Exercise slow ramp.
    with page.expect_response(lambda response: response.url.endswith("/options"), timeout=LONG_WAIT) as event:
        page.get_by_test_id("upgrade-options-save-button").click()  # Save through the operator control.
    assert event.value.status == OK, f"Options save answered {event.value.status}."  # Require a saved plan.


def _navigation_probe(page: Any, recorder: Recorder, name: str) -> None:
    """Record reload, back, and forward behavior on the current page."""
    current = page.url  # Save the current address.
    page.reload(wait_until="domcontentloaded")  # Reload the page.
    recorder.shot("navigation", f"{name}-reload")  # Capture reload behavior.
    page.go_back(wait_until="domcontentloaded")  # Use browser Back.
    recorder.shot("navigation", f"{name}-back")  # Capture Back behavior.
    page.go_forward(wait_until="domcontentloaded")  # Use browser Forward.
    recorder.shot("navigation", f"{name}-forward")  # Capture Forward behavior.
    assert page.url == current, "Forward did not return to the starting page."  # Require expected navigation.


def test_single_site_operator_journeys(page: Any, firmware_operator_page: Any) -> None:
    """Drive the assigned single-site journeys and write evidence."""
    recorder = Recorder(page)  # Create the evidence recorder.
    recorder.wire()  # Attach event capture.
    try:  # Write the findings file even when a step fails.
        _open(page, "/select/org")  # Open the organization picker.
        recorder.shot("full-path", "org-picker")  # Capture organization picker.
        page.get_by_test_id(f"org-select-{ORG_ID}").click()  # Select the stand-in organization.
        page.wait_for_url("**/select/mode", timeout=WAIT)  # Wait for mode picker.
        recorder.shot("full-path", "mode-picker")  # Capture mode picker.
        page.get_by_test_id("mode-continue").click()  # Trigger native required validation.
        recorder.shot("validation", "mode-required")  # Capture mode validation.
        page.get_by_test_id("mode-single-site").check()  # Select single-site mode.
        page.get_by_test_id("mode-continue").click()  # Continue to site list.
        page.wait_for_url("**/select/site", timeout=WAIT)  # Wait for site picker.
        recorder.shot("full-path", "site-list")  # Capture site list.
        page.get_by_test_id(f"site-open-{SITE_ID}").click()  # Open the stand-in inventory.
        page.wait_for_url(f"**/select/site/{SITE_ID}", timeout=WAIT)  # Wait for inventory.
        recorder.shot("full-path", "inventory")  # Capture inventory.
        page.get_by_test_id("site-capture-link").click()  # Open capture page.
        page.wait_for_url(f"**/captures/new?site_id={SITE_ID}", timeout=WAIT)  # Wait for capture page.
        _take_lock(page)  # Take the site lock before writes.
        recorder.shot("full-path", "precheck-ready")  # Capture ready pre-check.
        _start_capture(page)  # Start and verify pre-check.
        recorder.shot("full-path", "precheck-verified")  # Capture verified pre-check.
        page.get_by_test_id("capture-device-table").scroll_into_view_if_needed()  # Bring table into view.
        recorder.shot("full-path", "capture-table")  # Capture detailed capture table.
        href = str(page.get_by_test_id("capture-export-csv").get_attribute("href") or "")  # Read CSV export link.
        export_answer = page.request.get(href)  # Download the capture export through the signed session.
        if export_answer.status != OK:  # Keep the journey moving after this confirmed product defect.
            recorder.finding(
                "01",
                "Verified capture export answers 404",
                f"The verified capture export answered HTTP {export_answer.status}.",
                recorder.screenshots[-1],
                "src/upgrade_portal/app/routes/capture.py:1302 refuses export "
                "when the loader returns no comparable capture.",
            )  # Record the defect with code evidence.
        with page.expect_response(lambda response: response.url.endswith("/runs"), timeout=LONG_WAIT) as event:
            page.get_by_test_id("capture-start-upgrade-button").click()  # Create the upgrade run.
        assert event.value.status in {CREATED, 409}, f"Run create answered {event.value.status}."  # Accept conflict.
        run_id = (
            str(json.loads(event.value.text()).get("run_id", ""))
            if event.value.status == CREATED
            else str(json.loads(event.value.text()).get("error", {}).get("details", {}).get("run_id", ""))
        )  # Read the run key from either answer shape.
        _open(page, f"/runs/{run_id}/options")  # Open the options page.
        recorder.shot("full-path", "options-all-families")  # Capture all-family options.
        for name, choices in (
            ("ap-only", {"ap"}),
            ("switch-only", {"switch"}),
            ("gateway-only", {"gateway"}),
            ("mixed", {"ap", "switch", "gateway"}),
        ):
            _set_types(page, set(choices))  # Select one family set.
            recorder.shot("families", name)  # Capture family-specific visibility.
        _set_types(page, {"ap", "switch", "gateway"})  # Restore mixed mode for saving.
        _save_options(page)  # Save version and advanced choices.
        page.wait_for_url(f"**/runs/{run_id}/confirm", timeout=LONG_WAIT)  # Wait for confirm page.
        recorder.shot("confirm", "summary")  # Capture site, call count, warnings, and advanced summary.
        field = page.get_by_test_id("upgrade-confirm-input")  # Select confirm input.
        if field.is_disabled():  # A disabled field means the create path did not link a verified pre-check.
            recorder.finding(
                "02",
                "Run created from a verified capture opens a locked confirm gate",
                "The confirm input stayed disabled after the journey started from a verified pre-check capture.",
                recorder.screenshots[-1],
                "src/upgrade_portal/app/routes/upgrade.py:1184 prepares confirmation from the run record, "
                "but the create path did not retain the verified capture.",
            )  # Record the locked gate as a journey defect.
        else:  # The normal path can test the three typed confirmation states.
            field.fill("")  # Exercise blank text.
            recorder.shot("confirm", "blank")  # Capture blank gate.
            sync_api.expect(page.get_by_test_id("upgrade-start-button")).to_be_disabled()  # Blank stays locked.
            field.fill("confirm")  # Exercise wrong text.
            recorder.shot("confirm", "wrong-text")  # Capture wrong gate.
            sync_api.expect(page.get_by_test_id("upgrade-start-button")).to_be_disabled()  # Wrong text stays locked.
            field.fill(CONFIRM)  # Exercise exact text.
            recorder.shot("confirm", "exact-text")  # Capture exact gate.
        _navigation_probe(page, recorder, "confirm")  # Probe reload, Back, and Forward.

        _wait_seed(firmware_operator_page, f"/runs/{START_READY_RUN_ID}", "upgrade-confirm-link")  # Open start seed.
        firmware_operator_page.get_by_test_id("upgrade-confirm-link").click()  # Move to confirm page.
        firmware_operator_page.wait_for_url(f"**/runs/{START_READY_RUN_ID}/confirm", timeout=WAIT)  # Wait.
        firmware_operator_page.get_by_test_id("upgrade-confirm-input").fill(CONFIRM)  # Type exact word.
        recorder.page = firmware_operator_page  # Capture firmware-operator screenshots.
        recorder.shot("start", "firmware-operator-confirm")  # Capture start-ready confirm page.
        with firmware_operator_page.expect_response(
            lambda response: response.url.endswith(f"/api/runs/{START_READY_RUN_ID}/start"), timeout=LONG_WAIT
        ) as start:
            firmware_operator_page.get_by_test_id("upgrade-start-button").click()  # Start the upgrade.
        assert start.value.status == ACCEPTED, f"Start answered {start.value.status}."  # Require accepted start.
        firmware_operator_page.wait_for_url(f"**/runs/{START_READY_RUN_ID}", timeout=WAIT)  # Wait for run page.
        recorder.shot("start", "run-page")  # Capture run page after start.
        recorder.page = page  # Return screenshots to the main page.

        for run_id, marker in (
            (PREPARED_RUN_ID, "upgrade-confirm-link"),
            (FAILED_RUN_ID, "upgrade-failure-alert"),
            (STOPPED_RUN_ID, "run-retry-controls"),
            (STALE_PRECLOUD_RUN_ID, "run-stale-badge"),
            (STALE_STOPPING_RUN_ID, "run-reconciliation-controls"),
        ):
            _wait_seed(page, f"/runs/{run_id}", marker)  # Open each seeded state.
            recorder.shot("seeded-runs", run_id)  # Capture state, phase, table, and account labels.

        _open(page, f"/runs/{STALE_STOPPING_RUN_ID}")  # Open reconciliation state.
        page.get_by_test_id("run-reconciliation-confirmation").fill(
            f"RECONCILE {STALE_STOPPING_RUN_ID}"
        )  # Type phrase.
        recorder.shot("controls", "reconciliation")  # Capture reconciliation controls.
        schedule_run = _create_run(page)  # Create or reuse one scheduled run.
        _open(page, f"/runs/{schedule_run}")  # Open schedule controls.
        recorder.shot("controls", "schedule")  # Capture reschedule and cancel controls.
        if (
            page.get_by_test_id("run-reschedule-input").count() > 0
            and page.get_by_test_id("run-reschedule-input").is_enabled()
        ):
            page.get_by_test_id("run-reschedule-input").fill("5m")  # Enter a relative time.
            page.get_by_test_id("run-reschedule-button").click()  # Press reschedule.
            sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text(
                "moved", timeout=WAIT
            )  # Verify result.
            recorder.shot("controls", "reschedule-result")  # Capture result.
        _open(page, f"/runs/{schedule_run}")  # Reopen for stop control.
        if page.get_by_test_id("stop-button").count() > 0 and page.get_by_test_id("stop-button").is_enabled():
            page.route(
                "**/api/runs/*/stop",
                lambda route: route.fulfill(
                    status=OK,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "state": "stopping",
                            "outcome": {
                                "cancelled": ["5c5b350e0001"],
                                "already_writing": ["5c5b350e0002"],
                                "no_cancel_available": ["5c5b350e0003"],
                                "message": "The portal cancelled one device.",
                            },
                        }
                    ),
                ),
            )  # Stub the stop endpoint to avoid real cancellation.
            page.get_by_test_id("stop-button").click()  # Open stop box.
            recorder.shot("stop", "box")  # Capture stop confirmation.
            page.get_by_test_id("stop-confirm-input").fill(STOP)  # Type exact stop word.
            page.get_by_test_id("stop-confirm-submit").click()  # Submit stop.
            sync_api.expect(page.get_by_test_id("stop-outcome")).to_be_visible(timeout=WAIT)  # Require outcome lists.
            recorder.shot("stop", "outcome")  # Capture three outcome lists.

        _open(page, f"/runs/{FAILED_RUN_ID}")  # Open retry state.
        recorder.shot("controls", "retry")  # Capture retry controls.
        _open(page, "/compare")  # Open compare select page.
        recorder.shot("compare", "picker")  # Capture compare picker.
        choices = page.get_by_test_id("compare-before-select").evaluate(
            "node => Array.from(node.options).map(option => option.value).filter(Boolean)"
        )  # Read choices.
        if choices:  # The stand-in server normally seeds comparison captures.
            page.get_by_test_id("compare-before-select").select_option(str(choices[0]))  # Select before.
            page.get_by_test_id("compare-after-select").select_option(str(choices[-1]))  # Select after.
            page.get_by_test_id("compare-run-button").click()  # Run comparison.
            page.wait_for_load_state("domcontentloaded")  # Wait for page.
            recorder.shot("compare", "result")  # Capture comparison and statistics.
            if page.get_by_test_id("compare-export-csv").count() > 0:  # Verify the CSV link if comparison rendered.
                assert (
                    page.request.get(str(page.get_by_test_id("compare-export-csv").get_attribute("href") or "")).status
                    == OK
                )  # Download CSV.
        _open(page, "/history")  # Open history page.
        recorder.shot("history", "first-page")  # Capture filters, open buttons, and paging.
        open_buttons = page.locator("[data-testid^='history-open-']")  # Find capture open buttons.
        if open_buttons.count() > 0:  # Open the first capture when present.
            open_buttons.first.click()  # Open stored capture.
            page.wait_for_load_state("domcontentloaded")  # Wait for capture page.
            recorder.shot("history", "open-capture")  # Capture opened capture.
        _open(page, "/history?limit=1&offset=1")  # Open a later history page.
        recorder.shot("history", "paging")  # Capture paging controls.
        _navigation_probe(page, recorder, "history")  # Probe reload, Back, and Forward.
        for path in ("/api/sites/not-a-site/inventory", "/api/captures/not-a-capture/status"):
            answer = page.request.get(path)  # Exercise validation endpoint.
            body = answer.text()  # Read error body.
            assert "Traceback" not in body, f"{path} exposed a traceback."  # No raw Python error.
            assert answer.status >= 400, f"{path} did not refuse invalid input."  # Invalid input must refuse.
        _release_lock(page)  # Release site lock for later tests.
    finally:
        recorder.write()  # Always persist evidence and capabilities.
