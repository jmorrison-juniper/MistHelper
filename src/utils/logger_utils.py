"""Logging utilities for MistHelper.

Provides redaction helpers and log filters that prevent sensitive values
(passwords, API tokens, PSKs) from appearing in log output.

Target audience: Junior NOC engineers who should never see credentials
in log files even when DEBUG level is enabled.
"""

import hashlib  # One-way digests for private values that must stay correlatable in a log
import logging  # Standard library logging for type annotations
import re  # Regex for pattern-based redaction

REDACTED_PLACEHOLDER = "***REDACTED***"  # Canonical placeholder for scrubbed values
PRIVATE_DIGEST_EMPTY = "none"  # Token used when the caller supplies no private text
_PRIVATE_DIGEST_LENGTH = 12  # Hex characters kept from the digest. Enough to stay unique within one run

# Regex patterns that identify credential-like keys in log records.
# Match is case-insensitive so "Password", "PASSWORD", "password" all trigger.
_SENSITIVE_KEY_PATTERNS = re.compile(  # Compiled once at module load for performance
    r"(password|passwd|secret|token|api_key|psk|credential|auth)",
    re.IGNORECASE,
)


def redact_secret(value: str) -> str:
    """Replace a sensitive value with a fixed redaction placeholder.

    Use this when you need to log a variable that *might* hold a credential.
    Passing the return value instead of the raw value ensures the credential
    never reaches the log handler.

    Args:
        value: The sensitive string to redact (for example a password or API token).

    Returns:
        The canonical redaction placeholder string.

    Example::

        logging.debug("Using credential: %s", redact_secret(password))
        # → "Using credential: ***REDACTED***"
    """
    _ = value  # Accept the value so callers do not need to gate on None. Discard it
    return REDACTED_PLACEHOLDER  # Return placeholder instead of the real value


def private_digest(value: str | None) -> str:
    """Return a short one-way token for a private value so a log never shows the value.

    Use this for personal data that is not a credential, such as a street
    address. ``redact_secret`` returns the same placeholder for every input, so
    two log lines about two different addresses look identical. This helper
    returns a stable token instead. An operator can still follow one address
    through a whole run, but the log file never holds the address itself.

    The digest is one-way. A reader of the log cannot recover the address from
    the token.

    Args:
        value: The private string to protect, such as a street address.

    Returns:
        ``"none"`` when the value is empty or holds only whitespace.
        A 12-character lowercase hexadecimal token in every other case.

    Example::

        logging.info("Resolving address (key=%s)", private_digest(street))
        # -> "Resolving address (key=3f8a1c2d9b04)"
    """
    if not value or not value.strip():  # No private text to protect. Keep the log line readable
        return PRIVATE_DIGEST_EMPTY  # Constant token marks an absent value
    normalized = " ".join(value.lower().split())  # Case and spacing must not change the token
    encoded = normalized.encode("utf-8")  # SHA-256 needs bytes, and UTF-8 keeps non-ASCII input stable
    digest = hashlib.sha256(encoded).hexdigest()  # One-way digest. The private value cannot be restored
    return digest[:_PRIVATE_DIGEST_LENGTH]  # A short prefix keeps the log line readable


def redact_if_sensitive(key: str, value: str) -> str:
    """Conditionally redact a value based on whether its key looks credential-like.

    Useful when logging config dicts where some fields are sensitive and some
    are not, without having to enumerate every sensitive field name.

    Args:
        key:   The config/dict key name (for example "password", "username", "host").
        value: The value associated with that key.

    Returns:
        The original value when the key is not credential-like.
        ``REDACTED_PLACEHOLDER`` when the key matches a sensitive pattern.

    Example::

        for k, v in config.items():
            logging.debug("  %s = %s", k, redact_if_sensitive(k, v))
    """
    if _SENSITIVE_KEY_PATTERNS.search(key):  # Key matches a credential pattern
        return REDACTED_PLACEHOLDER  # Discard value and return placeholder
    return value  # Key is not credential-like. Return value unchanged


class SensitiveFilter(logging.Filter):
    """Logging filter that scrubs credential-like substrings from log messages.

    Install on a handler to provide a defence-in-depth layer: even if a
    caller accidentally logs a raw password, this filter replaces it before
    the message reaches the handler's output (file, console, syslog, and so on).

    Usage::

        handler = logging.StreamHandler()
        handler.addFilter(SensitiveFilter())
        logging.getLogger().addHandler(handler)

    The filter uses the same regex patterns as ``redact_if_sensitive()``.
    It operates on the formatted message string, so it catches values that
    slipped through argument formatting as well.
    """

    # Simple value-redaction pattern: anything after an = or : that looks like
    # it belongs to a sensitive key.  Matches patterns like:
    #   password=abc123  or  "password": "abc123"
    _VALUE_PATTERN = re.compile(  # Compiled once at class load for performance
        r"(?P<key>" + _SENSITIVE_KEY_PATTERNS.pattern + r')[=:\s"\']+(?P<value>\S+)',
        re.IGNORECASE,
    )

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        """Scrub the formatted log message in-place before it is emitted.

        Args:
            record: The log record being processed by the handler.

        Returns:
            True always — we never suppress records, only sanitize them.
        """
        try:
            message = record.getMessage()  # Render the final formatted message string
            sanitized = self._VALUE_PATTERN.sub(  # Replace credential values in-place
                r"\g<key>=***REDACTED***",  # Keep the key name, replace only the value
                message,
            )
            if sanitized != message:  # Only mutate if something was actually scrubbed
                record.msg = sanitized  # Replace the message with the sanitized version
                record.args = ()  # Clear args so getMessage() uses the new msg directly
        except Exception:  # noqa: BLE001 - never crash a logging filter
            pass  # nosec B110 - A log call inside this filter re-enters the filter and recurses without end.
        return True  # Always pass the record on. We only sanitize, never suppress
