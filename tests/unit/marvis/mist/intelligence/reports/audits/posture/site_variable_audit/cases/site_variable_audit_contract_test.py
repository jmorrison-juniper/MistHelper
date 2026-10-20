"""Contract tests for the site variable audit Mist reads."""

from __future__ import annotations  # Keep test annotations import-safe.

from typing import Any  # Type simple response doubles for offline tests.

from src.mist.intelligence.reports.site_variable_audit.client import (
    SiteVariableAuditClient,
)  # Test the client contract.


class _MistApiDouble:
    """Provide a paginated helper without network access."""

    def get_all(self, response: Any, mist_session: Any) -> list[dict[str, Any]]:
        """Return response rows exactly as the fixture supplied them."""
        assert mist_session == "session"  # Prove the client passes the active session to pagination.
        return list(response)  # Return a copy so caller mutations cannot affect fixture state.


def test_client_uses_required_openapi_operation_ids() -> None:
    """Prove the client names the required OpenAPI operation IDs."""
    assert SiteVariableAuditClient.OPERATION_KEYS == (  # Check the stable operation contract.
        "listOrgSites",
        "listOrgGatewayTemplates",
        "listOrgNetworkTemplates",
        "listOrgTemplates",
        "listOrgWlans",
        "listOrgDeviceProfiles",
        "searchOrgVars",
    )


def test_client_passes_required_search_and_pagination_parameters() -> None:
    """Prove the client uses organization search and SDK pagination."""
    calls: list[tuple[str, dict[str, Any]]] = []  # Record every offline operation call.

    def operation_factory(name: str) -> Any:
        def operation(session: Any, org_id: str, **query: Any) -> list[dict[str, Any]]:
            assert session == "session"  # Prove the client passes the active session.
            assert org_id == "org-1"  # Prove the client passes the selected organization.
            calls.append((name, dict(query)))  # Capture query parameters for contract checks.
            return [{"id": name}]  # Return one row so pagination is exercised.

        return operation  # Return the operation double for this OpenAPI ID.

    operations = {name: operation_factory(name) for name in SiteVariableAuditClient.OPERATION_KEYS}  # Build doubles.
    client = SiteVariableAuditClient(
        "session", "org-1", operations=operations, mistapi_module=_MistApiDouble()
    )  # Use offline SDK double.
    records = client.fetch()  # Fetch all datasets without a network.
    assert calls[-1] == ("searchOrgVars", {"var": "*"})  # Prove all site variables are searched at once.
    assert ("listOrgDeviceProfiles", {"type": "gateway"}) in calls  # Prove gateway profiles are bounded.
    assert len(records) == 7  # Prove each required dataset is returned.
