"""Tests for the gateway: HTTPS, the host allowlist, redirects, retries, the size cap, the token, and secrecy."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import logging  # WHY: the caplog fixture captures log records by level.
from typing import Any  # WHY: loose JSON types in fakes.

import pytest  # WHY: fixtures, parametrization, and raised-error checks.
import requests  # WHY: the connection error that the retry test raises.

from src.operations.exporting.juniper_rma.api.gateway import (  # WHY: the gateway under test.
    JuniperGatewayClient,
    JuniperTransportError,
    RequestRateLimiter,
)
from tests.unit.juniper_rma.fixtures.fake_gateway import (  # WHY: fixtures.
    CASE_BASE_URL,
    TEST_SECRET,
    TEST_TOKEN,
    FakeClock,
    FakeHttpSession,
    FakeResponse,
    json_bytes,
    make_settings,
)

TOKEN_REPLY_BODY = {
    "access_token": TEST_TOKEN,
    "token_type": "Bearer",
    "expires_in": 3600,
}  # WHY: the documented reply.
TOKEN_REPLY = FakeResponse(200, json_bytes(TOKEN_REPLY_BODY))  # WHY: a successful token reply.
LIST_REPLY = FakeResponse(200, json_bytes({"querySRListResponse": {"statusCode": "200", "cases": []}}))  # WHY: ok.


def _client(
    http: FakeHttpSession, clock: FakeClock | None = None, **settings: Any
) -> tuple[JuniperGatewayClient, list[float]]:
    """Return a gateway with a fake clock and a recorded sleeper, plus the list of recorded sleeps."""
    fake_clock = clock if clock is not None else FakeClock()  # WHY: time moves only when the test moves it.
    sleeps: list[float] = []  # WHY: record every pause that the gateway asks for.

    def sleeper(seconds: float) -> None:
        """Record the pause and move the fake clock forward by the same amount."""
        sleeps.append(seconds)  # WHY: the test checks the backoff values.
        fake_clock.advance(seconds)  # WHY: a pause moves time, as a real pause would.

    client = JuniperGatewayClient(make_settings(**settings), session=http, clock=fake_clock, sleeper=sleeper)  # WHY.
    return client, sleeps  # WHY: the client and recorded sleeps.


def _post(client: JuniperGatewayClient, seen: list[str] | None = None, base: str = CASE_BASE_URL) -> Any:
    """Send one POST and record each transaction identifier that the builder received."""

    def build(transaction_id: str) -> dict[str, Any]:
        """Return a small body and remember the identifier."""
        if seen is not None:  # WHY: the caller may not need the identifiers.
            seen.append(transaction_id)  # WHY: the retry test checks that each attempt is new.
        return {"transactionId": transaction_id}  # WHY: the body only needs to exist.

    return client.post("querysrlist", base, "querysrlist", build)  # WHY: one checked call.


def test_successful_call_uses_the_bearer_token_and_refuses_redirects() -> None:
    """The API call sends the bearer token, disables redirects, and sets the timeouts."""
    http = FakeHttpSession([TOKEN_REPLY, LIST_REPLY])  # WHY: token first, then the API reply.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    reply = _post(client)  # WHY: one call.
    assert reply.http_status == 200  # WHY: the API reply arrived.
    token_url, token_kwargs = http.calls[0]  # WHY: the token request is the first call.
    assert token_url.endswith("getAccessToken")  # WHY: the documented token endpoint.
    assert token_kwargs["headers"]["Authorization"].startswith("Basic ")  # WHY: the Basic header.
    assert token_kwargs["data"]["grant_type"] == "client_credentials"  # WHY: the documented form field.
    _api_url, api_kwargs = http.calls[1]  # WHY: the API call is the second call.
    assert api_kwargs["headers"]["Authorization"] == f"Bearer {TEST_TOKEN}"  # WHY: the bearer header.
    assert api_kwargs["allow_redirects"] is False  # WHY: redirects are never followed.
    assert api_kwargs["timeout"] == (10.0, 60.0)  # WHY: the connect and read limits.


def test_host_outside_the_allowlist_is_refused_before_any_send() -> None:
    """A call to an unlisted host raises before any network call."""
    http = FakeHttpSession([])  # WHY: no reply is queued, so any call would fail the test.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    with pytest.raises(JuniperTransportError, match="not in JUNIPER_ALLOWED_HOSTS"):  # WHY: the host check.
        _post(client, base="https://evil.example.org/css-caseapi/1.0")  # WHY: an unlisted host.
    assert http.calls == []  # WHY: nothing was sent.


def test_plain_http_base_address_is_refused_before_any_send() -> None:
    """A base address that does not use HTTPS raises before any network call."""
    http = FakeHttpSession([])  # WHY: no reply is queued.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    with pytest.raises(JuniperTransportError, match="HTTPS"):  # WHY: the scheme check.
        _post(client, base="http://apigw.juniper.net/css-caseapi/1.0")  # WHY: plain HTTP.
    assert http.calls == []  # WHY: nothing was sent.


def test_redirect_reply_is_refused_and_not_followed() -> None:
    """A 302 reply raises instead of being followed."""
    http = FakeHttpSession([TOKEN_REPLY, FakeResponse(302, b"")])  # WHY: the API replies with a redirect.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    with pytest.raises(JuniperTransportError, match="unexpected HTTP 302"):  # WHY: the redirect is refused.
        _post(client)  # WHY: one call.
    assert len(http.calls) == 2  # WHY: the token call and the one refused call, with no follow-up.


def test_temporary_status_retries_with_a_new_transaction_identifier() -> None:
    """A 503 reply retries after a 2-second pause, and each attempt uses a new identifier."""
    http = FakeHttpSession([TOKEN_REPLY, FakeResponse(503), LIST_REPLY])  # WHY: fail once, then succeed.
    client, sleeps = _client(http)  # WHY: the gateway under test.
    seen: list[str] = []  # WHY: record the identifiers.
    reply = _post(client, seen)  # WHY: the call with a retry.
    assert reply.attempts == 2  # WHY: two attempts were used.
    assert len(seen) == 2  # WHY: the builder ran once per attempt.
    assert seen[0] != seen[1]  # WHY: a new identifier avoids fault 955.
    assert 2.0 in sleeps  # WHY: the first backoff is 2 seconds (R-11).


def test_retries_stop_after_the_configured_attempts() -> None:
    """When every attempt returns 503, the call raises after the configured number of attempts."""
    http = FakeHttpSession([TOKEN_REPLY, FakeResponse(503), FakeResponse(503), FakeResponse(503)])  # WHY: three fails.
    client, _sleeps = _client(http, retry_attempts=3)  # WHY: three attempts in total.
    with pytest.raises(JuniperTransportError, match="failed after 3 attempts"):  # WHY: the retries are used up.
        _post(client)  # WHY: one call.


def test_connection_error_is_retried() -> None:
    """A connection error is treated as temporary and the call succeeds on the next attempt."""
    http = FakeHttpSession([TOKEN_REPLY, requests.ConnectionError("network down"), LIST_REPLY])  # WHY.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    assert _post(client).attempts == 2  # WHY: the second attempt succeeded.


def test_connection_timeout_is_retried() -> None:
    """A read timeout is treated as temporary, like a connection error, and the next attempt succeeds."""
    http = FakeHttpSession([TOKEN_REPLY, requests.Timeout("read timed out"), LIST_REPLY])  # WHY: one timeout first.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    assert _post(client).attempts == 2  # WHY: the second attempt succeeded.


def test_reply_larger_than_the_cap_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """A reply over the size cap raises while the body streams."""
    monkeypatch.setattr(JuniperGatewayClient, "MAX_RESPONSE_BYTES", 10)  # WHY: a small cap for the test.
    http = FakeHttpSession([TOKEN_REPLY, FakeResponse(200, b"x" * 50)])  # WHY: a body over the cap.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    with pytest.raises(JuniperTransportError, match="limit"):  # WHY: the size cap.
        _post(client)  # WHY: one call.


def test_unauthorized_reply_refreshes_the_token_once() -> None:
    """A 401 reply requests a new token and sends the call once more."""
    http = FakeHttpSession([TOKEN_REPLY, FakeResponse(401), TOKEN_REPLY, LIST_REPLY])  # WHY: expire, then refresh.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    assert _post(client).http_status == 200  # WHY: the refreshed call succeeded.
    token_calls = [call for call in http.calls if "data" in call[1]]  # WHY: token calls carry form data.
    assert len(token_calls) == 2  # WHY: exactly one refresh.


def test_token_reply_without_an_access_token_fails() -> None:
    """A token reply without an access token raises and never prints the reply."""
    http = FakeHttpSession([FakeResponse(200, json_bytes({"token_type": "Bearer"}))])  # WHY: no token in the reply.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    with pytest.raises(JuniperTransportError, match="no access token"):  # WHY: the missing token.
        _post(client)  # WHY: one call.


def test_secrets_and_tokens_never_reach_the_log(caplog: pytest.LogCaptureFixture) -> None:
    """A full successful call logs no client secret and no bearer token."""
    caplog.set_level(logging.DEBUG)  # WHY: capture every level so the check is strict.
    http = FakeHttpSession([TOKEN_REPLY, LIST_REPLY])  # WHY: token, then the API reply.
    client, _sleeps = _client(http)  # WHY: the gateway under test.
    _post(client)  # WHY: one full call that logs several lines.
    assert "juniper.request" in caplog.text  # WHY: the log is active, so the check means something.
    assert TEST_SECRET not in caplog.text  # WHY: the client secret never reaches the log.
    assert TEST_TOKEN not in caplog.text  # WHY: the bearer token never reaches the log.


def test_rate_limiter_pauses_when_no_token_is_left() -> None:
    """The second request in the same instant waits for the refill."""
    clock = FakeClock()  # WHY: time does not move on its own.
    sleeps: list[float] = []  # WHY: record the pauses.
    limiter = RequestRateLimiter(2.0, clock, lambda seconds: sleeps.append(seconds))  # WHY: 2 requests per second.
    assert limiter.acquire() == 0.0  # WHY: the first request uses the starting token.
    assert limiter.acquire() == pytest.approx(0.5)  # WHY: the next token refills in half a second at 2 per second.
    assert sleeps == [pytest.approx(0.5)]  # WHY: the pause was requested once.
