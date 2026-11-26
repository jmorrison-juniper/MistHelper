"""Tests for the read-only Mist client of the NOC runbook smoke test.

The tests use fake sessions and the SDK response class. No test opens a network connection, and no
test reads a token. Why: the client must show each HTTP outcome before the live run sends a request
with a production token.
"""

from __future__ import annotations  # Postpone annotations, so the helper types can refer to each other.

import io  # Hold the body bytes of a real HTTP response without a socket.
import json  # Encode the fake JSON bodies that the replies carry.
import threading  # Block a fake SDK call until the test releases it.
from collections.abc import Iterator  # Type the fixture, which yields once and gives no value.
from typing import Any  # Type the scripted replies, which can be fakes or exceptions.

import mistapi  # SDK package. This module is the only test module that imports it at module scope.
import pytest  # Run the parametrized cases and assert the raised errors.
import requests  # Build a real HTTP response object for the SDK response class.
import structlog  # Save and reset the global structlog chain around one test.
from mistapi.__api_response import APIResponse  # SDK class that parses the body text of a real response.
from requests.structures import CaseInsensitiveDict  # Header container of a real HTTP response.
from structlog.testing import capture_logs  # Capture the structured log events of one test.

from scripts.netcool_runbook_smoke.client import CallGovernor, CallRecord, PageSet, ReadOnlyMistClient  # Under test.

ORG_ID = "11111111-2222-4333-8444-555555555555"  # Fake organization identifier, never a real one.
HOST = "api.mist.com"  # Approved host of every test run.
PATH = "/api/v1/orgs/{org_id}/alarms/search"  # Path template with one placeholder.
IDENTIFIERS = {"org_id": ORG_ID}  # Values for the placeholder.
URL = f"https://{HOST}/api/v1/orgs/{ORG_ID}/alarms/search"  # URL that the SDK response reports.
ERROR = CallRecord.ErrorClass  # Short name of the error classes.
STOP = PageSet.StopReason  # Short name of the paging stop reasons.
FORM = PageSet.NextForm  # Short name of the next link forms.


class FakeResponse:  # Stand in for the SDK response with the members that the client reads.
    """Stand-in for an SDK response, with the members that the client reads."""

    def __init__(  # Store the scripted members of the fake SDK response.
        self,
        status_code: int | None,
        data: Any,
        raw_data: str,
        headers: dict[str, str] | None = None,
        next_value: Any = None,
    ) -> None:
        """Store the fake response members.

        Args:
            status_code: HTTP status, or None for a connection failure.
            data: Parsed body.
            raw_data: Body text.
            headers: Response headers.
            next_value: Next link.
        """
        self.status_code = status_code  # The HTTP status, read before the body.
        self.data = data  # The parsed body.
        self.raw_data = raw_data  # The body text, which tells an empty body from a malformed one.
        self.headers = CaseInsensitiveDict(headers or {})  # Case-insensitive headers, as in the SDK.
        self.next = next_value  # The next link of a search page.


def json_reply(  # Build a fake reply whose body text matches its JSON data.
    status_code: int,
    data: Any,
    headers: dict[str, str] | None = None,
    next_value: Any = None,
) -> FakeResponse:
    """Build a fake reply whose body text is the JSON of the data.

    Args:
        status_code: HTTP status of the reply.
        data: JSON data of the body.
        headers: Response headers.
        next_value: Next link of the reply.

    Returns:
        The fake reply.
    """
    return FakeResponse(status_code, data, json.dumps(data), headers, next_value)  # Keep the text consistent.


def sdk_reply(  # Build a real SDK response object, so the parse path runs as it does live.
    status_code: int | None, body: bytes | None, headers: dict[str, str] | None = None
) -> Any:
    """Build a real SDK response from an HTTP status, a body, and headers.

    Args:
        status_code: HTTP status, or None for a connection failure with no response.
        body: Body bytes, or None for no body.
        headers: Response headers.

    Returns:
        The SDK response object that the real mistapi class builds.
    """
    if status_code is None:  # A connection failure gives the SDK no response object.
        return APIResponse(response=None, url=URL)  # The SDK object for a connection failure.
    raw = requests.Response()  # A real requests response, filled without a socket.
    raw.status_code = status_code  # The HTTP status.
    raw.raw = io.BytesIO(body or b"")  # The body bytes, read by the response object.
    raw.encoding = "utf-8"  # The body encoding for the text member.
    raw.headers = CaseInsensitiveDict(headers or {})  # The response headers.
    raw.url = URL  # The request URL.
    return APIResponse(response=raw, url=URL)  # Let the SDK parse the body, as it does live.


class FakeSession:  # Replace the SDK session with a scripted list of replies.
    """Scripted session that records each call. Its only method for a request is mist_get."""

    def __init__(self, script: list[Any]) -> None:  # Store the replies that the calls return or raise, in order.
        """Store the scripted replies.

        Args:
            script: Replies or exceptions, used in order.
        """
        self.script = list(script)  # Replies that the next calls return or raise.
        self.calls: list[tuple[str, dict[str, str]]] = []  # Each GET call with its path and query.
        self.login_calls = 0  # The client must never log in, so this count must stay zero.

    def mist_get(  # Record each GET call and return the next scripted reply.
        self, uri: str, query: dict[str, str] | None = None
    ) -> Any:
        """Record one GET call and return the next scripted reply.

        Args:
            uri: Path of the call.
            query: Query parameters of the call.

        Returns:
            The next scripted reply.

        Raises:
            RuntimeError: The test has no scripted reply left.
        """
        self.calls.append((uri, dict(query or {})))  # Keep the path and the query of the call.
        if not self.script:  # The test scripted too few replies.
            raise RuntimeError("no scripted reply left")  # The test scripted too few replies.
        reply = self.script.pop(0)  # Take the next scripted reply.
        if isinstance(reply, BaseException):  # A scripted fault is raised in the caller.
            raise reply  # Raise the scripted fault.
        return reply  # Return the scripted reply.

    def login(self) -> None:  # Record a login call, so a test can prove that no login happens.
        """Record a login call, which the client must never make."""
        self.login_calls += 1  # Count the call, so that a test can fail on it.


class BlockingSession:  # Replace the SDK session with a call that waits until the test releases it.
    """Session whose GET call waits until the test releases it. It models a stalled SDK call."""

    def __init__(self) -> None:  # Create the events that show the call started and that release it.
        """Create the release and start events."""
        self.release = threading.Event()  # Set by the test, so that no worker stays blocked.
        self.started = threading.Event()  # Set when the worker enters the call.
        self.calls: list[str] = []  # Each requested path.

    def mist_get(  # Block the GET call until the test releases it, as a stalled SDK call does.
        self, uri: str, query: dict[str, str] | None = None
    ) -> Any:
        """Record the call, wait for the release, and then return an empty page.

        Args:
            uri: Path of the call.
            query: Query parameters of the call.

        Returns:
            An empty search page, after the release.
        """
        self.calls.append(uri)  # Keep the requested path.
        self.started.set()  # Tell the test that the worker is inside the call.
        self.release.wait()  # Block until the test sets the release event.
        return json_reply(200, {"results": []})  # An empty page, returned after the release.


class StepClock:  # Replace the wall clock with a counter that moves by a fixed step.
    """Clock that moves forward by a fixed step on each read, so no test waits for real time."""

    def __init__(self, step: float = 0.5) -> None:  # Fix the step, so no test waits for real time.
        """Store the start time and the step.

        Args:
            step: Seconds added on each read.
        """
        self.now = 0.0  # The current fake time.
        self.step = step  # The seconds added on each read.

    def __call__(self) -> float:  # Return the fake time and move the clock forward.
        """Return the current fake time and move the clock forward.

        Returns:
            The fake time before the step.
        """
        value = self.now  # The time of this read.
        self.now += self.step  # Move the clock for the next read.
        return value  # The time before the step.


def make_governor(  # Build a governor that uses fake time, fixed jitter, and no real sleep.
    session: Any,
    budget: int = 60,
    sent: int = 1,
    retries: int = 2,
    sleeps: list[float] | None = None,
) -> CallGovernor:
    """Build a governor with fake time, a fixed jitter, and no real sleep.

    Args:
        session: Session that the governor calls.
        budget: Most requests of the run.
        sent: Requests already counted, such as the login request.
        retries: Retries for a server error or a connection failure.
        sleeps: List that receives each retry wait, or None to discard the waits.

    Returns:
        The governor.
    """
    recorded = sleeps if sleeps is not None else []  # The waits that the governor requested.
    return CallGovernor(  # A governor with fake time, fixed jitter, and no real sleep.
        session=session,
        request_budget=budget,  # Most requests of the run.
        call_timeout_seconds=30.0,  # Longest wait for one call.
        max_retries=retries,  # Retries for the retryable outcomes.
        requests_sent=sent,  # The login request is already counted.
        sleep=recorded.append,  # Record each wait instead of sleeping.
        clock=StepClock(),  # Each attempt takes half a second of fake time.
        jitter=lambda: 0.25,  # A fixed jitter keeps the waits exact.
    )


def make_client(  # Build a client for the approved host, with a governor from make_governor.
    session: Any, **options: Any
) -> ReadOnlyMistClient:
    """Build a client for the approved host with a governor from make_governor.

    Args:
        session: Session that the governor calls.
        **options: Options for make_governor.

    Returns:
        The client.
    """
    return ReadOnlyMistClient(HOST, make_governor(session, **options))  # One governor for the run.


@pytest.fixture
def default_structlog_chain() -> Iterator[None]:  # Isolate one test from the global chain.
    """Run one test under the default structlog chain, then restore the earlier chain.

    The chain holds the processors, the wrapper class, and the logger factory.

    Why: an earlier test in the full CI suite can configure structlog with the stdlib wrapper class.
    That wrapper class keeps the raw template in the event text, and the path in positional_args.
    So capture_logs records "GET %s started" and not the path. The default wrapper class formats the
    arguments into the event text before the processors run, so the test sees the path.

    Yields:
        None. The test body runs at this yield.
    """
    previous = structlog.get_config()  # Save the earlier chain, so the finally block can restore it.
    structlog.reset_defaults()  # Switch to the default chain, which formats the path into the event text.
    try:  # Restore the chain even when the test body fails.
        yield  # Run the test body on the default chain.
    finally:  # Run on every exit path, so the later tests keep their own chain.
        structlog.configure(**previous)  # Restore the saved processors, wrapper class, and logger factory.


def test_success_reply_gives_one_attempt_without_error() -> (  # Confirm that a 200 reply with records is one attempt.
    None
):
    """A 200 reply with records is one successful attempt."""
    session = FakeSession([json_reply(200, {"results": [{"id": "a"}]})])  # One scripted reply.
    attempts = make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert len(attempts) == 1  # A success needs no retry.
    assert attempts[0].error_class is None  # A valid reply has no error class.
    assert attempts[0].status_code == 200  # The status is kept.
    assert attempts[0].data == {"results": [{"id": "a"}]}  # The parsed body is kept.


def test_success_reply_with_zero_records_is_an_empty_success() -> None:  # Confirm a 200 reply without records succeeds.
    """A 200 reply with an empty results list is a success with zero records."""
    session = FakeSession([json_reply(200, {"results": []})])  # An empty page.
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=3)  # Read the pages, then check the stop.
    assert result.complete is True  # No next link, so the query is complete.
    assert result.record_count == 0  # Zero records is a success, not an error.
    assert result.stop_reason is None  # Nothing stopped the query.


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, ERROR.HTTP_ERROR),
        (401, ERROR.UNAUTHORIZED),
        (403, ERROR.HTTP_ERROR),
        (404, ERROR.HTTP_ERROR),
    ],
)
def test_client_error_statuses_map_to_their_class_without_retry(  # Confirm each 4xx status maps to a class, no retry.
    status: int, expected: ERROR
) -> None:
    """Each HTTP 4xx status gives its class, and the client never retries it.

    Args:
        status: HTTP status of the reply.
        expected: Error class that the status must give.
    """
    session = FakeSession([json_reply(status, {"detail": "rejected"})])  # One reply with an error body.
    attempts = make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert len(attempts) == 1  # A 4xx status is never retried.
    assert attempts[0].error_class == expected  # The status gives its class.
    assert attempts[0].status_code == status  # The status is kept for the checks.


def test_status_400_with_empty_list_is_an_error_and_not_an_empty_success() -> (  # Confirm a 400 empty list is an error.
    None
):
    """The SDK insufficiency case: a 400 with an empty list fails, and it is never a zero-record success."""
    session = FakeSession([json_reply(400, [])])  # A 400 whose body is an empty list.
    attempts = make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert attempts[0].error_class == ERROR.HTTP_ERROR  # The 400 status decides the class.
    assert attempts[0].status_code == 400  # The status is kept.


def test_error_text_keeps_at_most_200_characters_of_the_detail() -> (  # Confirm error text is cut at 200 characters.
    None
):
    """The evidence keeps at most 200 characters of an error detail."""
    long_detail = "x" * 300  # A detail longer than the limit.
    session = FakeSession([json_reply(400, {"detail": long_detail})])  # An error with a long detail.
    attempts = make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert len(attempts[0].error_text) == 200  # The text is cut at 200 characters.


def test_status_429_is_throttled_without_retry_and_keeps_integer_retry_after() -> (  # Confirm HTTP 429 is not retried.
    None
):
    """HTTP 429 is throttled, is not retried, and keeps an integer Retry-After value."""
    session = FakeSession([json_reply(429, {"detail": "slow"}, {"Retry-After": "30"})])  # One throttled reply.
    attempts = make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert len(attempts) == 1  # The SDK already retried; the client does not.
    assert attempts[0].error_class == ERROR.THROTTLED  # The status gives the throttled class.
    assert attempts[0].retry_after_seconds == (30,)  # The integer value is kept.
    assert attempts[0].header_names == ("retry-after",)  # The header name is kept in lower case.


def test_status_429_with_a_date_retry_after_records_not_numeric() -> None:  # Confirm a date Retry-After is not numeric.
    """A Retry-After value in another form is recorded as the text not numeric."""
    date_form = "Wed, 21 Oct 2015 07:28:00 GMT"  # An HTTP date, which is not integer seconds.
    session = FakeSession([json_reply(429, {}, {"Retry-After": date_form})])  # One throttled reply.
    attempts = make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert attempts[0].retry_after_seconds == ("not numeric",)  # The other form is not a number.


def test_server_error_then_success_retries_once_after_one_second_plus_jitter() -> (  # Confirm HTTP 500 is retried once.
    None
):
    """HTTP 500 is retried once after a 1 second wait plus the jitter of 0.25 second."""
    sleeps: list[float] = []  # Records the waits that the client requested.
    session = FakeSession([json_reply(500, {"detail": "fault"}), json_reply(200, {"results": []})])  # 500, then 200.
    attempts = make_client(session, sleeps=sleeps).get(PATH, IDENTIFIERS, {})  # Call the client, record each wait.
    assert [attempt.status_code for attempt in attempts] == [500, 200]  # Both attempts are kept in order.
    assert attempts[-1].error_class is None  # The second attempt succeeded.
    assert sleeps == [1.25]  # One wait of 1 second plus the 0.25 second jitter.


def test_three_server_errors_end_with_server_error_after_two_retries() -> (  # Confirm three 503s end as a server error.
    None
):
    """HTTP 503 three times ends with a server error after waits of 1 and 2 seconds."""
    sleeps: list[float] = []  # Records the waits.
    session = FakeSession([json_reply(503, {}), json_reply(503, {}), json_reply(503, {})])  # Three 503 replies.
    attempts = make_client(session, sleeps=sleeps).get(PATH, IDENTIFIERS, {})  # Call the client, record each wait.
    assert len(attempts) == 3  # Three attempts: one call and two retries, then the stop.
    assert attempts[-1].error_class == ERROR.SERVER_ERROR  # The final outcome is a server error.
    assert sleeps == [1.25, 2.25]  # The waits grow from 1 second to 2 seconds, each with jitter.


def test_connection_failure_is_retried_then_reports_connection_error() -> (  # Confirm connection failures give errors.
    None
):
    """A connection failure with no response is retried, then reports ConnectionError."""
    no_response = FakeResponse(None, {}, "")  # The SDK form of a connection failure.
    sleeps: list[float] = []  # Records the waits.
    session = FakeSession([no_response, no_response, no_response])  # Three failed connections.
    attempts = make_client(session, sleeps=sleeps).get(PATH, IDENTIFIERS, {})  # Call the client, record each wait.
    assert len(attempts) == 3  # Three attempts: one call and two retries, then the stop.
    assert attempts[-1].error_class == ERROR.CONNECTION_ERROR  # The final outcome is a connection error.
    assert attempts[-1].status_code is None  # No HTTP status exists.
    assert len(sleeps) == 2  # Two waits came before the last attempt.


def test_timeout_is_not_retried_and_is_counted_for_the_run() -> (  # Confirm a timeout is not retried and is counted.
    None
):
    """A timeout ends the attempt at once, and the run counts it."""
    session = BlockingSession()  # A call that never returns until the release.
    client = ReadOnlyMistClient(  # A client whose call never finishes during the test.
        HOST,
        CallGovernor(
            session=session,
            request_budget=60,
            call_timeout_seconds=30.0,
            max_retries=2,
            requests_sent=1,
            clock=StepClock(),
            wait_for_thread=lambda thread, seconds: None,  # Do not wait; the call is still running.
        ),
    )
    try:  # Release the worker in every case, so that no thread stays blocked.
        attempts = client.get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    finally:  # Always release the worker.
        session.release.set()  # Let the blocked worker finish.
    assert session.started.wait(timeout=5) is True  # The worker entered the call before the test reads the calls.
    assert len(attempts) == 1  # A timeout is never retried.
    assert attempts[0].error_class == ERROR.TIMEOUT  # The class is Timeout.
    assert client.timeouts == 1  # The run counts one timeout.


def test_second_timeout_in_one_run_is_counted_as_two() -> (  # Confirm that two timeouts in one run are counted as two.
    None
):
    """Two timeouts in one run give a count of two, which the command uses for the rate-limit stop."""
    session = BlockingSession()  # A call that never returns until the release.
    client = ReadOnlyMistClient(  # A client whose calls never finish during the test.
        HOST,
        CallGovernor(
            session=session,
            request_budget=60,
            call_timeout_seconds=30.0,
            max_retries=2,
            requests_sent=1,
            clock=StepClock(),
            wait_for_thread=lambda thread, seconds: None,  # Do not wait; each call is still running.
        ),
    )
    try:  # Release the workers in every case.
        client.get(PATH, IDENTIFIERS, {})  # The first timeout.
        client.get(PATH, IDENTIFIERS, {})  # The second timeout.
    finally:  # Always release the workers.
        session.release.set()  # Let the blocked workers finish.
    assert client.timeouts == 2  # Both timeouts are counted for the run.


def test_timeout_on_a_page_stops_the_query_with_the_timeout_reason() -> (  # Confirm a timed-out page stops the query.
    None
):
    """A timed-out page stops the query, and the stop reason is Timeout."""
    session = BlockingSession()  # The first page never returns until the release.
    client = ReadOnlyMistClient(  # A client whose first page never finishes during the test.
        HOST,
        CallGovernor(
            session=session,
            request_budget=60,
            call_timeout_seconds=30.0,
            max_retries=2,
            requests_sent=1,
            clock=StepClock(),
            wait_for_thread=lambda thread, seconds: None,  # Do not wait; the call is still running.
        ),
    )
    try:  # Release the worker in every case.
        result = client.get_pages(PATH, IDENTIFIERS, {}, max_pages=3)  # Read the pages, then check the stop.
    finally:  # Always release the worker.
        session.release.set()  # Let the blocked worker finish.
    assert result.stop_reason == "Timeout"  # The timeout is the stop reason.
    assert result.complete is False  # The query did not complete.


def test_malformed_json_from_the_sdk_is_an_error_and_never_zero_records() -> (  # Confirm malformed JSON is an error.
    None
):
    """A 200 body with invalid JSON is MalformedJson, and the SDK leaves its data empty."""
    reply = sdk_reply(200, b"{not json")  # The real SDK object for a body that is not JSON.
    attempts = make_client(FakeSession([reply])).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert attempts[0].error_class == ERROR.MALFORMED_JSON  # The body is malformed.
    assert attempts[0].data == {}  # The SDK keeps an empty object for the data.


def test_empty_body_from_the_sdk_is_an_empty_body_error() -> None:  # Confirm that an empty 200 body is an error.
    """A 200 body with no text is EmptyBody, and it is not a success."""
    reply = sdk_reply(200, b"")  # The real SDK object for an empty body.
    attempts = make_client(FakeSession([reply])).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert attempts[0].error_class == ERROR.EMPTY_BODY  # The body is empty.
    assert attempts[0].status_code == 200  # The status alone does not make it a success.


def test_sdk_connection_failure_without_a_response_is_connection_error() -> (  # No response gives a connection error.
    None
):
    """A real SDK object with no response gives status None and ConnectionError."""
    replies = [sdk_reply(None, None), sdk_reply(None, None), sdk_reply(None, None)]  # Three failed connections.
    attempts = make_client(FakeSession(replies), sleeps=[]).get(PATH, IDENTIFIERS, {})  # Call the client, count tries.
    assert attempts[-1].error_class == ERROR.CONNECTION_ERROR  # The final outcome is a connection error.
    assert attempts[-1].status_code is None  # No HTTP status exists.


def test_sdk_server_error_body_is_retried_then_reports_server_error() -> None:  # Confirm real SDK 500s are retried.
    """A real SDK 500 response is a ServerError, and the client retries it."""
    replies = [sdk_reply(500, b'{"detail": "fault"}') for _ in range(3)]  # Three 500 responses.
    attempts = make_client(FakeSession(replies), sleeps=[]).get(PATH, IDENTIFIERS, {})  # Call the client, count tries.
    assert len(attempts) == 3  # Three attempts: one call and two retries, then the stop.
    assert attempts[-1].error_class == ERROR.SERVER_ERROR  # The final outcome is a server error.


def test_sdk_throttled_response_keeps_the_integer_retry_after() -> (  # Confirm a real SDK 429 keeps its integer wait.
    None
):
    """A real SDK 429 response keeps the integer Retry-After value."""
    reply = sdk_reply(429, b'{"detail": "slow"}', {"Retry-After": "5"})  # A throttled response.
    attempts = make_client(FakeSession([reply])).get(PATH, IDENTIFIERS, {})  # Call the client, to list each try.
    assert attempts[0].error_class == ERROR.THROTTLED  # The status gives the throttled class.
    assert attempts[0].retry_after_seconds == (5,)  # The integer seconds are kept.


def test_sdk_400_with_empty_list_is_http_error_for_a_page() -> (  # Confirm a real SDK 400 empty list stops the query.
    None
):
    """A real SDK 400 with an empty list stops a query with HttpError, and it is never complete."""
    reply = sdk_reply(400, b"[]")  # The insufficiency case with the real SDK object.
    result = make_client(FakeSession([reply])).get_pages(PATH, IDENTIFIERS, {}, max_pages=3)  # Check the stop reason.
    assert result.stop_reason == ERROR.HTTP_ERROR  # The 400 status stops the query.
    assert result.complete is False  # Incomplete, so the caller never treats the list as full.


def test_three_page_chain_reads_every_page_and_completes() -> (  # Confirm that a chain of three pages is read in full.
    None
):
    """A chain of three pages reads each page, follows each safe link, and completes."""
    first = json_reply(  # Page 1 links to page 2.
        200, {"results": [{"id": "a"}]}, next_value="/api/v1/orgs/x/alarms/search?search_after=p2"
    )
    second = json_reply(  # Page 2, with a next link to page 3.
        200, {"results": [{"id": "b"}]}, next_value=f"https://{HOST}/api/v1/orgs/x/alarms/search?search_after=p3"
    )
    third = json_reply(200, {"results": [{"id": "c"}]})  # The last page has no next link.
    session = FakeSession([first, second, third])  # Three scripted pages.
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {"start": "1", "end": "2"}, max_pages=5)  # Read.
    assert result.complete is True  # The last page had no next link.
    assert result.pages_read == 3  # Three pages were requested.
    assert [record["id"] for record in result.records] == ["a", "b", "c"]  # Records of each page, in order.
    assert result.record_count == 3  # The count matches the records.
    assert result.next_form == FORM.NONE  # The last page had no next link.
    assert session.calls[1] == ("/api/v1/orgs/x/alarms/search", {"search_after": "p2", "limit": "1000"})  # Page 2.


@pytest.mark.parametrize(
    "bad_link",
    [
        "https://evil.example/api/v1/orgs/x/alarms/search?search_after=a",  # A foreign host.
        "https://api.mist.com:8443/api/v1/orgs/x/alarms/search?search_after=a",  # A port other than 443.
        "http://api.mist.com/api/v1/orgs/x/alarms/search?search_after=a",  # A scheme other than https.
        "https://user@api.mist.com/api/v1/orgs/x/alarms/search?search_after=a",  # User information in the link.
        "/api/v1/orgs/../self?search_after=a",  # A parent path segment.
        "/api/v1/%2e%2e/self?search_after=a",  # An encoded parent path segment.
        "/api/v1/orgs\\x/alarms?search_after=a",  # A backslash.
        "//evil.example/api/v1/x?search_after=a",  # A protocol-relative link.
        "/other/path?search_after=a",  # A path outside the API prefix.
        42,  # A value that is not a string.
    ],
)
def test_unsafe_next_link_stops_the_query_before_any_request(  # Confirm that each unsafe next link stops the query.
    bad_link: Any,
) -> None:
    """Each unsafe next link stops the query with ForeignOrigin, and no request uses it.

    Args:
        bad_link: Next link that fails the origin or the path rules.
    """
    session = FakeSession([json_reply(200, {"results": [{"id": "a"}]}, next_value=bad_link)])  # Unsafe next link.
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=3)  # Read the pages, then check the stop.
    assert result.stop_reason == STOP.FOREIGN_ORIGIN  # The unsafe link stops the query.
    assert result.next_form == FORM.REJECTED  # The link was rejected.
    assert result.complete is False  # Incomplete, so the caller never treats the list as full.
    assert len(session.calls) == 1  # No request used the unsafe link.


def test_port_443_on_the_approved_host_is_followed() -> None:  # Confirm that an https link with port 443 is followed.
    """An https link on the approved host with port 443 is followed."""
    link = "https://api.mist.com:443/api/v1/orgs/x/alarms/search?search_after=a"  # Explicit port 443.
    session = FakeSession(  # Two pages: the first links to the second, which completes the query.
        [json_reply(200, {"results": [{"id": "a"}]}, next_value=link), json_reply(200, {"results": []})]
    )
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=3)  # Read the pages, then check the stop.
    assert result.complete is True  # The second page completed the query.
    assert session.calls[1][0] == "/api/v1/orgs/x/alarms/search"  # Only the path of the link is requested.


def test_repeated_next_link_stops_before_the_repeated_request() -> (  # Confirm a repeated next link stops the query.
    None
):
    """A next link that repeats an earlier link stops the query before it is requested again."""
    link = f"/api/v1/orgs/{ORG_ID}/alarms/search?search_after=a"  # The same link on two pages.
    session = FakeSession(  # Two pages that repeat the same next link.
        [
            json_reply(200, {"results": [{"id": "a"}]}, next_value=link),
            json_reply(200, {"results": [{"id": "b"}]}, next_value=link),
        ]
    )
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=5)  # Read the pages, then check the stop.
    assert result.stop_reason == STOP.REPEATED_PAGE  # The repeated link ends the query.
    assert len(session.calls) == 2  # The repeated link was never requested.
    assert result.record_count == 2  # The records of the two pages were accepted.


def test_repeated_page_content_under_a_new_link_stops_without_keeping_the_page() -> None:  # Repeated page is not kept.
    """The same page content under a new link stops the query, and the repeat is not kept."""
    session = FakeSession(  # Two pages whose content repeats under new links.
        [
            json_reply(200, {"results": [{"id": "a", "x": 1}]}, next_value="/api/v1/x?search_after=a"),
            json_reply(200, {"results": [{"x": 1, "id": "a"}]}, next_value="/api/v1/x?search_after=b"),
        ]
    )  # The second page has the same content with another key order.
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=5)  # Read the pages, then check the stop.
    assert result.stop_reason == STOP.REPEATED_PAGE  # The repeated content ends the query.
    assert result.record_count == 1  # The repeated page was not kept.
    assert len(session.calls) == 2  # Two pages were requested.


def test_page_ceiling_with_a_next_link_stops_the_query_as_incomplete() -> (  # Confirm the page ceiling is incomplete.
    None
):
    """The page ceiling with a next link still present gives an incomplete query."""
    pages = [  # Three pages, each with a next link to the following page.
        json_reply(200, {"results": [{"id": str(index)}]}, next_value=f"/api/v1/x?search_after=p{index}")
        for index in range(3)
    ]  # Three pages, each with a next link.
    session = FakeSession(pages)  # The scripted pages.
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=2)  # Read at most two pages.
    assert result.stop_reason == STOP.PAGE_CEILING  # The page limit ended the query.
    assert result.complete is False  # A next link remained.
    assert result.pages_read == 2  # Two pages were requested.
    assert result.next_form == FORM.RELATIVE  # The pending link was a relative path.


def test_budget_counts_the_login_request_and_refuses_the_next_call() -> (  # Confirm the login uses one unit of budget.
    None
):
    """With a budget of three and one login request, two calls fit and the third is refused."""
    pages = [  # Three pages with distinct content, each with a next link.
        json_reply(200, {"results": [{"id": str(index)}]}, next_value=f"/api/v1/x?search_after=p{index}")
        for index in range(3)
    ]  # Three distinct pages, so that no page content repeats.
    session = FakeSession(pages)  # Enough replies for every page.
    client = make_client(session, budget=3, sent=1)  # The login request is already counted.
    result = client.get_pages(PATH, IDENTIFIERS, {}, max_pages=5)  # Read the pages, then check the stop.
    assert len(session.calls) == 2  # Two requests fit in the budget of three.
    assert result.stop_reason == ERROR.BUDGET_EXHAUSTED  # The third page is refused.
    assert client.requests_sent == 3  # The login and the two calls are counted.


def test_spent_budget_sends_nothing_and_reports_budget_exhausted() -> None:  # Confirm a spent budget sends no request.
    """A budget spent before the first call sends no request."""
    session = FakeSession([json_reply(200, {"results": []})])  # A reply that must never be used.
    client = make_client(session, budget=1, sent=1)  # Only the login request fits.
    attempts = client.get(PATH, IDENTIFIERS, {})  # Try to send the request.
    assert attempts[0].error_class == ERROR.BUDGET_EXHAUSTED  # The budget refusal is the class.
    assert session.calls == []  # Check the call list, so the guard proves no request left.
    assert client.requests_sent == 1  # The count did not grow.


def test_each_query_carries_limit_1000_unless_the_caller_sets_one() -> None:  # Confirm the default query limit is 1000.
    """Each request takes limit 1000, and a caller limit stays when the caller sets one."""
    session = FakeSession([json_reply(200, {"results": []}), json_reply(200, {"results": []})])  # Two pages.
    client = make_client(session)  # One client for both requests.
    client.get(PATH, IDENTIFIERS, {"start": "1"})  # No limit from the caller.
    client.get(PATH, IDENTIFIERS, {"limit": "5000"})  # A limit from the caller.
    assert session.calls[0][1]["limit"] == "1000"  # The default limit is 1000.
    assert session.calls[1][1]["limit"] == "5000"  # The caller limit is kept.


def test_next_page_keeps_the_limit_of_the_first_request() -> None:  # Confirm that a later page keeps the first limit.
    """A next link with another limit uses the limit of the first request."""
    first = json_reply(200, {"results": [{"id": "a"}]}, next_value="/api/v1/x?search_after=a&limit=2000")  # Link.
    session = FakeSession([first, json_reply(200, {"results": []})])  # Two pages.
    make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=2)  # Read two pages.
    assert session.calls[1][1]["limit"] == "1000"  # The server limit is replaced by the first limit.


def test_caller_query_dictionary_is_not_changed() -> None:  # Confirm that the caller query dictionary keeps its values.
    """The client copies the query, so the caller dictionary keeps its values."""
    query = {"start": "1"}  # The caller query.
    session = FakeSession([json_reply(200, {"results": []})])  # One scripted page, so the test sets every reply.
    make_client(session).get(PATH, IDENTIFIERS, query)  # Pass the query, then compare it with the copy.
    assert query == {"start": "1"}  # No limit was added to the caller dictionary.


def test_client_sends_only_get_and_never_calls_login() -> None:  # Confirm the client sends one GET and never logs in.
    """The client sends one GET call and never calls login."""
    session = FakeSession([json_reply(200, {"results": []})])  # One scripted page, so the test sets every reply.
    make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, to check that it sends one GET.
    assert len(session.calls) == 1  # Exactly one GET call was sent.
    assert session.login_calls == 0  # The client never logs in.


def test_get_rejects_a_path_outside_the_api_prefix() -> None:  # Confirm that a path outside the API prefix is refused.
    """A path template outside /api/v1/ is refused before any request."""
    session = FakeSession([])  # No reply is needed, because nothing is sent.
    with pytest.raises(ValueError, match="/api/v1/"):  # The prefix check raises at once.
        make_client(session).get("/other/{org_id}", IDENTIFIERS, {})  # Send an invalid template.
    assert session.calls == []  # Check the call list, so the guard proves no request left.


def test_get_pages_rejects_a_page_count_below_one() -> None:  # Confirm that a page count below one is refused.
    """A walk needs at least one page, so zero pages is refused before any request."""
    session = FakeSession([])  # No reply is needed.
    with pytest.raises(ValueError, match="max_pages"):  # The page count check raises at once.
        make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=0)  # Ask for zero pages.
    assert session.calls == []  # Check the call list, so the guard proves no request left.


def test_identifier_values_are_encoded_as_one_path_segment() -> (  # Confirm that path characters stay in one segment.
    None
):
    """A slash or a question mark in an identifier cannot change the path."""
    session = FakeSession([json_reply(200, {"results": []})])  # One scripted page, so the test sets every reply.
    make_client(session).get(PATH, {"org_id": "a/b?c"}, {})  # An identifier with path characters.
    assert session.calls[0][0] == "/api/v1/orgs/a%2Fb%3Fc/alarms/search"  # The characters are encoded.


def test_search_page_without_a_results_list_is_missing_results() -> (  # Confirm that a top-level array stops the query.
    None
):
    """A top-level array is not a search page, so the query stops with MissingResults."""
    session = FakeSession([json_reply(200, [])])  # A top-level array.
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=3)  # Read the pages, then check the stop.
    assert result.stop_reason == ERROR.MISSING_RESULTS  # The missing list stops the query.
    assert result.record_count == 0  # No records were accepted.
    assert result.complete is False  # Incomplete, so the caller never treats the list as full.


def test_unexpected_sdk_fault_reaches_the_caller() -> None:  # Confirm that an unexpected SDK fault reaches the caller.
    """A fault that the SDK call raises reaches the caller, so the run ends with an internal error."""
    session = FakeSession([RuntimeError("unexpected fault")])  # The SDK raises a fault.
    with pytest.raises(RuntimeError, match="unexpected fault"):  # The fault must not be swallowed.
        make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, so the SDK fault reaches the caller.


def test_log_events_show_the_path_template_and_never_the_identifier_or_the_body(  # Logs hold no identifiers.
    default_structlog_chain: None,  # Run the test on the default chain, not the earlier one.
) -> None:
    """The log holds the path template, and it holds no real identifier and no response body."""
    session = FakeSession([json_reply(200, {"results": [{"echo": "body-text-that-must-stay-private"}]})])  # One page.
    with capture_logs() as logs:  # Capture every event of the request.
        make_client(session).get(PATH, IDENTIFIERS, {})  # Call the client, so the log holds the path only.
    rendered = repr(logs)  # All keys and values of every event.
    assert ORG_ID not in rendered  # The organization identifier never reaches a log event.
    assert "body-text-that-must-stay-private" not in rendered  # The response body never reaches a log event.
    assert any(PATH in str(entry.get("event", "")) for entry in logs)  # The event text names the path template.


def test_requests_sent_and_timeouts_properties_read_the_run_budget() -> None:  # Confirm the request and timeout counts.
    """The client properties give the request count and the timeout count of the run."""
    session = FakeSession([json_reply(200, {"results": []})])  # One scripted page, so the test sets every reply.
    client = make_client(session, sent=1)  # The login request is already counted.
    client.get(PATH, IDENTIFIERS, {})  # One request.
    assert client.requests_sent == 2  # The login and the request are counted.
    assert client.timeouts == 0  # No timeout happened.


def test_elapsed_seconds_round_to_two_decimals() -> None:  # Confirm that the elapsed time is rounded to two decimals.
    """The elapsed time of an attempt is rounded to two decimals."""
    ticks = iter([0.0, 0.123456])  # The clock reads before and after the call.
    governor = CallGovernor(  # A governor with one reply and a clock that gives 0.123456 seconds.
        session=FakeSession([json_reply(200, {"results": []})]),
        request_budget=60,
        call_timeout_seconds=30.0,
        max_retries=0,
        requests_sent=1,
        clock=lambda: next(ticks),
    )
    attempts = ReadOnlyMistClient(HOST, governor).get(PATH, IDENTIFIERS, {})  # Time one attempt.
    assert attempts[0].elapsed_seconds == 0.12  # The elapsed time is 0.123456 rounded to 0.12.


def test_backoff_is_one_then_two_seconds_plus_the_jitter() -> (  # Confirm that backoff grows from one to two seconds.
    None
):
    """The backoff grows from 1 second to 2 seconds, and it adds the jitter."""
    governor = CallGovernor(  # A governor with no session and a jitter of exactly 0.5 second.
        session=None,
        request_budget=60,
        call_timeout_seconds=30.0,
        max_retries=2,
        jitter=lambda: 0.5,
    )
    assert governor.backoff_seconds(1) == 1.5  # The first retry waits 1 second plus 0.5 second.
    assert governor.backoff_seconds(2) == 2.5  # The second retry waits 2 seconds plus 0.5 second.


def test_default_jitter_stays_within_half_a_second() -> (  # Confirm that the default jitter stays within half a second.
    None
):
    """The default jitter is between 0 and 0.5 second, and it needs no real sleep."""
    governor = CallGovernor(  # A governor with the default jitter, which is never zero by design.
        session=None, request_budget=60, call_timeout_seconds=30.0, max_retries=0
    )
    samples = [governor.jitter() for _ in range(200)]  # Draw many values from the default source.
    assert all(0.0 <= sample <= 0.5 for sample in samples)  # Every value stays in the range.


def test_the_sdk_package_exposes_the_version_that_the_client_targets() -> (  # Confirm the SDK is the pinned 0.64 line.
    None
):
    """The SDK in the environment is the 0.64 line that the project pins."""
    assert str(mistapi.__version__).startswith("0.64.")  # The pinned SDK line.


def test_next_link_with_a_port_that_is_not_a_number_is_a_foreign_origin() -> None:  # Confirm a bad port is foreign.
    """A port that is not a number cannot match the approved origin, so the link is rejected."""
    bad_port_link = "https://api.mist.com:notaport/api/v1/orgs/x/alarms/search?search_after=a"  # Port is text.
    session = FakeSession([json_reply(200, {"results": [{"id": "a"}]}, next_value=bad_port_link)])  # Bad port in link.
    result = make_client(session).get_pages(PATH, IDENTIFIERS, {}, max_pages=3)  # Read the pages, then check the stop.
    assert result.stop_reason == STOP.FOREIGN_ORIGIN  # The link is rejected.
    assert len(session.calls) == 1  # No request used the link.


def test_get_pages_rejects_a_path_outside_the_api_prefix() -> None:  # Confirm that a paged read refuses a bad API path.
    """A path template outside /api/v1/ is refused by the paged read before any request."""
    session = FakeSession([])  # No reply is needed, because nothing is sent.
    with pytest.raises(ValueError, match="/api/v1/"):  # The prefix check raises at once.
        make_client(session).get_pages("/other/{org_id}", IDENTIFIERS, {}, max_pages=1)  # Invalid template.
    assert session.calls == []  # Check the call list, so the guard proves no request left.
