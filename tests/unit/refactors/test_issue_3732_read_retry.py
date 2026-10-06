"""Prove that issue #3732 retries safe reads without repeating writes."""

from __future__ import annotations  # Keep modern annotations compatible with runtime imports.

import socket  # Close a local connection to simulate a stale pooled socket.
from collections import Counter  # Count each local transport attempt by method and path.
from collections.abc import Iterator  # Type the local server fixture yield.
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # Serve deterministic local failures.
from threading import Thread  # Run the local server without blocking the test process.
from types import SimpleNamespace  # Build the minimum upgrade-session validation object.
from typing import Any  # Type the standard library handler override.

import pytest  # Provide fixtures, parameters, and exception assertions.
import requests  # Exercise the configured Requests adapter through urllib3.
from mistapi.__api_request import APIRequest  # Initialize the real upgrade transport without credentials.
from urllib3.connection import HTTPConnection  # Build a local connection error with no network request.
from urllib3.exceptions import NewConnectionError  # Model an eligible connection establishment failure.

from src.foundation.support.refactors.initialize_mist_session import (
    MistSessionConfigurator,  # Build the production adapter under test.
)
from src.operations.execution.firmware.org_upgrade_service import (
    OrgUpgradeService,  # Prove the read adapter cannot cross the write boundary.
    OrgUpgradeSession,  # Prove the upgrade session keeps its zero-retry contract.
)


class LocalRetryHandler(BaseHTTPRequestHandler):
    """Return local success, reset, and error outcomes without a Mist call."""

    attempts: Counter[tuple[str, str]] = Counter()  # Share attempt counts with the test assertions.

    def log_message(self, _format: str, *args: Any) -> None:
        """Suppress local HTTP server output because assertions own the evidence."""

    def _handle(self, include_body: bool = True) -> None:
        """Apply the requested deterministic outcome for one local attempt."""
        key = (self.command, self.path)  # Separate method and path counts for exact retry evidence.
        self.attempts[key] += 1  # Record the attempt before the local connection can close.
        attempt = self.attempts[key]  # Read the new count for reset-once classification.
        if self.path == "/reset-once" and attempt == 1:  # Fail only the first safe read attempt.
            self.connection.shutdown(socket.SHUT_RDWR)  # End the socket before an HTTP status exists.
            self.connection.close()  # Release the local socket so urllib3 observes the reset.
            return  # Let the configured retry policy decide whether another attempt is safe.
        if self.path == "/always-reset":  # Exhaust the stale-read retry budget deterministically.
            self.connection.shutdown(socket.SHUT_RDWR)  # End each local attempt before a response exists.
            self.connection.close()  # Release the local socket after the simulated stale read.
            return  # Let the caller observe the bounded transport failure.
        status = 500 if self.path == "/status-error" else 200  # Keep HTTP failures separate from transport failures.
        body = b"ok" if include_body else b""  # A HEAD response carries no body by HTTP contract.
        self.send_response(status)  # Return one final local HTTP result for the current attempt.
        self.send_header("Content-Length", str(len(body)))  # Let Requests finish without waiting for EOF.
        self.end_headers()  # Finish the local response headers before the optional body.
        if body:  # A GET success returns content while HEAD returns headers only.
            self.wfile.write(body)  # Complete the local successful response.

    def do_GET(self) -> None:
        """Handle a local GET attempt."""
        self._handle()  # Use the shared deterministic transport behavior.

    def do_HEAD(self) -> None:
        """Handle a local HEAD attempt."""
        self._handle(include_body=False)  # Return headers only after the optional first reset.

    def do_POST(self) -> None:
        """Handle a local POST attempt."""
        self._handle()  # Reset the local write without sending it to an external service.


@pytest.fixture
def local_retry_server() -> Iterator[tuple[ThreadingHTTPServer, str]]:
    """Serve deterministic transport outcomes on the local loopback address."""
    LocalRetryHandler.attempts = Counter()  # Isolate the attempt count for this test.
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalRetryHandler)  # Bind an ephemeral local-only port.
    thread = Thread(target=server.serve_forever, daemon=True)  # Keep the server independent of the request thread.
    thread.start()  # Accept local Requests traffic for the test.
    host, port = server.server_address  # Read the bound loopback endpoint after allocation.
    yield server, f"http://{host}:{port}"  # Give the test a local endpoint with zero Mist reachability.
    server.shutdown()  # Stop accepting local requests after the assertion.
    thread.join(timeout=5)  # Wait for the bounded server thread to stop.
    server.server_close()  # Release the ephemeral local port.


def _configured_session() -> requests.Session:
    """Return a Requests session with the production safe-read adapter."""
    session = requests.Session()  # Build a local session with no Mist authentication or endpoint.
    session.trust_env = False  # Ignore proxy settings so every request stays on the local test transport.
    adapter = MistSessionConfigurator._build_timeout_adapter(1)  # Build the exact production retry policy.
    session.mount("http://", adapter)  # Exercise the policy through the local HTTP server.
    session.mount("https://", adapter)  # Match the production session mount contract.
    return session  # Give each test an isolated connection pool and retry state.


class TestSafeReadRetryPolicy:
    """Prove the exact retry counters and safe method boundary."""

    def test_policy_uses_the_required_bounds(self) -> None:
        """The adapter permits only the bounded GET and HEAD transport retries."""
        retry = _configured_session().adapters["https://"].max_retries  # Read the mounted production policy.
        assert retry.total == 2  # Two retries permit no more than three total attempts.
        assert retry.connect == 2  # A safe connection failure can receive two retries.
        assert retry.read == 1  # A stale pooled read can receive one retry.
        assert retry.redirect == 0  # Redirect transport retries remain disabled.
        assert retry.status == 0  # HTTP response status retries remain disabled.
        assert retry.other == 0  # Unclassified transport retries remain disabled.
        assert retry.allowed_methods == frozenset({"GET", "HEAD"})  # Only idempotent reads are repeatable.
        assert retry.status_forcelist == set()  # No HTTP status can trigger the transport retry path.
        assert retry.respect_retry_after_header is False  # A response header cannot enable another attempt.

    def test_session_configuration_preserves_authentication(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The shared session keeps its authentication when the read adapter is mounted."""
        inner_session = requests.Session()  # Build the local Requests transport used by mistapi.
        inner_session.headers["Authorization"] = "Token local-test"  # Use a non-secret test identity.
        wrapper = SimpleNamespace(_session=inner_session)  # Match the mistapi private transport seam.
        monkeypatch.setattr("MistHelper.API_REQUEST_TIMEOUT", 1)  # Supply the local timeout configuration.
        MistSessionConfigurator._configure_timeout(wrapper)  # Mount the production adapter without a cloud call.
        assert inner_session.headers["Authorization"] == "Token local-test"  # Preserve the authentication state.
        assert inner_session.adapters["https://"].max_retries.total == 2  # Install the bounded safe-read policy.
        inner_session.close()  # Release the local connection pools after the assertion.

    @pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def test_connection_failures_for_writes_raise_the_original_error(self, method: str) -> None:
        """Every non-read method stops before urllib3 can consume a connection retry."""
        retry = _configured_session().adapters["https://"].max_retries  # Read the production retry instance.
        connection = HTTPConnection("127.0.0.1")  # Build a local connection object with no request.
        error = NewConnectionError(connection, "local write failure")  # Create a fake local transport failure.
        with pytest.raises(NewConnectionError) as caught:  # The exact error must escape on the first attempt.
            retry.increment(method=method, url="/write", error=error)  # Exercise the method guard directly.
        assert caught.value is error  # The guard must re-raise the original transport failure object.


class TestLocalReadAttempts:
    """Prove safe read recovery and its strict attempt limits."""

    @pytest.mark.parametrize("method", ["GET", "HEAD"])
    def test_reset_then_success_uses_exactly_two_attempts(
        self, local_retry_server: tuple[ThreadingHTTPServer, str], method: str
    ) -> None:
        """A stale local read retries once and returns the second response."""
        _server, base_url = local_retry_server  # Read the isolated local endpoint.
        response = _configured_session().request(method, f"{base_url}/reset-once")  # Trigger one stale reset.
        assert response.status_code == 200  # The second local attempt returns the successful response.
        assert LocalRetryHandler.attempts[(method, "/reset-once")] == 2  # The read uses exactly two attempts.

    def test_exhausted_stale_read_stops_after_two_attempts(
        self, local_retry_server: tuple[ThreadingHTTPServer, str]
    ) -> None:
        """A repeated stale reset stops when the one-read-retry budget ends."""
        _server, base_url = local_retry_server  # Read the isolated local endpoint.
        with pytest.raises(requests.ConnectionError):  # The caller must receive the exhausted failure.
            _configured_session().get(f"{base_url}/always-reset")  # Trigger a reset on every local attempt.
        assert LocalRetryHandler.attempts[("GET", "/always-reset")] == 2  # The policy makes no third stale read.

    def test_connection_failure_stops_after_three_total_attempts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An eligible local connection failure cannot exceed the total bound."""
        attempts = 0  # Count fake local connection establishment attempts.

        def fail_connect(connection: HTTPConnection) -> None:
            nonlocal attempts  # Update the enclosing attempt counter for exact evidence.
            attempts += 1  # Count the attempt before the fake local connection fails.
            raise NewConnectionError(connection, "local connection refusal")  # Avoid any external network call.

        monkeypatch.setattr(HTTPConnection, "connect", fail_connect)  # Replace socket access with a local fake.
        with pytest.raises(requests.ConnectionError):  # Requests must surface the bounded failure.
            _configured_session().get("http://127.0.0.1:9/connect")  # Use a loopback URL with the patched connect.
        assert attempts == 3  # The initial safe read and two connection retries exhaust the total.

    def test_http_error_uses_one_attempt(self, local_retry_server: tuple[ThreadingHTTPServer, str]) -> None:
        """An HTTP status is an application result and receives no transport retry."""
        _server, base_url = local_retry_server  # Read the isolated local endpoint.
        response = _configured_session().get(f"{base_url}/status-error")  # Return one local HTTP 500 response.
        assert response.status_code == 500  # The response reaches the application unchanged.
        assert LocalRetryHandler.attempts[("GET", "/status-error")] == 1  # The status triggers no retry.


class TestWriteSessionIsolation:
    """Prove that local write failures and upgrade sessions keep one attempt."""

    def test_post_reset_uses_exactly_one_attempt(self, local_retry_server: tuple[ThreadingHTTPServer, str]) -> None:
        """A local POST reset fails without a second transport attempt."""
        _server, base_url = local_retry_server  # Read the isolated local endpoint.
        with pytest.raises(requests.ConnectionError):  # The uncertain write failure must reach the caller.
            _configured_session().post(f"{base_url}/always-reset", data=b"write")  # Send only to loopback.
        assert LocalRetryHandler.attempts[("POST", "/always-reset")] == 1  # The write receives no retry.

    def test_shared_read_adapter_fails_the_upgrade_write_validator(self) -> None:
        """The nonzero read adapter cannot become an upgrade write transport."""
        inner_session = _configured_session()  # Build the shared read transport with bounded retries.
        session = SimpleNamespace(_MAX_429_RETRIES=0, _session=inner_session)  # Keep SDK writes disabled.
        with pytest.raises(ValueError, match="transport retries disabled"):  # The write boundary rejects the adapter.
            OrgUpgradeService.check_write_session(session)  # Validate without sending a cloud request.

    def test_upgrade_session_keeps_zero_transport_retries(self) -> None:
        """The existing upgrade write session remains valid with zero retries."""
        session = object.__new__(OrgUpgradeSession)  # Avoid login and any Mist API initialization.
        APIRequest.__init__(session)  # Initialize the installed SDK request base without credentials or login.
        assert OrgUpgradeSession._MAX_429_RETRIES == 0  # The SDK write retry loop remains disabled.
        try:
            OrgUpgradeService.check_write_session(session)  # The actual write transport must pass validation.
            assert all(  # Inspect every adapter that the installed SDK mounted.
                adapter.max_retries.total in (0, False) for adapter in session._session.adapters.values()
            )  # Prove no write transport can repeat an uncertain request.
        finally:
            session._session.close()  # Release the installed SDK connection pools after the assertion.
