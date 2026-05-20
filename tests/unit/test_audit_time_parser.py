"""Unit tests for src.audit.time_parser module.

Covers TimeRangeParser.display_legend, parse, validate, and to_api_kwargs.
"""

import time

import pytest

from src.audit.time_parser import UNIT_SECONDS, ParsedTimeRange, TimeRangeParser


class TestDisplayLegend:
    """Tests for TimeRangeParser.display_legend static method."""

    def test_returns_nonempty_string(self):
        """display_legend must return a non-empty string."""
        result = TimeRangeParser.display_legend()  # Call the static method
        assert isinstance(result, str)  # Must be a string
        assert len(result) > 0  # Must not be empty

    def test_contains_shortcut_examples(self):
        """Legend must mention the '3d' and '4w' shortcut formats."""
        result = TimeRangeParser.display_legend()  # Invoke the legend helper
        assert "3d" in result  # Common day shortcut must appear
        assert "4w" in result  # Common week shortcut must appear


class TestParseEmpty:
    """Tests for TimeRangeParser.parse with empty/whitespace input."""

    def test_empty_string_defaults_to_7d(self):
        """Empty input returns a 7-day duration with a description."""
        result = TimeRangeParser.parse("")  # Parse an empty string
        assert result.duration == "7d"  # Default duration must be 7d
        assert "7" in result.description  # Description must mention 7

    def test_whitespace_defaults_to_7d(self):
        """Whitespace-only input strips to empty and defaults to 7 days."""
        result = TimeRangeParser.parse("   ")  # Whitespace stripped to empty
        assert result.duration == "7d"  # Same 7d default as empty input


class TestParseSimple:
    """Tests for TimeRangeParser.parse with simple shorthand inputs."""

    def test_3d_returns_duration_string(self):
        """Input '3d' must produce a duration of '3d' and plural label."""
        result = TimeRangeParser.parse("3d")  # Parse a simple day shorthand
        assert result.duration == "3d"  # Duration must match the input token
        assert "3" in result.description  # Count must appear in the description
        assert "days" in result.description  # Plural form for count > 1

    def test_1d_uses_singular_day_label(self):
        """Input '1d' must use singular 'day', not 'days'."""
        result = TimeRangeParser.parse("1d")  # Parse a singular-count input
        assert result.duration == "1d"  # Duration token matches input
        assert "1 day" in result.description  # Singular form required

    def test_4w_returns_weeks_label(self):
        """Input '4w' must produce plural 'weeks' in description."""
        result = TimeRangeParser.parse("4w")  # Parse weeks shorthand
        assert result.duration == "4w"  # Duration token matches
        assert "weeks" in result.description  # Plural weeks label

    def test_1w_uses_singular_week_label(self):
        """Input '1w' must use singular 'week'."""
        result = TimeRangeParser.parse("1w")  # Parse single-week input
        assert "1 week" in result.description  # Singular form

    def test_2h_returns_hours_label(self):
        """Input '2h' must produce 'hours' in description."""
        result = TimeRangeParser.parse("2h")  # Parse hours shorthand
        assert result.duration == "2h"  # Duration token matches
        assert "hours" in result.description  # Hours label

    def test_6m_returns_months_label(self):
        """Input '6m' must produce 'months' in description."""
        result = TimeRangeParser.parse("6m")  # Parse months shorthand
        assert result.duration == "6m"  # Duration token matches
        assert "months" in result.description  # Months label

    def test_1y_uses_singular_year_label(self):
        """Input '1y' must use singular 'year'."""
        result = TimeRangeParser.parse("1y")  # Parse a single-year input
        assert "1 year" in result.description  # Singular year form

    def test_uppercase_input_normalized(self):
        """Uppercase input '3D' is normalised and parses like '3d'."""
        result = TimeRangeParser.parse("3D")  # Uppercase variant should still work
        assert result.duration == "3d"  # Output is lowercase-normalised


class TestParseRange:
    """Tests for TimeRangeParser.parse with range inputs like '6w-2w'."""

    def test_6w_to_2w_produces_start_end_epochs(self):
        """'6w-2w' must return a ParsedTimeRange with start and end epochs."""
        before = int(time.time())  # Lower bound for timing comparison
        result = TimeRangeParser.parse("6w-2w")  # Parse a range string
        after = int(time.time())  # Upper bound for timing comparison
        assert result.start is not None  # Start epoch must be set
        assert result.end is not None  # End epoch must be set
        assert result.duration is None  # Duration must not be set for ranges
        expected_start = before - 6 * UNIT_SECONDS["w"]  # 6 weeks ago lower bound
        expected_end = after - 2 * UNIT_SECONDS["w"]  # 2 weeks ago upper bound
        assert abs(result.start - expected_start) <= 2  # Allow 2-second tolerance
        assert abs(result.end - expected_end) <= 2  # Allow 2-second tolerance

    def test_range_description_contains_counts_and_unit(self):
        """Range description must mention both counts and 'ago'."""
        result = TimeRangeParser.parse("6w-2w")  # Parse range
        assert "6" in result.description  # Start count in description
        assert "2" in result.description  # End count in description
        assert "ago" in result.description  # Time-offset language

    def test_range_with_different_units(self):
        """'3m-1w' must produce a valid start/end pair."""
        result = TimeRangeParser.parse("3m-1w")  # Mixed unit range
        assert result.start is not None  # Start epoch set
        assert result.end is not None  # End epoch set
        assert result.start < result.end  # Start must be before end


class TestParseErrors:
    """Tests for TimeRangeParser.parse error cases."""

    def test_inverted_range_raises_value_error(self):
        """'2w-6w' means 2 weeks ago to 6 weeks ago, which is backwards."""
        with pytest.raises(ValueError, match="Invalid range"):  # Expect ValueError
            TimeRangeParser.parse("2w-6w")  # start_epoch > end_epoch

    def test_invalid_format_raises_value_error(self):
        """Completely unrecognised input must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid time range"):  # Expect error
            TimeRangeParser.parse("xyz123")  # No valid pattern match

    def test_bare_number_raises_value_error(self):
        """A bare number with no unit suffix must raise ValueError."""
        with pytest.raises(ValueError):  # No unit = neither pattern matches
            TimeRangeParser.parse("42")  # Missing unit character


class TestValidate:
    """Tests for TimeRangeParser.validate static method."""

    def test_valid_7d_duration_returns_true(self):
        """A standard 7d duration must validate successfully."""
        parsed = ParsedTimeRange(duration="7d")  # Standard 7-day range
        assert TimeRangeParser.validate(parsed) is True  # Must be valid

    def test_malformed_duration_returns_false(self):
        """A duration string that fails SIMPLE_PATTERN returns False."""
        parsed = ParsedTimeRange(duration="bad_format")  # No regex match
        assert TimeRangeParser.validate(parsed) is False  # Fails pattern check

    def test_duration_exceeding_two_years_returns_false(self):
        """A duration > 2 years (63072000 s) must be rejected."""
        parsed = ParsedTimeRange(duration="3y")  # 3y = 94608000 s > 63072000
        assert TimeRangeParser.validate(parsed) is False  # Exceeds 2-year limit

    def test_duration_zero_seconds_returns_false(self):
        """A duration that evaluates to 0 seconds fails the 60-second floor."""
        parsed = ParsedTimeRange(duration="0h")  # 0 * 3600 = 0 < 60 threshold
        assert TimeRangeParser.validate(parsed) is False  # Below minimum duration

    def test_valid_start_end_returns_true(self):
        """A valid past start/end pair must validate."""
        now = int(time.time())  # Current epoch for reference
        parsed = ParsedTimeRange(  # Build a valid historical range
            start=now - 86400,  # 1 day ago
            end=now - 3600,  # 1 hour ago
        )
        assert TimeRangeParser.validate(parsed) is True  # Must be valid

    def test_start_equal_to_end_returns_false(self):
        """A zero-width range (start == end) is invalid."""
        now = int(time.time())  # Current epoch
        parsed = ParsedTimeRange(start=now - 3600, end=now - 3600)  # Same instant
        assert TimeRangeParser.validate(parsed) is False  # Zero-width range

    def test_end_in_future_returns_false(self):
        """An end epoch significantly past now must be rejected."""
        now = int(time.time())  # Current epoch
        parsed = ParsedTimeRange(  # Build a range with future end
            start=now - 3600,  # 1 hour ago
            end=now + 7200,  # 2 hours in the future (exceeds now + 60)
        )
        assert TimeRangeParser.validate(parsed) is False  # Future end rejected

    def test_start_too_old_returns_false(self):
        """A start epoch more than 2 years ago must be rejected."""
        now = int(time.time())  # Current epoch
        three_years_ago = now - (3 * 365 * 86400)  # 3 years > 2-year lookback
        parsed = ParsedTimeRange(  # Build a too-old range
            start=three_years_ago,  # Exceeds 2-year limit
            end=now - 3600,  # Valid end
        )
        assert TimeRangeParser.validate(parsed) is False  # Exceeds lookback limit

    def test_empty_parsed_range_returns_false(self):
        """An empty ParsedTimeRange with no fields set returns False."""
        parsed = ParsedTimeRange()  # All fields at default None/empty
        assert TimeRangeParser.validate(parsed) is False  # Nothing to validate


class TestToApiKwargs:
    """Tests for TimeRangeParser.to_api_kwargs static method."""

    def test_with_start_and_end_returns_both_values(self):
        """If start and end are set, they are returned directly."""
        now = int(time.time())  # Current epoch for building test input
        parsed = ParsedTimeRange(  # Pre-computed range
            start=now - 86400,  # 1 day ago
            end=now,  # Now
        )
        result = TimeRangeParser.to_api_kwargs(parsed)  # Convert to API kwargs
        assert result["start"] == now - 86400  # Start epoch preserved
        assert result["end"] == now  # End epoch preserved

    def test_with_duration_computes_start_and_end(self):
        """A duration string is expanded into start/end epochs."""
        before = int(time.time())  # Timing lower bound
        parsed = ParsedTimeRange(duration="3d")  # 3-day duration
        result = TimeRangeParser.to_api_kwargs(parsed)  # Expand to epochs
        after = int(time.time())  # Timing upper bound
        expected_delta = 3 * UNIT_SECONDS["d"]  # 3 days in seconds
        assert result["end"] >= before  # End should be close to now
        assert result["end"] <= after + 1  # Allow tiny execution-time skew
        assert abs(result["start"] - (result["end"] - expected_delta)) <= 2  # Correct offset

    def test_empty_parsed_falls_back_to_7_day_default(self):
        """Empty ParsedTimeRange with no fields defaults to a 7-day window."""
        before = int(time.time())  # Lower bound
        parsed = ParsedTimeRange()  # All fields unset
        result = TimeRangeParser.to_api_kwargs(parsed)  # Must return fallback
        after = int(time.time())  # Upper bound
        assert result["end"] >= before  # End near current time
        assert result["end"] <= after + 1  # Tight tolerance
        expected_start = result["end"] - 7 * UNIT_SECONDS["d"]  # 7-day offset
        assert abs(result["start"] - expected_start) <= 2  # 7-day default applied

    def test_bad_duration_falls_back_to_7_day_default(self):
        """A malformed duration that fails SIMPLE_PATTERN triggers the fallback."""
        before = int(time.time())  # Lower bound
        parsed = ParsedTimeRange(duration="not_a_valid_duration")  # Bad duration
        result = TimeRangeParser.to_api_kwargs(parsed)  # Pattern match fails
        after = int(time.time())  # Upper bound
        assert result["end"] >= before  # End is near now
        assert result["end"] <= after + 1  # Tiny tolerance
        expected_start = result["end"] - 7 * UNIT_SECONDS["d"]  # 7-day fallback
        assert abs(result["start"] - expected_start) <= 2  # Fallback confirmed
