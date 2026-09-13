"""Unit tests for src/utils/logger_utils.py.

Covers: redact_secret, redact_if_sensitive, and SensitiveFilter.filter.
All tests are pure logic -- no external dependencies, no API calls.

Target audience: Junior NOC engineers verifying that credentials are
never written to log files regardless of how callers use the logging API.
"""

from __future__ import annotations  # Enable PEP 604 union types on Python 3.10+

import logging  # Standard library logging for creating test LogRecord objects

from src.utils.logger_utils import (  # Module under test
    REDACTED_PLACEHOLDER,  # The canonical replacement string
    SensitiveFilter,  # Logging filter class
    redact_if_sensitive,  # Conditional redaction helper
    redact_secret,  # Unconditional redaction helper
)

# ---------------------------------------------------------------------------
# redact_secret
# ---------------------------------------------------------------------------


class TestRedactSecret:
    """Tests for redact_secret -- unconditional value replacement."""

    def test_returns_placeholder_for_any_string(self):  # Happy path
        """Any string passed to redact_secret is replaced with the placeholder."""
        result = redact_secret("super-secret-password-123")  # Pass a realistic credential
        assert result == REDACTED_PLACEHOLDER  # Value must be replaced entirely

    def test_returns_placeholder_for_empty_string(self):  # Edge case: empty value
        """Empty string is also replaced with the placeholder."""
        result = redact_secret("")  # Pass an empty credential
        assert result == REDACTED_PLACEHOLDER  # Even empty string is replaced

    def test_return_value_is_constant(self):  # Return value is predictable
        """Return value equals the module-level REDACTED_PLACEHOLDER constant."""
        assert redact_secret("anything") == REDACTED_PLACEHOLDER  # Verify constant match


# ---------------------------------------------------------------------------
# redact_if_sensitive
# ---------------------------------------------------------------------------


class TestRedactIfSensitive:
    """Tests for redact_if_sensitive -- key-pattern-based conditional redaction."""

    def test_sensitive_key_password_redacted(self):  # Key 'password' triggers redaction
        """Value is redacted when key is 'password'."""
        result = redact_if_sensitive("password", "my-secret")  # Sensitive key
        assert result == REDACTED_PLACEHOLDER  # Value must be replaced

    def test_sensitive_key_api_token_redacted(self):  # Key 'api_key' triggers redaction
        """Value is redacted when key is 'api_key'."""
        result = redact_if_sensitive("api_key", "tok_abc123")  # Sensitive key
        assert result == REDACTED_PLACEHOLDER  # Value must be replaced

    def test_non_sensitive_key_passes_through(self):  # Key 'hostname' is not sensitive
        """Value passes through unchanged when key does not match a sensitive pattern."""
        result = redact_if_sensitive("hostname", "192.168.1.1")  # Non-sensitive key
        assert result == "192.168.1.1"  # Value should be returned unchanged

    def test_case_insensitive_key_matching(self):  # Key 'PASSWORD' should match too
        """Key matching is case-insensitive (PASSWORD triggers the same as password)."""
        result = redact_if_sensitive("PASSWORD", "my-secret")  # Uppercase key
        assert result == REDACTED_PLACEHOLDER  # Should still trigger redaction

    def test_partial_key_match(self):  # Key 'auth_token' contains 'token' -- should match
        """Keys containing a sensitive substring (e.g. 'token') trigger redaction."""
        result = redact_if_sensitive("auth_token", "bearer-xyz")  # Key contains 'token'
        assert result == REDACTED_PLACEHOLDER  # Substring match triggers redaction


# ---------------------------------------------------------------------------
# SensitiveFilter
# ---------------------------------------------------------------------------


class TestSensitiveFilter:
    """Tests for SensitiveFilter.filter -- in-place log message sanitisation."""

    def _make_record(self, msg: str, args: tuple = ()) -> logging.LogRecord:  # Helper: create a LogRecord
        """Return a LogRecord with the given message and args."""
        record = logging.LogRecord(  # Minimal LogRecord for testing
            name="test",  # Logger name
            level=logging.DEBUG,  # Log level (unused in filter logic)
            pathname="",  # File path (unused)
            lineno=0,  # Line number (unused)
            msg=msg,  # The format string
            args=args,  # Format arguments
            exc_info=None,  # No exception info
        )
        return record  # Return the constructed record

    def test_credential_value_is_scrubbed(self):  # Message contains 'password=secret'
        """Filter replaces the value after a sensitive key in the log message."""
        flt = SensitiveFilter()  # Create filter instance
        record = self._make_record("Connecting with password=hunter2")  # Credential in message
        returned = flt.filter(record)  # Apply filter in-place
        assert returned is True  # Filter always returns True (never suppresses)
        assert "hunter2" not in record.getMessage()  # Plaintext credential removed
        assert "REDACTED" in record.getMessage()  # Replacement placeholder present

    def test_non_credential_message_unchanged(self):  # Normal message passes through
        """Filter does not modify log messages that contain no credential patterns."""
        flt = SensitiveFilter()  # Create filter instance
        record = self._make_record("Connected to host 192.168.1.1 on port 443")  # No credentials
        flt.filter(record)  # Apply filter
        assert "192.168.1.1" in record.getMessage()  # Non-sensitive value preserved
        assert "REDACTED" not in record.getMessage()  # No placeholder injected

    def test_filter_always_returns_true(self):  # Filter must never suppress records
        """filter() always returns True, even for sensitive messages."""
        flt = SensitiveFilter()  # Create filter instance
        record = self._make_record("token=abc123secret")  # Sensitive message
        result = flt.filter(record)  # Apply filter
        assert result is True  # Must return True to pass the record to the handler

    def test_args_cleared_after_redaction(self):  # Args must be cleared so getMessage() uses new msg
        """After redaction, record.args is cleared to prevent double-formatting."""
        flt = SensitiveFilter()  # Create filter instance
        record = self._make_record("Using password=%s", ("real-password",))  # Message with args
        flt.filter(record)  # Apply filter
        assert record.args == () or record.args == ()  # Args should be cleared after sanitisation

    def test_exception_in_filter_does_not_propagate(self):  # Filter must be fault-tolerant
        """Filter silently ignores exceptions rather than crashing the logging pipeline."""
        flt = SensitiveFilter()  # Create filter instance
        record = self._make_record("normal message")  # A normal record
        record.msg = None  # Inject a None msg to trigger an internal exception in getMessage()
        result = flt.filter(record)  # Apply filter -- should not raise
        assert result is True  # Must still return True even when an exception occurs internally

    def test_format_error_in_getmessage_is_caught(self):  # Lines 113-114: except Exception: pass
        """Lines 113-114: TypeError during getMessage() formatting hits except block, returns True."""
        flt = SensitiveFilter()  # Create filter instance
        # Mismatched format args: msg has 2 placeholders but args only supplies 1 → TypeError
        record = self._make_record("need %s and %s", args=("only_one",))  # Wrong arg count
        result = flt.filter(record)  # getMessage() raises TypeError → except catches → True
        assert result is True  # Filter always returns True; exception was silently swallowed
