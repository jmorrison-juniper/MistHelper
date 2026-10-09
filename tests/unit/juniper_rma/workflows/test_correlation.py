"""Tests for menu 302: matched, ambiguous, unmatched, older-ticket, and failed outcomes, plus the exports."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

from datetime import UTC, datetime, timedelta  # WHY: the window and the ticket ages.
from typing import Any  # WHY: loose fixture types.

from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a transport failure to replay.
)
from src.operations.exporting.juniper_rma.workflows.correlation import (  # WHY: the workflow under test.
    CorrelationWorkflow,
    MistTicket,
)
from tests.unit.juniper_rma.fixtures.fake_gateway import FakeGateway, build_session, make_settings  # WHY: fixtures.

NOW = datetime(2026, 10, 8, 12, 0, tzinfo=UTC)  # WHY: one fixed run time for every test.
LIST_REPLY = {  # WHY: three requests, one with a unique case and two that share a case.
    "querySRListResponse": {
        "statusCode": "200",
        "cases": [
            {"serviceRequestNumber": "REQ-1", "customerCaseNumber": "CASE-100", "srStatus": "Open"},
            {"serviceRequestNumber": "REQ-2", "customerCaseNumber": "CASE-200", "srStatus": "Open"},
            {"serviceRequestNumber": "REQ-3", "customerCaseNumber": "CASE-200", "srStatus": "Closed"},
        ],
    }
}
DETAIL_REPLY = {  # WHY: the detail of REQ-1, with one RMA.
    "querySRResponse": {
        "statusCode": "200",
        "serviceRequestNumber": "REQ-1",
        "customerCaseNumber": "CASE-100",
        "srStatus": "Open",
        "contact": {"accountName": "Test Account"},
        "rma": [{"rmaNumber": "RMA-1"}],
        "product": {"serialNumber": "JN1", "productID": "EX4300"},
    }
}
RMA_REPLY = {  # WHY: the RMA with one defective item and the personal fields that the export keeps in full.
    "queryRMAResponse": {
        "statusCode": "200",
        "rmaNumber": "RMA-1",
        "rmaContact": {
            "companyName": "Test Co",
            "contactName": "Jane Tester",
            "contactEmail": "jane.tester@example.com",
            "telephoneNumber": "5555550199",
            "address": {"address1": "1 Test Way", "city": "Testville", "state": "TX", "country": "United States"},
        },
        "defectiveItems": [
            {"itemNumber": "D-1", "serialNumber": "JN1", "trackingNumber": "TRK-1", "defectiveItemStatus": "Received"}
        ],
    }
}
FAULT_763 = {  # WHY: fault 763, more than one request for the case number.
    "querySRResponse": {"statusCode": "400", "fault": [{"errorCode": "763", "errorMessage": "more"}]}
}


class FakeExporter:
    """Records each write instead of writing a file."""

    def __init__(self) -> None:
        """Start with no writes."""
        self.writes: list[tuple[str, str, list[dict[str, Any]]]] = []  # WHY: name, API name, and rows per write.

    def write_with_format_selection(
        self,
        data: list[dict[str, Any]],
        filename_or_table: str,
        api_function_name: str,
        fieldnames: list[str] | None = None,
        backend_options: Any = None,
    ) -> bool:
        """Record the write and report success, as the real exporter does for non-empty data."""
        self.writes.append((filename_or_table, api_function_name, list(data)))  # WHY: keep the rows for assertions.
        return True  # WHY: the workflow does not branch on the result.

    def rows(self, filename: str) -> list[dict[str, Any]]:
        """Return the rows of the first write to the named file, or an empty list."""
        return next((rows for name, _api, rows in self.writes if name == filename), [])  # WHY: one file per name.


class FakeTickets:
    """Returns the tickets that a test supplies, in order."""

    def __init__(self, tickets: list[MistTicket]) -> None:
        """Store the tickets."""
        self._tickets = tickets  # WHY: the tickets the workflow should correlate.

    def read(self) -> list[MistTicket]:
        """Return a copy of the tickets."""
        return list(self._tickets)  # WHY: the workflow reads the list once.


def _ticket(ticket_id: str, case_number: str, days_ago: int = 10) -> MistTicket:
    """Return a ticket created the given number of days before the run time."""
    created = int((NOW - timedelta(days=days_ago)).timestamp())  # WHY: Mist times arrive as epoch seconds.
    return MistTicket(  # WHY: one ticket for the run.
        ticket_id=ticket_id,
        case_number=case_number,
        status="open",
        subject="Subject text",
        created_at=str(created),
    )


def _run(tickets: list[MistTicket], gateway: FakeGateway, key_field: str = "case_number") -> tuple[Any, FakeExporter]:
    """Run the workflow with the fakes and return the run record and the exporter."""
    settings = make_settings(ticket_key_field=key_field)  # WHY: the join field under test.
    exporter = FakeExporter()  # WHY: capture the writes.
    workflow = CorrelationWorkflow(
        build_session(gateway, settings),
        ticket_reader=FakeTickets(tickets),
        exporter=exporter,
        now=NOW,
    )  # WHY: the real workflow with injected collaborators.
    return workflow.execute(), exporter  # WHY: the run record and the writes.


def test_matched_ambiguous_and_unmatched_tickets_are_classified() -> None:
    """Each ticket gets one outcome, and the ambiguous ticket lists its candidates without choosing one."""
    gateway = FakeGateway(  # WHY: replies by endpoint.
        bodies={"querysrlist": [LIST_REPLY], "querysrdetails": [DETAIL_REPLY], "queryrmadetails": [RMA_REPLY]}
    )
    record, exporter = _run(  # WHY: run and keep the exporter.
        [_ticket("t-1", "CASE-100"), _ticket("t-2", "CASE-200"), _ticket("t-3", "CASE-999")], gateway
    )
    assert (record.matched_count, record.ambiguous_count, record.unmatched_count) == (1, 1, 1)  # WHY: one each.
    statuses = {  # WHY: match status by ticket.
        row["mistTicketId"]: row["matchStatus"] for row in exporter.rows("JuniperCorrelation.csv")
    }
    assert statuses == {"t-1": "matched", "t-2": "ambiguous", "t-3": "unmatched"}  # WHY: the outcome per ticket.
    ambiguous = next(  # WHY: the row of the ambiguous ticket.
        row for row in exporter.rows("JuniperCorrelation.csv") if row["mistTicketId"] == "t-2"
    )
    assert ambiguous["candidateRequests"] == "REQ-2,REQ-3"  # WHY: the candidates are listed, not chosen.
    assert record.status == "complete"  # WHY: no problem occurred.


def test_no_match_gives_the_account_reason_and_a_warning(caplog: Any) -> None:
    """When no ticket matches, the reason names the account boundary and the run logs one warning."""
    gateway = FakeGateway(bodies={"querysrlist": [LIST_REPLY]})  # WHY: only the list call is needed.
    with caplog.at_level("WARNING"):  # WHY: capture the operator warning.
        record, exporter = _run([_ticket("t-9", "CASE-999")], gateway)  # WHY: one ticket with no request.
    row = exporter.rows("JuniperCorrelation.csv")[0]  # WHY: the only correlation row.
    assert record.matched_count == 0  # WHY: nothing matched.
    assert "not visible to the Juniper account" in row["unmatchedReason"]  # WHY: the reason names the cause.
    assert any("No Mist ticket matched" in message for message in caplog.messages)  # WHY: the warning was logged.


def test_matched_ticket_fans_out_to_rma_items_with_the_personal_values_in_full() -> None:
    """A matched request writes its RMA item, and the export keeps the personal values in full."""
    gateway = FakeGateway(  # WHY: replies by endpoint.
        bodies={"querysrlist": [LIST_REPLY], "querysrdetails": [DETAIL_REPLY], "queryrmadetails": [RMA_REPLY]}
    )
    _record, exporter = _run([_ticket("t-1", "CASE-100")], gateway)  # WHY: one matched ticket.
    items = exporter.rows("JuniperRmaItems.csv")  # WHY: the item rows.
    assert len(items) == 1  # WHY: one defective item.
    assert items[0]["contactEmail"] == "jane.tester@example.com"  # WHY: the e-mail is kept in full.
    everything = str(exporter.writes)  # WHY: scan every written value.
    assert "jane.tester@example.com" in everything  # WHY: the raw e-mail reaches the export.
    assert "5555550199" in everything  # WHY: the raw telephone number reaches the export.


def test_older_ticket_uses_a_detail_lookup_and_fault_763_is_ambiguous() -> None:
    """A ticket older than 90 days is looked up by case number, and fault 763 marks it ambiguous."""
    gateway = FakeGateway(bodies={"querysrlist": [LIST_REPLY], "querysrdetails": [FAULT_763]})  # WHY: list, then fault.
    record, _exporter = _run([_ticket("t-9", "CASE-200", days_ago=200)], gateway)  # WHY: an older ticket.
    assert record.ambiguous_count == 1  # WHY: fault 763 means more than one request.
    lookup = gateway.calls_for("querysrdetails")[0].body["querySRRequest"]["caseInformation"]  # WHY: the lookup key.
    assert lookup["customerCaseNumber"] == "CASE-200"  # WHY: the detail lookup uses the case number.


def test_failed_request_list_writes_only_the_run_record() -> None:
    """When the request list fails, the run is failed and only the run record is written."""
    gateway = FakeGateway(failures={"querysrlist": [JuniperTransportError("connection lost")]})  # WHY: list call fails.
    record, exporter = _run([_ticket("t-1", "CASE-100")], gateway)  # WHY: one ticket.
    assert record.status == "failed"  # WHY: no ticket can be classified without the list.
    assert [name for name, _api, _rows in exporter.writes] == ["JuniperRunRecords.csv"]  # WHY: only the record.


def test_zero_tickets_still_writes_the_run_record() -> None:
    """A run with no tickets writes no correlation rows and still writes its record."""
    gateway = FakeGateway(bodies={"querysrlist": [LIST_REPLY]})  # WHY: an empty list.
    record, exporter = _run([], gateway)  # WHY: no tickets.
    assert record.ticket_count == 0  # WHY: no tickets were read.
    assert exporter.rows("JuniperCorrelation.csv") == []  # WHY: nothing to correlate.
    assert exporter.rows("JuniperRunRecords.csv")[0]["status"] == "complete"  # WHY: the record shows the run.


def test_failed_detail_call_marks_the_run_incomplete_and_keeps_the_reason() -> None:
    """A failed detail call leaves the matched request without detail and makes the run incomplete."""
    gateway = FakeGateway(  # WHY: replies for one ticket.
        bodies={"querysrlist": [LIST_REPLY]},
        failures={"querysrdetails": [JuniperTransportError("timeout")]},
    )
    record, _exporter = _run([_ticket("t-1", "CASE-100")], gateway)  # WHY: one ticket.
    assert record.status == "incomplete"  # WHY: a failed detail is an incomplete run.
    assert any("timeout" in problem for problem in record.problems)  # WHY: the reason is kept.


def test_join_on_the_mist_identifier_when_the_key_field_is_id() -> None:
    """With JUNIPER_TICKET_KEY_FIELD set to id, the Mist identifier is the value that is compared (O-1)."""
    gateway = FakeGateway(  # WHY: replies for a run.
        bodies={"querysrlist": [LIST_REPLY], "querysrdetails": [DETAIL_REPLY], "queryrmadetails": [RMA_REPLY]}
    )
    record, _exporter = _run(  # WHY: run the workflow.
        [MistTicket("CASE-100", "NOT-USED", "open", "s", str(int(NOW.timestamp())))], gateway, "id"
    )
    assert record.matched_count == 1  # WHY: the identifier matched the request's case number.
