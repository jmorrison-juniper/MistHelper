"""Regression tests for the named MistHelper menu row metadata."""

from __future__ import annotations  # WHY: allow modern annotations in the test module.

import pytest  # WHY: tests assert SystemExit behavior for invalid menu input.

import MistHelper  # WHY: the runtime menu table is the source under test.
from src.utils.menu_entry import MenuEntry  # WHY: the test verifies the production row type.

EXPECTED_MENU_ENTRY_COUNT = 270  # WHY: guard against lost rows during menu-table refactors.
EXPECTED_DESTRUCTIVE_NUMBERS = frozenset(  # WHY: operators rely on these numbers as write-capable actions.
    {str(number) for number in range(154, 188)}
    | {str(number) for number in range(189, 192)}
    | {"194", "206", "207", "208"}
)
DESTRUCTIVE_BOUNDARY_CASES = (  # WHY: test every edge of the discontinuous destructive set.
    ("153", False),
    ("154", True),
    ("187", True),
    ("188", False),
    ("189", True),
    ("191", True),
    ("192", False),
    ("193", False),
    ("194", True),
    ("195", False),
    ("205", False),
    ("206", True),
    ("208", True),
    ("209", False),
)


def test_menu_uses_named_entries_for_every_row() -> None:
    """Every menu row must expose named fields instead of tuple positions."""
    entries = list(MistHelper.menu_actions.values())  # WHY: inspect the full runtime table.
    assert len(entries) == EXPECTED_MENU_ENTRY_COUNT  # WHY: a lost row changes operator dispatch.
    assert all(isinstance(entry, MenuEntry) for entry in entries)  # WHY: callers must not need tuple unpacking.


def test_each_menu_number_is_unique() -> None:
    """No two entries may share one menu number."""
    keys = list(MistHelper.menu_actions)  # WHY: dictionary keys are the operator-facing numbers.
    row_ids = [entry.menu_id for entry in MistHelper.menu_actions.values()]  # WHY: row ids must match keys.
    assert len(keys) == len(set(keys))  # WHY: a duplicate literal would drop an operation silently.
    assert sorted(keys) == sorted(row_ids)  # WHY: each named row must carry the same number as its key.


def test_destructive_flag_matches_the_exact_required_set() -> None:
    """The explicit destructive flag must match the approved destructive number set."""
    actual = frozenset(  # WHY: derive the safety set from the named row field.
        number for number, entry in MistHelper.menu_actions.items() if entry.destructive
    )
    assert actual == EXPECTED_DESTRUCTIVE_NUMBERS  # WHY: missing or extra flags can run the wrong operation.


@pytest.mark.parametrize(("menu_number", "expected"), DESTRUCTIVE_BOUNDARY_CASES)
def test_destructive_boundaries_are_explicit(menu_number: str, expected: bool) -> None:
    """Each destructive range boundary must carry the correct flag."""
    assert MistHelper.menu_actions[menu_number].destructive is expected  # WHY: each edge guards a safety boundary.


@pytest.mark.parametrize("selection", ["9999", "not-a-number"])
def test_unknown_or_non_numeric_selection_exits(selection: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unknown selection and a non-numeric selection must fail closed."""
    messages: list[str] = []  # WHY: capture operator text without writing to the terminal.
    monkeypatch.setattr(MistHelper, "echo", lambda message, *args: messages.append(message % args if args else message))
    with pytest.raises(SystemExit) as raised:  # WHY: direct interactive mode exits on invalid input.
        MistHelper._handle_interactive_invalid_selection(selection, container_mode=False)
    assert raised.value.code == 1  # WHY: invalid input must produce an error exit.
    assert messages == ["Invalid selection. Please try again."]  # WHY: operator sees the refusal.


def test_empty_selection_does_not_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty selection must redisplay the menu instead of failing."""
    messages: list[str] = []  # WHY: capture operator text without writing to the terminal.
    monkeypatch.setattr(MistHelper, "echo", lambda message, *args: messages.append(message % args if args else message))
    MistHelper._handle_interactive_empty_input(container_mode=False)  # WHY: empty direct input is not an error.
    assert messages == ["No selection entered. Please enter a menu number."]  # WHY: operator gets a retry prompt.
