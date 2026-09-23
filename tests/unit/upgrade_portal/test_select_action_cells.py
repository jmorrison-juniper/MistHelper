"""The tests of the action cells of the organization table and the site table.

Why:
    Issue #3278 reports that at a width of 390 pixels the Choose, Open, and
    Select labels break into groups of letters. The shared cell rule of
    ``portal.css`` lets a word break at any letter, and a control inherits that
    rule. The repair puts the ``cell-control`` class on each action cell, and
    one stylesheet rule stops that cell from wrapping.

    Two parts hold the repair, and each part needs a test. The tests below
    render the real templates with Jinja and read the cell that holds each
    control. They also read the rule text of ``portal.css``. A stylesheet rule
    cannot run in a unit test, so
    ``tests/e2e/upgrade_portal/test_narrow_action_cells.py`` measures the
    painted label in a real browser.

    The site table serves two modes. The single-site mode shows an Open button,
    and the multi-site mode shows a check box with a Select label. Both modes
    must keep the label on one line, so both modes have a test.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import select

# The asset folder of the portal, beside the routes package. The template
# folder and the stylesheet both sit below it, so one anchor finds each of them.
_ASSET_ROOT = Path(select.__file__).resolve().parents[1] / "assets"
_TEMPLATE_ROOT = _ASSET_ROOT / "templates"
_STYLESHEET = _ASSET_ROOT / "static" / "css" / "portal.css"

# The class that stops a control cell from wrapping.
_CONTROL_CLASS = "cell-control"

# The selector of the stylesheet rule that carries the repair.
_CONTROL_SELECTOR = ".portal-table .cell-control"

# Two sample rows for each table. Two rows prove that every row carries the
# class, and not only the first row.
_ORGS = ({"org_id": "org-a", "name": "Alpha Networks"}, {"org_id": "org-b", "name": "Zulu Networks"})
_SITES = (
    {"site_id": "site-a", "name": "Branch A", "device_count": 4, "lock_state": "free"},
    {"site_id": "site-b", "name": "Branch B", "device_count": 9, "lock_state": "locked", "locked_by": "op@example.com"},
)

# Each page, the context that renders it, and the test identifier of each
# control in its action column.
_PAGES: dict[str, tuple[str, dict[str, Any], tuple[str, ...]]] = {
    "organization table": (
        "select/orgs.html",
        {"organizations": list(_ORGS)},
        ("org-select-org-a", "org-select-org-b"),
    ),
    "site table, single-site mode": (
        "select/sites.html",
        {"sites": list(_SITES), "selected_mode": "single_site"},
        ("site-open-site-a", "site-open-site-b"),
    ),
    "site table, multi-site mode": (
        "select/sites.html",
        {"sites": list(_SITES), "selected_mode": "multi_site"},
        ("site-select-site-a", "site-select-site-b"),
    ),
}


class _CellClassReader(HTMLParser):
    """Record the class names of the table cell that holds each identified element.

    Why:
        A search of the page text would pass when the class sat on a different
        cell. This reader ties each control to the one cell that holds it.

    Attributes:
        found: The test identifier of each element inside a cell, and the class
            names of that cell.
    """

    def __init__(self) -> None:
        """Start with no open cell and no recorded element."""
        super().__init__()
        self.found: dict[str, tuple[str, ...]] = {}  # One entry for each identified element inside a cell.
        self._cell_classes: tuple[str, ...] | None = None  # None while the reader stands outside a cell.

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Open a cell, or record an identified element inside the open cell.

        Args:
            tag: The element name.
            attrs: The attribute names and values of the element.
        """
        values = dict(attrs)  # One lookup table for the attributes of this element.
        if tag == "td":  # A new cell starts, so its class names apply to every child.
            self._cell_classes = tuple((values.get("class") or "").split())
        test_id = values.get("data-testid")  # The stable name of a control, if the element has one.
        if test_id and self._cell_classes is not None:  # Only an element inside a cell is recorded.
            self.found[test_id] = self._cell_classes

    def handle_endtag(self, tag: str) -> None:
        """Close the open cell.

        Args:
            tag: The element name.
        """
        if tag == "td":  # The cell ends, so the next element stands outside any cell.
            self._cell_classes = None


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset.

    Why:
        The base page asks ``url_for`` for its stylesheets and its scripts.
        Flask supplies that helper, and this test renders without Flask.

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
        The pages extend the real base page, so a stub loader would prove
        nothing. The strict undefined type turns a missing value into a failure.

    Returns:
        The environment.
    """
    built = Environment(loader=FileSystemLoader(str(_TEMPLATE_ROOT)), autoescape=True, undefined=StrictUndefined)
    built.globals["url_for"] = _static_url  # Flask supplies this name in production.
    built.globals["request"] = None  # The navigation partial reads this name.
    return built


def _declarations(selector: str) -> dict[str, str]:
    """Return the declarations of one stylesheet rule as a name and value table.

    Why:
        A search of the whole file would pass when the declaration sat under a
        different selector. This helper reads the one rule alone.

    Args:
        selector: The exact selector text, with no brace.

    Returns:
        The property name and the value of each declaration. The table is empty
        when the stylesheet holds no such rule.
    """
    text = _STYLESHEET.read_text(encoding="utf-8")  # The real stylesheet that the portal serves.
    found = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", text)  # The first rule with this exact selector.
    if found is None:  # No rule means no declaration.
        return {}
    pairs = (part.split(":", 1) for part in found.group(1).split(";") if ":" in part)  # Each "name: value" part.
    return {name.strip(): value.strip() for name, value in pairs}


@pytest.mark.parametrize("page_name", sorted(_PAGES))
def test_each_action_control_sits_in_a_control_cell(environment: Environment, page_name: str) -> None:
    """Prove that every control of the action column sits in a control cell.

    Why:
        The stylesheet rule reaches a cell only through the class. A cell with
        no class keeps the shared rule, and the label breaks again.

    Args:
        environment: The Jinja environment.
        page_name: The page and the mode under test.
    """
    template_name, context, test_ids = _PAGES[page_name]
    reader = _CellClassReader()
    reader.feed(environment.get_template(template_name).render(**context, theme="default"))
    assert {test_id: reader.found.get(test_id) for test_id in test_ids} == dict.fromkeys(test_ids, (_CONTROL_CLASS,))


def test_the_control_cell_never_wraps() -> None:
    """Prove that the stylesheet stops a control cell from wrapping.

    Why:
        Issue #3278 shows each label as groups of letters. A cell that never
        wraps cannot break a label.
    """
    assert _declarations(_CONTROL_SELECTOR) == {"white-space": "nowrap"}
