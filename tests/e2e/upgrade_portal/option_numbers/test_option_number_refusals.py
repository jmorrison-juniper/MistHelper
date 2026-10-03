"""Drive malformed text through unchanged forms, routes, and flash rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import expect

from src.upgrade_portal.upgrade import options
from tests.e2e.upgrade_portal import test_upgrade
from tests.e2e.upgrade_portal.test_org_advanced_options import open_org_options, plan_access_points_and_switches

fixture_run_ledger = test_upgrade.fixture_run_ledger
options_page = test_upgrade.options_page
portal_page = test_upgrade.portal_page
run_id = test_upgrade.run_id


class BrowserRefusals:
    """Check the actual response and actual flash region of each save."""

    @staticmethod
    def refuse(page: Any, mode: str, field: str, token: str, directory: Path) -> dict[str, Any]:
        """Post an invalid form value and retain browser evidence."""
        prefix = "org-upgrade-" if mode == "multi_site" else "upgrade-"
        control = (
            "max-failures-per-phase" if mode == "multi_site" and field == "max_failures" else field.replace("_", "-")
        )
        page.get_by_test_id(prefix + control).fill(token + "s" if field == "reboot_at" else token)
        before = page.url
        button = "org-upgrade-review" if mode == "multi_site" else "upgrade-options-save-button"
        with page.expect_response(
            lambda answer: answer.request.method == "POST" and answer.url.endswith("/options")
        ) as saved:
            page.get_by_test_id(button).click()
        answer = saved.value
        assert answer.status == 400
        response = answer.json()
        labels = options.ORG_OPTION_HELP if mode == "multi_site" else options.OPTION_HELP
        assert labels[field][0] in str(response)
        assert token not in str(response)
        flash = page.get_by_test_id("flash-message")
        expect(flash).to_contain_text(labels[field][0])
        expect(flash).not_to_contain_text(token)
        expect(flash).not_to_contain_text("sys.set_int_max_str_digits")
        expect(flash).not_to_contain_text("invalid literal")
        assert page.url == before
        page.screenshot(path=str(directory / f"{mode}-{field}-refusal.png"), full_page=True)
        return {"status": answer.status, "response": response, "url": page.url, "before": before}


@pytest.mark.parametrize("field", ("canary_phases", "max_failures", "reboot_at"))
@pytest.mark.parametrize(
    "token", ("5²", "7" * 5000, "５", "٧"), ids=("superscript", "5000-digits", "fullwidth", "arabic")
)
def test_single_site_native_form_refuses(options_page: Any, field: str, token: str, tmp_path: Path) -> None:
    """The single-site operator reads a named refusal and stays on the options form."""
    options_page.get_by_test_id("upgrade-strategy-canary").check()
    options_page.get_by_test_id("upgrade-canary-phases").fill("100")
    proof = BrowserRefusals.refuse(options_page, "single_site", field, token, tmp_path)
    assert proof["status"] == 400
    assert options.OPTION_HELP[field][0] in str(proof["response"])
    assert proof["url"] == proof["before"]


@pytest.mark.parametrize("field", ("canary_phases", "max_failures", "reboot_at"))
@pytest.mark.parametrize(
    "token", ("5²", "7" * 5000, "５", "٧"), ids=("superscript", "5000-digits", "fullwidth", "arabic")
)
def test_multi_site_native_form_refuses(page: Any, field: str, token: str, tmp_path: Path) -> None:
    """The multi-site operator reads its own label without a stored plan."""
    open_org_options(page)
    plan_access_points_and_switches(page)
    page.get_by_test_id("org-upgrade-canary-phases").fill("100")
    proof = BrowserRefusals.refuse(page, "multi_site", field, token, tmp_path)
    assert proof["status"] == 400
    assert options.ORG_OPTION_HELP[field][0] in str(proof["response"])
    assert proof["url"] == proof["before"]
