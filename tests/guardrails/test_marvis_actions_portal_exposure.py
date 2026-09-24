"""Guard the operations web dashboard exposure of the Marvis Actions menu (issue #3299).

Why:
    FR-031 states that the operator can run menu 270 from the operations web
    dashboard. The portal gate reads ``OperationRegistry`` alone, so the menu is
    runnable only while the registry calls it ``interactive_safe``. A future
    edit that moves the row to ``destructive`` would hide the menu from the
    browser without a failed test. A future edit that removes a control would
    shift every answer by one prompt.

    Menu 270 stays ``interactive_safe`` on purpose. A mode 3 resolve changes a
    Mist record, but the record is recoverable in the Mist UI, and the run
    sends nothing until the operator types ``RESOLVE <count>``. The decision
    and its rejected alternative are in ``specs/3299-marvis-actions-bulk-resolve``.

These tests prove both directions.

1. The gate admits menu 270, and the page lists it in a named category.
2. The gate refuses menu 270 when the registry category is not safe.

The guard reports the count of gate decisions and controls it checked, so a
future edit that empties the fixture cannot pass silently.
"""

from __future__ import annotations

import pytest

from src.utils.menu_entry import MenuEntry  # WHY: fixtures must match the production menu row.
from src.utils.operation_registry import OperationRegistry
from web_portal.services.operation import CATEGORY_RANGES, PARAMETER_REGISTRY, OperationExecutor

MARVIS_MENU = "270"  # The menu number this feature added.
CONTROL_NAMES = (  # The six controls, in the order of the six prompts.
    "marvis_mode",
    "marvis_category",
    "marvis_subcategory",
    "marvis_resolution_code",
    "marvis_comment",
    "marvis_confirmation",
)


def _noop() -> None:
    """Stand in for a menu action, because the gate runs before the call."""
    return None  # The gate must decide before the executor reaches this body.


def _entry(menu_id: str, title: str) -> MenuEntry:
    """Return a menu row for a portal gate fixture."""
    return MenuEntry(
        menu_id=menu_id,  # WHY: keep the row aligned with its dictionary key.
        handler=_noop,  # WHY: the gate checks this callable before execution.
        title=title,  # WHY: the listing path displays this text.
        category="interactive_safe",  # WHY: OperationRegistry supplies the real gate category.
        destructive=False,  # WHY: fixture actions must not change Mist Cloud.
        supports_fast=False,  # WHY: the portal does not use fast-mode metadata.
    )


@pytest.fixture
def executor():
    """Build an executor whose menu holds one row for each gate decision under test."""
    menu_actions = {
        MARVIS_MENU: _entry(MARVIS_MENU, "Export or resolve Marvis Actions by category and subcategory"),
        "190": _entry("190", "A destructive ticket write"),
    }
    built = OperationExecutor(menu_actions, None, None, None)  # Executor under test.
    yield built  # Hand the executor to the test before the pool shuts down.
    built._pool.shutdown(wait=False)  # Release the thread pool, so the test leaves no thread.


def test_the_guard_measured_every_decision(executor) -> None:
    """Report the count of decisions and controls this guard checked, so an empty fixture cannot pass."""
    decisions = {key: executor._is_portal_runnable(key) for key in executor._menu_actions}
    controls = PARAMETER_REGISTRY[MARVIS_MENU]["parameters"]
    print(f"The Marvis Actions portal guard checked {len(decisions)} gate decisions and {len(controls)} controls.")
    assert len(decisions) == 2, "The fixture must hold two gate decisions."
    assert len(controls) == len(CONTROL_NAMES), "The row must hold one control for each prompt."


def test_the_registry_calls_the_menu_interactive_safe() -> None:
    """FR-002. The gate depends on this category, so pin it here."""
    assert OperationRegistry.skip_category(MARVIS_MENU) == "interactive_safe"


def test_the_gate_admits_the_menu(executor) -> None:
    """FR-031. An operator must be able to start the menu from the browser."""
    assert executor._is_portal_runnable(MARVIS_MENU) is True


def test_the_run_path_admits_the_menu(executor) -> None:
    """FR-031. The listing and the run path must agree, or the Run button would fail."""
    assert executor._validate_operation(MARVIS_MENU) is None


def test_the_menu_appears_in_a_named_category(executor) -> None:
    """An operation outside every range would land in the generic 'Other' group."""
    names = {
        category["name"]
        for category in executor.build_category_list(executor._menu_actions)
        for operation in category["operations"]
        if operation["menu_number"] == MARVIS_MENU
    }
    assert names == {"Marvis Actions"}


def test_the_category_range_covers_the_menu() -> None:
    """Pin the range entry, so a future edit cannot drop it silently."""
    assert (270, 270, "Marvis Actions") in CATEGORY_RANGES


def test_the_menu_still_needs_a_safe_category(monkeypatch, executor) -> None:
    """Prove the failure path. The registry verdict is the only gate that remains."""
    monkeypatch.setattr(OperationRegistry, "skip_category", staticmethod(lambda _number: "destructive"))
    assert executor._is_portal_runnable(MARVIS_MENU) is False


def test_the_gate_still_refuses_a_destructive_ticket_write(executor) -> None:
    """Menu 190 writes a support ticket, so the portal must never run it."""
    assert executor._is_portal_runnable("190") is False


def test_the_static_registry_describes_the_menu() -> None:
    """The portal can start without the MistHelper command line, and it still must list the menu."""
    from web_portal.menu_registry import MENU_DESCRIPTIONS

    assert MARVIS_MENU in MENU_DESCRIPTIONS
    assert "Marvis Actions" in MENU_DESCRIPTIONS[MARVIS_MENU]


def test_the_controls_follow_the_prompt_order() -> None:
    """FR-032. The browser sends one answer for each control, in control order."""
    names = tuple(param["name"] for param in PARAMETER_REGISTRY[MARVIS_MENU]["parameters"])
    assert names == CONTROL_NAMES
