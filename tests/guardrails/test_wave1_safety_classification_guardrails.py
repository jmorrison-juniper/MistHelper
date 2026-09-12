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
        # Boundary: resource_intensive block ends at 101, websocket block starts at 102
        assert MistHelper.OperationRegistry.skip_category("101") == "resource_intensive"
        assert MistHelper.OperationRegistry.skip_category("102") == "websocket"
        # Boundary: last websocket at 123, interactive block starts at 124
        assert MistHelper.OperationRegistry.skip_category("123") == "websocket"
        assert MistHelper.OperationRegistry.skip_category("124") == "interactive"
        # Boundary: last non-destructive at 153 (resource_intensive), destructive block starts at 154
        assert MistHelper.OperationRegistry.skip_category("153") == "resource_intensive"
        assert MistHelper.OperationRegistry.skip_category("154") == "destructive"
        # Boundary: last destructive at 187
        assert MistHelper.OperationRegistry.skip_category("187") == "destructive"
