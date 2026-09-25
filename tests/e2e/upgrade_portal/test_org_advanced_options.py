"""Browser journeys for the advanced upgrade controls of the multi-site options page.

Why:
    Issue #3383. The single-site options page offers eleven advanced controls
    that the multi-site page did not offer. These journeys drive a real browser
    through the multi-site form. Each journey sets the visible controls, reads
    the body that the browser posts, reads the typed confirmation page, and
    goes Back. A screenshot records each page for a visual review. The stand-in
    cloud of the browser fixtures answers every read, so no journey sends a
    firmware request.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"  # The mode chooser, where each multi-site journey starts.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site.
TARGET_VERSION = "0.15.1"  # The newer version that the stand-in cloud offers for every model.
OPTIONS_SAVE_PATH = "/api/org-upgrades/options"  # The save route of the multi-site options.
SCREENSHOT_DIRECTORY = (  # The evidence folder of these journeys.
    Path(__file__).parents[3] / "data" / "test-artifacts" / "upgrade-portal-journeys" / "org-advanced-options"
)
RADIO_FIELD_IDS = (  # The five radio batch controls, which only a radio plan with access points reads.
    "org-upgrade-rrm-first-batch-percentage-field",
    "org-upgrade-rrm-max-batch-percentage-field",
    "org-upgrade-rrm-node-order-field",
    "org-upgrade-rrm-mesh-upgrade-field",
    "org-upgrade-rrm-slow-ramp-field",
)
PEER_SIZE_IDS = ("org-upgrade-p2p-cluster-size-field", "org-upgrade-p2p-parallelism-field")  # The two peer sizes.


def save_screenshot(page: Any, name: str) -> Path:
    """Save one journey screenshot.

    Args:
        page: The browser page.
        name: The file name of the screenshot.

    Returns:
        The path of the saved file.
    """
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep the evidence under the repository data tree.
    path = SCREENSHOT_DIRECTORY / name  # One stable file name for each page state.
    page.screenshot(path=str(path), full_page=True)  # Capture the full page for the visual review.
    return path  # The caller proves that the file exists.


def open_org_options(page: Any) -> None:
    """Open the multi-site options page with two selected sites.

    Args:
        page: The browser page.
    """
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode chooser with a signed session.
    page.get_by_test_id("mode-multi-site").check()  # Choose the multi-site mode.
    page.get_by_test_id("mode-continue").click()  # Move to the site picker.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select the first stand-in site.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # Select the second stand-in site.
    page.get_by_test_id("multi-site-continue").click()  # Open the shared options form.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait until the form script is ready.


def plan_access_points_and_switches(page: Any) -> None:
    """Choose a plan of the access points and the switches, with a typed version for each type.

    Args:
        page: The browser page.
    """
    page.get_by_test_id("org-upgrade-type-gateway").uncheck()  # The journeys plan two device types.
    page.get_by_test_id("org-upgrade-version").fill(TARGET_VERSION)  # The access point target version.
    page.get_by_test_id("org-upgrade-switch-version").fill(TARGET_VERSION)  # The switch target version.


def expect_shown(page: Any, test_id: str, shown: bool) -> None:
    """Assert that one control shows and posts, or hides and posts nothing.

    Args:
        page: The browser page.
        test_id: The test identifier of the control group.
        shown: True when the plan reads the control.
    """
    group = page.get_by_test_id(test_id)  # Find the control group by its stable identifier.
    if shown:  # The operator must see a control that the plan reads.
        sync_api.expect(group).to_be_visible()
    else:  # The operator must not see a control that the plan ignores.
        sync_api.expect(group).to_be_hidden()
    enabled = group.locator("input:not(:disabled), select:not(:disabled)").count()  # Controls that post a value.
    assert (enabled > 0) is shown, f"{test_id} has {enabled} enabled control(s)."  # A hidden control posts nothing.


def is_options_save(request: Any) -> bool:
    """Return true for the save request of the multi-site options.

    Args:
        request: One browser request.

    Returns:
        True when the request posts the multi-site options.
    """
    return request.method == "POST" and request.url.endswith(OPTIONS_SAVE_PATH)  # The one save of the form.


def review(page: Any) -> dict[str, Any]:
    """Click Review, return the posted body, and wait for the confirm page.

    Args:
        page: The browser page.

    Returns:
        The JSON body that the browser posted.
    """
    with page.expect_request(is_options_save) as sent:  # Record the body that the form script sends.
        page.get_by_test_id("org-upgrade-review").click()  # Save the options.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # The save accepted the plan.
    body = sent.value.post_data_json  # The exact body of the save.
    assert isinstance(body, dict), "The form posted no JSON object."  # The route reads a JSON object.
    return body  # The caller checks each field.


def summary_text(page: Any, field: str) -> str:
    """Return the text of one line of the advanced summary on the confirm page.

    Args:
        page: The browser page.
        field: The field part of the line identifier.

    Returns:
        The text of the line.
    """
    line = page.get_by_test_id(f"org-upgrade-summary-{field}")  # One line of the summary list.
    sync_api.expect(line).to_be_visible()  # The operator reads the line before the typed confirmation.
    return str(line.inner_text())  # The painted text.


def test_the_canary_and_peer_controls_reach_the_confirm_page_and_come_back(page: Any) -> None:
    """A canary plan with a peer download posts each value, lists it, and keeps it after Back."""
    open_org_options(page)  # Open the multi-site form.
    plan_access_points_and_switches(page)  # Plan the access points and the switches.
    expect_shown(page, "org-upgrade-max-failures-per-phase-field", True)  # A canary plan reads the counts.
    for test_id in (*PEER_SIZE_IDS, *RADIO_FIELD_IDS):  # The peer download is off, and the plan is canary.
        expect_shown(page, test_id, False)
    page.get_by_test_id("org-upgrade-max-failures-per-phase").fill("0,1,2,3")  # One count for each phase.
    page.get_by_test_id("org-upgrade-enable-p2p-yes").check()  # Turn on the peer download.
    for test_id in PEER_SIZE_IDS:  # The two sizes show with the peer download.
        expect_shown(page, test_id, True)
    page.get_by_test_id("org-upgrade-p2p-cluster-size").fill("20")  # The size of one download group.
    page.get_by_test_id("org-upgrade-p2p-parallelism").fill("4")  # The count of groups that run together.
    assert save_screenshot(page, "canary-peer-options.png").exists()  # The filled form.
    body = review(page)  # Save the plan.
    assert (body["max_failures"], body["enable_p2p"], body["stable_version"]) == ("0,1,2,3", "yes", "no")
    assert (body["p2p_cluster_size"], body["p2p_parallelism"]) == ("20", "4")  # The two sizes reach the save.
    assert not [name for name in body if name.startswith("rrm_")]  # A hidden radio control posts nothing.
    assert "0,1,2,3" in summary_text(page, "max-failures")  # The confirm page lists the counts.
    assert "neighbor" in summary_text(page, "enable-p2p")  # The confirm page lists the peer download.
    assert "20" in summary_text(page, "p2p-cluster-size")  # The confirm page lists the group size.
    assert save_screenshot(page, "canary-peer-confirm.png").exists()  # The summary before the typed word.
    page.get_by_role("link", name="Back").click()  # Return to the options page.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait for the restored form.
    sync_api.expect(page.get_by_test_id("org-upgrade-max-failures-per-phase")).to_have_value("0,1,2,3")
    sync_api.expect(page.get_by_test_id("org-upgrade-enable-p2p-yes")).to_be_checked()  # The choice stays.
    sync_api.expect(page.get_by_test_id("org-upgrade-p2p-parallelism")).to_have_value("4")  # The size stays.
    assert save_screenshot(page, "canary-peer-back.png").exists()  # The restored form.


def test_the_radio_controls_reach_the_confirm_page(page: Any) -> None:
    """A radio plan shows the five radio controls, posts each value, and names each choice."""
    open_org_options(page)  # Open the multi-site form.
    plan_access_points_and_switches(page)  # Plan the access points and the switches.
    page.get_by_test_id("org-strategy-rrm").check()  # Choose the radio strategy.
    expect_shown(page, "org-upgrade-max-failures-per-phase-field", False)  # A radio plan reads no counts.
    for test_id in RADIO_FIELD_IDS:  # Each radio control shows for a radio plan with access points.
        expect_shown(page, test_id, True)
    page.get_by_test_id("org-upgrade-rrm-first-batch-percentage").fill("10")  # The first batch share.
    page.get_by_test_id("org-upgrade-rrm-max-batch-percentage").fill("30")  # The largest later share.
    page.get_by_test_id("org-upgrade-rrm-node-order").select_option("fringe_to_center")  # Start at the edge.
    page.get_by_test_id("org-upgrade-rrm-mesh-upgrade").select_option("sequential")  # One mesh unit at a time.
    page.get_by_test_id("org-upgrade-rrm-slow-ramp").select_option("no")  # The usual growth rate.
    assert save_screenshot(page, "radio-options.png").exists()  # The filled form.
    body = review(page)  # Save the plan.
    assert body["rrm_node_order"] == "fringe_to_center"  # The order reaches the save.
    assert (body["rrm_first_batch_percentage"], body["rrm_max_batch_percentage"]) == ("10", "30")  # The shares.
    assert "max_failures" not in body  # A hidden count control posts nothing.
    assert "Start at the edge of each site" in summary_text(page, "rrm-node-order")  # The order in words.
    assert "One mesh access point at a time" in summary_text(page, "rrm-mesh-upgrade")  # The mesh order.
    assert "Grow each batch at the usual rate" in summary_text(page, "rrm-slow-ramp")  # The growth rate.
    assert save_screenshot(page, "radio-confirm.png").exists()  # The summary before the typed word.


def test_each_advanced_control_follows_the_device_types(page: Any) -> None:
    """Each advanced control shows only for a device type that reads it."""
    open_org_options(page)  # Open the multi-site form with every device type checked.
    page.get_by_test_id("org-strategy-rrm").check()  # A radio plan, so the radio controls can show.
    expect_shown(page, "org-upgrade-p2p-group", True)  # The access points read the peer download.
    expect_shown(page, "org-upgrade-stable-version-group", True)  # The switches and the gateways read it.
    page.get_by_test_id("org-upgrade-type-ap").uncheck()  # Take the access points out of the plan.
    for test_id in ("org-upgrade-p2p-group", *RADIO_FIELD_IDS):  # Only an access point reads these controls.
        expect_shown(page, test_id, False)
    page.get_by_test_id("org-upgrade-type-ap").check()  # Put the access points back.
    page.get_by_test_id("org-upgrade-type-switch").uncheck()  # Take the switches out of the plan.
    page.get_by_test_id("org-upgrade-type-gateway").uncheck()  # Take the gateways out of the plan.
    expect_shown(page, "org-upgrade-stable-version-group", False)  # No family that reads the stable build.
    expect_shown(page, "org-upgrade-p2p-group", True)  # The access points still read the peer download.
    sync_api.expect(page.get_by_test_id("org-upgrade-ssr-channel")).to_have_count(0)  # No router at a site.
    assert save_screenshot(page, "device-type-rules.png").exists()  # The form of an access point plan.


def test_the_stable_build_with_an_access_point_names_the_control(page: Any) -> None:
    """The save refuses the stable build for a plan with an access point, and names the control."""
    open_org_options(page)  # Open the multi-site form.
    plan_access_points_and_switches(page)  # Plan the access points and the switches.
    page.get_by_test_id("org-upgrade-stable-version-yes").check()  # Choose the vendor stable build.
    page.get_by_test_id("org-upgrade-review").click()  # Try to save the plan.
    flash = page.get_by_test_id("flash-message")  # The shared message region of the layout.
    sync_api.expect(flash).to_contain_text('"Firmware version of each switch and each gateway"')  # The label.
    sync_api.expect(flash).not_to_contain_text("stable_version")  # The message names no internal field.
    assert re.search(r".*/upgrade/org/options$", page.url)  # The page stays on the form, so no plan exists.
    assert save_screenshot(page, "stable-refusal.png").exists()  # The refusal on the form.
