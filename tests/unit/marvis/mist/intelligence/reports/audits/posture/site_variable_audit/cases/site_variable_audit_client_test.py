"""Client tests for the site variable audit."""

from __future__ import annotations  # Keep test annotations import-safe.

from typing import Any  # Type simple fixture doubles.

import pytest  # Assert client error behavior without network access.

from src.mist.intelligence.reports.site_variable_audit.client import (  # Test client read behavior.
    SiteVariableAuditClient,
    SiteVariableAuditReadError,
)


class _MistApiDouble:
    """Return paginated rows without network access."""

    def get_all(self, response: Any, mist_session: Any) -> list[dict[str, Any]]:
        """Return response rows and prove the active session is used."""
        assert mist_session == "session"  # Prove pagination receives the active session.
        return list(response)  # Return a copy to keep fixture state isolated.


class _StatusResponse:
    """Carry one mocked HTTP status for failure-mode tests."""

    def __init__(self, status_code: int) -> None:
        """Store the mocked HTTP status code."""
        self.status_code = status_code  # Preserve the HTTP status for the SDK double.


class _HttpStatusMistApiDouble:
    """Raise errors for mocked HTTP 4xx and 5xx responses."""

    def get_all(self, response: _StatusResponse, mist_session: Any) -> list[dict[str, Any]]:
        """Raise when the mocked response carries an error status."""
        assert mist_session == "session"  # Prove pagination receives the active session.
        if response.status_code >= 400:  # Treat any mocked error status as an SDK failure.
            raise RuntimeError(f"HTTP {response.status_code}")  # Match a failed SDK pagination path.
        return [{"status_code": response.status_code}]  # Return rows only for success responses.


def _client_for_status(status_code: int) -> SiteVariableAuditClient:
    """Return a client whose first operation returns one mocked status."""

    def operation(session: Any, org_id: str, **query: Any) -> _StatusResponse:
        """Return one mocked HTTP response object."""
        assert session == "session"  # Prove the active session reaches the operation.
        assert org_id == "org-1"  # Prove the selected organization reaches the operation.
        assert query == {}  # Prove the first endpoint receives no search filters.
        return _StatusResponse(status_code)  # Return the status-carrying response.

    operations = {
        "listOrgSites": operation,
        "listOrgGatewayTemplates": operation,
        "listOrgNetworkTemplates": operation,
        "listOrgTemplates": operation,
        "listOrgWlans": operation,
        "listOrgDeviceProfiles": operation,
        "searchOrgVars": operation,
    }  # Provide every required callable so construction stays realistic.
    return SiteVariableAuditClient(
        "session", "org-1", operations=operations, mistapi_module=_HttpStatusMistApiDouble()
    )  # Build the client with offline doubles.


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


def test_client_raises_read_error_for_http_4xx_response() -> None:
    """Prove a mocked HTTP 4xx response stops the client."""
    client = _client_for_status(404)  # Build a client that receives a not-found response.
    with pytest.raises(SiteVariableAuditReadError, match="listOrgSites") as error_info:  # Prove clear error type.
        client.fetch()  # Run the client against the mocked HTTP 4xx response.
    assert isinstance(error_info.value.__cause__, RuntimeError)  # Prove the original SDK failure is preserved.


def test_client_raises_read_error_for_http_5xx_response() -> None:
    """Prove a mocked HTTP 5xx response stops the client."""
    client = _client_for_status(503)  # Build a client that receives a service-unavailable response.
    with pytest.raises(SiteVariableAuditReadError, match="listOrgSites") as error_info:  # Prove clear error type.
        client.fetch()  # Run the client against the mocked HTTP 5xx response.
    assert str(error_info.value.__cause__) == "HTTP 503"  # Prove the 5xx status remains visible for triage.
