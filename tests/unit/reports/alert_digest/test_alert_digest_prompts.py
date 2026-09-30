"""Tests for alert digest prompt helpers."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

import pytest  # Assert validation failures without network calls.

from src.reports.alert_digest.prompts import AlertDigestPromptResolver  # Test pure prompt helpers.


def test_default_lookback_is_24_hours() -> None:
    """The shared lookback default is one day."""
    assert AlertDigestPromptResolver.resolve_lookback_hours({}) == 24  # Confirm the default contract.


def test_env_override_sets_lookback_hours() -> None:
    """A valid environment value overrides the default."""
    assert AlertDigestPromptResolver.resolve_lookback_hours({"ALERT_DIGEST_HOURS": "8"}) == 8  # Confirm override.


@pytest.mark.parametrize("value", ["", "0", "-1", "abc"])
def test_invalid_lookback_values_fail_closed(value: str) -> None:
    """Blank uses default, and invalid explicit values fail closed."""
    env = {"ALERT_DIGEST_HOURS": value}  # Build the injected environment.
    if value == "":  # Blank is equivalent to unset.
        assert AlertDigestPromptResolver.resolve_lookback_hours(env) == 24  # Confirm blank default.
    else:
        with pytest.raises(ValueError):  # Invalid explicit values must stop the operation.
            AlertDigestPromptResolver.resolve_lookback_hours(env)  # Exercise the validation path.


@pytest.mark.parametrize(
    ("text", "count", "expected"),
    [("ACK 3", 3, True), ("ACK 2", 3, False), ("ack 3", 3, False), ("ACK", 3, False), ("ACK three", 3, False)],
)
def test_confirmation_requires_ack_and_exact_count(text: str, count: int, expected: bool) -> None:
    """Only ACK followed by the exact count authorizes menu 281."""
    assert AlertDigestPromptResolver.confirmation_matches(text, count) is expected  # Confirm exact parsing.


@pytest.mark.parametrize(("arguments", "expected"), [(["--dry-run"], True), (["--menu", "281"], False)])
def test_dry_run_requested_reads_shared_flag(arguments: list[str], expected: bool) -> None:
    """Only --dry-run enables the acknowledgement preview mode."""
    assert AlertDigestPromptResolver.dry_run_requested(arguments) is expected  # Confirm dry-run flag parsing.
