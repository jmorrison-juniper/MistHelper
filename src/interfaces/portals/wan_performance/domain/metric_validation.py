"""Validate WAN metric values before they enter immutable domain records."""

import math


def validate_unit(unit: str) -> None:
    """Require a non-empty measurement unit."""
    if not isinstance(unit, str):
        raise ValueError("unit must contain a non-empty measurement unit.")
    if not unit.strip():
        raise ValueError("unit must contain a non-empty measurement unit.")


def validate_missing_reason(missing_reason: str | None) -> None:
    """Require a non-empty reason for a missing value."""
    if not isinstance(missing_reason, str):
        raise ValueError("missing_reason is required when value is missing.")
    if not missing_reason.strip():
        raise ValueError("missing_reason is required when value is missing.")


def validate_value(value: float | int | None, missing_reason: str | None) -> None:
    """Require a finite number or an explicit reason for a missing value."""
    if value is None:
        validate_missing_reason(missing_reason)
        return
    if isinstance(value, bool):
        raise ValueError("value must be a finite number or None.")
    if not isinstance(value, (int, float)):
        raise ValueError("value must be a finite number or None.")
    if not math.isfinite(value):
        raise ValueError("value must be a finite number or None.")
    if missing_reason is not None:
        raise ValueError("missing_reason must be absent when value is present.")


def validate_sample_count(sample_count: int | None) -> None:
    """Require a non-negative integer sample count."""
    if sample_count is None:
        return
    if isinstance(sample_count, bool):
        raise ValueError("sample_count must be a non-negative integer.")
    if not isinstance(sample_count, int):
        raise ValueError("sample_count must be a non-negative integer.")
    if sample_count < 0:
        raise ValueError("sample_count must be a non-negative integer.")


def validate_coverage_fraction(coverage_fraction: float | None) -> None:
    """Require a finite coverage value between zero and one."""
    if coverage_fraction is None:
        return
    if isinstance(coverage_fraction, bool):
        raise ValueError("coverage_fraction must be finite and between zero and one.")
    if not isinstance(coverage_fraction, (int, float)):
        raise ValueError("coverage_fraction must be finite and between zero and one.")
    if not math.isfinite(coverage_fraction):
        raise ValueError("coverage_fraction must be finite and between zero and one.")
    if not 0 <= coverage_fraction <= 1:
        raise ValueError("coverage_fraction must be finite and between zero and one.")
