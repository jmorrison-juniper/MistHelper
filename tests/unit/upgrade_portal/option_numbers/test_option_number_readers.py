"""Unit tests for upgrade option number refusal boundaries."""

from __future__ import annotations

import pytest

from src.upgrade_portal.upgrade import options
from tests.unit.upgrade_portal.option_numbers.option_number_harness import fixed_clock, read_options


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("canary_phases", "²,100"),
        ("max_failures", "²"),
        ("start_time", "²s"),
        ("reboot_at", "²s"),
    ],
)
def test_superscript_number_is_named_option_refusal(field: str, value: str) -> None:
    """A superscript digit must not reach Python integer conversion."""
    with pytest.raises(options.BadOptionError) as caught:
        read_options(field, value)
    assert caught.value.field == field
    assert "invalid literal" not in str(caught.value).lower()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("canary_phases", f"{'1' * 5000},100"),
        ("max_failures", "1" * 5000),
        ("max_failure_percentage", "1" * 5000),
        ("start_time", f"{'9' * 5000}s"),
        ("reboot_at", f"{'9' * 5000}s"),
    ],
)
def test_very_long_number_is_named_option_refusal(field: str, value: str) -> None:
    """A very long value must refuse before Python conversion."""
    with pytest.raises(options.BadOptionError) as caught:
        read_options(field, value)
    assert caught.value.field == field


def test_stored_epoch_uses_the_active_limit_without_a_clock() -> None:
    """Stored epoch replay keeps its unbounded business rule and active limit."""
    with pytest.raises(options.BadOptionError) as caught:
        read_options("start_time", "9" * 5000, now=None)
    assert caught.value.field == "start_time"


def test_supported_number_boundaries_remain_valid() -> None:
    """Existing finite values keep their accepted range."""
    result = options.build_options(
        {"strategy": "canary", "canary_phases": "100", "max_failure_percentage": "100"},
        now=fixed_clock,
    )
    assert result.canary.max_failure_percentage == 100
