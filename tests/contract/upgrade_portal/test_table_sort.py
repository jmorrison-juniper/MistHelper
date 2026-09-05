"""Contract tests for the table sort of issue #2027.

Why:
    No table of the upgrade capture portal ordered its rows. Every table
    rendered in the order that the cloud returned, and the cloud promises
    nothing about that order. An operator who reads a device table to decide
    what to upgrade could not group the devices that run an old version, the
    devices that are offline, or the devices that a naming convention already
    groups.

    A missed device is the fault that this whole feature exists to catch, so an
    operator who cannot order the list is more likely to miss one.

Scope:
    The markup and the script alone. The browser behavior of the sort belongs
    to a browser test, because a contract test runs no script.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import pathlib  # The test reads the template tree and the script.

# The templates and the script of the portal, found from this file.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TEMPLATE_ROOT = REPO_ROOT / "src/upgrade_portal/app/assets/templates"
SCRIPT_PATH = REPO_ROOT / "src/upgrade_portal/app/assets/static/js/portal.js"

# ---------------------------------------------------------------------------
# Issue #2027: every table offers a sort on every column
# ---------------------------------------------------------------------------

SORTABLE_TABLES = (
    "capture-device-table",
    "capture-client-wired-table",
    "capture-client-wireless-table",
    "compare-device-table",
    "compare-client-table",
    "history-table",
    "history-run-table",  # Issue #2199 added the runs section of the history page.
    "history-audit-table",  # Issue #2221 added the audit log of the history page.
    "inventory-table",
    "site-table",  # Issue #2227 added the one table that never sorted.
    "upgrade-target-table",
    "upgrade-run-table",
)


def test_every_table_of_the_portal_offers_a_sort() -> None:
    """No table ordered its rows, so every table followed the cloud answer.

    Why:
        An operator reads a device table to decide what to upgrade. Three
        questions need an order, and none of them can be answered by reading
        down an unordered list of 200 rows. A missed device is the fault that
        this whole feature exists to catch. Issue #2027 holds that report.
    """
    marked = {name for name in SORTABLE_TABLES if table_is_sortable(name)}
    assert marked == set(SORTABLE_TABLES), sorted(set(SORTABLE_TABLES) - marked)


def test_a_column_that_holds_a_control_offers_no_order() -> None:
    """An action column holds a button, so an order of those cells means nothing."""
    for name, label in (("review/history.html", "Action"), ("upgrade/options.html", "Target version")):
        markup = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
        assert f'<th scope="col" data-no-sort>{label}</th>' in markup, name


def test_the_sort_engine_names_every_state_of_aria_sort() -> None:
    """A screen reader reads the state from aria-sort, so all three values exist."""
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    for value in ('SORT_NONE = "none"', 'SORT_ASCENDING = "ascending"', 'SORT_DESCENDING = "descending"'):
        assert value in script, value


def test_the_sort_state_reads_without_color() -> None:
    """A reader who cannot tell two colors apart still reads the order."""
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "SORT_ARROWS" in script  # A shape names each state.
    assert "arrow.textContent = SORT_ARROWS[own]" in script  # The shape reaches the cell.


def test_a_sort_control_answers_the_keyboard() -> None:
    """The button role promises the Enter key and the Space key, so both work."""
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    assert 'header.setAttribute("tabindex", "0")' in script  # A keyboard reaches the control.
    assert 'event.key === "Enter"' in script  # The Enter key sorts.
    assert 'event.key === " "' in script  # The Space key sorts.


def test_a_paged_table_states_that_it_sorts_the_page_alone() -> None:
    """A browser sort orders the rows on screen, so a paged table names that limit.

    Why:
        An operator who sorted a paged table and read the first row as the
        smallest value of the whole list would read a false answer.
    """
    markup = (TEMPLATE_ROOT / "review/history.html").read_text(encoding="utf-8")
    assert 'data-testid="history-sort-scope"' in markup  # The note renders.
    assert "orders the rows of this page" in markup  # The note states the limit.


def table_is_sortable(test_id: str) -> bool:
    """Answer whether the named table carries the sort attribute.

    Args:
        test_id: The stable identifier of the table.

    Returns:
        True when one template marks that table as sortable.
    """
    for path in TEMPLATE_ROOT.rglob("*.html"):
        markup = path.read_text(encoding="utf-8")
        marker = f'data-testid="{test_id}"'
        if marker not in markup:
            continue
        opening = markup.split(marker)[0].rsplit("<table", 1)[-1] + markup.split(marker)[1].split(">")[0]
        if "data-sortable" in opening:
            return True
    return False
