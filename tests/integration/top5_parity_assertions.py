"""Shared parity assertions for top-5 decomposition tests."""

from __future__ import annotations


def assert_menu_identifiers_unchanged(menu_actions: dict[int, tuple[str, object]], expected_ids: list[int]) -> None:
    """Ensure target menu identifiers still exist after refactor."""
    missing = [menu_id for menu_id in expected_ids if menu_id not in menu_actions]
    assert not missing, f"Missing expected menu IDs: {missing}"


def assert_callable_registered(menu_actions: dict[int, tuple[str, object]], menu_id: int) -> None:
    """Ensure a menu action still points to a callable handler."""
    _label, handler = menu_actions[menu_id]
    assert callable(handler), f"Menu {menu_id} handler is not callable"
