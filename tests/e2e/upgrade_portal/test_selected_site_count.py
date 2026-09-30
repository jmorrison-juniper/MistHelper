"""Browser journey of issues #3447 and #3452: the site scope of the multi-site pages.

Why:
    Issue #3447. The note of the multi-site options page printed the count of
    the selected sites and the fixed word "sites". A plan of one site then
    read "One operation targets 1 selected sites." Issue #3452. The confirm
    page of a plan of one site stated a plural scope in its Warning and in
    its two pre-check buttons. This journey drives a real browser through the
    real site picker. It reads the note and the confirm page for one site and
    for two sites, and a screenshot records each page for a visual review. The
    stand-in cloud of the browser fixtures answers every read, so the journey
    sends no firmware request.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"  # The mode chooser, where each journey starts.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site, which holds one device of each type.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site.
TARGET_VERSION = "0.15.1"  # The newer version that the stand-in cloud offers for every model.
DEVICE_TYPES = ("ap", "switch", "gateway")  # The three device types of the multi-site form.
VERSION_FIELD_IDS = ("org-upgrade-version", "org-upgrade-switch-version", "org-upgrade-gateway-version")
NOTE_ID = "org-upgrade-site-count"  # The test identifier of the note.
SECOND_SENTENCE = "The portal selects the safe route for each device family."  # The second sentence stays.
ONE_SITE_NOTE = f"One operation targets 1 selected site. {SECOND_SENTENCE}"  # The singular noun.
TWO_SITES_NOTE = f"One operation targets 2 selected sites. {SECOND_SENTENCE}"  # The plural noun.
SCOPE_IDS = ("org-upgrade-scope-warning", "org-upgrade-precheck-all", "org-upgrade-precheck-missing")
CANCEL_SENTENCE = "Cancellation does not restore upgraded devices."  # The second sentence of the Warning stays.
ONE_SITE_SCOPE = (  # Issue #3452: the Warning and the two pre-check buttons of a plan of one site.
    f"Warning: the upgrade can interrupt network service at the selected site. {CANCEL_SENTENCE}",
    "Take a new pre-check for the site",
    "Take the missing pre-check",
)
TWO_SITES_SCOPE = (  # Issue #3452: the same three texts of a plan of two sites.
    f"Warning: the upgrade can interrupt network service at each selected site. {CANCEL_SENTENCE}",
    "Take a new pre-check for each site",
    "Take the missing pre-checks",
)
SCREENSHOT_DIRECTORY = (  # The evidence folder of this journey.
    Path(__file__).parents[3] / "test-artifacts" / "upgrade-portal-journeys" / "selected-site-count"
)


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


def open_the_options(page: Any, first: bool, second: bool) -> None:
    """Choose the multi-site mode, set the two site boxes, and open the options page.

    Args:
        page: The browser page.
        first: The state of the box of the first stand-in site.
        second: The state of the box of the second stand-in site.
    """
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode chooser with a signed session.
    page.get_by_test_id("mode-multi-site").check()  # Choose the multi-site mode.
    page.get_by_test_id("mode-continue").click()  # Move to the site picker.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.
    page.get_by_test_id(f"site-select-{SITE_ID}").set_checked(first)  # An earlier journey can leave a box checked.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").set_checked(second)  # Set each box explicitly.
    page.get_by_test_id("multi-site-continue").click()  # Store the site set.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait until the form script is ready.


def fill_the_plan(page: Any) -> None:
    """Check each device type, and type one version for each type.

    Args:
        page: The browser page.
    """
    for device_type in DEVICE_TYPES:  # A checked type shows its version field.
        page.get_by_test_id(f"org-upgrade-type-{device_type}").check()  # A checked box stays checked.
    for field_id in VERSION_FIELD_IDS:  # The first site holds one device of each type.
        page.get_by_test_id(field_id).fill(TARGET_VERSION)  # The newer version of every stand-in model.


def open_the_confirm_page(page: Any, site_count: int) -> None:
    """Type the plan, save it, and wait for the confirm page of the stated site count.

    Args:
        page: The browser page.
        site_count: The count of the selected sites.
    """
    fill_the_plan(page)  # Type the plan of the operator.
    page.get_by_test_id("org-upgrade-review").click()  # Save the plan.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # The save accepted the plan.
    confirm = page.get_by_test_id("org-upgrade-confirm")  # The summary card of the confirm page.
    sync_api.expect(confirm).to_contain_text(f"Sites: {site_count}")  # The confirm page states the same count.


def expect_the_scope(page: Any, texts: tuple[str, ...]) -> None:
    """Compare the whole Warning and the whole text of each pre-check button.

    Args:
        page: The browser page.
        texts: The Warning, the text of the full pre-check button, and the text of the missing button.
    """
    for test_id, text in zip(SCOPE_IDS, texts, strict=True):  # One whole-text compare for each element.
        sync_api.expect(page.get_by_test_id(test_id)).to_have_text(text)  # A browser reads the rendered text.


def test_one_selected_site_reads_as_one_site_and_reaches_the_confirm_page(page: Any) -> None:
    """The note and the confirm page of a one-site plan name one site."""
    open_the_options(page, first=True, second=False)  # The operator selects one site only.
    note = page.get_by_test_id(NOTE_ID)  # The note above the device table.
    sync_api.expect(note).to_have_text(ONE_SITE_NOTE)  # The whole note, with the singular noun.
    assert save_screenshot(page, "one-selected-site.png").exists()  # The note of one site.
    open_the_confirm_page(page, site_count=1)  # Save the one-site plan.
    expect_the_scope(page, ONE_SITE_SCOPE)  # Issue #3452: each scope text names one site.
    assert save_screenshot(page, "one-selected-site-confirm.png").exists()  # The summary before the typed word.


def test_two_selected_sites_read_as_sites(page: Any) -> None:
    """The note and the confirm page of a two-site plan keep a plural scope."""
    open_the_options(page, first=True, second=True)  # The operator selects both sites.
    note = page.get_by_test_id(NOTE_ID)  # The note above the device table.
    sync_api.expect(note).to_have_text(TWO_SITES_NOTE)  # The whole note, with the plural noun.
    assert save_screenshot(page, "two-selected-sites.png").exists()  # The note of two sites.
    open_the_confirm_page(page, site_count=2)  # Save the two-site plan.
    expect_the_scope(page, TWO_SITES_SCOPE)  # Issue #3452: each scope text keeps the plural scope.
    assert save_screenshot(page, "two-selected-sites-confirm.png").exists()  # The summary of two sites.
