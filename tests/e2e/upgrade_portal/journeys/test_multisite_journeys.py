"""Journey coverage for the multi-site upgrade portal."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

MODE_PATH = "/select/mode"  # Start each operator journey at the required mode page.
SITE_PATH = "/select/site"  # Revisit the selected site page for navigation checks.
OPTIONS_PATH = "/upgrade/org/options"  # Keep the organization option path in one value.
CONFIRM_PATH = "/upgrade/org/confirm"  # Keep the organization confirm path in one value.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # First stand-in site identifier.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # Second stand-in site identifier.
VERSION = "0.15.1"  # Use the offered stand-in version that is newer than the running version.
SHOTS = (
    Path(__file__).resolve().parents[4] / "data/test-artifacts/upgrade-portal-journeys/upj-multisite"
)  # Store only this agent evidence.


@dataclass
class BrowserEvidence:
    """Collect browser-side defects that appear during one journey."""

    console_errors: list[str] = field(default_factory=list)  # Store console errors with page timing.
    page_errors: list[str] = field(default_factory=list)  # Store uncaught page exceptions.
    failed_requests: list[str] = field(default_factory=list)  # Store request failures.
    bad_responses: list[str] = field(default_factory=list)  # Store response status codes above 399.
    steps: list[str] = field(default_factory=list)  # Store each measured journey step.


def _watch(page: Any) -> BrowserEvidence:
    """Attach the mandatory browser evidence listeners."""
    evidence = BrowserEvidence()  # Keep one evidence object per test for isolation.
    page.on("console", lambda message: _record_console(evidence, message))  # Capture console errors from the page.
    page.on("pageerror", lambda error: evidence.page_errors.append(str(error)))  # Capture browser exceptions.
    page.on("requestfailed", lambda request: evidence.failed_requests.append(request.url))  # Capture network failures.
    page.on("response", lambda response: _record_response(evidence, response))  # Capture server refusals.
    return evidence  # Return the listener sink to the caller.


def _record_console(evidence: BrowserEvidence, message: Any) -> None:
    """Record only console entries that signal a product fault."""
    if message.type == "error":  # Keep noise out, but keep faults visible.
        evidence.console_errors.append(message.text)  # Store the browser wording for the finding.


def _record_response(evidence: BrowserEvidence, response: Any) -> None:
    """Record failed HTTP responses without failing expected validation checks."""
    if response.status >= 500:  # Client-side validation may use 400, but 500 is always a fault here.
        evidence.bad_responses.append(f"{response.status} {response.url}")  # Store the status and the address.


def _step(
    page: Any, evidence: BrowserEvidence, journey: str, number: int, name: str, action: Callable[[], None]
) -> None:
    """Run one journey action and save the screenshot that proves it."""
    start = time.perf_counter()  # Start the local duration before the operator action.
    action()  # Drive the page in the same way an operator does.
    elapsed = time.perf_counter() - start  # Measure the local action duration.
    try:  # A submit can replace the document while Playwright reads the navigation entry.
        nav = page.evaluate(
            "performance.getEntriesByType('navigation').map((entry) => entry.type).join(',')"
        )  # Read navigation type.
    except Exception as error:  # Preserve the step evidence instead of hiding a product navigation.
        nav = f"navigation-read-failed:{type(error).__name__}"  # Keep one compact fault string.
    evidence.steps.append(f"{journey}:{number}:{name}:{elapsed:.3f}s:{nav}")  # Preserve timing for debugging.
    _shot(page, journey, number, name)  # Save the mandatory visual evidence.


def _shot(page: Any, journey: str, number: int, name: str) -> Path:
    """Save one full-page screenshot for visual review."""
    SHOTS.mkdir(parents=True, exist_ok=True)  # Create the evidence folder once per run.
    path = SHOTS / f"{journey}-{number:02d}-{name}.png"  # Build a stable evidence file name.
    page.screenshot(path=str(path), full_page=True)  # Capture the whole page, including off-screen rows.
    return path  # Return the path for optional finding text.


def _open_multisite_sites(page: Any, evidence: BrowserEvidence, journey: str) -> None:
    """Open the multi-site site picker from the mode page."""
    _step(page, evidence, journey, 1, "mode", lambda: page.goto(MODE_PATH, wait_until="domcontentloaded"))  # Open mode.
    _step(
        page, evidence, journey, 2, "choose-multi", lambda: page.get_by_test_id("mode-multi-site").check()
    )  # Select mode.
    _step(
        page, evidence, journey, 3, "site-picker", lambda: _click_and_wait(page, "mode-continue", SITE_PATH)
    )  # Continue.


def _select_sites(page: Any, evidence: BrowserEvidence, journey: str, sites: tuple[str, ...]) -> None:
    """Select the requested sites and continue to the options page."""
    for site_id in sites:  # Keep the site selection order visible in the browser.
        _step(
            page,
            evidence,
            journey,
            4 + sites.index(site_id),
            f"select-{site_id[:4]}",
            lambda site_id=site_id: page.get_by_test_id(f"site-select-{site_id}").check(),
        )  # Select one site.
    _step(
        page, evidence, journey, 7, "options", lambda: _click_and_wait(page, "multi-site-continue", OPTIONS_PATH)
    )  # Continue.


def _click_and_wait(page: Any, test_id: str, suffix: str) -> None:
    """Click one button and wait for the next route."""
    page.get_by_test_id(test_id).click()  # Click the page control by its stable contract.
    page.wait_for_url(re.compile(rf".*{re.escape(suffix)}$"))  # Wait until the route changes.


def _release_locks(page: Any) -> None:
    """Release site locks that a destructive journey can hold."""
    page.evaluate(  # Use the same origin and signed session as the browser.
        """async ([siteA, siteB]) => {
            for (const site of [siteA, siteB]) {
                await fetch(`/api/sites/${site}/lock`, {method: "DELETE"}).catch(() => undefined);
            }
        }""",
        [SITE_ID, SECOND_SITE_ID],
    )


def _set_families(page: Any, families: tuple[str, ...]) -> None:
    """Leave only the requested device families checked."""
    for family in ("ap", "switch", "gateway"):  # The page supports these three families.
        control = page.get_by_test_id(f"org-upgrade-type-{family}")  # Read the stable checkbox locator.
        if family in families:  # The requested family must stay active.
            control.check()  # Select the family for this combination.
        else:  # A family outside the combination must not affect the plan.
            control.uncheck()  # Clear the family for this combination.


def _fill_versions(page: Any, families: tuple[str, ...], version: str = VERSION) -> None:
    """Fill version fields for the selected families only."""
    values = {
        "ap": "org-upgrade-version",
        "switch": "org-upgrade-switch-version",
        "gateway": "org-upgrade-gateway-version",
    }  # Map family to field.
    for family, test_id in values.items():  # Visit each visible family field.
        page.get_by_test_id(test_id).fill(version if family in families else "")  # Use a blank for unused families.


def _save_options(page: Any, families: tuple[str, ...], strategy: str = "canary") -> None:
    """Save valid organization options for the selected family set."""
    _set_families(page, families)  # Match the option state to the test parameter.
    _fill_versions(page, families)  # Use the offered version for each selected family.
    page.get_by_test_id(f"org-strategy-{strategy}").check()  # Select the strategy under test.
    page.get_by_test_id("org-upgrade-canary-phases").fill("10,100")  # Use valid phases when they matter.
    page.get_by_test_id("org-upgrade-max-failures").fill("5")  # Use a safe failure threshold.
    page.get_by_test_id("org-upgrade-review").click()  # Ask the portal to validate the options.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # Wait for the review page.


def _start_upgrade(page: Any) -> str:
    """Start a confirmed upgrade and return the job URL."""
    page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # Unlock the destructive start button.
    sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_enabled()  # Prove the gate opened.
    page.get_by_test_id("org-upgrade-start").click()  # Submit the aggregate job once.
    page.wait_for_url(re.compile(r".*/upgrade/org/jobs/[^/]+$"))  # Wait for the progress page.
    return page.url  # Return the durable job page for revisit checks.


def _route_status(page: Any, payload: dict[str, Any]) -> None:
    """Replace the status poll with a deterministic browser response."""
    page.route(  # Keep every simulated state inside this browser context.
        re.compile(r".*/api/org-upgrades/[^/]+$"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(payload)),
    )


def _final_payload(status: str) -> dict[str, Any]:
    """Build a final multi-child status payload."""
    return {
        "upgrade_id": "org-run-journey",
        "status": status,
        "current_phase": 2,
        "total": 6,
        "upgraded_count": 4,
        "failed_count": 1,
        "site_upgrades": [
            {
                "site_id": SITE_ID,
                "site_name": "E2E Stand-In Site",
                "device_family": "ap",
                "status": "completed",
                "total": 2,
                "upgraded": 2,
                "failed": 0,
                "id": "child-ap",
            },
            {
                "site_id": SECOND_SITE_ID,
                "site_name": "E2E Second Stand-In Site",
                "device_family": "switch",
                "status": "failed",
                "total": 2,
                "upgraded": 1,
                "failed": 1,
                "id": "child-switch",
                "error": "Switch write failed.",
            },
            {
                "site_id": SECOND_SITE_ID,
                "site_name": "E2E Second Stand-In Site",
                "device_family": "gateway",
                "status": "unknown_child",
                "total": 2,
                "upgraded": 1,
                "failed": 0,
                "id": "child-gateway",
            },
        ],
    }


@pytest.mark.parametrize(
    ("families", "visible_fields"),
    [
        pytest.param(
            ("ap",),
            ("org-upgrade-version",),
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-001: unselected family fields remain visible."
            ),
        ),
        pytest.param(
            ("switch",),
            ("org-upgrade-switch-version",),
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-001: unselected family fields remain visible."
            ),
        ),
        pytest.param(
            ("gateway",),
            ("org-upgrade-gateway-version",),
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-001: unselected family fields remain visible."
            ),
        ),
        pytest.param(
            ("ap", "switch"),
            ("org-upgrade-version", "org-upgrade-switch-version"),
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-001: unselected family fields remain visible."
            ),
        ),
        pytest.param(
            ("ap", "gateway"),
            ("org-upgrade-version", "org-upgrade-gateway-version"),
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-001: unselected family fields remain visible."
            ),
        ),
        pytest.param(
            ("switch", "gateway"),
            ("org-upgrade-switch-version", "org-upgrade-gateway-version"),
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-001: unselected family fields remain visible."
            ),
        ),
        (
            ("ap", "switch", "gateway"),
            ("org-upgrade-version", "org-upgrade-switch-version", "org-upgrade-gateway-version"),
        ),
    ],
)
def test_family_combinations_show_only_selected_fields(
    firmware_operator_page: Any, families: tuple[str, ...], visible_fields: tuple[str, ...]
) -> None:
    """Each family combination must show only its needed version fields."""
    page = firmware_operator_page  # Use the reachable operator because the path can reach the start gate.
    evidence = _watch(page)  # Collect console, request, and timing evidence.
    journey = "families-" + "-".join(families)  # Make each screenshot unique and readable.
    try:  # Release locks even when the product fails the expected behavior.
        _open_multisite_sites(page, evidence, journey)  # Open site selection from the mode picker.
        _select_sites(page, evidence, journey, (SITE_ID, SECOND_SITE_ID))  # Use both stand-in sites.
        _set_families(page, families)  # Apply the family combination.
        _shot(page, journey, 8, "family-fields")  # Save the exact field set for review.
        all_fields = {
            "org-upgrade-version",
            "org-upgrade-switch-version",
            "org-upgrade-gateway-version",
        }  # Name every field.
        for test_id in visible_fields:  # Each selected family needs its field.
            sync_api.expect(page.get_by_test_id(test_id)).to_be_visible()  # Assert that required fields appear.
        for test_id in all_fields - set(visible_fields):  # Unselected family fields confuse the operator.
            sync_api.expect(page.get_by_test_id(test_id)).to_be_hidden()  # Assert that extra fields stay hidden.
    finally:  # Always release held site locks for the next test.
        _release_locks(page)  # Clean the server-side lock store.


def test_all_family_final_states_render_clearly(firmware_operator_page: Any) -> None:
    """All selected families reach the progress page and render final child states."""
    page = firmware_operator_page  # Use the operator that can submit firmware work.
    evidence = _watch(page)  # Capture required browser evidence.
    journey = "all-family-final-states"  # Use one stable journey name for screenshots.
    try:  # Release locks after the started job.
        _open_multisite_sites(page, evidence, journey)  # Open the site picker.
        _select_sites(page, evidence, journey, (SITE_ID, SECOND_SITE_ID))  # Select both sites for the submit seam.
        _step(
            page, evidence, journey, 8, "save-options", lambda: _save_options(page, ("ap", "switch", "gateway"))
        )  # Save.
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_contain_text(
            "E2E Stand-In Organization"
        )  # Confirm org.
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_contain_text(
            "Access points"
        )  # Confirm AP family.
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_contain_text(
            "Switches"
        )  # Confirm switch family.
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_contain_text(
            "Gateways"
        )  # Confirm gateway family.
        _shot(page, journey, 9, "confirm")  # Save the confirmation page.
        _step(page, evidence, journey, 10, "start", lambda: _start_upgrade(page))  # Start the job.
        sync_api.expect(page.get_by_test_id("org-upgrade-progress")).to_be_visible()  # Prove the progress page loaded.
        for state in ("completed", "failed", "partial", "unknown"):  # Simulate every final summary state.
            payload = _final_payload(state)  # Build the status payload for this state.
            _route_status(page, payload)  # Serve the next status read from the browser.
            _step(
                page,
                evidence,
                journey,
                11,
                f"status-{state}",
                lambda: page.get_by_test_id("org-upgrade-refresh").click(),
            )  # Refresh.
            sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text(
                "completed"
            )  # Check AP row.
            sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text(
                "failed"
            )  # Check switch row.
            sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text(
                "unknown_child"
            )  # Check gateway row.
            page.unroute(re.compile(r".*/api/org-upgrades/[^/]+$"))  # Reset the route for the next state.
        assert not evidence.console_errors  # Console errors indicate a broken browser path.
    finally:  # Release locks for later tests.
        _release_locks(page)  # Clean the test server lock state.


@pytest.mark.xfail(
    strict=True, reason="F-upj-multisite-002: confirmation omits route, schedule, and safety option details."
)
def test_confirmation_names_all_operator_decisions(firmware_operator_page: Any) -> None:
    """The confirmation page must show every decision before the typed word."""
    page = firmware_operator_page  # Use the reachable operator for the submit path.
    evidence = _watch(page)  # Capture required browser evidence.
    journey = "confirmation-details"  # Name evidence for this defect.
    try:  # Keep cleanup independent of assertion results.
        _open_multisite_sites(page, evidence, journey)  # Open site selection.
        _select_sites(page, evidence, journey, (SITE_ID, SECOND_SITE_ID))  # Select both sites.
        page.get_by_test_id("org-upgrade-start-time").fill("2099-01-01T01:00")  # Set a scheduled future start.
        page.get_by_test_id("org-upgrade-reboot-at").fill("8h")  # Set the reboot delay.
        page.locator("#org-junos-no").check()  # Select no Junos file action.
        page.locator("#org-upgrade-force").check()  # Select force to prove the risk appears.
        _step(
            page,
            evidence,
            journey,
            8,
            "save-options",
            lambda: _save_options(page, ("ap", "switch", "gateway"), "canary"),
        )  # Save.
        _shot(page, journey, 9, "confirm-missing-details")  # Save the defective confirmation page.
        page_text = page.get_by_test_id("org-upgrade-confirm").inner_text()  # Read the visible confirmation body.
        assert "E2E Stand-In Site" in page_text  # The operator must read the site names.
        assert "route" in page_text.lower()  # The operator must read each route before the write.
        assert "2099-01-01" in page_text  # The operator must read the scheduled start.
        assert "Maximum failure percentage" in page_text  # The operator must read the failure threshold.
        assert "Junos" in page_text and "No" in page_text  # The operator must read the file action choice.
        assert "force" in page_text.lower()  # The operator must read the forced write choice.
    finally:  # Release locks for later tests.
        _release_locks(page)  # Clean the test lock state.


@pytest.mark.parametrize(
    "strategy",
    [
        "canary",
        pytest.param(
            "big_bang",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-003: strategy controls do not adapt per strategy."
            ),
        ),
        pytest.param(
            "rrm",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-003: strategy controls do not adapt per strategy."
            ),
        ),
        pytest.param(
            "serial",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-003: strategy controls do not adapt per strategy."
            ),
        ),
    ],
)
def test_strategy_specific_fields_adapt_to_strategy(firmware_operator_page: Any, strategy: str) -> None:
    """Each strategy must expose only the fields that the strategy uses."""
    page = firmware_operator_page  # Use the standard write-capable operator.
    evidence = _watch(page)  # Capture required browser evidence.
    journey = f"strategy-{strategy}"  # Name evidence by strategy.
    try:  # Release locks even when an expected strategy defect appears.
        _open_multisite_sites(page, evidence, journey)  # Open site selection.
        _select_sites(page, evidence, journey, (SITE_ID, SECOND_SITE_ID))  # Select both sites.
        page.get_by_test_id(f"org-strategy-{strategy}").check()  # Select the strategy under test.
        _shot(page, journey, 8, "strategy-fields")  # Save the field layout.
        canary_field = page.get_by_test_id("org-upgrade-canary-phases")  # Locate canary phases.
        max_failure_field = page.get_by_test_id("org-upgrade-max-failures")  # Locate max failure percentage.
        if strategy == "canary":  # Canary needs phases and failure threshold.
            sync_api.expect(canary_field).to_be_visible()  # The phase field must appear.
            sync_api.expect(max_failure_field).to_be_visible()  # The failure field must appear.
        elif strategy == "big_bang":  # Big bang does not use phases or a staged failure threshold.
            sync_api.expect(canary_field).to_be_hidden()  # The phase field must not confuse the operator.
            sync_api.expect(max_failure_field).to_be_hidden()  # The failure field must not imply staging.
        else:  # RRM and serial need different staged controls.
            sync_api.expect(canary_field).to_be_hidden()  # Canary phases must not appear for this strategy.
            sync_api.expect(max_failure_field).to_be_visible()  # The failure threshold remains relevant.
    finally:  # Always release any lock records made while loading options.
        _release_locks(page)  # Clean the test lock state.


@pytest.mark.xfail(strict=True, reason="F-upj-multisite-004: empty multi-site selection opens raw JSON.")
def test_site_selection_navigation_and_mode_change(page: Any) -> None:
    """Site selection must refuse an empty set and clear targets on mode change."""
    evidence = _watch(page)  # Capture browser evidence.
    journey = "site-selection-navigation"  # Name evidence for this path.
    _open_multisite_sites(page, evidence, journey)  # Open site selection.
    _step(
        page, evidence, journey, 4, "no-site-refusal", lambda: page.get_by_test_id("multi-site-continue").click()
    )  # Submit empty.
    sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text(
        "Choose one or more sites"
    )  # Check inline error.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select one site.
    page.get_by_test_id(f"site-select-{SITE_ID}").uncheck()  # Clear the selection again.
    _shot(page, journey, 5, "select-then-clear")  # Prove the clear state.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select one site for navigation.
    _click_and_wait(page, "multi-site-continue", OPTIONS_PATH)  # Continue to options.
    _shot(page, journey, 6, "options-one-site")  # Save the one-site options page.
    page.reload(wait_until="domcontentloaded")  # Reload the options page to prove state stays readable.
    _shot(page, journey, 7, "options-reload")  # Save the reloaded page.
    page.go_back(wait_until="domcontentloaded")  # Move back to the site picker.
    _shot(page, journey, 8, "browser-back")  # Save browser back behavior.
    page.go_forward(wait_until="domcontentloaded")  # Move forward to options again.
    _shot(page, journey, 9, "browser-forward")  # Save browser forward behavior.
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Return to mode selection.
    page.get_by_test_id("mode-single-site").check()  # Change mode to single-site.
    _click_and_wait(page, "mode-continue", SITE_PATH)  # Continue to the site page.
    sync_api.expect(page.get_by_test_id(f"site-select-{SITE_ID}")).not_to_be_checked()  # Old target must clear.


@pytest.mark.parametrize(
    ("name", "mutator", "message"),
    [
        ("empty-versions", lambda page: _fill_versions(page, ("ap", "switch", "gateway"), ""), "target version"),
        pytest.param(
            "bad-version",
            lambda page: page.get_by_test_id("org-upgrade-version").fill("9.9.9"),
            "not available",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-005: invalid versions can reach confirmation."
            ),
        ),
        ("bad-phases-text", lambda page: page.get_by_test_id("org-upgrade-canary-phases").fill("abc"), "invalid"),
        pytest.param(
            "bad-phases-zero",
            lambda page: page.get_by_test_id("org-upgrade-canary-phases").fill("0"),
            "phase",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-006: invalid canary phases can reach confirmation."
            ),
        ),
        pytest.param(
            "bad-phases-high",
            lambda page: page.get_by_test_id("org-upgrade-canary-phases").fill("101"),
            "phase",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-006: invalid canary phases can reach confirmation."
            ),
        ),
        pytest.param(
            "bad-phases-order",
            lambda page: page.get_by_test_id("org-upgrade-canary-phases").fill("50,10"),
            "increasing",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-006: invalid canary phases can reach confirmation."
            ),
        ),
        pytest.param(
            "bad-max-failures",
            lambda page: page.get_by_test_id("org-upgrade-max-failures").fill("101"),
            "failure",
            marks=pytest.mark.xfail(strict=True, reason="F-upj-multisite-007: max failure validation can stay silent."),
        ),
        pytest.param(
            "bad-start-time",
            lambda page: page.get_by_test_id("org-upgrade-start-time").evaluate("node => node.value = 'not-a-date'"),
            "time",
            marks=pytest.mark.xfail(
                strict=True, reason="F-upj-multisite-008: malformed start time can reach confirmation."
            ),
        ),
    ],
)
def test_validation_errors_stay_in_page(page: Any, name: str, mutator: Callable[[Any], None], message: str) -> None:
    """Invalid values must show clear page errors and no raw JSON."""
    evidence = _watch(page)  # Capture required browser evidence.
    journey = f"validation-{name}"  # Name evidence by invalid value.
    try:  # Release the site lock even when validation fails as expected.
        _open_multisite_sites(page, evidence, journey)  # Open site selection.
        _select_sites(page, evidence, journey, (SITE_ID,))  # Use one site because this path stops at validation.
        _set_families(page, ("ap", "switch", "gateway"))  # Select all families for version validation.
        _fill_versions(page, ("ap", "switch", "gateway"))  # Start from valid versions.
        mutator(page)  # Apply the invalid value.
        _step(
            page, evidence, journey, 8, "submit-invalid", lambda: page.get_by_test_id("org-upgrade-review").click()
        )  # Submit.
        sync_api.expect(page.get_by_test_id("flash-message")).to_be_visible()  # The page must show the error region.
        sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text(
            re.compile(message, re.I)
        )  # Check clear text.
        assert page.url.endswith(OPTIONS_PATH)  # The browser must not open a raw JSON document.
    finally:  # Validation pages can still hold the selected site in session state.
        _release_locks(page)  # Clean the lock store.


@pytest.mark.xfail(strict=True, reason="F-upj-multisite-010: a double click sends two organization start requests.")
def test_confirmation_gate_and_replay_prevention(firmware_operator_page: Any) -> None:
    """The start button must require exact text and reject a replay."""
    page = firmware_operator_page  # Use a write-capable operator.
    evidence = _watch(page)  # Capture browser evidence.
    journey = "confirmation-gate-replay"  # Name evidence for this path.
    submissions: list[str] = []  # Count browser submit attempts to the start API.
    page.route(
        "**/api/org-upgrades", lambda route: _fake_replay_refusal(route, submissions)
    )  # Block a second real write.
    try:  # Release locks after the started job.
        _open_multisite_sites(page, evidence, journey)  # Open site selection.
        _select_sites(page, evidence, journey, (SITE_ID, SECOND_SITE_ID))  # Select both sites.
        _save_options(page, ("ap", "switch", "gateway"))  # Save valid options.
        for value in ("", "confirm", "CONFIRM ", " CONFIRM"):  # Try near misses that must stay disabled.
            page.get_by_test_id("org-upgrade-confirmation").fill(value)  # Type the near miss.
            _shot(page, journey, 8, "gate-" + (value.strip() or "blank").lower())  # Save each gate state.
            sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # Exact text only.
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # Type the exact word.
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_enabled()  # The button can start now.
        page.get_by_test_id("org-upgrade-start").dblclick()  # Double click attempts the replay path.
        sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text(
            re.compile("already started", re.I)
        )  # Replay must show inline.
        _shot(page, journey, 9, "double-click-refusal")  # Save the double-click result.
        assert len(submissions) <= 1  # The double-click must not send a second start request.
        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # Retype the exact word.
        page.get_by_test_id("org-upgrade-start").click()  # Attempt the second submit.
        sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text(
            re.compile("already started", re.I)
        )  # Replay must refuse.
        assert len(submissions) == 2  # The explicit replay sends one separate refused request.
    finally:  # Release locks for the next journey.
        _release_locks(page)  # Clean the lock store.


def _fake_replay_refusal(route: Any, submissions: list[str]) -> None:
    """Refuse a start request in the browser without starting another job."""
    submissions.append(route.request.url)  # Count each request that the browser sends.
    route.fulfill(  # Return the same envelope shape as the route returns for a replay.
        status=409,
        content_type="application/json",
        body=json.dumps(
            {
                "error": {
                    "code": "org_upgrade_already_submitted",
                    "message": "This confirmed request already started an organization upgrade.",
                }
            }
        ),
    )


@pytest.mark.xfail(
    strict=True, reason="F-upj-multisite-009: a second operator can open a synthetic organization job page."
)
def test_progress_cancel_ownership_and_lock_conflicts(firmware_operator_page: Any, second_operator_page: Any) -> None:
    """Progress, cancellation, ownership, and lock conflicts must be clear."""
    page = firmware_operator_page  # Use the owner page for the job.
    evidence = _watch(page)  # Capture browser evidence.
    journey = "progress-cancel-ownership"  # Name evidence for this path.
    try:  # Release owner locks at the end.
        _open_multisite_sites(page, evidence, journey)  # Open site selection.
        _select_sites(page, evidence, journey, (SITE_ID, SECOND_SITE_ID))  # Select both sites.
        _save_options(page, ("ap", "switch", "gateway"))  # Save valid options to establish organization context.
        job_url = page.url.replace(CONFIRM_PATH, "/upgrade/org/jobs/org-run-synthetic")  # Use a read-only status page.
        page.goto(job_url, wait_until="domcontentloaded")  # Open the progress page without another firmware write.
        poll_seconds = page.get_by_test_id("org-upgrade-progress").get_attribute(
            "data-poll-seconds"
        )  # Read poll interval.
        assert poll_seconds == "30"  # The page must poll at the documented interval.
        page.reload(wait_until="domcontentloaded")  # Revisit through reload.
        _shot(page, journey, 8, "progress-reload")  # Save reload behavior.
        page.go_back(wait_until="domcontentloaded")  # Go back from progress.
        _shot(page, journey, 9, "browser-back-from-job")  # Save back behavior.
        page.goto(job_url, wait_until="domcontentloaded")  # Revisit by URL.
        _shot(page, journey, 10, "job-url-revisit")  # Save direct revisit.
        _route_status(
            page,
            {
                **_final_payload("completed"),
                "site_upgrades": [
                    {
                        "site_name": "E2E Stand-In Site",
                        "device_family": "ap",
                        "status": "completed",
                        "total": 1,
                        "upgraded": 1,
                        "failed": 0,
                        "id": "done",
                    }
                ],
            },
        )  # Simulate completion.
        page.get_by_test_id("org-upgrade-refresh").click()  # Read completed state.
        _shot(page, journey, 11, "completed")  # Save completed state.
        page.get_by_test_id("org-upgrade-cancel-confirmation").fill("CANCEL")  # Try cancel after completion.
        page.route(
            "**/api/org-upgrades/*/cancel",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=json.dumps(_final_payload("cancelled"))
            ),
        )  # Simulate cancel.
        page.get_by_test_id("org-upgrade-cancel").click()  # Submit cancellation.
        _shot(page, journey, 12, "cancel-after-completion")  # Save refusal or result.
        second_operator_page.goto(job_url, wait_until="domcontentloaded")  # Open job as another operator.
        _shot(second_operator_page, journey, 13, "second-operator-job")  # Save ownership behavior.
        sync_api.expect(second_operator_page.get_by_test_id("flash-message")).to_contain_text(
            re.compile("did not start", re.I)
        )  # Ownership must refuse.
        _open_multisite_sites(
            second_operator_page, _watch(second_operator_page), "second-operator-same-sites"
        )  # Open competing selection.
        second_operator_page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select the locked first site.
        second_operator_page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # Select the locked second site.
        second_operator_page.get_by_test_id("multi-site-continue").click()  # Continue toward conflict.
        _shot(second_operator_page, journey, 14, "second-operator-same-sites")  # Save conflict visibility.
    finally:  # Release owner locks even when a lock check fails.
        _release_locks(page)  # Clean the owner lock records.
