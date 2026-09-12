"""Proof that the three upgrade pages name the site in words.

Why:
    The options page, the confirmation page, and the run page each lead to a
    firmware write. A junior network operations engineer reads one of those
    pages, types the word CONFIRM, and changes production hardware. The one
    field that names the target must therefore read as words.

    Issue #2100 records the defect. Each of the three pages showed a 36
    character identifier and showed no name. The site picker, the inventory
    page, and the comparison page all showed the name, so the three pages that
    lead to a write were the only pages an operator could not read at a glance.
    FR-072 lets one operator drive up to six sites at one time, so that operator
    had to match six identifiers by eye.

    Each page still shows the identifier, because an operator quotes the
    identifier in a support case. A run whose stored name is empty falls back to
    the identifier, so no page ever shows a blank field.

    These tests render the real templates with the strict undefined type, so a
    missing value fails the test instead of writing an empty string.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import upgrade

# WHY: This file sits at tests/unit/upgrade_portal, so the repository root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# WHY: The real template folder. A stub loader would prove nothing about the shipped pages.
_TEMPLATE_ROOT = _REPO_ROOT / "src" / "upgrade_portal" / "app" / "assets" / "templates"

# WHY: The contract that fixes every test identifier of the portal.
_CONTRACT_PATH = _REPO_ROOT / "specs" / "1823-upgrade-capture-portal" / "contracts" / "ui-testids.md"

# WHY: The exact pair that issue #2100 reports from a live portal.
_SITE_ID = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"
_SITE_NAME = "Morrison House Site"

# WHY: The two test identifiers that this change adds to the three pages.
_NAME_TESTID = "upgrade-site-name"
_ID_TESTID = "upgrade-site-id"

# WHY: The three pages that lead to a firmware write.
_PAGES = ("upgrade/options.html", "upgrade/confirm.html", "upgrade/progress.html")

# WHY: The six values that partials/lock_banner.html names in its own header.
_LOCK_CONTEXT: dict[str, Any] = {
    "lock_state": "free",
    "lock_holder": "",
    "lock_cooldown": 0,
    "lock_token": "",
    "lock_confirm_word": "CONFIRM",
}

# WHY: The values each page needs beside the shared ones. A missing value raises under StrictUndefined.
_PAGE_CONTEXT: dict[str, dict[str, Any]] = {
    "upgrade/options.html": {"targets": [], "versions_by_model": {}, "warnings": [], **_LOCK_CONTEXT},
    "upgrade/confirm.html": {"targets": [], "pre_capture_id": "", "pre_capture_verified": False},
    "upgrade/progress.html": {
        "status": {},
        "poll_interval_seconds": 30,
        "stop_outcome": None,
        "stop_available": True,
        **_LOCK_CONTEXT,
    },
}

# WHY: One element that carries a test identifier. No page nests a `p` in a `p` or a `dd` in a `dd`,
# so the matching close tag of the same name always ends the element.
_ELEMENT = r'<(?P<tag>[a-z]+)[^>]*data-testid="{0}"[^>]*>(?P<body>.*?)</(?P=tag)>'

# WHY: Any HTML tag. The assertions read the words an operator reads, never the markup around them.
_TAG = re.compile(r"<[^>]*>")


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset.

    Why:
        The base page asks ``url_for`` for three stylesheets and two scripts.
        Flask supplies that helper, and this render has no Flask.

    Args:
        endpoint: The endpoint name. Always ``static`` on these pages.
        **values: The endpoint arguments. Holds ``filename``.

    Returns:
        A path that stands in for the real asset path.
    """
    return f"/{endpoint}/{values.get('filename', '')}"  # WHY: The tests never read this value.


@pytest.fixture(scope="module")
def environment() -> Environment:
    """Return a Jinja environment that loads the real portal templates.

    Why:
        Each page under test extends the real base page and includes the real
        navigation. The strict undefined type turns a missing value into a
        failure, which is the state the portal itself runs in.

    Returns:
        The environment.
    """
    built = Environment(  # WHY: The next argument turns escaping on for every render.
        loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    built.globals["url_for"] = _static_url  # WHY: Flask supplies this name, and this render has no Flask.
    built.globals["request"] = None  # WHY: The navigation partial reads this name.
    return built


def _context(page: str, **overrides: Any) -> dict[str, Any]:
    """Return the full render context of one upgrade page.

    Args:
        page: The template name.
        **overrides: The values this test replaces.

    Returns:
        Every value the page reads.
    """
    shared: dict[str, Any] = {"run_id": "run-2100", "options": {}}  # WHY: Both values reach all three pages.
    labels = upgrade.site_labels({"site_id": _SITE_ID, "site_name": _SITE_NAME})  # WHY: The route owns the rule.
    return {**shared, **labels, **_PAGE_CONTEXT[page], **overrides}  # WHY: A test value beats a default.


def _render(environment: Environment, page: str, **overrides: Any) -> str:
    """Render one upgrade page.

    Args:
        environment: The Jinja environment.
        page: The template name.
        **overrides: The values this test replaces.

    Returns:
        The rendered page.
    """
    return environment.get_template(page).render(**_context(page, **overrides))  # WHY: The real page text.


def _field(page_text: str, testid: str) -> str:
    """Return the words inside the element that carries one test identifier.

    Args:
        page_text: The rendered page.
        testid: The test identifier of the element.

    Returns:
        The visible words of that element, with every run of white space squashed.
    """
    found = re.search(_ELEMENT.format(testid), page_text, re.DOTALL)  # WHY: The one element of that identifier.
    assert found is not None, f"The page holds no element with the test identifier {testid}."
    return " ".join(_TAG.sub(" ", found.group("body")).split())  # WHY: An operator reads the words, not the markup.


@pytest.mark.parametrize("page", _PAGES)
def test_each_upgrade_page_names_the_site_in_words(environment: Environment, page: str) -> None:
    """Each page that leads to a firmware write names the site in words.

    Why:
        This is the defect of issue #2100. A name makes a wrong-site upgrade
        obvious to a reader. A 36 character identifier does not.
    """
    assert _SITE_NAME in _field(_render(environment, page), _NAME_TESTID)  # The words, on the page itself.


@pytest.mark.parametrize("page", _PAGES)
def test_each_upgrade_page_still_shows_the_site_identifier(environment: Environment, page: str) -> None:
    """Each page still shows the site identifier beside the name.

    Why:
        An operator quotes the identifier in a support case. A page that showed
        the name alone would take that value away.
    """
    assert _SITE_ID in _field(_render(environment, page), _ID_TESTID)  # The identifier keeps its own field.


@pytest.mark.parametrize("page", _PAGES)
def test_each_upgrade_page_shows_one_site_identifier_field(environment: Environment, page: str) -> None:
    """Each page carries each new test identifier one time.

    Why:
        The run page includes the stop control. A second element with the same
        test identifier would break a browser test that selects one element.
    """
    text = _render(environment, page)  # WHY: The whole page, with every partial it includes.
    assert text.count(f'data-testid="{_NAME_TESTID}"') == 1  # One name field for each page.
    assert text.count(f'data-testid="{_ID_TESTID}"') == 1  # One identifier field for each page.


@pytest.mark.parametrize("page", _PAGES)
def test_an_empty_stored_name_shows_the_identifier_and_no_blank_field(environment: Environment, page: str) -> None:
    """A run with an empty stored name falls back to the identifier.

    Why:
        An older run and a failed cloud read both leave the stored name empty.
        A blank field would tell the operator nothing about the target.
    """
    labels = upgrade.site_labels({"site_id": _SITE_ID, "site_name": ""})  # WHY: The state of an older run.
    text = _render(environment, page, **labels)  # WHY: The page reads exactly what the route sends.
    assert _field(text, _NAME_TESTID) == _SITE_ID  # The name field falls back, and never reads as blank.
    assert _field(text, _ID_TESTID) == _SITE_ID  # The identifier field keeps its own value.


def test_site_labels_reads_the_name_and_the_identifier_from_the_run_record() -> None:
    """The route helper reports both values of one run record."""
    labels = upgrade.site_labels({"site_id": _SITE_ID, "site_name": _SITE_NAME})  # WHY: A healthy run record.
    assert labels == {"site_name": _SITE_NAME, "site_id": _SITE_ID}  # Two names, and no third value.


def test_site_labels_falls_back_to_the_identifier() -> None:
    """An empty stored name reads as the identifier, and never as an empty string."""
    assert upgrade.site_labels({"site_id": _SITE_ID})["site_name"] == _SITE_ID  # A record with no name at all.
    assert upgrade.site_labels({"site_id": _SITE_ID, "site_name": "   "})["site_name"] == _SITE_ID  # Only spaces.


def test_site_labels_survives_a_record_with_no_site() -> None:
    """An absent run renders a page instead of a fault.

    Why:
        `run_page` loads an empty record for a run the store does not hold. The
        helper must answer that record, because the page still renders.
    """
    assert upgrade.site_labels({}) == {"site_name": "", "site_id": ""}  # Both fields stay empty, and none raises.


def test_a_new_run_reads_the_site_name_from_the_cloud(monkeypatch: pytest.MonkeyPatch) -> None:
    """The create call names the site in words when the body carries no name.

    Why:
        This is the root cause of issue #2100. The site picker stores the site
        identifier alone, and the create call sends no name. The run record then
        held the identifier in its name field, and every later page showed it.
    """
    monkeypatch.setattr(upgrade, "find_site", lambda site, org: {"id": site, "name": _SITE_NAME})
    assert upgrade.readable_site_name("org-1", _SITE_ID, "") == _SITE_NAME  # The cloud answers the name.


def test_a_given_site_name_beats_the_cloud_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """A name in the create body wins, and the portal reads no cloud.

    Why:
        The create call runs while an operator waits. A read the portal does not
        need costs that operator time.
    """
    monkeypatch.setattr(upgrade, "find_site", _refuse_site_read)  # WHY: Any call here fails the test.
    assert upgrade.readable_site_name("org-1", _SITE_ID, "Given name") == "Given name"  # The body wins.


def test_a_silent_cloud_leaves_the_identifier_in_the_name_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cloud that refuses the read still creates the run.

    Why:
        A refused read must never stop a run. The identifier is a poor name, and
        it beats a create call that fails while an operator waits.
    """
    monkeypatch.setattr(upgrade, "find_site", _raise_site_read)  # WHY: The cloud refuses and times out.
    assert upgrade.readable_site_name("org-1", _SITE_ID, "") == _SITE_ID  # The identifier stands in.


def test_an_unknown_site_leaves_the_identifier_in_the_name_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """A site the organization does not hold still creates the run."""
    monkeypatch.setattr(upgrade, "find_site", lambda site, org: None)  # WHY: No such site in this organization.
    assert upgrade.readable_site_name("org-1", _SITE_ID, "") == _SITE_ID  # The identifier stands in.


def test_the_contract_names_the_two_site_test_identifiers() -> None:
    """The contract file names both new test identifiers.

    Why:
        contracts/ui-testids.md fixes every identifier a browser test selects. A
        page that carried an identifier the contract does not name would let the
        two files drift.
    """
    contract = _CONTRACT_PATH.read_text(encoding="utf-8")  # WHY: The contract is prose, so it keeps its comments.
    assert f"`{_NAME_TESTID}`" in contract  # The name field of the three pages.
    assert f"`{_ID_TESTID}`" in contract  # The identifier field of the three pages.


def _refuse_site_read(site_id: str, org_id: str) -> dict[str, Any]:
    """Fail the test when the create call reads the cloud it does not need.

    Args:
        site_id: The site the call named.
        org_id: The organization the call named.

    Raises:
        AssertionError: Always, because no call may reach this function.
    """
    raise AssertionError(f"The create call read the cloud for site {site_id} of organization {org_id}.")


def _raise_site_read(site_id: str, org_id: str) -> dict[str, Any]:
    """Stand in for a cloud that refuses the site read.

    Args:
        site_id: The site the call named.
        org_id: The organization the call named.

    Raises:
        RuntimeError: Always, which is the state a timed-out cloud read reaches.
    """
    raise RuntimeError(f"The cloud refused the site read of {site_id} in {org_id}.")
