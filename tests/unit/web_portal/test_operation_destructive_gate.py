"""Security tests for the web portal destructive operation gate.

`OperationExecutor` decided whether the portal may run an operation with a
hardcoded number. `src/utils/operation_registry.py` holds the safety category
for every operation, and the project documents that registry as the single
source of truth.

The tests prove two defects.

1. The gate allowed an operation that the registry does not call safe. The
   registry marks menu 0 as `interactive` and menu 14, 18, 19, and 59 as
   `resource_intensive`.
2. The gate failed open on a key that `int()` cannot parse. The listing hid the
   key, and the run path still accepted it.
"""

from __future__ import annotations

import pytest

from src.utils.operation_registry import OperationRegistry
from web_portal.services.operation import OperationExecutor


def _noop() -> None:
    """Stand in for a menu action, because the gate runs before the call."""
    return None  # The gate must refuse before the executor reaches this body.


@pytest.fixture
def executor():
    """Build an executor whose menu holds one entry for each test case."""
    menu_actions = {
        "11": (_noop, "Export the organization inventory"),  # Registry category `safe`.
        "60": (_noop, "An interactive but safe export"),  # Registry category `interactive_safe`.
        "0": (_noop, "An interactive operation"),  # Registry category `interactive`.
        "14": (_noop, "A resource intensive export"),  # Registry category `resource_intensive`.
        "18": (_noop, "A second resource intensive export"),  # Registry category `resource_intensive`.
        "59": (_noop, "A third resource intensive export"),  # Registry category `resource_intensive`.
        "154": (_noop, "A destructive operation"),  # Registry category `destructive`.
        "102": (_noop, "A websocket operation"),  # Registry category `websocket`.
        "151": (_noop, "A continuous loop operation"),  # Registry category `continuous_loop`.
        "x1": (_noop, "A key that int() cannot parse"),  # The old gate failed open on this key.
    }
    built = OperationExecutor(menu_actions, None, None, None)  # Executor under test.
    yield built  # Hand the executor to the test before the pool shuts down.
    built._pool.shutdown(wait=False)  # Release the thread pool, so the test leaves no thread.


def _refusal(executor, menu_number: str):
    """Return the gate verdict for one menu number, or None when allowed."""
    return executor._validate_operation(menu_number)  # None means the gate allows the operation.


class TestUnsafeCategoriesAreRefused:
    """Prove that the gate refuses every category the registry calls unsafe."""

    @pytest.mark.parametrize("menu_number", ["0", "14", "18", "59", "102", "151", "154"])
    def test_unsafe_category_is_refused(self, executor, menu_number):
        """The gate must refuse an operation the registry does not call safe."""
        category = OperationRegistry.skip_category(menu_number)  # Read the authoritative verdict.

        assert category not in ("safe", "interactive_safe")  # Guard the premise of this test.
        assert _refusal(executor, menu_number) is not None  # The gate must refuse the operation.

    def test_unparseable_key_is_refused(self, executor):
        """A key that `int()` cannot parse must not reach the thread pool."""
        assert _refusal(executor, "x1") is not None  # The old gate returned None and allowed it.

    def test_unknown_key_is_refused(self, executor):
        """A key that the menu does not hold must be refused."""
        assert _refusal(executor, "12345") is not None  # An absent key must never run.


class TestSafeCategoriesStillRun:
    """Prove that the stricter gate keeps the supported operations reachable."""

    @pytest.mark.parametrize("menu_number", ["11", "60"])
    def test_safe_category_is_allowed(self, executor, menu_number):
        """The gate must allow an operation the registry calls safe."""
        category = OperationRegistry.skip_category(menu_number)  # Read the authoritative verdict.

        assert category in ("safe", "interactive_safe")  # Guard the premise of this test.
        assert _refusal(executor, menu_number) is None  # The gate must allow the operation.


class TestListingAndGateAgree:
    """Prove that the listing path and the run path use one rule."""

    def test_every_listed_operation_is_runnable(self, executor):
        """The operations page must not show an operation the gate refuses."""
        categories = executor.build_category_list(executor._menu_actions)  # Build the page data.
        listed = {op["menu_number"] for cat in categories for op in cat["operations"]}  # Shown keys.

        refused = {key for key in listed if _refusal(executor, key) is not None}  # Shown and refused.

        assert refused == set()  # A shown operation that the gate refuses confuses the operator.

    def test_every_runnable_operation_is_listed(self, executor):
        """The gate must not accept an operation that the page hides."""
        categories = executor.build_category_list(executor._menu_actions)  # Build the page data.
        listed = {op["menu_number"] for cat in categories for op in cat["operations"]}  # Shown keys.

        hidden = set(executor._menu_actions) - listed  # Keys the operations page never shows.
        allowed = {key for key in hidden if _refusal(executor, key) is None}  # Hidden and allowed.

        assert allowed == set()  # A hidden operation that the gate allows is a fail-open defect.
