"""Unit tests of issue #3482: the capture history with no site names every site.

Why:
    The history page with no site read the site name of its first row. For
    the captures of two sites, the note then said "The list shows the stored
    captures of E2E Stand-In Site. The site holds 5 captures." The hidden
    caption said "The stored captures of the site." These tests read the texts
    of the scope class for each scope. They also render the real template and
    read the whole note and the whole caption.
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

_TEMPLATE_ROOT = Path(review.__file__).resolve().parents[1] / "assets" / "templates"  # The real template folder.
_HISTORY_TEMPLATE = "review/history.html"  # The capture history.
_NOTE_ID = "history-count-note"  # Issue #3449 added this test identifier to the note.
_SITE_ID = "site-a"  # The site of the page of one site.
_SITE_NAME = "Site A"  # The name that the rows of that site carry.
_OTHER_SITE_NAME = "Site B"  # The name of a second site of the same store.
_EVERY_SITE_LEAD = "The list shows the stored captures of every site."  # FR-001: the page with no site.
_NAMED_SITE_LEAD = f"The list shows the stored captures of {_SITE_NAME}."  # FR-003: the page of one site.
_NO_NAME_LEAD = "The list shows the stored captures."  # A site with no name keeps the old sentence.
_EVERY_SITE_HOLDER = "The portal holds"  # FR-002: the holder words of the page with no site.
_ONE_SITE_HOLDER = "The site holds"  # FR-003: the holder words of the page of one site.
_EVERY_SITE_CAPTION = "The stored captures of every site."  # FR-004: the caption of the page with no site.
_ONE_SITE_CAPTION = "The stored captures of the site."  # The caption of one site keeps the old sentence.
_CAPTION_TAIL = (  # The second sentence of the caption, which does not change.
    "Each row holds the moment, the role, the state, the device count, the device types, the client count, "
    "and the stored size."
)
_WINDOW_TAIL = "This page starts after 0 captures, and one page holds 25 rows."  # The default window sentence.


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


def _rows(*names: str) -> list[dict[str, Any]]:
    """Return one shaped history row for each site name.

    Args:
        *names: The site name of each row, in list order.

    Returns:
        The rows, as the route shapes them before it builds the scope.
    """
    return [{"capture_id": f"cap-{number}", "site_name": name} for number, name in enumerate(names)]  # One each.


def _history_view(total: int) -> render.HistoryView:
    """Build the compare view of the first history page.

    Args:
        total: The number of captures that the list holds.

    Returns:
        The compare view.
    """
    rows = tuple({"capture_id": f"cap-{number}", "role": "pre"} for number in range(total))  # One row each.
    return render.build_history_view(_StorePage(rows, total=total))  # The real builder settles the count texts.


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
        **values: The template values, such as the view and the scope.

    Returns:
        The rendered page.
    """
    return environment.get_template(_HISTORY_TEMPLATE).render(**values)  # The same template that the portal serves.


def _note(page: str) -> str:
    """Return the whole text of the note of the Captures card.

    Args:
        page: The rendered page.

    Returns:
        The text of the note, with one space between each word.
    """
    found = re.search(rf'<p[^>]*data-testid="{_NOTE_ID}"[^>]*>(.*?)</p>', page, re.DOTALL)  # One paragraph.
    assert found, f"The page holds no note with the test identifier {_NOTE_ID}."  # Issue #3449 added it.
    return " ".join(found.group(1).split())  # The template wraps the sentences across lines.


def _caption(page: str) -> str:
    """Return the whole text of the hidden caption of the history table.

    Args:
        page: The rendered page.

    Returns:
        The text of the caption, with one space between each word.
    """
    pattern = r'<table[^>]*data-testid="history-table"[^>]*>\s*<caption[^>]*>(.*?)</caption>'  # The first child.
    found = re.search(pattern, page, re.DOTALL)  # The caption of the capture table.
    assert found, "The page holds no caption of the history table."  # A screen reader reads this caption.
    return " ".join(found.group(1).split())  # The template wraps the sentences across lines.


# ---------------------------------------------------------------------------
# The scope texts
# ---------------------------------------------------------------------------


def test_the_scope_with_no_site_names_every_site() -> None:
    """FR-001, FR-002, and FR-004: the page with no site states the scope of every site."""
    scope = review.HistoryScope.for_page("", _rows(_SITE_NAME, _OTHER_SITE_NAME))  # The rows of two sites.
    texts = (scope.capture_lead_text, scope.capture_holder_text, scope.capture_caption_text)  # The three texts.
    assert texts == (_EVERY_SITE_LEAD, _EVERY_SITE_HOLDER, _EVERY_SITE_CAPTION)  # No text names one site.


def test_the_scope_with_no_site_reads_no_row_name() -> None:
    """FR-001: the name of the first row belongs to one of many sites, so the scope does not read it."""
    scope = review.HistoryScope.for_page("", _rows(_SITE_NAME, _OTHER_SITE_NAME))  # The rows of two sites.
    assert (scope.site_id, scope.site_name) == ("", "")  # The old route read "Site A" here.


def test_the_scope_of_a_named_site_keeps_the_site_name() -> None:
    """FR-003 and FR-004: the page of one site keeps its name and its old holder words."""
    scope = review.HistoryScope.for_page(_SITE_ID, _rows(_SITE_NAME))  # The rows of one site.
    texts = (scope.capture_lead_text, scope.capture_holder_text, scope.capture_caption_text)  # The three texts.
    assert texts == (_NAMED_SITE_LEAD, _ONE_SITE_HOLDER, _ONE_SITE_CAPTION)  # The page of one site does not change.


def test_the_scope_of_a_site_with_no_name_keeps_the_old_texts() -> None:
    """A site that holds no capture has no name on a row, so the note keeps the plain first sentence."""
    scope = review.HistoryScope.for_page(_SITE_ID, [])  # The site holds no capture yet.
    texts = (scope.capture_lead_text, scope.capture_holder_text, scope.capture_caption_text)  # The three texts.
    assert texts == (_NO_NAME_LEAD, _ONE_SITE_HOLDER, _ONE_SITE_CAPTION)  # The texts of a site with no name.


def test_the_scope_holds_two_fields_and_each_text_is_a_property() -> None:
    """FR-005: the scope holds the request values, and each text is a property and not a field."""
    assert [field.name for field in fields(review.HistoryScope)] == ["site_id", "site_name"]  # Two fields only.


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("total", "count_text"), [(0, "0 captures"), (1, "1 capture"), (5, "5 captures")])
def test_the_note_of_the_page_with_no_site_names_every_site(
    environment: Environment, total: int, count_text: str
) -> None:
    """User Story 1: the whole note of the page with no site, for each row of the acceptance table."""
    scope = review.HistoryScope.for_page("", _rows(_SITE_NAME, _OTHER_SITE_NAME))  # The rows of two sites.
    page = _render(environment, history_view=_history_view(total), history_scope=scope)  # The page with no site.
    expected = f"{_EVERY_SITE_LEAD} {_EVERY_SITE_HOLDER} {count_text}. {_WINDOW_TAIL}"  # The whole note.
    assert _note(page) == expected  # A whole-text compare also proves that no site name appears.


def test_the_caption_of_the_page_with_no_site_names_every_site(environment: Environment) -> None:
    """FR-004: the hidden caption names the same scope as the note."""
    scope = review.HistoryScope.for_page("", _rows(_SITE_NAME, _OTHER_SITE_NAME))  # The rows of two sites.
    page = _render(environment, history_view=_history_view(2), history_scope=scope)  # The page with no site.
    assert _caption(page) == f"{_EVERY_SITE_CAPTION} {_CAPTION_TAIL}"  # The screen reader hears every site.


def test_the_page_of_one_site_keeps_the_note_and_the_caption(environment: Environment) -> None:
    """User Story 2 and SC-002: the page of one site does not change."""
    scope = review.HistoryScope.for_page(_SITE_ID, _rows(_SITE_NAME))  # The rows of one site.
    page = _render(environment, history_view=_history_view(1), history_scope=scope)  # The page of one site.
    expected_note = f"{_NAMED_SITE_LEAD} {_ONE_SITE_HOLDER} 1 capture. {_WINDOW_TAIL}"  # The whole note.
    assert (_note(page), _caption(page)) == (expected_note, f"{_ONE_SITE_CAPTION} {_CAPTION_TAIL}")  # No change.


def test_the_page_of_a_site_with_no_name_keeps_the_plain_note(environment: Environment) -> None:
    """User Story 2: a site that holds no capture keeps the plain first sentence."""
    scope = review.HistoryScope.for_page(_SITE_ID, [])  # The site holds no capture yet.
    page = _render(environment, history_view=_history_view(0), history_scope=scope)  # The empty page of one site.
    assert _note(page) == f"{_NO_NAME_LEAD} {_ONE_SITE_HOLDER} 0 captures. {_WINDOW_TAIL}"  # The whole note.


def test_a_page_with_no_scope_uses_the_texts_of_a_site_with_no_name(environment: Environment) -> None:
    """FR-006: a render with no scope value still succeeds, and it prints the old texts."""
    page = _render(environment, history_view=_history_view(0))  # A caller that supplies no scope.
    assert _note(page) == f"{_NO_NAME_LEAD} {_ONE_SITE_HOLDER} 0 captures. {_WINDOW_TAIL}"  # The old note.
    assert _caption(page) == f"{_ONE_SITE_CAPTION} {_CAPTION_TAIL}"  # The old caption.


def test_the_page_escapes_the_site_name(environment: Environment) -> None:
    """A site name is text from the store, so the page prints it as text and never as markup."""
    scope = review.HistoryScope.for_page(_SITE_ID, _rows("<b>Site</b>"))  # A name that holds markup.
    page = _render(environment, history_view=_history_view(1), history_scope=scope)  # The page of that site.
    assert "of &lt;b&gt;Site&lt;/b&gt;." in _note(page)  # The note escapes each angle bracket.
    assert "<b>Site</b>" not in page  # No markup of the name reaches the page.
