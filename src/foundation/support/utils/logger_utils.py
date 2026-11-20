"""Logging utilities for MistHelper.

Provides redaction helpers and log filters that prevent sensitive values
(passwords, API tokens, PSKs) from appearing in log output.

Target audience: Junior NOC engineers who should never see credentials
in log files even when DEBUG level is enabled.
"""

import hashlib  # One-way digests for private values that must stay correlatable in a log
import logging  # Standard library logging for type annotations
import re  # Regex for pattern-based redaction
import sys  # Detect terminal color support for the structlog console renderer
from collections.abc import MutableMapping  # Type structlog event dictionaries accepted by processors
from typing import Any  # Type key-value event dictionaries used by structlog processors

import structlog  # Structured event frontend for database and DNS diagnostics

REDACTED_PLACEHOLDER = "***REDACTED***"  # Canonical placeholder for scrubbed values
PRIVATE_DIGEST_EMPTY = "none"  # Token used when the caller supplies no private text
_PRIVATE_DIGEST_LENGTH = 12  # Hex characters kept from the digest. Enough to stay unique within one run

# Regex patterns that identify credential-like keys in log records.
# Match is case-insensitive so "Password", "PASSWORD", "password" all trigger.
_SENSITIVE_KEY_PATTERNS = re.compile(  # Compiled once at module load for performance
    r"(password|passwd|secret|token|api_key|psk|credential|authorization|auth)",
    re.IGNORECASE,
)


def _redact_sensitive_event_dict(event_dict: MutableMapping[str, Any]) -> dict[str, Any]:
    """Redact credential-shaped keys in one structlog event dictionary."""
    sanitized = dict(event_dict)  # Copy the event so callers keep no mutated context.
    for key in tuple(sanitized):  # Inspect every key in the current event.
        if _SENSITIVE_KEY_PATTERNS.search(str(key)):  # The key names a credential-shaped field.
            sanitized[key] = REDACTED_PLACEHOLDER  # Replace the private value at the structlog boundary.
    return sanitized  # Return one safe event dictionary for rendering.


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


class StructuredLoggingFrontend:
    """Configure structlog to render through MistHelper stdlib handlers."""

    @staticmethod
    def _foreign_pre_chain() -> list[Any]:
        """Return processors that prepare stdlib records for structlog rendering."""
        return [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            StructuredLoggingFrontend.redact_sensitive_fields,
        ]  # Add timestamp, level, logger, and redaction to foreign records.

    @staticmethod
    def redact_sensitive_fields(
        _logger: Any,
        _method_name: str,
        event_dict: MutableMapping[str, Any],
    ) -> dict[str, Any]:
        """Redact credential-shaped structlog keys before rendering."""
        return _redact_sensitive_event_dict(event_dict)  # Delegate to the shared event-redaction helper.

    @staticmethod
    def console_formatter() -> structlog.stdlib.ProcessorFormatter:
        """Build the terminal renderer and enable ANSI only for an interactive stream."""
        supports_color = sys.stderr.isatty()  # A pipe or test capture gets no ANSI escape sequence.
        return structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=StructuredLoggingFrontend._foreign_pre_chain(),
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=supports_color, sort_keys=True),
            ],
        )  # Render one shared event style for terminal and stdlib records.

    @staticmethod
    def file_formatter() -> structlog.stdlib.ProcessorFormatter:
        """Build a plain-text structured renderer for script.log."""
        return structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=StructuredLoggingFrontend._foreign_pre_chain(),
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.KeyValueRenderer(
                    key_order=["timestamp", "logger", "level", "event"],
                    drop_missing=True,
                ),
            ],
        )  # Keep key-value evidence searchable and free of ANSI color.

    @staticmethod
    def configure() -> None:
        """Configure structlog to pass every event through stdlib logging."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                StructuredLoggingFrontend.redact_sensitive_fields,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=False,
        )  # The stdlib handlers remain the level, output, and redaction backend.


class SensitiveFilter(logging.Filter):
    """Redact credential-shaped values in messages and exception tracebacks.

    Install on a handler to provide a defence-in-depth layer: even if a
    caller accidentally logs a raw password, this filter replaces it before
    the message reaches the handler's output (file, console, syslog, and so on).

    Usage::

        handler = logging.StreamHandler()
        handler.addFilter(SensitiveFilter())
        logging.getLogger().addHandler(handler)

    The filter uses the same regex patterns as ``redact_if_sensitive()``.
    It sanitizes the formatted message and the exception text cache before a
    standard handler formats the record. This includes exception chains and
    cached text from earlier handlers. Safe traceback context stays visible.
    Credential separators do not cross line boundaries. Ordinary credential
    labels also recognize spaces and tabs without assignment punctuation.
    Only an exact menu entry from the console writer keeps its static title.
    Untrusted text and all exception text use the conservative redaction rule.
    Authorization headers protect the complete remaining line, including structured parameters.
    Any same-line diagnostic after that header is also removed.
    The exact email verification URL route protects its nonempty suffix,
    including punctuation, query, and fragment text, until whitespace.
    Adjacent non-whitespace diagnostic punctuation is also removed because
    punctuation alone cannot identify the end of a credential.
    Arbitrary unlabeled secrets and direct SDK console output are outside
    this pattern-based handler contract.

    The filter does not log its own actions because recursive logging can
    re-enter the filter. If rendering fails, it emits a safe diagnostic instead.
    """

    # Simple value-redaction pattern: anything after an = or : that looks like
    # it belongs to a sensitive key.  Matches patterns like:
    #   password=abc123  or  "password": "abc123"
    _VALUE_PATTERN = re.compile(  # Compiled once at class load for performance
        r"(?P<key>" + _SENSITIVE_KEY_PATTERNS.pattern + r')[=: \t"\']+(?P<value>\S+)',
        re.IGNORECASE,
    )
    _AUTHORIZATION_PATTERN = re.compile(
        r"""(?P<key>authorization)[ \t"']*[:=][ \t]*[^ \t\r\n][^\r\n]*""",
        re.IGNORECASE,
    )
    _VERIFICATION_URL_PATTERN = re.compile(
        r"""(?P<route>(?<![\w/])(?:(?i:https?)://[^/\s<>"'?#]+)?/api/v1/self/update/verify/)\S+"""
    )

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize a record in place without suppressing safe diagnostics."""
        try:
            if isinstance(record.msg, dict):  # Structlog passes an event dictionary to stdlib.
                record.msg = _redact_sensitive_event_dict(record.msg)  # Redact keys without string conversion.
                record.args = ()  # Keep the event dictionary as the ProcessorFormatter input.
                self._redact_traceback(record)  # Protect any exception text on the same record.
                return True  # Continue with the preserved dict event.
            message = record.getMessage()
            trusted_menu_message = self._is_trusted_menu_record(
                record, message
            )  # WHY: mark static rows, not caller text.
            sanitized = (
                message if trusted_menu_message else self._redact_text(message)
            )  # WHY: redact each other message.
            if sanitized != message:
                record.msg = sanitized
                record.args = ()
            self._redact_traceback(record)
        except Exception as error:
            record.msg = "Log redaction failed: %s"
            record.args = (type(error).__name__,)
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
        return True

    def _is_trusted_menu_record(self, record: logging.LogRecord, message: str) -> bool:
        """Trust only the exact static menu entry emitted by the console writer."""
        from src.foundation.support.utils.menu_entry import (
            MenuEntry,  # WHY: immutable rows define the trusted message source.
        )

        entry = getattr(record, "_misthelper_menu_entry", None)  # WHY: only the writer attaches this provenance field.
        expected = (
            f"{entry.menu_id}: {entry.title}" if isinstance(entry, MenuEntry) else ""
        )  # WHY: match the registered key and title.
        return (
            record.name == "src.foundation.support.utils.console"  # WHY: trust only the writer logger.
            and isinstance(entry, MenuEntry)  # WHY: a plain string cannot claim trusted provenance.
            and not record.args  # WHY: formatting arguments cannot alter the registered title.
            and message == expected  # WHY: trust applies only to the exact writer output.
        )

    def _redact_text(self, text: str) -> str:
        """Apply the same credential rule to message and exception text."""
        text = self._VERIFICATION_URL_PATTERN.sub(r"\g<route>***REDACTED***", text)
        text = self._AUTHORIZATION_PATTERN.sub(r"\g<key>=***REDACTED***", text)
        return self._VALUE_PATTERN.sub(r"\g<key>=***REDACTED***", text)

    def _redact_traceback(self, record: logging.LogRecord) -> None:
        """Protect the exception cache, including text from earlier handlers."""
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = self._redact_text(record.exc_text)
