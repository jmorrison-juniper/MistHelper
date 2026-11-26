"""Read-only Mist API client for the NOC runbook smoke test.

The client sends GET requests through a mistapi session, and no other method. It counts each
attempt against a request budget. It waits at most a call timeout for each attempt. It retries
server errors and connection failures with backoff. It follows a paging link only when the link
stays on the approved host.

Why: the smoke test uses a production read-only token. One fault must never send another method,
exceed the budget, or send a request to a foreign host.
"""

from __future__ import annotations  # Postpone annotation evaluation, so classes can name each other.

import hashlib  # Fingerprint each accepted page for the repeated page rule.
import json  # Read each 2xx body and write the canonical JSON of a page.
import random  # Draw the jitter that spreads the retry waits.
import re  # Read the Retry-After header as integer seconds.
import threading  # Run each SDK call in a daemon thread that has a timeout.
import time  # Supply the default clock and the default sleep.
from collections.abc import Callable  # Type the injected sleep, clock, and wait functions.
from dataclasses import dataclass, field  # Declare the value objects and the mutable governor.
from enum import StrEnum  # Name the error classes and the paging stop reasons.
from functools import partial  # Fix the jitter range of the default random source.
from typing import Any  # Type the JSON bodies, which can be objects or arrays.
from urllib.parse import SplitResult, parse_qsl, quote, unquote, urlsplit  # Split, encode, and decode links.

import structlog  # Structured logging of each request event.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


@dataclass(frozen=True)
class CallRecord:  # Hold one attempt, so checks count requests exactly.
    """One attempt of one GET call, with the facts that the checks and the evidence need.

    Why: each check counts its requests and reads each status. The record keeps the status, the
    error class, and the header names. It keeps no header value and no query value.
    """

    class ErrorClass(StrEnum):  # Name each failure class, so rules avoid status checks.
        """Error classes of one attempt, with the names of the smoke test contract."""

        THROTTLED = "Throttled"  # HTTP 429. The SDK already retried it, so the client does not retry.
        TIMEOUT = "Timeout"  # The SDK call did not finish within the call timeout.
        BUDGET_EXHAUSTED = "BudgetExhausted"  # The request budget was spent, so nothing was sent.
        MALFORMED_JSON = "MalformedJson"  # A 2xx body holds text that is not valid JSON.
        EMPTY_BODY = "EmptyBody"  # A 2xx body holds no text.
        MISSING_RESULTS = "MissingResults"  # A search page holds no results list.
        CONNECTION_ERROR = "ConnectionError"  # No HTTP response reached the client.
        SERVER_ERROR = "ServerError"  # HTTP 5xx.
        UNAUTHORIZED = "Unauthorized"  # HTTP 401. The token is rejected.
        HTTP_ERROR = "HttpError"  # Any other HTTP 4xx, and any other status outside 2xx.

    path_label: str  # Path template with placeholders, never the real identifiers.
    query_names: tuple[str, ...]  # Names of the query parameters, never their values.
    status_code: int | None  # HTTP status, or None when no response exists.
    error_class: ErrorClass | None  # None when the attempt succeeded.
    error_text: str  # At most 200 characters of the error detail.
    data: Any  # Parsed body. An empty object when the SDK could not parse the body.
    next_value: Any  # Next link from the SDK. Kept in memory only.
    header_names: tuple[str, ...]  # Lower-case names of the response headers.
    retry_after_seconds: tuple[int | str, ...]  # Integer seconds, or "not numeric" for another form.
    elapsed_seconds: float  # Time of the attempt, rounded to two decimals.
    attempt: int  # Attempt number, from 1.
    method: str = "GET"  # The only method that the client sends.

    @classmethod
    def from_response(  # Build an attempt from a response, reading the status first.
        cls,
        path_label: str,
        query_names: tuple[str, ...],
        response: Any,
        attempt: int,
        elapsed_seconds: float,
    ) -> CallRecord:
        """Build the record of one attempt that received an SDK response.

        Why: the status is read before the body. An error response therefore never reaches the
        result path, and an empty or malformed body never looks like zero records.

        Args:
            path_label: Path template of the call.
            query_names: Names of the query parameters that the call sent.
            response: SDK response with the status_code, data, raw_data, headers, and next members.
            attempt: Attempt number, from 1.
            elapsed_seconds: Time that the attempt took.

        Returns:
            The record of the attempt.
        """
        status_code = response.status_code  # Read the status before the body.
        headers = {str(name).lower(): value for name, value in (response.headers or {}).items()}  # Lower-case names.
        error_class, error_text = cls._classify(path_label, status_code, response)  # Map the status and the body.
        return cls(  # Build the record with the values that were read above.
            path_label=path_label,  # Keep the template, never the real identifiers.
            query_names=query_names,  # Names only.
            status_code=status_code,  # None when no response exists.
            error_class=error_class,  # None for a valid 2xx body.
            error_text=error_text,  # At most 200 characters.
            data=response.data,  # The parsed body, which the checks read.
            next_value=response.next,  # The SDK next link, kept in memory only.
            header_names=tuple(sorted(headers)),  # Header names only, in a stable order.
            retry_after_seconds=cls._retry_after_values(headers),  # Integer seconds or "not numeric".
            elapsed_seconds=round(elapsed_seconds, 2),  # Two decimals, as the data model states.
            attempt=attempt,  # Attempt number.
        )

    @classmethod
    def without_response(  # Keep counts exact for attempts that never got a response.
        cls,
        path_label: str,
        query_names: tuple[str, ...],
        error_class: ErrorClass,
        attempt: int,
        elapsed_seconds: float,
    ) -> CallRecord:
        """Build the record of an attempt that produced no SDK response.

        Why: the budget refusal and the timeout both end an attempt with no response. Each attempt
        still needs one record, so the request counts of the checks stay exact.

        Args:
            path_label: Path template of the call.
            query_names: Names of the query parameters of the call.
            error_class: Why the attempt ended without a response.
            attempt: Attempt number, from 1.
            elapsed_seconds: Time that the attempt took, or zero when nothing was sent.

        Returns:
            The record of the attempt, with no status and an empty body.
        """
        return cls(  # Build the record of an attempt with no response.
            path_label=path_label,  # Keep the template, never the real identifiers.
            query_names=query_names,  # Names only.
            status_code=None,  # No HTTP response exists.
            error_class=error_class,  # Why the attempt ended.
            error_text="",  # No error body exists.
            data={},  # The same empty object that the SDK uses when there is no body.
            next_value=None,  # No next link exists.
            header_names=(),  # No headers exist.
            retry_after_seconds=(),  # No Retry-After value exists.
            elapsed_seconds=round(elapsed_seconds, 2),  # Two decimals.
            attempt=attempt,  # Attempt number.
        )

    @staticmethod
    def _classify(  # Map each status to one class, so rules read one value.
        path_label: str,
        status_code: int | None,
        response: Any,
    ) -> tuple[CallRecord.ErrorClass | None, str]:
        """Map one HTTP status and its body to an error class and an error text.

        Why: each status has one meaning in the contract. The retry and stop rules read one class,
        so they never repeat the status tests.

        Args:
            path_label: Path template, for the log event of a malformed body.
            status_code: HTTP status, or None when no response exists.
            response: SDK response whose data and raw_data decide a 2xx result.

        Returns:
            The error class, or None for a valid 2xx body, and the error text of at most 200 characters.
        """
        if status_code is None:  # No HTTP response reached the client.
            return CallRecord.ErrorClass.CONNECTION_ERROR, ""  # A connection failure has no body.
        error_text = (  # Keep the detail text to 200 characters, or empty text when the body has no detail.
            str(response.data.get("detail") or "")[:200] if isinstance(response.data, dict) else ""
        )
        if not 200 <= status_code <= 299:  # Each status outside 2xx is an error.
            default_class = (  # A 5xx status can recover, so it is a server error. Other statuses are HTTP errors.
                CallRecord.ErrorClass.SERVER_ERROR if status_code >= 500 else CallRecord.ErrorClass.HTTP_ERROR
            )
            known_classes = {  # 401 and 429 have their own classes. Other statuses use the default.
                401: CallRecord.ErrorClass.UNAUTHORIZED,
                429: CallRecord.ErrorClass.THROTTLED,
            }
            return known_classes.get(status_code, default_class), error_text  # Return the class and the error text.
        return CallRecord._body_class(path_label, status_code, response)  # A 2xx body is checked here.

    @staticmethod
    def _body_class(  # The SDK gives both an empty object, so raw text decides.
        path_label: str, status_code: int, response: Any
    ) -> tuple[CallRecord.ErrorClass | None, str]:
        """Classify the body of a 2xx response as empty, malformed, or valid.

        Why: the SDK sets the data to an empty object for an empty body and for a malformed body.
        The body text therefore decides between them. A valid body that holds an empty object is
        still a valid body.

        Args:
            path_label: Path template, for the log event of a malformed body.
            status_code: HTTP status of the response, for the log event.
            response: SDK response whose raw_data holds the body text.

        Returns:
            The error class, or None for a valid body, and an empty error text.
        """
        raw_text = response.raw_data or ""  # A missing raw body counts as empty.
        if not raw_text.strip():  # A 2xx response with no text has an empty body.
            return CallRecord.ErrorClass.EMPTY_BODY, ""  # An empty body is an error, never zero records.
        try:  # The SDK keeps parsed data only for valid JSON, so the text is checked here too.
            json.loads(raw_text)  # Parse the text to prove that it is valid JSON.
        except ValueError:  # The text is not valid JSON.
            logger.exception("Body of %s is not valid JSON, status %s", path_label, status_code)  # Keep the traceback.
            return CallRecord.ErrorClass.MALFORMED_JSON, ""  # A malformed body is never zero records.
        return None, ""  # A valid 2xx body has no error class.

    @staticmethod
    def _retry_after_values(  # Read Retry-After as seconds, and keep other forms visible.
        headers: dict[str, Any],
    ) -> tuple[int | str, ...]:
        """Return the Retry-After header as integer seconds, or as the text "not numeric".

        Why: the contract records integer seconds only. Another form stays visible as a text value,
        so a reader never mistakes it for a zero wait.

        Args:
            headers: Response headers with lower-case names.

        Returns:
            A one-item tuple with the seconds or the text, or an empty tuple when the header is absent.
        """
        raw_value = headers.get("retry-after")  # Use the lower-case name, because the caller lower-cases each header.
        if raw_value is None:  # The response has no Retry-After header.
            return ()  # Record no value.
        text = str(raw_value).strip()  # Ignore the white space around the value.
        if re.fullmatch(r"[0-9]+", text) is None:  # Only plain digits are integer seconds.
            return ("not numeric",)  # Keep the other form visible.
        return (int(text),)  # Integer seconds.


@dataclass(frozen=True)
class PageSet:  # Hold the result of one paged query, with its stop reason.
    """Result of one paged query: its records, its attempts, and the reason that it stopped.

    Why: SMK-06 and SMK-07 compare the first page with a count, and each check counts its requests.
    The result keeps the records and the attempts, and it never keeps a next link.
    """

    class StopReason(StrEnum):  # Name the paging stop reasons, so each stop has one label.
        """Stop reasons of the paging rules. A failed call gives its error class instead."""

        PAGE_CEILING = "PageCeiling"  # The page limit ended the query while a next link remained.
        FOREIGN_ORIGIN = "ForeignOrigin"  # A next link names a host or a path that is not approved.
        REPEATED_PAGE = "RepeatedPage"  # A next link or the content of a page repeats an earlier one.

    class NextForm(StrEnum):  # Name each next link form, so evidence records its kind.
        """Form of the last next link of a query."""

        RELATIVE = "relative"  # A path under /api/v1/ with no host.
        ABSOLUTE = "absolute"  # An https link on the approved host.
        NONE = "none"  # The last page had no next link.
        REJECTED = "rejected"  # A next link failed the origin or the path rules.

    path_label: str  # Path template of the query.
    records: tuple[Any, ...]  # Items of the results lists of the accepted pages, in order.
    record_count: int  # Number of items in records.
    pages_read: int  # Number of pages that the query requested.
    calls: tuple[CallRecord, ...]  # Every attempt of every page, in request order.
    complete: bool  # True only when the last accepted page had no next link.
    stop_reason: str | None  # Why the query stopped early, or None when it completed.
    next_form: str  # Form of the last next link, as a NextForm value.

    @staticmethod
    def digest_of(records: list[Any]) -> str:  # Hash a page of records, so repeats are found by content.
        """Return the SHA-256 digest of the canonical JSON of one page of records.

        Why: a server that repeats a page under a new next link returns the same records again. The
        digest of the canonical JSON finds that repeat, even when the key order of the source differs.

        Args:
            records: Items of one results list.

        Returns:
            The lower-case hexadecimal digest.
        """
        canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False)  # Canonical JSON.
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()  # Digest of the UTF-8 bytes.

    @staticmethod
    def register(key: str, seen: set[str]) -> bool:  # Record each key once, so a repeat stops the query.
        """Remember a key in a set of seen keys, and report whether the key was seen before.

        Why: a repeated page digest or a repeated next link ends a paged query. Both checks use one rule:
        remember each key once, and report the second occurrence.

        Args:
            key: Page digest or next link to remember.
            seen: Keys that were seen earlier in the same query.

        Returns:
            True when the key was already in the set, and False when the key is new.
        """
        if key in seen:  # The key was seen before.
            return True  # The caller stops the query.
        seen.add(key)  # Remember the new key for the rest of the query.
        return False  # The key is new.

    @staticmethod
    def origin_is_allowed(  # Block foreign hosts, so the token never reaches them.
        parts: SplitResult, approved_host: str, path_label: str
    ) -> bool:
        """Return True when a link names no origin, or names the approved https origin.

        Why: a link names another host only through its scheme and host parts. An absolute link must
        therefore match the approved origin exactly, with port 443 or no port, and no user information.

        Args:
            parts: Split next link.
            approved_host: Lower-case host name that the run approved.
            path_label: Path template of the query, for the log event of a bad port.

        Returns:
            True when the origin is allowed.
        """
        if not (parts.scheme or parts.netloc):  # A relative link names no origin.
            return True  # No origin check applies to a relative link.
        if parts.scheme != "https" or "@" in parts.netloc:  # Only https is allowed, with no user information.
            return False  # The scheme or the user information is not allowed.
        try:  # An invalid port cannot match the approved origin.
            port = parts.port  # The port property raises ValueError when the port text is not a number.
        except ValueError:  # The port text is not a valid number.
            logger.exception("Next link of %s has an invalid port", path_label)  # Keep the traceback for the operator.
            return False  # An invalid port fails the origin check.
        return parts.hostname == approved_host and port in (None, 443)  # Host and port must both match.

    @staticmethod
    def path_is_allowed(path: str) -> bool:  # Block paths that escape the prefix, even when encoded.
        """Return True when a path stays under the API prefix and has no parent segment.

        Why: a backslash or an encoded dot segment can leave the API prefix on some servers. The path
        is therefore checked after it is decoded.

        Args:
            path: Path part of the next link, before decoding.

        Returns:
            True when the path is allowed.
        """
        decoded = unquote(path)  # Decode first, so that an encoded dot segment is found.
        if "\\" in path or "\\" in decoded:  # A backslash can change the path on some servers.
            return False  # A backslash is never allowed in a next link.
        if not decoded.startswith("/api/v1/") or decoded.startswith("//"):  # The path must stay under the prefix.
            return False  # The path leaves the API prefix.
        return ".." not in decoded.split("/")  # A parent segment could leave the prefix.


@dataclass
class CallGovernor:  # Share one budget and timeout count across the whole run.
    """Budget, timeout, and retry state of one run, shared by every request of the run.

    Why: the request budget and the timeout count belong to the run, not to one query. One governor
    for the run keeps the count exact, so no query can spend a unit twice or skip one.
    """

    session: Any = field(repr=False)  # The mistapi session. Hidden from repr, because a repr can show headers.
    request_budget: int  # Most requests of the run, including the token validation request.
    call_timeout_seconds: float  # Longest wait for one SDK call, in seconds.
    max_retries: int  # Retries for a server error or a connection failure, from 0 to 2.
    requests_sent: int = 0  # Requests already counted, such as the token validation request.
    timeouts: int = field(default=0, init=False)  # Timeout results of this run.
    sleep: Callable[[float], None] = time.sleep  # Waits between retries. Tests inject a recorder.
    clock: Callable[[], float] = time.monotonic  # Measures the time of each attempt. Tests inject a counter.
    jitter: Callable[[], float] = partial(random.uniform, 0.0, 0.5)  # Random spread of up to 0.5 seconds.
    wait_for_thread: Callable[[threading.Thread, float], None] = threading.Thread.join  # Bounds each call wait.

    def execute(  # Retry only server and connection faults, within the limit.
        self, path_label: str, uri: str, query: dict[str, str]
    ) -> tuple[CallRecord, ...]:
        """Send one request with its retries, and return every attempt in request order.

        Why: a server error or a connection failure can recover within seconds. The retries spread
        the attempts over a short backoff, and each attempt still counts against the budget.

        Args:
            path_label: Path template of the request, for the log events.
            uri: Path that the SDK call receives.
            query: Query parameters that the SDK call receives.

        Returns:
            Every attempt in request order. The last attempt is the final outcome.
        """
        attempts: list[CallRecord] = []  # Every attempt of this request, in order.
        attempt_number = 1  # The first attempt has number 1.
        retry_classes = (CallRecord.ErrorClass.SERVER_ERROR, CallRecord.ErrorClass.CONNECTION_ERROR)  # Retryable.
        while True:  # Retry until the outcome is final or the retries are spent.
            record = self._attempt(path_label, uri, query, attempt_number)  # Send one attempt through the budget.
            attempts.append(record)  # Keep the attempt for the request counts of the checks.
            if record.error_class not in retry_classes or attempt_number > self.max_retries:  # Final or no retry left.
                return tuple(attempts)  # Every attempt, in order, is the answer of this request.
            self._pause(path_label, attempt_number)  # Wait before the next attempt.
            attempt_number += 1  # Count the next attempt.

    def _pause(  # Wait before a retry, so a stalled server can recover.
        self, path_label: str, attempt_number: int
    ) -> None:
        """Wait before a retry, and log the wait before and after it.

        Why: the wait gives a stalled server time to recover. The log shows the operator why the run is quiet.

        Args:
            path_label: Path template of the request, for the log events.
            attempt_number: Attempt that failed, from 1.
        """
        wait_seconds = self.backoff_seconds(attempt_number)  # Compute the wait before the next attempt.
        logger.info(  # Log the planned wait before it starts, so the operator sees why the run is quiet.
            "Retry of %s after attempt %s, waiting %s seconds", path_label, attempt_number, wait_seconds
        )
        self.sleep(wait_seconds)  # Wait so that the server can recover.
        logger.debug("Retry wait for %s finished", path_label)  # Log the end of the wait.

    def backoff_seconds(self, attempt: int) -> float:  # Grow the wait per attempt, so retries do not hit at once.
        """Return the wait before the next attempt: 1 second, then 2 seconds, plus jitter.

        Why: a short wait that grows gives a stalled server time to recover. The wait stays short, so
        the run keeps its time limit.

        Args:
            attempt: Attempt number that failed, from 1.

        Returns:
            The wait in seconds, including the jitter.
        """
        base_seconds: float = 2.0 ** (attempt - 1)  # The first retry waits 1 second, and the second waits 2.
        return base_seconds + self.jitter()  # Add the random spread that avoids synchronized retries.

    def _attempt(  # Count the attempt before sending, so refusals stay exact.
        self, path_label: str, uri: str, query: dict[str, str], attempt: int
    ) -> CallRecord:
        """Send one attempt through the budget and the timeout, and return its record.

        Why: the budget counts each attempt before it starts. A refused attempt sends nothing, and a
        fault after the count still leaves the count correct.

        Args:
            path_label: Path template of the request.
            uri: Path that the SDK call receives.
            query: Query parameters that the SDK call receives.
            attempt: Attempt number, from 1.

        Returns:
            The record of the attempt.
        """
        query_names = tuple(query)  # Names of the query parameters, never the values.
        if self.requests_sent >= self.request_budget:  # The budget is spent, so the attempt sends nothing.
            logger.info(  # Log the refusal, so the operator sees the spent budget.
                "Budget spent for %s, %s of %s used", path_label, self.requests_sent, self.request_budget
            )
            spent = CallRecord.ErrorClass.BUDGET_EXHAUSTED  # Why this attempt ended without a request.
            return CallRecord.without_response(path_label, query_names, spent, attempt, 0.0)  # No request was sent.
        self.requests_sent += 1  # Count the attempt before it starts.
        logger.info("GET %s started, attempt %s", path_label, attempt, requests_sent=self.requests_sent)  # Log first.
        started = self.clock()  # Start the timer of this attempt.
        completed, response = self._run_with_timeout(path_label, uri, query)  # Send the call and wait for it.
        elapsed_seconds = self.clock() - started  # Measure the time of this attempt.
        if completed:  # The SDK returned in time, so its response decides the class.
            record = (  # Build the record from the SDK response, which decides the class.
                CallRecord.from_response(path_label, query_names, response, attempt, elapsed_seconds)
            )
        else:  # The wait ended first. A timeout is never retried.
            self.timeouts += 1  # Count the timeout, because a second one stops the run.
            logger.warning("GET %s timed out, attempt %s", path_label, attempt)  # Log the timeout.
            timed_out = CallRecord.ErrorClass.TIMEOUT  # The class of a wait that ended first.
            record = (  # Build the record of a timed-out attempt, which has no response.
                CallRecord.without_response(path_label, query_names, timed_out, attempt, elapsed_seconds)
            )
        logger.debug("GET %s done, attempt %s, status %s", path_label, attempt, record.status_code)  # Log the result.
        return record  # Return the record of this attempt.

    def _run_with_timeout(  # Run the SDK call in a thread, since the SDK lacks a timeout.
        self, path_label: str, uri: str, query: dict[str, str]
    ) -> tuple[bool, Any]:
        """Run one SDK GET in a daemon thread, and wait at most the call timeout.

        Why: the SDK has no timeout of its own, so a stalled call would block the run. A daemon thread
        can stay behind after a timeout, and it cannot block the exit of the process.

        Args:
            path_label: Path template, for the log event of a fault.
            uri: Path that the SDK call receives.
            query: Query parameters that the SDK call receives.

        Returns:
            True and the SDK response when the call finished in time. False and None on a timeout.

        Raises:
            BaseException: The fault that the SDK call raised, re-raised in the calling thread.
        """
        outcome: list[Any] = []  # Holds the SDK response when the worker finishes.
        failure: list[BaseException] = []  # Holds a fault that the worker raised.

        def work() -> None:  # Store the SDK result or fault, so the caller receives it.
            """Call the SDK GET, and store its response or its fault."""
            try:  # Catch every fault, so that none is lost in the worker thread.
                outcome.append(self.session.mist_get(uri, query))  # Call the GET method only.
            except BaseException as error:  # Any fault goes to the calling thread.
                logger.exception("SDK call for %s raised %s", path_label, type(error).__name__)  # Keep the traceback.
                failure.append(error)  # Hand the fault to the caller.

        worker = threading.Thread(target=work, daemon=True)  # A daemon thread cannot block the process exit.
        worker.start()  # Start the SDK call.
        self.wait_for_thread(worker, self.call_timeout_seconds)  # Wait at most the call timeout.
        if worker.is_alive():  # The call is still running, so the wait ended with a timeout.
            return False, None  # Report the timeout with no response.
        if failure:  # A fault must reach the caller, so the run ends with an internal error.
            raise failure[0]  # Re-raise the SDK fault in the calling thread.
        return True, outcome[0]  # Report the finished call and its response.


@dataclass
class PageWalker:  # Hold the state of one query, so its links stay separate.
    """Read the pages of one query, follow each next link, and stop at the first unsafe link.

    Why: the server controls the next request only through a next link. The link is checked here,
    before any request uses it, so a foreign host or a repeated page stops the query. Create one
    walker for each query, because the walker keeps the links and the digests of that query.
    """

    governor: CallGovernor  # Sends each page through the budget and the timeout.
    approved_host: str  # Lower-case host name that an absolute next link must name.
    records: list[Any] = field(default_factory=list)  # Items of the accepted pages, in order.
    calls: list[CallRecord] = field(default_factory=list)  # Every attempt, in request order.
    seen_next_values: set[str] = field(default_factory=set)  # Next links that were already followed.
    seen_page_digests: set[str] = field(default_factory=set)  # Digests of the accepted pages.
    stop_reason: str | None = None  # Set when the query stops before its last page.
    next_form: str = PageSet.NextForm.NONE  # Form of the last next link.
    pages_read: int = 0  # Number of pages that the walk requested.

    def walk(  # Return partial records at the page ceiling, not an error.
        self, path_label: str, uri: str, query: dict[str, str], max_pages: int
    ) -> PageSet:
        """Read up to max_pages pages, and report how the query ended.

        Why: the page ceiling is a warning for the check, not an error. The walk therefore reports
        the stop reason together with the records that it read.

        Args:
            path_label: Path template of the query.
            uri: Path of the first page.
            query: Query parameters of the first page, including the limit.
            max_pages: Most pages that the walk requests.

        Returns:
            The paged result with its records, its attempts, and its stop reason.
        """
        logger.info("Paging of %s started, up to %s pages", path_label, max_pages)  # Log before the first request.
        for _ in range(max_pages):  # Read at most max_pages pages.
            self.pages_read += 1  # Count the page before its request starts.
            next_value = self._read_page(path_label, uri, query)  # Send the page and read its next link.
            if next_value is None:  # No link follows, or the page stopped the query.
                break  # Leave the loop, because no further page is requested.
            uri, query = self._follow(path_label, next_value, query)  # Check the link before a request uses it.
            if self.stop_reason is not None:  # A rejected or repeated link ends the query.
                break  # Leave the loop, because the link must not be requested.
        else:  # Every allowed page was read, and a next link still remained.
            self.stop_reason = PageSet.StopReason.PAGE_CEILING  # Report the page ceiling.
        logger.debug("Paging of %s finished, %s pages, stop %s", path_label, self.pages_read, self.stop_reason)  # Done.
        return PageSet(  # Build the paged result from the state of this walk.
            path_label=path_label,  # Template of the query.
            records=tuple(self.records),  # Items of the accepted pages.
            record_count=len(self.records),  # Number of items.
            pages_read=self.pages_read,  # Number of pages requested.
            calls=tuple(self.calls),  # Every attempt.
            complete=self.stop_reason is None,  # Complete only when no stop reason was set.
            stop_reason=self.stop_reason,  # Why the query stopped, or None.
            next_form=self.next_form,  # Form of the last next link.
        )

    def _read_page(  # Fetch a page, and keep its records only when it passes.
        self, path_label: str, uri: str, query: dict[str, str]
    ) -> Any:
        """Send one page, keep its records, and return its next link.

        Why: a page is accepted only when the call succeeded and the body holds a results list.
        The content must differ from every earlier page of the query. A page that fails a test ends
        the query.

        Args:
            path_label: Path template of the query.
            uri: Path of the page.
            query: Query parameters of the page.

        Returns:
            The next link of the page, or None when the query ends on this page.
        """
        attempts = self.governor.execute(path_label, uri, query)  # Send the page with its retries.
        self.calls.extend(attempts)  # Keep every attempt for the request counts of the checks.
        return self._accept(attempts[-1])  # The last attempt decides the outcome of the page.

    def _accept(self, final: CallRecord) -> Any:  # Keep only accepted pages, so failed pages add no records.
        """Keep the records of an accepted page, and return its next link.

        Why: only a page that passed every test adds records. A page without a next link sets the form to none.

        Args:
            final: The last attempt of the page.

        Returns:
            The next link of the page, or None when the query ends on this page.
        """
        results = self._admit(final)  # Check the page. None means that the query stopped on this page.
        if results is None:  # A failed or repeated page adds no records.
            return None  # The query ends on this page, with no next link.
        self.records.extend(results)  # Keep the records of the accepted page.
        if final.next_value is None:  # The last page has no next link, so no link form applies.
            self.next_form = PageSet.NextForm.NONE  # Report that no link follows the page.
        return final.next_value  # The next link, or None when no link follows.

    def _admit(  # Reject a bad page, so it never adds records to the result.
        self, final: CallRecord
    ) -> list[Any] | None:
        """Return the results of a page that may be kept, or set the stop reason and return None.

        Why: a page fails when its call failed, when its body has no results list, or when its content
        repeats an earlier page. The digest of an accepted page is remembered for the pages that follow.

        Args:
            final: The last attempt of the page.

        Returns:
            The results list of the page, or None when the query stops on this page.
        """
        if final.error_class is not None:  # A failed page ends the query with its error class.
            self.stop_reason = final.error_class  # Keep the error class as the stop reason.
            return None  # The query ends on this page.
        results = final.data.get("results") if isinstance(final.data, dict) else None  # Search pages hold results.
        if not isinstance(results, list):  # A page without a results list is never an empty success.
            self.stop_reason = CallRecord.ErrorClass.MISSING_RESULTS  # Stop the query with this class.
            return None  # The query ends on this page.
        if PageSet.register(PageSet.digest_of(results), self.seen_page_digests):  # Repeated content stops the query.
            self.stop_reason = PageSet.StopReason.REPEATED_PAGE  # Stop before the repeated records are kept.
            return None  # The repeated page is not kept.
        return results  # The results list of the accepted page.

    def _follow(  # Check each next link, because the server controls it.
        self, path_label: str, next_value: Any, query: dict[str, str]
    ) -> tuple[str, dict[str, str]]:
        """Check one next link, and return the path and the query of the next page.

        Why: a next link comes from the server, so it is untrusted. The link must stay on the approved
        origin and under the API prefix, and it must not repeat an earlier link.

        Args:
            path_label: Path template of the query, for the log event.
            next_value: Next link from the last accepted page.
            query: Query parameters of the last page, which keep the page size.

        Returns:
            The path and the query of the next page. An empty path when the link is not followed.
        """
        parts = urlsplit(next_value) if isinstance(next_value, str) else None  # Only a string can name a page.
        if (  # A foreign origin or a path outside the API prefix is rejected here.
            parts is None
            or not PageSet.origin_is_allowed(parts, self.approved_host, path_label)
            or not PageSet.path_is_allowed(parts.path)
        ):  # The link stops the query before any request.
            self.next_form = PageSet.NextForm.REJECTED  # Record that the link was not followed.
            self.stop_reason = PageSet.StopReason.FOREIGN_ORIGIN  # Stop before any request uses the link.
            logger.warning("Next link of %s is not allowed, so it is not followed", path_label)  # No link in the log.
            return "", {}  # An empty path tells the caller that no request may follow.
        if PageSet.register(next_value, self.seen_next_values):  # The same link would fetch the same page again.
            self.stop_reason = PageSet.StopReason.REPEATED_PAGE  # Stop the query.
            return "", {}  # An empty path tells the caller that no request may follow.
        self.next_form = PageSet.NextForm.ABSOLUTE if parts.scheme else PageSet.NextForm.RELATIVE  # Link form.
        return (  # The next page keeps the query of the link and the page size of the first request.
            parts.path,
            {**dict(parse_qsl(parts.query, keep_blank_values=True)), "limit": query.get("limit", "1000")},
        )


class ReadOnlyMistClient:  # Route all reads through one client, so no check skips rules.
    """Read-only client for the Mist API, with one budget for the whole run.

    Why: the GET rule, the limit rule, the origin rule, and the budget belong in one place. No check
    can then skip one of these rules.
    """

    def __init__(  # Build the client for one run, with its host and budget.
        self, approved_host: str, governor: CallGovernor
    ) -> None:
        """Store the approved host and the governor of the run.

        Args:
            approved_host: Host name of the run, for example api.mist.com.
            governor: Budget, timeout, and retry state of the run.
        """
        self._approved_host: str = approved_host.lower()  # Paging links must name this host.
        self._governor: CallGovernor = governor  # State that every request of the run shares.

    def get(  # Offer one GET call that keeps the budget and limit rules.
        self, path_template: str, identifiers: dict[str, str], query: dict[str, str]
    ) -> tuple[CallRecord, ...]:
        """Send one GET request, and return every attempt in request order.

        Why: a request without paging still needs the budget, the timeout, and the limit rule.

        Args:
            path_template: Path that starts with /api/v1/ and holds placeholders such as {org_id}.
            identifiers: Values for the placeholders. Each value is encoded as one path segment.
            query: Query parameters. The client adds limit=1000 unless the caller sets a limit.

        Returns:
            Every attempt in request order. The last attempt is the final outcome.

        Raises:
            ValueError: The path template does not start with /api/v1/.
            KeyError: A placeholder has no identifier.
        """
        if not path_template.startswith("/api/v1/"):  # Only the API prefix is a valid path template.
            raise ValueError("path template must start with /api/v1/")  # Refuse the template before any request.
        uri = path_template.format_map({key: quote(value, safe="") for key, value in identifiers.items()})  # Encode.
        page_query = {**query, "limit": query.get("limit", "1000")}  # Copy the query, with limit 1000 by default.
        return self._governor.execute(path_template, uri, page_query)  # Send the request through the budget.

    def get_pages(  # Offer a paged GET that stops at the first unsafe link.
        self,
        path_template: str,
        identifiers: dict[str, str],
        query: dict[str, str],
        max_pages: int,
    ) -> PageSet:
        """Read the pages of one query, follow each safe next link, and stop at the page ceiling.

        Why: a search returns one page at a time. The walk stops at the first unsafe link or repeated
        page, and it never follows a link that the approved origin does not allow.

        Args:
            path_template: Path that starts with /api/v1/ and holds placeholders.
            identifiers: Values for the placeholders. Each value is encoded as one path segment.
            query: Query parameters of the first page. The client adds limit=1000 unless the caller sets one.
            max_pages: Most pages that the walk requests. Must be 1 or more.

        Returns:
            The paged result with its records, its attempts, and its stop reason.

        Raises:
            ValueError: The path template or max_pages is not valid.
            KeyError: A placeholder has no identifier.
        """
        if not path_template.startswith("/api/v1/"):  # Only the API prefix is a valid path template.
            raise ValueError("path template must start with /api/v1/")  # Refuse the template before any request.
        if max_pages < 1:  # A walk needs at least one page.
            raise ValueError("max_pages must be 1 or more")  # Refuse a walk with no page before any request.
        uri = path_template.format_map({key: quote(value, safe="") for key, value in identifiers.items()})  # Encode.
        page_query = {**query, "limit": query.get("limit", "1000")}  # Copy the query, with limit 1000 by default.
        return (  # Walk the pages, and stop at the page ceiling or at an unsafe link.
            PageWalker(self._governor, self._approved_host).walk(path_template, uri, page_query, max_pages)
        )

    @property
    def requests_sent(self) -> int:  # Report the request count, which the run summary prints.
        """Return the number of requests counted against the budget, including the login request.

        Why: the run prints the count in its summary line, so the count comes from the one budget.

        Returns:
            The request count of the run.
        """
        return self._governor.requests_sent  # The count that the budget keeps.

    @property
    def timeouts(self) -> int:  # Expose timeouts, since a second timeout stops the run.
        """Return the number of timeout results of this run.

        Why: a second timeout stops the run with the rate-limit exit code, so the command reads the count.

        Returns:
            The timeout count of the run.
        """
        return self._governor.timeouts  # The count that the budget keeps.
