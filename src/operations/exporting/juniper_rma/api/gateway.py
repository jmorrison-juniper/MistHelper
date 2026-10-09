"""HTTPS gateway for the Juniper service APIs.

The gateway enforces HTTPS, the host allowlist, refusal of redirects, the
timeouts, the response size cap, the rate limit, and bounded retries. It also
obtains the OAuth 2.0 bearer token. No other module opens a connection to Juniper.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import base64  # WHY: the token endpoint takes a Basic header built from the client ID and secret.
import logging  # WHY: action log before and after each request, retry, and refusal.
import time  # WHY: monotonic clock for the rate limiter and the token expiry.
from collections.abc import Callable  # WHY: the body builder receives a new transaction identifier.
from typing import TYPE_CHECKING, Any  # WHY: the settings type is needed only for annotations.
from urllib.parse import urlsplit  # WHY: check the scheme and the host of each address.

import requests  # WHY: HTTP transport with explicit redirect and timeout control (R-01).

from src.operations.exporting.juniper_rma.api.messages import (  # WHY: reply record and IDs.
    JuniperTransportReply,
    RequestMessageBuilder,
)

if TYPE_CHECKING:  # WHY: avoid a runtime import cycle with the settings module.
    from src.operations.exporting.juniper_rma.settings import JuniperSettings  # WHY: annotations only.

logger = logging.getLogger(__name__)  # WHY: module logger for request, retry, and refusal events.


class JuniperTransportError(RuntimeError):
    """A Juniper call could not complete. The message names the reason and never holds a secret."""


class RequestRateLimiter:
    """Token bucket with a burst of one token. The rate sets how fast a token refills (R-10)."""

    def __init__(
        self,
        requests_per_second: float,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        """Store the refill rate and the clock functions. The first request does not wait."""
        self._rate = requests_per_second  # WHY: tokens refilled each second.
        self._clock = clock  # WHY: an injected clock keeps the tests fast and exact.
        self._sleeper = sleeper  # WHY: an injected sleep keeps the tests fast.
        self._tokens = 1.0  # WHY: one token is available at the start.
        self._last = clock()  # WHY: refill time is measured from construction.

    def acquire(self) -> float:
        """Spend one token and return the seconds that the caller waited."""
        now = self._clock()  # WHY: refill from the time that passed.
        self._tokens = min(1.0, self._tokens + (now - self._last) * self._rate)  # WHY: the burst is capped at one.
        self._last = now  # WHY: remember the refill point for the next call.
        waited = 0.0  # WHY: report the wait for logging.
        if self._tokens < 1.0:  # WHY: wait only when no token is available.
            waited = (1.0 - self._tokens) / self._rate  # WHY: time for the missing fraction of a token.
            self._sleeper(waited)  # WHY: pause before the request.
            self._tokens = 1.0  # WHY: the pause refills exactly one token.
            self._last = self._clock()  # WHY: refill is measured from the end of the pause.
        self._tokens -= 1.0  # WHY: spend the token for this request.
        return waited  # WHY: the caller logs a real pause.


class JuniperTokenProvider:
    """Request the OAuth 2.0 bearer token and cache it in memory until it nears expiry (R-02)."""

    TIMEOUT = (10.0, 60.0)  # WHY: connect 10 seconds and read 60 seconds (R-12).
    TOKEN_REFRESH_MARGIN_SECONDS = 300.0  # WHY: renew five minutes before the lifetime ends.
    DEFAULT_LIFETIME_SECONDS = 3600  # WHY: the endpoints document shows 3600 seconds.

    def __init__(
        self,
        settings: JuniperSettings,
        http: requests.Session,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Store the settings, the shared HTTP session, and the clock. No token exists yet."""
        self._settings = settings  # WHY: the token URL and the client pair come from settings.
        self._http = http  # WHY: the same session keeps the same TLS trust.
        self._clock = clock  # WHY: an injected clock makes expiry testable.
        self._token: str | None = None  # WHY: nothing is cached before the first request.
        self._expires_at = 0.0  # WHY: an empty cache counts as expired.

    def authorization_header(self, force_refresh: bool = False) -> str:
        """Return the Authorization header value. Request a new token when the cache is empty or old."""
        expired = self._clock() >= self._expires_at  # WHY: refresh before the lifetime ends.
        if force_refresh or self._token is None or expired:  # WHY: a 401 reply forces a refresh.
            self._request_token()  # WHY: fetch a new token from the endpoint.
        return f"Bearer {self._token}"  # WHY: the form that the gateway sends.

    def _request_token(self) -> None:
        """Call the token endpoint with the Basic header and the form fields from the endpoints document."""
        logger.info("juniper.token_request endpoint=getAccessToken")  # WHY: action log before the call, no secret.
        basic = base64.b64encode(  # WHY: the Basic header carries the client pair in base64.
            f"{self._settings.client_id}:{self._settings.client_secret}".encode()
        ).decode(
            "ascii"
        )  # WHY: header values are ASCII text.
        response = self._http.post(  # WHY: one POST to the checked token endpoint.
            self._settings.token_url,
            headers={  # WHY: the two headers from the endpoints document.
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={  # WHY: the form fields from the endpoints document.
                "grant_type": "client_credentials",
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret,
            },
            timeout=self.TIMEOUT,  # WHY: bounded waits (R-12).
            allow_redirects=False,  # WHY: redirects are refused, never followed.
            verify=self._settings.ca_bundle or True,  # WHY: TLS verification with the optional CA bundle (R-13).
        )
        self._store_reply(response)  # WHY: check the status and cache the token.

    def _store_reply(self, response: requests.Response) -> None:
        """Cache the token from a successful reply. Raise when the reply holds no token."""
        if response.status_code != 200:  # WHY: only HTTP 200 carries a token.
            logger.error("juniper.token_failed http_status=%d", response.status_code)  # WHY: status only, not the body.
            raise JuniperTransportError(f"Juniper token request failed with HTTP {response.status_code}")  # WHY: stop.
        payload = JuniperTransportReply.parse_object(response.content)  # WHY: reuse the safe JSON reader.
        token = payload.get("access_token")  # WHY: the bearer value from the reply.
        if not isinstance(token, str) or not token:  # WHY: a reply without a token is a failure.
            raise JuniperTransportError("Juniper token reply held no access token")  # WHY: never print the reply.
        lifetime = self._lifetime_seconds(payload)  # WHY: the lifetime from the reply, or the default.
        self._token = token  # WHY: cache the bearer value in memory only.
        self._expires_at = self._clock() + lifetime - self.TOKEN_REFRESH_MARGIN_SECONDS  # WHY: renew before expiry.
        logger.info("juniper.token_ok lifetime_seconds=%d", lifetime)  # WHY: log the lifetime, never the value.

    def _lifetime_seconds(self, payload: dict[str, Any]) -> int:
        """Return the token lifetime from the reply, or the default when the value is not a number."""
        try:  # WHY: a malformed lifetime must not stop the run.
            return int(payload.get("expires_in", self.DEFAULT_LIFETIME_SECONDS))  # WHY: the reply sets the lifetime.
        except (TypeError, ValueError):  # WHY: non-numeric values use the default.
            return self.DEFAULT_LIFETIME_SECONDS  # WHY: a safe default lifetime.


class JuniperGatewayClient:
    """Send every Juniper request with the token, the limits, and the retry rules."""

    TIMEOUT = (10.0, 60.0)  # WHY: connect 10 seconds and read 60 seconds (R-12).
    MAX_RESPONSE_BYTES = 16 * 1024 * 1024  # WHY: 16 MB cap, enforced while the body streams (R-12).
    CHUNK_BYTES = 8192  # WHY: streaming chunk size for the size cap.
    RETRYABLE_STATUSES = frozenset({429, 502, 503, 504})  # WHY: temporary HTTP statuses (R-11).

    def __init__(
        self,
        settings: JuniperSettings,
        session: requests.Session | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        """Build the limiter and the token provider. The session is created when none is given."""
        self._settings = settings  # WHY: host allowlist, retries, and CA bundle come from settings.
        self._http = session if session is not None else requests.Session()  # WHY: one session for all calls.
        self._clock = clock  # WHY: an injected clock keeps the tests fast.
        self._sleeper = sleeper  # WHY: an injected sleep keeps the tests fast.
        self._limiter = RequestRateLimiter(settings.requests_per_second, clock, sleeper)  # WHY: rate limit (R-10).
        self._tokens = JuniperTokenProvider(settings, self._http, clock)  # WHY: bearer token source.

    def post(
        self,
        endpoint: str,
        base_url: str,
        path: str,
        build_body: Callable[[str], dict[str, Any]],
    ) -> JuniperTransportReply:
        """Send one JSON POST with retries. The builder receives a new transaction ID for each attempt."""
        url = self._checked_url(base_url, path)  # WHY: refuse a non-HTTPS or unlisted host before any send.
        logger.info("juniper.call_start endpoint=%s", endpoint)  # WHY: action log before the call.

        def prepare_attempt() -> tuple[str, Callable[[str], requests.Response]]:
            """Return a new transaction ID and a sender whose envelope carries that ID."""
            transaction_id = RequestMessageBuilder.new_transaction_id()  # WHY: a new identifier per attempt (R-03).
            body = build_body(transaction_id)  # WHY: the body carries that identifier and a fresh timestamp.
            return transaction_id, lambda authorization: self._post_once(url, body, authorization)  # WHY: the sender.

        return self._exchange(endpoint, prepare_attempt)  # WHY: the shared bounded retry loop.

    def get(
        self,
        endpoint: str,
        base_url: str,
        path: str,
        query: dict[str, str],
    ) -> JuniperTransportReply:
        """Send one GET with retries. The query carries the identifier, and no body is sent."""
        url = self._checked_url(base_url, path)  # WHY: refuse a non-HTTPS or unlisted host before any send.
        logger.info("juniper.call_start endpoint=%s", endpoint)  # WHY: action log before the call.

        def prepare_attempt() -> tuple[str, Callable[[str], requests.Response]]:
            """Return an empty transaction ID and a sender for the query, which has no envelope."""
            return "", lambda authorization: self._get_once(url, query, authorization)  # WHY: a GET has no envelope.

        return self._exchange(endpoint, prepare_attempt)  # WHY: the same retry rules as the POST.

    def _exchange(
        self,
        endpoint: str,
        prepare_attempt: Callable[[], tuple[str, Callable[[str], requests.Response]]],
    ) -> JuniperTransportReply:
        """Run the bounded attempts. Each attempt asks prepare_attempt for its transaction ID and sender."""
        for attempt in range(1, self._settings.retry_attempts + 1):  # WHY: bounded attempts from settings.
            transaction_id, send_once = prepare_attempt()  # WHY: a fresh envelope for each attempt.
            reply = self._attempt(endpoint, send_once, attempt, transaction_id)  # WHY: send one attempt.
            if reply is not None:  # WHY: a final reply ends the loop.
                return reply  # WHY: the caller reads the body status.
            self._sleeper(2**attempt)  # WHY: wait 2 seconds, then 4 seconds, before the next attempt (R-11).
        raise JuniperTransportError(f"Juniper {endpoint} did not complete")  # WHY: unreachable for a valid setting.

    def _checked_url(self, base_url: str, path: str) -> str:
        """Return the full address after the scheme and the host allowlist pass."""
        parts = urlsplit(base_url)  # WHY: check the scheme and the host separately.
        host = (parts.hostname or "").lower()  # WHY: the allowlist compares lowercase host names.
        if parts.scheme != "https":  # WHY: only HTTPS is allowed.
            raise JuniperTransportError("Juniper base address must use HTTPS")  # WHY: no address detail needed.
        if host not in self._settings.allowed_hosts:  # WHY: the host must be on the allowlist (FR-004).
            raise JuniperTransportError(
                f"Juniper host {host} is not in JUNIPER_ALLOWED_HOSTS"
            )  # WHY: host is not secret.
        return base_url.rstrip("/") + "/" + path.lstrip("/")  # WHY: exactly one slash between base and path.

    def _attempt(
        self,
        endpoint: str,
        send_once: Callable[[str], requests.Response],
        attempt: int,
        transaction_id: str,
    ) -> JuniperTransportReply | None:
        """Send one attempt. Return None when the failure is temporary and another attempt remains."""
        last_attempt = attempt >= self._settings.retry_attempts  # WHY: the final attempt never asks for a retry.
        waited = self._limiter.acquire()  # WHY: the rate limit applies before every send (R-10).
        if waited > 0:  # WHY: log a real pause only.
            logger.debug("juniper.rate_wait endpoint=%s seconds=%.2f", endpoint, waited)  # WHY: timing only.
        logger.info(  # WHY: action log before the send, with the attempt and the transaction ID.
            "juniper.request endpoint=%s attempt=%d transaction=%s", endpoint, attempt, transaction_id
        )
        started = self._clock()  # WHY: measure the call for the log.
        try:  # WHY: connection problems are temporary.
            response = self._send(send_once)  # WHY: one HTTP call with the bearer token.
        except (requests.ConnectionError, requests.Timeout) as error:  # WHY: retry only transport problems.
            self._on_temporary_failure(endpoint, attempt, last_attempt, type(error).__name__, error)  # WHY: retry rule.
            return None  # WHY: the caller waits and sends again.
        if response.status_code in self.RETRYABLE_STATUSES:  # WHY: 429, 502, 503, and 504 are temporary (R-11).
            response.close()  # WHY: release the connection before a retry.
            self._on_temporary_failure(
                endpoint, attempt, last_attempt, f"http_{response.status_code}", None
            )  # WHY: retry.
            return None  # WHY: the caller waits and sends again.
        raw = self._read_capped(response, endpoint)  # WHY: read the body under the size cap (R-12).
        elapsed_ms = int((self._clock() - started) * 1000)  # WHY: elapsed time for the log.
        logger.info(  # WHY: action log after the call, with the status and timing only.
            "juniper.request_done endpoint=%s http_status=%d elapsed_ms=%d",
            endpoint,
            response.status_code,
            elapsed_ms,
        )
        return JuniperTransportReply(  # WHY: the typed reply for the service layer.
            endpoint=endpoint,
            http_status=response.status_code,
            body=JuniperTransportReply.parse_object(raw),
            transaction_id=transaction_id,
            attempts=attempt,
        )

    def _on_temporary_failure(
        self,
        endpoint: str,
        attempt: int,
        last_attempt: bool,
        reason: str,
        error: BaseException | None,
    ) -> None:
        """Raise when no attempts remain. Otherwise log the retry and return."""
        if last_attempt:  # WHY: no attempts remain, so the call fails.
            raise JuniperTransportError(  # WHY: name the reason, never the URL or a secret.
                f"Juniper {endpoint} failed after {attempt} attempts ({reason})"
            ) from error
        logger.warning(  # WHY: log the retry and its wait.
            "juniper.retry endpoint=%s attempt=%d reason=%s wait_seconds=%d",
            endpoint,
            attempt,
            reason,
            2**attempt,
        )

    def _send(self, send_once: Callable[[str], requests.Response]) -> requests.Response:
        """Send with the bearer token. A 401 reply refreshes the token once. Redirects raise."""
        response = send_once(self._tokens.authorization_header())  # WHY: send with the cached token.
        if response.status_code == 401:  # WHY: an expired or revoked token gets one refresh.
            logger.info("juniper.token_refresh reason=http_401")  # WHY: action log before the refresh.
            response.close()  # WHY: release the first connection.
            fresh = self._tokens.authorization_header(force_refresh=True)  # WHY: a new token from the endpoint.
            response = send_once(fresh)  # WHY: retry once with the new token.
        if 300 <= response.status_code < 400:  # WHY: a redirect is never followed (R-07).
            logger.warning("juniper.redirect_refused http_status=%d", response.status_code)  # WHY: status only.
            response.close()  # WHY: release the connection.
            raise JuniperTransportError(f"Juniper replied with unexpected HTTP {response.status_code}")  # WHY: stop.
        return response  # WHY: the caller reads the body under the cap.

    def _post_once(self, url: str, body: dict[str, Any], authorization: str) -> requests.Response:
        """Send one POST with the given Authorization header. Redirects are not followed."""
        headers = {  # WHY: JSON request and reply, with the bearer header.
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        return self._http.post(  # WHY: one checked HTTP call.
            url,
            json=body,  # WHY: the envelope is sent as JSON.
            headers=headers,
            timeout=self.TIMEOUT,  # WHY: bounded waits (R-12).
            allow_redirects=False,  # WHY: redirects are refused.
            stream=True,  # WHY: the size cap is enforced while the body streams.
            verify=self._settings.ca_bundle or True,  # WHY: TLS verification (R-13).
        )

    def _get_once(self, url: str, query: dict[str, str], authorization: str) -> requests.Response:
        """Send one GET with the given Authorization header and query. Redirects are not followed."""
        headers = {  # WHY: a GET asks for JSON and carries the bearer header.
            "Authorization": authorization,
            "Accept": "application/json",
        }
        return self._http.get(  # WHY: one checked HTTP call.
            url,
            params=query,  # WHY: the identifier travels as a query parameter.
            headers=headers,
            timeout=self.TIMEOUT,  # WHY: bounded waits (R-12).
            allow_redirects=False,  # WHY: redirects are refused.
            stream=True,  # WHY: the size cap is enforced while the body streams.
            verify=self._settings.ca_bundle or True,  # WHY: TLS verification (R-13).
        )

    def _read_capped(self, response: requests.Response, endpoint: str) -> bytes:
        """Read the body in chunks and stop when it passes the size cap. Always release the connection."""
        chunks: list[bytes] = []  # WHY: collect the bytes in order.
        total = 0  # WHY: count bytes while the body streams.
        try:  # WHY: the connection is released on success and on failure.
            for chunk in response.iter_content(chunk_size=self.CHUNK_BYTES):  # WHY: stream the body.
                total += len(chunk)  # WHY: track the size before keeping the chunk.
                if total > self.MAX_RESPONSE_BYTES:  # WHY: enforce the 16 MB cap (R-12).
                    raise JuniperTransportError(f"Juniper {endpoint} reply passed the 16 MB limit")  # WHY: stop.
                chunks.append(chunk)  # WHY: keep the chunk.
        finally:  # WHY: runs on success and on failure.
            response.close()  # WHY: release the connection.
        return b"".join(chunks)  # WHY: one bytes object for the JSON reader.
