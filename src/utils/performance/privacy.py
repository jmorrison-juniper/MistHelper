"""Privacy and cardinality control for performance labels.

A metric label must never carry a credential, an identifier, a path, or user
text. The policy keeps an allowlist, and it buckets a count into a fixed set of
names, so the label cardinality cannot grow with the traffic.
"""

from __future__ import annotations

import re
from typing import Final

ALLOWED_DIMENSIONS: Final = frozenset(
    {
        "operation",  # The fixed operation or command name.
        "stage",  # The fixed planner stage name.
        "method",  # The HTTP method, from a closed set.
        "route",  # The route template, never the raw path.
        "status_class",  # The status family, such as 2xx.
        "result",  # The closed outcome value.
        "cache_family",  # The cache key prefix, never the full key.
        "statement_kind",  # The SQL verb, never the statement text.
        "engine",  # The solver or provider name, from a closed set.
        "workload_size",  # The bucketed input size.
        "monitor",  # The monitor type that produced the event.
        "phase",  # The fixed startup or task phase.
        "library",  # The native library name, from a closed set.
        "format",  # The serializer format name.
        "direction",  # The serializer direction, encode or decode.
        "error_class",  # The exception class name, never its message.
    }
)  # Every other label name is refused.

_DENY_PATTERNS: Final = (
    re.compile(r"[A-Za-z0-9+/]{24,}={0,2}"),  # A long opaque run looks like a token.
    re.compile(r"(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b"),  # A MAC address.
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),  # An IPv4 address.
    re.compile(r"(?i)[a-z]:[\\/]|(?:^|[^A-Za-z0-9])/(?:home|users|etc|var)/"),  # A file path.
    re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),  # A UUID.
    re.compile(r"(?i)\bselect\b.+\bfrom\b|\binsert\s+into\b|\bupdate\b.+\bset\b"),  # SQL text.
    re.compile(r"(?i)\b(?:password|secret|token|api[_-]?key|bearer|authorization)\b"),  # A secret.
    re.compile(r"(?i)https?://"),  # A URL, which can carry a query value.
)  # A value that matches any pattern never reaches a sink.

_SAFE_VALUE_RE: Final = re.compile(
    r"^/?[A-Za-z0-9][A-Za-z0-9._:/{}-]{0,63}$"
)  # Accept a route template, which starts with a slash and can hold a {name} part.
REDACTED: Final = "redacted"  # The single replacement value, which keeps cardinality at one.

_SAFE_VALUE_CACHE: set[str] = set()  # Proven safe values only. A private value never enters.
_SAFE_VALUE_CACHE_LIMIT: Final = 1_024  # The bound, because a label set stays small by policy.

_SIZE_BUCKETS: Final = (
    (10, "tiny"),  # Up to ten items.
    (100, "small"),  # Up to one hundred items.
    (1_000, "medium"),  # Up to one thousand items.
    (10_000, "large"),  # Up to ten thousand items.
)  # Any larger count reports "huge", so the label set stays at five names.


def bucket_size(count: int) -> str:
    """Return a fixed bucket name for an item count."""
    if count < 0:  # Guard, because a negative count is a caller defect.
        return "invalid"  # Report the defect without raising inside a metric path.
    for upper_bound, name in _SIZE_BUCKETS:  # Walk the ordered bucket list once.
        if count <= upper_bound:  # Take the first bucket that holds the count.
            return name  # Return the fixed name, never the raw count.
    return "huge"  # Every larger count shares one name, which bounds the cardinality.


def status_class(status_code: int) -> str:
    """Return the status family, such as 2xx, rather than the exact code."""
    if status_code < 100 or status_code > 599:  # Reject a value outside the HTTP range.
        return "invalid"  # Keep an unexpected code out of the label set.
    return f"{status_code // 100}xx"  # Collapse the code into one of five families.


def is_private(value: str) -> bool:
    """Return True when a value looks like private or unbounded data."""
    return any(pattern.search(value) for pattern in _DENY_PATTERNS)  # Any match is a refusal.


def scrub_value(value: str) -> str:
    """Return a safe label value, or the single redacted placeholder."""
    if value in _SAFE_VALUE_CACHE:  # A known safe value skips every pattern check.
        return value  # The cache holds only values that already passed each rule.
    if not _SAFE_VALUE_RE.fullmatch(value):  # Refuse a value with an unexpected shape.
        return REDACTED  # One placeholder keeps the cardinality bounded.
    if is_private(value):  # Refuse a value that matches a private pattern.
        return REDACTED  # Never emit the original text, and never cache it.
    _remember_safe(value)  # Store the safe value, so a repeat costs one set lookup.
    return value  # The value passed every check, so it is safe to emit.


def _remember_safe(value: str) -> None:
    """Add a proven safe value to the bounded cache.

    The cache holds safe values only. A private value never enters it, so the
    process never retains a credential, an identifier, or user text.
    """
    if len(_SAFE_VALUE_CACHE) >= _SAFE_VALUE_CACHE_LIMIT:  # Guard the memory bound.
        _SAFE_VALUE_CACHE.clear()  # Clear the whole set, which is cheaper than eviction.
    _SAFE_VALUE_CACHE.add(value)  # Remember this value for the next call.


def scrub_dimensions(dimensions: dict[str, str]) -> dict[str, str]:
    """Return only allowlisted labels, each with a scrubbed value."""
    safe: dict[str, str] = {}  # Collect the labels that pass every rule.
    for key, value in dimensions.items():  # Check one label at a time.
        if key not in ALLOWED_DIMENSIONS:  # Drop a label that the allowlist omits.
            continue  # Skip it silently, because a raise would break the measured path.
        safe[key] = scrub_value(str(value))  # Keep the key, but scrub its value.
    return safe  # Return the bounded label set.
