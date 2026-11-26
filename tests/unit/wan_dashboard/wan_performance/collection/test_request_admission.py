"""Verify shared request accounting before Mist transport."""

import logging
from types import SimpleNamespace

import pytest
import redis
from requests import Request
from requests.adapters import HTTPAdapter

from src.foundation.support.refactors.initialize_mist_session import MistSessionConfigurator
from src.foundation.support.utils.logger_utils import StructuredLoggingFrontend
from src.interfaces.wan_performance.collection.request_admission import (
    AdmittedAdapter,
    RequestLedger,
    organization_scope,
)

SECRET_HEADER = "Token secret-value"  # Credential that no traceback may print.


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

    def test_standalone_disables_shared_admission_even_if_explicit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Standalone mode always disables Redis request accounting."""
        monkeypatch.setenv("MISTHELPER_STANDALONE", "true")  # Force CSV-only mode.
        monkeypatch.setenv("WAN_SHARED_ADMISSION", "true")  # Create a conflicting explicit value.
        assert RequestLedger.enabled() is False  # Standalone precedence disables Redis.

    def test_redis_timeout_disables_admission_and_continues(self) -> None:
        """An unavailable local Redis must not block a read-only Mist request."""
        request = Request(
            "GET",
            "https://mist.example/api/v1/orgs/org-one/devices",
            headers={"Authorization": "Bearer token"},
        ).prepare()  # Prepare one authenticated read.

        class OfflineRedis:
            """Return a Redis timeout for the first admission call."""

            def __init__(self) -> None:
                """Record the first Redis attempt."""
                self.calls = 0  # Track Redis calls for the disabled ledger.

            def eval(self, *_arguments: object) -> int:
                """Raise a Redis timeout instead of reserving a request."""
                self.calls += 1  # Record the failed admission attempt.
                raise redis.exceptions.TimeoutError("offline")  # Simulate the workstation Redis outage.

        offline_redis = OfflineRedis()  # Use one deterministic offline store.
        ledger = RequestLedger(offline_redis)  # Build a ledger around the failing store.
        ledger.admit(request)  # The Redis failure must continue as a plain read.
        ledger.admit(request)  # The disabled ledger must not call Redis again.
        assert offline_redis.calls == 1  # One failure permanently disables this process ledger.

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

    def test_site_request_requires_organization_context(self) -> None:
        """Refuse site requests that cannot be assigned to a tenant."""
        request = Request(
            "GET", "https://mist.example/api/v1/sites/site-one/devices", headers={"Cookie": "session"}
        ).prepare()  # Prepare a site request.
        with pytest.raises(ConnectionError, match="organization"):  # Require tenant context.
            RequestLedger(FakeRedis()).admit(request)  # Refuse unsafe quota attribution.

    def test_site_request_uses_the_scoped_organization(self) -> None:
        """A site request inside an organization scope counts against that organization."""
        request = Request(
            "GET", "https://mist.example/api/v1/sites/site-one/devices/dev-one/vc", headers={"Cookie": "session"}
        ).prepare()  # Prepare a site-scoped VC read.
        client = FakeRedis()  # Allow the reservation.
        with organization_scope("org-two"):  # Name the organization that owns the site.
            RequestLedger(client).admit(request)  # Reserve the request under that organization.
        assert "org-two" in str(client.arguments[2:4])  # Count the site read against org-two.

    def test_organization_scope_ends_with_its_block(self) -> None:
        """A site request after the scope closes fails closed again."""
        request = Request(
            "GET", "https://mist.example/api/v1/sites/site-one/devices", headers={"Cookie": "session"}
        ).prepare()  # Prepare a site request.
        with organization_scope("org-two"):  # Open and close one organization scope.
            pass  # Leave the scope before the request runs.
        with pytest.raises(ConnectionError, match="organization"):  # The scope must not outlive its block.
            RequestLedger(FakeRedis()).admit(request)  # Refuse the unscoped site request.

    def test_credential_never_appears_in_exception_locals(self) -> None:
        """An admission failure must not expose the credential through a traceback frame."""
        request = Request(
            "GET",
            "https://mist.example/api/v1/sites/site-one/devices",
            headers={"Authorization": SECRET_HEADER},
        ).prepare()  # Prepare an authenticated site request that fails admission.
        with pytest.raises(ConnectionError) as error:  # Capture the admission failure.
            RequestLedger(FakeRedis()).admit(request)  # Fail after the credential is read.
        frame = error.value.__traceback__  # Start at the frame that caught the error.
        assert frame is not None  # pytest.raises always attaches the traceback.
        frame = frame.tb_next  # Skip the test frame, which holds the assertion literals.
        while frame is not None:  # Walk every frame in the traceback.
            assert "secret-value" not in repr(frame.tb_frame.f_locals)  # No local may hold the raw credential.
            frame = frame.tb_next  # Continue to the next frame.

    def test_console_renderer_hides_frame_locals(self) -> None:
        """A credential held in a frame local must not reach the terminal traceback."""

        def fail_with_credential() -> None:
            """Raise while a frame local holds the credential."""
            credential = SECRET_HEADER  # Hold the credential in a local name when the error is raised.
            raise ConnectionError(f"Shared request failed with {len(credential)} credential characters.")

        with pytest.raises(ConnectionError) as error:  # Capture the failure from the helper frame.
            fail_with_credential()  # Raise with the credential in a frame local.
        record = logging.LogRecord(  # Build one stdlib record like the one mistapi emits.
            name="mistapi",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="apirequest:mist_get:Exception occurred",
            args=(),
            exc_info=(type(error.value), error.value, error.value.__traceback__),
        )  # Attach the exception that the SDK logs.
        rendered = StructuredLoggingFrontend.console_formatter().format(record)  # Render with production settings.
        assert "ConnectionError" in rendered  # The operator still sees the error type.
        assert "secret-value" not in rendered  # The credential never reaches the terminal.

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
