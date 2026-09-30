"""Smoke tests for package imports."""

from src.reports.org_security_posture import OrganizationSecuritySourceData, OrgSecurityPostureChecklist


def test_package_exports_runner_and_model() -> None:
    assert callable(OrgSecurityPostureChecklist.run)  # Deferred integration needs the static handler export.
    assert OrganizationSecuritySourceData.__annotations__ == {  # Integration needs the source data contract.
        "org_settings": "dict[str, Any]",
        "org_ssos": "list[dict[str, Any]]",
        "org_admins": "list[dict[str, Any]]",
        "org_api_tokens": "list[dict[str, Any]]",
        "org_webhooks": "list[dict[str, Any]]",
    }
