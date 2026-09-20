"""Fetch pages, scripts, and files from the Juniper documentation site.

The transport reads its SSL context, timeout, and headers from ``HttpConfig``,
and it opens each URL through an HTTPS-only opener so a stray ``file:`` or
custom scheme cannot be read. The opener follows an HTTP redirect to its final
destination, allows a different host, and refuses any hop that leaves HTTPS.
HPE now hosts the Juniper datasheets, so a datasheet URL redirects to an
external HPE host, and the harvester must follow that redirect to save the file.
This network permits the Juniper host but blocks the HPE host, so the client
also detects a host that never answers, flags it as unreachable, and fails the
rest of that host's URLs at once instead of paying the full timeout each time.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import http.client  # Type the redirect response and the redirect header block.
import json  # Parse the embedded catalog JSON block.
import logging  # Trace each network read for observability.
import re  # Locate the embedded catalog assignment in the page markup.
import ssl  # Type the SSL context that the opener binds.
import time  # Wait the backoff delay between two retries.
import urllib.error  # Classify a URL error or an HTTP error.
import urllib.parse  # Split a redirect target to enforce the HTTPS-only rule.
import urllib.request  # Build the request and the HTTPS-only opener.
from typing import IO, Any  # Type the redirect stream and the dynamic opener response.

from src.juniper_docs.acquire.http_config import HttpConfig  # Origin, headers, SSL, timeout.

_LOGGER = logging.getLogger(__name__)  # Module logger for every catalog read.

RETRY_COUNT = 3  # Number of extra attempts for a transient network error.
RETRY_BASE_SECONDS = 1.0  # First backoff delay; it doubles on each retry.
MAX_REDIRECTS = 10  # Bound on redirect hops so a redirect loop cannot hang the run.
MAX_CONSECUTIVE_HOST_FAILURES = 3  # No-response failures on one host before it is unreachable.
HOST_COOLDOWN_SECONDS = 60.0  # Pause before a host is tried again after a failure burst.
MAX_HOST_PAUSE_CYCLES = 3  # Pauses without one success before a host is given up for the run.


class HostUnreachableError(urllib.error.URLError):
    """Raised when one host fails to answer repeatedly, so later URLs fail fast.

    This network permits the Juniper host but blocks the HPE host that now serves
    the datasheets. The blocked host accepts the TCP connection and then never
    returns the HTTP response, so each read waits the full timeout. After a small
    number of consecutive no-response failures, the client flags the host and
    raises this error at once for every later URL on that host. This error is a
    ``URLError`` subclass, so the existing download and resolve handlers catch it
    and one dead host fails cleanly instead of stalling the whole run.
    """

    def __init__(self, host: str, failure_count: int) -> None:
        """Store the host and build a clear reason string that names the host."""
        self.host = host  # The host that did not answer, named in the reason string.
        self.failure_count = failure_count  # The consecutive no-response failure count.
        reason = f"host {host} is unreachable from this network after {failure_count} no-response failures"
        super().__init__(reason)  # A URLError, so an existing except clause catches it.


def is_transient_error(error: BaseException) -> bool:
    """Return True when an error is a transient network error worth a retry."""
    if isinstance(error, HostUnreachableError):  # A flagged host must fail fast, never retry.
        return False  # The circuit breaker already decided this host does not answer.
    if isinstance(error, urllib.error.HTTPError):  # An HTTP status error.
        return error.code >= 500 or error.code == 429  # Server or rate-limit errors retry.
    return True  # Every other URL or OS error is a network error, so retry it.


def _is_no_response_error(error: BaseException) -> bool:
    """Return True when an error carries no HTTP response, so the host stayed silent."""
    return not isinstance(error, urllib.error.HTTPError)  # An HTTPError means a status arrived.


class HttpsOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only when every hop stays on HTTPS.

    HPE now hosts the Juniper datasheets, so a datasheet URL answers with an
    HTTP 301 to a different host. This handler follows that redirect to its
    final destination and allows the different host by design. It refuses any
    hop that leaves HTTPS, so the transport keeps its HTTPS-only posture on
    every hop. The base class bounds the chain at ``max_redirections``, so a
    redirect loop stops instead of hanging the run.

    The handler records the final hop host in a shared holder. A blocked
    destination must not blame the host that issued the redirect, because a
    healthy site would otherwise look unreachable and the run would stop.
    """

    max_redirections = MAX_REDIRECTS  # Total redirect hops before the loop guard stops.

    def __init__(self, last_host: list[str] | None = None) -> None:
        """Store the shared holder that carries the final redirect host."""
        super().__init__()  # The base class sets up the standard redirect handling.
        self._last_host = last_host if last_host is not None else []  # Own one when absent.

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: http.client.HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Return the next request for an HTTPS hop, or refuse a non-HTTPS hop."""
        parts = urllib.parse.urlsplit(newurl)  # Split the redirect target into its parts.
        if parts.scheme != "https":  # The HTTPS-only rule must hold for every redirect hop.
            _LOGGER.warning("Refusing a non-HTTPS redirect to %s", newurl)  # Record the refusal.
            raise urllib.error.HTTPError(newurl, code, "non-HTTPS redirect refused", headers, fp)  # Permanent.
        _LOGGER.debug("Following an HTTPS redirect to host %s", parts.netloc)  # Audit the destination.
        self._last_host.clear()  # Drop the host of the hop before this one.
        self._last_host.append(parts.netloc)  # A failure now belongs to this destination.
        return super().redirect_request(req, fp, code, msg, headers, newurl)  # Build the next request.


class JvdCatalogClient:
    """Fetch pages and JSON blocks from the Juniper documentation site."""

    def __init__(self, config: HttpConfig | None = None) -> None:
        """Store the config, build one HTTPS-only opener, and start host tracking."""
        self.config = config or HttpConfig.from_tls_mode("auto")  # Secure by default.
        self._redirect_host: list[str] = []  # The final hop host of the current request.
        self._opener = self._build_opener(self.config.ssl_context)  # Reuse one opener.
        self._host_failures: dict[str, int] = {}  # Consecutive no-response count per host.
        self._responsive_hosts: set[str] = set()  # Hosts that answered at least once.
        self._unreachable_hosts: set[str] = set()  # Hosts flagged so later URLs fail fast.
        self._host_cooldowns: dict[str, float] = {}  # Retry deadline for a paused host.
        self._host_pauses: dict[str, int] = {}  # Pause cycles without a success, per host.

    @property
    def unreachable_hosts(self) -> frozenset[str]:
        """Return the hosts flagged as unreachable, for a run summary count."""
        return frozenset(self._unreachable_hosts)  # A read-only copy for the caller.

    def _build_opener(self, context: ssl.SSLContext) -> urllib.request.OpenerDirector:
        """Return an opener that speaks HTTPS only and raises on an HTTP error."""
        opener = urllib.request.OpenerDirector()  # Start with no scheme handler at all.
        opener.add_handler(urllib.request.HTTPSHandler(context=context))  # HTTPS only.
        opener.add_handler(urllib.request.HTTPDefaultErrorHandler())  # Raise HTTPError.
        opener.add_handler(HttpsOnlyRedirectHandler(self._redirect_host))  # Track the hop.
        opener.add_handler(urllib.request.HTTPErrorProcessor())  # Process the status code.
        return opener  # A file or custom scheme has no handler and cannot be read.

    def _open(self, url: str, method: str = "GET", timeout: float | None = None) -> Any:
        """Return an open response for one HTTPS URL, or raise a URL error."""
        if not url.startswith("https://"):  # Refuse any non-HTTPS scheme up front.
            raise urllib.error.URLError(f"refusing a non-HTTPS URL: {url}")  # Guard.
        host = urllib.parse.urlsplit(url).netloc  # The host drives the reachability state.
        self._raise_when_unreachable(host)  # A flagged host fails fast, with no timeout wait.
        request = urllib.request.Request(url, headers=HttpConfig.HEADERS, method=method)
        return self._open_tracked(request, host, timeout)  # Open with retry and host tracking.

    def _open_tracked(self, request: urllib.request.Request, host: str, timeout: float | None) -> Any:
        """Open the request, retrying a transient error and tracking host reachability."""
        delay = RETRY_BASE_SECONDS  # The first backoff delay before a retry.
        for attempt in range(RETRY_COUNT):  # Retry a transient error a bounded number of times.
            self._raise_when_unreachable(host)  # Stop at once when the breaker has tripped.
            try:
                return self._attempt_open(request, host, timeout, attempt == 0)  # One attempt.
            except (urllib.error.URLError, OSError) as error:  # A network or HTTP error.
                self._raise_when_unreachable(host)  # A tripped breaker fails clearly, not slowly.
                if not is_transient_error(error):  # A permanent error fails at once.
                    raise  # Do not retry a 4xx or a refusing guard error.
                _LOGGER.warning("Transient error, retry %d for %s: %s", attempt + 1, request.full_url, error)
                time.sleep(delay)  # Wait the backoff delay before the next attempt.
                delay *= 2  # Double the delay for the next retry.
        self._raise_when_unreachable(host)  # The last retry may have tripped the breaker.
        return self._attempt_open(request, host, timeout, False)  # Final attempt; its error rises.

    def _attempt_open(
        self,
        request: urllib.request.Request,
        host: str,
        timeout: float | None,
        count_failure: bool,
    ) -> Any:
        """Open once, recording the host responsive on success or counting one failure.

        Only the first attempt for one document counts toward the host failure
        total. A retry of the same document must not count again, because one
        slow file would otherwise flag a healthy host as unreachable.
        """
        try:
            self._redirect_host.clear()  # Start with no redirect recorded for this request.
            response = self._opener.open(request, timeout=self._timeout_for(host, timeout))
        except (urllib.error.URLError, OSError) as error:  # A network or HTTP error.
            blamed = self._redirect_host[0] if self._redirect_host else host  # The real host.
            if count_failure:  # Count one failure for each document, never for each retry.
                self._record_failure(blamed, error)  # Blame the host that actually failed.
            raise  # Re-raise so the retry loop can decide the next step.
        self._record_success(host)  # The host answered, so mark it reachable.
        return response  # The caller reads the live response.

    def _timeout_for(self, host: str, override: float | None) -> float:
        """Return the timeout for one host, short until it answers, long after."""
        if override is not None:  # A caller can shorten the timeout for one request.
            return override  # Honor the explicit per-request timeout.
        if host in self._responsive_hosts:  # The host already answered at least once.
            return self.config.timeout_seconds  # A proven host keeps the full read timeout.
        return self.config.initial_timeout_seconds  # An unproven host waits only a short time.

    def _raise_when_unreachable(self, host: str) -> None:
        """Wait out a host pause, or fail fast once the host used every pause cycle."""
        if host not in self._unreachable_hosts:  # The host is not flagged, so proceed.
            return  # The caller continues with a normal request.
        until = self._host_cooldowns.get(host)  # A paused host carries a retry deadline.
        if until is None:  # The host used every pause cycle, so the run gives it up.
            raise HostUnreachableError(host, MAX_CONSECUTIVE_HOST_FAILURES)  # Fail fast.
        remaining = until - time.monotonic()  # Seconds left before the host is tried again.
        if remaining > 0:  # The pause is still running, so wait instead of losing the file.
            _LOGGER.info("Waiting %.0f seconds for host %s to recover", remaining, host)
            time.sleep(remaining)  # Ride out the pause so no document is lost.
        _LOGGER.info("Pause finished, so host %s is tried again", host)  # Log the retry.
        self._unreachable_hosts.discard(host)  # Let the host serve requests again.
        self._host_cooldowns.pop(host, None)  # Drop the deadline that has now passed.
        self._host_failures.pop(host, None)  # Start the failure count from zero.

    def _record_success(self, host: str) -> None:
        """Mark a host reachable and clear every failure count it carries."""
        self._responsive_hosts.add(host)  # The host answered, so switch to the full timeout.
        self._host_failures.pop(host, None)  # A success resets the consecutive-failure count.
        self._host_pauses.pop(host, None)  # A success proves the host recovered, so reset.

    def _record_failure(self, host: str, error: BaseException) -> None:
        """Count a no-response failure and pause the host when it crosses the threshold."""
        if not _is_no_response_error(error):  # An HTTP status means the host did answer.
            self._responsive_hosts.add(host)  # A status proves the host is reachable.
            self._host_failures.pop(host, None)  # A status resets the no-response count.
            self._host_pauses.pop(host, None)  # A status also clears the pause cycle count.
            return  # A 4xx or 5xx is not a reachability failure.
        count = self._host_failures.get(host, 0) + 1  # One more consecutive no-response failure.
        self._host_failures[host] = count  # Remember the running count for this host.
        if count < MAX_CONSECUTIVE_HOST_FAILURES or host in self._unreachable_hosts:  # Below limit?
            return  # The host keeps serving until it crosses the threshold.
        self._pause_host(host, count)  # The host crossed the threshold, so pause it now.

    def _pause_host(self, host: str, count: int) -> None:
        """Pause one host, and give it up once it used every pause cycle without a success."""
        self._unreachable_hosts.add(host)  # Later URLs wait or fail fast, never stall.
        cycles = self._host_pauses.get(host, 0) + 1  # One more pause without any success.
        self._host_pauses[host] = cycles  # Remember the cycle count for this host.
        if cycles > MAX_HOST_PAUSE_CYCLES:  # The host never recovered across every pause.
            self._host_cooldowns.pop(host, None)  # Drop any deadline from an earlier pause.
            _LOGGER.warning("Host %s is unreachable from this network after %d failures", host, count)
            return  # No deadline is stored, so every later URL on this host fails fast.
        self._host_cooldowns[host] = time.monotonic() + HOST_COOLDOWN_SECONDS  # Retry deadline.
        _LOGGER.warning(
            "Host %s stopped answering after %d failures, so it pauses %.0f seconds (cycle %d of %d)",
            host,
            count,
            HOST_COOLDOWN_SECONDS,
            cycles,
            MAX_HOST_PAUSE_CYCLES,
        )

    def fetch_text(self, url: str, timeout: float | None = None) -> str:
        """Return the decoded body of one page."""
        _LOGGER.debug("Fetching text from %s", url)  # Trace each page read.
        with self._open(url, timeout=timeout) as response:  # Open the HTTPS response and close it.
            body: bytes = response.read()  # Read the full response body into memory.
        return body.decode("utf-8", "ignore")  # Decode and ignore any bad byte.

    def fetch_bytes(self, url: str, timeout: float | None = None) -> bytes:
        """Return the raw bytes of one file."""
        _LOGGER.debug("Fetching bytes from %s", url)  # Trace each binary read.
        with self._open(url, timeout=timeout) as response:  # Open the HTTPS response and close it.
            payload: bytes = response.read()  # Read the undecoded payload into memory.
        return payload  # Return the raw bytes to the caller.

    def fetch_size(self, url: str, timeout: float | None = None) -> int | None:
        """Return the Content-Length of one file, or None when it is unknown."""
        _LOGGER.debug("Probing the size of %s", url)  # Trace the size probe.
        try:
            with self._open(url, method="HEAD", timeout=timeout) as response:  # A HEAD needs no body.
                length = response.headers.get("Content-Length")  # Read the size header.
        except (urllib.error.URLError, urllib.error.HTTPError) as error:  # A probe may fail.
            _LOGGER.warning("Cannot probe the size for %s: %s", url, error)  # Record miss.
            return None  # An unknown size lets the caller fall back to another rule.
        return int(length) if length and length.isdigit() else None  # Parsed byte count.

    def read_page_data(self, url: str) -> object | None:
        """Return the parsed ``__page_data__`` block of one page."""
        _LOGGER.info("Reading embedded catalog data from %s", url)  # Log the intent.
        html = self.fetch_text(url)  # Download the page markup first.
        match = re.search(  # Locate the embedded assignment in the markup.
            r"var __page_data__\s*=\s*(\[.*?\]|\{.*?\})\s*;?\s*(?:</script>|\n)",
            html,
            re.S,
        )
        if match is None:  # The page carries no catalog block.
            _LOGGER.warning("No __page_data__ block found at %s", url)  # Record the miss.
            return None  # The caller treats a missing block as an empty result.
        try:
            data: object = json.loads(match.group(1))  # Parse the captured JSON literal.
        except json.JSONDecodeError as error:  # A malformed block must not stop the run.
            _LOGGER.warning("Malformed __page_data__ block at %s: %s", url, error)  # Miss.
            return None  # The caller treats a malformed block as an empty result.
        _LOGGER.debug("Parsed a catalog block of %d characters", len(match.group(1)))
        return data  # Return the parsed catalog structure to the caller.
