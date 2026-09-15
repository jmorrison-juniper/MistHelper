"""Privacy and cardinality control for performance labels.

A metric label must never carry a credential, an identifier, a path, or user
text. The policy keeps an allowlist, and it buckets a count into a fixed set of
names, so the label cardinality cannot grow with the traffic.
"""

from __future__ import annotations  # Keep annotations lazy during import.

import logging  # Record privacy decisions without private values.
import re  # Detect unsafe values before they reach a sink.
from typing import Any, ClassVar, Final  # Declare bounded policy data.

log = logging.getLogger(__name__)  # Use one module logger for privacy decisions.


class PerformancePrivacyPolicy:
    """Apply the deny-by-default privacy policy to labels."""

    REDACTED: ClassVar[str] = "redacted"  # Use one replacement value to bound cardinality.
    SAFE_VALUE_CACHE_LIMIT: ClassVar[int] = 1_024  # Bound the set that skips repeated checks.
    SAFE_VALUE_CACHE: ClassVar[set[str]] = set()  # Store proven safe values only.
    SIZE_BUCKETS: ClassVar[tuple[tuple[int, str], ...]] = (
        (10, "tiny"),
        (100, "small"),
        (1_000, "medium"),
        (10_000, "large"),
    )  # Use fixed buckets for counts.
    ALLOWED_DIMENSIONS: ClassVar[frozenset[str]] = frozenset(
        {
            "cache_family",
            "direction",
            "engine",
            "error_class",
            "format",
            "library",
            "method",
            "monitor",
            "operation",
            "phase",
            "result",
            "route",
            "stage",
            "statement_kind",
            "status_class",
            "workload_size",
        }
    )  # Drop every label key that the catalog does not name.
    ALLOWED_VALUES: ClassVar[dict[str, frozenset[str]]] = {
        "cache_family": frozenset({"inventory", "session", "token", "unknown"}),
        "direction": frozenset({"decode", "encode"}),
        "engine": frozenset({"arango", "redis", "sqlite", "python"}),
        "error_class": frozenset({"RuntimeError", "TimeoutError", "ValueError", "OSError", "Exception"}),
        "format": frozenset({"csv", "json", "jsonl", "yaml"}),
        "library": frozenset({"python", "mistapi", "requests"}),
        "method": frozenset({"DELETE", "GET", "PATCH", "POST", "PUT"}),
        "monitor": frozenset({"cache", "database", "file", "http", "operation", "serialization"}),
        "operation": frozenset({"compare_clients", "probe", "sync"}),
        "phase": frozenset({"startup", "first_use", "flush", "shutdown"}),
        "result": frozenset({"cancelled", "error", "ok", "timeout"}),
        "route": frozenset({"route_template"}),
        "stage": frozenset({"decode", "fetch", "flatten", "render", "write"}),
        "statement_kind": frozenset({"delete", "insert", "select", "update", "upsert"}),
        "status_class": frozenset({"1xx", "2xx", "3xx", "4xx", "5xx", "invalid"}),
        "workload_size": frozenset({"tiny", "small", "medium", "large", "huge", "invalid"}),
    }  # Permit only fixed values for each stored label key.
    DENY_PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        re.compile(r"[A-Za-z0-9+/]{24,}={0,2}"),
        re.compile(r"(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b"),
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        re.compile(r"(?i)[a-z]:[\\/]|(?:^|[^A-Za-z0-9])/(?:home|users|etc|var|app|data)/"),
        re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
        re.compile(r"(?i)\bselect\b.+\bfrom\b|\binsert\s+into\b|\bupdate\b.+\bset\b|\bdelete\b.+\bfrom\b"),
        re.compile(r"(?i)\b(?:password|secret|token|api[_-]?key|bearer|authorization)\b"),
        re.compile(r"(?i)https?://"),
        re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    )  # Refuse common secret, identifier, path, URL, SQL, and personal data shapes.
    SAFE_VALUE_RE: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")  # Allow short slugs.

    @classmethod
    def bucket_size(cls, count: int) -> str:
        """Return a fixed bucket name for an item count."""
        log.info("Bucketing a performance size value")  # Log before reducing the count.
        if count < 0:  # Guard, because a negative count is a caller defect.
            log.debug("Performance size bucket is invalid")  # Record the fixed result only.
            return "invalid"  # Report the defect without raw data.
        for upper_bound, name in cls.SIZE_BUCKETS:  # Walk the fixed buckets in order.
            if count <= upper_bound:  # Use the first bucket that contains the count.
                log.debug("Performance size bucket is %s", name)  # Log the fixed bucket.
                return name  # Return a fixed label, never the raw count.
        log.debug("Performance size bucket is huge")  # Log the largest fixed bucket.
        return "huge"  # Bound all larger counts to one label.

    @classmethod
    def status_class(cls, status_code: int) -> str:
        """Return the status family, such as 2xx, rather than the exact code."""
        log.info("Bucketing a performance status value")  # Log before reducing the status.
        if status_code < 100 or status_code > 599:  # Reject a value outside the HTTP range.
            log.debug("Performance status family is invalid")  # Record the fixed fallback.
            return "invalid"  # Keep an unexpected code out of the label set.
        family = "%sxx" % (status_code // 100)  # Collapse the code into one of five families.
        log.debug("Performance status family is %s", family)  # Log the fixed family.
        return family  # Return the fixed status family.

    @classmethod
    def scrub_dimensions(cls, dimensions: dict[str, Any]) -> dict[str, str]:
        """Return only allowlisted labels, each with an allowlisted value."""
        log.info("Scrubbing performance dimensions")  # Log before the privacy boundary runs.
        safe: dict[str, str] = {}  # Collect labels that pass the key and value allowlists.
        for key, value in dimensions.items():  # Inspect one untrusted label at a time.
            cls._copy_dimension(safe, key, value)  # Copy only labels that the policy permits.
        log.debug("Scrubbed performance dimensions count=%d", len(safe))  # Report safe count only.
        return safe  # Return only labels that can be stored.

    @classmethod
    def scrub_value(cls, value: str) -> str:
        """Return a safe label value, or the single redacted placeholder."""
        log.info("Scrubbing one performance value")  # Log before private data detection.
        if value in cls.SAFE_VALUE_CACHE:  # A known safe value skips every pattern check.
            log.debug("Performance value came from the safe cache")  # Do not log the value.
            return value  # Return a value that already passed each rule.
        if cls.is_private(value) or not cls.SAFE_VALUE_RE.fullmatch(value):  # Refuse unsafe or unbounded values.
            log.debug("Performance value was redacted")  # Do not log the refused value.
            return cls.REDACTED  # Never emit the original text.
        cls._remember_safe(value)  # Store the proven safe value for a repeat call.
        log.debug("Performance value passed the scrubber")  # Report success without the value.
        return value  # Return the bounded safe value.

    @classmethod
    def scrub_source_label(cls, value: str) -> str:
        """Return a non-path source label."""
        log.info("Scrubbing one performance source label")  # Log before source reduction.
        if cls.is_private(value):  # Refuse the original source before reducing it.
            log.debug("Performance source label was redacted")  # Do not log the raw source value.
            return cls.REDACTED  # Never derive a stored label from private source text.
        text = value.replace("\\", "/")  # Normalize path separators before taking the source area.
        parts = [part for part in text.split("/") if part]  # Split without keeping raw separators.
        candidate = cls._source_candidate(parts)  # Build a fixed source family from the path shape.
        result = cls.scrub_value(candidate)  # Apply the same private data filter to the candidate.
        log.debug("Scrubbed performance source label")  # Do not log the original source text.
        return result  # Return a source area, never the raw path.

    @classmethod
    def is_private(cls, value: str) -> bool:
        """Return True when a value looks like private or unbounded data."""
        log.info("Checking whether a performance value is private")  # Log before pattern checks.
        private = any(pattern.search(value) for pattern in cls.DENY_PATTERNS)  # Match every deny pattern.
        log.debug("Performance value private=%s", private)  # Report the decision only.
        return private  # Return True when the value must not reach storage.

    @classmethod
    def _copy_dimension(cls, safe: dict[str, str], key: str, value: Any) -> None:
        """Copy one dimension when the key and value are allowed."""
        log.info("Checking one performance dimension")  # Log before the dimension decision.
        if key not in cls.ALLOWED_DIMENSIONS:  # Drop unknown keys before value handling.
            log.debug("Dropped performance dimension key")  # Do not log an untrusted key.
            return  # Unknown keys can contain private context.
        scrubbed = cls.scrub_value(str(value))  # Remove private shapes before the allowlist check.
        if scrubbed in cls.ALLOWED_VALUES[key]:  # Permit only fixed values for this key.
            safe[key] = scrubbed  # Store the key after both allowlists pass.
        log.debug("Performance dimension accepted=%s", key in safe)  # Report the result.

    @classmethod
    def _remember_safe(cls, value: str) -> None:
        """Add a proven safe value to the bounded cache."""
        log.info("Remembering one safe performance value")  # Log before the cache update.
        if len(cls.SAFE_VALUE_CACHE) >= cls.SAFE_VALUE_CACHE_LIMIT:  # Guard the memory bound.
            cls.SAFE_VALUE_CACHE.clear()  # Clear the whole set, which is cheaper than eviction.
        cls.SAFE_VALUE_CACHE.add(value)  # Remember only a value that passed every privacy rule.
        log.debug("Safe performance value cache entries=%d", len(cls.SAFE_VALUE_CACHE))  # Report cache size.

    @classmethod
    def _source_candidate(cls, parts: list[str]) -> str:
        """Return the source area without raw separators."""
        log.info("Selecting a performance source area")  # Log before path reduction.
        if "src" in parts and parts.index("src") + 1 < len(parts):  # Prefer the package below src.
            source_area = "src_" + parts[parts.index("src") + 1]  # Keep only the stable package name.
        elif parts:  # Use a generic area for non-src tools.
            source_area = "source_" + parts[0].split(".")[0]  # Keep only the first file stem.
        else:
            source_area = "source_unknown"  # Use a fixed fallback for empty input.
        log.debug("Selected a performance source area")  # Do not log the raw path-derived text.
        return source_area  # Return a non-path source area.


REDACTED: Final = PerformancePrivacyPolicy.REDACTED  # Expose the fixed redaction value for tests.
