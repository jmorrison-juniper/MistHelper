"""Wave 1 safety classification guardrails for OperationRegistry behavior."""

import MistHelper


class TestWave1SafetyClassificationGuardrails:
    """Protect destructive vs safe boundaries from accidental drift."""

    def test_safe_and_interactive_safe_predicates(self):
        baseline = MistHelper.OperationRegistry.wave1_safety_classification_baseline()

        for option in baseline["safe_true"]:
            assert MistHelper.OperationRegistry.is_safe(option) is True

        for option in baseline["safe_false"]:
            assert MistHelper.OperationRegistry.is_safe(option) is False

        for option in baseline["interactive_safe_true"]:
            assert MistHelper.OperationRegistry.is_interactive_safe(option) is True

        for option in baseline["interactive_safe_false"]:
            assert MistHelper.OperationRegistry.is_interactive_safe(option) is False

    def test_destructive_options_have_destructive_skip_reason_markers(self):
        destructive_options = MistHelper.OperationRegistry.wave1_safety_classification_baseline()["destructive_markers"]
        for option in destructive_options:
            reason = MistHelper.OperationRegistry.skip_reason(option)
            assert reason, f"Option {option} should have a non-empty skip reason"
            assert "DESTRUCTIVE" in reason.upper(), f"Option {option} skip reason lost destructive marker"

    def test_adjacent_boundary_options_remain_stable(self):
        assert MistHelper.OperationRegistry.skip_category("89") == "websocket"
        assert MistHelper.OperationRegistry.skip_category("90") == "destructive"
        assert MistHelper.OperationRegistry.skip_category("100") == "destructive"
        assert MistHelper.OperationRegistry.skip_category("101") == "interactive"
        assert MistHelper.OperationRegistry.skip_category("176") == "safe"
        assert MistHelper.OperationRegistry.skip_category("177") == "destructive"
