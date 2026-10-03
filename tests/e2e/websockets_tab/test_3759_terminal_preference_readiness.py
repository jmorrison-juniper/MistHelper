"""Check the preference wait with a local browser page."""

from __future__ import annotations  # Keep annotations lazy for optional imports.

import pytest  # Require failures from the bounded readiness control.

playwright_sync_api = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is absent, so the readiness controls cannot run",
)  # Keep the test module optional when browser dependencies are absent.
PREFERENCE_SELECTOR = '[data-testid="ws-terminal-copy-on-select"]'  # Match the J9 checkbox.
CHECKED_PREFERENCE_SCRIPT = """(selector) => {
    const control = document.querySelector(selector); // Find the preference control.
    return control instanceof HTMLInputElement && control.checked; // Require a checked input.
}"""  # Use the same checked-state condition as J9.


def test_3759_checked_preference_waits_for_deferred_initialization(page) -> None:
    """The native wait must pass after a delayed browser state change."""
    markup = f'<input type="checkbox" {PREFERENCE_SELECTOR[1:-1]}>'  # Build the initially unchecked control.
    page.set_content(markup)  # Start from the template-like DOM state.
    checkbox = page.locator(PREFERENCE_SELECTOR)  # Observe the control by its stable test ID.
    assert checkbox.is_checked() is False  # Confirm the control starts unchecked.
    page.evaluate(
        """(selector) => window.setTimeout(() => {
            const control = document.querySelector(selector); // Find the controlled test element.
            control.checked = true; // Simulate deferred preference initialization.
        }, 25)""",
        PREFERENCE_SELECTOR,
    )  # Schedule a browser event instead of sleeping in the test.
    page.wait_for_function(
        CHECKED_PREFERENCE_SCRIPT,
        arg=PREFERENCE_SELECTOR,
        timeout=1_000,
    )  # Wait with the same native predicate as J9.
    assert checkbox.is_checked() is True  # Confirm initialization completed before the snapshot.


def test_3759_unavailable_preference_fails_within_timeout(page) -> None:
    """The native wait must fail when the preference never becomes checked."""
    markup = f'<input type="checkbox" {PREFERENCE_SELECTOR[1:-1]}>'  # Build the initially unchecked control.
    page.set_content(markup)  # Keep the control in its initial state.
    checkbox = page.locator(PREFERENCE_SELECTOR)  # Observe the same control as J9.
    with pytest.raises(playwright_sync_api.TimeoutError):  # Require Playwright to report the bounded failure.
        page.wait_for_function(
            CHECKED_PREFERENCE_SCRIPT,
            arg=PREFERENCE_SELECTOR,
            timeout=100,
        )  # Stop waiting when the controlled preference remains unavailable.
    assert checkbox.is_checked() is False  # Confirm the failure did not change the control.
