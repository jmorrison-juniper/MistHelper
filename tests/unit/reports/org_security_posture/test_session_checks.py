"""Tests for session policy checks."""

from src.reports.org_security_posture.checks.access import SessionIdleTimeoutCheck, SessionMaximumLifetimeCheck
from tests.unit.reports.org_security_posture.fixtures.representative_org_security_posture import (
    RepresentativeOrgSecurityPostureFixture,
)


def test_session_idle_timeout_passes_at_thirty_minutes() -> None:
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use representative session settings.
    result = SessionIdleTimeoutCheck().run(source_data)  # Evaluate idle timeout.
    assert result.verdict == "pass"  # Thirty minutes meets the recommendation.


def test_session_maximum_lifetime_fails_above_twelve_hours() -> None:
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use a fixture with sixteen hours.
    result = SessionMaximumLifetimeCheck().run(source_data)  # Evaluate maximum lifetime.
    assert result.verdict == "fail"  # Sixteen hours exceeds the recommendation.
