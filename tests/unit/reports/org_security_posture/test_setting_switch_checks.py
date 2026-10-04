"""Tests for switch-style organization setting checks."""

from src.mist.intelligence.reports.org_security_posture.checks.access import (
    JunosShellRoleAccessDisabledCheck,
    PacketCaptureDisabledCheck,
    RemoteShellDisabledCheck,
    StaleCleanupEnabledCheck,
)
from src.mist.intelligence.reports.org_security_posture.models import OrganizationSecuritySourceData
from tests.unit.reports.org_security_posture.fixtures.representative_org_security_posture import (
    RepresentativeOrgSecurityPostureFixture,
)


def test_remote_shell_disabled_passes() -> None:
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use representative switch settings.
    result = RemoteShellDisabledCheck().run(source_data)  # Evaluate remote shell posture.
    assert result.verdict == "pass"  # Disabled remote shell meets the recommendation.


def test_packet_capture_enabled_fails() -> None:
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use a fixture with packet capture enabled.
    result = PacketCaptureDisabledCheck().run(source_data)  # Evaluate packet capture posture.
    assert result.verdict == "fail"  # Enabled packet capture violates the recommendation.


def test_stale_cleanup_enabled_passes() -> None:
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use representative cleanup settings.
    result = StaleCleanupEnabledCheck().run(source_data)  # Evaluate stale cleanup posture.
    assert result.verdict == "pass"  # Enabled cleanup meets the recommendation.


def test_junos_shell_access_empty_role_reviews() -> None:
    source_data = OrganizationSecuritySourceData(  # Build only the setting needed by this check.
        {"junos_shell_access": {"admin": "none", "helpdesk": ""}},
        [],
        [],
        [],
        [],
    )
    result = JunosShellRoleAccessDisabledCheck().run(source_data)  # Evaluate ambiguous role evidence.
    assert result.verdict == "review"  # Empty shell role values need manual review.
