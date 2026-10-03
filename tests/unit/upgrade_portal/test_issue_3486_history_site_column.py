"""Unit tests of issue #3486: the Captures table of the history with no site names the site of each row.

Why:
    The history page with no site lists the stored captures of every site in
    one table. No column named the site of a row. In the browser fixtures, the
    table listed 5 captures from 2 sites, and no cell showed the difference. An
    operator could then open a capture of the wrong site before an upgrade
    decision. These tests read the column class, the site text of each row,
    the rendered table, and the width rules of the stylesheet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import review
from src.upgrade_portal.compare import render

_ASSET_ROOT = Path(review.__file__).resolve().parents[1] / "assets"  # The real asset folder of the portal.
_TEMPLATE_ROOT = _ASSET_ROOT / "templates"  # The real template folder.
_STYLESHEET = _ASSET_ROOT / "static" / "css" / "portal.css"  # The real stylesheet of the portal.
_HISTORY_TEMPLATE = "review/history.html"  # The capture history.
_SITE_A = ("site-a", "Site A")  # The identifier and the name of the first site.
_SITE_B = ("site-b", "Site B")  # The identifier and the name of the second site.
_EVERY_SITE_ROW_VALUES = (  # FR-005: the row values of the table with the Site column.
    "Each row holds the site, the moment, the role, the state, the device count, the device types, "
    "the client count, and the stored size."
)
_ONE_SITE_ROW_VALUES = (  # FR-006: the row values of the table of one site, which do not change.
    "Each row holds the moment, the role, the state, the device count, the device types, the client count, "
    "and the stored size."
)
_EVERY_SITE_HEADERS = [  # FR-001: the Site column follows the Capture column.
    "Capture",
    "Site",
    "Started",
    "Role",
    "State",
    "Devices",
    "Device types",
    "Clients",
    "Stored size",
    "Action",
]
_ONE_SITE_HEADERS = [header for header in _EVERY_SITE_HEADERS if header != "Site"]  # The nine columns of today.
_SITE_WIDTHS = (8, 10, 10, 7, 8, 8, 24, 7, 9, 9)  # Issues #3491 and #3495: the ten readable shares.


@dataclass(frozen=True, slots=True)
class _StorePage:
    """A stand-in for the page record of the capture store.

    Attributes:
        captures: The capture records of this page.
        total: The number of captures that the list holds.
        limit: The number of rows that one page holds.
        offset: The number of rows that the earlier pages hold.
    """

    captures: tuple[dict[str, Any], ...] = ()
    total: int = 0
    limit: int = render.DEFAULT_HISTORY_PAGE_SIZE
    offset: int = 0


def _store_row(capture_id: str, site_id: str = "", site_name: str = "") -> dict[str, Any]:
    """Return one stored capture record, as the list projection of the store returns it.

    Args:
        capture_id: The identifier of the capture.
        site_id: The site identifier that the record holds, or an empty text.
        site_name: The site name that the record holds, or an empty text.

    Returns:
        The stored record.
    """
    record: dict[str, Any] = {"capture_id": capture_id, "role": "pre", "capture_status": "verified"}  # The base.
    record.update({key: value for key, value in (("site_id", site_id), ("site_name", site_name)) if value})
    return record  # A record with no site value holds no site field, as an old record does.


def _page_view(*stored: dict[str, Any]) -> review.HistoryPageView:
    """Build the history view that the route builds for these stored records.

    Args:
        *stored: The stored records of this page, in list order.

    Returns:
        The view that the page prints.
    """
    shaped = [review.history_row(record) for record in stored]  # The route shapes each stored row first.
    compare_view = render.build_history_view(_StorePage(tuple(shaped), total=len(shaped)))  # The compare view.
    return review.build_page_view(compare_view, shaped)  # The route joins the compare rows and the stored rows.


def _two_site_view() -> review.HistoryPageView:
    """Return the view of three captures: two of Site A and one of Site B."""
    return _page_view(
        _store_row("cap-0", *_SITE_A),  # The first capture of Site A.
        _store_row("cap-1", *_SITE_B),  # The one capture of Site B.
        _store_row("cap-2", *_SITE_A),  # The second capture of Site A.
    )


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset, because this render has no Flask.

    Args:
        endpoint: The endpoint name.
        **values: The endpoint arguments. Holds ``filename``.

    Returns:
        A path that stands in for the real asset path.
    """
    return f"/{endpoint}/{values.get('filename', '')}"  # The page only needs a string.


@pytest.fixture(scope="module")
def environment() -> Environment:
    """Return a Jinja environment that loads the real portal templates.

    Returns:
        The environment, with the strict undefined type.
    """
    built = Environment(loader=FileSystemLoader(str(_TEMPLATE_ROOT)), autoescape=True, undefined=StrictUndefined)
    built.globals["url_for"] = _static_url  # Flask supplies this name, and this render has no Flask.
    built.globals["request"] = None  # The navigation partial reads this name.
    return built


def _render(environment: Environment, **values: Any) -> str:
    """Render the real history template with the values that a route supplies.

    Args:
        environment: The Jinja environment.
        **values: The template values, such as the view, the scope, and the columns.

    Returns:
        The rendered page.
    """
    return environment.get_template(_HISTORY_TEMPLATE).render(**values)  # The same template that the portal serves.


def _render_every_site(environment: Environment, view: review.HistoryPageView) -> str:
    """Render the page with no site, with the values that the route gives.

    Args:
        environment: The Jinja environment.
        view: The history view of the page.

    Returns:
        The rendered page.
    """
    scope = review.HistoryScope.for_page("", [])  # The scope of every site reads no row.
    columns = review.HistoryCaptureColumns(site_id="")  # The columns of every site.
    return _render(environment, history_view=view, history_scope=scope, history_columns=columns)


def _capture_table(page: str) -> str:
    """Return the markup of the Captures table.

    Args:
        page: The rendered page.

    Returns:
        The markup from the table tag to its end tag.
    """
    found = re.search(r'<table[^>]*data-testid="history-table".*?</table>', page, re.DOTALL)  # One table.
    assert found, "The page holds no Captures table."  # The contract fixes this test identifier.
    return found.group(0)


def _fold(text: str) -> str:
    """Return the text with one space between each word.

    Args:
        text: A piece of markup.

    Returns:
        The same text with single spaces and no space at either end.
    """
    return " ".join(text.split())  # The template wraps long lines.


def _headers(page: str) -> list[str]:
    """Return the text of each column header of the Captures table.

    Args:
        page: The rendered page.

    Returns:
        The header texts, in column order.
    """
    head = re.search(r"<thead>(.*?)</thead>", _capture_table(page), re.DOTALL)  # The one header row.
    assert head, "The Captures table holds no header row."  # A screen reader needs the headers.
    return [_fold(cell) for cell in re.findall(r"<th\b[^>]*>(.*?)</th>", head.group(1), re.DOTALL)]


def _row_cells(page: str) -> list[list[str]]:
    """Return the opening tag of each cell of each capture row.

    Args:
        page: The rendered page.

    Returns:
        One list of opening tags for each row, in column order.
    """
    body = re.search(r"<tbody>(.*?)</tbody>", _capture_table(page), re.DOTALL)  # The rows of the table.
    assert body, "The Captures table holds no body."  # The template always prints a body.
    rows = re.findall(r'<tr data-testid="history-row-[^"]*">(.*?)</tr>', body.group(1), re.DOTALL)  # Capture rows.
    return [re.findall(r"<t[hd]\b[^>]*>", row) for row in rows]  # The opening tag of each cell.


def _site_cells(page: str) -> list[tuple[str, str, str]]:
    """Return the title, the test identifier, and the text of each site cell.

    Args:
        page: The rendered page.

    Returns:
        One entry for each site cell, in row order.
    """
    pattern = r'<td class="cell-site" title="([^"]*)" data-testid="([^"]*)">(.*?)</td>'  # FR-003 and FR-004.
    return [(title, test_id, _fold(text)) for title, test_id, text in re.findall(pattern, page, re.DOTALL)]


def _table_class(page: str) -> str:
    """Return the class list of the Captures table.

    Args:
        page: The rendered page.

    Returns:
        The class attribute text.
    """
    found = re.search(r'<table class="([^"]*)"[^>]*data-testid="history-table"', page)  # The table tag.
    assert found, "The Captures table holds no class list."  # The layout rules read this list.
    return found.group(1)


def _caption(page: str) -> str:
    """Return the whole text of the hidden caption of the Captures table.

    Args:
        page: The rendered page.

    Returns:
        The caption text, with one space between each word.
    """
    found = re.search(r"<caption[^>]*>(.*?)</caption>", _capture_table(page), re.DOTALL)  # The first child.
    assert found, "The Captures table holds no caption."  # A screen reader reads this caption.
    return _fold(found.group(1))


def _empty_span(page: str) -> str:
    """Return the column span of the empty row of the Captures table.

    Args:
        page: The rendered page.

    Returns:
        The value of the colspan attribute.
    """
    found = re.search(r'<td colspan="([^"]*)" class="portal-table-empty">', page)  # The one empty row.
    assert found, "The empty Captures table holds no empty row."  # The row tells the operator what to do.
    return found.group(1)


def _rule_body(selector: str) -> str:
    """Return the declarations of one stylesheet rule.

    Args:
        selector: The exact selector text, with no brace.

    Returns:
        The declarations between the braces, or an empty text.
    """
    found = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", _STYLESHEET.read_text(encoding="utf-8"))  # One rule.
    return found.group(1) if found else ""  # An absent rule reads as no declaration.


# ---------------------------------------------------------------------------
# The column class
# ---------------------------------------------------------------------------


def test_the_columns_of_the_page_with_no_site_show_the_site() -> None:
    """FR-001, FR-005, FR-008, and FR-009: the route decides the Site column of every site."""
    columns = review.HistoryCaptureColumns(site_id="")  # The page with no site.
    values = (columns.shows_site_column, columns.column_count, columns.row_values_text)  # The three values.
    assert values == (True, 10, _EVERY_SITE_ROW_VALUES)  # Ten columns, and the caption names the site.


def test_the_columns_of_the_page_of_one_site_do_not_change() -> None:
    """FR-006 and SC-002: the page of one site keeps the nine columns and the caption of today."""
    columns = review.HistoryCaptureColumns(site_id=_SITE_A[0])  # The page of one site.
    values = (columns.shows_site_column, columns.column_count, columns.row_values_text)  # The three values.
    assert values == (False, 9, _ONE_SITE_ROW_VALUES)  # A Site column would repeat one name in each row.


def test_the_columns_hold_one_field_and_each_value_is_a_property() -> None:
    """FR-008: the class holds the request value, and each column value is a property and not a field."""
    assert [field.name for field in fields(review.HistoryCaptureColumns)] == ["site_id"]  # One field only.


# ---------------------------------------------------------------------------
# The site text of each row
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        ({"site_id": "site-a", "site_name": "Site A"}, "Site A"),  # The name wins.
        ({"site_id": "site-a"}, "site-a"),  # An old record holds the identifier alone.
        ({"site_id": "site-a", "site_name": ""}, "site-a"),  # An empty name reads as no name.
        ({}, ""),  # A record with no site value gives an empty cell.
    ],
)
def test_the_site_label_prefers_the_name_then_the_identifier(record: dict[str, Any], expected: str) -> None:
    """FR-002: one rule gives the site text of a run row and of a capture row."""
    assert review.record_site_label(record) == expected  # The Runs table follows the same rule.


def test_each_page_row_names_its_site_and_its_test_identifier() -> None:
    """FR-002 and FR-004: each row carries the site text and the site test identifier."""
    pairs = [(row["site_text"], row["site_test_id"]) for row in _two_site_view().rows]  # The two new fields.
    assert pairs == [  # The rows keep the order of the compare view.
        ("Site A", "history-site-cap-0"),
        ("Site B", "history-site-cap-1"),
        ("Site A", "history-site-cap-2"),
    ]


def test_a_page_row_with_the_identifier_alone_names_the_identifier() -> None:
    """FR-002: a record with no site name shows the site identifier."""
    rows = _page_view(_store_row("cap-0", site_id="site-old")).rows  # An old record with no name.
    assert rows[0]["site_text"] == "site-old"  # The identifier at least reaches the site page.


def test_a_page_row_with_no_capture_identifier_carries_no_site_test_identifier() -> None:
    """FR-004: a row with no capture identifier carries no test identifier, as the device type cell does."""
    rows = review.page_rows({review.ROWS_KEY: [{"capture_id": ""}]}, [])  # The fallback shape of the view.
    assert (rows[0]["site_text"], rows[0]["site_test_id"]) == ("", "")  # No identifier, so no test hook.


# ---------------------------------------------------------------------------
# The page with no site
# ---------------------------------------------------------------------------


def test_the_table_of_the_page_with_no_site_shows_the_site_column_second(environment: Environment) -> None:
    """User Story 1 and FR-001: the Site header follows the Capture header."""
    page = _render_every_site(environment, _two_site_view())  # The page with no site.
    assert _headers(page) == _EVERY_SITE_HEADERS  # Ten headers, with Site second.


def test_the_second_cell_of_each_row_is_the_site_cell(environment: Environment) -> None:
    """FR-001: the site cell sits under the Site header in each row."""
    cells = _row_cells(_render_every_site(environment, _two_site_view()))  # The cells of the three rows.
    assert [len(row) for row in cells] == [10, 10, 10]  # Each row holds ten cells.
    assert all('class="cell-site"' in row[1] for row in cells)  # The second cell of each row is the site cell.


def test_each_site_cell_prints_the_site_with_its_title_and_test_identifier(environment: Environment) -> None:
    """User Story 1, FR-002, FR-003, and FR-004: the whole acceptance table of the site cells."""
    page = _render_every_site(environment, _two_site_view())  # The page with no site.
    assert _site_cells(page) == [
        ("Site A", "history-site-cap-0", "Site A"),
        ("Site B", "history-site-cap-1", "Site B"),
        ("Site A", "history-site-cap-2", "Site A"),
    ]


def test_the_caption_of_the_page_with_no_site_names_the_site(environment: Environment) -> None:
    """FR-005: a screen reader hears that each row holds the site."""
    page = _render_every_site(environment, _two_site_view())  # The page with no site.
    assert _caption(page) == f"The stored captures of every site. {_EVERY_SITE_ROW_VALUES}"  # The whole caption.


def test_the_table_of_the_page_with_no_site_carries_the_wide_class(environment: Environment) -> None:
    """research.md R4: the class selects the width set of ten columns."""
    page = _render_every_site(environment, _two_site_view())  # The page with no site.
    assert _table_class(page) == "portal-table history-table history-table-sites"  # The wide width set.


def test_the_empty_table_of_the_page_with_no_site_spans_ten_columns(environment: Environment) -> None:
    """FR-009: the empty row spans every column of the table."""
    page = _render_every_site(environment, _page_view())  # The page with no site and no capture.
    assert _empty_span(page) == "10"  # The old row spanned nine of the ten columns.


def test_the_site_cell_escapes_the_site_name(environment: Environment) -> None:
    """A site name is text from the store, so the page prints it as text and never as markup."""
    page = _render_every_site(environment, _page_view(_store_row("cap-0", "site-x", "<b>Site</b>")))  # Markup.
    escaped = "&lt;b&gt;Site&lt;/b&gt;"  # Jinja escapes each angle bracket.
    assert _site_cells(page) == [(escaped, "history-site-cap-0", escaped)]  # The title and the text escape.
    assert "<b>Site</b>" not in page  # No markup of the name reaches the page.


# ---------------------------------------------------------------------------
# The page of one site, and a render with no column value
# ---------------------------------------------------------------------------


def test_the_page_of_one_site_keeps_the_table_of_today(environment: Environment) -> None:
    """User Story 2, FR-006, and SC-002: the page of one site shows no Site column."""
    view = _page_view(_store_row("cap-0", *_SITE_A))  # The one capture of Site A.
    scope = review.HistoryScope.for_page(_SITE_A[0], [])  # The caption of one site reads no row name.
    columns = review.HistoryCaptureColumns(site_id=_SITE_A[0])  # The columns of one site.
    page = _render(environment, history_view=view, history_scope=scope, history_columns=columns)  # One site.
    assert (_headers(page), _site_cells(page)) == (_ONE_SITE_HEADERS, [])  # Nine headers, and no site cell.
    assert _table_class(page) == "portal-table history-table"  # The width set of today.
    assert _caption(page) == f"The stored captures of the site. {_ONE_SITE_ROW_VALUES}"  # The caption of today.


def test_the_empty_table_of_one_site_spans_nine_columns(environment: Environment) -> None:
    """FR-009: the empty row of the page of one site spans its nine columns."""
    columns = review.HistoryCaptureColumns(site_id=_SITE_A[0])  # The columns of one site.
    page = _render(environment, history_view=_page_view(), history_columns=columns)  # One site, no capture.
    assert _empty_span(page) == "9"  # The span of today.


def test_a_page_with_no_column_value_keeps_the_table_of_today(environment: Environment) -> None:
    """The template reads each column value with a default, so an earlier render test stays valid."""
    page = _render(environment, history_view=_page_view())  # A caller that gives no column value.
    assert (_headers(page), _table_class(page), _empty_span(page)) == (
        _ONE_SITE_HEADERS,
        "portal-table history-table",
        "9",
    )
    assert _caption(page) == f"The stored captures of the site. {_ONE_SITE_ROW_VALUES}"  # The caption of today.


# ---------------------------------------------------------------------------
# The stylesheet
# ---------------------------------------------------------------------------


def test_the_table_with_the_site_column_gives_ten_widths_that_total_one_hundred() -> None:
    """research.md R4: each column of the wider table holds a stated share."""
    for number, share in enumerate(_SITE_WIDTHS, start=1):  # One rule for each column, in column order.
        body = _rule_body(f".history-table.history-table-sites thead th:nth-child({number})")  # The rule.
        assert f"width: {share}%" in body, f"Column {number} of the wide table holds no share of {share} percent"
    assert sum(_SITE_WIDTHS) == 100  # The shares fill the table and no more.


def test_the_table_with_the_site_column_holds_a_floor_that_fits_a_narrow_window() -> None:
    """research.md R4: a window of 1024 pixels gives the table 982 pixels, so a floor of 60rem does not scroll."""
    assert "min-width: 60rem" in _rule_body(".history-table.history-table-sites")  # The floor of the wide table.


def test_the_site_cell_clips_a_long_name_on_one_line() -> None:
    """FR-003: a long site name stays on one line and ends in an ellipsis."""
    body = _rule_body(".history-table .cell-site")  # The rule of the site cell.
    assert "overflow: hidden" in body  # The cell hides the text past its edge.
    assert "text-overflow: ellipsis" in body  # The cut text ends in an ellipsis.
    assert "white-space: nowrap" in body  # The name stays on one line, so the row keeps its height.


def test_each_site_cell_rule_names_the_history_table() -> None:
    """The shared table class serves four pages, so no site cell rule may reach another table.

    Why:
        The selectors of the wide width set hold ``.history-table-sites``, and
        that text holds ``.history-table``. A check of those selectors would
        pass for any rule, so this guard reads the site cell rules only.
    """
    lines = [line for line in _STYLESHEET.read_text(encoding="utf-8").splitlines() if "{" in line]  # Selectors.
    site_lines = [line for line in lines if ".cell-site" in line]  # The rules of the site cell.
    assert len(site_lines) >= 1, f"The stylesheet holds {len(site_lines)} site cell rules."  # The guard measured.
    assert all(".history-table " in line for line in site_lines)  # Each site cell rule names the history table.
