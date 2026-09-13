"""Contract tests for the Data Browser file size sorting behavior."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]  # Resolve repository paths without hardcoded separators.
DATA_BROWSER_TEMPLATE = REPOSITORY_ROOT / "web_portal" / "templates" / "data_browser.html"  # Read the table source.
PORTAL_SCRIPT = REPOSITORY_ROOT / "web_portal" / "static" / "js" / "portal.js"  # Read the sorter source.


def test_data_browser_size_cell_keeps_display_text_and_exposes_bytes() -> None:
    """Require the size cell to expose bytes without changing its display text."""
    template = DATA_BROWSER_TEMPLATE.read_text(encoding="utf-8")  # Load the template sort contract.

    assert 'data-sort-value="' in template  # Require numeric metadata on the size cell.
    assert "formatFileSize(file.size_bytes)" in template  # Preserve the current human-readable display.
    assert "file.is_directory ? 0 : file.size_bytes" in template  # Sort files by true bytes and directories by zero.


def test_sortable_tables_prefer_explicit_sort_values() -> None:
    """Require sortable tables to use explicit numeric metadata when present."""
    script = PORTAL_SCRIPT.read_text(encoding="utf-8")  # Load the shared sorter contract.

    assert "getAttribute('data-sort-value')" in script  # Require explicit sort metadata when a cell provides it.
    assert "aCell.textContent.trim()" in script  # Preserve text sorting for ordinary table cells.
    assert "bCell.textContent.trim()" in script  # Preserve text sorting for the second ordinary table cell.
