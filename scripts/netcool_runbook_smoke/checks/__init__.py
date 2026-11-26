"""Shared types of the smoke checks: status, result, run context, run stop, and evidence record.

Why: each check reports through one result type.
Each HTTP call passes through one context that applies the run-stop rules.
Each run stop reaches the command as one exception.
The exit codes of the contract therefore come from one place.
"""

from __future__ import annotations  # Postpone annotation evaluation, so the classes can name each other.

from collections import Counter  # Count the statuses of the results for the summary line.
from collections.abc import Callable, Sequence  # Type the session factory and the sequences.
from dataclasses import dataclass, field  # Declare the frozen result and the mutable run context.
from datetime import UTC, datetime  # Stamp the evidence record in UTC.
from enum import Enum, StrEnum  # Name the check statuses and the outcome classes.
from itertools import chain  # Flatten the Retry-After values of the responses, in request order.
from pathlib import Path  # Name the evidence file with the path library.
from typing import TYPE_CHECKING, Any, ClassVar  # Type the evidence values and the class constants.

import structlog  # Structured logging of each request, each run stop, and each evidence write.

from scripts.netcool_runbook_smoke import __version__  # Tool version that the evidence record reports.
from scripts.netcool_runbook_smoke.checks.support import RequestTrail, SessionOpener  # Session and request helpers.
from scripts.netcool_runbook_smoke.client import CallGovernor, CallRecord, PageSet, ReadOnlyMistClient  # Client API.
from scripts.netcool_runbook_smoke.documents import (  # Document readers, the redactor, and the evidence writer.
    EvidenceRedactor,
    EvidenceWriter,
    OpenApiIndex,
    RunbookClaims,
)

if TYPE_CHECKING:  # Run the block for type checkers only, to avoid a cycle.
    from scripts.netcool_runbook_smoke.__main__ import SmokeSettings  # Type only, so the import forms no cycle.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


class CheckStatus(StrEnum):  # Name the five status words that each check reports.
    """Status of a check, or of one part of a check.

    Why: the status of a check is the most severe status of its parts. The member names are the
    contract words, and the roll-up order lives in one method.
    """

    PASS = "PASS"  # nosec B105 - a contract status word, not a password. The check confirmed its fact.
    WARN = "WARN"  # The check confirmed its fact with a limit or a risk.
    INFO = "INFO"  # The check recorded an observation without a judgment.
    FAIL = "FAIL"  # The proof of the check failed.
    SKIP = "SKIP"  # The check, or one part of it, did not run.

    @classmethod
    def most_severe(  # Roll part statuses up, so each check reports one status.
        cls, statuses: Sequence[CheckStatus]
    ) -> CheckStatus:
        """Return the most severe status of the parts, in the order FAIL, WARN, SKIP, INFO, PASS.

        Why: a skipped part stays visible in its check, and an observation never hides a warning.

        Args:
            statuses: Statuses of the parts of one check.

        Returns:
            The most severe status. SKIP when the sequence is empty, because no part ran.
        """
        order = (cls.FAIL, cls.WARN, cls.SKIP, cls.INFO, cls.PASS)  # The roll-up order of the contract.
        for status in order:  # Walk the order from the most severe status.
            if status in statuses:  # The first status that a part holds is the most severe one.
                return status  # Return the roll-up status.
        return cls.SKIP  # No part ran, so the check reports no result.


@dataclass(frozen=True)
class CheckResult:  # Hold one result, so the three outputs cannot disagree.
    """Result of one smoke check, with the fields of one evidence item.

    Why: the console line, the summary count, and the evidence item all read these fields, so the
    three outputs cannot disagree about one check.
    """

    TITLES: ClassVar[dict[str, str]] = {  # Titles of the checks, as the contract names them.
        "SMK-01": "Configuration",
        "SMK-02": "Runbook structure",
        "SMK-03": "Token and organization access",
        "SMK-04": "Hourly request budget",
        "SMK-05": "Definition catalogs",
        "SMK-06": "Organization search",
        "SMK-07": "Organization count",
        "SMK-08": "Site scope",
        "SMK-09": "Filters and limits",
        "SMK-10": "Inventory and webhooks",
    }

    check_id: str  # One of SMK-01 to SMK-10.
    title: str  # Title of the check, from the contract.
    status: CheckStatus  # Roll-up status of the check.
    detail: str  # ASCII text of 200 characters or fewer.
    request_count: int  # Requests that the check used.
    http_statuses: tuple[int, ...]  # HTTP statuses in request order.
    record_count: int | None = None  # Records that the check read, or None when it read none.
    page_count: int | None = None  # Pages that the check read, or None when it read none.
    stop_reason: str | None = None  # Stop reason of a paged query, or None.
    field_names: tuple[str, ...] = ()  # Names of the response fields that the check confirmed.
    header_names: tuple[str, ...] = ()  # Names of the response headers.
    retry_after_seconds: tuple[int | str, ...] = ()  # Retry-After values, as integers or "not numeric".

    @classmethod
    def from_calls(  # Build a result whose request facts come from the attempts.
        cls, check_id: str, status: CheckStatus, detail: str, calls: Sequence[CallRecord]
    ) -> CheckResult:
        """Build the result of a check from its request attempts.

        Why: the request count, the statuses, the header names, and the Retry-After values come from the
        attempts, so each check reports them the same way.

        Args:
            check_id: Identifier of the check, for example SMK-06.
            status: Roll-up status of the check.
            detail: Text that names the result. It is cut to 200 characters.
            calls: Every attempt of the check. An attempt refused by the budget sent no request.

        Returns:
            The result with the request facts of the attempts.
        """
        sent = [  # Drop refused attempts, because they sent no request.
            call for call in calls if call.error_class is not CallRecord.ErrorClass.BUDGET_EXHAUSTED
        ]  # Refused attempts sent nothing.
        return cls(  # Return the result with facts from the sent attempts only.
            check_id=check_id,  # Identifier of the check.
            title=cls.TITLES[check_id],  # Title from the contract table.
            status=status,  # Roll-up status.
            detail=cls._clean(detail),  # ASCII text of at most 200 characters.
            request_count=len(sent),  # Each sent attempt is one counted request.
            http_statuses=tuple(
                call.status_code for call in sent if call.status_code is not None
            ),  # Statuses in order.
            header_names=tuple(sorted({name for call in sent for name in call.header_names})),  # Names only.
            retry_after_seconds=tuple(value for call in sent for value in call.retry_after_seconds),  # In order.
        )

    @classmethod
    def skipped(  # Build a SKIP result, so each check has an evidence item.
        cls, check_id: str, detail: str
    ) -> CheckResult:
        """Build the SKIP result of a check that did not run.

        Why: the evidence record holds ten check items, so each check that did not run still needs one item.

        Args:
            check_id: Identifier of the check that did not run.
            detail: Text of the cause, for example "not run: rate-limit stop" or "runbook not found".

        Returns:
            The SKIP result, with no request.
        """
        return cls(  # Return the SKIP result, since the check sent no request.
            check_id=check_id,  # Identifier of the check that did not run.
            title=cls.TITLES[check_id],  # Title from the contract table.
            status=CheckStatus.SKIP,  # The check did not run.
            detail=cls._clean(detail),  # The cause, in ASCII and at most 200 characters.
            request_count=0,  # No request reached the API for this check.
            http_statuses=(),  # No response exists.
        )

    @staticmethod
    def _clean(detail: str) -> str:  # Make a detail ASCII and within the 200-character limit.
        """Return the detail as ASCII text of at most 200 characters.

        Why: the console and the evidence record accept ASCII only, and the contract limits a detail to 200 characters.

        Args:
            detail: Text that names the result.

        Returns:
            The ASCII text, cut to 200 characters.
        """
        ascii_text = detail.encode(  # Replace non-ASCII text, because the output must be ASCII.
            "ascii", "replace"
        ).decode(
            "ascii"
        )  # Replace each non-ASCII character with a question mark.
        return ascii_text[:200]  # Keep the contract limit.

    def as_evidence(self) -> dict[str, Any]:  # Convert the result to plain JSON values for the evidence.
        """Return the evidence item of this check, with the twelve keys of the contract.

        Why: the evidence writer needs plain values, so each field is converted to a JSON type here.

        Returns:
            The evidence item of this check.
        """
        return {  # Return the twelve evidence keys, in the contract order.
            "check_id": self.check_id,  # Identifier of the check.
            "title": self.title,  # Title of the check.
            "status": self.status.value,  # Status as its contract word.
            "detail": self.detail,  # Text of the result.
            "request_count": self.request_count,  # Requests of the check.
            "http_statuses": list(self.http_statuses),  # Statuses in request order.
            "record_count": self.record_count,  # Records read, or null.
            "page_count": self.page_count,  # Pages read, or null.
            "stop_reason": self.stop_reason,  # Stop reason of a paged query, or null.
            "field_names": list(self.field_names),  # Names only.
            "header_names": list(self.header_names),  # Names only.
            "retry_after_seconds": list(self.retry_after_seconds),  # Integers or "not numeric".
        }

    @classmethod
    def summary_line(  # Build the summary line that counts checks by status.
        cls, results: Sequence[CheckResult], requests_sent: int, budget: int
    ) -> str:
        """Return the summary line of the contract, which counts the checks by status.

        Why: the summary counts the checks that ran, and it counts each skipped check on its own.

        Args:
            results: Results of the run, in check order.
            requests_sent: Requests that the run counted, including the token validation request.
            budget: Accepted request budget of the run.

        Returns:
            The summary line, in the form of the contract.
        """
        counts = Counter(result.status for result in results)  # Number of checks for each status.
        examined = sum(  # Count the checks that ran, because a skip proves nothing.
            counts[status] for status in (CheckStatus.PASS, CheckStatus.WARN, CheckStatus.INFO, CheckStatus.FAIL)
        )
        return (  # Return the summary in the form of the contract.
            f"Checks examined: {examined}. Passed: {counts[CheckStatus.PASS]}. Warnings: {counts[CheckStatus.WARN]}. "
            f"Info: {counts[CheckStatus.INFO]}. Failed: {counts[CheckStatus.FAIL]}. "
            f"Skipped: {counts[CheckStatus.SKIP]}. "
            f"Requests sent: {requests_sent} of {budget}."
        )


class StopRun(Exception):  # Carry each run stop to the command as one exception.
    """End the run with an outcome class before the next check, and carry the result of the check that caused the stop.

    Why: a run stop has priority over a check failure, and the later checks do not run. One exception type carries
    the outcome from the rule that applies it to the command that prints it.
    """

    class Outcome(Enum):  # Name each outcome class with its label and exit code.
        """Outcome class of one run, with its label in the evidence record and its exit code.

        Why: the label and the exit code of an outcome come from one member, so the console line and the
        exit code cannot disagree.
        """

        PASS = ("Pass", 0)  # No check failed and no run stop applied.
        CHECK_FAILURE = ("Check failure", 1)  # One check failed, or no check ran.
        CONFIGURATION_ERROR = ("Configuration error", 2)  # An option, the token, the host, or the access is not valid.
        RATE_LIMIT_STOP = (  # Name the stop for throttling, a low budget, or two timeouts.
            "Rate-limit stop",
            3,
        )  # The API throttled the run, the hourly budget is low, or a second timeout.
        BUDGET_STOP = ("Budget stop", 4)  # The request budget of the run is spent.
        UNSAFE_PAGING_STOP = ("Unsafe paging stop", 5)  # A next link leaves the approved origin, or a page repeats.
        INTERNAL_ERROR = ("Internal error", 6)  # An unexpected exception ended the run.

        @property
        def label(self) -> str:  # Return the label that the console and the evidence print.
            """Return the outcome class name that the console and the evidence record print.

            Why: the contract names each outcome class, and the console line repeats that name.

            Returns:
                The label of the outcome class.
            """
            return str(self.value[0])  # The first item of the value is the label.

        @property
        def exit_code(self) -> int:  # Return the exit code that matches the printed label.
            """Return the exit code of the outcome class, from 0 to 6.

            Why: the process exit code must match the outcome class that the console prints.

            Returns:
                The exit code of the outcome class.
            """
            return int(self.value[1])  # The second item of the value is the exit code.

        @classmethod
        def verdict(  # Decide the outcome of a run that no run stop ended.
            cls, results: Sequence[CheckResult]
        ) -> StopRun.Outcome:
            """Return the outcome of a run that no run stop ended.

            Why: a run passes only when no check failed and at least one check ran. A run with no check
            result cannot prove anything, so it fails.

            Args:
                results: Results of the checks of the run, in check order.

            Returns:
                PASS when at least one check ran and none failed, otherwise CHECK_FAILURE.
            """
            ran = [  # Keep checks with a status, since a skip is not a result.
                result for result in results if result.status is not CheckStatus.SKIP
            ]  # Checks that produced a status.
            failed = [result for result in ran if result.status is CheckStatus.FAIL]  # Checks whose proof failed.
            if not ran or failed:  # No check ran, or one check failed.
                return cls.CHECK_FAILURE  # The run did not pass.
            return cls.PASS  # Every check that ran passed or reported a limit.

    def __init__(  # Store the outcome, cause, and result for the command.
        self, outcome: StopRun.Outcome, message: str, result: CheckResult | None = None
    ) -> None:
        """Keep the outcome, the cause, and the result of the check that caused the stop.

        Why: the command needs the outcome for the exit code, the cause for the log, and the result for the
        evidence record.

        Args:
            outcome: Outcome class that ends the run.
            message: Short ASCII text of the cause. It never holds a token.
            result: Result of the check that caused the stop, or None when the command builds it.
        """
        super().__init__(message)  # Keep the cause as the text of the exception.
        self.outcome: StopRun.Outcome = outcome  # Outcome class that ends the run.
        self.message: str = message  # Cause of the stop, for the command and the log.
        self.result: CheckResult | None = result  # Result of the check that caused the stop.

    @classmethod
    def failed_check(  # Build a stop that names the failed check in the evidence.
        cls, check_id: str, outcome: StopRun.Outcome, message: str
    ) -> StopRun:
        """Build the run stop of a check that failed before any request.

        Why: a configuration check fails with no attempt, so its result has no request facts. The stop carries
        the FAIL result, so the evidence shows which check caused the stop.

        Args:
            check_id: Identifier of the check that failed.
            outcome: Outcome class that ends the run.
            message: Short ASCII text of the cause.

        Returns:
            The run stop, with the FAIL result of the check.
        """
        result = CheckResult.from_calls(check_id, CheckStatus.FAIL, message, ())  # The check made no request.
        return cls(outcome, message, result)  # The stop carries the result for the evidence.

    @classmethod
    def review_calls(  # Stop the run at once, so no check reads a failed attempt.
        cls, attempts: Sequence[CallRecord], timeouts: int
    ) -> None:
        """Raise the run stop of the first attempt that ends the run.

        Why: HTTP 401, a final HTTP 429, a spent budget, and a second timeout end the run at once.
        Each attempt is reviewed before a check reads its data.

        Args:
            attempts: Attempts of one request or one query, in request order.
            timeouts: Timeout count of the whole run, including the attempts before these.

        Raises:
            StopRun: An attempt ends the run.
        """
        for attempt in attempts:  # Review each attempt in request order, so the first stop wins.
            error_class = attempt.error_class  # The error class decides whether this attempt stops the run.
            if error_class is CallRecord.ErrorClass.UNAUTHORIZED:  # The token is rejected, so no data can be read.
                raise cls(  # End the run, because a rejected token cannot read data.
                    cls.Outcome.CONFIGURATION_ERROR, "HTTP 401: the token was rejected by the API"
                )
            if error_class is CallRecord.ErrorClass.BUDGET_EXHAUSTED:  # The budget is spent, so nothing more is sent.
                raise cls(  # End the run, because the budget forbids another request.
                    cls.Outcome.BUDGET_STOP, "the request budget is spent"
                )
            if error_class is CallRecord.ErrorClass.THROTTLED:  # The SDK retried HTTP 429, and the last try failed too.
                raise cls(  # End the run, since the API still throttles after retries.
                    cls.Outcome.RATE_LIMIT_STOP, "HTTP 429 after the SDK retries"
                )
            if (  # Stop on a repeated timeout, a sign of a network fault.
                error_class is CallRecord.ErrorClass.TIMEOUT and timeouts >= 2
            ):  # A second timeout points to the network path.
                raise cls(  # End the run when the timeout count reaches two.
                    cls.Outcome.RATE_LIMIT_STOP, "the second request of the run timed out"
                )

    @classmethod
    def review_page(cls, page: PageSet) -> None:  # Stop the run if paging reads a foreign link or repeats.
        """Raise the unsafe paging stop when a query stopped on a foreign link or a repeated page.

        Why: a foreign next link can send the run to another host.
        A repeated page can loop, so the run ends at once.
        No further link is followed after either fault.

        Args:
            page: Paged result of one query.

        Raises:
            StopRun: The query stopped on a foreign origin or on a repeated page.
        """
        unsafe = (PageSet.StopReason.FOREIGN_ORIGIN, PageSet.StopReason.REPEATED_PAGE)  # The two unsafe stop reasons.
        if page.stop_reason in unsafe:  # The paging rules forbid any further request for this query.
            raise cls(  # End the run, because a foreign link or repeat is unsafe.
                cls.Outcome.UNSAFE_PAGING_STOP, "the paging stopped on a foreign next link or a repeated page"
            )

    @classmethod
    def review_query(cls, page: PageSet, timeouts: int) -> None:  # Review each attempt, then the paging of one query.
        """Raise the run stop of the first attempt or the paging of one query that ends the run.

        Why: a paged query has two review steps, the attempts and the paging. Both must pass before a check reads
        the pages, so the two steps are applied together.

        Args:
            page: Paged result of one query, with its attempts.
            timeouts: Timeout count of the whole run, including the attempts before these.

        Raises:
            StopRun: An attempt or the paging of the query ends the run.
        """
        cls.review_calls(page.calls, timeouts)  # Review each attempt of every page first.
        cls.review_page(page)  # Then review the paging, so a foreign link or repeat stops the run.


@dataclass
class CheckContext:  # Hold the run state, so every call follows the same rules.
    """Run state that the checks share: settings, parsed inputs, the API session, and observations.

    Why: each check reads one set of settings.
    Each check writes its observations to one place.
    Each HTTP call passes through one method that applies the run-stop rules.
    """

    OBSERVATION_KEYS: ClassVar[tuple[str, ...]] = (  # Answers of the live questions, in evidence order.
        "q1_device_type_default",
        "q2_mist_edge_window",
        "q3_limit_5000",
        "q4_next_form",
        "q5_distinct_type",
        "q6_last_trouble_present",
        "q7_response_headers",
        "q8_alarm_status_values",
        "device_event_types_by_device_type",
    )
    SDK_CONSOLE_LEVEL: ClassVar[int] = SessionOpener.CONSOLE_LEVEL  # Above CRITICAL, so the SDK console prints nothing.
    SDK_LOGGING_LEVEL: ClassVar[int] = SessionOpener.LOGGING_LEVEL  # WARNING for the mistapi logger in the run.
    SDK_ENVIRONMENT_NAMES: ClassVar[tuple[str, ...]] = SessionOpener.ENVIRONMENT_NAMES  # Variables the SDK reads.

    settings: SmokeSettings  # Validated options of the run.
    token: str = field(repr=False)  # Token value. It is passed to the SDK and never printed, logged, or written.
    redactor: EvidenceRedactor  # Redaction rules of the evidence record and of the console.
    session_factory: Callable[..., Any]  # Builds the API session. The command passes the SDK class.
    window_query: dict[str, str]  # Start and end of the collection window, in epoch seconds.
    openapi: OpenApiIndex | None = None  # OpenAPI index, set by SMK-01.
    claims: RunbookClaims | None = None  # Runbook facts, set by SMK-01 when the runbook exists.
    client: ReadOnlyMistClient | None = None  # The only route to the API, set by open_client.
    validation_requests: int = 0  # 1 once the token validation request was sent, even when it failed.
    calls: list[CallRecord] = field(default_factory=list)  # Every attempt of the run, in request order.
    catalogs: dict[str, dict[str, Any]] = field(default_factory=dict)  # Catalog entries, set by SMK-05.
    search_pages: dict[str, PageSet] = field(default_factory=dict)  # Organization search pages, set by SMK-06.
    observations: dict[str, Any] = field(  # Start each answer as null, so an unread one stays null.
        default_factory=lambda: dict.fromkeys(CheckContext.OBSERVATION_KEYS)
    )

    @classmethod
    def for_run(  # Build the run state, so every request shares one window.
        cls, settings: SmokeSettings, token: str, session_factory: Callable[..., Any]
    ) -> CheckContext:
        """Build the run state of one command: the collection window, the evidence rules, and the session factory.

        Why: the window is read once, so every request of the run shares it. The evidence rules use the same
        identifiers as the settings, so the record cannot name a value that the run did not validate.

        Args:
            settings: Validated settings of the run.
            token: Token value, which only the session constructor receives.
            session_factory: Builds the API session.

        Returns:
            The run state, with no client yet.
        """
        now = int(datetime.now(UTC).timestamp())  # One clock reading, so each request shares one window.
        window_query = {  # Start and end of the window in epoch seconds, with the end lag applied.
            "start": str(now - settings.window_minutes * 60),  # Epoch seconds at the start of the window.
            "end": str(now - settings.delay_minutes * 60),  # Epoch seconds at the end, after the lag for late events.
        }
        redactor = EvidenceRedactor(  # Redaction rules, which also redact the site ID when the run has one.
            organization_id=settings.org_id,
            site_ids=(settings.site_id,) if settings.site_id else (),
            token_value=token,
        )
        return cls(  # Return the run state with the shared window and redactor.
            settings=settings,  # Validated options of the run.
            token=token,  # Token value, passed to the session constructor only.
            redactor=redactor,  # Identifier and contact rules.
            session_factory=session_factory,  # Builds the API session.
            window_query=window_query,  # Start and end of the window, in epoch seconds.
        )

    def requests_used(self) -> int:  # Count each request, including a validation that failed.
        """Return the requests that the run counted, including the token validation request.

        Why: the summary line and the evidence record report this count. A failed validation still sent a request.

        Returns:
            The counted requests of the run, zero before the validation request.
        """
        if self.client is not None:  # The budget of the client holds the exact count.
            return self.client.requests_sent  # Every counted request of the run.
        return self.validation_requests  # The validation request was sent, but the session did not open.

    def open_client(self) -> None:  # Open the API session, and count its validation request.
        """Build the API session from the token, and count its token validation request.

        Why: the SDK sends one GET when the session receives the token. The budget counts that request as the
        first unit. The client never calls login(), because login() sends a second validation request.

        Raises:
            StopRun: The API rejected the token with HTTP 401, or the connection failed during validation.
        """
        self.validation_requests = 1  # The validation request is sent by the constructor below, so it counts now.
        try:  # Map each SDK fault to the run stop of the contract.
            session = SessionOpener.open(self.session_factory, self.settings.host, self.token)  # Validates the token.
        except ValueError as error:  # HTTP 401. The SDK message holds a masked token, so the log filter removes it.
            logger.exception("Token validation was rejected by the API")  # Keep the traceback for the operator.
            raise StopRun(  # End the run, since HTTP 401 means the token was rejected.
                StopRun.Outcome.CONFIGURATION_ERROR, "HTTP 401: the token was rejected by the API"
            ) from error
        except ConnectionError as error:  # No response reached the client during the validation.
            logger.exception("Token validation could not reach the API")  # Keep the traceback for the operator.
            raise StopRun(  # End the run, since no response reached the client.
                StopRun.Outcome.CONFIGURATION_ERROR, "the connection failed during token validation"
            ) from error
        self.client = ReadOnlyMistClient(  # Route to the API, with one budget and one timeout for the whole run.
            approved_host=self.settings.host,  # Lower-case host that the run approved.
            governor=CallGovernor(  # One budget and one timeout for every request of the run.
                session=session,  # The SDK session. Only its GET method is used.
                request_budget=self.settings.max_requests,  # Most requests of the run, including the validation.
                call_timeout_seconds=float(self.settings.call_timeout_seconds),  # Longest wait for one SDK call.
                max_retries=self.settings.max_retries,  # Retries for server errors and connection failures.
                requests_sent=1,  # The token validation request is the first counted unit.
            ),
        )
        logger.debug("API session open, %s requests counted", self.client.requests_sent)  # Log the count of the run.

    def get(  # Send one GET, so each attempt meets the run-stop rules.
        self, path_template: str, identifiers: dict[str, str], query: dict[str, str]
    ) -> tuple[CallRecord, ...]:
        """Send one GET request, keep its attempts, and raise the run stop of an attempt that ends the run.

        Why: a check reads its data only after the run-stop rules passed for every attempt of the request.

        Args:
            path_template: Path that starts with /api/v1/ and holds placeholders.
            identifiers: Values for the placeholders. Each value is encoded as one path segment.
            query: Query parameters of the request.

        Returns:
            Every attempt of the request, in request order.

        Raises:
            RuntimeError: The API session is not open.
            StopRun: An attempt ends the run.
        """
        client = RequestTrail.require_client(self.client)  # The session that open_client builds must exist first.
        attempts = RequestTrail.send(client, path_template, identifiers, query)  # Send through the budget and log.
        self.calls.extend(attempts)  # Keep every attempt for the request counts and the header observation.
        StopRun.review_calls(attempts, client.timeouts)  # Raise the stop when an attempt ends the run.
        return attempts  # Return every attempt, so each retry is counted.

    def get_pages(  # Read pages of one query, capped to limit the requests.
        self,
        path_template: str,
        identifiers: dict[str, str],
        query: dict[str, str],
        max_pages: int,
    ) -> PageSet:
        """Read the pages of one query, keep its attempts, and raise the run stop of an unsafe query.

        Why: a search reads up to the page ceiling, and a foreign next link or a repeated page ends the run.

        Args:
            path_template: Path that starts with /api/v1/ and holds placeholders.
            identifiers: Values for the placeholders. Each value is encoded as one path segment.
            query: Query parameters of the first page.
            max_pages: Most pages that the query reads.

        Returns:
            The paged result of the query.

        Raises:
            RuntimeError: The API session is not open.
            StopRun: An attempt or the paging of the query ends the run.
        """
        client = RequestTrail.require_client(self.client)  # The session that open_client builds must exist first.
        page = RequestTrail.read_pages(client, path_template, identifiers, query, max_pages)  # Read and log the pages.
        self.calls.extend(page.calls)  # Keep every attempt of every page.
        StopRun.review_query(page, client.timeouts)  # Raise the stop when an attempt or the paging ends the run.
        return page  # Return the pages only after the stop rules passed.


@dataclass(frozen=True)
class EvidenceBuilder:  # Build the evidence record, with one writer for each key.
    """Build and write the evidence record of one run from the run state.

    Why: the evidence schema is a contract with fourteen top-level keys.
    One builder writes each key in one place.
    A run that stops early still writes every key.
    Each value that the run did not obtain is null or empty.
    """

    CATALOG_KEYS: ClassVar[tuple[str, ...]] = (  # The six catalogs of SMK-05, in evidence order.
        "alarm_defs",
        "device_events",
        "mxedge_events",
        "system_events",
        "ap_led_status",
        "webhook_topics",
    )
    SETTINGS_KEYS: ClassVar[tuple[str, ...]] = (  # The eleven keys of the settings section.
        "call_timeout_seconds",
        "window_minutes",
        "delay_minutes",
        "max_pages",
        "max_requests",
        "max_retries",
        "site_scope",
        "runbook",
        "openapi",
        "runbook_explicit",
        "env_file_given",
    )
    DEFAULT_BUDGET: ClassVar[int] = 60  # Budget value of a run that accepted no --max-requests value.
    TOOL_SECTION: ClassVar[dict[str, str]] = {  # Name, module, and version of the smoke tool.
        "name": "netcool_runbook_smoke",
        "module": "scripts.netcool_runbook_smoke",
        "version": __version__,
    }

    context: CheckContext | None  # Run state, or None when the run stopped before the settings were valid.
    redactor: EvidenceRedactor  # Filters the record to the contract keys and scrubs each value.
    outcome: StopRun.Outcome  # Outcome class of the run.
    results: Sequence[CheckResult]  # Results of the checks, in check order.

    def build(self) -> dict[str, Any]:  # Build every top-level key, even after an early stop.
        """Return the evidence record as a dict, before the redactor filters it.

        Why: the record keeps the contract order of its top-level keys, and each value that the run did not
        obtain is null or empty.

        Returns:
            The evidence record with every top-level key.
        """
        context = self.context  # Run state, or None before the settings were valid.
        observations = {  # Null answers when the run had no valid settings, and q7 from every attempt of the run.
            **(dict.fromkeys(CheckContext.OBSERVATION_KEYS) if context is None else context.observations),
            "q7_response_headers": self._response_headers(),  # Headers come from every attempt of the run.
        }
        return {  # Return the top-level keys in the order of the contract.
            "schema_version": "1",  # Fixed value of the contract.
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),  # UTC with Z.
            "tool": dict(self.TOOL_SECTION),  # Name, module, and version of the smoke tool.
            "host": context.settings.host if context is not None else None,  # Regional host, or null.
            "organization_label": "org-1",  # The organization identifier is never written.
            "settings": self._settings(),  # Options of the run, without any secret.
            "request_count": context.requests_used() if context is not None else 0,  # Requests, with the validation.
            "request_budget": context.settings.max_requests if context is not None else self.DEFAULT_BUDGET,  # Budget.
            "sdk_retry_possible": True,  # The SDK can retry inside one client call.
            "outcome_class": self.outcome.label,  # Outcome class name.
            "exit_code": self.outcome.exit_code,  # Exit code of the outcome class.
            "checks": [result.as_evidence() for result in self.results],  # Ten items, or none before SMK-01.
            "catalogs": self._catalogs(),  # Six catalog entries.
            "observations": observations,  # Answers of the live questions.
        }

    def write(self, path: Path) -> Path:  # Write the record after the allowlist and redaction rules.
        """Filter the record with the redactor, write it as UTF-8 JSON, and return the written path.

        Why: the record is written only after the allowlist and the redaction rules passed, so no key or value
        outside the contract reaches the file.

        Args:
            path: File to write. Its folder is created when it is missing.

        Returns:
            The path of the written file.

        Raises:
            OSError: The file or its folder cannot be written.
        """
        logger.info("Filtering the evidence record of %s checks", len(self.results))  # Log before the transform.
        record = self.redactor.allow(self.build())  # Keep the contract keys and scrub each value.
        logger.debug("Evidence record keeps %s top-level keys", len(record))  # Log the result of the transform.
        return EvidenceWriter(path).write(record)  # Write the record. EvidenceWriter logs the file write.

    def _settings(self) -> dict[str, Any]:  # Build the settings section, with no secret or user path.
        """Return the settings section of the evidence record, without any secret or path of a user folder.

        Why: the section lets a reader repeat the run. It never names the env file or the site identifier.

        Returns:
            The eleven settings keys, with null values when the run has no validated settings.
        """
        if self.context is None:  # The run stopped before the settings were valid.
            return dict.fromkeys(self.SETTINGS_KEYS)  # Every value is null, because the run obtained none.
        settings = self.context.settings  # Validated options of the run.
        root = settings.root  # Repository root, so each path is written relative to it.
        return {  # Return the settings that let a reader repeat the run.
            "call_timeout_seconds": settings.call_timeout_seconds,  # Value of --call-timeout.
            "window_minutes": settings.window_minutes,  # Value of --window-minutes.
            "delay_minutes": settings.delay_minutes,  # Value of --delay-minutes.
            "max_pages": settings.max_pages,  # Value of --max-pages.
            "max_requests": settings.max_requests,  # Value of --max-requests.
            "max_retries": settings.max_retries,  # Value of --max-retries.
            "site_scope": "site-1" if settings.site_id else None,  # The site identifier is never written.
            "runbook": settings.runbook_path.relative_to(root).as_posix(),  # Relative runbook path.
            "openapi": settings.openapi_path.relative_to(root).as_posix(),  # Relative OpenAPI path.
            "runbook_explicit": settings.runbook_explicit,  # True when --runbook was given.
            "env_file_given": settings.env_file_given,  # True when --env-file was given. The path is not written.
        }

    def _response_headers(self) -> dict[str, Any] | None:  # Answer the header question from every attempt of the run.
        """Return the answer to question q7 from every attempt that sent a request.

        Why: q7 asks which headers the service returns and whether a rate-limit header exists. The answer
        comes from the whole run, so it cannot depend on one check.

        Returns:
            The names, the rate-limit flag, and the Retry-After values. None when no response exists.
        """
        if self.context is None:  # Without a run context, no request was sent.
            return None  # The answer stays null.
        responded = [call for call in self.context.calls if call.status_code is not None]  # Attempts with a response.
        if not responded:  # Every attempt was refused or failed before a response, so no header exists.
            return None  # The answer stays null.
        names = sorted({name for call in responded for name in call.header_names})  # Header names only.
        return {  # Return the header facts, which the evidence record keeps.
            "names": names,
            "rate_limit_header_present": any(
                "ratelimit" in name or "rate-limit" in name for name in names
            ),  # Lower case.
            "retry_after_seconds": list(
                chain.from_iterable(call.retry_after_seconds for call in responded)
            ),  # In request order.
        }

    def _catalogs(self) -> dict[str, Any]:  # Give each catalog an entry, with null values when none was fetched.
        """Return the six catalog entries of the evidence record, in the contract order.

        Why: the record keeps all six catalogs, so a reader sees every catalog even after an early stop. A catalog
        that the run did not fetch gets null values and no item.

        Returns:
            The six catalog entries, keyed by catalog name.
        """
        context = self.context  # Run state, or None before the settings were valid.
        return {  # One entry for each catalog, with null values when the run fetched none.
            key: (context.catalogs.get(key) if context is not None else None)
            or {"status_code": None, "item_count": 0, "items": []}
            for key in self.CATALOG_KEYS
        }
