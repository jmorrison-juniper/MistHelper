"""Organization search and count checks SMK-06 and SMK-07.

Why: the searches prove that the four event families return records in the collection window.
The counts prove that each search total agrees with the organization count.
A silent mismatch would hide missing events.
"""

from __future__ import annotations  # Postpone annotation evaluation.

from collections.abc import Sequence  # Type the record lists and the part lists.
from dataclasses import dataclass, field, replace  # Declare the observer and copy the result with the counts.
from typing import Any, ClassVar  # Type the JSON values and the class constants.

import structlog  # Structured logging of each search and each count comparison.

from scripts.netcool_runbook_smoke.checks import (  # Import the check types that each family check returns.
    CheckContext,
    CheckResult,
    CheckStatus,
)
from scripts.netcool_runbook_smoke.client import (  # Import the call and page types that paged reads return.
    CallRecord,
    PageSet,
)
from scripts.netcool_runbook_smoke.documents import (  # Import the runbook facts that name the identifier fields.
    RunbookClaims,
)

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


@dataclass
class SearchObservations:  # Hold the q1, q2, q4, and q8 answers, free of customer data.
    """Record the answers to the live questions q1, q2, q4, and q8 from the records that SMK-06 reads.

    Why: the answers come from the same records as the family checks. Each value is an enumerated word, a count,
    or a flag, never an identifier, so the evidence stays free of customer data. The run state is a dataclass
    field, so the class stays within the method limit of the package.
    """

    ENUMERATED: ClassVar[dict[str, tuple[str, ...]]] = {  # Enumerated fields of each family, from the OpenAPI file.
        "alarms": ("status", "severity", "group"),
        "device_events": ("ev_type",),
        "mxedge_events": ("severity",),
    }

    context: CheckContext = field(repr=False)  # Run state that receives the observations. Hidden: it holds the token.

    def record_device_types(  # Record q1 so the run shows the default device type.
        self, records: Sequence[Any]
    ) -> None:
        """Record q1: the device types of the device event records, and whether every record is an AP event.

        Why: the question asks whether the default device type of the search is AP. The answer is null when no
        record carries a device type, because then nothing was observed.

        Args:
            records: Records of the device event search.
        """
        types = sorted(  # Distinct device types of the records, sorted, so two runs compare with a plain diff.
            {r["device_type"] for r in records if isinstance(r, dict) and isinstance(r.get("device_type"), str)}
        )
        only_ap = (types == ["ap"]) if types else None  # Null when no device type was observed, so nothing is claimed.
        self.context.observations["q1_device_type_default"] = {  # Publish q1, which asks whether the default is AP.
            "device_types_seen": types,
            "only_ap": only_ap,
        }

    def record_mxedge_echo(  # Record q2 so the run shows whether the window is echoed.
        self, page: PageSet, window: dict[str, str]
    ) -> None:
        """Record q2: whether the Mist Edge search echoes the start and end that the request gave.

        Why: the window of a Mist Edge search decides which events it returns. The echo shows whether the
        service applies the window that the smoke test sent.

        Args:
            page: Paged result of the Mist Edge search.
            window: Start and end query values that the request sent.
        """
        first = page.calls[0].data if page.calls else None  # The first response of the Mist Edge search.
        if not isinstance(first, dict) or "start" not in first or "end" not in first:  # No echo exists.
            echoes: bool | None = None  # The answer stays null, because the response shows no window.
        else:  # The response carries the echoed window.
            start_echoed = first["start"] == int(window["start"])  # The echoed start equals the sent start.
            end_echoed = first["end"] == int(window["end"])  # The echoed end equals the sent end.
            echoes = start_echoed and end_echoed  # The echo holds only when both values match.
        self.context.observations["q2_mist_edge_window"] = {  # Publish q2. SMK-09 later fills its two probe keys.
            "echoes_start_end": echoes,
            "with_duration_1h": {"start": None, "end": None},  # Null until the SMK-09 probe runs.
            "without_time_parameter": {"start": None, "end": None},  # Null until the SMK-09 probe runs.
        }

    def record_enumerated(  # Record q8 values, so the run lists the enumerated words.
        self, family: str, records: Sequence[Any]
    ) -> None:
        """Record q8: the distinct enumerated values of one family, and the acked counts of alarms.

        Why: q8 asks which values the alarm search returns, including resolved alarms. The values are sorted, so two
        runs can be compared with a plain diff.

        Args:
            family: Family key, for example alarms.
            records: Records of the family search.
        """
        if family not in self.ENUMERATED:  # Only the three families of q8 are recorded.
            return  # Nothing to record for the other families.
        answer = self.context.observations.get("q8_alarm_status_values")  # The q8 object built so far.
        values: dict[str, Any] = answer if isinstance(answer, dict) else {}  # Start the object on the first family.
        values[family] = self._family_values(family, records)  # Null when the family read no record object.
        self.context.observations["q8_alarm_status_values"] = values  # Store the object with every family so far.

    def record_next_form(  # Record q4 to show how the service links result pages.
        self, pages: Sequence[PageSet]
    ) -> None:
        """Record q4: the form of the first next link that a search page returned, and whether it carries search_after.

        Why: the answer tells the operator how the service pages its results, which the collector must follow. The
        answer is null when no search page was read, and the form is none when no page returned a next link.

        Args:
            pages: Paged results of the four organization searches, in family order.
        """
        if not any(page.calls for page in pages):  # No search page was read, so nothing was observed.
            self.context.observations["q4_next_form"] = None  # The answer stays null.
            return  # Stop early, because no search page was read.
        links = [call.next_value for page in pages for call in page.calls if call.next_value is not None]  # Next links.
        if not links:  # Every search page ended without a next link.
            self.context.observations["q4_next_form"] = {"form": "none", "carries_search_after": None}  # Form: none.
            return  # Nothing to classify, because no link exists.
        first = str(links[0])  # The first next link that a search page returned.
        self.context.observations["q4_next_form"] = {  # Publish q4, which records the form of the first link.
            "form": (  # Relative, absolute, or rejected, as the client link rules classify it.
                "relative"
                if first.startswith("/api/v1/")  # The link names no host, so the approved origin is used.
                else (
                    "absolute"
                    if first.startswith("https://")  # A full link, whose origin the client checked.
                    else "rejected"
                )  # Any other form failed the link rules of the client.
            ),
            "carries_search_after": "search_after" in first,
        }

    def _family_values(  # Keep enumerated values, so the answer holds no identifier.
        self, family: str, records: Sequence[Any]
    ) -> dict[str, Any] | None:
        """Return the sorted enumerated values of one family, plus the acked counts for alarms.

        Why: the answer lists each value once, sorted, and the acked flag is a count, so no identifier is kept. A
        family that read no record object has no value, so its answer is null.

        Args:
            family: Family key, which names the enumerated fields.
            records: Records of the family search. Only the objects among them are read.

        Returns:
            The sorted values of each enumerated field, with the acked counts for alarms. None when no object exists.
        """
        rows = [record for record in records if isinstance(record, dict)]  # Only objects hold the fields.
        if not rows:  # The family read no record object, so nothing was observed.
            return None  # Null, because no value can be claimed.
        family_values: dict[str, Any] = {  # Sorted distinct text of each enumerated field, skipping null values.
            name: sorted({str(row[name]) for row in rows if row.get(name) is not None})
            for name in self.ENUMERATED[family]
        }
        if family == "alarms":  # Alarms also carry the acked flag, which is counted as true and false.
            family_values["acked"] = {  # Counts of the flag, so no alarm identifier is kept.
                "true": sum(row.get("acked") is True for row in rows),  # Alarms that are acknowledged.
                "false": sum(row.get("acked") is False for row in rows),  # Alarms that are not acknowledged.
            }
        return family_values  # The enumerated values of the family, with the acked counts for alarms.


class FamilyJudge:  # Judge each family page, so the roll-up gets one status.
    """Judge the paged result of one event family: its stop reason, its records, and its identifier fields.

    Why: the same rules apply to each family.
    A page ceiling is a warning, and a failed query is a failure.
    Zero records are a warning.
    A record set without the runbook identifier fields is a failure.
    """

    def __init__(  # Keep the runbook facts, which name the identifier fields.
        self, claims: RunbookClaims | None
    ) -> None:
        """Keep the runbook facts that name the identifier fields.

        Args:
            claims: Runbook facts, or None when the default runbook is absent.
        """
        self._claims: RunbookClaims | None = claims  # Runbook facts that name the identifier fields.

    def judge(  # Return one family status, so the roll-up can combine it.
        self, label: str, heading: str, page: PageSet
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text of one family.

        Why: each family contributes one part to the roll-up of SMK-06, and the text names the family.

        Args:
            label: Name of the family in the output, for example alarms.
            heading: Heading of the family in the runbook, which names its identifier fields.
            page: Paged result of the family search.

        Returns:
            The status and the text of the family.
        """
        if page.stop_reason == "PageCeiling":  # More pages remain, so the query is incomplete but not wrong.
            return (  # Warn: pages remain, so the query is incomplete but not wrong.
                CheckStatus.WARN,
                f"{label} search reached the page ceiling with a next link still present.",
            )
        if page.stop_reason is not None:  # Another error class ended the query, so its proof failed.
            return CheckStatus.FAIL, f"{label} search failed: {page.stop_reason}."  # Fail: no proof exists.
        if page.record_count == 0:  # Zero records do not prove that no event exists.
            return CheckStatus.WARN, (  # Warn on zero records, since zero is not proof of absence.
                f"zero records for {label} in the collection window. " "Zero records do not prove that no event exists."
            )
        for field_name in self._identifiers(heading):  # Each identifier field of the family, from the runbook.
            if not any(isinstance(record, dict) and field_name in record for record in page.records):  # Absent.
                return CheckStatus.FAIL, f"{label} identifier field {field_name} is in no record."  # Fail: no record.
        return CheckStatus.PASS, f"{page.record_count} {label} records, identifiers found."  # Pass: fields found.

    def _identifiers(self, heading: str) -> tuple[str, ...]:  # Read identifier fields from the runbook, not a copy.
        """Return the identifier fields that the runbook names for one family.

        Why: the runbook names the fields that prove a record, so the check uses the runbook rather than a copy.

        Args:
            heading: Heading of the family in the runbook.

        Returns:
            The identifier field names, or an empty tuple when the runbook is absent.
        """
        if self._claims is None:  # Without the runbook, no identifier is named.
            return ()  # Nothing is checked.
        return self._claims.identifier_fields.get(heading, ())  # The fields of this family.


class CountComparison:  # Compare each total with its count sum, so drift shows.
    """Compare the search total of one family with the sum of its count values.

    Why: the count endpoint and the search endpoint must agree for the same window. A difference means that one of
    them reads a different set of events, and the operator must see it.
    """

    def compare(  # Judge a family count, so each count proves its search.
        self,
        label: str,
        key: str,
        has_total: bool,
        final: CallRecord,
        search: PageSet | None,
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text of one family count comparison.

        Why: a count that is not a results list is a failure.
        A family without a total is an observation.
        A search that did not complete cannot prove its total.
        The part is therefore skipped.

        Args:
            label: Name of the family in the output.
            key: Family key, for example device_events.
            has_total: True when the search response carries a total.
            final: Final attempt of the count request.
            search: Paged result of the first search of the family, or None when it was not read.

        Returns:
            The status and the text of the comparison.
        """
        rows = self._rows(final)  # The count rows, or None when the count request failed.
        gate = CountVerdict.gate(label, key, has_total, rows, search)  # A rule that decides the family, or None.
        if gate is not None:  # A gate decided the family, so no total is compared.
            return gate  # Return the verdict of the gate.
        total = self._total(search)  # The total of the first search page.
        return CountVerdict.equal(label, total, self._counted(rows))  # Compare the total with the count sum.

    def _rows(  # Read count rows, since a count without rows proves nothing.
        self, final: CallRecord
    ) -> list[Any] | None:
        """Return the count rows of a count response, or None when the body is not a results list.

        Why: a count without its rows proves nothing, so the comparison stops at the first missing list.

        Args:
            final: Final attempt of the count request.

        Returns:
            The rows of the response, or None when the request failed or the body has no results list.
        """
        body = final.data if isinstance(final.data, dict) else {}  # The count body must be an object.
        results = body.get("results")  # The count rows of the response.
        if final.error_class is not None or final.status_code != 200 or not isinstance(results, list):  # Not readable.
            return None  # The count failed.
        return results  # The rows, in response order.

    def _total(self, search: PageSet | None) -> int | None:  # Read the total, so the comparison has an integer.
        """Return the total of the first search page, or None when that total is not an integer.

        Why: the first page holds the total of the query, and a boolean is not a count.

        Args:
            search: Paged result of the family search, or None when the search was not read.

        Returns:
            The integer total, or None.
        """
        first = search.calls[0].data if search is not None and search.calls else None  # The first page holds the total.
        total = first.get("total") if isinstance(first, dict) else None  # The total value, if the page has one.
        if isinstance(total, int) and not isinstance(total, bool):  # A boolean is not a count.
            return total  # The integer total.
        return None  # The total is missing or not an integer.

    def _counted(self, rows: Sequence[Any] | None) -> int:  # Sum the counts, so both sides add the same buckets.
        """Return the sum of the count values of the rows, ignoring each row without an integer count.

        Why: the count endpoint sums its buckets, so the comparison adds the same buckets.

        Args:
            rows: Count rows of the response, or None when the count request failed.

        Returns:
            The sum of the integer count values.
        """
        return int(  # Skip rows without an integer count, so the sum stays exact.
            sum(item["count"] for item in (rows or []) if isinstance(item, dict) and isinstance(item.get("count"), int))
        )


class CountVerdict:  # Judge one family count, after the rules that decide without a total.
    """Judge one family count against its search: the gates that decide a family, then the total comparison.

    Why: three conditions decide each family before any total is compared.
    A count that is not a results list is one condition.
    A family without a total is another condition.
    A search that did not complete is the third condition.
    The rules live apart from the request code, so each rule reads alone.
    """

    @staticmethod
    def gate(  # Return the verdict of a rule that decides the family, or None to compare the totals.
        label: str, key: str, has_total: bool, rows: Sequence[Any] | None, search: PageSet | None
    ) -> tuple[CheckStatus, str] | None:
        """Return the verdict that a rule gives before any total is compared, or None when the comparison may proceed.

        Why: a family whose count is unreadable fails.
        A family without a total is an observation.
        A search that was not read or did not complete cannot prove its total.
        The part is therefore skipped.

        Args:
            label: Name of the family in the output.
            key: Family key, for example device_events.
            has_total: True when the search response carries a total.
            rows: Count rows of the response, or None when the count request failed.
            search: Paged result of the first search of the family, or None when it was not read.

        Returns:
            The verdict of the gate, or None when the totals may be compared.
        """
        if rows is None:  # A count that is not a results list is a failure.
            return CheckStatus.FAIL, f"{label} count did not return a results list."  # Fail: no readable count.
        if not has_total:  # Mist Edge responses carry no total, so no comparison is possible.
            return CheckStatus.INFO, f"{label} have no total."  # Observation: the family has no total to compare.
        if search is None or not search.calls:  # The search was not read, so its total is unknown.
            return CheckStatus.SKIP, f"{label} search was not read."  # Skip: no total is known for the family.
        if key == "device_events" and not search.complete:  # An incomplete device search has no reliable total.
            return CheckStatus.SKIP, "device event search incomplete"  # Skip: an incomplete search misleads.
        return None  # No gate applies, so the totals may be compared.

    @staticmethod
    def equal(label: str, total: int | None, counted: int) -> tuple[CheckStatus, str]:  # Judge the total comparison.
        """Return the verdict of the total comparison of one family.

        Why: both sides must read the same set of events. A difference means that one endpoint reads other events,
        so the operator must see it as a warning.

        Args:
            label: Name of the family in the output.
            total: Integer total of the search, or None when the search has no integer total.
            counted: Sum of the count values of the count request.

        Returns:
            The status and the text of the comparison.
        """
        if total is None:  # The total must be an integer.
            return CheckStatus.SKIP, f"{label} search has no total."  # Skip when the search has no integer total.
        if total == counted:  # Both sides read the same set of events.
            return CheckStatus.PASS, f"{label} equal"  # Pass when both sides read the same set of events.
        return CheckStatus.WARN, f"{label} search total {total} differs from the count sum {counted}"  # Warn: mismatch.


class SearchChecks:  # Run SMK-06 and SMK-07, so both checks share search pages.
    """Run SMK-06 and SMK-07: the organization searches of four families, and their counts.

    Why: each family must return records in the collection window, and each count must agree with its search.
    The two checks share the search pages, so SMK-07 compares the page that SMK-06 read and makes no extra search.
    """

    FAMILIES: ClassVar[  # Map each family to its paths, so both checks use one list.
        tuple[tuple[str, str, str, str, str, bool], ...]
    ] = (  # Key, label, search, count, heading, total.
        (
            "alarms",
            "alarms",
            "/api/v1/orgs/{org_id}/alarms/search",
            "/api/v1/orgs/{org_id}/alarms/count",
            "6.1 Alarm Search",
            True,
        ),
        (
            "device_events",
            "device events",
            "/api/v1/orgs/{org_id}/devices/events/search",
            "/api/v1/orgs/{org_id}/devices/events/count",
            "6.2 Device Event Search",
            True,
        ),
        (
            "mxedge_events",
            "Mist Edge events",
            "/api/v1/orgs/{org_id}/mxedges/events/search",
            "/api/v1/orgs/{org_id}/mxedges/events/count",
            "6.3 Mist Edge Event Search",
            False,
        ),
        (
            "system_events",
            "system events",
            "/api/v1/orgs/{org_id}/events/system/search",
            "/api/v1/orgs/{org_id}/events/system/count",
            "6.4 System Event Search",
            True,
        ),
    )
    KEPT_STOP_REASONS: ClassVar[tuple[str, ...]] = ("PageCeiling", "Timeout")  # Stop reasons that the evidence keeps.

    def __init__(self, context: CheckContext) -> None:  # Keep the run context, so both checks read the same pages.
        """Keep the run context that the checks share.

        Args:
            context: Run state of the smoke test.
        """
        self._context: CheckContext = context  # Run state that receives the search pages.

    def smk_06(self) -> CheckResult:  # Run SMK-06, which reads and judges the four searches.
        """Read the organization searches of four families in the collection window, and judge each one.

        Why: each family must return records, and each identifier field of the runbook must appear in the records.
        The search pages are kept for SMK-07.

        Returns:
            The roll-up result of SMK-06.

        Raises:
            StopRun: A paged query stops on a foreign link, a repeated page, or a run-stop rule.
        """
        org = {"org_id": self._context.settings.org_id}  # Path value of the organization.
        observer = SearchObservations(self._context)  # Records q1, q2, and q8 from the same pages.
        judge = FamilyJudge(self._context.claims)  # Judges each family with the runbook identifier fields.
        pages: list[PageSet] = []  # The four paged results, in family order.
        parts: list[tuple[CheckStatus, str]] = []  # One status and text for each family.
        for key, label, search_path, _count, heading, _has_total in self.FAMILIES:  # Four families in order.
            logger.info("SMK-06 reads the %s search", key)  # Log before the paged read.
            page = self._context.get_pages(  # Read one family, capped by the configured page limit.
                search_path, org, dict(self._context.window_query), self._context.settings.max_pages
            )
            self._context.search_pages[key] = page  # SMK-07 compares the first page of each family.
            pages.append(page)  # Keep the paged result for the roll-up.
            parts.append(judge.judge(label, heading, page))  # Status and text of the family.
            observer.record_enumerated(key, page.records)  # q8 values of the family.
        observer.record_device_types(self._context.search_pages["device_events"].records)  # q1 answer.
        observer.record_mxedge_echo(self._context.search_pages["mxedge_events"], self._context.window_query)  # q2.
        observer.record_next_form(pages)  # q4, from the first next link of the searches.
        names = sorted(  # Collect the field names, but never the record values.
            {key for page in pages for record in page.records if isinstance(record, dict) for key in record}
        )
        return self._summarize(pages, parts, names)  # Return the roll-up, so SMK-06 reports all four families.

    def smk_07(self) -> CheckResult:  # Run SMK-07, which compares each count with its search.
        """Request the four count endpoints with distinct=type, and compare each total with its search.

        Why: the count and the search must agree for the same window. The count status of each family is
        recorded as observation q5, because the live run confirms that the service accepts distinct=type.

        Returns:
            The roll-up result of SMK-07.
        """
        org = {"org_id": self._context.settings.org_id}  # Path value of the organization.
        count_query = {**self._context.window_query, "distinct": "type"}  # Window plus the distinct type.
        comparison = CountComparison()  # Compares each count with its first search page.
        calls: list[CallRecord] = []  # Every attempt of the four count requests.
        parts: list[tuple[CheckStatus, str]] = []  # One status and text for each family.
        statuses: dict[str, int | None] = {}  # The HTTP status of each count request, for q5.
        for key, label, _search, count_path, _heading, has_total in self.FAMILIES:  # Four families in order.
            attempts = self._context.get(count_path, org, dict(count_query))  # One count request per family.
            calls.extend(attempts)  # Keep every attempt for the request counts.
            statuses[key] = attempts[-1].status_code  # The q5 answer of this family.
            search = self._context.search_pages.get(key)  # The first search page from SMK-06.
            parts.append(comparison.compare(label, key, has_total, attempts[-1], search))  # Status and text.
        self._context.observations["q5_distinct_type"] = statuses  # Store the q5 answer.
        status = CheckStatus.most_severe([part for part, _ in parts])  # Roll-up of the families.
        text = "; ".join(family_text for _, family_text in parts)  # Every family text, in family order.
        return CheckResult.from_calls(  # Return the SMK-07 result, with every count attempt kept.
            "SMK-07", status, text, calls
        )

    def _summarize(  # Build the SMK-06 roll-up for the four family pages.
        self,
        pages: Sequence[PageSet],
        parts: Sequence[tuple[CheckStatus, str]],
        names: Sequence[str],
    ) -> CheckResult:
        """Build the roll-up result of SMK-06 from the family pages, their parts, and the record field names.

        Why: the check status is the most severe part, and the record and page counts sum the four queries.

        Args:
            pages: Paged results of the four families, in family order.
            parts: Status and text of each family, in family order.
            names: Sorted names of the record fields that the families returned.

        Returns:
            The roll-up result of SMK-06.
        """
        status = CheckStatus.most_severe([part for part, _ in parts])  # Roll-up of the four families.
        text = self._headline(status, pages, parts)  # One sentence for the roll-up status.
        kept = [page.stop_reason for page in pages if page.stop_reason in self.KEPT_STOP_REASONS]  # Evidence stop.
        base = CheckResult.from_calls(  # Result with the request facts of every attempt of the four queries.
            "SMK-06", status, text, [call for page in pages for call in page.calls]
        )
        return replace(  # Copy the result, so the four query totals are added.
            base,
            record_count=sum(page.record_count for page in pages),  # Records of the four families.
            page_count=sum(page.pages_read for page in pages),  # Pages requested by the four queries.
            stop_reason=str(kept[0]) if kept else None,  # The first kept stop reason, or null.
            field_names=tuple(names),  # Names of the record fields, never values.
        )

    def _headline(  # Return the roll-up text, so a warning names its family.
        self,
        status: CheckStatus,
        pages: Sequence[PageSet],
        parts: Sequence[tuple[CheckStatus, str]],
    ) -> str:
        """Return the roll-up text: the record total when every family passed, else the first text of the status.

        Why: a passing run gets one summary, and a warning or failure names the family that caused it.

        Args:
            status: Roll-up status of the four families.
            pages: Paged results of the four families.
            parts: Status and text of each family, in family order.

        Returns:
            The text of the roll-up.
        """
        if status is CheckStatus.PASS:  # Every family passed, so one summary sentence describes the run.
            total = sum(page.record_count for page in pages)  # Records of the four families.
            return (  # Summarize the total only when every family passed.
                f"{total} records in the collection window across four families, identifiers found."
            )
        return next(family_text for part, family_text in parts if part is status)  # First text of the status.
