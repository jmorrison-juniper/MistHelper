"""Time range parsing for audit log analysis.

Converts human-friendly shorthand (3d, 4w, 6m) and custom ranges (6w-2w)
into parameters suitable for the Mist API (duration string or start/end epochs).
"""

import re
import time
from dataclasses import dataclass

UNIT_SECONDS = {
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "m": 2592000,
    "y": 31536000,
}

UNIT_LABELS = {
    "h": "hours",
    "d": "days",
    "w": "weeks",
    "m": "months",
    "y": "years",
}

SIMPLE_PATTERN = re.compile(r"^(\d+)([hdwmy])$", re.IGNORECASE)
RANGE_PATTERN = re.compile(r"^(\d+)([hdwmy])\s*[-–]\s*(\d+)([hdwmy])$", re.IGNORECASE)


@dataclass
class ParsedTimeRange:
    """Result of parsing a time range input."""

    duration: str | None = None
    start: int | None = None
    end: int | None = None
    description: str = ""


class TimeRangeParser:
    """Parse human-friendly time range inputs for audit log queries."""

    @staticmethod
    def display_legend() -> str:
        """Return formatted legend text for time range shortcuts."""
        return (
            "\n  Time Range Shortcuts:\n"
            "    2h = 2 hours    3d = 3 days     4w = 4 weeks\n"
            "    6m = 6 months   1y = 1 year\n"
            '  Custom range: "6w-2w" (from 6 weeks ago to 2 weeks ago)\n'
            "  Default: 7d (last 7 days)\n"
        )

    @staticmethod
    def parse(user_input: str) -> ParsedTimeRange:
        """Parse user input into API-compatible time parameters.

        Args:
            user_input: String like "3d", "4w", "6w-2w", or empty for default.

        Returns:
            ParsedTimeRange with either duration or start/end set.
        """
        text = user_input.strip().lower()

        if not text:
            return ParsedTimeRange(
                duration="7d",
                description="last 7 days",
            )

        simple = SIMPLE_PATTERN.match(text)
        if simple:
            count = int(simple.group(1))
            unit = simple.group(2)
            duration_str = f"{count}{unit}"
            label = UNIT_LABELS.get(unit, unit)
            if count == 1 and label.endswith("s"):
                label = label[:-1]
            return ParsedTimeRange(
                duration=duration_str,
                description=f"last {count} {label}",
            )

        range_match = RANGE_PATTERN.match(text)
        if range_match:
            start_count = int(range_match.group(1))
            start_unit = range_match.group(2)
            end_count = int(range_match.group(3))
            end_unit = range_match.group(4)

            now = int(time.time())
            start_seconds = start_count * UNIT_SECONDS[start_unit]
            end_seconds = end_count * UNIT_SECONDS[end_unit]

            start_epoch = now - start_seconds
            end_epoch = now - end_seconds

            if start_epoch >= end_epoch:
                raise ValueError(
                    f"Invalid range: start ({start_count}{start_unit} ago) "
                    f"must be before end ({end_count}{end_unit} ago)"
                )

            start_label = f"{start_count} {UNIT_LABELS[start_unit]}"
            end_label = f"{end_count} {UNIT_LABELS[end_unit]}"
            return ParsedTimeRange(
                start=start_epoch,
                end=end_epoch,
                description=f"from {start_label} ago to {end_label} ago",
            )

        raise ValueError(f"Invalid time range: '{user_input}'. " "Use format like '3d', '4w', or '6w-2w'.")

    @staticmethod
    def validate(parsed: ParsedTimeRange) -> bool:
        """Validate parsed time range has reasonable bounds."""
        if parsed.duration:
            match = SIMPLE_PATTERN.match(parsed.duration)
            if not match:
                return False
            count = int(match.group(1))
            unit = match.group(2)
            total_seconds = count * UNIT_SECONDS[unit]
            if total_seconds > 31536000 * 2:
                return False
            if total_seconds < 60:
                return False
            return True

        if parsed.start and parsed.end:
            if parsed.start >= parsed.end:
                return False
            now = int(time.time())
            if parsed.end > now + 60:
                return False
            if now - parsed.start > 31536000 * 2:
                return False
            return True

        return False

    @staticmethod
    def to_api_kwargs(parsed: ParsedTimeRange) -> dict[str, int]:
        """Convert parsed range to kwargs for the Mist API call (start/end epochs)."""
        if parsed.start and parsed.end:
            return {"start": parsed.start, "end": parsed.end}
        if parsed.duration:
            match = SIMPLE_PATTERN.match(parsed.duration)
            if match:
                count = int(match.group(1))
                unit = match.group(2)
                total_seconds = count * UNIT_SECONDS[unit]
                now = int(time.time())
                return {"start": now - total_seconds, "end": now}
        now = int(time.time())
        return {"start": now - 7 * 86400, "end": now}
