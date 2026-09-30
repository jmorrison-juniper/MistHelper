"""Formatting helpers for security posture rows."""

from __future__ import annotations

from typing import Any

SECRET_MARKERS = ("token", "secret", "password", "key", "credential")


class SecurityPostureFormatting:
    """Validate row text and protect sensitive display values."""

    @staticmethod
    def display_value(value: Any) -> str:
        """Return a safe display value for CSV output."""
        if value is None:  # Treat missing values consistently across all checks.
            return "absent"
        if isinstance(value, bool):  # Convert booleans to operator-facing words.
            return "enabled" if value else "disabled"
        if isinstance(value, dict):  # Redact nested values that can hold secrets.
            return SecurityPostureFormatting._display_mapping(value)
        if isinstance(value, list):  # Keep list output readable without exposing nested secrets.
            return SecurityPostureFormatting._display_list(value)
        return str(value)  # Use the existing value when no redaction rule applies.

    @staticmethod
    def validate_reason(reason: str) -> str:
        """Return one sentence, or raise when the reason violates the contract."""
        stripped = reason.strip()  # Normalize whitespace before validation.
        if not stripped:  # The CSV contract requires a reason for every row.
            raise ValueError("Reason must not be blank.")
        sentence_count = stripped.count(".") + stripped.count("!") + stripped.count("?")  # Count sentence endings.
        if sentence_count != 1 or stripped[-1] not in ".!?":  # Enforce one sentence for reviewer clarity.
            raise ValueError("Reason must be one sentence.")
        return stripped  # Return the validated reason for result construction.

    @staticmethod
    def _display_mapping(value: dict[str, Any]) -> str:
        """Return a safe string for a mapping."""
        redacted = {  # Build a sanitized copy before string conversion.
            key: "redacted" if SecurityPostureFormatting._is_secret_key(key) else item for key, item in value.items()
        }
        return str(redacted)  # Preserve enough evidence for reviewers without secrets.

    @staticmethod
    def _display_list(value: list[Any]) -> str:
        """Return a safe string for a list."""
        safe_items = [SecurityPostureFormatting.display_value(item) for item in value]  # Redact each nested item.
        return ", ".join(safe_items) if safe_items else "absent"  # Keep empty lists equivalent to no value.

    @staticmethod
    def _is_secret_key(key: str) -> bool:
        """Return whether a key name can contain a secret."""
        lowered_key = key.lower()  # Compare markers without case sensitivity.
        return any(marker in lowered_key for marker in SECRET_MARKERS)  # Redact names that indicate sensitive data.
