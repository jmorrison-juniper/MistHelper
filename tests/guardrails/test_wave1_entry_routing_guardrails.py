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
