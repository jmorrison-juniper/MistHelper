"""Browser tests for Recent Files sorting on the dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

PORTAL_SCRIPT = Path(__file__).parents[2] / "web_portal" / "static" / "js" / "portal.js"


def _dashboard_html(client, data_dir: Path) -> str:
    """Return dashboard HTML with files that expose every sort path."""
    first = data_dir / "small.txt"
    second = data_dir / "large.txt"
    first.write_bytes(b"1")
    second.write_bytes(b"x" * 2048)
    first.touch()
    second.touch()
    client.application.config["DATA_DIR"] = str(data_dir)
    response = client.get("/")
    assert response.status_code == 200
    return response.data.decode()


def _load_sortable_dashboard(page: Any, html: str) -> None:
    """Load the dashboard and attach the production sorter to its table."""
    page.set_content(html)
    page.add_script_tag(content=PORTAL_SCRIPT.read_text(encoding="utf-8"))
    page.evaluate("makeSortable(document.querySelector('[data-testid=\"recent-files-table\"]'))")


def _file_names(page: Any) -> list[str]:
    """Read the visible Recent Files names in their current order."""
    return page.locator('[data-testid="recent-files-table"] tbody tr td:first-child').all_text_contents()


def test_recent_files_headers_sort_ascending_and_descending(client, tmp_path, page: Any):
    """A size header click sorts rows in both directions."""
    html = _dashboard_html(client, tmp_path)
    _load_sortable_dashboard(page, html)
    size_header = page.locator('[data-testid="recent-files-table"] th').nth(1)

    size_header.click()
    assert _file_names(page) == ["small.txt", "large.txt"]
    assert size_header.get_attribute("aria-sort") == "ascending"

    size_header.click()
    assert _file_names(page) == ["large.txt", "small.txt"]
    assert size_header.get_attribute("aria-sort") == "descending"


def test_recent_files_name_header_updates_sort_state(client, tmp_path, page: Any):
    """A name header click sorts text and clears the other header state."""
    html = _dashboard_html(client, tmp_path)
    _load_sortable_dashboard(page, html)
    headers = page.locator('[data-testid="recent-files-table"] th')

    headers.nth(0).click()
    assert _file_names(page) == ["large.txt", "small.txt"]
    assert headers.nth(0).get_attribute("aria-sort") == "ascending"
    assert headers.nth(1).get_attribute("aria-sort") == "none"
