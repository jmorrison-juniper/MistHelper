"""Tests for the issue #3671 WebSocket endpoint helpers."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import json  # Logging tests parse each structured transport record.
import logging  # Logging tests capture debug records.
import ssl  # TLS option tests compare ssl constants.

import pytest  # The policy tests assert refusal errors.
import websocket  # ConnectFailure tests use real websocket-client exceptions.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Policy refusals use this contract error.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (  # Build endpoint policies for these tests.
    ConnectFailure,
    MistStreamEndpoint,
    ShellAddressPolicy,
    TransportProfile,
)
from src.mist.realtime.websocket_streams.live.transport.stream_client import (
    StreamClient,
)  # Fake-cloud fault tests open a stream.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.api import (
    FakeApiSession,
)  # Fake sessions expose the SDK private attributes.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeMistCloud,
    HandshakeFault,
)  # Fault tests use loopback failures.


class TestMistStreamEndpoint:
    """Verify connection values from the API session."""

    def test_stream_address_for_each_cloud_region(self) -> None:
        """Build the documented stream address for each cloud host."""
        hosts = (
            "api.mist.com",
            "api.eu.mist.com",
            "api.gc1.mist.com",
            "api.ac5.mist.com",
            "api.us.mist-federal.com",
        )  # Cover global, regional, and federal hosts.
        expected = (
            "wss://api-ws.mist.com/api-ws/v1/stream",
            "wss://api-ws.eu.mist.com/api-ws/v1/stream",
            "wss://api-ws.gc1.mist.com/api-ws/v1/stream",
            "wss://api-ws.ac5.mist.com/api-ws/v1/stream",
            "wss://api-ws.us.mist-federal.com/api-ws/v1/stream",
        )  # The SDK replaces the first api. label.
        result = [MistStreamEndpoint(FakeApiSession(cloud_uri=host)).stream_url() for host in hosts]  # Build URLs.
        assert result == list(expected)  # Each cloud region must map exactly.

    def test_profile_stream_url_overrides_cloud_address(self) -> None:
        """Use the test stream address when the profile sets one."""
        session = FakeApiSession(cloud_uri="api.mist.com")  # Build a fake SDK session.
        profile = TransportProfile(stream_url="ws://127.0.0.1:1234/api-ws/v1/stream")  # Test loopback address.
        endpoint = MistStreamEndpoint(session, profile)  # Build endpoint with override.
        assert endpoint.stream_url() == "ws://127.0.0.1:1234/api-ws/v1/stream"  # The override stays exact.

    def test_token_header_uses_active_token(self) -> None:
        """Build the Authorization header from the active token index."""
        session = FakeApiSession()  # Build a fake SDK session.
        session._apitoken = ["first", "second"]  # Simulate multiple configured tokens.
        session._apitoken_index = 1  # The second token is active.
        endpoint = MistStreamEndpoint(session)  # Build endpoint from the fake session.
        assert endpoint.headers() == ["Authorization: Token second"]  # The active token must be used.

    def test_cookie_text_skips_crlf_cookie(self) -> None:
        """Return only cookies that cannot inject a header."""
        session = FakeApiSession()  # Build a fake SDK session.
        session._apitoken = []  # Force cookie sign-in behavior.
        session._session.cookies.set("safe", "one")  # Add one safe cookie.
        session._session.cookies.set("bad", "two\r\nInjected: yes")  # Add one unsafe cookie.
        endpoint = MistStreamEndpoint(session)  # Build endpoint from the fake session.
        assert endpoint.cookie() == "safe=one"  # The CRLF cookie must be skipped.

    def test_ssl_options_follow_requests_session(self) -> None:
        """Map verify and cert values into websocket-client options."""
        session = FakeApiSession()  # Build a fake SDK session.
        session._session.verify = False  # Disable verification in the fake session.
        session._session.cert = ("client.pem", "client.key")  # Add a client certificate tuple.
        endpoint = MistStreamEndpoint(session)  # Build endpoint from the fake session.
        expected = {
            "cert_reqs": ssl.CERT_NONE,
            "check_hostname": False,
            "certfile": "client.pem",
            "keyfile": "client.key",
        }  # The SDK exposes these TLS options.
        assert endpoint.sslopt() == expected  # TLS options must match the SDK shape.

    def test_host_label_removes_path_and_query(self) -> None:
        """Return only the host part of a URL."""
        endpoint = MistStreamEndpoint(FakeApiSession())  # Build endpoint from the fake session.
        result = endpoint.host_label("wss://api-ws.mist.com/secret/path?token=no")  # Parse a sensitive URL.
        assert result == "api-ws.mist.com"  # Logs must use only the host label.


class TestShellAddressPolicy:
    """Verify shell address safety rules."""

    def test_accepts_wss_in_mist_domain(self) -> None:
        """Allow a TLS address inside the Mist domain."""
        policy = ShellAddressPolicy("api.mist.com")  # Build policy for the global cloud.
        url = "wss://shell.mist.com/shell/token"  # The path must not affect the decision.
        assert policy.check(url) == url  # The URL is safe for credentials.

    def test_refuses_ws_for_mist_domain(self) -> None:
        """Refuse a non-TLS Mist shell address."""
        policy = ShellAddressPolicy("api.mist.com")  # Build policy for the global cloud.
        with pytest.raises(StreamRequestError) as caught:  # The policy must raise the contract error.
            policy.check("ws://shell.mist.com/shell/token")  # Non-TLS can expose credentials.
        assert caught.value.code == "bad_request"  # Unsafe addresses are bad requests.

    def test_refuses_other_domain(self) -> None:
        """Refuse an address outside the Mist domain."""
        policy = ShellAddressPolicy("api.mist.com")  # Build policy for the global cloud.
        with pytest.raises(StreamRequestError) as caught:  # The policy must raise the contract error.
            policy.check("wss://example.net/shell/token")  # Another domain can steal credentials.
        assert caught.value.code == "bad_request"  # Unsafe addresses are bad requests.

    def test_refuses_lookalike_domain(self) -> None:
        """Refuse a look-alike domain."""
        policy = ShellAddressPolicy("api.mist.com")  # Build policy for the global cloud.
        with pytest.raises(StreamRequestError) as caught:  # The policy must raise the contract error.
            policy.check("wss://mist.com.example.net/shell/token")  # This is not under mist.com.
        assert caught.value.code == "bad_request"  # Unsafe addresses are bad requests.

    def test_accepts_loopback_only_when_allowed(self) -> None:
        """Allow loopback WebSocket URLs for offline tests only."""
        refused = ShellAddressPolicy("api.mist.com")  # Default policy is production-safe.
        allowed = ShellAddressPolicy("api.mist.com", allow_loopback=True)  # Tests opt into loopback.
        with pytest.raises(StreamRequestError) as caught:  # Default policy should refuse loopback.
            refused.check("ws://127.0.0.1:1234/shell/default")  # Loopback is cleartext.
        assert caught.value.code == "bad_request"  # Refusal code is stable.
        assert (  # Loopback works only when tests allow it.
            allowed.check("ws://127.0.0.1:1234/shell/default") == "ws://127.0.0.1:1234/shell/default"
        )


class TestConnectFailure:
    """Verify WebSocket open failure reasons."""

    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            (
                websocket.WebSocketBadStatusException("refused", status_code=403),
                "The Mist cloud refused the WebSocket connection with HTTP status 403.",
            ),
            (
                websocket.WebSocketBadStatusException("server", status_code=503),
                "The Mist cloud refused the WebSocket connection with HTTP status 503.",
            ),
            (
                websocket.WebSocketTimeoutException("Timeout during open"),
                "The Mist cloud did not answer the WebSocket connection in time.",
            ),
            (
                TimeoutError("The socket read timed out."),
                "The Mist cloud did not answer the WebSocket connection in time.",
            ),
            (
                ssl.SSLCertVerificationError("certificate verify failed"),
                "The TLS check of the Mist cloud connection failed.",
            ),
            (
                websocket.WebSocketAddressException("The name lookup failed."),
                "The portal could not find the address of the Mist cloud.",
            ),
            (
                ConnectionError("ConnectionError reset by peer"),
                "The portal could not connect to the Mist cloud.",
            ),
            (
                ConnectionRefusedError("The port is closed."),
                "The portal could not connect to the Mist cloud.",
            ),
            (
                websocket.WebSocketProxyException("The proxy refused the tunnel."),
                "The portal could not connect to the Mist cloud.",
            ),
            (
                websocket.WebSocketConnectionClosedException("The socket closed."),
                "The portal could not connect to the Mist cloud.",
            ),
        ],
    )
    def test_reason_maps_websocket_open_failures(self, error: BaseException, expected: str) -> None:
        """Map each connection failure family to a plain reason."""
        assert ConnectFailure.reason(error) == expected  # Operators need a safe reason for failed opens.

    def test_reason_returns_none_for_other_errors(self) -> None:
        """Ignore errors that are not WebSocket connection failures."""
        assert ConnectFailure.reason(RuntimeError("other")) is None  # Program errors keep their own handling.

    def test_fake_cloud_http_5xx_fault_reaches_connect_failure_reason(self) -> None:
        """Exercise the fake-cloud HTTP refusal through the stream client."""
        with FakeMistCloud() as cloud:  # Start a loopback fake cloud.
            cloud.fail_handshake("/api-ws/v1/stream", HandshakeFault("refuse", status_code=503))  # HTTP 5xx.
            profile = TransportProfile(
                stream_url=f"{cloud.base_ws_url}/api-ws/v1/stream",
                allow_loopback=True,
                subscribe_timeout_seconds=0.5,
            )  # Keep the end-to-end open fast.
            endpoint = MistStreamEndpoint(FakeApiSession(), profile)  # Build endpoint for fake cloud.
            client = StreamClient(endpoint, ["/one"])  # Open through real websocket-client.
            try:  # Always close the client after the failed open.
                with pytest.raises(websocket.WebSocketBadStatusException) as caught:  # HTTP refusal.
                    client.open()  # The fake cloud refuses the opening handshake.
                requests = cloud.wait_for_requests(1, 1.0)  # The fake records the failed request.
                assert caught.value.status_code == 503  # The client preserves the HTTP status.
                assert requests[0].path == "/api-ws/v1/stream"  # The request reached the fake cloud.
                assert (
                    ConnectFailure.reason(caught.value)
                    == "The Mist cloud refused the WebSocket connection with HTTP status 503."
                )  # The reason is safe.
            finally:
                client.close()  # Ensure the client releases any socket state.


class TestEndpointStructuredLogging:
    """Verify endpoint records use the T072 safe JSON boundary."""

    def test_endpoint_records_are_json_and_exclude_secrets(self, caplog: pytest.LogCaptureFixture) -> None:
        """Emit bounded records without token, cookie, or certificate values."""
        caplog.set_level(
            logging.DEBUG, logger="src.mist.realtime.websocket_streams.live.transport.endpoint"
        )  # Capture all events.
        session = FakeApiSession()  # Build a session with sensitive connection values.
        session._apitoken = ["token-secret-value"]  # Add a token that must not enter logs.
        session._session.cookies.set("session", "cookie-secret-value")  # Add a cookie that must not enter logs.
        session._session.cert = ("certificate-secret.pem", "key-secret.pem")  # Add sensitive file paths.
        endpoint = MistStreamEndpoint(session)  # Emit endpoint construction records.
        endpoint.headers()  # Emit authentication records.
        endpoint.cookie()  # Emit cookie records.
        endpoint.sslopt()  # Emit TLS records.
        records = [json.loads(record.message) for record in caplog.records]  # Parse every captured record.
        serialized = json.dumps(records)  # Build one text value for secret checks.
        assert len(records) == 7  # The endpoint must emit readiness and each authentication result pair.
        assert all("event" in record for record in records)  # Every record has the required event field.
        assert "secret" not in serialized  # No sensitive connection value can cross the log boundary.
