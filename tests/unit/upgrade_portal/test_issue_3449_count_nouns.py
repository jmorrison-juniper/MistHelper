"""Unit tests of issue #3449: the picker note and the history note agree with each count.

Why:
    The organization picker note said "The filter matches 1 organizations."
    The history note said "The site holds 1 captures." Each second sentence
    said "This page starts after N of them", and the word "them" cannot refer
    to one item. The two templates hold no rule, so each view model now gives
    the three texts of its note. These tests read each text of each view for
    the counts 0, 1, and 2. They also render each real template and read the
    whole note.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.interfaces.portals.upgrade_portal.app.routes import review, select
from src.interfaces.portals.upgrade_portal.compare import render

_TEMPLATE_ROOT = Path(select.__file__).resolve().parents[1] / "assets" / "templates"  # The real template folder.
_PICKER_TEMPLATE = "select/orgs.html"  # The organization picker.
_HISTORY_TEMPLATE = "review/history.html"  # The capture history.
_PICKER_NOTE_ID = "org-search-note"  # FR-006: the test identifier of the picker note.
_HISTORY_NOTE_ID = "history-count-note"  # FR-006: the test identifier of the history note.
_PICKER_NOTE_START = (  # The two fixed sentences before the count sentence of the picker note.
    "The filter reads the organization name and the organization identifier. The portal filters every "
    "organization that this sign-in may act on, and then shows one page of the matches."
)
_HISTORY_NOTE_START = "The list shows the stored captures of Site A."  # The fixed first sentence for one site.
_NO_SITE_NOTE_START = "The list shows the stored captures."  # The fixed first sentence when no site name exists.


@dataclass(frozen=True, slots=True)
class _StorePage:
    """A stand-in for the page record of the capture store.

    Attributes:
        captures: The capture records of this page.
        total: The number of captures that the site holds.
        limit: The number of rows that one page holds.
        offset: The number of rows that the earlier pages hold.
    """

    captures: tuple[dict[str, Any], ...] = ()
    total: int = 0
    limit: int = render.DEFAULT_HISTORY_PAGE_SIZE
    offset: int = 0


def _org(number: int) -> dict[str, str]:
    """Return one organization record as `permitted_orgs` builds it.

    Args:
        number: The number of the organization.

    Returns:
        The record, with the two fields that the picker shows.
    """
    return {"org_id": f"org-{number:03d}", "name": f"Org {number:03d}"}  # One unique key and one name.


def _orgs(count: int) -> list[dict[str, str]]:
    """Return a list of organization records.

    Args:
        count: The number of records.

    Returns:
        The records, in name order.
    """
    return [_org(number) for number in range(count)]  # One record for each number.


def _captures(count: int) -> tuple[dict[str, Any], ...]:
    """Return a run of history records with unique identifiers.

    Args:
        count: The number of records.

    Returns:
        The history records.
    """
    return tuple({"capture_id": f"cap-{number}", "role": "pre"} for number in range(count))  # One row each.


def _history_view(total: int, offset: int = 0, limit: int = render.DEFAULT_HISTORY_PAGE_SIZE) -> render.HistoryView:
    """Build the compare view of one history page.

    Args:
        total: The number of captures that the site holds.
        offset: The number of rows that the earlier pages hold.
        limit: The number of rows that one page holds.

    Returns:
        The compare view.
    """
    rows = _captures(min(max(total - offset, 0), limit))  # The rows that this page shows.
    return render.build_history_view(_StorePage(rows, total=total, limit=limit, offset=offset))  # The real builder.


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


def _note(page: str, test_id: str) -> str:
    """Return the whole text of the note that carries one test identifier.

    Args:
        page: The rendered page.
        test_id: The test identifier of the note.

    Returns:
        The text of the note, with one space between each word.
    """
    found = re.search(rf'<p[^>]*data-testid="{test_id}"[^>]*>(.*?)</p>', page, re.DOTALL)  # One paragraph.
    assert found, f"The page holds no note with the test identifier {test_id}."  # FR-006.
    return " ".join(found.group(1).split())  # The template wraps the sentences across lines.


# ---------------------------------------------------------------------------
# The picker view
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("count", "expected"),
    [(0, "0 organizations"), (1, "1 organization"), (2, "2 organizations")],
)
def test_the_picker_view_states_the_matches_with_the_noun_of_the_count(count: int, expected: str) -> None:
    """FR-001: only a count of one takes the singular noun."""
    assert select.build_org_view(_orgs(count), 0, "").total_text == expected  # The real builder settles the text.


def test_the_picker_view_of_no_organization_states_zero_organizations() -> None:
    """An empty privilege list gives the plural noun for each count text."""
    view = select.build_org_view([], 0, "")  # The account reaches no organization.
    assert (view.total_text, view.offset_text) == ("0 organizations", "0 organizations")  # Zero takes the plural.


def test_the_picker_view_states_an_offset_of_one_with_the_singular_noun() -> None:
    """FR-002: the offset uses the noun rule and never the words "of them"."""
    view = select.build_org_view(_orgs(2), 1, "")  # A hand-edited link can ask for the offset 1.
    assert (view.total_text, view.offset_text) == ("2 organizations", "1 organization")  # One row came before.


def test_the_picker_view_states_the_page_size_with_the_noun_of_the_count() -> None:
    """FR-005: the fixed page size of 25 takes the plural noun, and a size of 1 takes the singular noun."""
    assert select.build_org_view(_orgs(1), 0, "").page_size_text == "25 rows"  # The fixed page size of the picker.
    assert select.OrgPickerView(page_size=1).page_size_text == "1 row"  # The rule still covers a size of one.


def test_the_picker_rule_joins_the_count_and_the_noun() -> None:
    """The static rule gives one space between the count and the noun."""
    assert select.OrgPickerView.count_text(1, "row", "rows") == "1 row"  # One takes the singular noun.
    assert select.OrgPickerView.count_text(3, "row", "rows") == "3 rows"  # Each other count takes the plural noun.


# ---------------------------------------------------------------------------
# The two history views
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("total", "offset", "limit", "expected"),
    [
        (0, 0, 25, ("0 captures", "0 captures", "25 rows")),
        (1, 0, 25, ("1 capture", "0 captures", "25 rows")),
        (2, 0, 25, ("2 captures", "0 captures", "25 rows")),
        (2, 1, 1, ("2 captures", "1 capture", "1 row")),
    ],
)
def test_each_history_view_states_each_count_with_the_noun_of_the_count(
    total: int, offset: int, limit: int, expected: tuple[str, str, str]
) -> None:
    """FR-003, FR-004, and FR-005: the compare view and the route view give the same three texts."""
    compare_view = _history_view(total, offset, limit)  # The view that the unit tests of the page print.
    page_view = review.build_page_view(compare_view, [])  # The route view. The counts need no stored row.
    for view in (compare_view, page_view):  # The two views inherit one mixin.
        assert (view.total_text, view.offset_text, view.page_size_text) == expected  # The three texts agree.


def test_the_history_view_of_an_empty_store_page_states_zero_captures() -> None:
    """A store page with no row gives the plural noun."""
    view = render.build_history_view(())  # A bare empty row list counts itself.
    assert (view.total_text, view.offset_text) == ("0 captures", "0 captures")  # Zero takes the plural noun.


def test_the_default_route_view_states_zero_captures_and_zero_rows() -> None:
    """The default route view holds a page size of 0, which takes the plural noun."""
    view = review.HistoryPageView()  # Each field keeps its default.
    assert (view.total_text, view.offset_text, view.page_size_text) == ("0 captures", "0 captures", "0 rows")  # Zero.


def test_the_texts_are_properties_and_never_fields() -> None:
    """SC-002: a text is not a field, so `asdict` and each JSON body do not change."""
    view = _history_view(1)  # A view of one capture.
    assert [field.name for field in fields(render.HistoryView)] == [  # The eight fields of the view do not change.
        "rows",
        "total",
        "page_size",
        "offset",
        "has_next",
        "has_previous",
        "next_url",
        "previous_url",
    ]
    assert "total_text" not in asdict(view)  # The text does not reach a serialized record.
    assert not hasattr(view, "__dict__")  # The mixin keeps the slots view free of an instance dictionary.


def test_the_mixin_rule_joins_the_count_and_the_noun() -> None:
    """The static rule of the mixin gives one space between the count and the noun."""
    assert render.HistoryNoteText.count_text(1, "capture", "captures") == "1 capture"  # One takes the singular noun.
    assert render.HistoryNoteText.count_text(0, "capture", "captures") == "0 captures"  # Zero takes the plural noun.


# ---------------------------------------------------------------------------
# The real templates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("count", "offset", "sentence"),
    [
        (0, 0, "The filter matches 0 organizations. This page starts after 0 organizations,"),
        (1, 0, "The filter matches 1 organization. This page starts after 0 organizations,"),
        (2, 0, "The filter matches 2 organizations. This page starts after 0 organizations,"),
        (2, 1, "The filter matches 2 organizations. This page starts after 1 organization,"),
    ],
)
def test_the_picker_note_agrees_with_each_count(
    environment: Environment, count: int, offset: int, sentence: str
) -> None:
    """User Story 1: the whole picker note, for each row of the acceptance table."""
    view = select.build_org_view(_orgs(count), offset, "")  # The real builder.
    page = environment.get_template(_PICKER_TEMPLATE).render(org_view=view, organizations=view.rows)  # The page.
    expected = f"{_PICKER_NOTE_START} {sentence} and one page holds 25 rows."  # The whole note.
    assert _note(page, _PICKER_NOTE_ID) == expected  # A whole-text compare finds each wrong word.


@pytest.mark.parametrize(
    ("total", "offset", "limit", "sentence"),
    [
        (0, 0, 25, "The site holds 0 captures. This page starts after 0 captures, and one page holds 25 rows."),
        (1, 0, 25, "The site holds 1 capture. This page starts after 0 captures, and one page holds 25 rows."),
        (2, 0, 25, "The site holds 2 captures. This page starts after 0 captures, and one page holds 25 rows."),
        (2, 1, 1, "The site holds 2 captures. This page starts after 1 capture, and one page holds 1 row."),
    ],
)
def test_the_history_note_agrees_with_each_count(
    environment: Environment, total: int, offset: int, limit: int, sentence: str
) -> None:
    """User Story 2: the whole history note, for each row of the acceptance table."""
    view = _history_view(total, offset, limit)  # The real builder.
    scope = review.HistoryScope(site_id="site-a", site_name="Site A")  # Issue #3482: the page of one named site.
    page = environment.get_template(_HISTORY_TEMPLATE).render(history_scope=scope, history_view=view)  # The page.
    assert _note(page, _HISTORY_NOTE_ID) == f"{_HISTORY_NOTE_START} {sentence}"  # The whole note.


def test_the_history_note_of_a_page_with_no_view_states_zero(environment: Environment) -> None:
    """FR-007: the page with no view still renders, and the note states zero."""
    page = environment.get_template(_HISTORY_TEMPLATE).render()  # The route supplied nothing.
    expected = (
        "The site holds 0 captures. This page starts after 0 captures, and one page holds 0 rows."  # The defaults.
    )
    assert _note(page, _HISTORY_NOTE_ID) == f"{_NO_SITE_NOTE_START} {expected}"  # The whole note.


def test_the_two_notes_never_say_of_them(environment: Environment) -> None:
    """FR-002 and FR-004: the words "of them" cannot refer to one item, so they do not appear."""
    picker = environment.get_template(_PICKER_TEMPLATE).render(org_view=select.build_org_view(_orgs(1), 0, ""))  # One.
    history = environment.get_template(_HISTORY_TEMPLATE).render(history_view=_history_view(1))  # One capture.
    for page in (picker, history):  # Each note printed a count sentence.
        assert "of them" not in " ".join(page.split())  # The squash joins a sentence that wraps across lines.
