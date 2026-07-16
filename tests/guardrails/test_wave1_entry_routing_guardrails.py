"""Wave 1 routing guardrails for OperationRegistry invariants."""

import MistHelper


class TestWave1EntryRoutingGuardrails:
    """Validate representative routing categories remain stable."""

    def test_representative_category_mappings_are_stable(self):
        expected_categories = MistHelper.OperationRegistry.wave1_entry_routing_baseline()

        for option, expected in expected_categories.items():
            actual = MistHelper.OperationRegistry.skip_category(option)
            assert actual == expected, f"Option {option} category drifted: {actual} != {expected}"

    def test_critical_menu_keys_exist_in_menu_actions(self):
        required_options = set(MistHelper.OperationRegistry.wave1_entry_routing_baseline().keys())
        assert required_options.issubset(set(MistHelper.menu_actions.keys()))

    def test_registered_safe_options_unaffected_by_fail_closed_default(self):
        """Feature 1020 (FR-006): the fail-closed default must not regress already-correct classifications."""
        # Already-registered safe options still run in --test.
        for option in ("26", "58", "23"):
            assert MistHelper.OperationRegistry.is_safe(option) is True, f"Safe option {option} regressed"
            assert MistHelper.OperationRegistry.is_interactive_safe(option) is False
        # Already-registered interactive_safe options still run in --testinteractive, not --test.
        for option in ("62", "60", "89"):
            assert MistHelper.OperationRegistry.is_interactive_safe(option) is True, f"Option {option} regressed"
            assert MistHelper.OperationRegistry.is_safe(option) is False
