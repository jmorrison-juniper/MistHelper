"""Representative source data for organization security posture tests."""

from src.mist.intelligence.reports.org_security_posture.models import OrganizationSecuritySourceData


class RepresentativeOrgSecurityPostureFixture:
    """Build fixture data that exercises pass, fail, and review verdicts."""

    @staticmethod
    def source_data() -> OrganizationSecuritySourceData:
        """Return representative source data for contract tests."""
        settings = {  # Mix secure and insecure values so summary counts exercise every verdict.
            "password_policy": {
                "enabled": True,
                "min_length": 10,
                "requires_uppercase": True,
                "requires_lowercase": True,
                "requires_number": True,
                "requires_special_char": True,
                "requires_two_factor_auth": True,
                "reuse_history": 5,
                "expiry_in_days": 120,
            },
            "ui_idle_timeout": 30,
            "session_policy": {"max_lifetime_hours": 16},
            "api_policy": {"access": "restricted"},
            "disable_remote_shell": True,
            "disable_pcap": False,
            "junos_shell_access": {"admin": "none", "helpdesk": "none", "read": "none", "write": "none"},
            "pcap_bucket_verified": True,
            "switch_mgmt": {"remove_existing_configs": True},
        }
        tokens = [{"created_time": 1_700_000_000, "expire_time": 1_731_536_000}]  # Keep token lifetime within 365 days.
        webhooks = [{"url": "https://example.invalid/hook"}]  # Keep webhook transport secure for base fixture.
        return OrganizationSecuritySourceData(settings, [{"enabled": True}], [{"role": "admin"}], tokens, webhooks)
