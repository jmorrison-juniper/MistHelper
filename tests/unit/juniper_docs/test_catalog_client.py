"""Unit tests for the promoted catalog client (T009 coverage).

The tests replace the HTTPS opener with a fake so the fetch, size, and page-data
methods run without a network call. The HTTPS-only guard is exercised directly.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from email.message import Message
from typing import Any
from urllib.parse import urlsplit

import pytest

from src.juniper_docs.acquire.catalog_client import (
    MAX_CONSECUTIVE_HOST_FAILURES,
    MAX_HOST_PAUSE_CYCLES,
    MAX_REDIRECTS,
    HostUnreachableError,
    HttpsOnlyRedirectHandler,
    JvdCatalogClient,
    is_transient_error,
)
from src.juniper_docs.acquire.http_config import HttpConfig


class _FakeResponse:
    """A fake HTTP response that supports the context-manager protocol."""

    def __init__(self, body: bytes = b"", headers: dict[str, str] | None = None) -> None:
        """Store the body and the headers for the fake response."""
        self._body = body  # The response body bytes.
        self.headers = headers or {}  # The response headers map.

    def read(self) -> bytes:
        """Return the fake response body."""
        return self._body  # The scripted payload.

    def __enter__(self) -> _FakeResponse:
        """Enter the response context manager."""
        return self  # The client uses the response with a with-statement.

    def __exit__(self, *_exc: object) -> bool:
        """Exit the response context manager without swallowing an error."""
        return False  # Never suppress an exception.


class _FakeOpener:
    """A fake opener that returns one scripted response for any request."""

    def __init__(self, response: _FakeResponse) -> None:
        """Store the response the opener returns."""
        self.response = response  # The scripted response.

    def open(self, _request: Any, timeout: float | None = None) -> _FakeResponse:
        """Return the scripted response, ignoring the request and timeout."""
        return self.response  # The client reads this response.


def _client(response: _FakeResponse) -> JvdCatalogClient:
    """Return a client whose opener is replaced with the fake opener."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # Build a client.
    client._opener = _FakeOpener(response)  # Replace the HTTPS opener with the fake.
    return client  # Every fetch now reads the scripted response.


def test_fetch_text_decodes_the_body() -> None:
    """The client decodes the response body and ignores a bad byte."""
    client = _client(_FakeResponse(b"hello \xff world"))  # A body with a bad byte.
    assert "hello" in client.fetch_text("https://x/page")  # The body decodes cleanly.


def test_fetch_bytes_returns_the_raw_payload() -> None:
    """The client returns the raw response bytes unchanged."""
    client = _client(_FakeResponse(b"%PDF-1.4 body"))  # A raw PDF payload.
    assert client.fetch_bytes("https://x/a.pdf") == b"%PDF-1.4 body"  # The raw bytes.


def test_fetch_size_reads_the_content_length() -> None:
    """The client reads the content length header as an integer."""
    client = _client(_FakeResponse(headers={"Content-Length": "512"}))  # A size header.
    assert client.fetch_size("https://x/a.pdf") == 512  # The parsed byte count.


def test_fetch_size_is_none_without_a_header() -> None:
    """The client returns None when no content length header is present."""
    client = _client(_FakeResponse(headers={}))  # No content length header.
    assert client.fetch_size("https://x/a.pdf") is None  # An unknown size is None.


def test_read_page_data_parses_the_embedded_block() -> None:
    """The client parses the embedded page-data JSON block."""
    body = b'var __page_data__ = {"jvds": [1, 2]};</script>'  # An embedded block.
    assert _client(_FakeResponse(body)).read_page_data("https://x/") == {"jvds": [1, 2]}


def test_read_page_data_is_none_without_a_block() -> None:
    """The client returns None when the page carries no data block."""
    client = _client(_FakeResponse(b"<html>no block here</html>"))  # No block.
    assert client.read_page_data("https://x/") is None  # A missing block yields None.


def test_read_page_data_is_none_for_a_malformed_json_block() -> None:
    """A malformed JSON block yields None instead of stopping the run."""
    body = b'var __page_data__ = {"jvds": [1, 2,};</script>'  # A truncated literal.
    client = _client(_FakeResponse(body))  # The page carries a broken block.
    with pytest.raises(json.JSONDecodeError):  # The raw literal is not valid JSON.
        json.loads('{"jvds": [1, 2,}')  # Prove the fixture body is truly malformed.
    assert client.read_page_data("https://x/") is None  # The client absorbs the error.


def test_read_page_data_absorbs_a_raised_json_decode_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client returns None when the JSON parser raises a decode error."""
    body = b'var __page_data__ = {"jvds": [1, 2]};</script>'  # A well-formed block.
    client = _client(_FakeResponse(body))  # The page carries a parsable block.

    def _raise(*_args: object, **_kwargs: object) -> object:
        """Raise a decode error for any parse attempt."""
        raise json.JSONDecodeError("bad", "", 0)  # The failure mode under test.

    monkeypatch.setattr(json, "loads", _raise)  # Force the parser to fail.
    assert client.read_page_data("https://x/") is None  # No exception escapes.


def test_read_page_data_logs_the_malformed_block(caplog: pytest.LogCaptureFixture) -> None:
    """The client records the malformed block so an operator can find the page."""
    body = b'var __page_data__ = {"jvds": [1, 2,};</script>'  # A truncated literal.
    client = _client(_FakeResponse(body))  # The page carries a broken block.
    with caplog.at_level(logging.WARNING):  # Capture the warning record.
        client.read_page_data("https://x/bad-page/")  # Read the broken page.
    assert "Malformed __page_data__ block" in caplog.text  # The reason is named.
    assert "https://x/bad-page/" in caplog.text  # The page URL is named.


def test_open_refuses_a_non_https_url() -> None:
    """The client refuses a non-HTTPS URL before it opens any connection."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real opener.
    with pytest.raises(urllib.error.URLError):  # The guard raises a URL error.
        client.fetch_text("http://insecure/page")  # A plain HTTP URL is refused.


def test_open_refuses_a_file_url() -> None:
    """The client refuses a file URL, so a local file cannot be read."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real opener.
    with pytest.raises(urllib.error.URLError):  # The guard raises a URL error.
        client.fetch_bytes("file:///etc/passwd")  # A file URL is refused.


class _FlakyOpener:
    """An opener that fails with a transient error, then succeeds."""

    def __init__(self, failures: int, error: Exception) -> None:
        """Store how many times to fail and the error to raise."""
        self.calls = 0  # Count every open call for the assertions.
        self._failures = failures  # Fail this many times before succeeding.
        self._error = error  # The error to raise on a failing call.

    def open(self, _request: Any, timeout: float | None = None) -> _FakeResponse:
        """Fail a bounded number of times, then return a live response."""
        self.calls += 1  # Record the attempt.
        if self.calls <= self._failures:  # This attempt is scripted to fail.
            raise self._error  # Raise the scripted transient error.
        return _FakeResponse(b"ok body")  # A later attempt succeeds.


def test_client_retries_a_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client retries a transient error with a backoff, then succeeds (defect 3)."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._opener = _FlakyOpener(2, ConnectionResetError("reset"))  # Two resets, then ok.
    assert client.fetch_text("https://x/page") == "ok body"  # The retry recovers the read.
    assert client._opener.calls == 3  # Two failed attempts and one success.


def test_client_does_not_retry_a_permanent_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client never retries a permanent 404 error (defect 3)."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)
    error = urllib.error.HTTPError("https://x/page", 404, "not found", {}, None)  # A 404.
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._opener = _FlakyOpener(99, error)  # Always raises the 404 error.
    with pytest.raises(urllib.error.HTTPError):  # The 404 propagates at once.
        client.fetch_text("https://x/page")  # A 404 is never retried.
    assert client._opener.calls == 1  # Exactly one attempt, no retry.


class _AlwaysTimeout:
    """An opener that answers once, then times out on every later call."""

    def __init__(self, good_calls: int) -> None:
        """Store how many calls succeed before every later call times out."""
        self.calls = 0  # Count every open call for the assertions.
        self._good_calls = good_calls  # Succeed this many times, then always time out.

    def open(self, _request: Any, timeout: float | None = None) -> _FakeResponse:
        """Answer the first calls, then raise a no-response timeout."""
        self.calls += 1  # Record the attempt.
        if self.calls <= self._good_calls:  # The host answers early in the run.
            return _FakeResponse(b"ok body")  # A real response proves the host is alive.
        raise TimeoutError("read timed out")  # A silent host never returns a status.


def test_one_slow_document_does_not_flag_a_healthy_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every retry of one document counts once, so one slow file keeps the host alive."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._opener = _AlwaysTimeout(0)  # Every read of this one document times out.
    with pytest.raises(OSError):  # The document itself fails after every retry.
        client.fetch_bytes("https://healthy/one-big-file.pdf")  # One slow document.
    assert "healthy" not in client.unreachable_hosts  # One document never flags the host.
    assert client._host_failures.get("healthy") == 1  # Exactly one failure, not one per retry.


class _RedirectThenHang:
    """An opener that records a redirect hop, then times out on the destination."""

    def __init__(self, destination: str) -> None:
        """Store the destination host that the request redirects to."""
        self.calls = 0  # Count every open call for the assertions.
        self._destination = destination  # The host the redirect points at.
        self.holder: list[str] = []  # The client shares this holder with the handler.

    def open(self, _request: Any, timeout: float | None = None) -> _FakeResponse:
        """Record the redirect destination, then fail as a silent host does."""
        self.calls += 1  # Record the attempt.
        self.holder.clear()  # Drop the host of the hop before this one.
        self.holder.append(self._destination)  # The redirect moved to this host.
        raise TimeoutError("read timed out")  # The destination never answers.


def test_a_blocked_redirect_target_does_not_blame_the_referring_host() -> None:
    """A dead redirect destination must not flag the healthy site that redirected."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    opener = _RedirectThenHang("www.hpe.com")  # Every request lands on a silent host.
    opener.holder = client._redirect_host  # Share the holder the handler would fill.
    client._opener = opener  # Replace the network opener with the redirecting opener.
    for index in range(MAX_CONSECUTIVE_HOST_FAILURES):  # Enough documents to trip it.
        try:
            client.fetch_bytes(f"https://www.juniper.net/doc-{index}.pdf")  # Redirects.
        except OSError:  # The document fails because the destination never answers.
            continue  # Keep going until the breaker decides which host is at fault.
    assert client.unreachable_hosts == frozenset({_HPE_HOST})  # Only the dead destination is flagged.


def test_a_proven_host_is_paused_rather_than_banned() -> None:
    """A host that answered earlier gets a pause deadline, not a permanent ban."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._record_success("proven")  # The host answered, so the run proved it is alive.
    for _ in range(MAX_CONSECUTIVE_HOST_FAILURES):  # Drive it past the failure threshold.
        client._record_failure("proven", TimeoutError("read timed out"))  # A silent failure.
    assert "proven" in client.unreachable_hosts  # The breaker paused the proven host.
    assert "proven" in client._host_cooldowns  # A pause deadline lets the host return.


def test_a_paused_host_waits_rather_than_losing_a_document() -> None:
    """A proven host pause delays the next read, so no document is recorded as failed."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._responsive_hosts.add("proven")  # The host answered earlier in this run.
    client._unreachable_hosts.add("proven")  # A failure burst paused the host.
    client._host_cooldowns["proven"] = time.monotonic() + 0.2  # A short pause to wait out.
    client._opener = _FlakyOpener(0, TimeoutError("unused"))  # The host answers again.
    started = time.monotonic()  # Record the start so the wait is measurable.
    assert client.fetch_text("https://proven/page") == "ok body"  # The read succeeds.
    assert time.monotonic() - started >= 0.2  # The client waited out the pause.
    assert "proven" not in client.unreachable_hosts  # The flag cleared after the pause.


def test_a_host_that_never_answered_stays_flagged() -> None:
    """A host that never answers is given up, which keeps the fast-fail saving."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    for _ in range(MAX_HOST_PAUSE_CYCLES + 1):  # Use every pause cycle the host receives.
        client._unreachable_hosts.discard("silent")  # Clear the flag, as a pause end does.
        for _ in range(MAX_CONSECUTIVE_HOST_FAILURES):  # Another burst with no answer.
            client._record_failure("silent", TimeoutError("read timed out"))  # Silent again.
    assert "silent" in client.unreachable_hosts  # The host stays flagged for the whole run.
    assert "silent" not in client._host_cooldowns  # No deadline means the run gave it up.
    with pytest.raises(HostUnreachableError):  # Every later URL on the host fails fast.
        client.fetch_text("https://silent/page")  # No wait, because the host is given up.


def test_a_success_clears_the_pause_cycle_count() -> None:
    """One success proves a host recovered, so its pause budget starts again."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    for _ in range(MAX_CONSECUTIVE_HOST_FAILURES):  # One failure burst pauses the host.
        client._record_failure("flaky", TimeoutError("read timed out"))  # A silent failure.
    assert client._host_pauses["flaky"] == 1  # The host used one pause cycle.
    client._record_success("flaky")  # The host answered after the pause finished.
    assert "flaky" not in client._host_pauses  # The pause budget reset, so no ban follows.


def test_is_transient_error_classifies_each_kind() -> None:
    """A server or network error is transient, and a 404 is permanent."""
    assert is_transient_error(urllib.error.HTTPError("u", 503, "e", {}, None)) is True  # 5xx.
    assert is_transient_error(urllib.error.HTTPError("u", 429, "e", {}, None)) is True  # Rate.
    assert is_transient_error(urllib.error.HTTPError("u", 404, "e", {}, None)) is False  # 4xx.
    assert is_transient_error(ConnectionResetError("reset")) is True  # A connection reset.
    assert is_transient_error(urllib.error.URLError("boom")) is True  # A network error.


# The realistic PDF body a datasheet host returns after a redirect.
_PDF_BODY = b"%PDF-1.7 datasheet body"
# An HTML error page a retired link returns with a 206 status, near the measured 11.5 KB.
_HTML_ERROR_BODY = b"<!DOCTYPE html><html><body>Not found</body></html>" + b" " * 11_500


class _ScriptedResponse:
    """A fake HTTP response with a status code, a body, and header access."""

    def __init__(self, code: int, body: bytes, location: str | None = None) -> None:
        """Store the status code, the body, and an optional redirect location."""
        self.code = code  # The HTTP status code the transport reports.
        self.msg = "Scripted"  # The reason phrase the error processor reads.
        self._body = body  # The response body bytes.
        self._headers = Message()  # The header block for the redirect handler.
        if location is not None:  # A redirect response carries a Location header.
            self._headers["Location"] = location  # Point the redirect at the next hop.

    def info(self) -> Message:
        """Return the header block for the redirect and error machinery."""
        return self._headers  # The redirect handler reads the Location from here.

    def read(self, *_args: Any) -> bytes:
        """Return the full response body for a read of any size."""
        return self._body  # The body is a plain bytes value, so it re-reads cleanly.

    def close(self) -> None:
        """Close the response, a no-op for the fake body."""
        return None  # The redirect handler drains and closes each intermediate hop.

    def __enter__(self) -> _ScriptedResponse:
        """Enter the response context manager."""
        return self  # The client reads the final response with a with-statement.

    def __exit__(self, *_exc: object) -> bool:
        """Exit the response context manager without swallowing an error."""
        return False  # Never suppress an exception.


class _ScriptedHttpsHandler(urllib.request.BaseHandler):
    """A fake HTTPS transport that returns a scripted response for each URL."""

    def __init__(self, respond: Callable[[str], _ScriptedResponse]) -> None:
        """Store the response factory and start an empty opened-URL log."""
        self.respond = respond  # A callable that maps one URL to its response.
        self.opened: list[str] = []  # Every opened URL, in order, for the assertions.

    def https_open(self, req: urllib.request.Request) -> _ScriptedResponse:
        """Record the opened URL and return its scripted response."""
        url = req.full_url  # The URL of this hop in the redirect chain.
        self.opened.append(url)  # Record the hop so a test can bound the chain.
        return self.respond(url)  # The scripted response drives the redirect machinery.


def _redirect_client(respond: Callable[[str], _ScriptedResponse]) -> JvdCatalogClient:
    """Return a client whose opener uses the fake transport and the real redirect handler."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # Build a real client.
    opener = urllib.request.OpenerDirector()  # Build an opener with no default handler.
    handler = _ScriptedHttpsHandler(respond)  # The fake HTTPS transport for every hop.
    opener.add_handler(handler)  # The transport answers each https_open call.
    opener.add_handler(urllib.request.HTTPDefaultErrorHandler())  # Raise on an HTTP error.
    opener.add_handler(HttpsOnlyRedirectHandler())  # The handler under test follows redirects.
    opener.add_handler(urllib.request.HTTPErrorProcessor())  # Turn a 3xx into a redirect call.
    client._opener = opener  # Replace the network opener with the scripted opener.
    return client  # Every fetch now runs through the fake transport.


def test_build_opener_uses_the_https_only_redirect_handler() -> None:
    """The production opener wires in the HTTPS-only redirect handler (defect 1)."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    handlers = client._opener.handlers  # The handler chain the client built.
    assert any(isinstance(handler, HttpsOnlyRedirectHandler) for handler in handlers)  # Wired in.


def test_redirect_is_followed_to_its_destination() -> None:
    """A 301 redirect is followed to the destination that serves the PDF (defect 1)."""
    start = "https://www.juniper.net/assets/us/en/local/pdf/datasheets/1000254-en.pdf"  # Legacy ID.
    final = "https://www.juniper.net/content/dam/www/assets/datasheets/us/en/x.pdf"  # Canonical path.
    script = {start: _ScriptedResponse(301, b"", final), final: _ScriptedResponse(200, _PDF_BODY)}
    client = _redirect_client(lambda url: script[url])  # Drive the two-hop redirect chain.
    payload = client.fetch_bytes(start)  # Fetch the legacy URL that redirects onward.
    assert payload == _PDF_BODY  # The client returns the PDF from the redirect destination.


def test_redirect_to_a_different_host_is_allowed_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    """A cross-host redirect is allowed, and the final host is logged for the audit (defect 1)."""
    start = "https://www.juniper.net/content/dam/www/assets/datasheets/us/en/ap47.pdf"  # Datasheet.
    final = "https://www.hpe.com/psnow/doc/ap47-datasheet.pdf"  # HPE now hosts the datasheet.
    script = {start: _ScriptedResponse(301, b"", final), final: _ScriptedResponse(200, _PDF_BODY)}
    client = _redirect_client(lambda url: script[url])  # Drive the cross-host redirect.
    with caplog.at_level(logging.DEBUG, logger="src.juniper_docs.acquire.catalog_client"):  # Capture.
        payload = client.fetch_bytes(start)  # Fetch the datasheet that redirects to HPE.
    assert payload == _PDF_BODY  # The cross-host destination serves the real PDF.
    assert any(
        token == _HPE_HOST for record in caplog.records for token in record.getMessage().split()
    )  # The audit log names the final host as one exact token.


def test_redirect_to_a_non_https_scheme_is_refused() -> None:
    """A redirect to a non-HTTPS scheme is refused and never opened (defect 1)."""
    start = "https://www.juniper.net/assets/us/en/local/pdf/datasheets/legacy.pdf"  # Legacy URL.
    insecure = "http://downgrade.example/legacy.pdf"  # A downgrade to plain HTTP.
    handler_log: list[str] = []  # Record every URL the transport opens.

    def respond(url: str) -> _ScriptedResponse:
        """Return a 301 to the insecure scheme, or fail if the insecure URL is opened."""
        handler_log.append(url)  # Record the opened URL for the assertion below.
        return _ScriptedResponse(301, b"", insecure)  # Redirect to the non-HTTPS scheme.

    client = _redirect_client(respond)  # Drive the downgrade redirect through the handler.
    with pytest.raises(urllib.error.HTTPError) as caught:  # The non-HTTPS hop is refused.
        client.fetch_bytes(start)  # Fetch the URL that redirects to plain HTTP.
    assert insecure not in handler_log  # The insecure destination was never opened.
    assert is_transient_error(caught.value) is False  # A refused hop is a permanent failure.


def test_redirect_chain_is_bounded_so_a_loop_cannot_hang() -> None:
    """A redirect loop stops at the bound instead of hanging the run (defect 1)."""
    client = _redirect_client(lambda url: _ScriptedResponse(301, b"", url + "/next"))  # Endless loop.
    with pytest.raises(urllib.error.HTTPError):  # The bound turns the loop into an error.
        client.fetch_bytes("https://loop.example/start")  # Each hop points at a new URL.
    handler = client._opener.handlers[0]  # The fake transport records every opened URL.
    assert len(handler.opened) <= MAX_REDIRECTS + 1  # The chain stops at the bound.


def test_partial_content_html_body_is_not_retried() -> None:
    """A 206 status with an HTML body is a success, so it consumes no retry (defect 2)."""
    url = "https://www.juniper.net/documentation/en_US/junos/junos-xml-ref-config.pdf"  # Retired link.
    client = _redirect_client(lambda _url: _ScriptedResponse(206, _HTML_ERROR_BODY))  # 206 HTML page.
    payload = client.fetch_bytes(url)  # A 206 is a 2xx status, so the read returns the body.
    handler = client._opener.handlers[0]  # The fake transport records every opened URL.
    assert payload == _HTML_ERROR_BODY  # The client returns the HTML body without an error.
    assert handler.opened == [url]  # One open call only, so a retired link consumes no retry.


# The datasheet host that this network blocks; it accepts the connection then never answers.
_HPE_HOST = "www.hpe.com"  # Compare a parsed hostname to this exact value.
_JUNIPER_HOST = "www.juniper.net"  # The reachable documentation host.
_HPE_URL = "https://www.hpe.com/psnow/doc/a00-datasheet.pdf"
# A second URL on the same blocked host, used to prove the later URL fails fast.
_HPE_URL_TWO = "https://www.hpe.com/psnow/doc/a01-datasheet.pdf"
# A reachable Juniper URL, used to prove one dead host does not affect a different host.
_JUNIPER_URL = "https://www.juniper.net/content/dam/www/assets/datasheets/x.pdf"


class _SilentOpener:
    """An opener whose hosts never answer, so every read raises a timeout."""

    def __init__(self) -> None:
        """Start an empty call log so a test can count the open attempts."""
        self.calls: list[str] = []  # Every opened URL, in order, for the assertions.

    def open(self, request: Any, timeout: float | None = None) -> _FakeResponse:
        """Record the URL and raise a read timeout, the measured HPE failure mode."""
        self.calls.append(request.full_url)  # Record the attempt for the assertions.
        raise TimeoutError("The read operation timed out")  # The blocked host never answers.


class _SelectiveOpener:
    """An opener that times out for the HPE host but answers for the Juniper host."""

    def __init__(self) -> None:
        """Start an empty call log for the per-host assertions."""
        self.calls: list[str] = []  # Every opened URL, in order, for the assertions.

    def open(self, request: Any, timeout: float | None = None) -> _FakeResponse:
        """Answer the Juniper host, but raise a read timeout for the HPE host."""
        self.calls.append(request.full_url)  # Record the attempt for the assertions.
        if urlsplit(request.full_url).hostname == _HPE_HOST:  # The blocked host never answers.
            raise TimeoutError("The read operation timed out")  # The silent read hang.
        return _FakeResponse(b"%PDF juniper body")  # The reachable host answers at once.


class _RecordingOpener:
    """An opener that records the timeout of every open call and answers with a PDF."""

    def __init__(self) -> None:
        """Start empty logs for the recorded timeouts and URLs."""
        self.timeouts: list[float | None] = []  # The timeout passed to each open call.
        self.calls: list[str] = []  # Every opened URL, in order, for the assertions.

    def open(self, request: Any, timeout: float | None = None) -> _FakeResponse:
        """Record the timeout and the URL, then answer with a small PDF body."""
        self.timeouts.append(timeout)  # Record the timeout the client selected for this host.
        self.calls.append(request.full_url)  # Record the URL for the assertions.
        return _FakeResponse(b"%PDF ok")  # A responsive host answers at once.


class _ServerErrorOpener:
    """An opener that always answers with a 503, so the host stays reachable."""

    def __init__(self) -> None:
        """Start an empty call log for the retry-count assertion."""
        self.calls: list[str] = []  # Every opened URL, in order, for the assertions.

    def open(self, request: Any, timeout: float | None = None) -> _FakeResponse:
        """Raise a 503 server error, an HTTP status that proves the host answered."""
        self.calls.append(request.full_url)  # Record the attempt for the assertions.
        raise urllib.error.HTTPError(request.full_url, 503, "unavailable", Message(), None)  # 5xx.


def _trip_host(client: JvdCatalogClient, base: str) -> None:
    """Drive enough distinct documents on one host to trip the failure breaker."""
    for index in range(MAX_CONSECUTIVE_HOST_FAILURES):  # One failure for each document.
        try:
            client.fetch_bytes(f"{base}/doc-{index}.pdf")  # A distinct document each time.
        except OSError:  # The document fails, which is the point of the helper.
            continue  # Keep going until the host crosses the failure threshold.


def test_repeated_no_response_marks_the_host_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A host that times out repeatedly is flagged unreachable after the threshold."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)  # No sleep.
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.MAX_HOST_PAUSE_CYCLES", 0)
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    opener = _SilentOpener()  # Every read on this host times out.
    client._opener = opener  # Replace the network opener with the silent opener.
    _trip_host(client, "https://www.hpe.com/psnow")  # Distinct documents trip the breaker.
    assert client.unreachable_hosts == frozenset({_HPE_HOST})  # The host is now flagged unreachable.
    assert client._host_failures.get(_HPE_HOST, 0) >= MAX_CONSECUTIVE_HOST_FAILURES


def test_a_later_url_on_an_unreachable_host_fails_without_opening(monkeypatch: pytest.MonkeyPatch) -> None:
    """A later URL on a flagged host fails fast, so it never waits the full timeout."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)  # No sleep.
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.MAX_HOST_PAUSE_CYCLES", 0)
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    opener = _SilentOpener()  # Every read on this host times out.
    client._opener = opener  # Replace the network opener with the silent opener.
    _trip_host(client, "https://www.hpe.com/psnow")  # Distinct documents trip the breaker.
    calls_after_trip = len(opener.calls)  # The open-call count once the host is flagged.
    with pytest.raises(HostUnreachableError):  # The next URL must fail at once.
        client.fetch_bytes(_HPE_URL_TWO)  # A later URL on the same flagged host.
    assert len(opener.calls) == calls_after_trip  # No new open call, so no timeout wait.


def test_a_different_host_is_unaffected_by_an_unreachable_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """One flagged host does not stop a read from a different, reachable host."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)  # No sleep.
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.MAX_HOST_PAUSE_CYCLES", 0)
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._opener = _SelectiveOpener()  # The HPE host hangs, the Juniper host answers.
    _trip_host(client, "https://www.hpe.com/psnow")  # Flag the blocked host.
    payload = client.fetch_bytes(_JUNIPER_URL)  # The reachable host still answers.
    assert payload == b"%PDF juniper body"  # The different host returns its body.
    assert _JUNIPER_HOST not in client.unreachable_hosts  # It is not flagged.


def test_the_unreachable_reason_names_the_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """The failure reason names the host and states it is unreachable from this network."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)  # No sleep.
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.MAX_HOST_PAUSE_CYCLES", 0)
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._opener = _SilentOpener()  # Every read on this host times out.
    _trip_host(client, "https://www.hpe.com/psnow")  # Flag the blocked host first.
    with pytest.raises(HostUnreachableError) as caught:  # Capture the raised error.
        client.fetch_bytes(_HPE_URL)  # A later URL on the flagged host fails fast.
    reason = str(caught.value)  # The reason string the runner records on the document.
    assert _HPE_HOST in reason.split()  # The reason names the offending host as one token.
    assert "unreachable from this network" in reason  # The reason states the cause plainly.


def test_a_reachable_host_still_retries_a_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A transient blip on a reachable host still retries, so the retry does not regress."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)  # No sleep.
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    client._opener = _FlakyOpener(2, ConnectionResetError("reset"))  # Two blips, then a success.
    assert client.fetch_bytes(_JUNIPER_URL) == b"ok body"  # The retry recovers the read.
    assert client._opener.calls == 3  # Two failed attempts and one success, as before.
    assert "www.juniper.net" not in client.unreachable_hosts  # A recovered host is not flagged.


def test_a_persistent_server_error_retries_without_flagging_the_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 5xx means the host answered, so it retries fully and is never flagged unreachable."""
    monkeypatch.setattr("src.juniper_docs.acquire.catalog_client.RETRY_BASE_SECONDS", 0.0)  # No sleep.
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    opener = _ServerErrorOpener()  # Every read returns a 503 server error.
    client._opener = opener  # Replace the network opener with the 503 opener.
    with pytest.raises(urllib.error.HTTPError):  # The 503 propagates after the retries.
        client.fetch_bytes(_JUNIPER_URL)  # A 5xx host answers, so the breaker never trips.
    assert len(opener.calls) == 4  # Three retries and one final attempt, the full budget.
    assert "www.juniper.net" not in client.unreachable_hosts  # A 5xx host is not unreachable.


def test_an_unproven_host_uses_the_short_timeout_then_the_full_timeout() -> None:
    """An unproven host waits the short timeout, and a proven host waits the full timeout."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    opener = _RecordingOpener()  # Record the timeout the client selects for each call.
    client._opener = opener  # Replace the network opener with the recording opener.
    client.fetch_bytes(_JUNIPER_URL)  # The first read, before the host has answered.
    client.fetch_bytes(_JUNIPER_URL)  # The second read, after the host has answered once.
    assert opener.timeouts[0] == client.config.initial_timeout_seconds  # Short until it answers.
    assert opener.timeouts[1] == client.config.timeout_seconds  # Full once it is proven.


def test_a_caller_can_shorten_the_per_request_timeout() -> None:
    """A caller can pass a shorter timeout, which the client uses for that request."""
    client = JvdCatalogClient(HttpConfig.from_tls_mode("insecure"))  # A real client.
    opener = _RecordingOpener()  # Record the timeout the client passes to open.
    client._opener = opener  # Replace the network opener with the recording opener.
    client.fetch_bytes(_JUNIPER_URL, timeout=5.0)  # Ask for a short five-second timeout.
    assert opener.timeouts[0] == 5.0  # The client honors the caller's shorter timeout.


def test_is_transient_error_treats_an_unreachable_host_as_permanent() -> None:
    """An unreachable-host error is permanent, so the retry loop never repeats it."""
    error = HostUnreachableError("www.hpe.com", MAX_CONSECUTIVE_HOST_FAILURES)  # The flag error.
    assert is_transient_error(error) is False  # A flagged host must fail fast, never retry.
