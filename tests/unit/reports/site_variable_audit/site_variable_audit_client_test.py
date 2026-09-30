"""Client tests for the site variable audit."""

from __future__ import annotations  # Keep test annotations import-safe.

from typing import Any  # Type simple fixture doubles.

from src.reports.site_variable_audit.client import SiteVariableAuditClient  # Test client read behavior.


class _MistApiDouble:
    """Return paginated rows without network access."""

    def get_all(self, response: Any, mist_session: Any) -> list[dict[str, Any]]:
        """Return response rows and prove the active session is used."""
        assert mist_session == "session"  # Prove pagination receives the active session.
        return list(response)  # Return a copy to keep fixture state isolated.


def test_client_reads_each_required_endpoint_once() -> None:
    """Prove each unique template source and variable source is read once."""
    calls: list[str] = []  # Capture operation names in call order.

    def operation_factory(name: str) -> Any:
        def operation(session: Any, org_id: str, **query: Any) -> list[dict[str, Any]]:
            assert session == "session"  # Prove the active session reaches each operation.
            assert org_id == "org-1"  # Prove the selected organization reaches each operation.
            calls.append(name)  # Record the operation call for one-read assertions.
            return [{"id": name, "query": query}]  # Return one row for pagination.

        return operation  # Return this operation double.

    operations = {name: operation_factory(name) for name in SiteVariableAuditClient.OPERATION_KEYS}  # Build doubles.
    client = SiteVariableAuditClient(
        "session", "org-1", operations=operations, mistapi_module=_MistApiDouble()
    )  # Use only offline doubles.
    client.fetch()  # Fetch all required records once.
    assert calls == list(SiteVariableAuditClient.OPERATION_KEYS)  # Prove each endpoint is read one time.


def test_client_does_not_use_per_site_settings_lookup() -> None:
    """Prove the client exposes no per-site settings operation."""
    assert "getSiteSetting" not in SiteVariableAuditClient.OPERATION_KEYS  # Prove no per-site settings operation.
