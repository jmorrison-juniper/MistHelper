"""Smoke tests for package imports."""

from src.reports.org_security_posture import OrganizationSecuritySourceData, OrgSecurityPostureChecklist


def test_package_exports_runner_and_model() -> None:
    assert OrgSecurityPostureChecklist is not None  # Deferred integration needs the static handler export.
    assert OrganizationSecuritySourceData is not None  # Tests and integration need the source data model export.
