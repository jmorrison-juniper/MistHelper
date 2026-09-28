"""Prove the teardown rules of the multi-site browser journeys with no browser and no network.

Why:
    Issue #3518. Six browser modules start a multi-site operation on the
    stand-in sites. When a step failed before the cancel of the journey, the
    operation kept both sites, and a later journey could fail. The classes of
    `tests/support/upgrade_portal_e2e/org_operations.py` hold each decision of
    the repair. The fault shows only when a browser step fails, so these
    direct tests prove each decision with stand-in answers.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Build the body text of each stand-in answer, and read each sent body.
import logging  # Read the warning of the ledger.
from dataclasses import dataclass, field  # Describe each stand-in object.
from types import SimpleNamespace  # Give a stand-in route the request field of a Playwright route.
from typing import Any  # A recorded call holds values of mixed types.

import pytest  # Check each refusal and each warning.

from tests.support.upgrade_portal_e2e.org_operations import (  # The classes under test.
    OrgOperationCalls,
    OrgOperationLedger,
    OrgOperationRelease,
    OrgStartAnswer,
    OrgStartTap,
)

OPERATION_ID = "org-run-3518aa"  # An operation that one browser test started.
SECOND_OPERATION_ID = "org-run-3518bb"  # A second operation of the same test.
BASE_URL = "http://127.0.0.1:9601"  # The address of the test portal.
START_URL = f"{BASE_URL}/api/org-upgrades"  # The Start request of the confirmation form.
JOB_URL = f"{BASE_URL}/upgrade/org/jobs/{OPERATION_ID}"  # The progress page of the operation.
CONFIRM_URL = f"{BASE_URL}/upgrade/org/confirm"  # The confirmation page, which names no operation.
STATUS_PATH = f"/api/org-upgrades/{OPERATION_ID}"  # The status route of the operation.
CANCEL_PATH = f"/api/org-upgrades/{OPERATION_ID}/cancel"  # The cancel route of the operation.
SECOND_STATUS_PATH = f"/api/org-upgrades/{SECOND_OPERATION_ID}"  # The status route of the second operation.
SECOND_CANCEL_PATH = f"/api/org-upgrades/{SECOND_OPERATION_ID}/cancel"  # The cancel route of the second operation.
CSRF_TOKEN = "csrf-3518"  # The token for the cross-site request check.
MODULE_LOGGER = "tests.support.upgrade_portal_e2e.org_operations"  # The logger of the module under test.
READ_FAULT = "Target page, context or browser has been closed"  # The text of a read after the context closed.


@dataclass
class StandInAnswer:
    """Give one status and one body text, in the shape of a fetched Playwright answer."""

    status: int  # The status of the answer.
    body: str  # The body text of the answer.
    url: str = ""  # The address of the request.
    fault: Exception | None = None  # The fault that the body read raises, when the test closed the context first.

    @classmethod
    def of(cls, status: int, body: object, **fields: Any) -> StandInAnswer:
        """Build one answer, and write a body that is not text as JSON text."""
        text = body if isinstance(body, str) else json.dumps(body)  # The portal answers JSON text.
        return cls(status, text, **fields)  # One answer for one call.

    def text(self) -> str:
        """Return the body text, or raise the fault of a failed body read."""
        if self.fault is not None:  # The context closed before the read.
            raise self.fault  # Playwright raises its own error class here.
        return self.body  # Playwright gives the body through a method.


@dataclass
class ScriptedRequests:
    """Answer each call from a script, and record each call."""

    script: dict[tuple[str, str], list[StandInAnswer]]  # The answers for each method and path, in order.
    calls: list[dict[str, Any]] = field(default_factory=list)  # Each call that the class under test sent.

    def fetch(
        self, url_or_request: str, *, method: str, headers: dict[str, str], data: str | None, timeout: float
    ) -> StandInAnswer:
        """Record one call, and return the next scripted answer for its method and path."""
        call = {"method": method, "path": url_or_request, "headers": dict(headers), "data": data}  # One record.
        call["timeout"] = timeout  # The bound that the class under test chose.
        self.calls.append(call)  # The test reads the order of the calls later.
        return self.script[(method, url_or_request)].pop(0)  # A call with no script raises, and the test fails.

    def paths(self) -> list[tuple[str, str]]:
        """Return the method and the path of each call, in the order of the calls."""
        return [(str(call["method"]), str(call["path"])) for call in self.calls]  # The order proves each decision.


@dataclass
class StandInTokenPage:
    """Give the token of one portal page, and record each step on the page."""

    token: str  # The value of the token tag in the page head.
    steps: list[str] = field(default_factory=list)  # Each step, in the order of the steps.

    def goto(self, url: str, *, wait_until: str, timeout: float) -> None:
        """Record the page load."""
        self.steps.append(f"goto {url} {wait_until} {timeout}")  # The test compares the load and its bound.

    def evaluate(self, script: str) -> str:
        """Record the read, and return the token."""
        self.steps.append("evaluate" if "csrf-token" in script else f"evaluate {script}")  # The tag name counts.
        return self.token  # The script gives an empty text when the head holds no tag.

    def close(self) -> None:
        """Record the close."""
        self.steps.append("close")  # A page left open would hold a browser target.


@dataclass
class StandInContext:
    """Give the request source of a browser context, and open each token page."""

    request: ScriptedRequests  # The request source of the context.
    token: str = CSRF_TOKEN  # The token that each new page holds.
    pages: list[StandInTokenPage] = field(default_factory=list)  # Each page that the class under test opened.
    pauses: list[float] = field(default_factory=list)  # Each pause of the release, so no test waits for a clock.

    def new_page(self) -> StandInTokenPage:
        """Open one token page."""
        opened = StandInTokenPage(self.token)  # A new page of the same session.
        self.pages.append(opened)  # The test counts the pages later.
        return opened  # The class under test loads the page and reads the token.


@dataclass
class StandInPage:
    """Give the address and the context of the page of one browser test."""

    url: str  # The address that the page shows.
    context: StandInContext  # The browser context of the page.
    closed: bool = False  # True after the test closed the page.

    def is_closed(self) -> bool:
        """Report whether the test closed the page."""
        return self.closed  # A closed page shows no address.


@dataclass
class StandInRoute:
    """Give one intercepted request of the Start path, and record each step of the tap."""

    method: str  # The method of the intercepted request.
    outcome: StandInAnswer | Exception  # The answer that the fetch gives, or the fault that the fetch raises.
    page_fault: Exception | None = None  # The fault of the fulfill or the abort, when the page closed first.
    ledger: OrgOperationLedger | None = None  # The fulfill reads this ledger, so the test proves the order.
    steps: list[tuple[str, object]] = field(default_factory=list)  # Each step of the tap and its value.

    @property
    def request(self) -> SimpleNamespace:
        """Return the request of the route, which names the method and the address."""
        return SimpleNamespace(method=self.method, url=START_URL)  # Playwright gives both through the request.

    def fetch(self, *, max_redirects: int, timeout: float) -> StandInAnswer:
        """Record the options of the fetch, and give the answer or raise the fault."""
        self.steps.append(("fetch", (max_redirects, timeout)))  # The test compares the options.
        if isinstance(self.outcome, Exception):  # The portal stopped, or the context closed.
            raise self.outcome  # Playwright raises its own error class here.
        return self.outcome  # The real answer of the portal.

    def fulfill(self, *, response: StandInAnswer) -> None:
        """Record the answer that the page gets, and the ledger at that moment."""
        held = self.ledger.operations if self.ledger is not None else ()  # The ledger when the page gets the answer.
        self.steps.append(("fulfill", (response, held)))  # The test compares the answer and the order.
        if self.page_fault is not None:  # The page closed first.
            raise self.page_fault  # Playwright raises its own error class here.

    def abort(self) -> None:
        """Record the stop of the page request."""
        self.steps.append(("abort", None))  # The page script reports a failed request.
        if self.page_fault is not None:  # The page closed first.
            raise self.page_fault  # Playwright raises its own error class here.

    def fallback(self) -> None:
        """Record that the browser sends the request as usual."""
        self.steps.append(("fallback", None))  # The tap left the request alone.


def _status_answer(operation_id: str, state: str, cancel_allowed: object) -> StandInAnswer:
    """Return one 200 answer of the status route."""
    body = {"upgrade_id": operation_id, "status": state, "cancel_allowed": cancel_allowed}  # The fields of the route.
    return StandInAnswer.of(200, body)  # The owner of the operation gets 200.


def _live(operation_id: str = OPERATION_ID) -> StandInAnswer:
    """Return the status answer of a running operation."""
    return _status_answer(operation_id, "running", True)  # The operator can still cancel.


def _ended(operation_id: str = OPERATION_ID) -> StandInAnswer:
    """Return the status answer of a cancelled operation."""
    return _status_answer(operation_id, "cancelled", False)  # A final operation accepts no cancel.


def _start_answer(status: int, body: object, fault: Exception | None = None) -> StandInAnswer:
    """Return one answer of the Start request."""
    return StandInAnswer.of(status, body, url=START_URL, fault=fault)  # The tap fetches the Start route only.


def _release(script: dict[tuple[str, str], list[StandInAnswer]]) -> tuple[OrgOperationRelease, StandInContext]:
    """Build one release on a scripted context, and give back the context."""
    context = StandInContext(ScriptedRequests(script))  # The context records each call.
    release = OrgOperationRelease(OrgOperationCalls(context), pause=context.pauses.append)  # The class under test.
    return release, context  # The test reads the calls and the pauses.


class TestTheStartAnswer:
    """The start rules find each operation that a Start request built."""

    @pytest.mark.parametrize(
        ("method", "url", "status", "expected"),
        [
            ("POST", START_URL, 200, True),  # The Start request that built an operation.
            ("POST", f"{START_URL}?source=form", 200, True),  # A query does not change the route.
            ("GET", START_URL, 200, False),  # A read builds nothing.
            ("POST", START_URL, 409, False),  # A second tab gets a refusal, so nothing starts.
            ("POST", START_URL, 503, False),  # A retryable refusal starts nothing.
            ("POST", f"{BASE_URL}/api/org-upgrades/options", 200, False),  # The Review request builds no operation.
            ("POST", f"{BASE_URL}{CANCEL_PATH}", 200, False),  # A cancel ends an operation.
        ],
    )
    def test_only_a_200_answer_to_the_start_request_counts(
        self, method: str, url: str, status: int, expected: bool
    ) -> None:
        """Only a 200 answer to `POST /api/org-upgrades` names a new operation."""
        assert OrgStartAnswer.is_start(method, url, status) is expected  # One decision for each answer.

    def test_the_id_comes_from_the_field_next(self) -> None:
        """The field `next` names the progress page, and the page names the operation."""
        text = json.dumps({"next": f"/upgrade/org/jobs/{OPERATION_ID}"})  # The body of the Start answer.
        assert OrgStartAnswer.operation_id(text) == OPERATION_ID  # The id of the new operation.

    @pytest.mark.parametrize(
        "text",
        [
            "",  # An empty body.
            "<html>proxy</html>",  # A body that is not JSON.
            "[]",  # JSON that is not an object.
            json.dumps({}),  # No field `next`.
            json.dumps({"next": 5}),  # A field that is not text.
            json.dumps({"next": "/upgrade/org/confirm"}),  # A page that is not a progress page.
            json.dumps({"next": f"/upgrade/org/jobs/{OPERATION_ID}/extra"}),  # A longer path.
            json.dumps({"next": "/upgrade/org/jobs/0f2c9a"}),  # An id that is not an aggregate operation.
        ],
    )
    def test_a_body_that_names_no_progress_page_gives_no_id(self, text: str) -> None:
        """A body that names no progress page gives no id, and it raises nothing."""
        assert OrgStartAnswer.operation_id(text) is None  # The ledger then records nothing.

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (JOB_URL, OPERATION_ID),  # The progress page names the operation.
            (f"{JOB_URL}?tab=children", OPERATION_ID),  # A query does not change the operation.
            (CONFIRM_URL, None),  # The confirmation page names no operation.
            ("about:blank", None),  # A new page names no operation.
        ],
    )
    def test_the_address_of_a_progress_page_names_the_operation(self, url: str, expected: str | None) -> None:
        """Only the address of a progress page names an operation."""
        assert OrgStartAnswer.page_operation(url) == expected  # One decision for each address.


class TestTheOperationLedger:
    """The ledger holds each operation that one browser test started."""

    def test_the_ledger_keeps_each_operation_one_time_in_the_order_of_the_start(self) -> None:
        """An operation that the ledger meets two times gets one entry, and the order stays."""
        ledger = OrgOperationLedger()  # A new ledger for one test.
        ledger.record(OPERATION_ID)  # The first start.
        ledger.record(SECOND_OPERATION_ID)  # The second start.
        ledger.record(OPERATION_ID)  # The page source finds the first operation again.
        assert ledger.operations == (OPERATION_ID, SECOND_OPERATION_ID)  # One entry for each operation.

    @pytest.mark.parametrize("operation_id", ["", "   "])
    def test_the_ledger_refuses_an_empty_id(self, operation_id: str) -> None:
        """An empty id names no operation, so the ledger refuses it."""
        with pytest.raises(ValueError, match="needs the id of an operation"):  # A caller fault stops the test.
            OrgOperationLedger().record(operation_id)  # The record must fail.

    def test_the_ledger_records_the_operation_of_a_start_answer(self) -> None:
        """The ledger records the id from the 200 answer of the Start request (FR-001)."""
        ledger = OrgOperationLedger()  # A new ledger for one test.
        ledger.observe("POST", _start_answer(200, {"next": f"/upgrade/org/jobs/{OPERATION_ID}"}))  # The answer.
        assert ledger.operations == (OPERATION_ID,)  # The teardown can end the operation.

    @pytest.mark.parametrize(
        ("method", "status"),
        [
            ("GET", 200),  # A read of the path builds nothing.
            ("POST", 409),  # A second tab gets a refusal, so nothing starts.
            ("POST", 503),  # A retryable refusal starts nothing.
        ],
    )
    def test_the_ledger_reads_no_body_of_another_answer(self, method: str, status: int) -> None:
        """The ledger returns before the body read for each answer that built no operation."""
        ledger = OrgOperationLedger()  # A new ledger for one test.
        refusal = _start_answer(status, "", fault=RuntimeError(READ_FAULT))  # A body read would raise the fault.
        ledger.observe(method, refusal)  # The ledger must not read the body.
        assert ledger.operations == ()  # A refusal names no new operation.

    def test_a_body_read_fault_logs_a_warning_and_records_nothing(self, caplog: pytest.LogCaptureFixture) -> None:
        """A fault of the body read stays inside the ledger (FR-006)."""
        caplog.set_level(logging.WARNING, logger=MODULE_LOGGER)  # Keep the warning of the ledger.
        ledger = OrgOperationLedger()  # A new ledger for one test.
        ledger.observe("POST", _start_answer(200, "", fault=RuntimeError(READ_FAULT)))  # The context closed.
        assert ledger.operations == ()  # The ledger records nothing.
        warnings = [record for record in caplog.records if record.levelno == logging.WARNING]  # The warnings only.
        assert len(warnings) == 1  # One warning tells the reader that the ledger missed a start.
        assert "RuntimeError" in warnings[0].getMessage()  # The warning names the class of the fault.

    @pytest.mark.parametrize("raw", [b"", b'{"next": "/upgrade/org/jobs/'])
    def test_an_empty_or_cut_start_body_logs_a_warning_and_records_nothing(
        self, raw: bytes, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A 200 Start answer with an empty body or a cut body names no operation, and it raises nothing (FR-006)."""
        caplog.set_level(logging.WARNING, logger=MODULE_LOGGER)  # Keep the warning of the ledger.
        ledger = OrgOperationLedger()  # A new ledger for one test.
        ledger.observe("POST", _start_answer(200, raw.decode("ascii")))  # Playwright gives the body as text.
        assert ledger.operations == ()  # The page source of FR-002 must find the operation instead.
        assert [record.levelno for record in caplog.records] == [logging.WARNING]  # One warning for the reader.

    def test_a_start_answer_that_names_no_progress_page_logs_a_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """A 200 answer with a body that names no operation leaves the ledger empty."""
        caplog.set_level(logging.WARNING, logger=MODULE_LOGGER)  # Keep the warning of the ledger.
        ledger = OrgOperationLedger()  # A new ledger for one test.
        ledger.observe("POST", _start_answer(200, {"next": "/upgrade/org/jobs/0f2c9a"}))  # An id of another kind.
        assert ledger.operations == ()  # The ledger records nothing.
        assert [record.levelno for record in caplog.records] == [logging.WARNING]  # One warning.

    def test_the_page_source_records_a_progress_page_only(self) -> None:
        """The address of a progress page adds its operation, and another page adds nothing (FR-002)."""
        ledger = OrgOperationLedger()  # A new ledger for one test.
        assert ledger.record_page(CONFIRM_URL) is None  # The confirmation page names no operation.
        assert ledger.record_page(JOB_URL) == OPERATION_ID  # The progress page names the operation.
        assert ledger.operations == (OPERATION_ID,)  # One entry.


class TestTheStartTap:
    """The tap reads each Start answer before the page gets it."""

    def test_a_read_of_the_path_goes_to_the_browser(self) -> None:
        """A read of the Start path goes to the browser, and the tap fetches nothing."""
        ledger = OrgOperationLedger()  # A new ledger for one test.
        route = StandInRoute("GET", _start_answer(200, {"next": f"/upgrade/org/jobs/{OPERATION_ID}"}))  # A read.
        OrgStartTap(ledger).pass_start(route)  # The class under test.
        assert route.steps == [("fallback", None)]  # No fetch, no fulfill.
        assert ledger.operations == ()  # A read names no operation.

    def test_the_ledger_holds_the_operation_before_the_page_gets_the_answer(self) -> None:
        """The tap records the operation first, and the page then gets the same answer (FR-001)."""
        ledger = OrgOperationLedger()  # A new ledger for one test.
        answer = _start_answer(200, {"next": f"/upgrade/org/jobs/{OPERATION_ID}"})  # The real Start answer.
        route = StandInRoute("POST", answer, ledger=ledger)  # The fulfill reads the ledger.
        OrgStartTap(ledger).pass_start(route)  # The class under test.
        options = (OrgStartTap.NO_REDIRECT, OrgStartTap.FETCH_TIMEOUT_MS)  # The page follows a redirect itself.
        assert route.steps == [("fetch", options), ("fulfill", (answer, (OPERATION_ID,)))]  # Record, then give.

    def test_a_refusal_goes_to_the_page_and_records_nothing(self) -> None:
        """The page gets a refusal unchanged, and the ledger stays empty."""
        ledger = OrgOperationLedger()  # A new ledger for one test.
        refusal = _start_answer(409, {"error": {"code": "ORG_UPGRADE_REPLAYED"}})  # A second tab gets a refusal.
        route = StandInRoute("POST", refusal, ledger=ledger)  # The fulfill reads the ledger.
        OrgStartTap(ledger).pass_start(route)  # The class under test.
        assert route.steps[-1] == ("fulfill", (refusal, ()))  # The page shows the refusal.

    @pytest.mark.parametrize("page_fault", [None, RuntimeError(READ_FAULT)])
    def test_a_fetch_fault_stops_the_page_request_and_raises_nothing(
        self, page_fault: Exception | None, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed fetch stops the page request, so no second request can start a second operation (FR-006)."""
        caplog.set_level(logging.WARNING, logger=MODULE_LOGGER)  # Keep the warnings of the tap.
        ledger = OrgOperationLedger()  # A new ledger for one test.
        route = StandInRoute("POST", TimeoutError("Timeout 60000ms exceeded."), page_fault=page_fault)  # No answer.
        OrgStartTap(ledger).pass_start(route)  # No fault may escape the route handler.
        assert [step for step, _ in route.steps] == ["fetch", "abort"]  # No second request.
        assert ledger.operations == ()  # The tap has no answer to read.
        assert "TimeoutError" in caplog.records[0].getMessage()  # The warning names the class of the fault.
        assert len(caplog.records) == (1 if page_fault is None else 2)  # A closed page adds one warning.

    def test_a_closed_page_keeps_the_operation_in_the_ledger(self, caplog: pytest.LogCaptureFixture) -> None:
        """A fulfill fault raises nothing, and the teardown can still end the operation."""
        caplog.set_level(logging.WARNING, logger=MODULE_LOGGER)  # Keep the warning of the tap.
        ledger = OrgOperationLedger()  # A new ledger for one test.
        answer = _start_answer(200, {"next": f"/upgrade/org/jobs/{OPERATION_ID}"})  # The portal started it.
        route = StandInRoute("POST", answer, page_fault=RuntimeError(READ_FAULT))  # The page closed first.
        OrgStartTap(ledger).pass_start(route)  # No fault may escape the route handler.
        assert ledger.operations == (OPERATION_ID,)  # The teardown ends the operation.
        assert [record.levelno for record in caplog.records] == [logging.WARNING]  # One warning.


class TestTheOperationCalls:
    """The calls reach the status route and the cancel route of the portal."""

    def test_a_status_read_sends_no_token_and_asks_for_json(self) -> None:
        """A read needs no token, so it opens no page."""
        context = StandInContext(ScriptedRequests({("get", STATUS_PATH): [_live()]}))  # One status read.
        body = OrgOperationCalls(context).read_status(OPERATION_ID)  # The class under test.
        assert body["cancel_allowed"] is True  # The fields of the answer.
        assert context.request.calls[0]["headers"] == {"Accept": "application/json"}  # A JSON read only.
        assert context.request.calls[0]["data"] is None  # A read sends no body.
        assert context.pages == []  # No page load for a read.

    def test_a_cancel_sends_the_word_and_the_token_of_the_history_page(self) -> None:
        """A cancel reads the token from a new page, and it sends the typed word."""
        cancelled = _ended()  # The cancel route answers the summary of the operation.
        context = StandInContext(ScriptedRequests({("post", CANCEL_PATH): [cancelled]}))  # One cancel.
        answer = OrgOperationCalls(context).cancel(OPERATION_ID)  # The class under test.
        assert answer.status == 200  # The caller reads the status.
        sent = context.request.calls[0]  # The one call.
        assert json.loads(str(sent["data"])) == {"confirmation": "CANCEL"}  # The typed word of the route.
        assert sent["headers"]["X-CSRFToken"] == CSRF_TOKEN  # The cross-site request check.
        assert sent["headers"]["Accept"] == "application/json"  # A JSON answer, not a redirect.
        assert sent["headers"]["Content-Type"] == "application/json"  # The route reads a JSON body.
        assert context.pages[0].steps == ["goto /history domcontentloaded 30000.0", "evaluate", "close"]  # One load.

    def test_the_token_is_read_one_time(self) -> None:
        """Two cancels open one page."""
        answers = {("post", CANCEL_PATH): [_ended()], ("post", SECOND_CANCEL_PATH): [_ended(SECOND_OPERATION_ID)]}
        context = StandInContext(ScriptedRequests(answers))  # Two cancels.
        calls = OrgOperationCalls(context)  # One set of calls for one teardown.
        calls.cancel(OPERATION_ID)  # The first cancel reads the token.
        calls.cancel(SECOND_OPERATION_ID)  # The second cancel keeps the token.
        assert len(context.pages) == 1  # One page load for the teardown.

    def test_a_page_with_no_token_fails_the_cancel(self) -> None:
        """A page with no token tag stops the teardown before the cancel."""
        context = StandInContext(ScriptedRequests({}), token="")  # The head holds no token tag.
        with pytest.raises(AssertionError, match=r"issue #3518.*no CSRF token"):  # The message names the issue.
            OrgOperationCalls(context).cancel(OPERATION_ID)  # The cancel must fail.
        assert context.request.calls == []  # No cancel went out with no token.
        assert context.pages[0].steps[-1] == "close"  # The page closes also after the fault.

    def test_a_refused_status_read_fails_with_the_call_and_the_body(self) -> None:
        """A refused read names the issue, the call, the status, and the body (FR-004)."""
        refusal = StandInAnswer.of(503, {"error": {"code": "STATUS_FAILED"}})  # The route refused the read.
        context = StandInContext(ScriptedRequests({("get", STATUS_PATH): [refusal]}))  # One refused read.
        with pytest.raises(AssertionError, match=rf"issue #3518.*GET {STATUS_PATH}.*503.*STATUS_FAILED"):
            OrgOperationCalls(context).read_status(OPERATION_ID)  # The read must fail.

    @pytest.mark.parametrize("raw", [b"", b" \r\n "])
    def test_an_empty_status_body_fails_and_names_the_call(self, raw: bytes) -> None:
        """A 200 read with an empty body names no state, so the read fails (FR-004)."""
        empty = StandInAnswer.of(200, raw.decode("ascii"))  # Playwright gives the body as text.
        context = StandInContext(ScriptedRequests({("get", STATUS_PATH): [empty]}))  # One read.
        with pytest.raises(AssertionError, match=rf"GET {STATUS_PATH} answered 200 with an empty body"):
            OrgOperationCalls(context).read_status(OPERATION_ID)  # The read must fail.

    @pytest.mark.parametrize("text", ["<html>proxy</html>", '{"upgrade_id": "org-run-3518aa", "status": '])
    def test_a_status_body_that_is_not_json_fails_and_keeps_the_parser_error(self, text: str) -> None:
        """A 200 read with a proxy page or a cut body fails, and the parser error stays the cause (FR-004)."""
        page = StandInAnswer.of(200, text)  # A proxy page, or a body that the connection cut short.
        context = StandInContext(ScriptedRequests({("get", STATUS_PATH): [page]}))  # One read.
        with pytest.raises(AssertionError, match="not JSON") as failure:  # The message names the fault.
            OrgOperationCalls(context).read_status(OPERATION_ID)  # The read must fail.
        assert isinstance(failure.value.__cause__, json.JSONDecodeError)  # The report keeps the parser position.

    def test_a_cancel_answer_of_409_goes_back_to_the_caller(self) -> None:
        """A 409 can come from a race, so the caller decides (FR-005)."""
        conflict = StandInAnswer.of(409, {"error": {"code": "NOT_CANCELLABLE"}})  # The operation ended first.
        context = StandInContext(ScriptedRequests({("post", CANCEL_PATH): [conflict]}))  # One cancel.
        answer = OrgOperationCalls(context).cancel(OPERATION_ID)  # The class under test.
        assert answer.status == 409  # The caller reads the status again.

    def test_a_refused_cancel_fails(self) -> None:
        """A cancel that answers another refusal fails the teardown (FR-004)."""
        refusal = StandInAnswer.of(503, {"error": {"code": "CANCEL_FAILED"}})  # The outcome is unknown.
        context = StandInContext(ScriptedRequests({("post", CANCEL_PATH): [refusal]}))  # One cancel.
        with pytest.raises(AssertionError, match=rf"issue #3518.*POST {CANCEL_PATH}.*503.*CANCEL_FAILED"):
            OrgOperationCalls(context).cancel(OPERATION_ID)  # The cancel must fail.

    def test_a_cancel_answer_of_200_must_hold_a_json_object(self) -> None:
        """A 200 cancel with a proxy page fails the teardown, and the parser error stays the cause (FR-004)."""
        page = StandInAnswer.of(200, "<html>proxy</html>")  # A proxy page.
        context = StandInContext(ScriptedRequests({("post", CANCEL_PATH): [page]}))  # One cancel.
        with pytest.raises(AssertionError, match="not JSON") as failure:  # The message names the fault.
            OrgOperationCalls(context).cancel(OPERATION_ID)  # The cancel must fail.
        assert isinstance(failure.value.__cause__, json.JSONDecodeError)  # The report keeps the parser position.

    def test_an_empty_cancel_answer_of_200_fails(self) -> None:
        """A 200 cancel with an empty body names no state, so the teardown fails (FR-004)."""
        empty = StandInAnswer.of(200, "")  # The connection closed before the body.
        context = StandInContext(ScriptedRequests({("post", CANCEL_PATH): [empty]}))  # One cancel.
        with pytest.raises(AssertionError, match=rf"POST {CANCEL_PATH} answered 200 with an empty body"):
            OrgOperationCalls(context).cancel(OPERATION_ID)  # The cancel must fail.


class TestTheOperationRelease:
    """The release ends each live operation, and it waits for the final state."""

    def test_a_final_operation_gets_no_cancel(self) -> None:
        """An operation that the test cancelled on the page needs one read only (SC-004)."""
        release, context = _release({("get", STATUS_PATH): [_ended()]})  # The operation already ended.
        assert release.end_operations([OPERATION_ID]) == 0  # No cancel.
        assert context.request.paths() == [("get", STATUS_PATH)]  # One read.
        assert context.pauses == []  # No wait.

    def test_a_live_operation_gets_one_cancel_and_the_reads_until_final(self) -> None:
        """A live operation gets one cancel, and the reads stop at the final state (FR-003)."""
        reads = [_live(), _live(), _ended()]  # Live, live after the cancel, and then final.
        release, context = _release({("get", STATUS_PATH): reads, ("post", CANCEL_PATH): [_ended()]})
        assert release.end_operations([OPERATION_ID]) == 1  # One cancel.
        expected = [("get", STATUS_PATH), ("post", CANCEL_PATH), ("get", STATUS_PATH), ("get", STATUS_PATH)]
        assert context.request.paths() == expected  # The read, the cancel, and two reads.
        assert context.pauses == [0.5]  # One pause between two reads.

    def test_a_409_after_the_operation_ended_is_a_race(self) -> None:
        """The operation ended between the read and the cancel, so the teardown passes (FR-005)."""
        conflict = StandInAnswer.of(409, {"error": {"code": "NOT_CANCELLABLE"}})  # The operation ended first.
        release, context = _release({("get", STATUS_PATH): [_live(), _ended()], ("post", CANCEL_PATH): [conflict]})
        assert release.end_operations([OPERATION_ID]) == 0  # No cancel counted.
        assert context.request.paths()[-1] == ("get", STATUS_PATH)  # One read after the 409.

    def test_a_409_while_the_operation_stays_live_fails(self) -> None:
        """A 409 for a live operation is a real fault, and the message holds the body (FR-004)."""
        conflict = StandInAnswer.of(409, {"error": {"code": "CANCEL_FAILED"}})  # A damaged state.
        release, _context = _release({("get", STATUS_PATH): [_live(), _live()], ("post", CANCEL_PATH): [conflict]})
        with pytest.raises(AssertionError, match=r"issue #3518.*409.*'running'.*CANCEL_FAILED"):
            release.end_operations([OPERATION_ID])  # The teardown must fail.

    def test_an_operation_that_stays_live_fails_after_the_bound(self) -> None:
        """The reads stop at the bound, and the message names the state (FR-004)."""
        reads = [_live() for _ in range(OrgOperationRelease.READ_TRIES + 1)]  # The operation never ends.
        release, context = _release({("get", STATUS_PATH): reads, ("post", CANCEL_PATH): [_ended()]})
        with pytest.raises(AssertionError, match=rf"issue #3518.*{OPERATION_ID}.*'running'.*30 status reads"):
            release.end_operations([OPERATION_ID])  # The teardown must fail.
        assert len(context.pauses) == OrgOperationRelease.READ_TRIES  # One pause after each live read.

    @pytest.mark.parametrize("flag", [None, "true", 1])
    def test_a_status_answer_with_no_boolean_flag_fails(self, flag: object) -> None:
        """A missing flag or a flag that is not a boolean cannot pass as a final state."""
        release, _context = _release({("get", STATUS_PATH): [_status_answer(OPERATION_ID, "running", flag)]})
        with pytest.raises(AssertionError, match=r"issue #3518.*cancel_allowed"):  # The message names the field.
            release.end_operations([OPERATION_ID])  # The teardown must fail.

    def test_a_fault_of_one_operation_does_not_stop_the_next_operation(self) -> None:
        """The release tries each operation, and then it reports each fault."""
        refusal = StandInAnswer.of(503, {"error": {"code": "STATUS_FAILED"}})  # The first read fails.
        script = {
            ("get", STATUS_PATH): [refusal],
            ("get", SECOND_STATUS_PATH): [_live(SECOND_OPERATION_ID), _ended(SECOND_OPERATION_ID)],
            ("post", SECOND_CANCEL_PATH): [_ended(SECOND_OPERATION_ID)],
        }  # The second operation is live, and it ends after its cancel.
        release, context = _release(script)  # The release records each call.
        with pytest.raises(AssertionError, match=rf"GET {STATUS_PATH}.*503"):  # The first fault stays visible.
            release.end_operations([OPERATION_ID, SECOND_OPERATION_ID])  # The teardown must fail.
        assert ("post", SECOND_CANCEL_PATH) in context.request.paths()  # The second operation got its cancel.


class TestTheReleaseForAPage:
    """The fixture calls one method that finds and ends each operation of the test."""

    def test_an_empty_ledger_sends_no_call(self) -> None:
        """A test that started no operation gets no call (FR-009)."""
        context = StandInContext(ScriptedRequests({}))  # A call with no script would fail the test.
        page = StandInPage(CONFIRM_URL, context)  # The page names no operation.
        assert OrgOperationRelease.end_for(page, OrgOperationLedger()) == 0  # No cancel.
        assert context.request.calls == []  # No call.
        assert context.pages == []  # No page load.

    def test_the_teardown_records_the_progress_page_and_reads_its_operation(self) -> None:
        """The page source finds the operation of the progress page (FR-002)."""
        context = StandInContext(ScriptedRequests({("get", STATUS_PATH): [_ended()]}))  # The operation ended.
        ledger = OrgOperationLedger()  # The handler missed the start.
        assert OrgOperationRelease.end_for(StandInPage(JOB_URL, context), ledger) == 0  # No cancel.
        assert ledger.operations == (OPERATION_ID,)  # The page source added the operation.
        assert context.request.paths() == [("get", STATUS_PATH)]  # One read.

    def test_a_closed_page_adds_no_operation(self) -> None:
        """A closed page shows no progress page, so the page source adds nothing."""
        context = StandInContext(ScriptedRequests({}))  # A call with no script would fail the test.
        ledger = OrgOperationLedger()  # The ledger holds no operation.
        assert OrgOperationRelease.end_for(StandInPage(JOB_URL, context, closed=True), ledger) == 0  # No cancel.
        assert ledger.operations == ()  # The closed page added nothing.

    def test_each_recorded_operation_is_ended_in_the_order_of_the_start(self) -> None:
        """Two live operations get two cancels, in the order of the start."""
        script = {
            ("get", STATUS_PATH): [_live(), _ended()],
            ("post", CANCEL_PATH): [_ended()],
            ("get", SECOND_STATUS_PATH): [_live(SECOND_OPERATION_ID), _ended(SECOND_OPERATION_ID)],
            ("post", SECOND_CANCEL_PATH): [_ended(SECOND_OPERATION_ID)],
        }  # Each operation is live once, and final after its cancel.
        context = StandInContext(ScriptedRequests(script))  # The context records each call.
        ledger = OrgOperationLedger()  # The ledger of the test.
        ledger.record(OPERATION_ID)  # The first start.
        ledger.record(SECOND_OPERATION_ID)  # The second start.
        assert OrgOperationRelease.end_for(StandInPage(CONFIRM_URL, context), ledger) == 2  # Two cancels.
        posts = [path for method, path in context.request.paths() if method == "post"]  # The cancels only.
        assert posts == [CANCEL_PATH, SECOND_CANCEL_PATH]  # The order of the start.
