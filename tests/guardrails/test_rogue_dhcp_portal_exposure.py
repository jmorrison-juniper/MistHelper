"""Guard the operations web dashboard exposure of the rogue DHCP scan (issue #2985).

History:
    The portal gate once carried a numeric bound, ``DESTRUCTIVE_THRESHOLD``, set
    to 90. Menu 269 sits far above that bound, so the gate refused it. The first
    repair added an explicit allowlist that named menu 269 only.

    Issue #3082 removed that bound. A menu number states when an operation was
    added, not what the operation does, and the bound hid 79 operations that the
    registry calls safe. ``OperationRegistry`` now decides alone, so the
    allowlist is gone as well.

    ``tests/guardrails/test_portal_operation_coverage.py`` now proves the rule
    for every operation. This file stays as the named regression guard for menu
    269, because that operation is the reason the gate changed twice.

These tests prove both directions.

1. The gate admits menu 269, so the operator can run the scan from the browser.
2. The gate still refuses a destructive number, an unparseable key, and menu 269
   itself when the registry category is not safe.

The guard reports the count of gate decisions it checked, so a future edit that
empties the fixture cannot pass silently.
"""

from __future__ import annotations

import pytest

from src.utils.menu_entry import MenuEntry  # WHY: fixtures must match the production menu row.
from src.utils.operation_registry import OperationRegistry
from web_portal.services.operation import (
    CATEGORY_RANGES,
    PORTAL_RUNNABLE_CATEGORIES,
    OperationExecutor,
)

ROGUE_DHCP_MENU = "269"  # The menu number this feature added.


def _noop() -> None:
    """Stand in for a menu action, because the gate runs before the call."""
    return None  # The gate must decide before the executor reaches this body.


def _entry(menu_id: str, title: str) -> MenuEntry:
    """Return a menu row for a portal gate fixture."""
    return MenuEntry(
        menu_id=menu_id,  # WHY: keep the row aligned with its dictionary key.
        handler=_noop,  # WHY: the gate checks this callable before execution.
        title=title,  # WHY: the listing path displays this text.
        category="safe",  # WHY: OperationRegistry supplies the real gate category.
        destructive=False,  # WHY: fixture actions must not change Mist Cloud.
        supports_fast=False,  # WHY: the portal does not use fast-mode metadata.
    )


@pytest.fixture
def executor():
    """Build an executor whose menu holds one row for each gate decision under test."""
    menu_actions = {
        ROGUE_DHCP_MENU: _entry(ROGUE_DHCP_MENU, "Scan the organization for rogue DHCP servers"),
        "11": _entry("11", "An ordinary safe export below the bound"),
        "154": _entry("154", "A destructive operation"),
        "268": _entry("268", "An interactive safe operation above the bound"),
        "x1": _entry("x1", "A key that int() cannot parse"),
    }
    built = OperationExecutor(menu_actions, None, None, None)  # Executor under test.
    yield built  # Hand the executor to the test before the pool shuts down.
    built._pool.shutdown(wait=False)  # Release the thread pool, so the test leaves no thread.


def test_the_guard_measured_every_gate_decision(executor) -> None:
    """Report the count of decisions this guard checked, so an empty fixture cannot pass."""
    decisions = {key: executor._is_portal_runnable(key) for key in executor._menu_actions}
    print(f"The rogue DHCP portal guard checked {len(decisions)} gate decisions.")
    assert len(decisions) == 5, "The fixture must hold five gate decisions."


def test_the_registry_calls_the_scan_safe() -> None:
    """FR-002. The gate depends on this category, so pin it here."""
    assert OperationRegistry.skip_category(ROGUE_DHCP_MENU) == "safe"


def test_the_gate_reads_no_numeric_bound(executor) -> None:
    """Issue #3082. A number must not decide what the portal may run.

    Menu 269 is the operation that proved the bound wrong twice. It sits far
    above the old value of 90, and the registry calls it safe, so the gate must
    admit it on the category alone.
    """
    from web_portal.services import operation as module

    assert not hasattr(module, "DESTRUCTIVE_THRESHOLD"), "A numeric menu bound returned to the portal gate."
    assert not hasattr(module, "PORTAL_EXPLICIT_ALLOWLIST"), "The allowlist returned, so the bound likely did too."
    assert executor._is_portal_runnable(ROGUE_DHCP_MENU) is True


def test_the_gate_admits_the_scan(executor) -> None:
    """FR-029. An operator must be able to start the scan from the browser."""
    assert executor._is_portal_runnable(ROGUE_DHCP_MENU) is True


def test_the_run_path_admits_the_scan(executor) -> None:
    """FR-029. The listing and the run path must agree, or the button would fail."""
    assert executor._validate_operation(ROGUE_DHCP_MENU) is None


def test_the_scan_appears_in_the_portal_listing(executor) -> None:
    """FR-029. The operation must be visible, not only runnable."""
    listed = {
        operation["menu_number"]
        for category in executor.build_category_list(executor._menu_actions)
        for operation in category["operations"]
    }
    assert ROGUE_DHCP_MENU in listed


def test_the_scan_lands_in_a_named_category(executor) -> None:
    """An operation outside every range would land in the generic 'Other' group."""
    names = {
        category["name"]
        for category in executor.build_category_list(executor._menu_actions)
        for operation in category["operations"]
        if operation["menu_number"] == ROGUE_DHCP_MENU
    }
    assert names == {"Network Security Scans"}


def test_the_category_range_covers_the_scan() -> None:
    """Pin the range entry, so a future edit cannot drop it silently."""
    assert any(low <= int(ROGUE_DHCP_MENU) <= high for low, high, _ in CATEGORY_RANGES)


def test_the_gate_still_refuses_a_destructive_operation(executor) -> None:
    """Widening the portal must never admit an operation that writes."""
    assert executor._is_portal_runnable("154") is False


def test_the_gate_still_refuses_an_unparseable_key(executor) -> None:
    """The gate must stay fail-closed on a key the page cannot place."""
    assert executor._is_portal_runnable("x1") is False


def test_the_gate_now_admits_a_safe_operation_above_the_old_bound(executor) -> None:
    """Issue #3082. Menu 268 is interactive safe, and the bound used to hide it."""
    assert OperationRegistry.skip_category("268") == "interactive_safe"
    assert executor._is_portal_runnable("268") is True


def test_the_scan_still_needs_a_safe_category(monkeypatch, executor) -> None:
    """Prove the failure path. The registry verdict is the only gate that remains."""
    monkeypatch.setattr(OperationRegistry, "skip_category", staticmethod(lambda _number: "destructive"))
    assert executor._is_portal_runnable(ROGUE_DHCP_MENU) is False


def test_the_runnable_categories_stay_narrow() -> None:
    """Widening this set would admit every websocket and destructive operation."""
    assert PORTAL_RUNNABLE_CATEGORIES == frozenset({"safe", "interactive_safe"})


def test_the_static_registry_describes_the_scan() -> None:
    """The portal can start without the MistHelper command line, and it still must list the scan."""
    from web_portal.menu_registry import MENU_DESCRIPTIONS

    assert ROGUE_DHCP_MENU in MENU_DESCRIPTIONS
    assert "rogue DHCP" in MENU_DESCRIPTIONS[ROGUE_DHCP_MENU]
