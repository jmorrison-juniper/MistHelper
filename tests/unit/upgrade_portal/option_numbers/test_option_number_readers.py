"""Unit tests for upgrade option number refusal boundaries."""

from __future__ import annotations

import pytest

from src.interfaces.portals.upgrade_portal.upgrade import options
from src.interfaces.portals.upgrade_portal.upgrade.options import format_duration
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


def test_negative_number_is_named_option_refusal() -> None:
    """A negative value must not become a whole-number option."""
    with pytest.raises(options.BadOptionError) as caught:  # Confirm that the mapper keeps the named refusal boundary.
        read_options(  # Exercise a signed value through the posted-text representation.
            "max_failure_percentage",
            str(-1),
        )
    assert caught.value.field == "max_failure_percentage"  # Confirm that the refusal identifies the invalid control.


def test_zero_number_remains_valid() -> None:
    """A zero value must remain valid for a control that permits zero."""
    result = read_options("p2p_cluster_size", str(0))  # Exercise the posted-text representation of the lower boundary.
    assert result.peer_to_peer.p2p_cluster_size == 0  # Confirm that validation does not treat zero as an absent value.


def test_duration_formatter_handles_numeric_edges() -> None:
    """The duration formatter must preserve zero and signed seconds."""
    assert format_duration(0) == "0s"  # Keep a zero-second stored value visible and exact.
    assert format_duration(-1) == "-1s"  # Keep a signed stored value visible for later validation.


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
