"""Time range parsing for audit log analysis.

Converts human-friendly shorthand (3d, 4w, 6m) and custom ranges (6w-2w)
into parameters suitable for the Mist API (duration string or start/end epochs).
"""

import re  # regex-driven parsing of shorthand and range inputs
import time  # epoch conversion for now-relative windows
from collections.abc import Callable  # typing for the parser dispatch table
from dataclasses import dataclass  # immutable result container for parsed ranges

UNIT_SECONDS: dict[str, int] = {  # WHY: unit letter -> seconds multiplier for offset math
    "h": 3600,  # hours in seconds
    "d": 86400,  # days in seconds
    "w": 604800,  # weeks in seconds
    "m": 2592000,  # 30-day months (calendar approximation used across Mist tooling)
    "y": 31536000,  # 365-day years (leap days ignored for shorthand parity)
}

UNIT_LABELS: dict[str, str] = {  # WHY: unit letter -> plural label for descriptions
    "h": "hours",  # hour label used in "last N hours" strings
    "d": "days",  # day label used in "last N days" strings
    "w": "weeks",  # week label used in "last N weeks" strings
    "m": "months",  # month label used in "last N months" strings
    "y": "years",  # year label used in "last N years" strings
}

SIMPLE_PATTERN = re.compile(r"^(\d+)([hdwmy])$", re.IGNORECASE)  # WHY: matches "3d", "4w", etc.
RANGE_PATTERN = re.compile(  # WHY: matches "6w-2w" or "3m-1w" (start-ago to end-ago)
    r"^(\d+)([hdwmy])\s*[-\u2013]\s*(\d+)([hdwmy])$", re.IGNORECASE
)

DEFAULT_DURATION = "7d"  # WHY: fallback shorthand for empty/whitespace input
DEFAULT_LABEL = "last 7 days"  # WHY: matching description for the default window
DEFAULT_FALLBACK_SECONDS = 7 * 86400  # WHY: 7-day span for to_api_kwargs fallback
MAX_LOOKBACK_SECONDS = 31536000 * 2  # WHY: 2-year cap keeps audit queries bounded
MIN_DURATION_SECONDS = 60  # WHY: reject sub-minute windows as accidental input
FUTURE_SKEW_ALLOWANCE = 60  # WHY: tolerate ~1 min of clock skew on end epochs

LEGEND_TEXT = (  # WHY: cached user-facing help block; identical across every call
    "\n  Time Range Shortcuts:\n"
    "    2h = 2 hours    3d = 3 days     4w = 4 weeks\n"
    "    6m = 6 months   1y = 1 year\n"
    '  Custom range: "6w-2w" (from 6 weeks ago to 2 weeks ago)\n'
    "  Default: 7d (last 7 days)\n"
)

INVALID_INPUT_TEMPLATE = (  # WHY: consistent error phrasing shared by parse()
    "Invalid time range: '{}'. Use format like '3d', '4w', or '6w-2w'."
)


@dataclass(frozen=True, slots=True)
class ParsedTimeRange:  # WHY: immutable bundle returned by TimeRangeParser.parse
    """Result of parsing a time range input."""

    duration: str | None = None  # WHY: shorthand like "3d" when input matched simple pattern
    start: int | None = None  # WHY: explicit epoch start when a range was supplied
    end: int | None = None  # WHY: explicit epoch end when a range was supplied
    description: str = ""  # WHY: human-readable window label for reporting


def _describe_simple(count: int, unit: str) -> str:  # WHY: format shorthand as "last N units"
    """Return a human label like 'last 3 days' or 'last 1 day'."""
    label = UNIT_LABELS.get(unit, unit)  # WHY: fall back to raw unit if unknown
    if count == 1 and label.endswith("s"):  # WHY: singularize plural label for 1-unit ranges
        label = label[:-1]  # strip trailing 's' to produce "day"/"week"/etc.
    return f"last {count} {label}"  # canonical description phrasing


def _parse_empty() -> ParsedTimeRange:  # WHY: build the default range for empty input
    """Return the default 7-day range used for empty or whitespace input."""
    return ParsedTimeRange(duration=DEFAULT_DURATION, description=DEFAULT_LABEL)  # WHY: canonical default


def _parse_simple(text: str) -> ParsedTimeRange | None:  # WHY: shorthand parser dispatch entry
    """Parse simple shorthand like '3d' into a ParsedTimeRange, or None if no match."""
    match = SIMPLE_PATTERN.match(text)  # attempt shorthand regex match
    if not match:  # WHY: signal caller to try the next parser
        return None  # no shorthand match here
    count = int(match.group(1))  # numeric count component
    unit = match.group(2)  # unit letter component
    return ParsedTimeRange(
        duration=f"{count}{unit}",  # canonical shorthand form (lowercase)
        description=_describe_simple(count, unit),  # human-readable description
    )


def _parse_range(text: str) -> ParsedTimeRange | None:  # WHY: range parser dispatch entry
    """Parse a range like '6w-2w' into epoch bounds, or None if no match."""
    match = RANGE_PATTERN.match(text)  # attempt range regex match
    if not match:  # WHY: signal caller no range parser applies
        return None  # no range match here
    start_count = int(match.group(1))  # start offset value (older bound)
    start_unit = match.group(2)  # start offset unit
    end_count = int(match.group(3))  # end offset value (newer bound)
    end_unit = match.group(4)  # end offset unit
    now = int(time.time())  # WHY: anchor both offsets to the same reference now
    start_epoch = now - start_count * UNIT_SECONDS[start_unit]  # older bound epoch
    end_epoch = now - end_count * UNIT_SECONDS[end_unit]  # newer bound epoch
    if start_epoch >= end_epoch:  # WHY: start must precede end chronologically
        raise ValueError(  # surface a caller-friendly message
            f"Invalid range: start ({start_count}{start_unit} ago) "  # older bound context
            f"must be before end ({end_count}{end_unit} ago)"  # newer bound context
        )
    description = (  # WHY: human-readable "from N X ago to M Y ago" label
        f"from {start_count} {UNIT_LABELS[start_unit]} ago " f"to {end_count} {UNIT_LABELS[end_unit]} ago"
    )
    return ParsedTimeRange(start=start_epoch, end=end_epoch, description=description)  # frozen bundle


# WHY: table-driven dispatch — first parser to return non-None wins.
_PARSERS: tuple[Callable[[str], ParsedTimeRange | None], ...] = (
    _parse_simple,  # ordered attempt 1: '3d' shorthand
    _parse_range,  # ordered attempt 2: '6w-2w' range
)


def _validate_duration(duration: str) -> bool:  # WHY: bounds check for shorthand duration form
    """Return True when a duration shorthand parses and falls in the allowed span."""
    match = SIMPLE_PATTERN.match(duration)  # only shorthand-form durations are valid
    if not match:  # WHY: garbage duration cannot be validated
        return False  # unparseable duration is not valid
    total_seconds = int(match.group(1)) * UNIT_SECONDS[match.group(2)]  # expand to seconds
    return MIN_DURATION_SECONDS <= total_seconds <= MAX_LOOKBACK_SECONDS  # bounds check


def _validate_range(start: int, end: int) -> bool:  # WHY: bounds check for explicit epoch pair
    """Return True when an explicit start/end pair is chronological and in-bounds."""
    if start >= end:  # WHY: reject zero-width or inverted ranges
        return False  # non-chronological range is invalid
    now = int(time.time())  # shared reference for future/past checks
    if end > now + FUTURE_SKEW_ALLOWANCE:  # WHY: reject clearly future end epochs
        return False
    return now - start <= MAX_LOOKBACK_SECONDS  # WHY: cap total lookback at 2 years


def _duration_to_epochs(duration: str) -> dict[str, int] | None:
    """Expand a shorthand duration to a now-anchored {start, end} kwargs dict."""
    match = SIMPLE_PATTERN.match(duration)  # only shorthand can be expanded
    if not match:  # WHY: caller falls back to a 7-day window on failure
        return None
    total_seconds = int(match.group(1)) * UNIT_SECONDS[match.group(2)]  # expand to seconds
    now = int(time.time())  # anchor the resulting window at "now"
    return {"start": now - total_seconds, "end": now}  # now-relative window


def _fallback_kwargs() -> dict[str, int]:
    """Return the default 7-day API kwargs used when parsing fails."""
    now = int(time.time())  # WHY: compute now once for both bounds
    return {"start": now - DEFAULT_FALLBACK_SECONDS, "end": now}  # 7-day default window


class TimeRangeParser:  # WHY: static facade preserves public API for existing callers
    """Parse human-friendly time range inputs for audit log queries."""

    @staticmethod
    def display_legend() -> str:
        """Return formatted legend text for time range shortcuts."""
        return LEGEND_TEXT  # WHY: return cached module constant

    @staticmethod
    def parse(user_input: str) -> ParsedTimeRange:
        """Parse user input into API-compatible time parameters.

        Args:
            user_input: String like "3d", "4w", "6w-2w", or empty for default.

        Returns:
            ParsedTimeRange with either duration or start/end set.
        """
        text = user_input.strip().lower()  # normalize whitespace and case
        if not text:  # WHY: empty input maps to the default 7-day window
            return _parse_empty()
        for parser in _PARSERS:  # WHY: try each parser in priority order
            result = parser(text)  # attempt one parse strategy
            if result is not None:  # first successful parser wins
                return result
        raise ValueError(INVALID_INPUT_TEMPLATE.format(user_input))  # no parser matched

    @staticmethod
    def validate(parsed: ParsedTimeRange) -> bool:
        """Validate parsed time range has reasonable bounds."""
        if parsed.duration:  # WHY: duration form is validated by regex + bounds
            return _validate_duration(parsed.duration)
        if parsed.start and parsed.end:  # WHY: explicit range form is validated separately
            return _validate_range(parsed.start, parsed.end)
        return False  # WHY: empty/partial ParsedTimeRange is not valid

    @staticmethod
    def to_api_kwargs(parsed: ParsedTimeRange) -> dict[str, int]:
        """Convert parsed range to kwargs for the Mist API call (start/end epochs)."""
        if parsed.start and parsed.end:  # WHY: explicit epochs pass through unchanged
            return {"start": parsed.start, "end": parsed.end}
        if parsed.duration:  # WHY: shorthand duration expands to a now-relative window
            expanded = _duration_to_epochs(parsed.duration)
            if expanded is not None:  # duration parsed cleanly
                return expanded
        return _fallback_kwargs()  # WHY: last resort default window
