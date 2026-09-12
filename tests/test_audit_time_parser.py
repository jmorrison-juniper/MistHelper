"""Tests for src.audit.time_parser module."""

import time

import pytest

from src.audit.time_parser import TimeRangeParser


@pytest.fixture
def parser():
    return TimeRangeParser()


class TestSimpleRanges:
    """Test parsing simple duration strings."""

    def test_parse_hours(self, parser):
        result = parser.parse("3h")
        assert result.duration == "3h"
        assert result.start is None
        assert result.end is None
        assert "3 hour" in result.description

    def test_parse_days(self, parser):
        result = parser.parse("7d")
        assert result.duration == "7d"
        assert "7 day" in result.description

    def test_parse_weeks(self, parser):
        result = parser.parse("4w")
        assert result.duration == "4w"
        assert "4 week" in result.description

    def test_parse_single_digit(self, parser):
        result = parser.parse("1d")
        assert result.duration == "1d"


class TestCustomRanges:
    """Test parsing custom offset ranges like 6w-2w."""

    def test_parse_weeks_offset(self, parser):
        result = parser.parse("6w-2w")
        assert result.duration is None
        assert result.start is not None
        assert result.end is not None
        assert result.start < result.end

    def test_parse_days_offset(self, parser):
        result = parser.parse("30d-7d")
        assert result.start is not None
        assert result.end is not None
        now = int(time.time())
        # Start should be ~30 days ago
        assert abs((now - result.start) - 30 * 86400) < 5
        # End should be ~7 days ago
        assert abs((now - result.end) - 7 * 86400) < 5


class TestValidation:
    """Test validation of parsed time ranges."""

    def test_valid_simple(self, parser):
        result = parser.parse("3d")
        assert parser.validate(result)

    def test_valid_custom(self, parser):
        result = parser.parse("6w-2w")
        assert parser.validate(result)

    def test_empty_returns_default(self, parser):
        result = parser.parse("")
        assert parser.validate(result)
        assert result.duration == "7d"

    def test_invalid_garbage_raises(self, parser):
        with pytest.raises(ValueError, match="Invalid time range"):
            parser.parse("foobar")


class TestToApiKwargs:
    """Test conversion to API keyword arguments."""

    def test_simple_duration(self, parser):
        result = parser.parse("7d")
        kwargs = parser.to_api_kwargs(result)
        assert "start" in kwargs
        assert "end" in kwargs
        assert kwargs["end"] - kwargs["start"] == 7 * 86400

    def test_custom_range(self, parser):
        result = parser.parse("6w-2w")
        kwargs = parser.to_api_kwargs(result)
        assert "start" in kwargs
        assert "end" in kwargs
        assert "duration" not in kwargs
        assert kwargs["start"] < kwargs["end"]
