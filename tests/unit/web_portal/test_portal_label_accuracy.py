"""Guard the operation labels against wrong counts and internal tracking numbers.

Issue #3219: menu 236 promised "32 operations", and its chooser offered 33. A
count that someone types by hand drifts the moment its table changes. Fourteen
labels also showed internal numbers such as "issue #1802" to the operator.

The labels live in two sources that must agree: the ``MenuEntry`` titles in
``MistHelper.py``, which the command line prints, and ``MENU_DESCRIPTIONS`` in
``web_portal/menu_registry.py``, which the portal renders. These tests read both.
"""

import ast
import re
from pathlib import Path

import pytest

from src.export import count_exporter, endpoint_family_exporter, simple_endpoint_exporter
from web_portal.menu_registry import MENU_DESCRIPTIONS

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

# Each chooser row, and the table that its chooser prints. A label that
# promises a count must name the length of this table.
CHOOSER_TABLES = {
    "235": count_exporter._ORG_OPS,
    "236": count_exporter._SITE_OPS,
    "237": count_exporter._MSP_OPS,
    "259": simple_endpoint_exporter._NONE_OPS,
    "260": simple_endpoint_exporter._ORG_OPS,
    "261": simple_endpoint_exporter._SITE_OPS,
    "262": simple_endpoint_exporter._MSP_OPS,
    "263": endpoint_family_exporter._SITE_SLE_OPS,
    "264": endpoint_family_exporter._SITE_MAP_OPS,
    "265": endpoint_family_exporter._SITE_DETAIL_OPS,
    "266": endpoint_family_exporter._ORG_DETAIL_OPS,
    "267": endpoint_family_exporter._MSP_DETAIL_OPS,
    "268": endpoint_family_exporter._OTHER_DETAIL_OPS,
}

PROMISED_COUNT = re.compile(r"\((\d+) operations\)")  # The form each chooser label uses.
TRACKING_NUMBER = re.compile(r"issue #\d+|spec \d+|#\d{3,}", re.IGNORECASE)  # Numbers an operator cannot use.


def _cli_titles() -> dict[str, str]:
    """Return the title of each MenuEntry in MistHelper.py, read without an import."""
    tree = ast.parse((REPOSITORY_ROOT / "MistHelper.py").read_text(encoding="utf-8"))
    titles: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "MenuEntry":
            fields = {keyword.arg: keyword.value for keyword in node.keywords}
            menu = fields.get("menu_id")
            title = fields.get("title")
            if isinstance(menu, ast.Constant) and title is not None:
                titles[str(menu.value)] = ast.literal_eval(title)
    return titles


CLI_TITLES = _cli_titles()
LABEL_SOURCES = {"portal": MENU_DESCRIPTIONS, "command line": CLI_TITLES}


def test_both_label_sources_were_read():
    """The guards below mean something only when both sources hold real rows."""
    # Measured on 2026-09-23: the portal renders 165 labels, one for each row it
    # runs, and MistHelper.py names every menu row. Each floor sits under its
    # measurement, so a broken read fails here instead of passing over nothing.
    assert len(MENU_DESCRIPTIONS) >= 160, f"the portal source held only {len(MENU_DESCRIPTIONS)} labels"
    assert len(CLI_TITLES) >= 250, f"the MistHelper.py parse found only {len(CLI_TITLES)} titles"


@pytest.mark.parametrize("source_name", sorted(LABEL_SOURCES))
@pytest.mark.parametrize("menu", sorted(CHOOSER_TABLES, key=int))
def test_each_promised_count_matches_its_chooser_table(source_name, menu):
    """A label that promises N operations must offer exactly N."""
    label = LABEL_SOURCES[source_name].get(menu, "")
    match = PROMISED_COUNT.search(label)
    promised = int(match.group(1)) if match else None  # None marks a label that names no count at all.
    real = len(CHOOSER_TABLES[menu])
    assert promised == real, (
        f"the {source_name} label of menu {menu} promises {promised} operations, "
        f"and its chooser offers {real}: {label!r}"
    )


@pytest.mark.parametrize("source_name", sorted(LABEL_SOURCES))
def test_every_label_that_promises_a_count_has_a_known_table(source_name):
    """A new chooser row cannot promise a count that no guard compares."""
    unguarded = {
        menu: label
        for menu, label in LABEL_SOURCES[source_name].items()
        if PROMISED_COUNT.search(label) and menu not in CHOOSER_TABLES
    }
    assert unguarded == {}, f"these {source_name} labels promise a count that no table backs: {unguarded}"


@pytest.mark.parametrize("source_name", sorted(LABEL_SOURCES))
def test_no_label_shows_an_internal_tracking_number(source_name):
    """An operator cannot use an issue number or a spec number."""
    exposed = {menu: label for menu, label in LABEL_SOURCES[source_name].items() if TRACKING_NUMBER.search(label)}
    assert exposed == {}, f"these {source_name} labels show an internal tracking number: {exposed}"
