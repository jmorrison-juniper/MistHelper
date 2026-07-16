"""Unit tests for OperationRegistry fail-closed default (feature 1020, User Story 1).

Asserts that any option key absent from ``_REGISTRY`` resolves to the new
``unregistered`` category (fail-closed) — never the old fail-open ``safe`` —
and is therefore ineligible for both ``--test`` and ``--testinteractive``. See
``specs/1020-safe-test-clean-run/contracts/operation_registry_classification_contract.md``.
"""

from __future__ import annotations

from src.utils.operation_registry import OperationRegistry

# WHY: a key guaranteed never to appear in _REGISTRY; exercises the fail-closed fallback branch only.
_NEVER_REGISTERED = "__never_registered__"


class TestOperationRegistryFailClosed:
    """Guarantee unregistered options fail closed uniformly across both test modes."""

    def test_unknown_key_resolves_to_unregistered(self):
        """An unknown key resolves to category 'unregistered', not the legacy fail-open 'safe'."""
        entry = OperationRegistry.get(_NEVER_REGISTERED)  # WHY: exercise the fallback for an absent key.
        assert entry["category"] == "unregistered", "Fallback must be fail-closed 'unregistered'"
        assert entry["category"] != "safe", "Fallback must never default an unknown option to 'safe'"

    def test_unregistered_is_in_skip_categories(self):
        """The 'unregistered' category is a member of SKIP_CATEGORIES (excluded from every test mode)."""
        assert "unregistered" in OperationRegistry.SKIP_CATEGORIES

    def test_unknown_key_is_not_safe_and_not_interactive_safe(self):
        """An unregistered key is False for both is_safe() and is_interactive_safe()."""
        assert OperationRegistry.is_safe(_NEVER_REGISTERED) is False
        assert OperationRegistry.is_interactive_safe(_NEVER_REGISTERED) is False

    def test_fail_closed_behavior_is_order_independent(self):
        """FR-007: is_safe() and is_interactive_safe() agree regardless of evaluation order.

        Both predicates route through get(); checking one first must not change the other's verdict.
        """
        interactive_first = OperationRegistry.is_interactive_safe(_NEVER_REGISTERED)
        safe_second = OperationRegistry.is_safe(_NEVER_REGISTERED)
        safe_first = OperationRegistry.is_safe(_NEVER_REGISTERED)
        interactive_second = OperationRegistry.is_interactive_safe(_NEVER_REGISTERED)
        assert interactive_first is False and safe_second is False
        assert safe_first is False and interactive_second is False

    def test_unknown_key_surfaces_a_skip_reason(self):
        """An unregistered key exposes a non-empty, actionable skip_reason (never silently blank)."""
        reason = OperationRegistry.skip_reason(_NEVER_REGISTERED)  # WHY: telemetry/summary must show a reason.
        assert reason, "Unregistered options must carry a non-empty skip reason"
        assert OperationRegistry.skip_category(_NEVER_REGISTERED) == "unregistered"
