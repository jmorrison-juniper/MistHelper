"""API posture fixture cases."""

from src.reports.org_security_posture.models import OrganizationSecuritySourceData


class ApiPostureCases:
    """Build source data for API edge-case checks."""

    @staticmethod
    def absent_api_policy() -> OrganizationSecuritySourceData:
        """Return source data with no API policy setting."""
        return OrganizationSecuritySourceData({}, [], [], [], [])  # Empty source data forces review verdicts.

    @staticmethod
    def non_https_webhook() -> OrganizationSecuritySourceData:
        """Return source data with a non-HTTPS webhook URL."""
        settings = {"api_policy": {"access": "restricted"}}  # Keep access secure so webhook is the tested defect.
        webhooks = [{"url": "http://example.invalid/hook"}]  # Non-HTTPS transport must fail.
        tokens = [{"created_time": 1_700_000_000, "expire_time": 1_731_536_000}]  # Keep token posture secure.
        return OrganizationSecuritySourceData(settings, [], [], tokens, webhooks)

    @staticmethod
    def long_lived_token() -> OrganizationSecuritySourceData:
        """Return source data with an API token that exceeds one year."""
        settings = {"api_policy": {"access": "restricted"}}  # Keep access secure so token age is the tested defect.
        tokens = [{"created_time": 1_700_000_000, "expire_time": 1_800_000_000}]  # This lifespan exceeds 365 days.
        return OrganizationSecuritySourceData(settings, [], [], tokens, [{"url": "https://example.invalid/hook"}])
