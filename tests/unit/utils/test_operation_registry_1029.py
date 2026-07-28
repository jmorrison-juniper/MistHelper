"""Registry-classification test for feature 1029 (menus 207 and 208).

Locks in FR-001: both new destructive menu options MUST be classified
``destructive`` in ``OperationRegistry`` before any handler code ships.

Why:
    The CI guardrail already scans ``OPERATION_CATEGORIES`` for known menu
    numbers, but that check only fails on absence -- it does not assert the
    *category* value. This test pins the category to ``destructive`` and
    requires a non-empty ``skip_reason``, so a future edit that silently
    downgrades the classification (for example to ``interactive_safe``) fails
    fast in the unit suite rather than during a live systematic-test run.
"""

# WHY: forward references keep the type annotations lightweight and let the
# module import cleanly before pytest has resolved the runtime types.
from __future__ import annotations

from src.utils.operation_registry import OperationRegistry


def test_menu_207_registered_as_destructive() -> None:
    """Menu 207 (migrate APs) MUST be classified destructive with a reason.

    Why:
        SC-006 requires the destructive-guardrail classification to be
        present before any live-run entry point ships; this locks the
        category value and the non-empty reason in a single assertion set.
    """
    # WHY: read the private registry through the accessor helpers exposed by
    # the class so this test does not couple to the private ``_REGISTRY``
    # dict layout.
    category = OperationRegistry.skip_category("207")
    reason = OperationRegistry.skip_reason("207")

    # WHY: assert the exact expected category rather than "in a set" so a
    # silent downgrade to interactive_safe or wip fails loudly.
    assert category == "destructive", f"Menu 207 category must be destructive, got {category!r}"
    # WHY: skip_reason must name the operation so operators can grep the
    # systematic-test skip log and find the reason without cross-referencing.
    assert isinstance(reason, str) and reason.strip(), "Menu 207 skip_reason must be a non-empty string"


def test_menu_208_registered_as_destructive() -> None:
    """Menu 208 (revert AP profile migration) MUST be classified destructive with a reason.

    Why:
        Same rationale as the 207 test -- see that docstring. This test is
        split into two functions so a regression on either menu number
        surfaces the exact failing option in the pytest summary.
    """
    category = OperationRegistry.skip_category("208")
    reason = OperationRegistry.skip_reason("208")

    assert category == "destructive", f"Menu 208 category must be destructive, got {category!r}"
    assert isinstance(reason, str) and reason.strip(), "Menu 208 skip_reason must be a non-empty string"
