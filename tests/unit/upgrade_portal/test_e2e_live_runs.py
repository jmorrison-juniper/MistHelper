"""Prove the live-run check of the browser run with no browser and no network.

Why:
    Issue #3511. The walk of `test_capture.py` built a run on the first site of
    the picker, and no teardown ended it. Each later create call at that site
    answered 409, and two tests used the leftover run in place of their own
    run. No check saw the leftover run, so each test passed.

    The classes of `tests/support/upgrade_portal_e2e/live_runs.py` hold each
    decision of the new module check. These direct tests prove that each
    decision can fail. The live rule must agree with the portal helper
    `run_is_live`. The reader must read each page and stop at a bound. Each
    answer that the reader cannot read must fail. A new live run must fail the
    module.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import io  # Give a refused answer a body, as the real error object holds.
import json  # Build the body text of each stand-in answer.
from collections.abc import Callable  # The type of the stand-in clock.
from dataclasses import dataclass, field  # Describe the stand-in answer and the stand-in opener.
from email.message import Message  # The header type of a refused answer.
from typing import Any  # A recorded request holds values of mixed types.
from urllib.error import HTTPError, URLError  # The two failures of a real opener.

import pytest  # Check each refusal.

from src.upgrade_portal.app.routes.upgrade import run_is_live  # The live rule of the create refusal.
from src.upgrade_portal.runtime.runs import RunState, RunStateMachine  # The states of the run model.
from tests.support.upgrade_portal_e2e.live_runs import (  # The classes under test.
    LiveRun,
    LiveRunCheck,
    SiteRunReader,
    SiteRunScan,
)

BASE_URL = "http://127.0.0.1:9601"  # A loopback address of a test portal.
COOKIE_HEADER = "session=signed-3511; browser_id=browser-3511"  # The two cookies of one operator.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first site of the picker.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second site of the picker.
MODULE = "tests/e2e/upgrade_portal/test_capture.py"  # The browser module that one check follows.
FIRST_PAGE_PATH = f"/api/sites/{SITE_ID}/runs/history?limit=200&offset=0"  # The first read of the first site.
FIRST_PAGE_CALL = f"GET {FIRST_PAGE_PATH}"  # The first read, as each message names it.
LIVE = LiveRun(SITE_ID, "run-live-3511", "created")  # A run that a module left live.


@dataclass
class StandInReply:
    """Give one status and one body, in the shape of an answer of `urllib`."""

    status: int  # The status of the answer.
    text: str  # The body text of the answer.

    @classmethod
    def of(cls, body: object, status: int = 200) -> StandInReply:
        """Build one answer, and write a body that is not text as JSON text."""
        text = body if isinstance(body, str) else json.dumps(body)  # The portal answers JSON text.
        return cls(status, text)  # One answer for one read.

    def __enter__(self) -> StandInReply:
        """Open the answer, as a real answer opens in a `with` block."""
        return self  # The reader reads the status and the body inside the block.

    def __exit__(self, *details: object) -> None:
        """Close the answer. A stand-in holds no socket, so the close does nothing."""

    def read(self) -> bytes:
        """Return the body as bytes, as a real answer does."""
        return self.text.encode("utf-8")  # The portal answers UTF-8 text.


@dataclass
class ScriptedOpener:
    """Answer each read from a script, and record each request."""

    replies: list[StandInReply | Exception]  # The answers in order. An exception stands for a failed read.
    requests: list[Any] = field(default_factory=list)  # Each request that the reader sent.
    timeouts: list[float] = field(default_factory=list)  # The bound of each read.

    def open(self, request: Any, timeout: float) -> StandInReply:
        """Record one request, and return or raise the next scripted answer."""
        self.requests.append(request)  # The test reads each address and each header later.
        self.timeouts.append(timeout)  # The test reads the bound that the reader chose.
        reply = self.replies.pop(0)  # A read with no script raises, and the test fails.
        if isinstance(reply, Exception):  # The script stands for a refused read or a failed read.
            raise reply  # The reader must turn the failure into a named failure.
        return reply  # A plain answer.

    def urls(self) -> list[str]:
        """Return the address of each request, in the order of the reads."""
        return [str(request.full_url) for request in self.requests]  # The order proves the paging.


def _row(run_id: str, state: object) -> dict[str, Any]:
    """Return one history row of the first site."""
    return {"run_id": run_id, "site_id": SITE_ID, "state": state}  # The three fields that the check reads.


def _page(rows: list[Any]) -> StandInReply:
    """Return one history page that holds the rows."""
    return StandInReply.of({"runs": rows, "total": len(rows)})  # The route answers the rows and a count.


def _full_page() -> StandInReply:
    """Return one full history page of final runs."""
    rows = [_row(f"run-done-{index}", "complete") for index in range(SiteRunReader.PAGE_SIZE)]  # A full page.
    return _page(rows)  # A full page tells the reader to read the next page.


def _reader(opener: ScriptedOpener, clock: Callable[[], float] | None = None) -> SiteRunReader:
    """Return a reader that sends each read to the scripted opener."""
    return SiteRunReader(BASE_URL, COOKIE_HEADER, opener=opener.open, clock=clock)  # No socket opens.


def _scan(runs: set[LiveRun], rows: int = 5, elapsed_ms: float = 10.0) -> SiteRunScan:
    """Return one scan of the five sites of the picker."""
    return SiteRunScan(frozenset(runs), rows, 5, elapsed_ms)  # The picker lists five sites.


class TestTheLiveRule:
    """The live rule of the check agrees with the create refusal of the portal."""

    @pytest.mark.parametrize("state", [state.value for state in RunState])
    def test_the_rule_agrees_with_the_portal_for_each_state(self, state: str) -> None:
        """Each state of the run model gives the answer of `run_is_live`."""
        row = _row("run-3511", state)  # One history row in this state.
        assert (LiveRun.from_row(SITE_ID, row) is not None) is run_is_live(row)  # The two rules agree.

    def test_a_created_run_is_live_and_names_its_site_its_key_and_its_state(self) -> None:
        """A run that no test ended blocks a create, so the check keeps it."""
        found = LiveRun.from_row(SITE_ID, _row("run-3511", "created"))  # The state of the leftover walk run.
        assert found == LiveRun(SITE_ID, "run-3511", "created")  # The message can name all three values.

    @pytest.mark.parametrize("state", sorted(state.value for state in RunStateMachine.TERMINAL))
    def test_a_final_run_is_not_live(self, state: str) -> None:
        """A final run blocks no create, so the check skips it."""
        assert LiveRun.from_row(SITE_ID, _row("run-3511", state)) is None  # The create refusal skips it too.

    @pytest.mark.parametrize("state", ["", "paused", None, 7])
    def test_a_row_with_an_unknown_state_is_not_live(self, state: object) -> None:
        """A state outside the run model is not live, as `run_is_live` states."""
        assert LiveRun.from_row(SITE_ID, _row("run-3511", state)) is None  # The create refusal skips it too.

    def test_a_row_with_no_state_is_not_live(self) -> None:
        """A row with no state field is not live, as `run_is_live` states."""
        assert LiveRun.from_row(SITE_ID, {"run_id": "run-3511", "site_id": SITE_ID}) is None  # No state to read.

    def test_an_empty_row_is_not_live_for_the_portal_or_the_check(self) -> None:
        """An empty history row blocks no create call, so the check never reports it as a leak."""
        assert run_is_live({}) is False  # The create refusal cannot read a state from an empty row.
        assert LiveRun.from_row(SITE_ID, {}) is None  # The check uses the same rule, so it skips the row too.


class TestTheReader:
    """The reader reads each page of the run history of each site."""

    def test_one_short_page_ends_the_read_of_a_site(self) -> None:
        """A page with fewer rows than the page size is the last page."""
        opener = ScriptedOpener([_page([_row("run-live", "created"), _row("run-done", "complete")])])  # One page.
        scan = _reader(opener).scan([SITE_ID])  # Read the first site.
        assert scan.runs == frozenset({LiveRun(SITE_ID, "run-live", "created")})  # The live run only.
        assert (scan.rows, scan.sites) == (2, 1)  # Two rows at one site.
        assert opener.urls() == [BASE_URL + FIRST_PAGE_PATH]  # One read of the largest page.

    def test_each_read_carries_the_session_cookies_and_the_bound(self) -> None:
        """The route needs a session, and each read must end within the bound."""
        opener = ScriptedOpener([_page([])])  # A site with no run.
        _reader(opener).scan([SITE_ID])  # Read the first site.
        request = opener.requests[0]  # The one request of the read.
        assert (request.get_method(), request.get_header("Cookie")) == ("GET", COOKIE_HEADER)  # A signed read.
        assert opener.timeouts == [SiteRunReader.TIMEOUT_S]  # The read cannot wait for ever.

    def test_a_full_page_asks_for_the_next_page(self) -> None:
        """A full page can hide more rows, so the reader reads the next page."""
        opener = ScriptedOpener([_full_page(), _page([_row("run-live", "created")])])  # Two pages.
        scan = _reader(opener).scan([SITE_ID])  # Read the first site.
        assert scan.runs == frozenset({LiveRun(SITE_ID, "run-live", "created")})  # The live run of page two.
        assert scan.rows == SiteRunReader.PAGE_SIZE + 1  # Each row of both pages.
        assert opener.urls()[1].endswith(f"offset={SiteRunReader.PAGE_SIZE}")  # Page two starts after page one.

    def test_the_page_bound_stops_a_history_that_does_not_end(self) -> None:
        """A wrong answer cannot start an endless read."""
        opener = ScriptedOpener([_full_page() for _ in range(SiteRunReader.PAGE_BOUND)])  # Only full pages.
        with pytest.raises(AssertionError, match="did not end") as failure:  # The read stops at the bound.
            _reader(opener).scan([SITE_ID])  # Read the first site.
        missing = [text for text in (SITE_ID, "#3511") if text not in str(failure.value)]  # The words to find.
        assert missing == []  # The reader learns the site and the issue.
        assert len(opener.requests) == SiteRunReader.PAGE_BOUND  # No read after the bound.

    def test_a_row_that_is_not_an_object_counts_as_read_and_never_as_live(self) -> None:
        """A damaged row blocks no create, as `site_run_records` of the portal states."""
        opener = ScriptedOpener([_page([_row("run-live", "created"), "damaged", 7])])  # Two damaged rows.
        scan = _reader(opener).scan([SITE_ID])  # Read the first site.
        assert scan.runs == frozenset({LiveRun(SITE_ID, "run-live", "created")})  # The live run only.
        assert scan.rows == 3  # The count names each row that the route answered.

    def test_the_scan_reads_each_site_in_order_and_times_the_read(self) -> None:
        """The scan reads each site of the picker, and the record holds its time."""
        opener = ScriptedOpener([_page([]), _page([])])  # Two sites with no run.
        ticks = iter([2.0, 2.0125])  # The clock before and after the scan.
        scan = _reader(opener, clock=ticks.__next__).scan([SITE_ID, SECOND_SITE_ID])  # Read two sites.
        assert [url.split("/")[5] for url in opener.urls()] == [SITE_ID, SECOND_SITE_ID]  # In the order given.
        assert (scan.sites, scan.elapsed_ms) == (2, 12.5)  # Two sites in 12.5 milliseconds.

    @pytest.mark.parametrize(
        ("reply", "words"),
        [
            (StandInReply.of(""), "empty body"),
            (StandInReply.of("<html>sign in</html>"), "not JSON"),
            (StandInReply.of([]), "not an object"),
            (StandInReply.of({"total": 0}), "no run list"),
            (StandInReply.of({"runs": {"run_id": "run-3511"}, "total": 1}), "no run list"),
        ],
    )
    def test_a_body_that_the_check_cannot_read_fails_and_names_the_call(self, reply: StandInReply, words: str) -> None:
        """A body that holds no run list must fail, because "no live run" would hide a leak."""
        with pytest.raises(AssertionError, match=words) as failure:  # The check stops at once.
            _reader(ScriptedOpener([reply])).scan([SITE_ID])  # Read the first site.
        assert FIRST_PAGE_CALL in str(failure.value)  # The reader learns which call failed.

    def test_a_refusal_fails_and_names_the_call_the_status_and_the_body(self) -> None:
        """A refused read must fail, because "no live run" would hide a leak."""
        body = b'{"error": {"code": "session_required"}}'  # The body of a refusal of the portal.
        refusal = HTTPError(BASE_URL + FIRST_PAGE_PATH, 401, "UNAUTHORIZED", Message(), io.BytesIO(body))
        with pytest.raises(AssertionError, match="answered 401") as failure:  # The check stops at once.
            _reader(ScriptedOpener([refusal])).scan([SITE_ID])  # Read the first site.
        words = (FIRST_PAGE_CALL, "session_required", "#3511")  # The call, the refusal code, and the issue.
        assert [text for text in words if text not in str(failure.value)] == []  # The reader learns each one.

    @pytest.mark.parametrize("cause", [URLError("connection refused"), TimeoutError("timed out")])
    def test_an_unreachable_portal_fails_and_names_the_call(self, cause: Exception) -> None:
        """A read that gets no answer must fail, because "no live run" would hide a leak."""
        with pytest.raises(AssertionError, match="did not answer") as failure:  # The check stops at once.
            _reader(ScriptedOpener([cause])).scan([SITE_ID])  # Read the first site.
        assert FIRST_PAGE_CALL in str(failure.value)  # The reader learns which call failed.
        assert failure.value.__cause__ is cause  # The report keeps the cause.


class TestTheCheck:
    """The check fails the module that left a new live run."""

    def test_a_new_live_run_fails_the_module_and_names_the_run(self) -> None:
        """A run that is live after the module, and not before it, is a leak of the module."""
        check = LiveRunCheck(MODULE, frozenset(), _scan({LIVE}))  # No live run before the module.
        assert check.leaks == (LIVE,)  # The module left one live run.
        with pytest.raises(AssertionError, match="left 1 live run") as failure:  # The module fails.
            check.require_no_leak()  # Decide the module.
        words = (MODULE, LIVE.run_id, LIVE.state, LIVE.site_id, "#3511")  # The module, the run, and the issue.
        assert [text for text in words if text not in str(failure.value)] == []  # The reader learns each one.

    def test_a_run_that_was_live_before_the_module_is_not_a_leak(self) -> None:
        """An earlier module left the run, so this module gets no blame, even when the state moved."""
        moved = LiveRun(LIVE.site_id, LIVE.run_id, "awaiting_confirmation")  # The same run in a later state.
        check = LiveRunCheck(MODULE, frozenset({LIVE}), _scan({moved}))  # The run was live before the module.
        assert check.leaks == ()  # No new live run.
        assert check.require_no_leak() is None  # The module passes.

    def test_a_run_that_the_module_ended_is_not_a_leak(self) -> None:
        """A module that ends a leftover run leaves no leak."""
        check = LiveRunCheck(MODULE, frozenset({LIVE}), _scan(set()))  # The run ended during the module.
        assert check.leaks == ()  # No live run after the module.

    def test_the_leaks_come_in_a_stable_order(self) -> None:
        """Each leak comes in the order of the site and the key, so two runs give one message."""
        later = LiveRun(SECOND_SITE_ID, "run-b", "created")  # A leak at the second site.
        check = LiveRunCheck(MODULE, frozenset(), _scan({later, LIVE}))  # Two leaks in a set.
        assert check.leaks == (LIVE, later)  # The first site comes first.

    def test_the_record_states_each_count_and_each_leak(self) -> None:
        """One line of the record holds the counts and each leak of one module."""
        check = LiveRunCheck(MODULE, frozenset(), _scan({LIVE}, rows=7, elapsed_ms=12.5))  # One leak.
        leak = {"site_id": SITE_ID, "run_id": LIVE.run_id, "state": "created"}  # The leak as a record.
        expected = {"module": MODULE, "before": 0, "after": 1, "leaks": [leak]}  # The module and the runs.
        expected.update({"rows": 7, "sites": 5, "elapsed_ms": 12.5})  # The size and the time of the scan.
        assert check.record() == expected  # Each value of the record.
        assert json.loads(json.dumps(check.record())) == expected  # One JSON line holds the record.

    def test_the_summary_states_what_the_check_read_and_found(self) -> None:
        """The summary line names the sites, the modules, the rows, the leaks, and the time."""
        clean = LiveRunCheck(MODULE, frozenset(), _scan(set(), rows=5, elapsed_ms=10.0))  # No leak.
        leaking = LiveRunCheck(MODULE, frozenset(), _scan({LIVE}, rows=7, elapsed_ms=12.5))  # One leak.
        assert LiveRunCheck.summary([clean, leaking]) == (  # The one line of the terminal summary.
            "The live-run check of issue #3511 scanned 5 site(s) after each of 2 module(s). "
            "It read 12 history row(s), found 1 leaked live run(s), and took 22.5 ms."
        )

    def test_the_summary_is_empty_when_no_module_ran_the_check(self) -> None:
        """A run that started no portal ran no check, so the summary prints no line."""
        assert LiveRunCheck.summary([]) == ""  # The hook prints nothing for an empty line.
