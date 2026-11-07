"""Verify shared request accounting before Mist transport."""

from types import SimpleNamespace

import pytest
from requests import Request
from requests.adapters import HTTPAdapter

from src.foundation.support.refactors.initialize_mist_session import MistSessionConfigurator
from src.interfaces.wan_performance.collection.request_admission import AdmittedAdapter, RequestLedger


class FakeRedis:
    """Capture atomic reservation arguments."""

    def __init__(self, result: int = 1) -> None:
        """Set the deterministic reservation result."""
        self.result = result  # Keep the test result explicit.
        self.arguments: tuple[object, ...] = ()  # Capture the quota keys.

    def eval(self, *arguments: object) -> int:
        """Return the configured reservation result."""
        self.arguments = arguments  # Record the script and key arguments.
        return self.result  # Return success or quota refusal.


class TestRequestAdmission:
    """Verify credentials, tenant keys, and adapter behavior."""

    def test_ledger_hashes_auth_and_counts_org(self) -> None:
        """Store only a credential hash and include the organization bucket."""
        request = Request(
            "GET", "https://mist.example/api/v1/orgs/org-one/devices", headers={"Authorization": "Bearer secret-value"}
        ).prepare()  # Prepare one authenticated request.
        client = FakeRedis()  # Allow the reservation.
        RequestLedger(client).admit(request)  # Reserve one request.
        keys = client.arguments[2:4]  # Read the credential and organization keys.
        assert len(keys) == 2  # Count both shared limits.
        assert "org-one" in str(keys[1])  # Preserve tenant-level accounting.
        assert "secret-value" not in repr(client.arguments)  # Never store the raw token.

    def test_quota_refusal_stops_before_transport(self) -> None:
        """Refuse an exhausted quota before any HTTP request can run."""
        request = Request(
            "GET", "https://mist.example/api/v1/orgs/org-one/devices", headers={"Authorization": "Bearer token"}
        ).prepare()  # Prepare one request.
        ledger = RequestLedger(FakeRedis(result=0))  # Refuse the reservation.
        with pytest.raises(ConnectionError, match="quota"):  # Require explicit failure.
            ledger.admit(request)  # Stop before adapter transport.

    def test_missing_authentication_is_rejected(self) -> None:
        """Do not place anonymous callers in a shared request bucket."""
        request = Request(
            "GET", "https://mist.example/api/v1/orgs/org-one/devices"
        ).prepare()  # Prepare an anonymous request.
        with pytest.raises(ConnectionError, match="authentication"):  # Require fail-closed behavior.
            RequestLedger(FakeRedis()).admit(request)  # Refuse before accounting.

    def test_site_request_without_context_uses_credential_quota(self) -> None:
        """Admit generic site requests while keeping credential accounting active."""
        request = Request(
            "GET", "https://mist.example/api/v1/sites/site-one/devices", headers={"Cookie": "session"}
        ).prepare()  # Prepare a site request.
        client = FakeRedis()  # Allow the credential-level reservation.
        RequestLedger(client).admit(request)  # Reserve one request without an unknown tenant key.
        assert client.arguments[1] == 1  # Count only the credential bucket.
        assert str(client.arguments[2]).startswith("misthelper:api:v1:requests:")  # Keep credential admission active.

    def test_site_request_uses_configured_organization_quota(self) -> None:
        """Apply organization accounting when session context supplies the tenant."""
        request = Request(
            "GET", "https://mist.example/api/v1/sites/site-one/devices", headers={"Cookie": "session"}
        ).prepare()  # Prepare a site request.
        client = FakeRedis()  # Allow the two scoped reservations.
        RequestLedger(client, org_id="org-one").admit(request)  # Use the selected organization context.
        keys = client.arguments[2:4]  # Read the credential and organization buckets.
        assert client.arguments[1] == 2  # Count both limits.
        assert "org-one" in str(keys[1])  # Preserve tenant-level accounting.

    def test_adapter_counts_429_and_initializer_selects_shared_adapter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stop after HTTP 429 and wire shared admission into session setup."""
        request = Request(
            "GET", "https://mist.example/api/v1/orgs/org-one/devices", headers={"Authorization": "Bearer token"}
        ).prepare()  # Prepare one request.
        closed: list[bool] = []  # Record response cleanup.
        monkeypatch.setattr(
            HTTPAdapter,
            "send",
            lambda *args, **kwargs: SimpleNamespace(status_code=429, close=lambda: closed.append(True)),
        )  # Mock one 429 response.
        with pytest.raises(ConnectionError, match="429"):  # Require no hidden retry.
            AdmittedAdapter(RequestLedger(FakeRedis()), 5).send(request)  # Count then stop the response.
        assert closed == [True]  # Release the rate-limit response.
        monkeypatch.setattr(RequestLedger, "enabled", staticmethod(lambda: True))  # Enable shared accounting.
        ledger = RequestLedger(FakeRedis())  # Use an isolated ledger.
        monkeypatch.setattr(
            RequestLedger, "connect", classmethod(lambda cls, org_id=None: ledger)
        )  # Inject the ledger.
        adapter = MistSessionConfigurator._build_timeout_adapter(5)  # Use the session configuration seam.
        assert isinstance(adapter, AdmittedAdapter)  # Verify the shared transport adapter.

    def test_shared_initializer_admits_site_request_without_org_context(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Keep globally mounted shared admission usable for site-scoped SDK calls."""
        request = Request(
            "GET", "https://mist.example/api/v1/sites/site-one/insights", headers={"Authorization": "******"}
        ).prepare()  # Prepare a site-scoped request through the global adapter.
        redis_client = FakeRedis()  # Simulate the shared Redis reservation script.
        ledger = RequestLedger(redis_client)  # Match the initializer's absent organization context.
        connect_arguments: list[str | None] = []  # Record the context passed by global session setup.

        def connect(cls: type[RequestLedger], org_id: str | None = None) -> RequestLedger:
            """Return the fake shared ledger and record its selected context."""
            connect_arguments.append(org_id)  # Preserve the initializer call arguments.
            return ledger  # Use the isolated Redis-backed test double.

        monkeypatch.setattr(RequestLedger, "enabled", staticmethod(lambda: True))  # Enable configured Redis mode.
        monkeypatch.setattr(RequestLedger, "connect", classmethod(connect))  # Inject the shared test ledger.
        monkeypatch.setattr(
            HTTPAdapter, "send", lambda *args, **kwargs: SimpleNamespace(status_code=200)
        )  # Complete one request after admission.
        adapter = MistSessionConfigurator._build_timeout_adapter(5)  # Build the production adapter.
        response = adapter.send(request)  # Exercise admission and the wrapped transport path.
        assert response.status_code == 200  # Confirm the site request reaches transport.
        assert connect_arguments == [None]  # Confirm global setup has no organization context.
        assert redis_client.arguments[1] == 1  # Enforce the credential quota.
        assert str(redis_client.arguments[2]).startswith("misthelper:api:v1:requests:")  # Avoid tenant guessing.
