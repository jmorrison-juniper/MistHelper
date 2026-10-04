"""Tests for client session control target normalization."""

import pytest  # WHY: parametrized tests cover supported operator input formats.

from src.mist.resources.device.client_session_control.models import (
    normalize_target,
)  # WHY: pure normalizer owns target safety.


@pytest.mark.parametrize(  # WHY: one table proves every accepted MAC input form.
    ("raw_value", "expected_value"),  # WHY: pair raw operator text with the Mist request value.
    [  # WHY: accepted examples from the feature contract.
        ("AA:BB:CC:DD:EE:FF", "aabbccddeeff"),  # WHY: colon separated input is common in Mist UI output.
        ("AA-BB-CC-DD-EE-FF", "aabbccddeeff"),  # WHY: hyphen separated input is common in Windows tools.
        ("aabb.ccdd.eeff", "aabbccddeeff"),  # WHY: dotted input is common in network CLI output.
        ("AABBCCDDEEFF", "aabbccddeeff"),  # WHY: bare input is the exact confirmation target form.
    ],  # WHY: close the cases list for pytest collection.
)
def test_normalize_target_accepts_supported_forms(raw_value: str, expected_value: str) -> None:  # WHY: prove forms.
    actual_value = normalize_target(raw_value)  # WHY: convert operator text before prompts or API calls.
    assert actual_value == expected_value  # WHY: Mist API path parameters require lowercase colon-free values.


def test_normalize_target_rejects_invalid_mac() -> None:  # WHY: invalid input must stop before confirmation.
    with pytest.raises(ValueError):  # WHY: validation failure is the expected early stop signal.
        normalize_target("not-a-mac")  # WHY: non-hex text must never reach a Mist request.
