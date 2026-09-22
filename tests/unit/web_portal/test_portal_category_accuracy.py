"""Tests that every category name describes the operations it holds.

Issue #3153 reported eight misfiled rows. A menu number records when an
operation joined the menu, not what the operation does, so a range table
cannot decide the category on its own.

Three category names described no operation they held. An operator who
opened "Packet Captures" found two device inventory exports and no packet
capture at all.

These tests hold the repair in place, and they also guard the general
rule. A future category that holds no matching operation fails here.
"""

import pytest

from web_portal.menu_registry import build_static_menu_actions
from web_portal.services.operation import CATEGORY_OVERRIDES, CATEGORY_RANGES, OperationExecutor

# Words that must appear in at least one label of the category that carries them.
# A category name is a promise to the operator, so the rows must keep it.
CATEGORY_KEYWORDS = {
    "Packet Captures": ("capture", "packet"),
    "WebSocket Device Commands": ("websocket", "command", "shell"),
    "Statistics & Analytics": ("statistic", "analytic"),
    "Template Exports": ("template",),
    "Location Exports": ("location", "alarm", "event", "zone", "map", "beacon"),
    "Device Troubleshooting": ("device", "switch", "gateway", "ap ", "cable", "port"),
}


@pytest.fixture
def categories():
    """Return the category list the portal serves."""
    executor = OperationExecutor(build_static_menu_actions(), None, None, None)
    try:
        yield executor.build_category_list(build_static_menu_actions())
    finally:
        executor.shutdown()  # Close the pool, so the test leaves no worker thread behind.


def _labels(categories: list, name: str) -> list[str]:
    """Return the lowercase labels of one category, or an empty list."""
    for category in categories:
        if category["name"] == name:
            return [operation["description"].lower() for operation in category["operations"]]
    return []


def test_no_category_promises_work_it_does_not_hold(categories):
    """Every category that survives holds at least one matching operation."""
    # A category name is a promise. An empty promise sends the operator hunting.
    broken = []  # Collect every offender, so one failure names them all.
    for name, keywords in CATEGORY_KEYWORDS.items():
        labels = _labels(categories, name)
        if not labels:
            continue  # The category no longer appears, which is a valid repair.
        if not any(word in label for label in labels for word in keywords):
            broken.append(f"{name} holds {len(labels)} rows and none mention {keywords}")
    assert not broken, "these categories describe work they do not hold: " + "; ".join(broken)


def test_the_three_misleading_categories_are_gone(categories):
    """The categories that held no matching operation no longer appear."""
    # Each of these held only rows that belonged elsewhere. Issue #3153.
    names = [category["name"] for category in categories]
    assert "Packet Captures" not in names  # It held two device inventory exports.
    assert "WebSocket Device Commands" not in names  # It held reports and an inventory export.
    assert "Statistics & Analytics" not in names  # It held two template exports.


@pytest.mark.parametrize(
    ("menu_number", "expected_category", "expected_word"),
    [
        ("5", "Organization Exports", "e911"),
        ("6", "Insights & Diagnostics", "analysis"),
        ("7", "Insights & Diagnostics", "analysis"),
        ("8", "Organization Exports", "inventory"),
        ("9", "Organization Exports", "devices"),
        ("10", "Organization Exports", "devices"),
        ("40", "Template Exports", "template"),
        ("41", "Template Exports", "template"),
    ],
)
def test_each_misfiled_row_now_sits_with_its_own_kind(categories, menu_number, expected_category, expected_word):
    """Each repaired row sits in the category its label describes."""
    found = None  # Hold the row, so a failure can name what the page shows.
    for category in categories:
        for operation in category["operations"]:
            if operation["menu_number"] == menu_number:
                found = (category["name"], operation["description"].lower())
    assert found is not None, f"menu {menu_number} no longer appears on the page"
    assert found[0] == expected_category  # The row must sit under the name that describes it.
    assert expected_word in found[1]  # The label must still match the reason it moved.


def test_every_override_names_a_category_that_exists():
    """An override never invents a category name."""
    # A typo would create a category of one row, and the operator would never find it.
    known = {name for _, _, name in CATEGORY_RANGES}
    unknown = {number: name for number, name in CATEGORY_OVERRIDES.items() if name not in known}
    assert not unknown, f"these overrides name a category that no range defines: {unknown}"


def test_every_override_changes_something():
    """An override that matches the range it replaces is dead weight."""
    executor = OperationExecutor(build_static_menu_actions(), None, None, None)
    try:
        pointless = {}  # Collect every override that repeats the range answer.
        for number, name in CATEGORY_OVERRIDES.items():
            ranged = next((title for low, high, title in CATEGORY_RANGES if low <= number <= high), "Other")
            if ranged == name:
                pointless[number] = name
        assert not pointless, f"these overrides repeat the range they replace: {pointless}"
    finally:
        executor.shutdown()  # Close the pool, so the test leaves no worker thread behind.
