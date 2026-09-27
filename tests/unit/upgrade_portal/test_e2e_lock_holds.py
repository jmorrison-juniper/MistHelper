"""Prove the site lock record of the run-control browser tests with no browser and no network.

Why:
    Issue #3508. The fixture `site_lock` of the run-control tests logged a
    warning when a release failed, and the run still passed. The test of the
    lost action answer cleared the cookies before the teardown. Its release then
    answered 400 `csrf_missing`, and the site kept its lock. The class
    `HeldSiteLocks` of `tests/support/upgrade_portal_e2e/lock_holds.py` now
    fails the teardown. These direct tests prove each decision of the class
    with a stand-in page, so each decision can fail with no portal.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Build the body text of each stand-in answer, and read each sent body.
import logging  # Read the log lines of the class under test.
from dataclasses import dataclass, field  # Describe the stand-in page and its locator.
from typing import Any  # A recorded call holds values of mixed types.

import pytest  # Check each refusal of the class under test.

from tests.support.upgrade_portal_e2e.lock_holds import HeldSiteLocks  # The class under test.

SITE_ID = "66666666-6666-6666-6666-666666666666"  # The site of the test of the lost action answer.
OTHER_SITE_ID = "22222222-2222-2222-2222-222222222222"  # A second site of the run-control tests.
LOCK_PATH = f"/api/sites/{SITE_ID}/lock"  # The lock route of the first site.
OTHER_LOCK_PATH = f"/api/sites/{OTHER_SITE_ID}/lock"  # The lock route of the second site.
CSRF_TOKEN = "csrf-3508"  # The token that the page head publishes.
LOCK_TOKEN = "lock-3508"  # The token of the first grant.
OTHER_LOCK_TOKEN = "lock-3508-other"  # The token of the second grant.
CSRF_SELECTOR = 'meta[name="csrf-token"]'  # `layout.html` publishes the token in this element.
LOCK_LOST_BODY = {"error": {"code": "lock_lost", "message": "You no longer hold this site."}}  # The 409 body.
CSRF_MISSING_BODY = {"error": {"code": "csrf_missing", "message": "The request carries no valid security token."}}
CLOSED_PAGE = "Target page, context or browser has been closed"  # The text of a Playwright error.
LOG_NAME = "tests.support.upgrade_portal_e2e.lock_holds"  # The logger of the class under test.


def _answer(status: int, body: object) -> dict[str, Any]:
    """Build one answer of the page script, in the shape that the lock script returns."""
    text = body if isinstance(body, str) else json.dumps(body)  # The portal answers JSON text.
    return {"ok": 200 <= status < 300, "status": status, "text": text}  # The three fields of the script.


def _grant(token: str = LOCK_TOKEN, state: str = "acquired") -> dict[str, Any]:
    """Build one grant of the lock take."""
    return _answer(200, {"lock_token": token, "state": state, "expires_in": 3600})  # The grant body.


def _released() -> dict[str, Any]:
    """Build the one answer of a release that the contract names."""
    return _answer(200, {"released": True})  # `select.free_site_lock` answers this body with 200.


@dataclass
class StandInLocator:
    """Give the value of one attribute, in the shape of a Playwright locator."""

    value: str | None  # The value of the content attribute.

    def get_attribute(self, name: str) -> str | None:
        """Return the value of the content attribute, and no value for another attribute."""
        return self.value if name == "content" else None  # The class under test reads the content only.


@dataclass
class StandInPage:
    """Answer each lock script from a script of answers, and record each call."""

    answers: list[dict[str, Any] | Exception]  # The answers in order. An exception raises in place of an answer.
    csrf_token: str | None = CSRF_TOKEN  # The token that the page head publishes.
    calls: list[dict[str, Any]] = field(default_factory=list)  # Each argument of each script call.
    selectors: list[str] = field(default_factory=list)  # Each selector that the class under test read.

    def locator(self, selector: str) -> StandInLocator:
        """Record the selector, and return the locator of the token."""
        self.selectors.append(selector)  # The test proves that the class reads the page head.
        return StandInLocator(self.csrf_token)  # The class reads the token at call time.

    def evaluate(self, script: str, argument: dict[str, Any]) -> dict[str, Any]:
        """Record one script call, and return the next answer or raise the next exception."""
        self.calls.append({**argument, "script": script})  # Keep the path, the method, the token, and the body.
        answer = self.answers.pop(0)  # A call with no scripted answer raises IndexError, and the test fails.
        if isinstance(answer, Exception):  # A closed page raises in place of an answer.
            raise answer  # The class under test must turn this into a named failure.
        return answer  # The class under test decides from the status and the text.

    def methods(self) -> list[tuple[str, str]]:
        """Return the method and the path of each call, in the order of the calls."""
        return [(str(call["method"]), str(call["path"])) for call in self.calls]  # The order proves each decision.


class TestTheTake:
    """A take records one hold, and each other answer fails."""

    def test_a_fresh_grant_records_one_hold_and_sends_the_token_of_the_page(self) -> None:
        """A grant with the state acquired records the site, and the call carries the token of the page."""
        page = StandInPage([_grant()])  # The portal grants a fresh lock.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The first operator page takes the site.
        assert holds.sites == (SITE_ID,)  # The record holds the site.
        assert page.methods() == [("POST", LOCK_PATH)]  # One take on the lock route of the site.
        assert page.calls[0]["token"] == CSRF_TOKEN  # The call carries the token that the page shows now.
        assert page.calls[0]["body"] == "{}"  # A plain take types no word.
        assert page.selectors == [CSRF_SELECTOR]  # The class read the token from the page head.

    def test_a_refused_take_fails_and_names_the_path_the_status_and_the_body(self) -> None:
        """A refusal of the take fails, and the message names the call, the status, and the body."""
        page = StandInPage([_answer(409, {"error": {"code": "site_locked"}})])  # Another operator holds the site.
        holds = HeldSiteLocks(page)  # The record of one test.
        with pytest.raises(AssertionError) as caught:  # A test that needs the site must stop.
            holds.take(SITE_ID)  # The portal refuses the take.
        message = str(caught.value)  # The text that pytest reports.
        assert f"POST {LOCK_PATH}" in message and "409" in message  # The call and the status.
        assert "site_locked" in message  # The body names the refusal code.
        assert holds.sites == ()  # A refused take records no hold.

    def test_a_grant_that_is_not_fresh_fails_because_an_earlier_test_left_the_lock(self) -> None:
        """A grant with the state resume means that an earlier test left the lock, so the take fails."""
        page = StandInPage([_grant(state="resume")])  # The same operator held the site already.
        holds = HeldSiteLocks(page)  # The record of one test.
        with pytest.raises(AssertionError, match="An earlier test left the lock"):  # Name the leak.
            holds.take(SITE_ID)  # The portal answers a resume.
        assert holds.sites == ()  # A take that shares a lock records no hold.

    def test_a_grant_with_bad_json_fails_and_keeps_the_parser_error(self) -> None:
        """A 200 with a body that is not JSON fails, and the cause is the JSONDecodeError of the parser."""
        page = StandInPage([_answer(200, "<html>proxy page</html>")])  # A proxy answered in place of the portal.
        holds = HeldSiteLocks(page)  # The record of one test.
        with pytest.raises(AssertionError, match="is not JSON") as caught:  # The message names the call.
            holds.take(SITE_ID)  # The body holds no token.
        assert isinstance(caught.value.__cause__, json.JSONDecodeError)  # The report keeps the parser position.
        assert holds.sites == ()  # A body with no token records no hold.

    def test_a_take_on_a_second_page_releases_from_that_page(self) -> None:
        """A lock that a second page took goes back through the same page."""
        first = StandInPage([])  # The first operator page sends no call.
        second = StandInPage([_grant(), _released()])  # The second page takes the site and releases it.
        holds = HeldSiteLocks(first)  # The fixture binds the first page.
        holds.take(SITE_ID, lock_page=second)  # The test names the second page.
        holds.release_all()  # The teardown frees the site.
        assert first.calls == []  # The first page sent no call.
        assert second.methods() == [("POST", LOCK_PATH), ("DELETE", LOCK_PATH)]  # The same session releases.


class TestTheRelease:
    """A release passes only on 200 with the released field true."""

    def test_a_release_sends_the_token_and_forgets_the_hold(self) -> None:
        """A release sends the token of the grant, and the teardown then sends no second release."""
        page = StandInPage([_grant(), _released()])  # The portal grants the lock and accepts the release.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The test takes the site.
        holds.release(SITE_ID)  # The test frees the site before it ends.
        assert json.loads(page.calls[1]["body"]) == {"lock_token": LOCK_TOKEN}  # The token of the grant.
        assert page.methods()[1] == ("DELETE", LOCK_PATH)  # The release goes to the same route.
        assert holds.sites == ()  # The record forgets the site.
        holds.release_all()  # The teardown runs after the test.
        assert len(page.calls) == 2  # The teardown sent no second release.

    def test_a_release_of_a_site_with_no_hold_fails_and_names_the_site(self) -> None:
        """A release of a site that the record does not hold is a fault of the test."""
        holds = HeldSiteLocks(StandInPage([]))  # The record holds no lock.
        with pytest.raises(AssertionError, match=SITE_ID):  # The message names the site.
            holds.release(SITE_ID)  # The test releases a site that it never took.

    @pytest.mark.parametrize(
        ("status", "body", "code"),
        [
            (409, LOCK_LOST_BODY, "lock_lost"),  # A new token, and the session holds no lock record.
            (400, CSRF_MISSING_BODY, "csrf_missing"),  # The red run of issue #3508: the page kept an old token.
        ],
    )
    def test_a_refused_release_fails_and_names_the_path_the_status_and_the_body(
        self, status: int, body: dict[str, Any], code: str
    ) -> None:
        """A refused release fails, and the message names the call, the status, and the code of the body."""
        page = StandInPage([_grant(), _answer(status, body)])  # The session lost its lock record or its token.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The test takes the site.
        with pytest.raises(AssertionError) as caught:  # The site keeps its lock, so the release must fail.
            holds.release(SITE_ID)  # The portal refuses the release.
        message = str(caught.value)  # The text that pytest reports.
        assert f"DELETE {LOCK_PATH}" in message and str(status) in message  # The call and the status.
        assert code in message  # The body names the refusal code.
        assert holds.sites == ()  # The record forgets the site, so the teardown reports the fault one time.

    @pytest.mark.parametrize(
        ("body", "cause"),
        [
            ("", "empty body"),
            ("[]", "not an object"),
            ('{"released": false}', "did not report the release"),
            ("{}", "did not report the release"),
            ('{"released": "true"}', "did not report the release"),
        ],
    )
    def test_a_release_with_a_bad_200_body_fails(self, body: str, cause: str) -> None:
        """A 200 that holds no JSON object, or no released field that is true, fails."""
        page = StandInPage([_grant(), _answer(200, body)])  # The route answered 200 with a bad body.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The test takes the site.
        with pytest.raises(AssertionError, match=cause):  # The message names the fault of the body.
            holds.release(SITE_ID)  # The release cannot prove that the site is free.

    def test_a_release_with_bad_json_keeps_the_parser_error_as_the_cause(self) -> None:
        """A 200 with a body that is not JSON fails, and the cause is the JSONDecodeError of the parser."""
        page = StandInPage([_grant(), _answer(200, "released")])  # A body of plain text.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The test takes the site.
        with pytest.raises(AssertionError, match=f"DELETE {LOCK_PATH}") as caught:  # The message names the call.
            holds.release(SITE_ID)  # The body is not JSON.
        assert isinstance(caught.value.__cause__, json.JSONDecodeError)  # The report keeps the parser position.

    def test_a_release_that_cannot_run_fails_and_names_the_site_and_the_cause(self) -> None:
        """A release on a closed page fails, and the message names the site and the error of the browser."""
        page = StandInPage([_grant(), RuntimeError(CLOSED_PAGE)])  # The browser closed before the release.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The test takes the site.
        with pytest.raises(AssertionError) as caught:  # The site keeps its lock, so the release must fail.
            holds.release(SITE_ID)  # The page cannot send the call.
        message = str(caught.value)  # The text that pytest reports.
        assert SITE_ID in message and CLOSED_PAGE in message  # The site and the cause.
        assert isinstance(caught.value.__cause__, RuntimeError)  # The report keeps the error of the browser.


class TestTheTeardown:
    """The teardown tries each hold, and it fails after the last try."""

    def test_the_teardown_releases_each_hold_newest_first(self) -> None:
        """The teardown releases in the reverse order of the takes."""
        answers = [_grant(), _grant(OTHER_LOCK_TOKEN), _released(), _released()]  # Two takes, two releases.
        page = StandInPage(list(answers))  # The portal accepts each call.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The first take.
        holds.take(OTHER_SITE_ID)  # The second take.
        holds.release_all()  # The teardown frees both sites.
        assert page.methods()[2:] == [("DELETE", OTHER_LOCK_PATH), ("DELETE", LOCK_PATH)]  # Newest first.
        assert json.loads(page.calls[2]["body"]) == {"lock_token": OTHER_LOCK_TOKEN}  # Each token goes home.
        assert holds.sites == ()  # The record holds no lock after the teardown.

    def test_the_teardown_tries_each_hold_and_names_each_fault(self) -> None:
        """Two failed releases give one failure that names both faults."""
        answers: list[dict[str, Any] | Exception] = [_grant(), _grant(OTHER_LOCK_TOKEN)]  # Two takes.
        answers += [_answer(409, LOCK_LOST_BODY), RuntimeError(CLOSED_PAGE)]  # Both releases fail.
        page = StandInPage(answers)  # The portal grants both locks.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The first take.
        holds.take(OTHER_SITE_ID)  # The second take.
        with pytest.raises(AssertionError) as caught:  # Both sites keep a lock.
            holds.release_all()  # The teardown tries both releases.
        message = str(caught.value)  # The text that pytest reports.
        assert "2 site lock(s)" in message  # The count of faults.
        assert f"DELETE {OTHER_LOCK_PATH}" in message and "lock_lost" in message  # The first fault.
        assert SITE_ID in message and CLOSED_PAGE in message  # The second fault.
        assert len(page.calls) == 4  # The first fault did not stop the second release.

    def test_one_fault_does_not_stop_the_release_of_another_site(self) -> None:
        """A failed release of the newest hold still lets the teardown free the older hold."""
        answers = [_grant(), _grant(OTHER_LOCK_TOKEN), _answer(409, LOCK_LOST_BODY), _released()]  # One fault.
        page = StandInPage(list(answers))  # The portal refuses the first release only.
        holds = HeldSiteLocks(page)  # The record of one test.
        holds.take(SITE_ID)  # The first take.
        holds.take(OTHER_SITE_ID)  # The second take.
        with pytest.raises(AssertionError) as caught:  # One site keeps a lock.
            holds.release_all()  # The teardown tries both releases.
        assert "1 site lock(s)" in str(caught.value)  # One fault.
        assert OTHER_LOCK_PATH in str(caught.value) and LOCK_PATH not in str(caught.value)  # Only the fault.
        assert page.methods()[3] == ("DELETE", LOCK_PATH)  # The older hold went home.

    def test_the_teardown_with_no_hold_sends_no_call(self) -> None:
        """A test that took no lock ends with no call."""
        page = StandInPage([])  # The page answers no call.
        HeldSiteLocks(page).release_all()  # The teardown of a test that took no lock.
        assert page.calls == []  # No call reached the page.


def test_no_log_line_holds_a_lock_token(caplog: pytest.LogCaptureFixture) -> None:
    """The log names each call and each status, and it never names the token of a lock."""
    caplog.set_level(logging.DEBUG, logger=LOG_NAME)  # Read each line of the class under test.
    page = StandInPage([_grant(), _released()])  # The portal grants the lock and accepts the release.
    holds = HeldSiteLocks(page)  # The record of one test.
    holds.take(SITE_ID)  # The test takes the site.
    holds.release(SITE_ID)  # The test frees the site.
    assert "POST" in caplog.text and "DELETE" in caplog.text  # The log names both calls.
    assert LOCK_TOKEN not in caplog.text  # A token in a log line could free the site of another test.
