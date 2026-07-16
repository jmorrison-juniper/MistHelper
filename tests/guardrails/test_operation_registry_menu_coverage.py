"""Exhaustive menu/registry coverage guardrail for OperationRegistry.

Feature 1020-safe-test-clean-run, User Story 1. Replaces the brittle 11-key
``WAVE1_ENTRY_ROUTING_BASELINE`` sample as the *sole* coverage mechanism with
an exhaustive key-parity assertion that fails the instant ``menu_actions`` and
``OperationRegistry._REGISTRY`` diverge in either direction. See
``specs/1020-safe-test-clean-run/contracts/operation_registry_classification_contract.md``
for the four guarantees enforced here.
"""

from __future__ import annotations

import MistHelper  # WHY: menu_actions + OperationRegistry are re-exported by the MistHelper script module.

# WHY: the eight categories documented in the operation_registry module docstring; the ninth value
#      ``unregistered`` is a fail-closed fallback only and must NEVER appear inside _REGISTRY itself.
_DOCUMENTED_REGISTRY_CATEGORIES = frozenset(
    {
        "safe",
        "interactive_safe",
        "destructive",
        "wip",
        "resource_intensive",
        "websocket",
        "continuous_loop",
        "interactive",
    }
)


class TestOperationRegistryMenuCoverage:
    """Guarantee every reachable menu option is explicitly classified (fail-closed)."""

    def test_registered_options_matches_menu_actions_exactly(self):
        """Guarantee 3: registered_options() covers every menu_actions key (superset), with no stray keys."""
        menu_keys = set(MistHelper.menu_actions.keys())  # WHY: authoritative set of reachable options.
        registered = MistHelper.OperationRegistry.registered_options()  # WHY: new classmethod under test.

        missing = menu_keys - registered  # WHY: any menu option lacking an explicit classification is a defect.
        assert not missing, f"menu_actions keys missing from OperationRegistry._REGISTRY: {sorted(missing)}"

        stray = registered - menu_keys  # WHY: a registry entry with no menu option indicates stale drift.
        assert not stray, f"OperationRegistry._REGISTRY has keys absent from menu_actions: {sorted(stray)}"

    def test_every_registered_category_is_documented(self):
        """Guarantee: every _REGISTRY entry uses one of the eight documented categories (catches typos)."""
        for option in sorted(MistHelper.OperationRegistry.registered_options()):
            category = MistHelper.OperationRegistry.get(option)["category"]  # WHY: read the classified category.
            assert (
                category in _DOCUMENTED_REGISTRY_CATEGORIES
            ), f"Option {option} has undocumented category {category!r}"

    def test_every_destructive_entry_carries_destructive_marker(self):
        """Guarantee 4: every destructive entry has a skip_reason containing the 'DESTRUCTIVE' substring."""
        for option in sorted(MistHelper.OperationRegistry.registered_options()):
            if MistHelper.OperationRegistry.get(option)["category"] != "destructive":
                continue  # WHY: only destructive entries must carry the operator-visible marker.
            reason = MistHelper.OperationRegistry.skip_reason(option)  # WHY: skip_reason is what operators scan.
            assert reason, f"Destructive option {option} must have a non-empty skip reason"
            assert "DESTRUCTIVE" in reason.upper(), f"Destructive option {option} lost its DESTRUCTIVE marker"

    def test_menu_194_is_destructive_and_never_eligible(self):
        """Guarantee: menu 194 (clone device config) is destructive and excluded from both test modes (FR-004)."""
        entry = MistHelper.OperationRegistry.get("194")  # WHY: 194 clones config into a new gateway template.
        assert entry["category"] == "destructive", "Menu 194 must be classified destructive"
        assert "DESTRUCTIVE" in MistHelper.OperationRegistry.skip_reason("194").upper()

        all_options = list(MistHelper.menu_actions.keys())  # WHY: evaluate over the full reachable key set.
        assert "194" not in MistHelper.OperationRegistry.safe_options(all_options), "194 must not run in --test"
        assert "194" not in MistHelper.OperationRegistry.interactive_safe_options(
            all_options
        ), "194 must not run in --testinteractive"

    def test_no_reachable_menu_option_resolves_to_unregistered(self):
        """Guarantee: zero reachable menu options fall through to the fail-closed 'unregistered' category.

        This is the "dangerous incomplete categorization" detector: if a future menu addition is
        forgotten, this fails loudly instead of silently defaulting safe *or* silently skipping forever.
        """
        unregistered = [
            option
            for option in MistHelper.menu_actions
            if MistHelper.OperationRegistry.get(option)["category"] == "unregistered"
        ]
        assert not unregistered, f"Menu options resolve to fail-closed 'unregistered' (classify them): {unregistered}"
