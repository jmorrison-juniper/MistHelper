"""The tests of the history table layout.

Why:
    Issue #2106 reports that one history row stands about 113 pixels tall. The
    capture identifier takes a third of the table width and wraps across three
    lines. The raw moment wraps across four lines. The action column then
    collapses, and the ``Open`` control prints one letter on each line.

    Three parts hold the repair, and each part needs a test.

    The first part shapes the moment in Python. A template must never hold a
    rule, so ``src.upgrade_portal.app.routes.review`` cuts the seconds and names
    the zone. The tests below read that shaper directly.

    The second part prints the short text and keeps the full text in a ``title``
    attribute. The tests below render the real template with Jinja.

    The third part gives each column a width budget. A stylesheet rule cannot
    run in a unit test, so the tests below read the rule text of ``portal.css``.
    ``tests/e2e/upgrade_portal/test_history_layout.py`` measures the painted box
    in a real browser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import review
from src.upgrade_portal.compare import render

# The repository root. This file sits at tests/unit/upgrade_portal/.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# The asset folder of the portal. The template folder and the stylesheet both
# sit below it, so one anchor finds each of them.
_ASSET_ROOT = Path(render.__file__).resolve().parents[1] / "app" / "assets"
_TEMPLATE_ROOT = _ASSET_ROOT / "templates"
_STYLESHEET = _ASSET_ROOT / "static" / "css" / "portal.css"

# The page under test.
_TEMPLATE_NAME = "review/history.html"

# A real capture identifier holds 39 characters. Issue #2106 measured this shape.
_LONG_CAPTURE_ID = "cap-0eb57df4b3e445e6b179efc6953a271d-01"

# A real stored moment. `capture/assembly.py` writes `datetime.now(tz=UTC).isoformat()`.
_LONG_MOMENT = "2026-08-27T05:50:06.563952+00:00"
_SHORT_MOMENT = "2026-08-27 05:50 UTC"


@dataclass(frozen=True, slots=True)
class _StorePage:
    """A stand-in for the page record of the capture store.

    Why:
        The real record lives in ``src.upgrade_portal.capture.store``, and that
        module imports the database driver. A stand-in with the same four field
        names keeps the driver out of a unit test.

    Attributes:
        captures: The capture records of this page.
        total: The number of captures the site holds.
        limit: The number of rows one page holds.
        offset: The number of rows the earlier pages hold.
    """

    captures: tuple[dict[str, Any], ...] = ()
    total: int = 0
    limit: int = 25
    offset: int = 0


def _capture_row(capture_id: str = _LONG_CAPTURE_ID, started_at: str = _LONG_MOMENT) -> dict[str, Any]:
    """Return one history record as the store hands it over.

    Args:
        capture_id: The identifier of the capture.
        started_at: The stored moment of the capture.

    Returns:
        One history record.
    """
    return {
        "capture_id": capture_id,
        "started_at": started_at,
        "role": "pre",
        "capture_status": "verified",
        "actor_email": "operator@example.com",
        "stored_size_bytes": 1_234_567,
    }


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset.

    Why:
        The base page asks ``url_for`` for three stylesheets and two scripts.
        Flask supplies that helper, and this test renders without Flask.

    Args:
        endpoint: The endpoint name. Always ``static`` on this page.
        **values: The endpoint arguments. Holds ``filename``.

    Returns:
        A path that stands in for the real asset path.
    """
    return f"/{endpoint}/{values.get('filename', '')}"


@pytest.fixture(scope="module")
def environment() -> Environment:
    """Return a Jinja environment that loads the real portal templates.

    Why:
        The page extends the real base page and includes the real navigation.
        The strict undefined type turns a missing value into a failure, so a
        new template value without a default cannot pass unseen.

    Returns:
        The environment.
    """
    built = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    built.globals["url_for"] = _static_url  # Flask supplies this name in production.
    built.globals["request"] = None  # The navigation partial reads this name.
    return built


def _render_page(environment: Environment, **context: Any) -> str:
    """Render the history page with the given context.

    Args:
        environment: The Jinja environment.
        **context: The template context.

    Returns:
        The rendered page.
    """
    return environment.get_template(_TEMPLATE_NAME).render(**context)


def _squash(text: str) -> str:
    """Return the text with every run of white space replaced by one space.

    Args:
        text: The rendered page, or a piece of markup.

    Returns:
        The same text with single spaces.
    """
    return re.sub(r"\s+", " ", text)


def _stylesheet_text() -> str:
    """Return the text of the portal stylesheet.

    Returns:
        The whole stylesheet.
    """
    return _STYLESHEET.read_text(encoding="utf-8")


def _rule_body(selector: str) -> str:
    """Return the declarations of one stylesheet rule.

    Why:
        A test must read the declarations of one selector alone. A search of
        the whole file would pass when the declaration sat under a different
        selector, and the column budget would then reach the wrong table.

    Args:
        selector: The exact selector text, with no brace.

    Returns:
        The declarations between the braces, or an empty text.
    """
    pattern = re.compile(re.escape(selector) + r"\s*\{([^}]*)\}")
    found = pattern.search(_stylesheet_text())
    return found.group(1) if found else ""


# ---------------------------------------------------------------------------
# The short moment text
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        (_LONG_MOMENT, _SHORT_MOMENT),
        ("2026-08-19T09:00:00Z", "2026-08-19 09:00 UTC"),
        ("2026-08-27T07:50:06+02:00", _SHORT_MOMENT),
        ("2026-08-27T05:50:06", _SHORT_MOMENT),
    ],
)
def test_the_short_moment_drops_the_seconds_and_names_the_zone(stored: str, expected: str) -> None:
    """Prove the shaper answers a short moment that a person reads at a glance.

    Why:
        Issue #2106 measured a 32 character moment that wrapped across four
        lines. A 20 character moment fits one line, and the operator still
        reads the day and the minute.

    Args:
        stored: The moment as the store holds it.
        expected: The short text the page must show.
    """
    assert review.short_moment(stored) == expected


@pytest.mark.parametrize("stored", ["", "   ", "not a moment", "2026-13-45T99:99:99"])
def test_the_short_moment_keeps_a_value_it_cannot_read(stored: str) -> None:
    """Prove a value the shaper cannot read reaches the page unchanged.

    Why:
        The page must never drop a stored value. A moment from a later release
        of the store therefore prints as it stands, and the operator still
        quotes it in a support case.

    Args:
        stored: The moment as the store holds it.
    """
    assert review.short_moment(stored) == stored


def test_the_short_moment_reads_a_value_that_is_not_a_text() -> None:
    """Prove a record that holds no text answers an empty moment.

    Why:
        A partial record can hold ``None`` under ``started_at``. The shaper
        must answer an empty text there instead of raising, because a raise
        would show a server fault in place of the whole page.
    """
    assert review.short_moment(None) == ""


def test_the_moment_texts_carry_one_entry_for_each_row() -> None:
    """Prove the map holds the short moment of every row, under the row key."""
    rows = [_capture_row("cap-a"), _capture_row("cap-b", "2026-08-19T09:00:00Z")]
    assert review.moment_texts(rows) == {"cap-a": _SHORT_MOMENT, "cap-b": "2026-08-19 09:00 UTC"}


def test_the_moment_texts_skip_a_row_with_no_identifier() -> None:
    """Prove a row with no identifier reaches no entry.

    Why:
        The page reads the map by the capture identifier. An entry under an
        empty key could reach a second row that also holds no identifier, and
        the page would then show the moment of the wrong capture.
    """
    assert review.moment_texts([_capture_row("")]) == {}


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------


def test_the_page_shows_the_short_moment_and_keeps_the_stored_one(environment: Environment) -> None:
    """Prove the cell prints the short moment and holds the stored moment.

    Args:
        environment: The Jinja environment.
    """
    rows = (_capture_row(),)
    view = render.build_history_view(_StorePage(rows, total=1))
    page = _squash(_render_page(environment, history_view=view, moment_texts=review.moment_texts(rows)))
    assert f'title="{_LONG_MOMENT}"' in page  # The stored value stays reachable.
    assert f">{_SHORT_MOMENT}<" in page  # The visible text is the short one.


def test_the_page_falls_back_to_the_stored_moment(environment: Environment) -> None:
    """Prove a page with no moment map still prints the stored moment.

    Why:
        The strict undefined type raises on a value with no default. A page
        that another caller renders without the map must still show a moment.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view(_StorePage((_capture_row(),), total=1))
    page = _squash(_render_page(environment, history_view=view))
    assert f">{_LONG_MOMENT}<" in page


def test_the_page_keeps_the_whole_capture_identifier(environment: Environment) -> None:
    """Prove the row header holds the whole identifier in a title attribute.

    Why:
        An operator quotes the capture identifier in a support case. The cell
        clips the text with an ellipsis, so the whole value must stay in the
        markup.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view(_StorePage((_capture_row(),), total=1))
    page = _squash(_render_page(environment, history_view=view))
    assert f'title="{_LONG_CAPTURE_ID}"' in page
    assert f">{_LONG_CAPTURE_ID}<" in page


def test_the_page_marks_the_three_columns_that_hold_a_width_budget(environment: Environment) -> None:
    """Prove the table and its three narrow cells carry the layout classes.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view(_StorePage((_capture_row(),), total=1))
    page = _squash(_render_page(environment, history_view=view))
    assert 'class="portal-table history-table"' in page
    assert "cell-capture" in page
    assert "cell-moment" in page
    assert "cell-action" in page


def test_the_page_keeps_every_history_identifier(environment: Environment) -> None:
    """Prove the layout change kept all five fixed test identifiers.

    Why:
        ``specs/1823-upgrade-capture-portal/contracts/ui-testids.md`` fixes
        these names. A browser test finds no control once a name moves.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view(_StorePage((_capture_row(),), total=1))
    page = _squash(_render_page(environment, history_view=view))
    for identifier in (
        "history-table",
        f"history-row-{_LONG_CAPTURE_ID}",
        f"history-open-{_LONG_CAPTURE_ID}",
        "history-page-next",
        "history-page-previous",
    ):
        assert f'data-testid="{identifier}"' in page


def test_the_page_adds_no_style_attribute() -> None:
    """Prove the page carries no inline style attribute.

    Why:
        The content security policy of this portal is ``'self'`` only. That
        policy blocks a style attribute, so the layout must live in a class.
    """
    assert "style=" not in (_TEMPLATE_ROOT / _TEMPLATE_NAME).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The stylesheet
# ---------------------------------------------------------------------------


def test_the_history_table_holds_a_fixed_column_layout() -> None:
    """Prove the table shares its width by a plan instead of by content.

    Why:
        An automatic layout hands the width to the widest column. The 39
        character identifier took a third of the table, and the action column
        then collapsed. A fixed layout obeys the stated column widths.
    """
    assert "table-layout: fixed" in _rule_body(".history-table")


def test_the_capture_cell_clips_the_identifier_on_one_line() -> None:
    """Prove the identifier cell stays on one line and shows an ellipsis."""
    body = _rule_body(".history-table .cell-capture")
    assert "white-space: nowrap" in body
    assert "text-overflow: ellipsis" in body
    assert "overflow: hidden" in body


def test_the_moment_cell_and_the_action_cell_stay_on_one_line() -> None:
    """Prove neither the moment nor the action control wraps.

    Why:
        Issue #2106 shows the ``Open`` control as four stacked letters. A cell
        that never wraps cannot stack a letter.
    """
    assert "white-space: nowrap" in _rule_body(".history-table .cell-moment")
    assert "white-space: nowrap" in _rule_body(".history-table .cell-action")


def test_the_history_row_holds_a_height_budget() -> None:
    """Prove the open control is short enough for a 48 pixel row.

    Why:
        The shared button asks for 2.5rem of height. That height plus the cell
        padding stands above 48 pixels, so the history table asks for less.
    """
    assert "min-height: 2rem" in _rule_body(".history-table .cell-action .portal-button")


def test_the_stylesheet_scopes_every_new_rule_to_the_history_table() -> None:
    """Prove no new rule reaches the capture table or the comparison table.

    Why:
        ``.portal-table`` serves four pages. A width budget for eight columns
        would break a table that holds a different number of columns.
    """
    for selector in (".cell-capture", ".cell-moment", ".cell-action"):
        for line in _stylesheet_text().splitlines():
            if selector in line and "{" in line:
                assert ".history-table" in line, f"{line!r} reaches every portal table"
