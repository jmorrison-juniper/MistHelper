"""API posture checks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.mist.intelligence.reports.org_security_posture.checks.base import BaseSecurityPostureCheck
from src.mist.intelligence.reports.org_security_posture.models import (
    OrganizationSecuritySourceData,
    SecurityPostureCheckResult,
)


class ApiAccessRestrictionCheck(BaseSecurityPostureCheck):
    """Check that API access is disabled or restricted."""

    check_id = "ORGSEC-API-001"
    area = "API policy"
    setting_path = "organization settings > API policy > API access"
    recommended_value = "`disabled`, `restricted`, or `admins_only`"
    source_page = "Mist Organization Settings > API Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether API access is disabled or restricted."""
        value = self.get_setting(source_data, "api_policy", "access")  # Read the API access posture.
        if value is None:  # Absent API settings need a visible review verdict.
            return self.result(None, "review", "The API access setting is absent and needs manual review.")
        if not isinstance(value, str):  # Non-string API modes are ambiguous evidence.
            return self.result(value, "review", "The API access setting value could not be interpreted.")
        normalized = value.lower().strip()  # Normalize the API mode before comparison.
        if normalized in {"disabled", "restricted", "admins_only"}:  # These modes keep access controlled.
            return self.result(value, "pass", "The API access setting matches the recommended value.")
        if normalized in {"enabled", "unrestricted", "all_admins"}:  # These modes allow broad API use.
            return self.result(value, "fail", "The API access setting allows broad access.")
        return self.result(value, "review", "The API access setting value could not be interpreted.")


class ApiTokenExpirationCheck(BaseSecurityPostureCheck):
    """Check that visible API tokens expire within one year."""

    check_id = "ORGSEC-API-002"
    area = "API policy"
    setting_path = "organization settings > API policy > token expiration"
    recommended_value = "API tokens expire within 365 days or less"
    source_page = "Mist Organization Settings > API Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether API tokens expire within the baseline."""
        if not source_data.org_api_tokens:  # No token evidence means the reviewer must confirm token posture.
            return self.result(None, "review", "The API token expiration evidence is absent and needs manual review.")
        expirations = [
            self._read_token_days(token) for token in source_data.org_api_tokens
        ]  # Read each token lifespan.
        if any(days is None for days in expirations):  # Unknown dates cannot prove token expiration posture.
            summary = self._token_count_summary(source_data.org_api_tokens, expirations)  # Summarize only counts.
            return self.result(summary, "review", "An API token expiration value is absent and needs review.")
        known_expirations = [days for days in expirations if days is not None]  # Narrow values for type checking.
        if any(days > 365 for days in known_expirations):  # Any long-lived token fails the check.
            return self.result(
                max(known_expirations), "fail", "At least one API token expires after more than 365 days."
            )
        return self.result(
            max(known_expirations), "pass", "All visible API tokens expire within the recommended limit."
        )

    @staticmethod
    def _token_count_summary(tokens: list[dict[str, Any]], expirations: list[int | None]) -> str:
        """Return a safe count summary for token evidence."""
        token_count = len(tokens)  # Count visible token records without exporting their contents.
        missing_count = sum(1 for days in expirations if days is None)  # Count records with unclear lifetime data.
        return f"{token_count} token records checked, {missing_count} missing expiration values"  # Export no secrets.

    @staticmethod
    def _read_token_days(token: dict[str, Any]) -> int | None:
        """Return token lifetime in days when creation and expiration are readable."""
        created = ApiTokenExpirationCheck._parse_datetime(
            token.get("created_time") or token.get("created_at")
        )  # Read start.
        expires = ApiTokenExpirationCheck._parse_datetime(
            token.get("expire_time") or token.get("expires_at")
        )  # Read end.
        if created is None or expires is None:  # Both timestamps are required for lifespan evidence.
            return None
        return max((expires - created).days, 0)  # Avoid negative values when API data is inconsistent.

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Return a timezone-aware datetime from common API timestamp shapes."""
        if isinstance(value, int | float):  # Mist APIs often use epoch seconds for timestamps.
            return datetime.fromtimestamp(value, tz=UTC)
        if isinstance(value, str):  # ISO strings appear in fixtures and some API payloads.
            cleaned = value.replace("Z", "+00:00")  # Python parses explicit UTC offsets.
            try:
                return datetime.fromisoformat(cleaned)  # Convert readable ISO data to a datetime.
            except ValueError:
                return None  # Unreadable strings require review.
        return None  # Unknown timestamp shapes require review.


class ApiWebhookHttpsCheck(BaseSecurityPostureCheck):
    """Check that all webhook URLs use HTTPS."""

    check_id = "ORGSEC-API-003"
    area = "API policy"
    setting_path = "organization settings > API policy > webhook URLs"
    recommended_value = "Every configured webhook URL uses https://"
    source_page = "Mist Organization Settings > API Policy"

    def run(self, source_data: OrganizationSecuritySourceData) -> SecurityPostureCheckResult:
        """Evaluate whether every visible webhook uses HTTPS."""
        urls = [
            url for webhook in source_data.org_webhooks for url in self._read_urls(webhook)
        ]  # Flatten webhook URLs.
        if not urls:  # No webhook evidence means the reviewer must confirm no webhook exists.
            return self.result(None, "review", "The webhook URL evidence is absent and needs manual review.")
        if any(not url.lower().startswith("https://") for url in urls):  # HTTP or other schemes fail the check.
            return self.result(urls, "fail", "At least one webhook URL uses non-HTTPS transport.")
        return self.result(urls, "pass", "Every visible webhook URL uses HTTPS transport.")

    @staticmethod
    def _read_urls(webhook: dict[str, Any]) -> list[str]:
        """Return URL strings from known webhook payload fields."""
        raw_value = webhook.get("url") or webhook.get("urls") or webhook.get("webhook_url")  # Try known URL keys.
        if isinstance(raw_value, str):  # A single webhook URL is the common payload shape.
            return [raw_value]
        if isinstance(raw_value, list):  # Some payloads can hold more than one URL.
            return [item for item in raw_value if isinstance(item, str)]
        return []  # Unknown shapes provide no usable URL evidence.
