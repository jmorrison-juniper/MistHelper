"""Unit tests for WAN edge scorecard scoring helpers."""

from __future__ import annotations  # Keep annotations import-safe in tests.

import logging  # Capture threshold warnings.

from src.reports.wan_edge_scorecard.scoring import DEFAULT_DHCP_POOL_WARN_PERCENT, WanEdgeScoring


def test_predominant_version_and_version_compliance(gateway_stats_sample: list[dict[str, object]]) -> None:
    """The most common version becomes the compliance baseline."""
    version = WanEdgeScoring.predominant_version(gateway_stats_sample)  # Calculate the baseline from fixtures.
    assert version == "22.4R1"  # Two of three gateways use this version.
    assert WanEdgeScoring.version_compliant("22.4R1", version) is True  # Matching version is compliant.
    assert WanEdgeScoring.version_compliant("21.4R3", version) is False  # Non-matching version is not compliant.


def test_dhcp_warn_percent_defaults_to_80(monkeypatch) -> None:
    """Missing DHCP_POOL_WARN_PERCENT uses the required default."""
    monkeypatch.delenv("DHCP_POOL_WARN_PERCENT", raising=False)  # Remove override for the default test.
    assert WanEdgeScoring.parse_dhcp_warn_percent() == DEFAULT_DHCP_POOL_WARN_PERCENT  # Confirm default value.


def test_dhcp_warn_percent_accepts_valid_value() -> None:
    """A valid threshold override is used."""
    assert WanEdgeScoring.parse_dhcp_warn_percent("75") == 75.0  # Use the provided valid threshold.


def test_dhcp_warn_percent_rejects_invalid_value(caplog) -> None:
    """Invalid threshold values fall back to the required default."""
    caplog.set_level(logging.WARNING)  # Capture the operator warning.
    assert WanEdgeScoring.parse_dhcp_warn_percent("not-a-number") == DEFAULT_DHCP_POOL_WARN_PERCENT  # Fallback.
    assert "Invalid DHCP_POOL_WARN_PERCENT" in caplog.text  # Confirm the warning is visible.


def test_safe_percent_handles_zero_total() -> None:
    """A zero denominator returns no percentage."""
    assert WanEdgeScoring.safe_percent(1, 0) is None  # Avoid division by zero.
    assert WanEdgeScoring.safe_percent(40, 100) == 40.0  # Confirm normal percentage math.
