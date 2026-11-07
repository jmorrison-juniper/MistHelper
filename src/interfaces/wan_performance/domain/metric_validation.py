"""Validate metric values before collection records can use them."""

import math


class MetricValueValidator:
    """Reject invalid metric data instead of creating healthy-looking defaults."""

    @staticmethod
    def unit(value: str) -> None:
        """Require a readable unit for every metric."""
        if not isinstance(value, str) or not value.strip():  # Units explain how operators read a value.
            raise ValueError("unit must contain a non-empty measurement unit.")  # Reject ambiguous metrics.

    @staticmethod
    def value(value: float | int | None, missing_reason: str | None) -> None:
        """Require a finite number or a reason for missing data."""
        if value is None:  # Missing values need evidence for their absence.
            if not isinstance(missing_reason, str) or not missing_reason.strip():  # Reject unexplained absence.
                raise ValueError("missing_reason is required when value is missing.")  # Keep unknown data explicit.
            return  # Accept an explained missing value.
        if isinstance(value, bool) or not isinstance(value, (int, float)):  # Booleans are not measurements.
            raise ValueError("value must be a finite number or None.")  # Reject invalid external data.
        try:  # Guard conversion of oversized integers to floating-point form.
            finite = math.isfinite(value)  # Check the numeric range.
        except OverflowError as error:  # Reject values outside the supported numeric range.
            raise ValueError("value must be a finite number or None.") from error  # Keep the error contract stable.
        if not finite or missing_reason is not None:  # Prevent non-finite or contradictory values.
            raise ValueError("value must be finite and cannot have a missing reason.")  # Preserve metric meaning.

    @staticmethod
    def sample_count(value: int | None) -> None:
        """Require a non-negative integer sample count when present."""
        if value is None:  # Some point-in-time metrics have no source count.
            return  # Preserve the absent count.
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:  # Reject false or negative counts.
            raise ValueError("sample_count must be a non-negative integer.")  # Keep the source contract explicit.

    @staticmethod
    def coverage_fraction(value: float | None) -> None:
        """Require a finite coverage fraction between zero and one."""
        if value is None:  # A snapshot can have no interval coverage evidence.
            return  # Keep unknown coverage unknown.
        if isinstance(value, bool) or not isinstance(value, (int, float)):  # Reject non-numeric coverage.
            raise ValueError("coverage_fraction must be between zero and one.")  # Reject malformed input.
        try:  # Guard conversion of oversized integers to floating-point form.
            finite = math.isfinite(value)  # Check the numeric range.
        except OverflowError as error:  # Reject values outside the supported numeric range.
            raise ValueError("coverage_fraction must be between zero and one.") from error  # Keep the error stable.
        if not finite or not 0 <= value <= 1:  # Enforce the fraction boundary.
            raise ValueError("coverage_fraction must be between zero and one.")  # Reject invalid coverage.

    @staticmethod
    def raw_values(values: tuple[float | int, ...] | None, sample_count: int | None) -> None:
        """Validate retained samples and their declared count."""
        if values is None:  # Raw values are optional for a summarized measurement.
            return  # Keep summaries compact when source samples are absent.
        if not isinstance(values, tuple):  # Immutable records must not retain a mutable sequence.
            raise ValueError("raw_values must be a tuple of finite numbers.")  # Require immutable samples.
        for value in values:  # Validate each retained source sample.
            MetricValueValidator.value(value, None)  # Reject invalid raw values.
        if sample_count is not None and sample_count != len(values):  # Keep count aligned with stored values.
            raise ValueError("sample_count must match raw_values.")  # Reject inconsistent metric metadata.
