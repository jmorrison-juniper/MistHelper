"""Verify browser-session persistence with the isolated feature blueprint."""

from pathlib import Path
from typing import Any


def fill_session_values(page: Any, portal_url: str) -> None:
    """Save one purchased value and one manual organization in the browser session."""
    page.goto(portal_url + "/license-comparison")  # Open the feature page.
    page.get_by_test_id("organization-checkbox").wait_for()
    page.get_by_test_id("organization-checkbox").check()
    purchase = page.locator(".purchase-input[data-row-id='org-1'] input[data-license='SUB-AI']")
    purchase.fill("4")
    purchase.press("Tab")  # Commit the change event that stores session state.
    page.get_by_test_id("add-manual-row").click()  # Add a session-only organization row.
    page.locator(".manual-name").fill("Manual office")  # Name the synthetic row.
    page.locator(".manual-row input[data-license='SUB-MAN']").fill("2")
    page.locator(".manual-row input[data-inventory='AP']").fill("3")
    page.locator(".manual-row input[data-inventory='AP']").press("Tab")


def assert_session_values(page: Any) -> None:
    """Check the selected organization, manual row, and purchase value."""
    page.get_by_test_id("organization-checkbox").wait_for()
    assert page.get_by_test_id("organization-checkbox").is_checked()
    assert page.locator(".manual-name").input_value() == "Manual office"  # Restore the manual row name.
    assert page.locator(".manual-row input[data-license='SUB-MAN']").input_value() == "2"
    assert page.locator(".manual-row input[data-inventory='AP']").input_value() == "3"
    organization_purchase = page.locator(
        ".purchase-input[data-row-id='org-1'] input[data-license='SUB-AI']"
    )  # Select the organization field when manual rows add more purchase inputs.
    assert organization_purchase.input_value() == "4"


def save_failure_screenshot(page: Any) -> Path:
    """Write a browser screenshot to the CI artifact directory after a failure."""
    target = Path(__file__).resolve().parents[4] / "test-artifacts/licensing-comparison-session-state.png"
    target.parent.mkdir(parents=True, exist_ok=True)  # Create the artifact directory when needed.
    page.screenshot(path=str(target), full_page=True)  # Preserve the failed browser state for review.
    return target  # Return the exact evidence path.


def test_session_values_survive_reload_and_same_tab_navigation(
    page: Any, browser: Any, licensing_portal_url: str
) -> None:
    """Keep manual and purchase values in one browser session and clear them in a new context."""
    try:
        fill_session_values(page, licensing_portal_url)  # Store the test values in the current tab.
        page.reload()  # Verify persistence across a page reload.
        assert_session_values(page)  # Check the restored values.
        page.goto(licensing_portal_url + "/test-away")  # Navigate within the same origin.
        page.go_back()  # Return to the dashboard in the same browser tab.
        assert_session_values(page)  # Check values after in-page history navigation.
        fresh_context = browser.new_context()  # Create a separate browser session.
        fresh_page = fresh_context.new_page()  # Open a tab with empty session storage.
        fresh_page.goto(licensing_portal_url + "/license-comparison")  # Load the dashboard in the new session.
        assert fresh_page.locator(".manual-row").count() == 0  # Keep the prior manual row private to its session.
        assert fresh_page.evaluate("JSON.parse(sessionStorage.getItem('misthelper.licensingComparison.v1'))") == {
            "selected": [],
            "manual": [],
            "purchased": {},
        }  # Keep the prior tab values private.
        fresh_context.close()  # Close the isolated browser context.
    except Exception:
        save_failure_screenshot(page)  # Preserve the failure for the CI artifact step.
        raise  # Keep the original browser failure visible to pytest.
