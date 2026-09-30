"""Hold the teardown rules of the multi-site browser journeys of the upgrade portal.

Why:
    Issue #3518. Six browser modules start a multi-site operation on the
    stand-in sites 2222 and 3333. Each journey cancels its operation on the
    progress page at the end of the test. When a step failed before that
    cancel, the operation kept both sites, and a later journey could fail.
    The old teardown of the double-click module read the address of the page
    only. A slow start left the page on the confirmation page, so that
    teardown cancelled nothing.

    `OrgStartAnswer` holds the start rules. `OrgOperationLedger` records the
    id of each operation from the answer of the Start request. `OrgStartTap`
    fetches each Start answer before a page gets it, so no navigation can drop
    the body. `OrgOperationCalls` sends the status reads and the cancels.
    `OrgOperationRelease` ends each live operation of the ledger. It waits for
    the final child state and the end of the phase watch. Each class holds one
    set of decisions, so a direct test proves each decision with no browser.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Build the body of each cancel, and read the body of each Start answer.
import logging  # Record each step of the teardown without a token value.
import re  # Match the address of the progress page.
import time  # Pause between two status reads.
from collections.abc import Callable, Iterable  # The pause is a callable, and the ids come in any iterable.
from typing import Any, ClassVar  # Playwright gives each answer and each page, so their type is Any.
from urllib.parse import urlsplit  # Read the path of each address.

from tests.support.upgrade_portal_e2e.site_lock import AnswerBody  # Issue #3497: read one 200 body.

logger = logging.getLogger(__name__)  # Keep each record of the teardown rules tied to this module.


class OrgStartAnswer:  # Find the operation that one answer of the Start request built.
    """Find the operation that one answer of the Start request built."""

    START_PATH: ClassVar[str] = "/api/org-upgrades"  # The Start route of the confirmation form.
    START_METHOD: ClassVar[str] = "POST"  # The Start request posts the confirmed plan.
    OK_STATUS: ClassVar[int] = 200  # Only a 200 answer built an operation.
    NEXT_FIELD: ClassVar[str] = "next"  # The field of the answer that names the progress page.
    JOB_PATH: ClassVar[re.Pattern[str]] = re.compile(r"/upgrade/org/jobs/(org-run-[0-9a-f]+)")  # One progress page.

    @classmethod
    def is_start(cls, method: str, url: str, status: int) -> bool:
        """Report whether one answer is the 200 answer of the Start request.

        Args:
            method: The method of the request.
            url: The address of the request.
            status: The status of the answer.

        Returns:
            True only for a 200 answer to `POST /api/org-upgrades`.
        """
        is_post = method.upper() == cls.START_METHOD  # A read builds nothing.
        return is_post and urlsplit(url).path == cls.START_PATH and status == cls.OK_STATUS  # A refusal builds nothing.

    @classmethod
    def operation_id(cls, text: str) -> str | None:
        """Return the id that the field `next` of one Start answer names.

        Args:
            text: The body text of the answer.

        Returns:
            The id of the operation, or None when the body names no progress page.
        """
        try:  # The parser raises its own error for text that is not JSON.
            body = json.loads(text)  # The Start route answers `{"next": "/upgrade/org/jobs/<id>"}`.
        except json.JSONDecodeError:  # A proxy page or an empty body names no operation.
            return None  # The caller logs the miss.
        target = body.get(cls.NEXT_FIELD) if isinstance(body, dict) else None  # Only an object holds the field.
        return cls.page_operation(target) if isinstance(target, str) else None  # The field must hold an address.

    @classmethod
    def page_operation(cls, url: str) -> str | None:
        """Return the id that the address of one progress page names.

        Args:
            url: The address of a page, or the path of a page.

        Returns:
            The id of the operation, or None for each other page.
        """
        match = cls.JOB_PATH.fullmatch(urlsplit(url).path)  # The whole path must be one progress page.
        return match.group(1) if match else None  # The first group holds the id.


class OrgOperationLedger:  # Hold each multi-site operation that one browser test started.
    """Hold the id of each multi-site operation that one browser test started, in the order of the start."""

    def __init__(self) -> None:
        """Start with no operation."""
        self._operations: list[str] = []  # A list keeps the order of the start.

    @property
    def operations(self) -> tuple[str, ...]:
        """Return each recorded id, in the order of the start."""
        return tuple(self._operations)  # A tuple keeps each caller away from the list of the ledger.

    def record(self, operation_id: str) -> None:
        """Record one operation that the test started.

        Args:
            operation_id: The id of the operation.

        Raises:
            ValueError: The id is empty, so no teardown could end the operation.
        """
        logger.info("Record one operation in the operation ledger")  # Log before the record.
        if not operation_id.strip():  # An empty id names no operation.
            raise ValueError("The operation ledger needs the id of an operation.")  # Refuse the record at once.
        if operation_id not in self._operations:  # The page source can find the same operation again.
            self._operations.append(operation_id)  # The teardown then ends the operation one time only.
        logger.debug("The operation ledger holds %s operation(s)", len(self._operations))  # Log after the record.

    def record_page(self, url: str) -> str | None:
        """Record the operation of the progress page that the page of the test shows.

        Why:
            The tap misses a start when its fetch fails. The page source still
            finds the operation of a progress page (FR-002).

        Args:
            url: The address that the page shows.

        Returns:
            The id of the operation, or None for each other page.
        """
        logger.info("Read the operation of the page that the test shows")  # Log before the read.
        operation_id = OrgStartAnswer.page_operation(url)  # Only a progress page names an operation.
        if operation_id is not None:  # The page shows one operation.
            self.record(operation_id)  # The teardown ends this operation too.
        logger.debug("The page named %s operation", "one" if operation_id else "no")  # Log after the read.
        return operation_id  # A direct test compares the id.

    def observe(self, method: str, answer: Any) -> None:
        """Record the operation of one Start answer. The tap calls this for each answer that it fetches.

        Why:
            A fault that escapes a route handler fails the next Playwright call
            of the test, at a step that has no fault. So the ledger catches each
            fault of the body read (FR-006).

        Args:
            method: The method of the request. A fetched answer names no request.
            answer: One fetched answer, with its address, its status, and its body text.
        """
        if not OrgStartAnswer.is_start(method, answer.url, answer.status):  # A refusal built no operation.
            return  # Return at once, so a refusal costs no body read.
        logger.info("Read the answer of one Start request")  # Log before the body read.
        try:  # The read fails when the test closed the context first.
            text = str(answer.text())  # The body names the progress page.
        except Exception as fault:  # Keep broad: Playwright raises its own error class, and no fault may escape.
            logger.warning(  # The page source of FR-002 can still find the operation.
                "The ledger could not read the body of a Start answer (%s: %s), so it records nothing",
                type(fault).__name__,
                fault,
            )
            return  # Record nothing.
        operation_id = OrgStartAnswer.operation_id(text)  # The id that the field `next` names.
        if operation_id is None:  # The body names no progress page of a multi-site operation.
            logger.warning("The Start answer names no progress page, so the ledger records nothing")  # Tell the reader.
            return  # Record nothing.
        self.record(operation_id)  # The teardown ends this operation.
        logger.debug("The ledger recorded the operation of one Start answer")  # Log after the record.


class OrgStartTap:  # Fetch each Start answer of one browser context before a page gets it.
    """Fetch each Start answer of one browser context, record its operation, and give the page the same answer.

    Why:
        Issue #3518. The first design read the body in a handler of the answer
        event. The page script opens the progress page at once, and the browser
        then drops the body of the old document. The first browser proof lost
        the body of 2 of 2 starts. A route of the context fetches the answer
        first, so the ledger reads the body from memory. A page route still
        takes precedence, so a test can hold the Start request itself.
    """

    ROUTE: ClassVar[str] = "**/api/org-upgrades"  # The glob matches the whole address, so a status path is out.
    NO_REDIRECT: ClassVar[int] = 0  # The page follows a redirect itself, so the fetch keeps the redirect.
    FETCH_TIMEOUT_MS: ClassVar[float] = 60000.0  # Above the 45-second bound of the start step, so the step fails first.

    def __init__(self, ledger: OrgOperationLedger) -> None:
        """Bind the tap to the ledger of one browser test.

        Args:
            ledger: The ledger that records each operation of the test.
        """
        self._ledger = ledger  # Each fetched Start answer goes to this ledger.

    def pass_start(self, route: Any) -> None:
        """Fetch one Start answer, record its operation, and give the page the same answer.

        Args:
            route: The route of one request to the Start path, from any page of the context.
        """
        method = str(route.request.method)  # Only a post builds an operation.
        if method.upper() != OrgStartAnswer.START_METHOD:  # A read of the path builds nothing.
            route.fallback()  # The browser sends the read as usual.
            return  # The tap records nothing.
        logger.info("Fetch the answer of one Start request for the operation ledger")  # Log before the fetch.
        try:  # The fetch fails when the portal stops, or when the test closes the context first.
            answer = route.fetch(max_redirects=self.NO_REDIRECT, timeout=self.FETCH_TIMEOUT_MS)  # The real answer.
        except Exception as fault:  # Keep broad: Playwright raises its own error class, and no fault may escape.
            self._abort(route, fault)  # The page sees a failed request.
            return  # The ledger has no answer to read.
        self._ledger.observe(method, answer)  # The ledger reads the body from memory, so no page can drop it.
        self._forward(route, answer)  # The page script gets the same status, headers, and body.
        logger.debug("The tap gave the page the Start answer with HTTP %s", answer.status)  # Log after the step.

    @staticmethod
    def _abort(route: Any, fault: Exception) -> None:
        """Stop the page request after a failed fetch.

        Why:
            The portal can accept a start after the fetch stopped its wait. A
            second request could then start a second operation, so the tap
            stops the request instead of sending it again.
        """
        logger.warning(  # The page source of FR-002 can still find the operation.
            "The tap could not fetch a Start answer (%s: %s), so it stops the page request",
            type(fault).__name__,
            fault,
        )
        try:  # The page can close before the tap stops the request.
            route.abort()  # The page script reports a failed request.
        except Exception as closed:  # Keep broad: no fault may escape the route handler.
            logger.warning("The tap could not stop the page request (%s)", type(closed).__name__)  # Tell the reader.

    @staticmethod
    def _forward(route: Any, answer: Any) -> None:
        """Give the fetched answer to the page."""
        try:  # The page can close before the answer arrives.
            route.fulfill(response=answer)  # The same status, headers, and body.
        except Exception as fault:  # Keep broad: no fault may escape the route handler.
            logger.warning(  # The ledger already holds the operation, so the teardown still ends it.
                "The tap could not give the Start answer to the page (%s: %s)",
                type(fault).__name__,
                fault,
            )


class OrgOperationCalls:  # Send the status reads and the cancels of the teardown.
    """Send the status reads and the cancels of the teardown through one browser context.

    Why:
        The status route and the cancel route read the owner from the session
        of the browser. The request source of the context shares the cookies of
        each page, so each call reaches the operation of the same operator. A
        read needs no token. A cancel needs the CSRF token, so the calls read
        the token one time, from a new page, and only when a cancel is due.
    """

    STATUS_PATH: ClassVar[str] = "/api/org-upgrades/{operation_id}"  # The status route of one operation.
    CANCEL_PATH: ClassVar[str] = "/api/org-upgrades/{operation_id}/cancel"  # The cancel route of one operation.
    TOKEN_PAGE: ClassVar[str] = "/history"  # A portal page that publishes the token and takes no site lock.
    TOKEN_SCRIPT: ClassVar[str] = "() => document.querySelector('meta[name=\"csrf-token\"]')?.content || ''"
    CANCEL_WORD: ClassVar[str] = "CANCEL"  # The typed confirmation word of the cancel route.
    JSON_TYPE: ClassVar[str] = "application/json"  # Each call sends and asks for JSON.
    OK_STATUS: ClassVar[int] = 200  # A read and a cancel answer 200 on success.
    CONFLICT_STATUS: ClassVar[int] = 409  # The cancel route answers 409 for a final operation.
    TIMEOUT_MS: ClassVar[float] = 30000.0  # One call reaches the process-owned store of the test portal.

    def __init__(self, context: Any) -> None:
        """Bind the calls to one browser context.

        Args:
            context: The browser context of the test. Its `request` source sends each call.
        """
        self._context = context  # The context opens the token page and sends each call.
        self._token = ""  # The first cancel reads the token.

    def read_status(self, operation_id: str) -> dict[str, Any]:
        """Return the fields of one status answer.

        Args:
            operation_id: The id of the operation.

        Returns:
            The fields of the answer. The route also frees the sites of a settled operation.

        Raises:
            AssertionError: The route refused the read, or the body holds no JSON object.
        """
        path = self.STATUS_PATH.format(operation_id=operation_id)  # The status route of the operation.
        answer = self._fetch("get", path, {"Accept": self.JSON_TYPE}, None)  # A read sends no body and no token.
        return self._require_ok("get", path, answer)  # A refusal fails the teardown.

    def cancel(self, operation_id: str) -> Any:
        """Send one cancel, and return a 200 answer or a 409 answer.

        Args:
            operation_id: The id of the operation.

        Returns:
            The answer. A 409 can come from an operation that ended first, so the caller decides.

        Raises:
            AssertionError: The route answered another refusal, or a 200 body holds no JSON object.
        """
        path = self.CANCEL_PATH.format(operation_id=operation_id)  # The cancel route of the operation.
        body = json.dumps({"confirmation": self.CANCEL_WORD})  # The route reads the typed word.
        answer = self._fetch("post", path, self._write_headers(), body)  # The cancel needs the token.
        if answer.status != self.CONFLICT_STATUS:  # Each answer other than 409 must be a 200 with a JSON object.
            self._require_ok("post", path, answer)  # A refusal fails the teardown.
        return answer  # The caller reads the status.

    def _write_headers(self) -> dict[str, str]:
        """Return the headers of one write, and read the token on the first write."""
        if not self._token:  # No cancel went out yet.
            self._token = self._read_token()  # One page load for the whole teardown.
        return {"X-CSRFToken": self._token, "Content-Type": self.JSON_TYPE, "Accept": self.JSON_TYPE}  # JSON, no page.

    def _read_token(self) -> str:
        """Read the CSRF token of the session from a new page of the context.

        Why:
            The page of the test can be closed, or it can be in the middle of a
            navigation after a failed step. A new page avoids both cases.
        """
        logger.info("Read the CSRF token of the session from a new page")  # Log before the page load.
        page = self._context.new_page()  # A new page shares the session cookie of the test.
        try:  # Close the page also when the load fails.
            page.goto(self.TOKEN_PAGE, wait_until="domcontentloaded", timeout=self.TIMEOUT_MS)  # The head has the tag.
            token = str(page.evaluate(self.TOKEN_SCRIPT)).strip()  # An empty text means no tag.
        finally:  # A page left open would hold a browser target.
            page.close()  # Close the page of the token.
        if not token:  # No cancel can pass the cross-site request check.
            raise AssertionError(
                f"The teardown of issue #3518 found no CSRF token on the page {self.TOKEN_PAGE}, "
                "so it cannot send a cancel."
            )
        logger.debug("The new page held a CSRF token")  # Log after the read, without the value.
        return token  # Each later cancel reuses the token.

    def _fetch(self, method: str, path: str, headers: dict[str, str], data: str | None) -> Any:
        """Send one call through the request source of the browser context."""
        logger.info("Send one %s call of the teardown", method.upper())  # Log before the call.
        answer = self._context.request.fetch(  # The request source shares the cookies of the context.
            path, method=method, headers=headers, data=data, timeout=self.TIMEOUT_MS
        )
        logger.debug("The %s call of the teardown answered %s", method.upper(), answer.status)  # Log the status only.
        return answer  # The caller decides from the status.

    @classmethod
    def _require_ok(cls, method: str, path: str, answer: Any) -> dict[str, Any]:
        """Return the JSON object of a 200 answer, or fail with the call, the status, and the body."""
        call = f"{method.upper()} {path}"  # Each message names the call, so the reader finds the route.
        text = str(answer.text())  # The body names the refusal code.
        if answer.status != cls.OK_STATUS:  # A refusal leaves an operation behind.
            raise AssertionError(  # Pytest reports a teardown error apart from the result of the test.
                f"The teardown of issue #3518 sent {call}, and the portal answered {answer.status}. "
                f"The body reads: {text!r}"
            )
        return AnswerBody.read(call, answer.status, text)  # A 200 must carry a JSON object.


class OrgOperationRelease:  # End each live operation of one browser test.
    """End each live operation of one browser test, and wait until the portal reports a final state.

    Why:
        The portal frees the sites of an operation only after each child job
        settles and the phase watch ends. The status route checks both states,
        so the reads after a cancel also free the sites. The fields
        `cancel_allowed` and `phase_active` tell whether the teardown must wait.
    """

    LIVE_FIELD: ClassVar[str] = "cancel_allowed"  # True while the operator can cancel the operation.
    PHASE_ACTIVE_FIELD: ClassVar[str] = "phase_active"  # True while the watch or post-check stage still runs.
    STATE_FIELD: ClassVar[str] = "status"  # The state of the operation, which each message names.
    READ_TRIES: ClassVar[int] = 30  # The bound on the status reads after one cancel.
    READ_PAUSE_S: ClassVar[float] = 0.5  # The pause between two status reads.

    def __init__(self, calls: OrgOperationCalls, pause: Callable[[float], object] = time.sleep) -> None:
        """Bind the release to the calls of one browser context.

        Args:
            calls: The status reads and the cancels of one browser context.
            pause: The wait between two status reads. A direct test gives a recorder.
        """
        self._calls = calls  # Each call reaches the portal of the test.
        self._pause = pause  # The real teardown sleeps.

    @classmethod
    def end_for(cls, page: Any, ledger: OrgOperationLedger) -> int:
        """End each live operation that the ledger or the page of one test names.

        Args:
            page: The page of the test. The page can be closed.
            ledger: The ledger of the browser context of the test.

        Returns:
            The count of operations that needed a cancel.

        Raises:
            AssertionError: A call failed, or an operation stayed live after the bound.
        """
        logger.info("End each live multi-site operation of one browser test")  # Log before the teardown.
        if not page.is_closed():  # A closed page shows no progress page.
            ledger.record_page(page.url)  # FR-002: the operation of the progress page counts too.
        if not ledger.operations:  # FR-009: the test started no operation.
            logger.debug("The ledger holds no operation, so the teardown sends no call")  # Log the skip.
            return 0  # No call.
        ended = cls(OrgOperationCalls(page.context)).end_operations(ledger.operations)  # End each operation.
        logger.debug("The teardown of the browser test cancelled %s operation(s)", ended)  # Log after the teardown.
        return ended  # The journey of the teardown compares the count.

    def end_operations(self, operation_ids: Iterable[str]) -> int:
        """Cancel each live operation, and return the count of cancels.

        Why:
            A fault of one operation must not leave the next operation live.
            So the release tries each operation, and then it reports each fault.

        Args:
            operation_ids: The ids of the operations, in the order of the start.

        Returns:
            The count of operations that needed a cancel.

        Raises:
            AssertionError: One or more operations failed. The message names each fault.
        """
        logger.info("End each live operation of the ledger")  # Log before the loop.
        ended, faults = 0, []  # No cancel and no fault yet.
        for operation_id in operation_ids:  # The ledger gives the order of the start.
            try:  # Keep each fault, and go on to the next operation.
                ended += self._end_one(operation_id)  # One or zero cancels.
            except AssertionError as fault:  # A refused call or a live operation.
                faults.append(str(fault))  # The final message names each fault.
        if faults:  # One or more operations may still hold a site.
            raise AssertionError(" ".join(faults))  # Pytest reports a teardown error.
        logger.debug("The teardown cancelled %s operation(s)", ended)  # Log after the loop.
        return ended  # The caller logs the count.

    def _end_one(self, operation_id: str) -> int:
        """End one operation, and return 1 for a cancel or 0 for no cancel."""
        body = self._calls.read_status(operation_id)  # Read both the child state and the phase watch state.
        if not self._is_live(operation_id, body):  # The test ended the operation and the phase watch.
            logger.debug("The operation is final, so it needs no cancel")  # SC-004: one read only.
            return 0  # No cancel.
        if not self._cancel_allowed(operation_id, body):  # The child jobs ended before the phase watch.
            self._wait_until_final(operation_id)  # Wait for the post-check stage and the lock release.
            return 0  # No cancel was necessary.
        answer = self._calls.cancel(operation_id)  # The operation holds both stand-in sites.
        if answer.status == OrgOperationCalls.CONFLICT_STATUS:  # The operation can have ended first.
            self._accept_race(operation_id, str(answer.text()))  # FR-005: read the state again.
            return 0  # The operation ended with no cancel of the teardown.
        self._wait_until_final(operation_id)  # The reads also free the sites.
        return 1  # One cancel.

    def _accept_race(self, operation_id: str, refusal: str) -> None:
        """Accept a 409 only when the next status read shows a final state."""
        body = self._calls.read_status(operation_id)  # One read after the 409.
        if self._cancel_allowed(operation_id, body):  # A replay or a damaged state, not a race.
            raise AssertionError(
                f"The teardown of issue #3518 sent the cancel of {operation_id}, and the portal answered 409. "
                f"The operation stays in the state {body.get(self.STATE_FIELD)!r}. The body reads: {refusal!r}"
            )
        if self._phase_active(operation_id, body):  # The child jobs ended before the post-check stage.
            self._wait_until_final(operation_id)  # Keep the sites held until the phase watch releases them.
        logger.debug("The operation ended before the cancel, so the 409 is a race")  # Log the accepted race.

    def _wait_until_final(self, operation_id: str) -> None:
        """Read the status until the operation is final, or fail after the bound."""
        state: object = None  # No live read yet.
        for _ in range(self.READ_TRIES):  # The stand-in cloud cancels each child job at once.
            body = self._calls.read_status(operation_id)  # The read checks each child job.
            if not self._is_live(operation_id, body):  # The operation is final, and its sites are free.
                logger.debug("The operation reached a final state after the cancel")  # Log the end.
                return  # The next test can use both sites.
            state = body.get(self.STATE_FIELD)  # The message names the last live state.
            self._pause(self.READ_PAUSE_S)  # Give the child jobs time to settle.
        raise AssertionError(
            f"The teardown of issue #3518 cancelled {operation_id}, and the operation stayed in the state "
            f"{state!r} after {self.READ_TRIES} status reads."
        )

    @classmethod
    def _is_live(cls, operation_id: str, body: dict[str, Any]) -> bool:
        """Return True while a child job or the phase watch still runs."""
        return cls._cancel_allowed(operation_id, body) or cls._phase_active(operation_id, body)  # Either scope.

    @classmethod
    def _cancel_allowed(cls, operation_id: str, body: dict[str, Any]) -> bool:
        """Return the boolean cancel flag of one status answer."""
        flag = body.get(cls.LIVE_FIELD)  # The progress page reads the same field.
        if not isinstance(flag, bool):  # A wrong answer must not pass as a final state.
            raise AssertionError(
                f"The teardown of issue #3518 read the status of {operation_id}, and the answer holds no "
                f"boolean field {cls.LIVE_FIELD!r}. The field holds {flag!r}."
            )
        return flag  # True means that one child job can still accept a cancel.

    @classmethod
    def _phase_active(cls, operation_id: str, body: dict[str, Any]) -> bool:
        """Return the boolean phase-watch flag of one status answer."""
        flag = body.get(cls.PHASE_ACTIVE_FIELD, False)  # An earlier portal answer has no phase watch.
        if not isinstance(flag, bool):  # A wrong answer must not pass as a released lock scope.
            raise AssertionError(
                f"The teardown of issue #3518 read the status of {operation_id}, and the answer holds no "
                f"boolean field {cls.PHASE_ACTIVE_FIELD!r}. The field holds {flag!r}."
            )
        return flag  # True means that the phase watch or the post-check stage still needs the site.
