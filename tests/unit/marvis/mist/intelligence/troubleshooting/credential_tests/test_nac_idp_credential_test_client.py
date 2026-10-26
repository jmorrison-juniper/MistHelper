"""Tests for the NAC identity provider credential test client."""

from __future__ import annotations  # WHY: keep annotation behavior the same as source modules.

import logging  # WHY: failure-mode tests verify safe client warnings.
from dataclasses import dataclass  # WHY: fake responses need a tiny response object.
from typing import Any  # WHY: fake SDK functions accept dynamic session objects.

from src.mist.intelligence.troubleshooting.nac_idp_credential_test import (
    client as client_module,
)  # WHY: monkeypatch SDK seams.
from src.mist.intelligence.troubleshooting.nac_idp_credential_test.client import (
    NacIdpCredentialClient,
)  # WHY: class under test.
from src.mist.intelligence.troubleshooting.nac_idp_credential_test.model import (  # Import the moved dependency.
    CredentialTestRequest,
    IdentityProviderChoice,
)


@dataclass(slots=True)
class FakeResponse:
    """Represent the response fields used by the client."""

    status_code: int  # WHY: client branches on the HTTP status.
    data: Any  # WHY: client reads the parsed response payload.


def test_nac_idp_credential_test_client_reads_mist_nac_idps(monkeypatch: Any) -> None:
    """Read NAC identity providers from organization settings."""

    def fake_get_settings(session: Any, org_id: str) -> FakeResponse:
        """Return one NAC identity provider row."""
        assert session == "session"  # WHY: verify the active session is passed through.
        assert org_id == "org-1"  # WHY: verify the organization scope is correct.
        return FakeResponse(  # WHY: settings payload mirrors the OpenAPI schema path.
            200,
            {"mist_nac": {"idps": [{"id": "idp-1", "name": "Corp LDAP", "type": "ldap"}]}},
        )

    monkeypatch.setattr(client_module.setting, "getOrgSettings", fake_get_settings)  # WHY: block live API calls.
    test_client = NacIdpCredentialClient("session", "org-1")  # WHY: bind fake session and org.

    providers = test_client.list_identity_providers()  # WHY: exercise the primary provider source.

    assert [provider.idp_id for provider in providers] == ["idp-1"]  # WHY: provider id feeds `idp_id`.
    assert providers[0].source == "mist_nac.idps"  # WHY: source evidence must be preserved.


def test_nac_idp_credential_test_client_falls_back_to_sso(monkeypatch: Any) -> None:
    """Use organization SSO rows only when NAC settings are empty."""

    def fake_get_settings(session: Any, org_id: str) -> FakeResponse:
        """Return empty NAC settings."""
        return FakeResponse(200, {"mist_nac": {"idps": []}})  # WHY: force the fallback branch.

    def fake_list_ssos(session: Any, org_id: str, limit: int | None = None) -> FakeResponse:
        """Return one SSO row from the fallback endpoint."""
        assert limit == client_module.SSO_PAGE_LIMIT  # WHY: client should request a full page.
        return FakeResponse(200, [{"id": "sso-1", "name": "Portal SSO", "domain": "example.net"}])

    monkeypatch.setattr(client_module.setting, "getOrgSettings", fake_get_settings)  # WHY: block live settings read.
    monkeypatch.setattr(client_module.ssos, "listOrgSsos", fake_list_ssos)  # WHY: block live SSO read.
    monkeypatch.setattr(client_module.mistapi, "get_all", lambda response, mist_session: response.data)  # WHY.
    test_client = NacIdpCredentialClient("session", "org-1")  # WHY: bind fake session and org.

    providers = test_client.list_identity_providers()  # WHY: exercise the fallback provider source.

    assert providers[0].idp_id == "sso-1"  # WHY: fallback rows still need a selectable identifier.
    assert providers[0].source == "listOrgSsos"  # WHY: operator can see that this is not NAC settings.


def test_nac_idp_credential_test_client_sends_request_body(monkeypatch: Any) -> None:
    """Send the exact request body to `validateOrgIdpCredential`."""
    captured: dict[str, Any] = {}  # WHY: capture the SDK call without network access.

    def fake_validate(session: Any, org_id: str, body: dict[str, str]) -> FakeResponse:
        """Capture one credential validation request."""
        captured["session"] = session  # WHY: verify the active session is used.
        captured["org_id"] = org_id  # WHY: verify the organization path parameter.
        captured["body"] = body  # WHY: acceptance criteria assert the body shape.
        return FakeResponse(200, {"status": "success", "groups": ["staff"]})  # WHY: return a success result.

    monkeypatch.setattr(client_module.mist_nac, "validateOrgIdpCredential", fake_validate)  # WHY: no live API call.
    test_client = NacIdpCredentialClient("session", "org-1")  # WHY: bind fake session and org.
    provider = IdentityProviderChoice("idp-1", "Corp LDAP", "ldap")  # WHY: result needs provider context.
    request = CredentialTestRequest("idp-1", "user@example.net", "hidden-value")  # WHY: representative request.

    result = test_client.validate_credential(request, provider)  # WHY: exercise the validation method.

    assert captured["body"] == {  # WHY: OpenAPI-derived request shape plus selected `idp_id`.
        "idp_id": "idp-1",
        "username": "user@example.net",
        "password": "hidden-value",
    }
    assert result.status == "success"  # WHY: client must normalize the response.


def test_nac_idp_credential_test_client_handles_http_4xx(monkeypatch: Any, caplog: Any) -> None:
    """Return a safe failure result when the API rejects the request."""

    def fake_validate(session: Any, org_id: str, body: dict[str, str]) -> FakeResponse:
        """Return one client-side API failure response."""
        return FakeResponse(status_code=400, data={"error": "Bad Request"})  # WHY: cover the HTTP 4xx response.

    monkeypatch.setattr(client_module.mist_nac, "validateOrgIdpCredential", fake_validate)  # WHY: no network.
    caplog.set_level(logging.WARNING)  # WHY: test quality gate requires a checked failure behavior.
    test_client = NacIdpCredentialClient("session", "org-1")  # WHY: bind fake session and org.
    provider = IdentityProviderChoice("idp-1", "Corp LDAP", "ldap")  # WHY: result needs provider context.
    request = CredentialTestRequest("idp-1", "user@example.net", "hidden-value")  # WHY: representative request.

    result = test_client.validate_credential(request, provider)  # WHY: exercise the HTTP 4xx path.

    assert result.status == "failure"  # WHY: HTTP 4xx is a failed credential validation call.
    assert result.reason == "Bad Request"  # WHY: operator needs the API reason.
    assert "HTTP 400" in caplog.text  # WHY: client logs the transport failure without the password.
    assert "hidden-value" not in caplog.text  # WHY: logs must not expose the password.


def test_nac_idp_credential_test_client_handles_http_5xx(monkeypatch: Any, caplog: Any) -> None:
    """Return a safe failure result when the API service fails."""

    def fake_validate(session: Any, org_id: str, body: dict[str, str]) -> FakeResponse:
        """Return one service-side API failure response."""
        return FakeResponse(status_code=503, data={"message": "Service Unavailable"})  # WHY: cover HTTP 5xx behavior.

    monkeypatch.setattr(client_module.mist_nac, "validateOrgIdpCredential", fake_validate)  # WHY: no network.
    caplog.set_level(logging.WARNING)  # WHY: test quality gate requires a checked failure behavior.
    test_client = NacIdpCredentialClient("session", "org-1")  # WHY: bind fake session and org.
    provider = IdentityProviderChoice("idp-1", "Corp LDAP", "ldap")  # WHY: result needs provider context.
    request = CredentialTestRequest("idp-1", "user@example.net", "hidden-value")  # WHY: representative request.

    result = test_client.validate_credential(request, provider)  # WHY: exercise the HTTP 5xx path.

    assert result.status == "failure"  # WHY: HTTP 5xx is a failed credential validation call.
    assert result.reason == "Service Unavailable"  # WHY: operator needs the API reason.
    assert "HTTP 503" in caplog.text  # WHY: client logs the transport failure without the password.
    assert "hidden-value" not in caplog.text  # WHY: logs must not expose the password.
