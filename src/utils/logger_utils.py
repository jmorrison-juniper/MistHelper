"""Logging utilities for MistHelper.

Provides redaction helpers and log filters that prevent sensitive values
(passwords, API tokens, PSKs) from appearing in log output.

Target audience: Junior NOC engineers who should never see credentials
in log files even when DEBUG level is enabled.
"""

import logging  # Standard library logging for type annotations
import re  # Regex for pattern-based redaction

REDACTED_PLACEHOLDER = "***REDACTED***"  # Canonical placeholder for scrubbed values

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
        value: The sensitive string to redact (e.g. a password or API token).

    Returns:
        The canonical redaction placeholder string.

    Example::

        logging.debug("Using credential: %s", redact_secret(password))
        # → "Using credential: ***REDACTED***"
    """
    _ = value  # Accept the value so callers don't need to gate on None; discard it
    return REDACTED_PLACEHOLDER  # Return placeholder instead of the real value


def redact_if_sensitive(key: str, value: str) -> str:
    """Conditionally redact a value based on whether its key looks credential-like.

    Useful when logging config dicts where some fields are sensitive and some
    are not, without having to enumerate every sensitive field name.

    Args:
        key:   The config/dict key name (e.g. "password", "username", "host").
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
    return value  # Key is not credential-like; return value unchanged


class SensitiveFilter(logging.Filter):
    """Logging filter that scrubs credential-like substrings from log messages.

    Install on a handler to provide a defence-in-depth layer: even if a
    caller accidentally logs a raw password, this filter replaces it before
    the message reaches the handler's output (file, console, syslog, etc.).

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

    def filter(self, record: logging.LogRecord) -> bool:
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
        except Exception:
            pass  # Silently ignore filter errors; logging must not interrupt execution
        return True  # Always pass the record on; we only sanitize, never suppress
