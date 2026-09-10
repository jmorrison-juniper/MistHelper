"""Browser tests for Operations category counts after search filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

OPERATIONS_SCRIPT = Path(__file__).parents[2] / "web_portal" / "static" / "js" / "operations.js"


def _open_operations_filter(page) -> None:
    """Build the operation list and activate the production search handler."""
    page.set_content("""
        <input id="opSearch" type="text">
        <div class="accordion-item">
            <button type="button">
                Safe (<span class="op-count" data-testid="operation-count-cat0">2</span>)
            </button>
            <ul>
                <li class="op-item">1 Export sites</li>
                <li class="op-item">2 Export devices</li>
            </ul>
        </div>
        <div class="accordion-item">
            <button type="button">
                Interactive (<span class="op-count" data-testid="operation-count-cat1">1</span>)
            </button>
            <ul>
                <li class="op-item">3 Upgrade device</li>
            </ul>
        </div>
        """)
    page.add_script_tag(path=str(OPERATIONS_SCRIPT))
    page.evaluate("setupSearch()")


def _category_count(page, category_id: str) -> str:
    """Read one rendered category count by its stable test identifier."""
    return page.locator(f'[data-testid="operation-count-{category_id}"]').inner_text()


def test_filter_updates_each_category_count(page) -> None:
    """A search updates counts to the number of visible operation rows."""
    _open_operations_filter(page)

    page.locator("#opSearch").fill("device")

    assert _category_count(page, "cat0") == "1"
    assert _category_count(page, "cat1") == "1"


def test_filter_restores_counts_and_shows_zero(page) -> None:
    """Clearing a search restores totals, while an unmatched search shows zero."""
    _open_operations_filter(page)

    page.locator("#opSearch").fill("missing")
    assert _category_count(page, "cat0") == "0"
    assert _category_count(page, "cat1") == "0"

    page.locator("#opSearch").fill("")
    assert _category_count(page, "cat0") == "2"
    assert _category_count(page, "cat1") == "1"
