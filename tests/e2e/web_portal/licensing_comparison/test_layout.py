"""Verify readable licensing comparisons and safe browser controls offline."""

from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import expect


class ComparisonFixture:
    """Build synthetic comparison envelopes without production credentials."""

    @staticmethod
    def outcome(data: Any, status: int = 200) -> dict[str, Any]:
        """Describe a successful read or a visible HTTP failure."""
        return {"data": data, "status_code": status, "error": None if status == 200 else "Synthetic failure"}

    @classmethod
    def row(cls, name: str = "North", failed: bool = False) -> dict[str, Any]:
        """Provide inventory and license counts for a predictable row."""
        return {
            "org_id": "org-1",
            "name": name,
            "request_status": "partial" if failed else "success",
            "license_summary": cls.outcome(
                {"summary": {"SUB-MAN": 4}, "entitled": {"SUB-MAN": 7}}, 503 if failed else 200
            ),
            "inventory": cls.outcome([{"type": "ap"}, {"type": "switch"}, {"type": "gateway"}]),
            "license_use_by_site": cls.outcome([]),
            "balances": [],
        }

    @staticmethod
    def serve(page: Any, address: str, rows: list[dict[str, Any]]) -> None:
        """Serve only synthetic browser responses through the actual page."""
        page.route(
            "**/api/license-comparison/organizations",
            lambda route: route.fulfill(
                json={
                    "organizations": [{"org_id": "org-1", "name": "North"}, {"org_id": "org-2", "name": "South"}],
                    "errors": [],
                }
            ),
        )
        page.route(
            "**/api/license-comparison",
            lambda route: route.fulfill(json={"results": rows, "discovery_errors": [], "catalog_error": None}),
        )
        page.goto(address + "/license-comparison")
        expect(page.get_by_test_id("organization-checkbox")).to_have_count(2)


def test_readable_comparison_and_responsive_source_palette(page: Any, licensing_portal_url: str) -> None:
    """Render shared navigation, numeric cells, totals, and scoped dark panels."""
    ComparisonFixture.serve(page, licensing_portal_url, [ComparisonFixture.row(), ComparisonFixture.row("South")])
    expect(page.get_by_test_id("portal-navbar")).to_be_visible()
    page.get_by_test_id("select-all-organizations").click()
    expect(page.get_by_test_id("compare-button")).to_contain_text("(2)")
    page.get_by_test_id("compare-button").click()
    expect(page.locator("#comparison-results tr")).to_have_count(2)
    expect(page.locator("#comparison-results tr").first).to_contain_text("4 / 7")
    expect(page.get_by_test_id("comparison-totals")).to_contain_text("8 / 14")
    expect(page.get_by_test_id("summary-ap")).to_have_text("2")
    expect(page.locator("th[data-license='SUB-MAN']")).to_have_attribute(
        "title", "Wireless Assurance: access point management."
    )
    assert page.locator("#comparison-results pre").count() == 0
    assert (
        page.locator(".licensing-dashboard").evaluate("(node) => getComputedStyle(node).backgroundColor")
        == "rgb(26, 26, 26)"
    )
    target = Path(__file__).resolve().parents[4] / "test-artifacts/licensing-comparison-desktop.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(target), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth") is True
    page.screenshot(path=str(target.with_name("licensing-comparison-mobile.png")), full_page=True)


def test_failed_counts_are_not_zero_and_api_markup_is_text(page: Any, licensing_portal_url: str) -> None:
    """Keep unknown counts explicit and never interpret organization markup."""
    ComparisonFixture.serve(page, licensing_portal_url, [ComparisonFixture.row("<img src=x onerror=alert(1)>", True)])
    page.get_by_test_id("select-all-organizations").click()
    page.get_by_test_id("compare-button").click()
    expect(page.locator("#comparison-results")).to_contain_text("Unavailable")
    expect(page.locator("#comparison-results")).to_contain_text("<img src=x onerror=alert(1)>")
    expect(page.get_by_test_id("comparison-totals")).to_contain_text("incomplete")
    assert page.locator("#comparison-results img").count() == 0


def test_manual_purchases_bundles_and_csv_use_the_shared_services(page: Any, licensing_portal_url: str) -> None:
    """Exercise numeric inputs through real feature routes with real CSRF."""
    page.goto(licensing_portal_url + "/license-comparison")
    page.get_by_test_id("organization-checkbox").check()
    purchase = page.locator(".purchase-input[data-row-id='org-1'] input[data-license='SUB-AI']")
    purchase.fill("4")
    purchase.press("Tab")
    page.get_by_test_id("add-manual-row").click()
    page.get_by_test_id("manual-name").fill("Manual office")
    for kind, value in (("AP", "3"), ("SWITCH", "1"), ("GATEWAY", "0")):
        page.locator(f".manual-row input[data-inventory='{kind}']").fill(value)
    page.locator(".manual-row input[data-license='SUB-MAN']").fill("2")
    page.get_by_test_id("calculate-remaining").click()
    expect(page.get_by_test_id("balance-results")).to_contain_text("SUB-AI: purchased 4, used 1, remaining 3")
    expect(page.get_by_test_id("balance-results")).to_contain_text("SUB-MAN: purchased 4, used 2, remaining 2")
    expect(page.get_by_test_id("summary-ap")).to_have_text("3")
    expect(page.get_by_test_id("summary-organizations")).to_have_text("2")
    with page.expect_download() as download:
        page.get_by_test_id("csv-export").click()
    assert download.value.suggested_filename == "mist_org_licensing_comparison.csv"
    assert "Manual office" in Path(download.value.path()).read_text(encoding="utf-8")
    page.get_by_test_id("remove-manual-row").click()
    expect(page.locator(".manual-row")).to_have_count(0)
    page.reload()
    expect(page.locator(".manual-row")).to_have_count(0)


def test_refresh_prunes_selections_and_purchases_before_comparison(page: Any, licensing_portal_url: str) -> None:
    """Never send purchases belonging to an organization removed by discovery."""
    ComparisonFixture.serve(page, licensing_portal_url, [ComparisonFixture.row("South")])
    page.get_by_test_id("select-all-organizations").click()
    purchase = page.locator(".purchase-input[data-row-id='org-1'] input[data-license='SUB-AI']")
    purchase.fill("5")
    purchase.press("Tab")
    page.unroute("**/api/license-comparison/organizations")
    page.route(
        "**/api/license-comparison/organizations",
        lambda route: route.fulfill(
            json={
                "organizations": [{"org_id": "org-2", "name": "South"}],
                "errors": [],
            }
        ),
    )
    page.get_by_test_id("refresh-organizations").click()
    expect(page.get_by_test_id("organization-checkbox")).to_have_count(1)
    expect(page.get_by_test_id("compare-button")).to_contain_text("(1)")
    with page.expect_request("**/api/license-comparison") as request:
        page.get_by_test_id("compare-button").click()
    assert request.value.post_data_json["organization_ids"] == ["org-2"]
    assert request.value.post_data_json["purchased_amounts"] == {"org-2": {}}
    assert request.value.headers["x-csrftoken"] != ""


@pytest.mark.parametrize("invalid", ["-1", "1.5"])
def test_invalid_counts_stop_before_comparison(page: Any, licensing_portal_url: str, invalid: str) -> None:
    """Reject invalid counts without sending stale values to Mist."""
    ComparisonFixture.serve(page, licensing_portal_url, [])
    page.get_by_test_id("select-all-organizations").click()
    calls: list[str] = []
    page.on(
        "request",
        lambda request: calls.append(request.url) if request.url.endswith("/api/license-comparison") else None,
    )
    field = page.locator(".purchase-input[data-row-id='org-1'] input[data-license='SUB-AI']")
    field.fill(invalid)
    field.press("Tab")
    page.get_by_test_id("compare-button").click()
    expect(page.locator("#page-status")).to_have_text("Enter non-negative whole-number counts.")
    expect(page.get_by_test_id("csv-export")).to_be_disabled()
    assert calls == []


@pytest.mark.parametrize("status", [403, 503])
def test_browser_reports_failed_discovery(page: Any, licensing_portal_url: str, status: int) -> None:
    """Show client and server failures without a success-shaped empty list."""
    page.route(
        "**/api/license-comparison/organizations",
        lambda route: route.fulfill(
            status=status,
            json={"organizations": [], "errors": [{"error": "Synthetic discovery failure"}]},
        ),
    )
    page.goto(licensing_portal_url + "/license-comparison")
    expect(page.locator("#page-status")).to_have_text("Synthetic discovery failure")
    expect(page.get_by_test_id("compare-button")).to_be_disabled()
    expect(page.get_by_test_id("refresh-organizations")).to_be_enabled()
    assert page.get_by_test_id("organization-checkbox").count() == 0


def test_csrf_and_missing_session_boundaries(licensing_client: Any) -> None:
    """Keep page and POST boundaries explicit when no session or token exists."""
    from flask_wtf.csrf import CSRFProtect

    CSRFProtect(licensing_client.application)
    denied = licensing_client.post("/api/license-comparison", json={"organization_ids": ["org-1"]})
    assert denied.status_code == 400
    licensing_client.application.config["APISESSION"] = None
    response = licensing_client.get("/license-comparison")
    assert response.status_code == 503
    assert 'data-testid="missing-session"' in response.get_data(as_text=True)


def test_three_rows_unknown_license_and_missing_inventory(page: Any, licensing_portal_url: str) -> None:
    """Count real and manual rows without disguising missing inventory as zero."""
    manual = ComparisonFixture.row("Manual")
    manual["inventory"] = ComparisonFixture.outcome({"AP": 3, "SWITCH": 1, "GATEWAY": 0})
    manual["license_summary"] = ComparisonFixture.outcome(
        {
            "summary": {"SUB_NEW": 0},
            "entitled": {"SUB_NEW": 2},
            "amendments": [{"type": "SUB-OTHER"}],
        }
    )
    unavailable = ComparisonFixture.row("Unavailable")
    unavailable["inventory"] = ComparisonFixture.outcome([], 503)
    ComparisonFixture.serve(page, licensing_portal_url, [ComparisonFixture.row(), manual, unavailable])
    page.get_by_test_id("select-all-organizations").click()
    page.get_by_test_id("compare-button").click()
    expect(page.get_by_test_id("summary-ap")).to_have_text("4 (incomplete)")
    expect(page.get_by_test_id("summary-organizations")).to_have_text("3")
    expect(page.locator("#comparison-results tr").nth(1)).to_contain_text("0 / 2")
    expect(page.locator("th[data-license='SUB-NEW']")).to_have_attribute("title", "SUB-NEW: description unavailable.")
    expect(page.locator("th[data-license='SUB-OTHER']")).to_be_visible()
    assert page.locator("#comparison-results tr").count() == 3


def test_empty_comparison_and_clear_purchases(page: Any, licensing_portal_url: str) -> None:
    """Keep empty results explicit and clear only the current purchase values."""
    ComparisonFixture.serve(page, licensing_portal_url, [])
    page.get_by_test_id("select-all-organizations").click()
    field = page.locator(".purchase-input[data-row-id='org-1'] input[data-license='SUB-AI']")
    field.fill("6")
    field.press("Tab")
    page.get_by_test_id("clear-purchases").click()
    expect(field).to_have_value("")
    page.get_by_test_id("compare-button").click()
    expect(page.locator("#comparison-results")).to_have_text("No comparison results are available.")
    expect(page.get_by_test_id("csv-export")).to_be_disabled()
    assert page.locator("#comparison-results tr").count() == 1


def test_invalid_saved_state_reports_error_without_breaking_controls(page: Any, licensing_portal_url: str) -> None:
    """Reject malformed session input and retain working organization controls."""
    page.add_init_script("sessionStorage.setItem('misthelper.licensingComparison.v1', '{\"manual\":null}')")
    page.goto(licensing_portal_url + "/license-comparison")
    expect(page.get_by_test_id("organization-checkbox")).to_have_count(1)
    expect(page.locator("#page-status")).to_contain_text("Browser session data is unavailable")
    expect(page.get_by_test_id("add-manual-row")).to_be_enabled()
    page.get_by_test_id("organization-checkbox").check()
    expect(page.get_by_test_id("compare-button")).to_be_enabled()
    assert page.locator(".manual-row").count() == 0
