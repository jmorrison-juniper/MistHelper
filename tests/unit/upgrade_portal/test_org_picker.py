"""The tests of the organization picker of the upgrade capture portal.

Why:
    ``contracts/http-api.md`` line 53 states that the picker "paginates and
    filters in the portal itself". Both halves of that sentence are rules, and
    a rule that lives in a template cannot be tested without a browser. These
    tests prove that the rules live in
    ``src.upgrade_portal.app.routes.select`` instead, and that the page only
    prints what ``build_org_view`` decided.

    The order of the two rules carries the whole point. The portal filters the
    privilege list first and cuts one page out of the matches second. A filter
    that ran after the paging would search one page and would hide every match
    that sits on a later page, so one test below pins that order directly.

    The last group renders the real template with Jinja and the strict
    undefined type. A page that needed a rule of its own would fail there,
    because the render receives a view model and nothing else.

    No test here opens a socket or reaches the Mist cloud. Every organization
    record is a literal, so no cloud session is needed at all.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from flask import Flask
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import select

# The repository root. This file sits at tests/unit/upgrade_portal/.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# The contract that fixes every test identifier of the portal.
_CONTRACT_PATH = _REPO_ROOT / "specs" / "1823-upgrade-capture-portal" / "contracts" / "ui-testids.md"

# The template folder of the portal, beside the routes package.
_TEMPLATE_ROOT = Path(select.__file__).resolve().parents[1] / "assets" / "templates"

# The page under test.
_TEMPLATE_NAME = "select/orgs.html"

# The path that `contracts/http-api.md` line 50 fixes for the picker.
_ORG_PATH = "/select/org"

# The expression delimiters of Jinja. A rule can hide in either one.
_EXPRESSION_PATTERN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)

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


def _org(org_id: str, name: str) -> dict[str, str]:
    """Return one organization record as ``permitted_orgs`` builds it.

    Args:
        org_id: The organization identifier.
        name: The organization name.

    Returns:
        The record, with the two fields the picker shows.
    """
    return {"org_id": org_id, "name": name}


def _many_orgs(count: int) -> list[dict[str, str]]:
    """Return a list of organizations, numbered and sorted by name.

    Why:
        Every paging test needs more rows than one page holds, and only the
        number changes between them. One builder keeps the tests short.

    Args:
        count: The number of records to build.

    Returns:
        The records, in name order.
    """
    return [_org(f"org-{index:03d}", f"Org {index:03d}") for index in range(count)]


def _names(view: select.OrgPickerView) -> list[str]:
    """Return the name of each row of one page.

    Args:
        view: The view model under test.

    Returns:
        One name for each row, in page order.
    """
    return [row["name"] for row in view.rows]


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset.

    Why:
        The base page asks ``url_for`` for its stylesheets and its scripts.
        Flask supplies that helper, and this test renders without Flask, so the
        environment needs a helper of its own.

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
        The page under test extends the real base page, so a stub loader would
        prove nothing. The strict undefined type turns a missing value into a
        failure instead of an empty string, which is the state this page claims
        in its own header comment.

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
    """Render the organization picker with the given context.

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
        test that read the raw text.

    Args:
        text: The rendered page.

    Returns:
        The page on one line.
    """
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------


def test_the_contract_holds_every_named_org_identifier() -> None:
    """Prove the contract file still names the three picker identifiers.

    Why:
        Every other test in this file compares against a value this module
        spells out. That proves the module is self-consistent and proves
        nothing about the contract. This test reads the contract itself, so a
        silent change to the contract fails here first.
    """
    contract = _CONTRACT_PATH.read_text(encoding="utf-8")
    for identifier in ("org-search", "org-row-{org_id}", "org-select-{org_id}"):
        assert f"`{identifier}`" in contract


def test_the_paging_identifiers_follow_the_contract_convention() -> None:
    """Prove the two paging identifiers copy the shape the contract already uses.

    Why:
        `contracts/ui-testids.md` names no paging control for the picker, so
        this page had to choose two names. The history page has the same two
        controls and the contract does name those, so the picker copies that
        spelling. One term for one concept keeps a browser test readable.
    """
    contract = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert "`history-page-next`" in contract
    assert "`history-page-previous`" in contract
    assert select.ORG_NEXT_TEST_ID == "org-page-next"
    assert select.ORG_PREVIOUS_TEST_ID == "org-page-previous"
    assert select.ORG_NEXT_TEST_ID.endswith("-page-next")
    assert select.ORG_PREVIOUS_TEST_ID.endswith("-page-previous")


def test_the_picker_holds_one_page_size() -> None:
    """Prove one constant states the page size, and states a usable number."""
    assert select.ORG_PAGE_SIZE == 25
    assert select.OrgPickerView().page_size == select.ORG_PAGE_SIZE


# ---------------------------------------------------------------------------
# The filter
# ---------------------------------------------------------------------------


def test_the_filter_matches_the_organization_name() -> None:
    """The filter keeps a row whose name holds the fragment."""
    rows = [_org("aaa", "Alpha Networks"), _org("bbb", "Zulu Networks")]
    assert select.filter_org_rows(rows, "alpha") == [rows[0]]


def test_the_filter_matches_the_organization_identifier() -> None:
    """The filter keeps a row whose identifier holds the fragment.

    Why:
        An operator often reads an organization identifier out of a support
        ticket and pastes it. A filter over the name alone would answer with an
        empty table and would read as a missing organization.
    """
    rows = [_org("aaa-111", "Alpha Networks"), _org("bbb-222", "Zulu Networks")]
    assert select.filter_org_rows(rows, "bbb-222") == [rows[1]]


def test_the_filter_ignores_the_letter_case() -> None:
    """The filter matches whatever case the operator typed."""
    rows = [_org("aaa", "Alpha Networks")]
    assert select.filter_org_rows(rows, "ALPHA") == rows


def test_an_empty_filter_keeps_every_row() -> None:
    """An empty filter and a filter of spaces both keep every row."""
    rows = _many_orgs(3)
    assert select.filter_org_rows(rows, "") == rows
    assert select.filter_org_rows(rows, "   ") == rows


def test_a_filter_that_matches_nothing_keeps_no_row() -> None:
    """A filter with no match answers an empty list, never every row."""
    assert select.filter_org_rows(_many_orgs(3), "no such organization") == []


def test_the_row_test_reads_a_missing_field_as_empty() -> None:
    """A record with no name and no identifier matches nothing and raises nothing.

    Why:
        The privilege list comes from the cloud, so a record may name neither
        field. A reader that indexed the record would raise and would take the
        whole picker down for one damaged privilege entry.
    """
    assert select.org_row_matches({}, "alpha") is False


# ---------------------------------------------------------------------------
# The paging
# ---------------------------------------------------------------------------


def test_a_short_list_fills_one_page_and_locks_both_controls() -> None:
    """A list shorter than one page shows every row and offers no other page."""
    view = select.build_org_view(_many_orgs(3), 0, "")
    assert view.total == 3
    assert len(view.rows) == 3
    assert view.has_next is False
    assert view.has_previous is False
    assert view.next_url == ""
    assert view.previous_url == ""


def test_the_first_page_holds_one_page_size_of_rows() -> None:
    """A long list arrives one page at a time, and the later page waits."""
    view = select.build_org_view(_many_orgs(60), 0, "")
    assert view.total == 60
    assert len(view.rows) == select.ORG_PAGE_SIZE
    assert _names(view)[0] == "Org 000"
    assert view.has_next is True
    assert view.has_previous is False


def test_the_middle_page_offers_both_controls() -> None:
    """A page with rows on each side of it offers both paging controls."""
    view = select.build_org_view(_many_orgs(60), 25, "")
    assert _names(view)[0] == "Org 025"
    assert view.has_next is True
    assert view.has_previous is True
    assert view.next_url == "/select/org?offset=50"
    assert view.previous_url == "/select/org?offset=0"


def test_the_last_page_locks_the_later_control() -> None:
    """The last page holds the remainder and offers no later page."""
    view = select.build_org_view(_many_orgs(60), 50, "")
    assert len(view.rows) == 10
    assert view.has_next is False
    assert view.next_url == ""
    assert view.has_previous is True


def test_an_offset_past_the_end_shows_an_empty_page() -> None:
    """A hand-edited link past the last row shows an empty page, not the far end.

    Why:
        A paging link is a path, so an operator may edit it. A slice with a
        start past the end must answer nothing. A start that wrapped around
        would show the first rows and would read as a portal that ignores the
        link.
    """
    view = select.build_org_view(_many_orgs(10), 500, "")
    assert view.rows == ()
    assert view.offset == 10
    assert view.has_next is False
    assert view.has_previous is True


def test_a_negative_offset_reads_as_the_first_page() -> None:
    """A link with a negative offset shows the first page."""
    view = select.build_org_view(_many_orgs(10), -5, "")
    assert view.offset == 0
    assert _names(view)[0] == "Org 000"
    assert view.has_previous is False


def test_the_second_page_steps_back_to_the_first_row() -> None:
    """The earlier link of the second page names the first row and not a negative one."""
    view = select.build_org_view(_many_orgs(30), 25, "")
    assert view.previous_url == "/select/org?offset=0"


# ---------------------------------------------------------------------------
# The filter and the paging together
# ---------------------------------------------------------------------------


def test_the_filter_runs_before_the_paging() -> None:
    """A match beyond the first page still reaches the operator.

    Why:
        This is the whole reason the filter lives in the portal. The browser
        script hides a row of the page on screen, so a browser filter alone
        would search the first 25 rows and would answer "no match" for an
        organization that sits at row 57.
    """
    rows = _many_orgs(60)
    unfiltered = select.build_org_view(rows, 0, "")
    assert "Org 057" not in _names(unfiltered)
    filtered = select.build_org_view(rows, 0, "Org 057")
    assert _names(filtered) == ["Org 057"]


def test_the_paging_counts_the_matches_and_not_the_whole_list() -> None:
    """The total and both controls count the rows the filter kept."""
    view = select.build_org_view(_many_orgs(60), 0, "Org 05")
    assert view.total == 10
    assert view.has_next is False
    assert view.has_previous is False


def test_a_filtered_list_still_pages() -> None:
    """A filter that keeps more rows than one page holds still pages."""
    view = select.build_org_view(_many_orgs(200), 0, "Org 1")
    assert view.total == 100
    assert len(view.rows) == select.ORG_PAGE_SIZE
    assert view.has_next is True


def test_a_paging_link_carries_the_filter() -> None:
    """Each paging path holds the filter text.

    Why:
        A link that dropped the filter would widen the list on the second page,
        and the operator would read that as a filter that stopped working.
    """
    view = select.build_org_view(_many_orgs(200), 25, "Org 1")
    assert "q=Org+1" in view.next_url
    assert "q=Org+1" in view.previous_url
    assert view.next_url.startswith(f"{_ORG_PATH}?")


def test_the_view_reports_the_filter_state() -> None:
    """The view states whether a filter ran, so the page picks its empty sentence.

    Why:
        The empty table shows one of two sentences. `query` is the only signal,
        so a companion boolean would repeat it and could disagree with it.
    """
    assert select.build_org_view(_many_orgs(3), 0, "").query == ""
    assert select.build_org_view(_many_orgs(3), 0, "zzz").query == "zzz"


def test_the_view_states_the_page_size() -> None:
    """The builder leaves the page size at the one constant the module holds."""
    assert select.build_org_view(_many_orgs(3), 0, "").page_size == select.ORG_PAGE_SIZE


# ---------------------------------------------------------------------------
# The paging path
# ---------------------------------------------------------------------------


def test_the_path_holds_the_contract_path() -> None:
    """Every paging path starts at the path the contract fixes."""
    assert select.org_page_url(25, "").startswith(f"{_ORG_PATH}?")


def test_the_path_omits_an_empty_filter() -> None:
    """A path with no filter carries the offset alone."""
    assert select.org_page_url(25, "") == "/select/org?offset=25"


def test_the_path_never_names_a_negative_row() -> None:
    """A negative offset reaches the path as the first row."""
    assert select.org_page_url(-40, "") == "/select/org?offset=0"


def test_the_path_escapes_the_filter_text() -> None:
    """A filter with a space and an ampersand reaches the path escaped.

    Why:
        An organization name holds a space, and a name may hold an ampersand.
        A raw ampersand would start a second query argument and would drop the
        rest of the filter.
    """
    built = select.org_page_url(0, "Acme & Sons")
    assert "q=Acme+%26+Sons" in built
    assert built.count("?") == 1


# ---------------------------------------------------------------------------
# The query reader
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", 0),
        ("?offset=25", 25),
        ("?offset=+7", 7),
        ("?offset=", 0),
        ("?offset=-5", 0),
        ("?offset=two", 0),
        ("?offset=2.5", 0),
        ("?offset=25%2C50", 0),
    ],
)
def test_the_reader_answers_a_whole_number_or_the_fallback(query: str, expected: int) -> None:
    """A damaged offset reads as the fallback and never reaches the slice.

    Args:
        query: The query string of the request.
        expected: The value the reader must answer.
    """
    app = Flask(__name__)
    with app.test_request_context(f"{_ORG_PATH}{query}"):
        assert select.read_whole_number("offset", 0) == expected


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------


def test_the_page_shows_one_row_for_each_organization(environment: Environment) -> None:
    """The page shows the row identifier of each organization of the page.

    Args:
        environment: The Jinja environment.
    """
    view = select.build_org_view([_org("aaa", "Alpha Networks"), _org("bbb", "Zulu Networks")], 0, "")
    page = _render_page(environment, org_view=view, organizations=view.rows)
    assert 'data-testid="org-row-aaa"' in page
    assert 'data-testid="org-select-bbb"' in page


def test_the_page_prints_the_filter_back_into_the_field(environment: Environment) -> None:
    """The search field holds the filter that produced the page.

    Why:
        The portal filters, so the page the operator reads is already narrowed.
        A field that came back empty would tell the operator that no filter
        ran, and the short list would then read as a missing organization.
    """
    view = select.build_org_view(_many_orgs(60), 0, "Org 05")
    squashed = _squash(_render_page(environment, org_view=view, organizations=view.rows))
    assert 'name="q" value="Org 05"' in squashed


def test_the_search_field_sits_in_a_get_form(environment: Environment) -> None:
    """The filter reaches the portal through a get form on the contract path.

    Why:
        The content security policy blocks an inline script, and the page must
        work with no script at all. A plain get form filters every page without
        one line of script.
    """
    squashed = _squash(_render_page(environment, org_view=select.build_org_view([], 0, "")))
    assert f'<form method="get" action="{_ORG_PATH}" role="search">' in squashed
    assert 'data-testid="org-search-submit"' in squashed


def test_the_later_control_is_a_link_when_a_later_page_exists(environment: Environment) -> None:
    """The later control carries the path when a later page exists.

    Args:
        environment: The Jinja environment.
    """
    view = select.build_org_view(_many_orgs(60), 0, "")
    squashed = _squash(_render_page(environment, org_view=view, organizations=view.rows))
    assert '<a class="portal-button" data-testid="org-page-next" href="/select/org?offset=25">' in squashed


def test_the_later_control_is_a_locked_button_on_the_last_page(environment: Environment) -> None:
    """The later control takes no press when no later page exists.

    Why:
        A link with no target still takes a press. A disabled button takes
        none, and the test identifier stays on the control in both states.
    """
    view = select.build_org_view(_many_orgs(3), 0, "")
    squashed = _squash(_render_page(environment, org_view=view, organizations=view.rows))
    assert '<button type="button" class="portal-button" data-testid="org-page-next" disabled>' in squashed


def test_the_earlier_control_is_a_locked_button_on_the_first_page(environment: Environment) -> None:
    """The earlier control takes no press on the first page.

    Args:
        environment: The Jinja environment.
    """
    view = select.build_org_view(_many_orgs(60), 0, "")
    squashed = _squash(_render_page(environment, org_view=view, organizations=view.rows))
    assert '<button type="button" class="portal-button" data-testid="org-page-previous" disabled>' in squashed


def test_the_earlier_control_is_a_link_on_the_second_page(environment: Environment) -> None:
    """The earlier control carries the path when an earlier page exists.

    Args:
        environment: The Jinja environment.
    """
    view = select.build_org_view(_many_orgs(60), 25, "")
    squashed = _squash(_render_page(environment, org_view=view, organizations=view.rows))
    assert '<a class="portal-button" data-testid="org-page-previous" href="/select/org?offset=0">' in squashed


def test_an_empty_scope_names_the_cause(environment: Environment) -> None:
    """An account that reaches no organization reads why, and what to do next."""
    page = _render_page(environment, org_view=select.build_org_view([], 0, ""))
    assert "This sign-in reaches no organization." in page


def test_an_empty_filter_result_names_the_filter(environment: Environment) -> None:
    """A filter with no match reads as a filter, never as a lost account.

    Why:
        Two causes reach an empty table, and the operator fixes only one of
        them. A page that showed the "ask an administrator" sentence after a
        typed filter would send the operator to the wrong person.
    """
    page = _render_page(environment, org_view=select.build_org_view(_many_orgs(5), 0, "zzz"))
    assert "No organization matches the filter." in page
    assert "This sign-in reaches no organization." not in page


def test_the_page_renders_with_the_row_list_alone(environment: Environment) -> None:
    """A caller that supplies no view model still gets a readable page.

    Why:
        The page states that every value passes a default filter first. The
        strict undefined type here proves that claim, because a missing name
        would raise instead of printing an empty string.
    """
    page = _render_page(environment, organizations=[_org("aaa", "Alpha Networks")])
    assert 'data-testid="org-row-aaa"' in page
    assert 'data-testid="org-page-next"' in page


def test_the_page_holds_no_rule() -> None:
    """Prove the page holds no arithmetic and no numeric comparison.

    Why:
        The paging is the clearest case. A page that compared the offset with
        the total would hold the rule, and no unit test could reach it.
    """
    source = (_TEMPLATE_ROOT / _TEMPLATE_NAME).read_text(encoding="utf-8")
    for expression in _EXPRESSION_PATTERN.findall(source):
        for token in _RULE_TOKENS:
            assert token not in expression, f"{expression} holds {token!r}."


def test_the_page_holds_no_script() -> None:
    """Prove the page adds no script of its own.

    Why:
        The content security policy is 'self' only. The policy blocks an inline
        script and the style attribute, so either one would fail in a browser
        and would pass every unit test.
    """
    source = (_TEMPLATE_ROOT / _TEMPLATE_NAME).read_text(encoding="utf-8")
    assert "<script" not in source
    assert "{% block scripts %}" not in source
    assert "style=" not in source
