"""Browser contract for visible upgrade option number refusals."""

from __future__ import annotations

import re
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"
SITE_IDS = ("22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333")


def _open_org_options(page: Any) -> None:
    """Open the seeded multi-site options form."""
    page.goto(MODE_PATH, wait_until="domcontentloaded")
    page.get_by_test_id("mode-multi-site").check()
    page.get_by_test_id("mode-continue").click()
    page.wait_for_url(re.compile(r".*/select/site$"))
    for site_id in SITE_IDS:
        page.get_by_test_id(f"site-select-{site_id}").check()
    page.get_by_test_id("multi-site-continue").click()
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))


@pytest.mark.parametrize("value", ["²", "9" * 5000])
def test_number_refusal_keeps_python_policy_text_out_of_the_page(page: Any, value: str) -> None:
    """The multi-site page shows a named refusal without Python conversion text."""
    _open_org_options(page)
    page.get_by_test_id("org-strategy-canary").check()
    page.get_by_test_id("org-upgrade-canary-phases").fill(value)
    page.get_by_test_id("org-upgrade-review").click()
    flash = page.get_by_test_id("flash-message")
    sync_api.expect(flash).to_contain_text("Canary phases")
    sync_api.expect(flash).not_to_contain_text("invalid literal")
    assert flash.count() == 1  # Confirm that the refusal creates one visible message after the browser waits complete.
