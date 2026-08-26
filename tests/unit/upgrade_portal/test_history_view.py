"""The tests of the history view model and of the history page.

Why:
    The history page must show a stable test identifier on every row, a stored
    size a person can read, and a paging control that never lies. Each of those
    three is a rule, and a rule that lives in a template cannot be tested
    without a browser. These tests prove that the rules live in
    ``src.upgrade_portal.compare.render`` instead, and that the page only
    prints what that module decided.

    The last group renders the real template with Jinja. A page that needs a
    rule of its own would fail there, because the render receives a view model
    and nothing else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.compare import render

# The repository root. This file sits at tests/unit/upgrade_portal/.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# The contract that fixes every test identifier of the portal.
_CONTRACT_PATH = _REPO_ROOT / "specs" / "1823-upgrade-capture-portal" / "contracts" / "ui-testids.md"

# The template folder of the portal, beside the compare package.
_TEMPLATE_ROOT = Path(render.__file__).resolve().parents[1] / "app" / "assets" / "templates"

# The page under test.
_TEMPLATE_NAME = "review/history.html"

# The expression delimiters of Jinja. A rule can hide in either one.
_EXPRESSION_PATTERN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)

# A Jinja comment holds prose, and prose holds a hyphen and a full stop.
_COMMENT_PATTERN = re.compile(r"\{#.*?#\}", re.DOTALL)

# Every token that would prove the page holds arithmetic or a numeric test.
_RULE_TOKENS = (
    " + ",
    " - ",
    " * ",
    " / ",
    " // ",
    " < ",
    " > ",
    " <= ",
    " >= ",
    "|sum",
    "| sum",
    "|length",
    "| length",
    "|round",
    "| round",
)


@dataclass(frozen=True, slots=True)
class _StorePage:
    """A stand-in for the page record of the capture store.

    Why:
        The real record lives in ``src.upgrade_portal.capture.store``, and that
        module imports the database driver. A stand-in with the same four field
        names proves the view builder reads the record without pulling a driver
        into a unit test.

    Attributes:
        captures: The capture records of this page.
        total: The number of captures the site holds.
        limit: The number of rows one page holds.
        offset: The number of rows the earlier pages hold.
    """

    captures: tuple[dict[str, Any], ...] = ()
    total: int = 0
    limit: int = render.DEFAULT_HISTORY_PAGE_SIZE
    offset: int = 0


@dataclass(frozen=True, slots=True)
class _RouteWindow:
    """A stand-in for the paging record of the route lane.

    Why:
        The route lane owns the real path of the history page, so it may hand
        the two links to the view builder. This record proves the builder takes
        those links and prefers them over the links it can build itself.

    Attributes:
        total: The number of captures the site holds.
        limit: The number of rows one page holds.
        offset: The number of rows the earlier pages hold.
        previous_href: The path of the earlier page, or an empty text.
        next_href: The path of the later page, or an empty text.
    """

    total: int = 0
    limit: int = render.DEFAULT_HISTORY_PAGE_SIZE
    offset: int = 0
    previous_href: str = ""
    next_href: str = ""


def _capture_row(capture_id: str, **extra: Any) -> dict[str, Any]:
    """Return one history record as the store hands it over.

    Why:
        Every paging test needs many rows, and only the identifier changes
        between them. One builder keeps the tests short.

    Args:
        capture_id: The identifier of the capture.
        **extra: Any further field of the record.

    Returns:
        One history record.
    """
    row = {
        "capture_id": capture_id,
        "started_at": "2026-08-19T09:00:00Z",
        "role": "pre",
        "capture_status": "verified",
        "actor_email": "operator@example.com",
        "stored_size_bytes": 1_234_567,
    }
    row.update(extra)
    return row


def _capture_rows(count: int, first: int = 0) -> tuple[dict[str, Any], ...]:
    """Return a run of history records with unique identifiers.

    Args:
        count: The number of records.
        first: The number of the first record.

    Returns:
        The history records.
    """
    return tuple(_capture_row(f"cap-{number}") for number in range(first, first + count))


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset.

    Why:
        The base page asks ``url_for`` for three stylesheets and two scripts.
        Flask supplies that helper, and this test renders without Flask, so the
        environment needs a helper of its own.

    Args:
        endpoint: The endpoint name. Always ``static`` on these pages.
        **values: The endpoint arguments. Holds ``filename``.

    Returns:
        A path that stands in for the real asset path.
    """
    return f"/{endpoint}/{values.get('filename', '')}"


@pytest.fixture(scope="module")
def environment() -> Environment:
    """Return a Jinja environment that loads the real portal templates.

    Why:
        The page under test extends the real base page and includes the real
        navigation, so a stub loader would prove nothing. The strict undefined
        type turns a missing value into a failure instead of an empty string,
        which is the state several templates already claim.

    Returns:
        The environment.
    """
    built = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    # Flask supplies both names. This render has no Flask, so the environment does.
    built.globals["url_for"] = _static_url
    built.globals["request"] = None
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

    Why:
        A markup test must read the attributes of one control, and those
        attributes sit on separate lines. A reindent of the page would break a
        test that matched the line breaks, and a reindent changes no behavior.

    Args:
        text: The rendered page, or a piece of markup.

    Returns:
        The same text with single spaces.
    """
    return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------------------------
# The test identifiers
# ---------------------------------------------------------------------------


def test_the_contract_holds_every_history_identifier() -> None:
    """Prove the contract file still names the five history identifiers.

    Why:
        Every other test in this file compares against a value this module
        spells out. That proves the module is self-consistent and proves
        nothing about the contract. This test reads the contract itself, so a
        silent change to the contract fails here first.
    """
    contract = _CONTRACT_PATH.read_text(encoding="utf-8")
    for identifier in ("history-table", "history-row-{capture_id}", "history-open-{capture_id}"):
        assert f"`{identifier}`" in contract
    for identifier in ("history-page-next", "history-page-previous", "nav-history"):
        assert f"`{identifier}`" in contract


def test_the_prefixes_match_the_contract() -> None:
    """Prove the two row prefixes match the contract spelling."""
    assert render.HISTORY_ROW_TEST_ID_PREFIX == "history-row-"
    assert render.HISTORY_OPEN_TEST_ID_PREFIX == "history-open-"


def test_the_fixed_identifiers_match_the_contract() -> None:
    """Prove the three page identifiers match the contract spelling."""
    assert render.HISTORY_TABLE_TEST_ID == "history-table"
    assert render.HISTORY_NEXT_TEST_ID == "history-page-next"
    assert render.HISTORY_PREVIOUS_TEST_ID == "history-page-previous"


def test_the_builders_append_the_capture_identifier() -> None:
    """Prove both builders append the capture identifier and change nothing else.

    Why:
        Contract rule 5 asks a dynamic row to append a stable key. A builder
        that changed the case or the separator would break every browser test
        that reads the key from an API body.
    """
    assert render.history_row_test_id("cap-7") == "history-row-cap-7"
    assert render.history_open_test_id("cap-7") == "history-open-cap-7"


def test_the_row_carries_both_identifiers_and_the_open_link() -> None:
    """Prove the row builder settles the two identifiers and the capture path."""
    row = render.build_history_row(_capture_row("cap-9"))
    assert row.row_test_id == "history-row-cap-9"
    assert row.open_test_id == "history-open-cap-9"
    assert row.open_url == "/captures/cap-9"


def test_a_row_with_no_identifier_still_builds() -> None:
    """Prove a record with no identifier renders instead of raising.

    Why:
        A partial capture may drop a field. The page must still list the row,
        because a missing row hides the fault from the operator.
    """
    row = render.build_history_row({})
    assert row.capture_id == ""
    assert row.row_test_id == "history-row-"
    assert row.stored_size_text == "0 B"


# ---------------------------------------------------------------------------
# The stored size text
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("size_bytes", "expected"),
    [
        (0, "0 B"),
        (1, "1 B"),
        (999, "999 B"),
        (1_000, "1.0 kB"),
        (1_500, "1.5 kB"),
        (1_599, "1.5 kB"),
        (999_999, "999.9 kB"),
        (1_000_000, "1.0 MB"),
        (1_234_567, "1.2 MB"),
        (2_900_000, "2.9 MB"),
        (1_500_000_000, "1.5 GB"),
        (2_000_000_000_000, "2.0 TB"),
        (9_999_000_000_000_000, "9999.0 TB"),
    ],
)
def test_the_size_text_follows_one_rule(size_bytes: int, expected: str) -> None:
    """Prove the size rule is decimal, one decimal place, and cut not rounded.

    Why:
        The customer asked to see the stored size in a readable form. One rule
        must answer every size, and a size of 1 599 bytes must read 1.5 kB, not
        1.6 kB. A rounded text would state a size the disk does not hold.

    Args:
        size_bytes: The stored size.
        expected: The text the rule produces.
    """
    assert render.format_stored_size(size_bytes) == expected


def test_the_size_text_never_states_a_larger_size() -> None:
    """Prove the text never overstates the stored size.

    Why:
        An operator reads the size before a copy or a delete. A text that
        rounds up states a size the store does not hold, and a floating point
        step would do that once for every few thousand values.
    """
    units = {"B": 1, "kB": 1_000, "MB": 1_000_000, "GB": 1_000_000_000}
    for size_bytes in range(0, 4_000_000, 7_919):
        number, unit = render.format_stored_size(size_bytes).split(" ")
        assert float(number) * units[unit] <= size_bytes


@pytest.mark.parametrize("value", [None, "big", True, False, -5, float("nan"), float("inf")])
def test_the_size_text_answers_zero_for_a_bad_shape(value: object) -> None:
    """Prove a value that is not a size reads zero instead of raising.

    Why:
        The size arrives from a stored document, so the shape is not certain.
        A page that raised on one bad record would hide every other record.

    Args:
        value: One value that is not a byte count.
    """
    assert render.format_stored_size(value) == "0 B"


def test_the_size_text_cuts_a_floating_point_size() -> None:
    """Prove a size that arrived through JSON as a float still reads correctly."""
    assert render.format_stored_size(1_234_567.9) == "1.2 MB"


def test_the_row_carries_the_size_twice() -> None:
    """Prove the row holds the byte count and the readable text together.

    Why:
        A test and a later sort need the number, and the operator needs the
        text. The page must never build one from the other.
    """
    row = render.build_history_row(_capture_row("cap-1", stored_size_bytes=2_900_000))
    assert row.stored_size_bytes == 2_900_000
    assert row.stored_size_text == "2.9 MB"


# ---------------------------------------------------------------------------
# The paging
# ---------------------------------------------------------------------------


def test_the_first_page_offers_a_later_page_only() -> None:
    """Prove the first page hides the previous control and shows the next one."""
    view = render.build_history_view(_StorePage(_capture_rows(25), total=60, limit=25, offset=0))
    assert view.has_previous is False
    assert view.has_next is True
    assert view.previous_url == ""
    assert view.next_url == "/history?limit=25&offset=25"


def test_a_middle_page_offers_both_pages() -> None:
    """Prove a middle page shows both controls and points at the right offsets."""
    view = render.build_history_view(_StorePage(_capture_rows(25, 25), total=60, limit=25, offset=25))
    assert view.has_previous is True
    assert view.has_next is True
    assert view.previous_url == "/history?limit=25&offset=0"
    assert view.next_url == "/history?limit=25&offset=50"


def test_the_last_page_offers_an_earlier_page_only() -> None:
    """Prove the last page hides the next control and shows the previous one."""
    view = render.build_history_view(_StorePage(_capture_rows(10, 50), total=60, limit=25, offset=50))
    assert view.has_previous is True
    assert view.has_next is False
    assert view.previous_url == "/history?limit=25&offset=25"
    assert view.next_url == ""


def test_a_single_page_offers_neither_page() -> None:
    """Prove a site with few captures shows two locked controls."""
    view = render.build_history_view(_StorePage(_capture_rows(3), total=3, limit=25, offset=0))
    assert view.has_previous is False
    assert view.has_next is False


def test_an_empty_site_offers_neither_page() -> None:
    """Prove a site with no capture never offers a page."""
    view = render.build_history_view(_StorePage())
    assert view.rows == ()
    assert view.has_previous is False
    assert view.has_next is False


def test_the_previous_link_never_asks_for_a_negative_offset() -> None:
    """Prove a short first page cannot build a negative offset.

    Why:
        A route may hand a page whose offset is smaller than the page size. A
        negative offset would reach the store as a bind parameter and would
        raise there, far from the cause.
    """
    view = render.build_history_view(_StorePage(_capture_rows(5, 10), total=60, limit=25, offset=10))
    assert view.previous_url == "/history?limit=25&offset=0"


def test_the_route_link_wins_over_the_built_link() -> None:
    """Prove the view builder prefers the links of the route lane.

    Why:
        The route lane owns the real path of the page. A built link is the
        fallback for a caller that hands no link at all.
    """
    window = _RouteWindow(total=60, limit=25, offset=25, previous_href="/history?p=1", next_href="/history?p=3")
    view = render.build_history_view(_capture_rows(25, 25), window=window)
    assert view.previous_url == "/history?p=1"
    assert view.next_url == "/history?p=3"


def test_the_builder_reads_a_plain_row_list_with_a_window() -> None:
    """Prove the route lane may hand the rows and the paging apart.

    Why:
        The route lane builds its own paging record and passes the rows as a
        plain list. Both shapes must reach the same view model.
    """
    window = _RouteWindow(total=60, limit=25, offset=25)
    view = render.build_history_view(list(_capture_rows(25, 25)), window=window)
    assert len(view.rows) == 25
    assert view.total == 60
    assert view.offset == 25
    assert view.page_size == 25


def test_a_bare_row_list_counts_itself() -> None:
    """Prove a caller that hands rows alone still gets a whole view model."""
    view = render.build_history_view(list(_capture_rows(4)))
    assert view.total == 4
    assert view.has_next is False
    assert view.page_size == render.DEFAULT_HISTORY_PAGE_SIZE


def test_a_page_size_of_zero_never_reaches_the_view() -> None:
    """Prove a page size of zero becomes one.

    Why:
        The page prints the page size, and a later reader may divide by it. A
        zero would produce a wrong page count or a failure.
    """
    view = render.build_history_view(_StorePage(_capture_rows(2), total=2, limit=0, offset=0))
    assert view.page_size == 1


def test_a_bad_shape_never_reaches_the_view() -> None:
    """Prove a caller that hands nothing gets an empty view instead of a failure."""
    view = render.build_history_view(None)
    assert view.rows == ()
    assert view.total == 0
    assert view.has_next is False


# ---------------------------------------------------------------------------
# The counts
# ---------------------------------------------------------------------------


def test_the_row_reads_a_direct_count() -> None:
    """Prove a record that names both counts wins over any other source."""
    row = render.build_history_row(_capture_row("cap-1", device_count=12, client_count=44))
    assert row.device_count == 12
    assert row.client_count == 44


def test_a_zero_direct_count_gives_way_to_the_counts_map() -> None:
    """Prove a direct count of zero falls through to the counts map.

    Why:
        The two count readers test the direct value for truth, not for
        presence, so a zero written by a default fill never beats a real
        number. The store makes this shape unreachable today, because
        ``store.LIST_FIELDS`` projects ``counts`` and projects neither count
        name. A later release that projects a real ``device_count`` makes a
        true zero reachable, and truthiness would then hide it. This test
        fails on that day and names the rule to revisit.
    """
    counts = {"devices_total": 12, "clients_wired": 5, "clients_wireless": 2, "clients_guest": 1}
    row = render.build_history_row(_capture_row("cap-1", device_count=0, client_count=0, counts=counts))
    assert row.device_count == 12
    assert row.client_count == 8


def test_the_row_reads_the_counts_map_of_a_whole_document() -> None:
    """Prove a whole capture document answers with its counts map.

    Why:
        The store projection of contracts/http-api.md line 361 carries neither
        count. A caller that hands the whole document instead must still show a
        real number, and the three client groups add to one number.
    """
    counts = {"devices_total": 30, "clients_wired": 4, "clients_wireless": 9, "clients_guest": 2}
    row = render.build_history_row(_capture_row("cap-1", counts=counts))
    assert row.device_count == 30
    assert row.client_count == 15


def test_a_record_with_no_count_reads_zero() -> None:
    """Prove a record with no count anywhere reads zero and never raises."""
    row = render.build_history_row(_capture_row("cap-1"))
    assert row.device_count == 0
    assert row.client_count == 0


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------


def test_the_page_shows_the_table_and_every_row(environment: Environment) -> None:
    """Prove the page prints every identifier and every value of the view model.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view(_StorePage(_capture_rows(2), total=2, limit=25, offset=0))
    page = _render_page(environment, page_title="Capture history", site_name="Site A", history_view=view)
    assert 'data-testid="history-table"' in page
    assert 'data-testid="history-row-cap-0"' in page
    assert 'data-testid="history-open-cap-0"' in page
    assert 'href="/captures/cap-1"' in page
    assert "1.2 MB" in page


def test_the_page_shows_the_state_word_beside_the_color(environment: Environment) -> None:
    """Prove the state reaches the page as a word, not as a color alone.

    Why:
        WCAG 1.4.1 forbids color as the only signal. A badge class alone would
        leave a color-blind operator with no state.

    Args:
        environment: The Jinja environment.
    """
    rows = (_capture_row("cap-0", capture_status="partial"),)
    view = render.build_history_view(_StorePage(rows, total=1, limit=25, offset=0))
    page = _render_page(environment, history_view=view)
    assert 'class="portal-badge badge-partial">partial<' in page


def test_the_page_locks_the_previous_control_on_the_first_page(environment: Environment) -> None:
    """Prove the first page shows a locked previous control and an open next one.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view(_StorePage(_capture_rows(25), total=60, limit=25, offset=0))
    page = _squash(_render_page(environment, history_view=view))
    assert 'data-testid="history-page-previous" disabled' in page
    assert 'data-testid="history-page-next" href="/history?limit=25&amp;offset=25"' in page


def test_the_page_locks_the_next_control_on_the_last_page(environment: Environment) -> None:
    """Prove the last page shows a locked next control and an open previous one.

    Args:
        environment: The Jinja environment.
    """
    view = render.build_history_view(_StorePage(_capture_rows(10, 50), total=60, limit=25, offset=50))
    page = _squash(_render_page(environment, history_view=view))
    assert 'data-testid="history-page-next" disabled' in page
    assert 'data-testid="history-page-previous" href="/history?limit=25&amp;offset=25"' in page


def test_the_paging_controls_stay_on_every_page(environment: Environment) -> None:
    """Prove both identifiers appear once on the first page and on the last page.

    Why:
        Contract rule 6 asks a value to appear once for each page. A control
        that disappeared when it was locked would force a browser test to know
        which page it opened.

    Args:
        environment: The Jinja environment.
    """
    for offset in (0, 50):
        view = render.build_history_view(_StorePage(_capture_rows(10, offset), total=60, limit=25, offset=offset))
        page = _render_page(environment, history_view=view)
        assert page.count('data-testid="history-page-next"') == 1
        assert page.count('data-testid="history-page-previous"') == 1


def test_the_page_renders_with_no_context(environment: Environment) -> None:
    """Prove the page renders with no view model at all.

    Why:
        The environment uses the strict undefined type. A page that read a
        value without a default would raise here, and the operator would see a
        server fault instead of an empty table.

    Args:
        environment: The Jinja environment.
    """
    page = _render_page(environment)
    assert "The portal found no stored capture." in page
    assert page.count('data-testid="history-page-next"') == 1


def test_the_page_reaches_the_navigation_identifier(environment: Environment) -> None:
    """Prove the shared navigation still carries the history link.

    Why:
        The ``Shared`` section of contracts/ui-testids.md fixes ``nav-history``.
        That control lives in partials/nav.html, and this page includes it
        through the base page, so the render is the place that proves it arrives.

    Args:
        environment: The Jinja environment.
    """
    page = _render_page(environment)
    assert 'data-testid="nav-history"' in page


def _template_expressions() -> list[str]:
    """Return every Jinja expression of the history page, with no comment.

    Why:
        A Jinja comment holds prose, and prose holds a hyphen and a full stop.
        The rule scan must read the expressions only.

    Returns:
        The text of each expression.
    """
    source = (_TEMPLATE_ROOT / _TEMPLATE_NAME).read_text(encoding="utf-8")
    return _EXPRESSION_PATTERN.findall(_COMMENT_PATTERN.sub("", source))


def test_the_page_holds_no_rule() -> None:
    """Prove the page performs no arithmetic and no numeric comparison.

    Why:
        A template must never hold a rule, because a rule in a template needs a
        browser to test. Every number, every link, and every boolean of this
        page comes from build_history_view.
    """
    for expression in _template_expressions():
        for token in _RULE_TOKENS:
            assert token not in expression, f"{expression} holds {token!r}"


def test_the_page_holds_no_script() -> None:
    """Prove the page adds no script of its own.

    Why:
        The content security policy is 'self' only. The policy blocks an inline
        script, so a script tag on this page would fail in a browser and would
        pass every unit test.
    """
    source = (_TEMPLATE_ROOT / _TEMPLATE_NAME).read_text(encoding="utf-8")
    assert "<script" not in source
    assert "{% block scripts %}" not in source
    assert "style=" not in source
