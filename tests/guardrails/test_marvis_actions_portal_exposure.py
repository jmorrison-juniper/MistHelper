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

    Issue #3357 adds the seventh control, the optional alarm acknowledge
    confirmation. The run sends no acknowledge request until the operator
    confirms that control, so the added control keeps the safe category.

These tests prove both directions.

1. The gate admits menu 270, and the page lists it in a named category.
2. The gate refuses menu 270 when the registry category is not safe.

The guard reports the count of gate decisions and controls it checked, so a
future edit that empties the fixture cannot pass silently.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import pytest

from src.foundation.support.utils.menu_entry import MenuEntry  # WHY: fixtures must match the production menu row.
from src.foundation.support.utils.operation_registry import OperationRegistry
from web_portal.services.operation import CATEGORY_RANGES, PARAMETER_REGISTRY, OperationExecutor

MARVIS_MENU = "270"  # The menu number this feature added.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Read the production prompt source from this checkout.
SELECTION_SOURCE = REPOSITORY_ROOT / "src/mist/intelligence/marvis/actions/selection.py"
PROMPT_CONTEXT_PREFIX = "marvis_actions."  # Select only menu 270 prompts from the shared input helper calls.


def _prompt_contexts() -> tuple[str, ...]:
    """Return the menu 270 prompt contexts in production source order."""
    source = SELECTION_SOURCE.read_text(encoding="utf-8")  # Read the source that owns each prompt context.
    tree = ast.parse(source, filename=str(SELECTION_SOURCE))  # Parse syntax so comments and strings cannot match.
    calls = sorted(
        (node for node in ast.walk(tree) if isinstance(node, ast.Call)),
        key=lambda node: node.lineno,
    )
    contexts: list[str] = []
    for call in calls:
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "safe_input":
            continue
        context = next((keyword.value for keyword in call.keywords if keyword.arg == "context"), None)
        if isinstance(context, ast.Constant) and isinstance(context.value, str):
            if context.value.startswith(PROMPT_CONTEXT_PREFIX):
                contexts.append(context.value)
    return tuple(contexts)


def _control_name(prompt_context: str) -> str:
    """Return the portal control name for one production prompt context."""
    prompt_name = prompt_context.removeprefix(PROMPT_CONTEXT_PREFIX)
    portal_name = "_".join("ack" if word == "acknowledge" else word for word in prompt_name.split("_"))
    return f"marvis_{portal_name}"


def _expected_control_names() -> tuple[str, ...]:
    """Return portal control names from the production prompt context order."""
    return tuple(_control_name(context) for context in _prompt_contexts())


def _control_differences(expected: tuple[str, ...], actual: tuple[str, ...]) -> tuple[list[str], list[str], list[str]]:
    """Return named missing, extra, and out-of-order controls."""
    missing = sorted((Counter(expected) - Counter(actual)).elements())
    extra = sorted((Counter(actual) - Counter(expected)).elements())
    order = [
        f"position {position}: expected={expected_name} actual={actual_name}"
        for position, (expected_name, actual_name) in enumerate(zip(expected, actual, strict=False), start=1)
        if expected_name != actual_name
    ]
    return missing, extra, order


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
def executor() -> Iterator[OperationExecutor]:
    """Build an executor whose menu holds one row for each gate decision under test."""
    menu_actions = {
        MARVIS_MENU: _entry(MARVIS_MENU, "Export or resolve Marvis Actions by category and subcategory"),
        "190": _entry("190", "A destructive ticket write"),
    }
    built = OperationExecutor(menu_actions, None, None, None)  # Executor under test.
    yield built  # Hand the executor to the test before the pool shuts down.
    built._pool.shutdown(wait=False)  # Release the thread pool, so the test leaves no thread.


def test_the_guard_measured_every_decision(executor: OperationExecutor) -> None:
    """Report the count of decisions and controls this guard checked, so an empty fixture cannot pass."""
    decisions = {key: executor._is_portal_runnable(key) for key in executor._menu_actions}
    controls = PARAMETER_REGISTRY[MARVIS_MENU]["parameters"]
    expected_controls = _expected_control_names()
    print(f"The Marvis Actions portal guard checked {len(decisions)} gate decisions and {len(controls)} controls.")
    assert len(decisions) == 2, "The fixture must hold two gate decisions."
    assert expected_controls, "The production prompt inventory is empty, so the guard measured nothing."
    assert controls, "The portal control inventory is empty, so the guard measured nothing."


def test_the_registry_calls_the_menu_interactive_safe() -> None:
    """FR-002. The gate depends on this category, so pin it here."""
    assert OperationRegistry.skip_category(MARVIS_MENU) == "interactive_safe"


def test_the_gate_admits_the_menu(executor: OperationExecutor) -> None:
    """FR-031. An operator must be able to start the menu from the browser."""
    assert executor._is_portal_runnable(MARVIS_MENU) is True


def test_the_run_path_admits_the_menu(executor: OperationExecutor) -> None:
    """FR-031. The listing and the run path must agree, or the Run button would fail."""
    assert executor._validate_operation(MARVIS_MENU) is None


def test_the_menu_appears_in_a_named_category(executor: OperationExecutor) -> None:
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


def test_the_menu_still_needs_a_safe_category(monkeypatch: pytest.MonkeyPatch, executor: OperationExecutor) -> None:
    """Prove the failure path. The registry verdict is the only gate that remains."""
    monkeypatch.setattr(OperationRegistry, "skip_category", staticmethod(lambda _number: "destructive"))
    assert executor._is_portal_runnable(MARVIS_MENU) is False


def test_the_gate_still_refuses_a_destructive_ticket_write(executor: OperationExecutor) -> None:
    """Menu 190 writes a support ticket, so the portal must never run it."""
    assert executor._is_portal_runnable("190") is False


def test_the_static_registry_describes_the_menu() -> None:
    """The portal can start without the MistHelper command line, and it still must list the menu."""
    from web_portal.menu_registry import MENU_DESCRIPTIONS

    assert MARVIS_MENU in MENU_DESCRIPTIONS
    assert "Marvis Actions" in MENU_DESCRIPTIONS[MARVIS_MENU]


def test_the_controls_follow_the_prompt_order() -> None:
    """FR-032. The browser sends one answer for each control, in control order."""
    expected = _expected_control_names()
    actual = tuple(param["name"] for param in PARAMETER_REGISTRY[MARVIS_MENU]["parameters"])
    missing, extra, order = _control_differences(expected, actual)
    assert actual == expected, f"Marvis portal controls differ: missing={missing} extra={extra} order={order}"
