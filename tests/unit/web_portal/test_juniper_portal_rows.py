"""Unit tests for the web portal rows of the Juniper RMA menus 294 to 304 (issue #3519).

Why:
    The portal sends one answer for each control, in the order of the controls. A workflow
    reads its answers in the order of its prompts. A control in the wrong place sends its
    answer to the wrong prompt, and the workflow then reads a wrong value without any error.
    These tests pin the order of each row to the prompts that its workflow asks.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

from typing import Any  # WHY: the parameter definitions are loosely typed dictionaries.

import pytest  # WHY: parametrized checks over the eleven menus.

from src.foundation.support.utils.operation_registry import (
    OperationRegistry,
)  # WHY: the safety class that the portal gate reads.
from web_portal.menu_registry import MENU_DESCRIPTIONS, build_static_menu_actions  # WHY: the static menu rows.
from web_portal.services.operation import (  # WHY: the portal registry, its page groups, and its run gate.
    CATEGORY_RANGES,
    PARAMETER_REGISTRY,
    PORTAL_RUNNABLE_CATEGORIES,
)

JUNIPER_MENUS = tuple(str(number) for number in range(294, 305))  # Menus 294 to 304 inclusive, as text keys.

# The controls of each menu that asks at least one question, in the order the workflow asks them.
PROMPTED_CONTROLS: dict[str, tuple[str, ...]] = {
    "294": ("start_date", "end_date"),  # The list asks for the start, then the end.
    "295": ("key_kind",),  # The detail asks for the key kind, and its value is a dynamic control.
    "296": ("rma_number", "request_number", "case_number"),  # The RMA read asks three identifiers in order.
    "297": ("key_kind", "note_id"),  # The notes read asks the key, then an optional note identifier.
    "300": ("start_date", "end_date"),  # The bulk read asks the snapshot start, then the end.
    "303": ("key_kind", "rma_number"),  # The lookup asks the key, then an optional RMA number.
    "304": ("serial_numbers",),  # The asset lookup asks one line of serial numbers.
}

# The menus that ask no question. They keep no row, so the portal shows them with no controls.
UNPROMPTED_MENUS: tuple[str, ...] = ("298", "299", "301", "302")

# The controls that a user may leave blank. The workflow reads a blank answer as Enter.
OPTIONAL_CONTROLS: dict[str, tuple[str, ...]] = {
    "294": ("start_date", "end_date"),  # A blank date keeps the default window.
    "296": ("case_number",),  # A blank case number skips the case lookup.
    "297": ("note_id",),  # A blank note identifier reads every note.
    "300": ("start_date", "end_date"),  # A blank date keeps the default snapshot window.
    "303": ("rma_number",),  # A blank RMA number skips the RMA read.
}

# The controls that must hold a value before the Run button enables.
REQUIRED_CONTROLS: dict[str, tuple[str, ...]] = {
    "295": ("key_kind",),  # The workflow cancels without a key kind.
    "296": ("rma_number", "request_number"),  # The RMA read cannot run without both identifiers.
    "297": ("key_kind",),  # The notes read cannot run without a key kind.
    "303": ("key_kind",),  # The lookup cannot run without a key kind.
    "304": ("serial_numbers",),  # The asset lookup cannot run without serial numbers.
}


def _controls(menu: str) -> list[dict[str, Any]]:
    """Return the control definitions of one menu, in the order the portal sends them."""
    return list(PARAMETER_REGISTRY[menu]["parameters"])  # A copy, so a test cannot change the registry.


def _control(menu: str, name: str) -> dict[str, Any]:
    """Return the control of one menu with the given name, or fail when the menu has no such control."""
    for control in _controls(menu):  # Visit each control of the menu once.
        if control["name"] == name:  # The name identifies the control.
            return control  # Return the matching definition.
    raise AssertionError(f"Menu {menu} has no control named {name}")  # A missing control is a test failure.


def _category_name(menu: str) -> str:
    """Return the name of the page group that holds one menu number, the way the portal groups it."""
    number = int(menu)  # The ranges compare numbers, not text.
    for low, high, name in CATEGORY_RANGES:  # Walk the ranges in the order the portal reads them.
        if low <= number <= high:  # The first range that holds the number names the group.
            return name  # Return the group name.
    return "Other"  # A number outside every range lands under this group.


@pytest.mark.parametrize("menu", JUNIPER_MENUS)
def test_each_juniper_menu_is_runnable_from_the_portal(menu: str) -> None:
    """The portal runs only the categories it allows, so each Juniper menu must be one of them."""
    assert OperationRegistry.skip_category(menu) in PORTAL_RUNNABLE_CATEGORIES  # The registry verdict must allow it.


@pytest.mark.parametrize("menu", JUNIPER_MENUS)
def test_each_juniper_menu_sits_in_the_juniper_rma_group(menu: str) -> None:
    """The operator finds every Juniper menu under one page group."""
    assert _category_name(menu) == "Juniper RMA"  # The group name is the one the range table declares.


@pytest.mark.parametrize("menu", JUNIPER_MENUS)
def test_each_juniper_menu_has_a_readable_title(menu: str) -> None:
    """The static list shows the title, so every menu needs a non-empty title."""
    assert MENU_DESCRIPTIONS[menu].strip()  # An empty title leaves an operator with no label.


@pytest.mark.parametrize("menu", sorted(PROMPTED_CONTROLS, key=int))
def test_the_controls_follow_the_workflow_prompt_order(menu: str) -> None:
    """A control in the wrong place sends its answer to the wrong prompt, so the order is the contract."""
    assert tuple(control["name"] for control in _controls(menu)) == PROMPTED_CONTROLS[menu]  # Same names, same order.


@pytest.mark.parametrize("menu", sorted(PROMPTED_CONTROLS, key=int))
def test_control_names_are_unique_within_a_menu(menu: str) -> None:
    """Two controls with one name would overwrite each other's answer in the browser form."""
    names = [control["name"] for control in _controls(menu)]  # Every name of the menu, in order.
    assert len(names) == len(set(names))  # A duplicate name would collapse two answers into one.


@pytest.mark.parametrize("menu", UNPROMPTED_MENUS)
def test_a_menu_that_asks_no_question_keeps_no_control_row(menu: str) -> None:
    """A menu with no prompt keeps no row, so the portal shows it with no controls."""
    assert menu not in PARAMETER_REGISTRY  # No row means no control, which is correct for these menus.


@pytest.mark.parametrize(
    ("menu", "name"),
    [(menu, name) for menu, names in OPTIONAL_CONTROLS.items() for name in names],
)
def test_an_optional_control_may_stay_blank(menu: str, name: str) -> None:
    """The operator may leave an optional control blank, so the Run button must not wait for it."""
    assert _control(menu, name)["required"] is False  # A blank answer is valid for this control.


@pytest.mark.parametrize(
    ("menu", "name"),
    [(menu, name) for menu, names in REQUIRED_CONTROLS.items() for name in names],
)
def test_a_required_control_blocks_run_until_it_has_a_value(menu: str, name: str) -> None:
    """A control the workflow cannot run without must hold a value before Run enables."""
    assert _control(menu, name)["required"] is True  # The browser form marks this control as required.


def test_the_key_kind_offers_two_choices_that_match_the_case_key_prompt() -> None:
    """The workflow accepts only the choices 1 and 2, so the chooser must offer exactly those."""
    for menu in ("295", "297", "303"):  # Each menu that asks a key kind.
        chooser = _control(menu, "key_kind")  # The chooser of this menu.
        assert [option["value"] for option in chooser["options"]] == ["1", "2"]  # Only the two valid answers.


def test_each_key_kind_reveals_the_identifier_that_the_workflow_asks_next() -> None:
    """Choice 1 reveals the request number, and choice 2 reveals the customer case number."""
    dynamic = _control("295", "key_kind")["dynamic_parameters"]  # The control that follows each choice.
    assert [control["name"] for control in dynamic["1"]] == ["request_number"]  # Choice 1 asks a request number.
    assert [control["name"] for control in dynamic["2"]] == ["case_number"]  # Choice 2 asks a case number.


def test_the_revealed_identifier_controls_are_required() -> None:
    """The identifier that the workflow asks next cannot be blank, so the Run button waits for it."""
    dynamic = _control("297", "key_kind")["dynamic_parameters"]  # The identifier controls of menu 297.
    assert all(control["required"] is True for controls in dynamic.values() for control in controls)  # All required.


def test_the_static_menu_list_offers_every_juniper_menu_with_its_title() -> None:
    """The portal list must show all eleven Juniper menus with the title that MistHelper registers."""
    actions = build_static_menu_actions()  # The rows that the portal lists when no session exists.
    for menu in JUNIPER_MENUS:  # Each Juniper menu must be listed.
        assert menu in actions, f"Menu {menu} is missing from the static portal list"  # A missing row is hidden.
        assert actions[menu].title == MENU_DESCRIPTIONS[menu]  # The row carries the registry title.
