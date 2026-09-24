"""Browser tests for the organization upgrade options form."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"
SCREENSHOT_DIRECTORY = Path(__file__).parents[3] / "data" / "test-artifacts" / "upgrade-portal-journeys" / "fix-options"


def _save_screenshot(page: Any, name: str) -> Path:
    """Save one required journey screenshot."""
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep required evidence under the repository data tree.
    path = SCREENSHOT_DIRECTORY / name  # Give each behavior its own stable file name.
    page.screenshot(path=str(path), full_page=True)  # Capture the full page for visual review.
    return path  # Return the path so the assertion can prove the file exists.


def _open_org_options(page: Any) -> None:
    """Open the organization options page with two selected sites."""
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode chooser with a signed test session.
    page.get_by_test_id("mode-multi-site").check()  # Select the organization workflow under test.
    page.get_by_test_id("mode-continue").click()  # Move to the site picker.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select the first stand-in site.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # Select the second stand-in site.
    page.get_by_test_id("multi-site-continue").click()  # Open the shared options form.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait until the form script is ready.


def _expect_hidden(page: Any, test_id: str, hidden: bool) -> None:
    """Assert the visibility and disabled state of one conditional control."""
    group = page.get_by_test_id(test_id)  # Find the control group by the stable test identifier.
    if hidden:  # Hidden groups must carry the hidden attribute.
        sync_api.expect(group).to_be_hidden()  # Prove the operator cannot see an irrelevant control.
    else:  # Visible groups must not carry the hidden attribute.
        sync_api.expect(group).to_be_visible()  # Prove the operator can use a relevant control.
    disabled = group.locator("input:disabled, select:disabled, textarea:disabled").count()  # Count disabled inputs.
    enabled = group.locator(
        "input:not(:disabled), select:not(:disabled), textarea:not(:disabled)"
    ).count()  # Count enabled inputs.
    assert (disabled > 0) is hidden  # Hidden groups must not send a value through FormData.
    assert (enabled > 0) is not hidden  # Visible groups need enabled controls for the operator.


def _set_family_state(page: Any, ap: bool, switch: bool, gateway: bool) -> None:
    """Select one device-family combination."""
    page.get_by_test_id("org-upgrade-type-ap").set_checked(ap)  # Set the access point family state.
    page.get_by_test_id("org-upgrade-type-switch").set_checked(switch)  # Set the switch family state.
    page.get_by_test_id("org-upgrade-type-gateway").set_checked(gateway)  # Set the gateway family state.


def test_back_from_confirm_restores_every_multisite_choice(page: Any) -> None:
    """Back from confirmation must not reset saved organization choices."""
    _open_org_options(page)  # Open the multi-site form with the stand-in sites.
    page.get_by_test_id("org-upgrade-type-gateway").uncheck()  # Clear one family before the save.
    page.get_by_test_id("org-upgrade-version").fill("0.15.1")  # Select the AP target version.
    page.get_by_test_id("org-upgrade-switch-version").fill("0.15.1")  # Select the switch target version.
    page.get_by_test_id("org-reboot-no").check()  # Preserve the no-reboot safety choice.
    page.get_by_test_id("org-junos-no").check()  # Preserve the no-Junos-action safety choice.
    page.get_by_test_id("org-upgrade-force").check()  # Preserve the force checkbox state.
    page.get_by_test_id("org-strategy-big_bang").check()  # Use a strategy that hides canary phases.
    page.get_by_test_id("org-upgrade-review").click()  # Save the options and open confirmation.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # Wait for the accepted route.
    page.get_by_role("link", name="Back").click()  # Return to the options page through the visible link.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait for the restored form.
    sync_api.expect(page.get_by_test_id("org-upgrade-type-ap")).to_be_checked()  # AP must stay selected.
    sync_api.expect(page.get_by_test_id("org-upgrade-type-switch")).to_be_checked()  # Switch must stay selected.
    sync_api.expect(page.get_by_test_id("org-upgrade-type-gateway")).not_to_be_checked()  # Gateway must stay clear.
    sync_api.expect(page.get_by_test_id("org-reboot-no")).to_be_checked()  # Reboot No must stay selected.
    sync_api.expect(page.get_by_test_id("org-junos-no")).to_be_checked()  # Junos No must stay selected.
    sync_api.expect(page.get_by_test_id("org-upgrade-force")).to_be_checked()  # Force must stay selected.
    assert _save_screenshot(page, "restore-saved-choices.png").exists()  # Keep visual proof of restored choices.


def test_family_controls_hide_for_each_selected_combination(page: Any) -> None:
    """The form must show only controls that apply to selected families."""
    _open_org_options(page)  # Open the multi-site form with the stand-in sites.
    combinations = (  # Cover every non-empty family combination.
        (True, False, False),
        (False, True, False),
        (False, False, True),
        (True, True, False),
        (True, False, True),
        (False, True, True),
        (True, True, True),
    )
    for ap, switch, gateway in combinations:  # Drive all seven supported combinations.
        _set_family_state(page, ap, switch, gateway)  # Apply one combination through real controls.
        has_junos_device = switch or gateway  # Switches and gateways use the Junos controls.
        _expect_hidden(page, "org-upgrade-ap-version-group", not ap)  # AP target follows AP selection.
        _expect_hidden(page, "org-upgrade-switch-version-group", not switch)  # Switch target follows switch selection.
        _expect_hidden(page, "org-upgrade-gateway-version-group", not gateway)  # Gateway target follows gateway.
        _expect_hidden(page, "org-upgrade-reboot-group", not has_junos_device)  # Reboot follows Junos families.
        _expect_hidden(page, "org-upgrade-reboot-at-field", not has_junos_device)  # Delay follows Junos families.
        _expect_hidden(page, "org-upgrade-junos-file-action-group", not has_junos_device)  # File action follows Junos.
    page.get_by_test_id("org-strategy-big_bang").check()  # Non-canary strategy must hide the phase control.
    _expect_hidden(page, "org-upgrade-canary-phases-field", True)  # Phases apply only to canary.
    page.get_by_test_id("org-strategy-canary").check()  # Canary strategy must show the phase control.
    _expect_hidden(page, "org-upgrade-canary-phases-field", False)  # Phases return when canary returns.
    assert _save_screenshot(page, "family-visibility.png").exists()  # Keep visual proof of the hidden controls.


def test_reboot_delay_placeholder_is_guidance_not_a_value(page: Any) -> None:
    """The reboot delay placeholder must look different from a saved value."""
    _open_org_options(page)  # Open the multi-site form with the stand-in sites.
    reboot_at = page.get_by_test_id("org-upgrade-reboot-at")  # Find the delay control.
    sync_api.expect(reboot_at).to_have_attribute(
        "placeholder", "Empty: reboot as soon as the write ends"
    )  # Name action.
    style = reboot_at.evaluate(  # Read the pseudo-element style from the browser engine.
        "(node) => { const style = getComputedStyle(node, '::placeholder'); "
        "return {color: style.color, fontStyle: style.fontStyle, opacity: style.opacity}; }"
    )
    assert style["fontStyle"] == "italic"  # A placeholder must not look like an entered value.
    assert style["opacity"] != "1"  # A dim placeholder must not look like an entered value.
    assert _save_screenshot(page, "placeholder-guidance.png").exists()  # Keep visual proof of the placeholder style.


def test_refused_review_moves_the_message_into_view(page: Any) -> None:
    """A refused Review must focus the flash and name a control that the multi-site page paints."""
    _open_org_options(page)  # Open the multi-site form with the stand-in sites.
    page.get_by_test_id("org-upgrade-version").fill("")  # Leave required targets empty to trigger a refusal.
    page.get_by_test_id("org-upgrade-switch-version").fill("")  # Leave the switch target empty too.
    page.get_by_test_id("org-upgrade-gateway-version").fill("")  # Leave the gateway target empty too.
    page.get_by_test_id("org-upgrade-review").click()  # Submit an invalid request through the script path.
    flash = page.get_by_test_id("flash-message")  # Find the shared flash region.
    # WHY: Issue #3273. The multi-site page paints no control with the label
    # "Target version", so the refusal names the legend of the device types.
    sync_api.expect(flash).to_contain_text('"Device types to upgrade"')  # The message must name a page label.
    sync_api.expect(flash).not_to_contain_text("Target version")  # The page paints no control with this label.
    sync_api.expect(flash).not_to_contain_text("version_target")  # The message must not name an internal field.
    active_text = page.evaluate("document.activeElement && document.activeElement.textContent")  # Read focused text.
    assert "Device types to upgrade" in active_text  # Focus must move to the message so the refusal is in view.
    assert _save_screenshot(page, "refused-review-focus.png").exists()  # Keep visual proof of the focused flash.


def test_a_past_start_time_names_the_multisite_control(page: Any) -> None:
    """Issue #3273: a past start time names the multi-site control and states the multi-site rule."""
    _open_org_options(page)  # Open the multi-site form with the stand-in sites.
    _set_family_state(page, True, False, False)  # Upgrade the access points alone.
    page.get_by_test_id("org-upgrade-version").fill("0.15.1")  # Type a target that the stand-in site accepts.
    page.get_by_test_id("org-strategy-big_bang").check()  # Use a strategy with no phase list.
    page.get_by_test_id("org-upgrade-start-time").fill("2020-01-01T00:00")  # Choose a moment in the past.
    page.get_by_test_id("org-upgrade-review").click()  # Submit the request through the script path.
    flash = page.get_by_test_id("flash-message")  # Find the shared flash region.
    sync_api.expect(flash).to_contain_text('"Start time (UTC)"')  # The message names the multi-site control.
    sync_api.expect(flash).not_to_contain_text("Begin the firmware download")  # The single-site label is absent.
    sync_api.expect(flash).not_to_contain_text("Write a number and a unit")  # The control holds a date and a time.
    assert _save_screenshot(page, "refused-past-start-time.png").exists()  # Keep visual proof of the refusal.
