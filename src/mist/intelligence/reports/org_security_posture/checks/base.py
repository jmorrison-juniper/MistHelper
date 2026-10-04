"""Shared helpers for individual posture checks."""

from __future__ import annotations

from typing import Any, ClassVar

from src.mist.intelligence.reports.org_security_posture.io.formatting import SecurityPostureFormatting
from src.mist.intelligence.reports.org_security_posture.models import (
    OrganizationSecuritySourceData,
    SecurityPostureCheckResult,
    Verdict,
)


class BaseSecurityPostureCheck:
    """Base class for one small setting check."""

    check_id: ClassVar[str]
    area: ClassVar[str]
    setting_path: ClassVar[str]
    recommended_value: ClassVar[str]
    source_page: ClassVar[str]

    def result(self, current_value: Any, verdict: Verdict, reason: str) -> SecurityPostureCheckResult:
        """Build one contract-compliant result row."""
        safe_value = SecurityPostureFormatting.display_value(current_value)  # Redact and normalize evidence.
        safe_reason = SecurityPostureFormatting.validate_reason(reason)  # Fail fast when a reason is not one sentence.
        return SecurityPostureCheckResult(  # Centralize row construction for every check class.
            check_id=self.check_id,
            area=self.area,
            setting_path=self.setting_path,
            current_value=safe_value,
            recommended_value=self.recommended_value,
            verdict=verdict,
            reason=safe_reason,
        )

    def get_setting(self, source_data: OrganizationSecuritySourceData, *path: str) -> Any:
        """Return a nested org setting value, or None when it is absent."""
        value: Any = source_data.org_settings  # Start at the full settings document.
        for key in path:  # Walk one known path segment at a time.
            if not isinstance(value, dict) or key not in value:  # Missing or non-object values need review.
                return None
            value = value[key]  # Advance to the next nested value.
        return value  # Return the exact setting value for the check rule.

    def get_first_setting(self, source_data: OrganizationSecuritySourceData, paths: tuple[tuple[str, ...], ...]) -> Any:
        """Return the first present value from equivalent API setting paths."""
        for path in paths:  # Try new and legacy field names in a deterministic order.
            value = self.get_setting(source_data, *path)  # Reuse the safe nested lookup for each path.
            if value is not None:  # The first present value is the best evidence for this check.
                return value
        return None  # No equivalent path was present, so the check must return review.

    def boolean_enabled_result(self, value: Any, secure_enabled: bool) -> SecurityPostureCheckResult:
        """Evaluate a boolean setting against the expected enabled state."""
        if value is None:  # Absent values must not pass.
            return self.result(None, "review", "The setting is absent and needs manual review.")
        if not isinstance(value, bool):  # Unexpected types are ambiguous evidence.
            return self.result(value, "review", "The setting value could not be interpreted.")
        if value is secure_enabled:  # Clear match to the recommended state passes.
            return self.result(value, "pass", "The setting matches the recommended value.")
        return self.result(value, "fail", "The setting does not match the recommended value.")

    def integer_minimum_result(self, value: Any, minimum_value: int) -> SecurityPostureCheckResult:
        """Evaluate an integer setting that must be at least a minimum."""
        parsed_value = self._parse_integer(value)  # Normalize string and integer payloads.
        if parsed_value is None:  # Absent or unclear values require review.
            reason = (
                "The setting is absent and needs manual review."
                if value is None
                else "The setting value could not be interpreted."
            )
            return self.result(value, "review", reason)
        if parsed_value >= minimum_value:  # Values at or above the target pass.
            return self.result(parsed_value, "pass", "The setting matches the recommended value.")
        return self.result(parsed_value, "fail", "The setting is below the recommended value.")

    def integer_maximum_result(self, value: Any, maximum_value: int) -> SecurityPostureCheckResult:
        """Evaluate an integer setting that must be no more than a maximum."""
        parsed_value = self._parse_integer(value)  # Normalize string and integer payloads.
        if parsed_value is None:  # Absent or unclear values require review.
            reason = (
                "The setting is absent and needs manual review."
                if value is None
                else "The setting value could not be interpreted."
            )
            return self.result(value, "review", reason)
        if parsed_value <= maximum_value:  # Values at or below the target pass.
            return self.result(parsed_value, "pass", "The setting matches the recommended value.")
        return self.result(parsed_value, "fail", "The setting is above the recommended value.")

    @staticmethod
    def _parse_integer(value: Any) -> int | None:
        """Return an integer value when the payload is unambiguous."""
        if isinstance(value, bool):  # Booleans are integers in Python but not valid numeric settings here.
            return None
        if isinstance(value, int):  # Native integer values can be evaluated directly.
            return value
        if isinstance(value, str) and value.strip().isdigit():  # Numeric strings are common in API payloads.
            return int(value.strip())
        return None  # Any other shape needs manual review.
