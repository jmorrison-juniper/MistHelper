"""Unit tests for src/foundation/support/utils/logger_utils.py.

Covers: redact_secret, redact_if_sensitive, and SensitiveFilter.filter.
All tests are pure logic -- no external dependencies, no API calls.

Target audience: Junior NOC engineers verifying that credentials are
never written to log files regardless of how callers use the logging API.
"""

from __future__ import annotations  # Enable PEP 604 union types on Python 3.10+

import logging  # Standard library logging for creating test LogRecord objects
import sys
from io import StringIO
from unittest.mock import Mock

import pytest

from src.foundation.support.utils.logger_utils import (  # Module under test
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


class TestSensitiveTracebacks:
    """Prove that complete handler output protects synthetic exception values."""

    token = "ISSUE4704_SYNTHETIC_TOKEN"
    password = "ISSUE4704_SYNTHETIC_PASSWORD"

    def _record(self, chain: str = "direct") -> logging.LogRecord:
        """Build a real exception chain without external services."""
        try:
            try:
                message = "Host unreachable" if chain == "safe" else f"token={self.token}"
                raise ValueError(message)
            except ValueError as error:
                if chain == "cause":
                    raise RuntimeError(f"password={self.password}") from error
                if chain == "context":
                    raise RuntimeError(f"password={self.password}")  # noqa: B904 - This case must use implicit context.
                if chain == "group":
                    failures = [error, RuntimeError(f"password={self.password}")]
                    raise ExceptionGroup("Dependency failures", failures) from None
                if chain == "note":
                    error.add_note(f"password={self.password}")
                raise
        except Exception:
            return logging.makeLogRecord({"msg": "Dependency failed", "exc_info": sys.exc_info()})

    @pytest.mark.parametrize("chain", ["direct", "cause", "context", "group", "note"])
    @pytest.mark.parametrize("cached", [False, True])
    def test_complete_stream_output(self, chain: str, cached: bool) -> None:
        """Keep frames and exception types while redacting fresh and cached text."""
        record = self._record(chain)
        original_exception = record.exc_info
        if cached:
            raw = logging.Formatter().format(record)
            assert self.token in raw, "The earlier formatter did not render the synthetic value."
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.addFilter(SensitiveFilter())
        handler.handle(record)
        handler.handle(record)
        rendered = output.getvalue()
        handler.close()
        assert self.token not in rendered and self.password not in rendered
        assert REDACTED_PLACEHOLDER in rendered
        assert rendered.count("Dependency failed") == 2
        assert "Traceback" in rendered and "_record" in rendered and "ValueError" in rendered
        assert record.exc_info is original_exception, "Redaction changed the exception objects."
        if chain in ("cause", "context", "group"):
            assert "RuntimeError" in rendered
        if chain == "cause":
            assert "The above exception was the direct cause" in rendered
        if chain == "context":
            assert "During handling of the above exception" in rendered

    def test_cached_text_without_exception_info(self) -> None:
        """Protect a record whose earlier handler supplied only cached text."""
        record = logging.LogRecord("redaction.probe", logging.ERROR, __file__, 1, "Safe message", (), None)
        record.exc_text = f"ValueError: token={self.token}\nUseful frame context"
        assert SensitiveFilter().filter(record) is True
        rendered = logging.Formatter().format(record)
        assert self.token not in rendered
        assert REDACTED_PLACEHOLDER in rendered
        assert "ValueError" in rendered and "Useful frame context" in rendered and "Safe message" in rendered

    def test_safe_traceback_matches_standard_output(self) -> None:
        """Leave safe messages and tracebacks unchanged, including their cache."""
        record = self._record("safe")
        expected = logging.Formatter().format(record)
        assert SensitiveFilter().filter(record) is True
        assert logging.Formatter().format(record) == expected
        assert "Host unreachable" in expected

    @pytest.mark.parametrize("failure", ["message", "traceback"])
    def test_redaction_failure_excludes_unsafe_fields(self, failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """A redaction error must not expose either exception value."""

        class UnrenderableMessage:
            """Raise a synthetic credential-bearing error during message rendering."""

            def __str__(self) -> str:
                """Fail without a real credential."""
                raise RuntimeError("token=ISSUE4704_SYNTHETIC_RENDER_ERROR")

        record = self._record()
        if failure == "message":
            record.msg = UnrenderableMessage()
        else:
            monkeypatch.setattr(
                logging.Formatter, "formatException", Mock(side_effect=RuntimeError(f"token={self.token}"))
            )
        assert SensitiveFilter().filter(record) is True
        rendered = logging.Formatter().format(record)
        assert rendered == "Log redaction failed: RuntimeError"
        assert record.exc_info is None and record.exc_text is None


class TestLabeledCredentials:
    """Keep credential matching on one line and cover complete header values."""

    @pytest.mark.parametrize(
        "message",
        [
            "Authorization: Bearer ISSUE4705_SYNTHETIC_VALUE",
            "aUtHoRiZaTiOn: bEaReR ISSUE4705_SYNTHETIC_VALUE",
            "AUTHORIZATION: Basic ISSUE4705_SYNTHETIC_VALUE",
            "Authorization: Custom-Scheme ISSUE4705_SYNTHETIC_VALUE",
            "Authorization: ISSUE4705_SYNTHETIC_VALUE",
            "Authorization=Bearer\tISSUE4705_SYNTHETIC_VALUE",
            '"Authorization": "Bearer ISSUE4705_SYNTHETIC_VALUE"',
            "password=ISSUE4705_SYNTHETIC_VALUE",
            "token: ISSUE4705_SYNTHETIC_VALUE",
            "api_key=ISSUE4705_SYNTHETIC_VALUE",
            'Authorization: Digest username="synthetic", realm="example", response="ISSUE4705_SYNTHETIC_VALUE"',
            (
                "Authorization: AWS4-HMAC-SHA256 Credential=synthetic, SignedHeaders=host, "
                "Signature=ISSUE4705_SYNTHETIC_VALUE"
            ),
        ],
    )
    def test_complete_labeled_value_is_removed(self, message: str) -> None:
        """A credential scheme must not conceal the value from redaction."""
        record = logging.makeLogRecord({"msg": message})
        assert SensitiveFilter().filter(record) is True
        assert "ISSUE4705_SYNTHETIC_VALUE" not in record.getMessage()
        assert REDACTED_PLACEHOLDER in record.getMessage()

    @pytest.mark.parametrize("ending", ["token", "password", "auth", "Authorization:"])
    @pytest.mark.parametrize("newline", ["\n", "\r\n"])
    def test_empty_label_does_not_consume_next_line(self, ending: str, newline: str) -> None:
        """A label without a value must leave the following diagnostic intact."""
        message = f"Invalid {ending}{newline}{newline}The above exception was the direct cause"
        record = logging.makeLogRecord({"msg": message})
        assert SensitiveFilter().filter(record) is True
        assert record.getMessage() == message

    @pytest.mark.parametrize("newline", ["\n", "\r\n"])
    def test_complete_header_stops_at_line_boundary(self, newline: str) -> None:
        """Protect all parameters without removing the next safe diagnostic."""
        message = (
            f'Authorization: Digest username="synthetic", response="ISSUE4705_SYNTHETIC_VALUE"{newline}Safe context'
        )
        record = logging.makeLogRecord({"msg": message})
        assert SensitiveFilter().filter(record) is True
        assert record.getMessage() == f"Authorization={REDACTED_PLACEHOLDER}{newline}Safe context"

    def test_unlabeled_text_is_outside_the_redaction_contract(self) -> None:
        """Do not claim recognition of an arbitrary unlabeled value."""
        message = "Request failed ISSUE4705_SYNTHETIC_UNLABELED"
        record = logging.makeLogRecord({"msg": message})
        assert SensitiveFilter().filter(record) is True
        assert record.getMessage() == message
