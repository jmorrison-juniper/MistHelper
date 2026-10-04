"""Tests for bounded transport structured logging."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Every emitted message must parse as one JSON object.
import logging  # caplog captures records from the standard logging system.

import pytest  # Parametrized redaction cases cover each required secret class.

from src.mist.realtime.websocket_streams.live.transport.runtime.logging.bounds import (
    MAX_EVENT_LENGTH,
    MAX_FIELD_LENGTH,
    REDACTED_VALUE,
)
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)


def _records(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    """Parse every captured message as JSON."""
    return [json.loads(record.message) for record in caplog.records]  # Fail if any record is not valid JSON.


def test_records_are_ascii_json_with_only_bounded_safe_fields(caplog: pytest.LogCaptureFixture) -> None:
    """Emit parseable ASCII JSON and reject or bound unsafe fields."""
    target = logging.getLogger("test.transport.bounds")  # Use one isolated capture logger.
    logger = StructuredTransportLogger(target)  # Apply the production logging boundary.
    event = f"{'e' * 200}\u2603"  # Build an overlong non-ASCII event before the logging action.
    detail = f"{'d' * 200}\u2603"  # Build an overlong non-ASCII safe field before the logging action.
    with caplog.at_level(logging.DEBUG, logger=target.name):  # Capture the emitted debug record.
        logger.emit(
            logging.DEBUG, event, {"detail": detail, "count": 10**20, "unknown": "drop"}
        )  # Emit one hostile record.
    message = caplog.records[0].message  # Inspect the exact serialized log message.
    parsed = _records(caplog)[0]  # Parse the record through the standard JSON parser.
    assert message.isascii()  # JSON escaping must keep the complete log message ASCII.
    assert set(parsed) == {"count", "detail", "event"}  # Only allowlisted fields can enter the record.
    assert len(str(parsed["event"])) == MAX_EVENT_LENGTH  # Bound the event name.
    assert len(str(parsed["detail"])) == MAX_FIELD_LENGTH  # Bound safe text values.
    assert parsed["count"] == 1_000_000_000  # Clamp hostile numeric values.


@pytest.mark.parametrize(
    ("field", "secret"),
    [
        ("token", "mist_token_123"),
        ("cookie", "session=secret-cookie"),
        ("shell_url", "wss://api.example.test/shell/private"),
        ("shell_path", "/api/v1/sites/private/shell"),
        ("private_key", "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----"),
        ("pasted_text", "configure private secret"),
        ("terminal_output", "switch> show confidential"),
    ],
)
def test_sensitive_fields_are_redacted_at_boundary(caplog: pytest.LogCaptureFixture, field: str, secret: str) -> None:
    """Redact each required secret class before standard logging receives it."""
    target = logging.getLogger(f"test.transport.redaction.{field}")  # Isolate each parametrized log capture.
    logger = StructuredTransportLogger(target)  # Apply the production logging boundary.
    with caplog.at_level(logging.INFO, logger=target.name):  # Capture one information record.
        logger.emit(
            logging.INFO, "boundary_test", {field: secret, "status": "safe"}
        )  # Submit the secret at the boundary.
    parsed = _records(caplog)[0]  # Parse the emitted record as JSON.
    assert secret not in caplog.records[0].message  # Never pass the original secret to a handler.
    assert field in parsed["redacted"]  # Record only which sensitive field was removed.
    assert parsed["status"] == "safe"  # Preserve unrelated safe metadata.


@pytest.mark.parametrize(
    "detail",
    [
        "Authorization: token-secret",
        "Bearer bearer-secret",
        "Cookie: cookie-secret",
        "session=session-secret",
        "wss://api.example.test/shell/private",
        "C:\\private\\shell\\capture.txt",
        "-----BEGIN OPENSSH PRIVATE KEY----- secret",
    ],
)
def test_safe_text_values_redact_embedded_secrets(caplog: pytest.LogCaptureFixture, detail: str) -> None:
    """Remove recognized secret forms from an otherwise safe text field."""
    target = logging.getLogger("test.transport.embedded")  # Use one capture logger for embedded values.
    logger = StructuredTransportLogger(target)  # Apply the production logging boundary.
    with caplog.at_level(logging.DEBUG, logger=target.name):  # Capture one debug record.
        logger.emit(logging.DEBUG, "embedded_secret", {"detail": detail})  # Submit the secret in an allowlisted field.
    message = caplog.records[0].message  # Inspect the exact serialized boundary output.
    assert detail not in message  # The complete original secret form must not reach a handler.
    assert REDACTED_VALUE in _records(caplog)[0]["detail"]  # The parsed field must show redaction.
