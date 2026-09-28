"""Cross-cutting journeys for the upgrade capture portal.

Why:
    Issue #3200 asks for the journeys that both portal modes share. These tests
    drive the sign-in, selection, navigation, lock, history, error, theme, and
    viewport paths in a real browser.
"""

from __future__ import annotations

import re  # Match portal URLs after form submissions.
import time  # Measure each step duration for the evidence record.
from collections.abc import Callable  # Type the optional step action.
from pathlib import Path  # Build Windows-safe artifact paths.
from typing import Any  # Playwright objects have no project-local stubs.

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")
expect = sync_api.expect  # Use Playwright retry assertions for live browser state.

pytestmark = pytest.mark.journey  # The journey runner opts these tests in.

AGENT = "upj-crosscut"  # The assigned explorer name.
SHOTS = (
    Path(__file__).parents[4] / "data" / "test-artifacts" / "upgrade-portal-journeys" / AGENT
)  # The required screenshot folder.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site.
ORG_ID = "11111111-1111-1111-1111-111111111111"  # The stand-in organization.
PRE_CAPTURE_ID = "e2e-capture-pre-0001"  # The seeded pre-check capture.
POST_CAPTURE_ID = "e2e-capture-post-0001"  # The seeded post-check capture.
SIGNIN_PATH = "/auth/signin"  # The sign-in page path.
ORG_PATH = "/select/org"  # The organization picker path.
MODE_PATH = "/select/mode"  # The mode picker path.
SITE_PATH = "/select/site"  # The site picker path.
HISTORY_PATH = "/history"  # The history page path.
COMPARE_PATH = "/compare"  # The comparison picker path.
OK = 200  # A rendered page answers this status.
BAD_REQUEST = 400  # A CSRF refusal answers this status.
NOT_FOUND = 404  # A missing route or record answers this status.
GATE_TIMEOUT_MS = 7000  # The browser scripts should settle quickly.
VIEWPORTS = ((390, 844), (1024, 768))  # The narrow and tablet sizes from the mission.
MAIN_NAV = ("Sites", "History", "Compare")  # The signed-in navigation links.


class StepShots:
    """Take required screenshots and record timing for one journey."""

    def __init__(self, page: Any, journey: str) -> None:
        """Attach browser event listeners and prepare the screenshot folder.

        Args:
            page: The Playwright page for this journey.
            journey: The stable name of the journey.
        """
        self.page = page  # Store the page that every step uses.
        self.journey = journey  # Store the name used in screenshot files.
        self.count = 0  # Count screenshots from one for each journey.
        self.console_errors: list[str] = []  # Keep browser console errors.
        self.page_errors: list[str] = []  # Keep uncaught page errors.
        self.failed_requests: list[str] = []  # Keep requests that failed before a response.
        self.error_responses: list[str] = []  # Keep HTTP responses with an error status.
        SHOTS.mkdir(parents=True, exist_ok=True)  # Create the required artifact folder.
        page.on("console", self._console)  # Collect browser console output.
        page.on("pageerror", lambda error: self.page_errors.append(str(error)))  # Collect script faults.
        page.on("requestfailed", lambda request: self.failed_requests.append(request.url))  # Collect failures.
        page.on("response", self._response)  # Collect failed HTTP answers.

    def _console(self, message: Any) -> None:
        """Record console errors only."""
        if message.type == "error":  # A console error is actionable evidence.
            self.console_errors.append(message.text)  # Store the error text.

    def _response(self, response: Any) -> None:
        """Record HTTP responses that indicate a fault."""
        if response.status >= BAD_REQUEST:  # Successful assets would add noise.
            self.error_responses.append(f"{response.status} {response.request.method} {response.url}")  # Store it.

    def step(self, name: str, action: Callable[[], Any] | None = None) -> Path:
        """Run one action, then save a full-page screenshot.

        Args:
            name: The short step name.
            action: The optional browser action.

        Returns:
            The screenshot path.
        """
        started = time.perf_counter()  # Measure the action time.
        if action is not None:  # Some steps only record the current page.
            action()  # Drive the browser.
        elapsed = time.perf_counter() - started  # Finish the step timer.
        self.count += 1  # Advance the screenshot number.
        safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")  # Make a file-safe name.
        path = SHOTS / f"{self.journey}-{self.count:02d}-{safe_name}.png"  # Follow the required pattern.
        self.page.screenshot(path=str(path), full_page=True)  # Capture the complete page.
        self.page.evaluate("name => console.debug('journey step', name)", f"{name}:{elapsed:.3f}")  # Mark timing.
        return path  # Let a caller include the path in an assertion.


def goto(page: Any, shots: StepShots, path: str, name: str, status: int = OK) -> Any:
    """Open one path and require the expected status.

    Args:
        page: The Playwright page.
        shots: The screenshot recorder.
        path: The portal path.
        name: The step name.
        status: The expected HTTP status.

    Returns:
        The navigation response.
    """
    responses: list[Any] = []  # Keep the response from inside the lambda.
    shots.step(name, lambda: responses.append(page.goto(path, wait_until="domcontentloaded")))  # Open the page.
    answer = responses[0]  # One navigation gives one response.
    assert answer is not None, f"{path} returned no browser response."  # A missing response hides the page state.
    assert answer.status == status, f"{path} answered {answer.status}, not {status}."  # Keep route contracts visible.
    return answer  # A caller may inspect headers.


def assert_one_h1(page: Any) -> None:
    """Require one visible page heading."""
    count = page.locator("h1").count()  # Count the page headings.
    assert count == 1, f"The page has {count} h1 elements."  # Each page must have one primary heading.


def assert_labeled_inputs(page: Any) -> None:
    """Require a visible label or an aria label for each visible input."""
    missing = page.locator("input:visible, select:visible, textarea:visible").evaluate_all("""
        nodes => nodes.filter(node => {
            if (node.type === 'hidden') return false;
            if (node.getAttribute('aria-label')) return false;
            if (node.getAttribute('aria-labelledby')) return false;
            if (node.id && document.querySelector(`label[for="${CSS.escape(node.id)}"]`)) return false;
            return true;
        }).map(node => node.getAttribute('data-testid') || node.id || node.name || node.tagName)
        """)  # Ask the browser to use its DOM labels.
    assert missing == [], f"Visible fields without labels: {missing}."  # A screen reader needs a name.


def assert_icon_buttons_named(page: Any) -> None:
    """Require accessible names for icon-only buttons and links."""
    missing = page.locator("button:visible, a:visible").evaluate_all("""
        nodes => nodes.filter(node => {
            const text = (node.innerText || '').trim();
            const name = node.getAttribute('aria-label') || node.getAttribute('title') || text;
            const visibleIcon = node.querySelector('[aria-hidden="true"], svg, .stale-symbol');
            return visibleIcon && !name;
        }).map(node => node.getAttribute('data-testid') || node.href || node.tagName)
        """)  # Let the page report controls that need an accessible name.
    assert missing == [], f"Icon controls without a name: {missing}."  # Icon-only controls need text.


def assert_focus_visible(page: Any) -> None:
    """Press Tab and require a visible focus indicator."""
    page.keyboard.press("Tab")  # Move focus to the first focusable control.
    visible = page.evaluate("""
        () => {
            const node = document.activeElement;
            if (!node || node === document.body) return false;
            const style = getComputedStyle(node);
            const box = node.getBoundingClientRect();
            const outline = style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0;
            const shadow = style.boxShadow && style.boxShadow !== 'none';
            return box.width > 0 && box.height > 0 && (outline || shadow);
        }
        """)  # Read the actual painted focus style.
    assert visible is True, "The focused element has no visible outline or shadow."  # Keyboard users need focus.


def assert_no_horizontal_scroll(page: Any) -> None:
    """Require the document to fit the viewport width."""
    fits = page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"
    )  # Compare widths.
    assert fits is True, "The page has horizontal document scroll."  # Forms must fit a narrow viewport.


def assert_signed_in_nav(page: Any) -> None:
    """Require the signed-in navigation options to be visible."""
    for label in MAIN_NAV:  # Check each shared menu option.
        expect(page.get_by_role("link", name=label)).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The nav link is visible.
    expect(page.get_by_test_id("theme-select")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The theme switch is visible.
    expect(page.get_by_test_id("signout-button")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # Sign out is visible.


def assert_signed_out_nav(page: Any) -> None:
    """Require the signed-out header to hide signed-in options."""
    for label in MAIN_NAV:  # Signed-out pages must not show app links.
        expect(page.get_by_role("link", name=label)).to_have_count(0)  # The link is absent.
    expect(page.get_by_test_id("theme-select")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The theme switch remains.


def assert_common_accessibility(page: Any, signed_in: bool = True) -> None:
    """Run the shared accessibility checks for one page."""
    assert_one_h1(page)  # Each page needs one primary heading.
    assert_labeled_inputs(page)  # Each visible field needs a label.
    assert_icon_buttons_named(page)  # Icon controls need accessible names.
    if signed_in:  # Signed-in pages have the full menu.
        assert_signed_in_nav(page)  # Verify the navigation visually and by role.
    else:  # Signed-out pages show only the brand and theme controls.
        assert_signed_out_nav(page)  # Verify hidden links on sign-in pages.


def choose_org(page: Any) -> None:
    """Choose the stand-in organization."""
    page.get_by_test_id(f"org-select-{ORG_ID}").click()  # Submit the row form.
    page.wait_for_url(re.compile(r".*/select/mode$"))  # The mode picker follows the organization.


def choose_mode(page: Any, mode_id: str) -> None:
    """Choose one upgrade mode and open the site picker."""
    page.get_by_test_id(mode_id).check()  # Select the requested radio button.
    page.get_by_test_id("mode-continue").click()  # Submit the mode form.
    page.wait_for_url(re.compile(r".*/select/site$"))  # The site picker follows the mode.


def open_inventory(page: Any, site_id: str = SITE_ID) -> None:
    """Open the inventory page of one site."""
    page.get_by_test_id(f"site-open-{site_id}").click()  # Use the published Open control.
    page.wait_for_url(re.compile(rf".*/select/site/{re.escape(site_id)}$"))  # Wait for the inventory page.


def open_capture(page: Any) -> None:
    """Open the capture page from the inventory page."""
    page.get_by_test_id("site-capture-link").click()  # Use the forward link on the inventory page.
    page.wait_for_url(re.compile(r".*/captures/.*"))  # Wait for the capture page.


def csrf_token(page: Any) -> str:
    """Read the current CSRF token from the page."""
    token = page.get_by_test_id("csrf-meta").get_attribute("content")  # The layout exposes the token.
    assert token, "The page did not publish a CSRF token."  # POST requests need this token.
    return token  # Return the value for page.request.


def test_sign_in_sign_out_and_signed_out_errors(signed_out_page: Any, browser_token_value: str) -> None:
    """Drive the shared sign-in path, sign-out, and signed-out redirects."""
    page = signed_out_page  # Use the clean context required for sign-in.
    shots = StepShots(page, "signin")  # Record the sign-in journey.
    goto(page, shots, SIGNIN_PATH, "sign in form")  # Open the real form.
    assert_common_accessibility(page, signed_in=False)  # Check labels, heading, and signed-out nav.
    expect(page.get_by_test_id("signin-email")).to_be_visible()  # The email field is visible.
    expect(page.get_by_test_id("signin-password")).to_be_visible()  # The password field is visible.
    expect(page.locator("#signin-host")).to_be_visible()  # The Mist cloud picker is visible.
    page.get_by_test_id("signin-submit").click()  # Empty required fields must stop in the browser.
    shots.step("empty submit blocked")  # Capture the browser validation state.
    assert (
        page.locator('form[action="/auth/signin"]').evaluate("form => form.checkValidity()") is False
    )  # Empty fields are invalid.
    page.get_by_test_id("signin-mode-browser-token").check()  # Select the browser-token path.
    page.get_by_test_id("signin-browser-token").fill(f"{browser_token_value}-wrong")  # Type a refused fake token.
    shots.step("wrong browser token", lambda: page.get_by_test_id("signin-submit").click())  # Submit the refusal.
    expect(page.get_by_test_id("signin-error")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The error appears.
    page.get_by_test_id("signin-browser-token").fill(browser_token_value)  # Type the accepted fake token.
    page.get_by_test_id("signin-submit").click()  # Submit the accepted browser token.
    page.wait_for_url(re.compile(r".*/select/org$"), timeout=GATE_TIMEOUT_MS)  # The org picker follows sign-in.
    shots.step("browser token opens orgs")  # Capture the signed-in picker.
    assert_common_accessibility(page, signed_in=True)  # The signed-in header is present.
    shots.step("sign out", lambda: page.get_by_test_id("signout-button").click())  # End the session.
    page.wait_for_url(re.compile(r".*/auth/signin$"), timeout=GATE_TIMEOUT_MS)  # Sign-out returns to the form.
    assert_common_accessibility(page, signed_in=False)  # The form is readable after sign-out.
    answer = page.goto(ORG_PATH, wait_until="domcontentloaded")  # Visit a page that needs a session.
    assert answer is not None and answer.status != 401  # The browser must not receive a raw 401 page.
    expect(page.locator("h1")).to_contain_text("Sign in")  # The route returns the form.
    shots.step("protected page after sign out")  # Capture the redirect result.
    goto(page, shots, "/auth/twofactor", "two factor page")  # Open the second factor form.
    assert_common_accessibility(page, signed_in=False)  # The second factor page hides signed-in links.
    page.get_by_test_id("twofactor-code").fill("000000")  # Type a refused stand-in code.
    shots.step("two factor refused", lambda: page.get_by_test_id("twofactor-submit").click())  # Submit without wait.
    expect(page.get_by_test_id("signin-error")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The refusal is visible.


def test_navigation_selection_switching_and_themes(page: Any) -> None:
    """Drive navigation, organization choice, mode switching, and themes."""
    shots = StepShots(page, "navigation-selection-theme")  # Record the cross-page journey.
    goto(page, shots, ORG_PATH, "organization picker")  # Open the organization picker.
    assert_common_accessibility(page)  # Check shared header and controls.
    shots.step("mode picker", lambda: choose_org(page))  # Select the organization.
    assert_common_accessibility(page)  # Check the mode page.
    page.get_by_test_id("mode-single-site").check()  # Choose single-site first.
    shots.step("single site chosen")  # Capture the selected radio button.
    page.get_by_test_id("mode-continue").click()  # Submit the single-site mode.
    page.wait_for_url(re.compile(r".*/select/site$"))  # The site list follows.
    shots.step("single site picker")  # Capture the single-site picker.
    open_inventory(page)  # Open a site inventory.
    shots.step("inventory from site link")  # Capture the inventory page.
    for target, pattern in (
        ("nav-history", r".*/history.*"),
        ("nav-compare", r".*/compare.*"),
        ("nav-sites", r".*/select/site.*"),
    ):  # Test every nav link.
        page.get_by_test_id(target).click()  # Press one visible menu link.
        page.wait_for_url(re.compile(pattern))  # Verify the link target.
        shots.step(f"{target} works")  # Capture the target page.
        assert_common_accessibility(page)  # Verify the target page header.
    goto(page, shots, MODE_PATH, "mode picker before multi")  # Return to mode selection.
    choose_mode(page, "mode-multi-site")  # Select multi-site mode.
    shots.step("multi site picker")  # Capture the multi-site controls.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select the first site.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # Select the second site.
    shots.step("multi targets selected")  # Capture the checked targets.
    page.get_by_test_id("multi-site-continue").click()  # Store the target list.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Options page follows.
    shots.step("multi options after targets")  # Capture the selected targets on the options page.
    goto(page, shots, MODE_PATH, "mode picker before single")  # Return to the mode picker.
    choose_mode(page, "mode-single-site")  # Switch to single-site mode.
    shots.step("single site after mode switch")  # Capture the single-site list.
    goto(page, shots, MODE_PATH, "mode picker before returning multi")  # Return again to the mode picker.
    choose_mode(page, "mode-multi-site")  # Switch back to multi-site mode.
    shots.step("multi site after clear")  # Capture the cleared multi-site list.
    checked = page.locator('input[name="site_ids"]:checked').count()  # Count selected site targets.
    assert checked == 0, f"Mode switch left {checked} selected site target(s)."  # Old targets must clear.
    for theme in ("default", "magenta"):  # Test both offered themes.
        page.get_by_test_id("theme-select").select_option(theme)  # Pick the theme.
        shots.step(f"theme {theme}", lambda: page.get_by_role("button", name="Apply theme").click())  # Apply it.
        expect(page.get_by_test_id("theme-select")).to_have_value(theme)  # Verify the selection survived.


def test_locks_heartbeat_conflict_and_release(page: Any, second_operator_page: Any) -> None:
    """Drive the lock banner, heartbeat, conflict, and release."""
    first = page  # Name the first operator page.
    second = second_operator_page  # Name the second operator page.
    first_shots = StepShots(first, "locks-first-operator")  # Record the holder journey.
    second_shots = StepShots(second, "locks-second-operator")  # Record the conflict journey.
    goto(first, first_shots, f"/select/site/{SITE_ID}", "first inventory")  # Open the first inventory.
    open_capture(first)  # Open the lock banner page.
    first_shots.step("free lock banner")  # Capture the free state.
    expect(first.get_by_test_id("lock-banner")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The banner is visible.
    first.get_by_test_id("lock-take-button").click()  # Take the site through the page.
    expect(first.get_by_test_id("lock-state-message")).to_contain_text("You hold", timeout=GATE_TIMEOUT_MS)  # Held.
    first_shots.step("held lock banner")  # Capture the held state.
    token = first.get_by_test_id("lock-banner").get_attribute("data-lock-token")  # Read the heartbeat token.
    assert token, "The held banner has no lock token."  # The heartbeat needs this value.
    heartbeat = first.request.post(  # Beat the lock through the documented API.
        f"/api/sites/{SITE_ID}/lock/heartbeat",
        data={"lock_token": token},
        headers={"X-CSRFToken": csrf_token(first)},
    )
    assert heartbeat.status == OK, f"Heartbeat answered {heartbeat.status}."  # The heartbeat works.
    first_shots.step("heartbeat accepted")  # Capture the page after the heartbeat.
    goto(
        second, second_shots, first.url.replace(first.evaluate("() => location.origin"), ""), "second sees lock"
    )  # Same page.
    expect(second.get_by_test_id("lock-state-message")).to_contain_text(
        "holds this site", timeout=GATE_TIMEOUT_MS
    )  # Conflict.
    second.get_by_test_id("lock-take-button").click()  # Try to take the held site.
    expect(second.get_by_test_id("lock-error")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The conflict is visible.
    expect(second.get_by_test_id("lock-cooldown")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The wait is visible.
    second_shots.step("second operator conflict")  # Capture the conflict state.
    first.get_by_test_id("lock-release-button").click()  # Release the lock through the page.
    expect(first.get_by_test_id("lock-state-message")).to_contain_text("released", timeout=GATE_TIMEOUT_MS)  # Released.
    first_shots.step("lock released")  # Capture the released state.
    second.reload(wait_until="domcontentloaded")  # Read the state after release.
    second_shots.step("second operator after release")  # Capture the free state for the second operator.


def test_history_comparison_errors_and_viewports(page: Any, signed_out_page: Any) -> None:
    """Drive read-only history, comparison, errors, and viewport checks."""
    shots = StepShots(page, "history-comparison-errors")  # Record the read-only journey.
    goto(page, shots, f"{HISTORY_PATH}?site_id={SITE_ID}&limit=1", "history first page")  # Open history.
    assert_common_accessibility(page)  # Check the history page.
    expect(page.get_by_test_id("history-table")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # Capture table exists.
    next_control = page.get_by_test_id("history-page-next")  # Read the next control.
    if next_control.get_attribute("href"):  # The stand-in may have a second page.
        shots.step("history next page", lambda: next_control.click())  # Open the next page.
    first_open = page.locator('[data-testid^="history-open-"]').first  # Read the first Open button.
    if first_open.count():  # A seeded capture should exist.
        shots.step("history open capture", lambda: first_open.click())  # Open the capture.
        expect(page.locator("h1")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The capture page rendered.
    goto(page, shots, f"{HISTORY_PATH}?site_id=00000000-0000-0000-0000-000000000000", "history empty state")  # Empty.
    expect(page.get_by_text("The portal found no stored capture")).to_be_visible(
        timeout=GATE_TIMEOUT_MS
    )  # Empty state.
    goto(page, shots, COMPARE_PATH, "compare picker")  # Open the comparison picker.
    assert_common_accessibility(page)  # Check the picker.
    goto(
        page, shots, f"{COMPARE_PATH}?before={PRE_CAPTURE_ID}&after={POST_CAPTURE_ID}", "comparison result"
    )  # Compare.
    expect(page.get_by_test_id("compare-statistics")).to_be_visible(timeout=GATE_TIMEOUT_MS)  # Result exists.
    goto(page, shots, "/unknown-upgrade-portal-route", "unknown url", NOT_FOUND)  # 404 page.
    shots.step("unknown url reviewed")  # The screenshot records whether the page offers recovery.
    page.goto(
        "/runs/not-a-real-run", wait_until="domcontentloaded"
    )  # Open the missing run without hiding its bad status.
    shots.step("missing run reviewed")  # The screenshot records the known JSON defect.
    page.goto(
        "/upgrade/org/jobs/not-a-real-job", wait_until="domcontentloaded"
    )  # Open the missing job without hiding its bad status.
    shots.step("missing org job reviewed")  # The screenshot records whether the page offers recovery.
    csrf_answer = page.request.post(MODE_PATH, data={"mode": "single_site"})  # POST without the token.
    assert csrf_answer.status == BAD_REQUEST, f"CSRF refusal answered {csrf_answer.status}."  # The guard failed closed.
    csrf_body = csrf_answer.text()  # Read the refusal body.
    assert (
        "csrf_missing" in csrf_body
    ), "The CSRF refusal body did not name the missing token."  # Record the guard code.
    shots.step("csrf post refusal checked")  # Capture the current page after the request check.
    out_shots = StepShots(signed_out_page, "signed-out-required-page")  # Record the missing-session page.
    answer = signed_out_page.goto(HISTORY_PATH, wait_until="domcontentloaded")  # Open a protected page signed out.
    assert answer is not None and answer.status != 401  # The browser must not see a raw 401.
    out_shots.step("history needs session")  # Capture the sign-in form.
    expect(signed_out_page.locator("h1")).to_contain_text("Sign in")  # The form is shown.
    for width, height in VIEWPORTS:  # Check the requested viewport sizes.
        page.set_viewport_size({"width": width, "height": height})  # Resize the browser viewport.
        for path, label in (
            (SIGNIN_PATH, "signin"),
            (ORG_PATH, "org"),
            (SITE_PATH, "sites"),
            (HISTORY_PATH, "history"),
            (COMPARE_PATH, "compare"),
        ):  # Main pages.
            page.goto(path, wait_until="domcontentloaded")  # Open the page at this size.
            shots.step(f"viewport {width}x{height} {label}")  # Capture the layout.
            assert_no_horizontal_scroll(page)  # Forms and cards must not force body scroll.


@pytest.mark.xfail(
    strict=True, reason="F-upj-crosscut-01: missing run returns status 200 and renders JSON instead of an error page"
)
def test_missing_run_error_page_offers_back_link(page: Any) -> None:
    """A missing run must render the shared error page."""
    shots = StepShots(page, "missing-run-error-page")  # Record the defect proof.
    goto(page, shots, "/runs/not-a-real-run", "missing run", NOT_FOUND)  # Open the missing run.
    expect(page.get_by_role("link", name="Go to the site list")).to_be_visible(
        timeout=GATE_TIMEOUT_MS
    )  # Recovery link.


@pytest.mark.xfail(strict=True, reason="F-upj-crosscut-02: missing org job renders JSON instead of an error page")
def test_missing_org_job_error_page_offers_back_link(page: Any) -> None:
    """A missing organization job must render the shared error page."""
    shots = StepShots(page, "missing-org-job-error-page")  # Record the defect proof.
    goto(page, shots, "/upgrade/org/jobs/not-a-real-job", "missing org job", NOT_FOUND)  # Open the missing job.
    expect(page.get_by_role("link", name="Go to the site list")).to_be_visible(
        timeout=GATE_TIMEOUT_MS
    )  # Recovery link.


@pytest.mark.xfail(strict=True, reason="F-upj-crosscut-03: unknown URL renders JSON instead of an error page")
def test_unknown_url_error_page_offers_back_link(page: Any) -> None:
    """An unknown URL must render the shared error page."""
    shots = StepShots(page, "unknown-url-error-page")  # Record the defect proof.
    goto(page, shots, "/unknown-upgrade-portal-route", "unknown url", NOT_FOUND)  # Open the unknown path.
    expect(page.get_by_role("link", name="Go to the site list")).to_be_visible(
        timeout=GATE_TIMEOUT_MS
    )  # Recovery link.


@pytest.mark.xfail(strict=True, reason="F-upj-crosscut-04: CSRF POST returns JSON without a recovery link")
def test_csrf_post_error_response_offers_back_link(page: Any) -> None:
    """A CSRF refusal must offer a way back."""
    answer = page.request.post(MODE_PATH, data={"mode": "single_site"})  # Send no CSRF token.
    assert answer.status == BAD_REQUEST, f"CSRF refusal answered {answer.status}."  # The guard must fail closed.
    assert "Go to the site list" in answer.text(), "The CSRF error offers no way back."  # Recovery link.
