"""Hold each site lock that one run-control browser test took, and free each lock after the test.

Why:
    Issue #3508. The fixture `site_lock` of the run-control tests released each
    lock in its teardown, and it logged a warning when a release failed. The
    test of the lost action answer cleared the cookies before the teardown. The
    page kept the cross-site request token of the first session, so the release
    answered 400 `csrf_missing`. The site kept its lock, and the run still
    passed.

    `LockCall` sends one lock call from the browser session of one page.
    `LockHold` holds the page, the site, and the token of one take, and it
    releases that lock. `HeldSiteLocks` records each hold of one test. A test
    can release one site before it ends. The teardown releases each hold that
    remains, and it fails when a release fails. The module holds no Playwright
    import, so a direct test proves each decision with a stand-in page.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Build the body of each release.
import logging  # Record each lock action without a token value.
from dataclasses import dataclass  # Describe one hold.
from typing import Any, ClassVar  # Playwright gives the page, so its type is Any.

from tests.support.upgrade_portal_e2e.site_lock import AnswerBody, LockTakeAnswer  # Issue #3497: the body rules.

logger = logging.getLogger(__name__)  # Keep each lock record of the fixture tied to this module.


class LockCall:  # Send one lock call from the browser session of one page.
    """Send one lock call from the browser session of one page.

    Why:
        The route reads the lock record from the signed session cookie, and it
        checks the cross-site request token. A call from the page carries the
        cookie. The token comes from the page head at call time, so a page that
        opened after the take still sends a valid token.
    """

    PATH: ClassVar[str] = "/api/sites/{site_id}/lock"  # `contracts/site-lock.md` fixes this path.
    CSRF_SELECTOR: ClassVar[str] = 'meta[name="csrf-token"]'  # `layout.html` publishes the token in the page head.
    # WHY: One script serves the take and the release, because both calls need the
    # browser session cookie and the cross-site request token of the same page.
    SCRIPT: ClassVar[str] = """async ({path, token, method, body}) => {
    const response = await fetch(path, {
        method: method,
        credentials: "same-origin",
        headers: {"X-CSRFToken": token, "Content-Type": "application/json"},
        body: body
    });
    return {ok: response.ok, status: response.status, text: await response.text()};
}"""

    @classmethod
    def send(cls, page: Any, site_id: str, method: str, body: str) -> tuple[str, int, str]:
        """Send one lock call, and return the path, the status, and the body text.

        Args:
            page: The Playwright page object that holds the operator session.
            site_id: The site that the call names.
            method: `POST` to take the lock, or `DELETE` to release it.
            body: The request body text.

        Returns:
            The path of the call, the status of the answer, and the body text.
        """
        path = cls.PATH.format(site_id=site_id)  # Build the one path that the contract fixes.
        token = str(page.locator(cls.CSRF_SELECTOR).get_attribute("content") or "")  # An empty token still refuses.
        logger.info("Send a %s lock call from the browser page", method)  # Log before the call.
        arguments = {"path": path, "token": token, "method": method, "body": body}  # The four values of the script.
        answer = page.evaluate(cls.SCRIPT, arguments)  # The browser sends the call with its session cookie.
        status = int(answer.get("status", 0))  # The status decides each answer.
        logger.debug("The %s lock call answered status %s", method, status)  # Log the status, never a token.
        return path, status, str(answer.get("text", ""))  # The caller names the call in each failure.


@dataclass(frozen=True, eq=False)
class LockHold:  # One site lock that one page took.
    """Hold the page, the site, and the token of one take, and release that lock.

    Why:
        The class compares by identity, so the record removes the exact hold that
        a test releases.
    """

    page: Any  # The page that holds the session of the take.
    site_id: str  # The site that the lock covers.
    token: str  # The token that the release must send back.

    OK_STATUS: ClassVar[int] = 200  # `select.free_site_lock` answers 200 for a release.
    RELEASED_FIELD: ClassVar[str] = "released"  # The one field of the release answer.

    def release(self) -> None:
        """Release this lock, and fail when the portal does not report the release.

        Raises:
            AssertionError: The call did not run, the portal refused the release,
                or the answer did not report the release.
        """
        logger.info("Release the site lock of one site")  # Log before the release.
        try:  # A closed page and a lost browser raise here.
            path, status, text = LockCall.send(
                self.page, self.site_id, "DELETE", json.dumps({"lock_token": self.token})
            )
        except Exception as failure:  # Each fault of the call leaves the lock, so each fault must fail.
            raise AssertionError(  # Keep the fault as the cause, so the report shows the error of the browser.
                f"The release of the site {self.site_id} did not run, so the site keeps its lock. Cause: {failure}"
            ) from failure
        if status != self.OK_STATUS:  # A refusal leaves the lock for the next test.
            raise AssertionError(
                f"DELETE {path} answered {status}, so the site keeps its lock. The body reads: {text!r}"
            )
        body = AnswerBody.read(f"DELETE {path}", status, text)  # A 200 must carry a JSON object.
        if body.get(self.RELEASED_FIELD) is not True:  # Only `{"released": true}` proves a free site.
            raise AssertionError(
                f"DELETE {path} answered {status} and did not report the release. The body reads: {text!r}"
            )
        logger.debug("The portal released the site lock")  # Log after the release.


class HeldSiteLocks:  # Take, release, and free each site lock of one browser test.
    """Record each site lock of one browser test, and free each lock that remains after the test.

    Why:
        Issue #3508. A teardown that only logs a failed release hides a leak, so
        the next test meets a held site. `release_all` tries each hold, newest
        first, and it fails after the last try. One fault therefore never leaves
        a second site held.
    """

    OK_STATUS: ClassVar[int] = 200  # The contract fixes 200 for a grant.

    def __init__(self, page: Any) -> None:
        """Bind the record to the first operator page of the test.

        Args:
            page: The Playwright page object that each call uses when the test names no other page.
        """
        self._page = page  # The default page of each take.
        self._holds: list[LockHold] = []  # A list keeps the order of the takes.

    @property
    def sites(self) -> tuple[str, ...]:
        """Return the site of each hold, in the order of the takes."""
        return tuple(hold.site_id for hold in self._holds)  # A tuple keeps each caller away from the list.

    def take(self, site_id: str, lock_page: Any = None) -> None:
        """Take the lock of one site, and record the hold.

        Args:
            site_id: The site to lock.
            lock_page: The page that holds the operator session. No value uses the first operator page.

        Raises:
            AssertionError: The portal refused the take, an earlier test left the
                lock, or the grant names no token.
        """
        page = self._page if lock_page is None else lock_page  # The session that the release must use too.
        logger.info("Take the site lock of one site for one browser test")  # Log before the take.
        path, status, text = LockCall.send(page, site_id, "POST", "{}")  # A plain take types no word.
        if status != self.OK_STATUS:  # A test that needs the site must stop.
            raise AssertionError(
                f"POST {path} answered {status}, so this test holds no lock of the site. The body reads: {text!r}"
            )
        token = LockTakeAnswer.require_token(path, status, text)  # Issue #3497: a grant must name a fresh lock.
        self._holds.append(LockHold(page, site_id, token))  # The teardown releases this hold.
        logger.debug("The record holds %s site lock(s)", len(self._holds))  # Log after the take.

    def release(self, site_id: str) -> None:
        """Release the newest hold of one site now, and forget the hold.

        Args:
            site_id: The site to free.

        Raises:
            AssertionError: The record holds no lock of the site, or the release failed.
        """
        logger.info("Release one site lock before the test ends")  # Log before the release.
        matches = [hold for hold in self._holds if hold.site_id == site_id]  # Each hold of the site.
        if not matches:  # A release of a site that the test never took is a fault of the test.
            raise AssertionError(f"This test holds no lock of the site {site_id}, so the release frees nothing.")
        self._holds.remove(matches[-1])  # Forget the hold first, so the teardown reports a fault one time only.
        matches[-1].release()  # A refusal fails the test at the step that released.
        logger.debug("The record holds %s site lock(s)", len(self._holds))  # Log after the release.

    def release_all(self) -> None:
        """Release each hold that remains, newest first, and fail after the last try.

        Raises:
            AssertionError: One or more releases failed. The message names each fault.
        """
        logger.info("Free each site lock that the test still holds")  # Log before the teardown.
        faults: list[str] = []  # One sentence for each failed release.
        while self._holds:  # Newest first, the reverse order of the takes.
            hold = self._holds.pop()  # Forget the hold, so a second teardown sends no second release.
            try:  # One fault must not stop the release of another site.
                hold.release()  # Free the site for the next test.
            except AssertionError as failure:  # The release names its own fault.
                faults.append(str(failure))  # Keep the fault for the one failure below.
        logger.debug("The teardown met %s failed release(s)", len(faults))  # Log after the teardown.
        if faults:  # A site keeps its lock, so the run must fail.
            raise AssertionError(
                f"The teardown of issue #3508 could not free {len(faults)} site lock(s). " + " ".join(faults)
            )
