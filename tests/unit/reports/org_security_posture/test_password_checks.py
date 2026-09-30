"""Tests for password policy checks."""

from src.reports.org_security_posture.checks.password import PasswordMinimumLengthCheck, PasswordPolicyEnabledCheck
from tests.unit.reports.org_security_posture.fixtures.representative_org_security_posture import (
    RepresentativeOrgSecurityPostureFixture,
)


def test_password_policy_enabled_passes_when_enabled() -> None:
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use representative settings.
    result = PasswordPolicyEnabledCheck().run(source_data)  # Evaluate the enabled check.
    assert result.verdict == "pass"  # Enabled policy meets the recommendation.


def test_password_minimum_length_fails_when_too_short() -> None:
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use a fixture with length ten.
    result = PasswordMinimumLengthCheck().run(source_data)  # Evaluate minimum length.
    assert result.verdict == "fail"  # Ten characters is below the recommendation.
