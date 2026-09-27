"""Hold the site lock rules of the browser tests of the upgrade portal.

Why:
    Issue #3497. The run-control tests of `test_existing.py` built runs on the
    stand-in site, and no test ended them or released the site lock. The
    fixture `held_site` of `test_two_operators.py` then took the lock of the
    same site with the same operator. Within 300 seconds, the take answered
    `resume`, and no test saw the leak. After 300 seconds, the take answered
    400, and 18 tests reported a skip. Pytest counts a skip as a pass.

    `RunLedger` records each run that one test built. `AnswerBody` reads the
    body of each 200 answer. `SiteRelease` ends each live run of the ledger,
    and then it frees the site lock. `LockTakeAnswer` turns one answer of the
    lock take into a held lock, a skip, or a failure. Each class holds one
    decision, so a direct test proves each decision with no browser and no
    portal.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Build each request body, and read each answer body.
import logging  # Record each step of the teardown without a token value.
from collections.abc import Iterable  # The teardown accepts the runs of a ledger in any iterable.
from typing import Any, ClassVar  # Playwright gives the request source and each answer, so their type is Any.
from urllib.parse import parse_qs, urlsplit  # Read the run key from the address of the capture page.

import pytest  # Report a workstation with no lock store as a skip.

from src.upgrade_portal.runtime.lock import LockState  # The grant states that the lock route answers.
from src.upgrade_portal.runtime.runs import RunStateMachine  # The final states of the run model.

logger = logging.getLogger(__name__)  # Keep each record of the site lock rules tied to this module.


class RunLedger:  # Hold each run that one browser test built.
    """Hold the key of each run that one browser test built, in the order of the record."""

    RUN_FIELD: ClassVar[str] = "run_id"  # The query field that names the run on the capture page.

    def __init__(self) -> None:
        """Start with no run."""
        self._runs: list[str] = []  # A list keeps the order in which the test built the runs.

    @property
    def runs(self) -> tuple[str, ...]:
        """Return each recorded run key, in the order of the record."""
        return tuple(self._runs)  # A tuple keeps each caller away from the list of the ledger.

    def record(self, run_id: str) -> None:
        """Record one run that the test built.

        Args:
            run_id: The key of the run.

        Raises:
            ValueError: The key is empty, so no teardown could end the run.
        """
        logger.info("Record one run in the run ledger")  # Log before the record.
        if not run_id.strip():  # An empty key names no run.
            raise ValueError("The run ledger needs the key of a run.")  # Refuse the record at once.
        if run_id not in self._runs:  # A test can meet the same run two times.
            self._runs.append(run_id)  # The teardown then ends the run one time only.
        logger.debug("The run ledger holds %s run(s)", len(self._runs))  # Log after the record.

    def record_from_url(self, url: str) -> str:
        """Record the run that the query of one address names.

        Why:
            The retry control opens the capture page of the new run. The address
            of that page is the one place where a browser test can read the key.

        Args:
            url: The address of the page.

        Returns:
            The run key.

        Raises:
            AssertionError: The address names no run, so the teardown cannot end the retry run.
        """
        logger.info("Read one run key from the address of a page")  # Log before the read.
        values = parse_qs(urlsplit(url).query).get(self.RUN_FIELD, [])  # A query can repeat a field.
        run_id = values[0].strip() if values else ""  # The capture page names one run.
        if not run_id:  # The page names no run, so the retry run stays unknown.
            raise AssertionError(f"The address {url!r} names no run, so the teardown cannot end the retry run.")
        self.record(run_id)  # The teardown ends this run too.
        logger.debug("The address named one run")  # Log after the read.
        return run_id  # The caller can open the run page.


class AnswerBody:  # Read the body of one 200 answer as a JSON object, or fail with the call and the status.
    """Read the body of one 200 answer as a JSON object.

    Why:
        A proxy or a broken route can answer 200 with an empty body or with an
        HTML page. The JSON parser then raises an error that names no call. This
        class names the call, the status, and the body in each failure, so the
        reader can find the route that answered.
    """

    @staticmethod
    def read(call: str, status: int, text: str) -> dict[str, Any]:
        """Return the fields of one body that holds a JSON object.

        Args:
            call: The method and the path of the call, which each message names.
            status: The status of the answer, which each message names.
            text: The body text of the answer.

        Returns:
            The fields of the object.

        Raises:
            AssertionError: The body is empty, is not JSON, or holds JSON that is not an object.
        """
        logger.info("Read the body of one answer as a JSON object")  # Log before the parse.
        if not text.strip():  # An empty body names no field, and the parser error would not name the call.
            raise AssertionError(f"{call} answered {status} with an empty body, so the answer names no field.")
        try:  # The parser raises its own error for text that is not JSON.
            body = json.loads(text)  # The portal answers JSON text for each 200.
        except json.JSONDecodeError as failure:  # A proxy page or a broken route answered text that is not JSON.
            raise AssertionError(  # Keep the parser error as the cause, so the report shows the position.
                f"{call} answered {status} with a body that is not JSON. The body reads: {text!r}"
            ) from failure
        if not isinstance(body, dict):  # A list, a number, a string, or null holds no named field.
            raise AssertionError(f"{call} answered {status} with JSON that is not an object. The body reads: {text!r}")
        logger.debug("The body of the answer holds %s field(s)", len(body))  # Log the field count, not a value.
        return body  # The caller reads the fields that it needs.


class SiteRelease:  # End each live run of one test, and then free the site lock of that test.
    """End each live run that one browser test built, and then free the site lock of that test.

    Why:
        The release route reads the lock record from the session of the
        browser. The teardown therefore uses the request source of the same
        browser context. The take sends the word `continue`, because the lock
        module asks for that word after the quiet time of 300 seconds.
    """

    FINAL_STATES: ClassVar[frozenset[str]] = frozenset(  # The run model names each final state, so no copy drifts.
        state.value for state in RunStateMachine.TERMINAL
    )
    STATUS_PATH: ClassVar[str] = "/api/runs/{run_id}/status"  # `contracts/http-api.md` fixes this path.
    CANCEL_PATH: ClassVar[str] = "/api/runs/{run_id}/cancel"  # `contracts/http-api.md` fixes this path.
    LOCK_PATH: ClassVar[str] = "/api/sites/{site_id}/lock"  # `contracts/site-lock.md` fixes this path.
    CONTINUE_WORD: ClassVar[str] = "continue"  # The word that a quiet lock of the same operator needs.
    OK_STATUS: ClassVar[int] = 200  # Each step of the teardown must answer 200.
    NOT_FOUND_STATUS: ClassVar[int] = 404  # The status route answers 404 for a run that the store does not hold.
    TIMEOUT_MS: ClassVar[float] = 30000.0  # One call reaches the process-owned store of the test portal.

    def __init__(self, requests: Any, csrf_token: str) -> None:
        """Bind the teardown to the request source and the token of one page.

        Args:
            requests: The request context of the page. It shares the cookies of
                the browser context, and its `fetch` method sends each call.
            csrf_token: The token for the cross-site request check. The page publishes it.
        """
        self._requests = requests  # Each call carries the session cookie of the browser context.
        self._headers = {"X-CSRFToken": csrf_token, "Content-Type": "application/json"}  # Each write needs both.

    def end_runs(self, runs: Iterable[str]) -> int:
        """Cancel each run that is not final, and return the count of cancels.

        Args:
            runs: The keys of the runs that the test built.

        Returns:
            The count of runs that needed a cancel.

        Raises:
            AssertionError: A status read or a cancel answered a refusal, or a 200 held no JSON object.
        """
        logger.info("End each live run that one browser test built")  # Log before the teardown step.
        ended = 0  # No run needed a cancel yet.
        for run_id in runs:  # The ledger gives the runs in the order of the record.
            if self._is_live(run_id):  # A final run, or a run that the store does not hold, needs no cancel.
                self._send("post", self.CANCEL_PATH.format(run_id=run_id), {})  # The cancel must answer 200.
                ended += 1  # Count the cancel for the log and for the caller.
        logger.debug("The teardown ended %s run(s)", ended)  # Log after the teardown step.
        return ended  # A direct test compares the count.

    def free_site(self, site_id: str) -> None:
        """Take the site lock with the word `continue`, and then release the lock.

        Args:
            site_id: The site that the test used.

        Raises:
            AssertionError: The take or the release answered a refusal, or a 200 held no JSON object.
        """
        logger.info("Free the site lock that one browser test held")  # Log before the teardown step.
        path = self.LOCK_PATH.format(site_id=site_id)  # One path serves the take and the release.
        grant = self._send("post", path, {"confirm": self.CONTINUE_WORD})  # The same operator takes the lock back.
        token = str(grant.get("lock_token", ""))  # The release sends back the token of the take.
        self._send("delete", path, {"lock_token": token})  # Free the site for the next test.
        logger.debug("The teardown freed the site lock")  # Log after the teardown step.

    def _is_live(self, run_id: str) -> bool:
        """Report whether one run needs a cancel.

        Args:
            run_id: The key of the run.

        Returns:
            True when the store holds the run and the run is not final.
        """
        path = self.STATUS_PATH.format(run_id=run_id)  # The status route of the run.
        answer = self._fetch("get", path, None)  # A read sends no body.
        if answer.status == self.NOT_FOUND_STATUS:  # The store holds no such run, so no run exists to end.
            logger.debug("The store holds no run under the recorded key")  # Log the run that needs no cancel.
            return False  # Move on to the next run.
        state = str(self._require_ok("get", path, answer).get("state", ""))  # The effective state of the run.
        return state not in self.FINAL_STATES  # A final run accepts no cancel.

    def _send(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Send one write, and return the body of a 200 answer."""
        answer = self._fetch(method, path, json.dumps(body))  # Each write sends a JSON body.
        return self._require_ok(method, path, answer)  # A refusal fails the teardown.

    def _fetch(self, method: str, path: str, data: str | None) -> Any:
        """Send one call through the request source of the browser context."""
        logger.info("Send one %s call of the teardown", method.upper())  # Log before the call.
        answer = self._requests.fetch(  # The request source shares the cookies of the browser context.
            path, method=method, headers=self._headers, data=data, timeout=self.TIMEOUT_MS
        )
        logger.debug("The %s call of the teardown answered %s", method.upper(), answer.status)  # Log the status only.
        return answer  # The caller decides from the status.

    @classmethod
    def _require_ok(cls, method: str, path: str, answer: Any) -> dict[str, Any]:
        """Return the JSON object of a 200 answer, or fail with the call, the status, and the body."""
        call = f"{method.upper()} {path}"  # Each message names the call, so the reader finds the route.
        text = str(answer.text())  # The body names the refusal code.
        if answer.status != cls.OK_STATUS:  # A refusal leaves a run or a lock behind.
            raise AssertionError(  # Pytest reports a teardown error apart from the result of the test.
                f"The teardown of issue #3497 sent {call}, and the portal answered "
                f"{answer.status}. The body reads: {text!r}"
            )
        return AnswerBody.read(call, answer.status, text)  # A 200 must carry a JSON object.


class LockTakeAnswer:  # Turn one answer of the lock take into a held lock, a skip, or a failure.
    """Decide one answer of the lock take for the fixture `held_site`.

    Why:
        The fixture skipped on each status other than 200. A 400 and a 409 then
        read as a pass, and 18 checks of site isolation did not run. Only a
        workstation with no lock store may skip, and that workstation answers
        503. A grant with the state `resume` means that an earlier test left the
        lock, so that grant fails too.
    """

    OK_STATUS: ClassVar[int] = 200  # The contract fixes 200 for a grant.
    STORE_DOWN_STATUS: ClassVar[int] = 503  # `lock_store_unreachable`, which a workstation with no Redis answers.
    ROUTE_FAULT_STATUSES: ClassVar[frozenset[int]] = frozenset({401, 404})  # No sign-in seam, or no lock route.
    FRESH_STATE: ClassVar[str] = LockState.ACQUIRED.value  # The one state of a site that no test held.
    TOKEN_FIELD: ClassVar[str] = "lock_token"  # `contracts/http-api.md:129` fixes the grant body.
    STATE_FIELD: ClassVar[str] = "state"  # `contracts/http-api.md:129` fixes the grant body.

    @classmethod
    def require_token(cls, path: str, status: int, text: str) -> str:
        """Return the token of a fresh lock, or skip, or fail.

        Args:
            path: The lock path, which each message names.
            status: The status of the answer.
            text: The body text of the answer.

        Returns:
            The token that the release must send back.

        Raises:
            AssertionError: The portal refused the take, an earlier test left the
                lock, the body holds no JSON object, or the grant names no token.
        """
        logger.info("Decide one answer of the lock take")  # Log before the decision.
        if status in cls.ROUTE_FAULT_STATUSES:  # The portal itself is broken, so a skip would hide the fault.
            raise AssertionError(f"{path} answered {status}, so the portal serves no lock route.")
        if status == cls.STORE_DOWN_STATUS:  # A workstation with no lock store describes the workstation.
            pytest.skip(f"{path} answered 503, so the lock store does not answer. The body reads: {text!r}")
        if status != cls.OK_STATUS:  # Each other refusal hides a leak or a fault, so it must fail.
            raise AssertionError(  # A skip here hid 18 tests before issue #3497.
                f"{path} answered {status}, so the first operator holds no lock. The body reads: {text!r}"
            )
        return cls._fresh_token(path, AnswerBody.read(f"POST {path}", status, text))  # A grant names a fresh lock.

    @classmethod
    def _fresh_token(cls, path: str, body: dict[str, Any]) -> str:
        """Return the token of a fresh grant, or fail when an earlier test left the lock."""
        state = str(body.get(cls.STATE_FIELD, ""))  # One of `acquired`, `resume`, or `takeover`.
        if state != cls.FRESH_STATE:  # The site was not free, so this test would share the lock of another test.
            raise AssertionError(  # Name the leak, so the reader looks for the test that left the lock.
                f"{path} answered the state {state!r}. An earlier test left the lock of this site, "
                "so this test would share that lock. Find the test that took the lock and did not "
                "release it. Issue #3497 records the first case."
            )
        token = str(body.get(cls.TOKEN_FIELD, ""))  # The release must send this value back.
        if not token.strip():  # A grant with no token leaves a lock that no release can free.
            raise AssertionError(f"{path} granted a fresh lock and named no lock token, so no release can free it.")
        logger.debug("The lock take gave a fresh lock")  # Log after the decision.
        return token  # The fixture sends this value back in its release.
