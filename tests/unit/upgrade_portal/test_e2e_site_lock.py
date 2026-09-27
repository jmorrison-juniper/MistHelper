"""Prove the site lock rules of the browser tests with no browser and no network.

Why:
    Issue #3497. The run-control tests left a run and a site lock on the
    stand-in site. The fixture `held_site` of the two-operator tests then
    skipped 18 tests, and pytest counted each skip as a pass. The classes of
    `tests/support/upgrade_portal_e2e/site_lock.py` hold each decision of the
    repair. These direct tests prove that each decision can fail, so a later
    leak cannot hide as a skip. The tests of `AnswerBody` also prove that an
    empty body and a body that is not JSON fail with the name of the call.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Build the body text of each stand-in answer, and read each sent body.
from dataclasses import dataclass, field  # Describe the stand-in answer and the stand-in request source.
from typing import Any  # A recorded call holds values of mixed types.

import pytest  # Check each refusal and each skip.

from src.upgrade_portal.runtime.runs import RunStateMachine  # The final states of the run model.
from tests.support.upgrade_portal_e2e.site_lock import (  # The classes under test.
    AnswerBody,
    LockTakeAnswer,
    RunLedger,
    SiteRelease,
)

RUN_ID = "e2e-run-3497"  # A run that one browser test built.
RETRY_RUN_ID = "e2e-retry-3497"  # The retry run that the retry control built.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The stand-in site of the run-control tests.
CSRF_TOKEN = "csrf-3497"  # The token for the cross-site request check.
LOCK_TOKEN = "lock-3497"  # The token that a lock take gives back.
STATUS_PATH = f"/api/runs/{RUN_ID}/status"  # The status route of the run.
CANCEL_PATH = f"/api/runs/{RUN_ID}/cancel"  # The cancel route of the run.
LOCK_PATH = f"/api/sites/{SITE_ID}/lock"  # The lock route of the site.
STATUS_CALL = f"GET {STATUS_PATH}"  # The status read, as each message of the teardown names it.
TAKE_CALL = f"POST {LOCK_PATH}"  # The lock take, as each message names it.
CAPTURE_URL = "http://127.0.0.1:9601/captures/new"  # The capture page that the retry control opens.


@dataclass
class StandInAnswer:
    """Give one status and one body text, in the shape of a Playwright answer."""

    status: int  # The status of the answer.
    body: str  # The body text of the answer.

    @classmethod
    def of(cls, status: int, body: object) -> StandInAnswer:
        """Build one answer, and write a body that is not text as JSON text."""
        text = body if isinstance(body, str) else json.dumps(body)  # The portal answers JSON text.
        return cls(status, text)  # One answer for one call.

    def text(self) -> str:
        """Return the body text."""
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


def _live_run_script() -> dict[tuple[str, str], list[StandInAnswer]]:
    """Return the script of a live run that accepts one cancel."""
    return {  # The status read comes first, and the cancel comes second.
        ("get", STATUS_PATH): [StandInAnswer.of(200, {"run_id": RUN_ID, "state": "created"})],
        ("post", CANCEL_PATH): [StandInAnswer.of(200, {"run_id": RUN_ID, "state": "cancelled"})],
    }


def _free_site_script(release: StandInAnswer) -> dict[tuple[str, str], list[StandInAnswer]]:
    """Return the script of a lock take that the portal grants, and of one release answer."""
    grant = StandInAnswer.of(200, {"lock_token": LOCK_TOKEN, "state": "resume", "expires_in": 300})  # A grant.
    return {("post", LOCK_PATH): [grant], ("delete", LOCK_PATH): [release]}  # The take, then the release.


class TestTheRunLedger:
    """The ledger holds each run that one browser test built."""

    def test_the_ledger_keeps_each_run_one_time_in_the_order_of_the_record(self) -> None:
        """A run that the test meets two times gets one entry, and the order stays."""
        ledger = RunLedger()  # A new ledger for one test.
        ledger.record(RUN_ID)  # The create call built the first run.
        ledger.record(RETRY_RUN_ID)  # The retry control built the second run.
        ledger.record(RUN_ID)  # The test met the first run again.
        assert ledger.runs == (RUN_ID, RETRY_RUN_ID)  # One entry for each run, in the order of the record.

    @pytest.mark.parametrize("run_id", ["", "   "])
    def test_the_ledger_refuses_an_empty_key(self, run_id: str) -> None:
        """An empty key names no run, so the ledger refuses it."""
        with pytest.raises(ValueError, match="needs the key of a run"):  # A caller fault stops the test.
            RunLedger().record(run_id)  # No teardown could end a run with an empty key.

    def test_the_ledger_reads_the_retry_run_from_the_address(self) -> None:
        """The key of the retry run comes from the query of the capture page."""
        ledger = RunLedger()  # A new ledger for one test.
        url = f"{CAPTURE_URL}?site_id={SITE_ID}&run_id={RETRY_RUN_ID}&role=pre"  # The address after the retry.
        assert ledger.record_from_url(url) == RETRY_RUN_ID  # The ledger gives back the key that it read.
        assert ledger.runs == (RETRY_RUN_ID,)  # The teardown ends the retry run too.

    def test_an_address_with_no_run_fails_and_names_the_address(self) -> None:
        """An address with no run fails, because the teardown then cannot end the retry run."""
        url = f"{CAPTURE_URL}?site_id={SITE_ID}&role=pre"  # The address names no run.
        with pytest.raises(AssertionError, match="names no run") as failure:  # The test stops at once.
            RunLedger().record_from_url(url)  # The retry run stays unknown.
        assert url in str(failure.value)  # The reader learns which address held no run.


class TestTheAnswerBody:
    """Each 200 answer must carry a JSON object, and each failure names the call."""

    def test_an_object_body_gives_its_fields(self) -> None:
        """A body that holds a JSON object gives each field to the caller."""
        text = json.dumps({"run_id": RUN_ID, "state": "created"})  # The body of a status read.
        assert AnswerBody.read(STATUS_CALL, 200, text) == {"run_id": RUN_ID, "state": "created"}  # Both fields.

    @pytest.mark.parametrize("raw", [b"", b" \r\n "])
    def test_an_empty_body_fails_and_names_the_call_and_the_status(self, raw: bytes) -> None:
        """An empty body fails, because the parser error would not name the call."""
        with pytest.raises(AssertionError, match="empty body") as failure:  # The reader learns the fault.
            AnswerBody.read(TAKE_CALL, 200, raw.decode("ascii"))  # Playwright gives the body as text.
        message = str(failure.value)  # The text that the pytest report shows.
        assert TAKE_CALL in message  # The reader learns which call failed.
        assert "200" in message  # The reader learns the status.

    def test_a_body_that_is_not_json_fails_and_keeps_the_parser_error(self) -> None:
        """A proxy page fails with its body, and the parser error stays the cause."""
        page = "<html>Access denied</html>"  # A proxy answered 200 with an HTML page.
        with pytest.raises(AssertionError, match="not JSON") as failure:  # The reader learns the fault.
            AnswerBody.read(STATUS_CALL, 200, page)
        assert page in str(failure.value)  # The reader learns the body.
        assert isinstance(failure.value.__cause__, json.JSONDecodeError)  # The parser error names the position.

    @pytest.mark.parametrize("text", ["[]", "42", '"acquired"', "null"])
    def test_json_that_is_not_an_object_fails(self, text: str) -> None:
        """A list, a number, a string, and null hold no named field, so each one fails."""
        with pytest.raises(AssertionError, match="not an object") as failure:  # The reader learns the fault.
            AnswerBody.read(STATUS_CALL, 200, text)
        assert text in str(failure.value)  # The reader learns the body.


class TestTheEndOfTheRuns:
    """The teardown cancels each built run that is not final."""

    def test_a_live_run_gets_one_cancel(self) -> None:
        """A run in a live state gets one status read and then one cancel."""
        requests = ScriptedRequests(_live_run_script())  # The portal answers a live run.
        ended = SiteRelease(requests, CSRF_TOKEN).end_runs([RUN_ID])  # End the one built run.
        assert ended == 1  # One run needed a cancel.
        assert requests.paths() == [("get", STATUS_PATH), ("post", CANCEL_PATH)]  # The read comes first.

    @pytest.mark.parametrize("state", sorted(state.value for state in RunStateMachine.TERMINAL))
    def test_a_final_run_gets_no_cancel(self, state: str) -> None:
        """A run in each final state of the run model gets no cancel."""
        status = StandInAnswer.of(200, {"run_id": RUN_ID, "state": state})  # The run already ended.
        requests = ScriptedRequests({("get", STATUS_PATH): [status]})  # A cancel call would find no script.
        assert SiteRelease(requests, CSRF_TOKEN).end_runs([RUN_ID]) == 0  # No run needed a cancel.
        assert requests.paths() == [("get", STATUS_PATH)]  # The teardown read the state only.

    def test_a_run_that_the_store_does_not_hold_gets_no_cancel(self) -> None:
        """A 404 from the status route means that no run exists to end."""
        missing = StandInAnswer.of(404, {"error": {"code": "run_not_found"}})  # The store holds no such run.
        requests = ScriptedRequests({("get", STATUS_PATH): [missing]})  # A cancel call would find no script.
        assert SiteRelease(requests, CSRF_TOKEN).end_runs([RUN_ID]) == 0  # No run needed a cancel.
        assert requests.paths() == [("get", STATUS_PATH)]  # The teardown moved on after the read.

    def test_a_refused_cancel_fails_and_names_the_path_the_status_and_the_body(self) -> None:
        """A cancel that the portal refuses fails the teardown with the refusal body."""
        script = _live_run_script()  # A live run, and a cancel that the next line replaces.
        script[("post", CANCEL_PATH)] = [StandInAnswer.of(409, {"error": {"code": "run_already_started"}})]
        with pytest.raises(AssertionError) as failure:  # The teardown must not hide the live run.
            SiteRelease(requests=ScriptedRequests(script), csrf_token=CSRF_TOKEN).end_runs([RUN_ID])
        message = str(failure.value)  # The text that the pytest report shows.
        assert CANCEL_PATH in message  # The reader learns which call failed.
        assert "409" in message  # The reader learns the status.
        assert "run_already_started" in message  # The reader learns the refusal code.

    def test_a_refused_status_read_fails_and_names_the_body(self) -> None:
        """A status read that the portal refuses fails the teardown with the body."""
        requests = ScriptedRequests({("get", STATUS_PATH): [StandInAnswer.of(500, "the store did not answer")]})
        with pytest.raises(AssertionError) as failure:  # The teardown cannot tell whether the run is live.
            SiteRelease(requests, CSRF_TOKEN).end_runs([RUN_ID])
        message = str(failure.value)  # The text that the pytest report shows.
        assert STATUS_PATH in message  # The reader learns which call failed.
        assert "500" in message  # The reader learns the status.
        assert "the store did not answer" in message  # The reader learns the body.

    def test_a_status_read_whose_body_is_not_json_fails_and_names_the_call(self) -> None:
        """A 200 status read with a body that is not JSON fails, so no live run stays hidden."""
        page = StandInAnswer.of(200, "<html>Access denied</html>")  # A proxy answered in place of the portal.
        requests = ScriptedRequests({("get", STATUS_PATH): [page]})  # A cancel call would find no script.
        with pytest.raises(AssertionError, match="not JSON") as failure:  # The teardown cannot read the state.
            SiteRelease(requests, CSRF_TOKEN).end_runs([RUN_ID])
        assert STATUS_CALL in str(failure.value)  # The reader learns which call failed.


class TestTheFreeSite:
    """The teardown takes the site lock with the word `continue`, and then it releases the lock."""

    def test_the_site_is_taken_with_the_word_continue_and_then_released(self) -> None:
        """The take sends the word `continue`, and the release sends the token of the take."""
        requests = ScriptedRequests(_free_site_script(StandInAnswer.of(200, {"released": True})))  # Both calls pass.
        SiteRelease(requests, CSRF_TOKEN).free_site(SITE_ID)  # Free the site of one test.
        assert requests.paths() == [("post", LOCK_PATH), ("delete", LOCK_PATH)]  # The take comes first.
        assert json.loads(str(requests.calls[0]["data"])) == {"confirm": "continue"}  # The word of a quiet lock.
        assert json.loads(str(requests.calls[1]["data"])) == {"lock_token": LOCK_TOKEN}  # The token of the take.

    def test_each_call_carries_the_token_for_the_cross_site_check(self) -> None:
        """Each call of the teardown sends the token of the page, or the portal refuses it."""
        requests = ScriptedRequests(_free_site_script(StandInAnswer.of(200, {"released": True})))  # Both calls pass.
        SiteRelease(requests, CSRF_TOKEN).free_site(SITE_ID)  # Free the site of one test.
        tokens = [call["headers"].get("X-CSRFToken") for call in requests.calls]  # The header of each call.
        assert tokens == [CSRF_TOKEN, CSRF_TOKEN]  # Both calls carry the token.

    def test_a_refused_take_fails_and_sends_no_release(self) -> None:
        """A take that the portal refuses fails the teardown, and no release follows."""
        refusal = StandInAnswer.of(409, {"error": {"code": "site_locked"}})  # Another operator holds the site.
        requests = ScriptedRequests({("post", LOCK_PATH): [refusal]})  # A release call would find no script.
        with pytest.raises(AssertionError, match="site_locked") as failure:  # The reader learns the code.
            SiteRelease(requests, CSRF_TOKEN).free_site(SITE_ID)
        assert "409" in str(failure.value)  # The reader learns the status.
        assert requests.paths() == [("post", LOCK_PATH)]  # No release followed the refusal.

    def test_a_refused_release_fails_and_names_the_body(self) -> None:
        """A release that the portal refuses fails the teardown with the refusal body."""
        refusal = StandInAnswer.of(409, {"error": {"code": "lock_lost"}})  # The session lost the lock.
        requests = ScriptedRequests(_free_site_script(refusal))  # The take passes, and the release fails.
        with pytest.raises(AssertionError, match="lock_lost") as failure:  # The reader learns the code.
            SiteRelease(requests, CSRF_TOKEN).free_site(SITE_ID)
        assert "DELETE" in str(failure.value)  # The reader learns which call failed.


class TestTheLockTakeAnswer:
    """The fixture `held_site` accepts a fresh lock only."""

    def test_an_acquired_lock_gives_the_token(self) -> None:
        """A fresh lock gives the token to the fixture."""
        body = json.dumps({"lock_token": LOCK_TOKEN, "state": "acquired", "expires_in": 300})  # A fresh grant.
        assert LockTakeAnswer.require_token(LOCK_PATH, 200, body) == LOCK_TOKEN  # The fixture holds the lock.

    def test_a_resumed_lock_fails_and_names_the_leak(self) -> None:
        """A resumed lock fails, because an earlier test left the lock of the site."""
        body = json.dumps({"lock_token": LOCK_TOKEN, "state": "resume", "expires_in": 300})  # A leaked lock.
        with pytest.raises(AssertionError, match="An earlier test left the lock") as failure:  # The leak shows.
            LockTakeAnswer.require_token(LOCK_PATH, 200, body)
        assert "'resume'" in str(failure.value)  # The reader learns the state.

    def test_a_grant_with_no_token_fails(self) -> None:
        """A fresh grant with no token fails, because no release could free that lock."""
        body = json.dumps({"state": "acquired", "expires_in": 300})  # The grant names no token.
        with pytest.raises(AssertionError, match="named no lock token") as failure:  # The fault shows.
            LockTakeAnswer.require_token(LOCK_PATH, 200, body)
        assert LOCK_PATH in str(failure.value)  # The reader learns which call failed.

    def test_a_grant_with_an_empty_body_fails_and_names_the_take(self) -> None:
        """A 200 with an empty body fails, and the message names the take call."""
        with pytest.raises(AssertionError, match="empty body") as failure:  # No token can come from no body.
            LockTakeAnswer.require_token(LOCK_PATH, 200, "")
        assert TAKE_CALL in str(failure.value)  # The reader learns which call failed.

    @pytest.mark.parametrize(("status", "code"), [(400, "confirmation_required"), (409, "site_locked")])
    def test_a_refusal_fails_and_names_the_status_and_the_body(self, status: int, code: str) -> None:
        """A refusal fails the fixture, and pytest never counts it as a pass."""
        body = json.dumps({"error": {"code": code}})  # The refusal envelope of the contract.
        with pytest.raises(AssertionError) as failure:  # A skip here hid 18 tests before this change.
            LockTakeAnswer.require_token(LOCK_PATH, status, body)
        message = str(failure.value)  # The text that the pytest report shows.
        assert LOCK_PATH in message  # The reader learns which call failed.
        assert str(status) in message  # The reader learns the status.
        assert code in message  # The reader learns the refusal code.

    def test_a_missing_lock_store_is_a_skip_that_names_the_store(self) -> None:
        """A 503 describes a workstation with no lock store, so it stays a skip."""
        body = json.dumps({"error": {"code": "lock_store_unreachable"}})  # The store did not answer.
        with pytest.raises(pytest.skip.Exception, match="lock store") as skipped:  # A skip, and not a failure.
            LockTakeAnswer.require_token(LOCK_PATH, 503, body)
        assert "lock_store_unreachable" in str(skipped.value)  # The reader learns the refusal code.

    @pytest.mark.parametrize("status", [401, 404])
    def test_a_missing_route_fails_and_names_the_lock_route(self, status: int) -> None:
        """A 401 and a 404 name a fault of the portal, so neither may skip."""
        with pytest.raises(AssertionError, match="serves no lock route") as failure:  # The portal is broken.
            LockTakeAnswer.require_token(LOCK_PATH, status, "{}")
        assert str(status) in str(failure.value)  # The reader learns the status.

    def test_any_other_status_fails_and_names_the_status_and_the_body(self) -> None:
        """A status that the contract does not name fails the fixture with the body."""
        with pytest.raises(AssertionError) as failure:  # No other status may pass as a skip.
            LockTakeAnswer.require_token(LOCK_PATH, 500, "the portal failed")
        message = str(failure.value)  # The text that the pytest report shows.
        assert "500" in message  # The reader learns the status.
        assert "the portal failed" in message  # The reader learns the body.
