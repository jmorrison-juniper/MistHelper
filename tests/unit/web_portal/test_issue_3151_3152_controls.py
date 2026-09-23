"""Tests for operations portal controls added for issues 3151 and 3152."""

from __future__ import annotations

from web_portal.services.operation import PARAMETER_REGISTRY


CHECKED_MENU_COUNT = 15
REQUIRED_CONTROL_MENUS = {
    "93": ("site",),
    "94": ("site", "device"),
    "95": ("site", "device"),
    "96": ("site", "device"),
    "257": ("site",),
    "258": ("site",),
    "261": ("choice", "site"),
    "263": ("choice", "site", "text"),
    "264": ("choice", "site", "text"),
    "265": ("choice", "site", "text"),
    "266": ("choice", "text"),
    "267": ("choice", "text"),
    "268": ("choice", "text"),
}


def _parameter_types(menu_number: str) -> tuple[str, ...]:
    """Return the portal parameter types for one menu number."""
    entry = PARAMETER_REGISTRY[menu_number]  # Use the same registry that the route returns.
    parameters = entry["parameters"]  # Read the declared controls for this menu row.
    return tuple(parameter["param_type"] for parameter in parameters)  # Compare by control type only.


def test_issue_3151_3152_declares_required_controls() -> None:
    """Assert the repaired rows declare the controls that the browser must render."""
    checked = 0  # Count the rows so the failure output states the guard scope.
    for menu_number, expected_types in REQUIRED_CONTROL_MENUS.items():  # Check every repaired control row.
        actual_types = _parameter_types(menu_number)  # Read the operation contract for this menu.
        for expected_type in expected_types:  # Verify each required kind appears at least once.
            assert expected_type in actual_types, f"menu {menu_number} lacks {expected_type}; checked {CHECKED_MENU_COUNT} rows"
        checked += 1  # Count a menu after its contract passes.
    assert checked == 13, f"checked {checked} control menus out of {CHECKED_MENU_COUNT} issue rows"


def test_issue_3151_menu_92_is_cli_only() -> None:
    """Assert menu 92 stays out of the stateless browser run path."""
    entry = PARAMETER_REGISTRY["92"]  # Read the menu 92 portal contract.
    assert entry["category"] == "cli_only", f"menu 92 contract changed; checked {CHECKED_MENU_COUNT} rows"
    assert entry["parameters"] == [], f"menu 92 must not render stale controls; checked {CHECKED_MENU_COUNT} rows"
    assert "SSH access" in entry["cli_only_message"], f"menu 92 lacks the SSH message; checked {CHECKED_MENU_COUNT} rows"


def test_issue_3151_menu_91_no_longer_promises_selection() -> None:
    """Assert menu 91 is the one label repair from the issue set."""
    from MistHelper import menu_actions  # Import lazily because MistHelper builds the menu at module import.

    title = menu_actions["91"].title  # Read the label that the portal operation list uses.
    forbidden_words = ("browse", "select")  # These words promised a browser control before the repair.
    assert not any(word in title.lower() for word in forbidden_words), (
        f"menu 91 still promises a selection; checked {CHECKED_MENU_COUNT} rows"
    )
