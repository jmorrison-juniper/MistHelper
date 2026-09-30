"""Tests for safe display values and reason validation."""

import pytest

from src.reports.org_security_posture.io.formatting import SecurityPostureFormatting


def test_display_value_redacts_secret_fields() -> None:
    value = SecurityPostureFormatting.display_value({"api_token": "secret", "name": "visible"})  # Redact token values.
    assert "secret" not in value  # Secret values must not be exported.
    assert "redacted" in value  # Redaction must remain visible to reviewers.


def test_validate_reason_rejects_multiple_sentences() -> None:
    with pytest.raises(ValueError):  # Multiple sentences violate the CSV contract.
        SecurityPostureFormatting.validate_reason("First sentence. Second sentence.")


def test_display_value_formats_absent_value() -> None:
    assert SecurityPostureFormatting.display_value(None) == "absent"  # Missing settings must display as absent.
