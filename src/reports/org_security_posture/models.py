"""Data model for the organization security posture report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Protocol

Verdict = Literal["pass", "fail", "review"]


@dataclass(frozen=True)
class SecurityPostureCheckResult:
    """One exported checklist row."""

    check_id: str
    area: str
    setting_path: str
    current_value: str
    recommended_value: str
    verdict: Verdict
    reason: str

    def to_row(self) -> dict[str, str]:
        """Return the exact CSV row shape required by the contract."""
        return {  # Map internal field names to the user-facing CSV headings.
            "check id": self.check_id,  # Keep the stable check identifier visible to reviewers.
            "area": self.area,  # Keep the posture area visible for triage.
            "setting path": self.setting_path,  # Name the exact setting a reviewer must inspect.
            "current value": self.current_value,  # Show the redacted source value or review state.
            "recommended value": self.recommended_value,  # Show the secure target beside the evidence.
            "verdict": self.verdict,  # Use the fixed verdict vocabulary from the contract.
            "reason": self.reason,  # Give the reviewer one sentence that explains the verdict.
        }


@dataclass(frozen=True)
class OrganizationSecuritySourceData:
    """Source payloads collected once for all checks."""

    org_settings: dict[str, Any]
    org_ssos: list[dict[str, Any]]
    org_admins: list[dict[str, Any]]
    org_api_tokens: list[dict[str, Any]]
    org_webhooks: list[dict[str, Any]]


class SecurityPostureCheck(Protocol):
    """Interface that each small posture check class implements."""

    check_id: ClassVar[str]
    area: ClassVar[str]
    setting_path: ClassVar[str]
    recommended_value: ClassVar[str]
    source_page: ClassVar[str]

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate this check against previously collected source data."""
