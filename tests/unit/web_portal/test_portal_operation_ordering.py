"""Tests that the portal lists every operation in numeric order.

Issue #3139 reported a shuffled operation list. Thirteen of eighteen
categories showed their operations in dictionary insertion order, so an
operator read "1, 2, 4, 3" under Core Organization. The page offers no
search box, so a shuffled list makes an operator hunt for a number.

These tests hold the sort in place. Each one feeds the builder a menu
dictionary whose keys arrive out of order, because a dictionary keeps the
order its keys arrived in. A fixture that is already sorted would pass
with or without the repair, and it would prove nothing.
"""

import pytest

from src.utils.menu_entry import MenuEntry
from web_portal.menu_registry import build_static_menu_actions
from web_portal.services.operation import OperationExecutor


def _entry(menu_id: str) -> MenuEntry:
    """Return one safe menu row for the ordering fixtures."""
    return MenuEntry(  # The portal reads named row fields, so build a real row.
        menu_id=menu_id,  # Keep the row aligned with its dictionary key.
        handler=lambda: None,  # A no-op action never runs in these tests.
        title=f"Operation {menu_id}",  # The page shows this text beside the number.
        category="safe",  # Only a safe row reaches the portal list.
        destructive=False,  # A destructive row never reaches the portal list.
        supports_fast=False,  # The portal never uses fast-mode metadata.
    )


def _shuffled_actions(numbers: list[int]) -> dict:
    """Return a menu dictionary whose keys arrive in the given order."""
    # Python keeps insertion order, so this dictionary reproduces the defect.
    return {str(number): _entry(str(number)) for number in numbers}


@pytest.fixture
def executor():
    """Return an OperationExecutor, shut down after the test."""
    built = OperationExecutor(build_static_menu_actions(), None, None, None)
    yield built
    built.shutdown()  # Close the pool, so the test leaves no worker thread behind.


def _numbers_by_category(executor, actions: dict) -> dict:
    """Return the menu numbers the builder produced for each category."""
    categories = executor.build_category_list(actions)  # Run the code under test.
    return {c["name"]: [int(o["menu_number"]) for o in c["operations"]] for c in categories}


def test_shuffled_input_comes_back_in_numeric_order(executor):
    """The builder sorts operations even when the keys arrive shuffled."""
    # These four numbers reproduce the reported "1, 2, 4, 3" order.
    produced = _numbers_by_category(executor, _shuffled_actions([1, 2, 4, 3]))
    assert produced, "the builder returned no category, so this test proves nothing"
    for numbers in produced.values():
        assert numbers == sorted(numbers), f"the builder kept the input order: {numbers}"


def test_sort_is_numeric_and_not_text(executor):
    """The builder sorts by value, so 9 comes before 10."""
    # Text order puts "10" before "9", so this input separates the two sort keys.
    produced = _numbers_by_category(executor, _shuffled_actions([10, 9, 11, 2]))
    assert produced, "the builder returned no category, so this test proves nothing"
    for numbers in produced.values():
        assert numbers == sorted(numbers), f"the builder sorted as text, not as numbers: {numbers}"


def test_reverse_input_comes_back_in_numeric_order(executor):
    """A fully reversed input returns in ascending order."""
    # A reversed input fails loudly if the builder does no sorting at all.
    produced = _numbers_by_category(executor, _shuffled_actions([13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]))
    assert produced, "the builder returned no category, so this test proves nothing"
    for numbers in produced.values():
        assert numbers == sorted(numbers), f"the builder kept the reversed order: {numbers}"


def test_the_shipped_menu_lists_every_category_in_numeric_order(executor):
    """The real menu the portal serves is in numeric order."""
    # This test guards the shipped data. The tests above guard the sort logic.
    produced = _numbers_by_category(executor, build_static_menu_actions())
    shuffled = [f"{name}: {numbers}" for name, numbers in produced.items() if numbers != sorted(numbers)]
    assert not shuffled, "these categories list operations out of numeric order: " + "; ".join(shuffled)


def test_categories_themselves_stay_in_name_order(executor):
    """The category order does not change, so the page keeps its shape."""
    categories = executor.build_category_list(build_static_menu_actions())  # Run the code under test.
    names = [category["name"] for category in categories]  # Read the category names in page order.
    assert names == sorted(names)  # The existing sort by name must survive the new operation sort.
