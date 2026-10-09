"""Menu 302: correlate Mist support tickets with Juniper service requests and RMA details.

The join rule (R-05) matches a ticket to every request with the same customer
case number. Tickets older than 90 days use a detail lookup (R-06). Matched
requests fan out to their RMAs and items. Every export goes through DataExporter.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log before each read, call, and export.
from dataclasses import dataclass  # WHY: immutable ticket, outcome, and detail records.
from datetime import UTC, datetime, timedelta  # WHY: the 90-day age rule for each ticket.
from typing import Any  # WHY: the exporter and the ticket reader are injected objects.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: mistapi without the root module.
)
from src.operations.exporting.export.data_exporter import (
    DataExporter,  # WHY: every export goes through the shared exporter.
)
from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a failed call marks one ticket only.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: reply reading.
    ResponseOutcome,
    ResponseStatusReader,
)
from src.operations.exporting.juniper_rma.model.export_rows import (  # WHY: the row builders and the retention purge.
    ExportRowBuilder,
    PersonalDataRetention,
)
from src.operations.exporting.juniper_rma.model.run_record import RunRecord  # WHY: counts, status, and the reason text.
from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: parsed records.
    RmaItem,
    RmaRecord,
    ServiceRequest,
)
from src.operations.exporting.juniper_rma.settings import (
    JuniperServiceSession,  # WHY: the checked session for this menu.
)

logger = logging.getLogger(__name__)  # WHY: module logger for each correlation step.


@dataclass(frozen=True)
class MistTicket:
    """The five ticket fields that the export keeps. Ticket comments are never read (R-16)."""

    ticket_id: str  # WHY: Mist ticket identifier, the join value when the key field is id.
    case_number: str  # WHY: Mist display name, the join value by default (O-1).
    status: str  # WHY: Mist status.
    subject: str  # WHY: Mist subject, free text and not masked (see the plan risks).
    created_at: str  # WHY: creation time as received, used for the 90-day rule.

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> MistTicket:
        """Build the ticket from one Mist row and keep only the five fields."""
        return cls(  # WHY: each field is read as trimmed text.
            ticket_id=str(row.get("id", "")).strip(),  # WHY: Mist identifier.
            case_number=str(row.get("case_number", "")).strip(),  # WHY: Mist display name.
            status=str(row.get("status", "")).strip(),  # WHY: Mist status.
            subject=str(row.get("subject", "")).strip(),  # WHY: Mist subject.
            created_at=str(row.get("created_at", "")).strip(),  # WHY: creation time as received.
        )

    def key_value(self, key_field: str) -> str:
        """Return the join value that JUNIPER_TICKET_KEY_FIELD names, with spaces removed."""
        value = self.case_number if key_field == "case_number" else self.ticket_id  # WHY: the configured field.
        return value.strip()  # WHY: spaces do not change the value.


class MistTicketReader:
    """Read the organization support tickets through the same mistapi listing as menu 188 (R-16)."""

    def read(self) -> list[MistTicket]:
        """Return the tickets of the last 365 days, with the five kept fields."""
        mh = SourceDependencyResolver  # WHY: resolve the SDK and the organization helper.
        logger.info("Reading Mist support tickets for the last 365 days")  # WHY: action log before the call.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # WHY: the cached or prompted organization.
        response = mh.mistapi.api.v1.orgs.tickets.listOrgTickets(
            mh.apisession, org_id, duration="365d"
        )  # WHY: menu 188.
        rows = mh.mistapi.get_all(response=response, mist_session=mh.apisession)  # WHY: page through all tickets.
        logger.debug("Read %d Mist support ticket rows", len(rows))  # WHY: count only.
        return [MistTicket.from_api(row) for row in rows if isinstance(row, dict)]  # WHY: keep the five fields.


@dataclass(frozen=True)
class RequestBundle:
    """One matched request with its RMA records and item records."""

    request: ServiceRequest  # WHY: the request detail.
    rmas: tuple[RmaRecord, ...]  # WHY: the RMA records of the request.
    items: tuple[RmaItem, ...]  # WHY: the items of every RMA of the request.


@dataclass(frozen=True)
class CorrelationOutcome:
    """The outcome of one ticket: matched, ambiguous, unmatched, or failed, with the reason."""

    ticket: MistTicket  # WHY: the Mist ticket that was classified.
    status: str  # WHY: matched, ambiguous, unmatched, or failed (failed is counted and exported as unmatched).
    reason: str  # WHY: plain-text reason for the operator and the export.
    request_numbers: tuple[str, ...] = ()  # WHY: the matched request, or the candidate requests.
    join_value: str = ""  # WHY: the value that was compared with the customer case number.

    def to_rows(self, details: dict[str, RequestBundle], run_id: str) -> list[dict[str, Any]]:
        """Return the correlation rows: one per RMA item for a matched ticket, otherwise one row."""
        base = self._base_row(run_id)  # WHY: the ticket columns repeat on every row of this ticket.
        if self.status != "matched" or not self.request_numbers:  # WHY: no request means one row only.
            return [base]  # WHY: the ticket with its reason.
        rows: list[dict[str, Any]] = []  # WHY: collect one row for each item of each matched request.
        for number in self.request_numbers:  # WHY: a matched ticket has one request number.
            bundle = details.get(number)  # WHY: the detail that the run fetched for this request.
            rows.extend(self._rows_for_bundle(base, bundle))  # WHY: one row per item, or one row for the request.
        return rows  # WHY: every correlation row of this ticket.

    def _base_row(self, run_id: str) -> dict[str, Any]:
        """Return the ticket columns with the match fields filled in."""
        export_status = "unmatched" if self.status == "failed" else self.status  # WHY: the contract has three statuses.
        return {  # WHY: the ticket columns; the request and item columns stay blank until a row adds them.
            "mistTicketId": self.ticket.ticket_id,  # WHY: Mist identifier.
            "mistCaseNumber": self.ticket.case_number,  # WHY: Mist display name.
            "joinValue": self.join_value,  # WHY: the compared value.
            "mistSubject": self.ticket.subject,  # WHY: Mist subject.
            "mistStatus": self.ticket.status,  # WHY: Mist status.
            "matchStatus": export_status,  # WHY: matched, ambiguous, or unmatched.
            "candidateCount": str(len(self.request_numbers)),  # WHY: the number of matching requests.
            "unmatchedReason": self.reason if export_status == "unmatched" else "",  # WHY: reason for unmatched.
            "serviceRequestNumber": "",  # WHY: filled in for a matched request.
            "candidateRequests": (
                ",".join(self.request_numbers) if export_status == "ambiguous" else ""
            ),  # WHY: ambiguous.
            "srStatus": "",  # WHY: filled in for a matched request.
            "rmaNumber": "",  # WHY: filled in for an item row.
            "itemType": "",  # WHY: filled in for an item row.
            "itemNumber": "",  # WHY: filled in for an item row.
            "serialNumber": "",  # WHY: filled in for an item row.
            "productID": "",  # WHY: filled in for an item row.
            "carrierDescription": "",  # WHY: filled in for an item row.
            "trackingNumber": "",  # WHY: filled in for an item row.
            "shipDate": "",  # WHY: filled in for an item row.
            "deliveredDate": "",  # WHY: filled in for an item row.
            "rmaStatus": "",  # WHY: filled in for an item row.
            "shipToCompany": "",  # WHY: filled in for an item row.
            "shipToContact": "",  # WHY: filled in for an item row.
            "shipToCityState": "",  # WHY: filled in for an item row.
            "shipToCountry": "",  # WHY: filled in for an item row.
            "runId": run_id,  # WHY: the run that produced the row.
        }

    def _rows_for_bundle(self, base: dict[str, Any], bundle: RequestBundle | None) -> list[dict[str, Any]]:
        """Return one row per item of the bundle, or one row for the request when it has no items."""
        if bundle is None:  # WHY: the detail call failed, so the request has no detail for this row.
            return [dict(base, serviceRequestNumber=self.request_numbers[0], srStatus="")]  # WHY: request only.
        request_part = {  # WHY: the request fields that the row keeps.
            "serviceRequestNumber": bundle.request.request_number,
            "srStatus": bundle.request.status,
        }
        if not bundle.items:  # WHY: a request with no items still gets one row.
            return [dict(base, **request_part)]  # WHY: the request columns only.
        rma_by_number = {rma.rma_number: rma for rma in bundle.rmas}  # WHY: look up the shipping data of each item.
        return [self._item_row(base, request_part, rma_by_number, item) for item in bundle.items]  # WHY: one per item.

    @staticmethod
    def _item_row(
        base: dict[str, Any],
        request_part: dict[str, str],
        rma_by_number: dict[str, RmaRecord],
        item: RmaItem,
    ) -> dict[str, Any]:
        """Return one correlation row for one RMA item, with its shipping fields."""
        rma = rma_by_number.get(item.rma_number)  # WHY: the RMA holds the shipping and contact data.
        shipping = {  # WHY: shipping columns, with the personal fields in full.
            "shipToCompany": rma.company_name if rma else "",  # WHY: business name.
            "shipToContact": rma.contact_name if rma else "",  # WHY: contact name, kept in full.
            "shipToCityState": f"{rma.city}, {rma.state}".strip(", ") if rma else "",  # WHY: business location.
            "shipToCountry": rma.country if rma else "",  # WHY: country name.
        }
        item_part = {  # WHY: item columns from the record.
            "rmaNumber": item.rma_number,  # WHY: parent RMA.
            "itemType": item.item_type,  # WHY: item type.
            "itemNumber": item.item_number,  # WHY: item number.
            "serialNumber": item.serial_number,  # WHY: serial number.
            "productID": item.product_id,  # WHY: product identifier.
            "carrierDescription": item.carrier,  # WHY: carrier.
            "trackingNumber": item.tracking_number,  # WHY: tracking number.
            "shipDate": item.ship_date,  # WHY: ship date as text.
            "deliveredDate": item.delivered_date,  # WHY: delivered date as text.
            "rmaStatus": item.status,  # WHY: item status.
        }
        return dict(base, **request_part, **item_part, **shipping)  # WHY: merge the four parts into one row.


class CorrelationEngine:
    """Apply the join rule (R-05) and the 90-day age rule (R-06) to each ticket."""

    RECENT_DAYS = 90  # WHY: the list operation covers this many days.

    def __init__(self, key_field: str, now: datetime | None = None) -> None:
        """Store the join field and the clock for this run."""
        self._key_field = key_field  # WHY: the configured join field.
        self._now = now if now is not None else datetime.now(UTC)  # WHY: one clock for the whole run.

    def join_value(self, ticket: MistTicket) -> str:
        """Return the join value of one ticket."""
        return ticket.key_value(self._key_field)  # WHY: the configured field decides the value.

    def is_recent(self, ticket: MistTicket) -> bool:
        """Return True when the ticket is inside the list window. An unreadable date uses the list path."""
        created = self._parse_created(ticket.created_at)  # WHY: the age needs a readable date.
        if created is None:  # WHY: an unreadable date cannot be aged, so it uses the list path.
            return True  # WHY: the list path needs no date.
        return created >= self._now - timedelta(days=self.RECENT_DAYS)  # WHY: inside the 90-day window.

    def classify_recent(self, ticket: MistTicket, requests: list[ServiceRequest]) -> CorrelationOutcome:
        """Match the ticket against the requests of the 90-day list. Two or more matches stay ambiguous."""
        join = self.join_value(ticket)  # WHY: the value to compare.
        if not join:  # WHY: an empty value cannot match anything.
            reason = f"The ticket has no value in {self._key_field}"  # WHY: name the empty field.
            return CorrelationOutcome(ticket, "unmatched", reason)  # WHY: the unmatched outcome.
        matches = tuple(
            request.request_number for request in requests if request.case_number == join
        )  # WHY: exact match.
        if len(matches) == 1:  # WHY: exactly one match is a matched link.
            return CorrelationOutcome(  # WHY: exactly one request, so the link is matched.
                ticket, "matched", "One request carries this case number", matches, join
            )
        if len(matches) > 1:  # WHY: two or more matches never choose one request (R-05).
            return CorrelationOutcome(  # WHY: two or more requests, so no request is chosen (R-05).
                ticket, "ambiguous", "More than one request carries this case number", matches, join
            )
        return CorrelationOutcome(  # WHY: no match in the window.
            ticket,
            "unmatched",
            "No request in the last 90 days carries this case number. The case is not visible to the "
            "Juniper account of this app, so ask Juniper to link the Mist case numbers to the account",
            (),
            join,
        )

    def classify_detail(
        self,
        ticket: MistTicket,
        join: str,
        outcome: ResponseOutcome,
        requests: list[ServiceRequest],
    ) -> CorrelationOutcome:
        """Classify an older ticket from its detail lookup by case number."""
        if outcome.has_fault("763"):  # WHY: fault 763 means the case number matches more than one request.
            candidates = tuple(
                request.request_number for request in requests if request.case_number == join
            )  # WHY: the request numbers that match.
            return CorrelationOutcome(  # WHY: fault 763 leaves several candidates, so no request is chosen.
                ticket, "ambiguous", "More than one request carries this case number", candidates, join
            )
        if outcome.is_usable:  # WHY: a usable detail names the one matching request.
            request = ServiceRequest.from_detail(outcome.result)  # WHY: read the request number from the detail.
            if request.request_number:  # WHY: a detail without a number cannot match.
                return CorrelationOutcome(  # WHY: the detail names exactly one request.
                    ticket, "matched", "One request carries this case number", (request.request_number,), join
                )
        return CorrelationOutcome(
            ticket, "unmatched", ResponseStatusReader.explain(outcome), (), join
        )  # WHY: the reason.

    @staticmethod
    def _parse_created(raw: str) -> datetime | None:
        """Parse epoch seconds or ISO text into an aware UTC time. Return None when the text is unreadable."""
        text = raw.strip()  # WHY: spaces are not part of the value.
        if not text:  # WHY: an empty value has no date.
            return None  # WHY: the caller uses the list path.
        try:  # WHY: a malformed value is not a crash.
            if text.replace(".", "", 1).isdigit():  # WHY: epoch seconds, optionally with a fraction.
                return datetime.fromtimestamp(float(text), tz=UTC)  # WHY: convert the epoch.
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))  # WHY: ISO text with a Z suffix.
        except (ValueError, OverflowError, OSError):  # WHY: any parse failure means no date.
            return None  # WHY: the caller uses the list path.
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)  # WHY: aware UTC.


class CorrelationWorkflow:
    """Run menu 302 end to end. Each ticket gets one outcome. Every export goes through DataExporter."""

    def __init__(
        self,
        session: JuniperServiceSession,
        ticket_reader: MistTicketReader | None = None,
        exporter: Any = DataExporter,
        now: datetime | None = None,
    ) -> None:
        """Store the session, the ticket source, the exporter, and the clock."""
        self._session = session  # WHY: the Juniper services and the settings.
        self._tickets = ticket_reader if ticket_reader is not None else MistTicketReader()  # WHY: Mist tickets.
        self._exporter = exporter  # WHY: the shared exporter (a test may inject a double).
        self._engine = CorrelationEngine(session.settings.ticket_key_field, now)  # WHY: the join and age rules.
        self._now = now if now is not None else datetime.now(UTC)  # WHY: one timestamp for the exports.

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and run the correlation."""
        session = JuniperServiceSession.open_for_menu()  # WHY: the automated modes and missing settings stop here.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to run.
        CorrelationWorkflow(session).execute()  # WHY: the full correlation.

    def execute(self) -> RunRecord:
        """Run the correlation, write the exports, and return the run record."""
        record = RunRecord("juniper_rma_correlation")  # WHY: one record for this run.
        logger.info("Menu 302: starting Juniper RMA correlation (run %s)", record.run_id)  # WHY: action log.
        record.purged_count = PersonalDataRetention(self._session.settings.retention_days).purge()  # WHY: purge first.
        tickets = self._tickets.read()  # WHY: the Mist tickets to correlate.
        record.ticket_count = len(tickets)  # WHY: count for the summary.
        recent = self._load_recent_requests(record)  # WHY: the request list of the last 90 days.
        if recent is None:  # WHY: without the list, no ticket can be classified.
            return self._finish_failed(record)  # WHY: write the record and stop.
        outcomes = [self._classify(ticket, recent, record) for ticket in tickets]  # WHY: one outcome per ticket.
        details = self._fetch_details(outcomes, record)  # WHY: detail and RMA data of the matched requests.
        self._export(outcomes, details, record)  # WHY: exports through DataExporter.
        record.finish()  # WHY: the final status after all the work.
        self._write_run(record)  # WHY: the run record is written last.
        logger.info(self._summary(record))  # WHY: the completion line for the operator.
        if record.ticket_count and not record.matched_count:  # WHY: zero matches needs an explanation.
            logger.warning(  # WHY: tell the operator that the join key is the cause, not a program fault.
                "No Mist ticket matched a Juniper request. The Mist case numbers are not visible to the "
                "Juniper account of this app. Ask Juniper to link them, then run menu 302 again."
            )
        return record  # WHY: the caller may inspect the counts.

    def _finish_failed(self, record: RunRecord) -> RunRecord:
        """Finish a run that could not read the request list, and write its record."""
        record.finish(status="failed")  # WHY: the status depends on the reason that the list call stored.
        self._write_run(record)  # WHY: the record shows why nothing was correlated.
        logger.error(self._summary(record))  # WHY: the operator sees the failed status.
        return record  # WHY: the caller sees the failed record.

    def _load_recent_requests(self, record: RunRecord) -> list[ServiceRequest] | None:
        """Read the request list of the last 90 days. Return None when the call fails."""
        logger.info("Reading the Juniper request list for the last 90 days")  # WHY: action log before the call.
        record.add_requests()  # WHY: count the call.
        try:  # WHY: a transport failure is a run problem, not a crash.
            outcome = self._session.case.list_requests()  # WHY: the default 90-day window.
        except JuniperTransportError as error:  # WHY: keep the reason, never a secret.
            record.note_problem(f"The Juniper request list call failed: {error}")  # WHY: the reason for the run.
            return None  # WHY: no list, no correlation.
        if not outcome.is_usable:  # WHY: a fault gives no list.
            record.note_problem(
                f"The Juniper request list failed: {ResponseStatusReader.explain(outcome)}"
            )  # WHY: reason.
            return None  # WHY: no list, no correlation.
        rows = outcome.result.get("cases")  # WHY: the list rows sit under cases (contract).
        row_list = rows if isinstance(rows, list) else []  # WHY: an odd value has no rows.
        requests = [ServiceRequest.from_list_row(row) for row in row_list if isinstance(row, dict)]  # WHY: parse rows.
        logger.debug("Juniper request list held %d requests", len(requests))  # WHY: count only.
        return requests  # WHY: the list for the classification.

    def _classify(self, ticket: MistTicket, recent: list[ServiceRequest], record: RunRecord) -> CorrelationOutcome:
        """Classify one ticket. A failed Juniper call marks only this ticket as failed."""
        try:  # WHY: a transport failure must not stop the other tickets.
            if self._engine.is_recent(ticket):  # WHY: a recent ticket uses the list.
                outcome = self._engine.classify_recent(ticket, recent)  # WHY: no extra call needed.
            else:  # WHY: an older ticket is outside the list window.
                outcome = self._classify_older(ticket, recent, record)  # WHY: a detail lookup by case number.
        except JuniperTransportError as error:  # WHY: keep the reason, never a secret.
            record.note_problem(f"A Juniper call failed for one ticket: {error}")  # WHY: the run is incomplete.
            outcome = CorrelationOutcome(
                ticket,
                "failed",
                f"Juniper call failed: {error}",
                (),
                ticket.key_value(self._session.settings.ticket_key_field),
            )  # WHY: the ticket is counted as failed.
        record.record_outcome(outcome.status)  # WHY: count the outcome.
        return outcome  # WHY: the outcome for the export.

    def _classify_older(
        self, ticket: MistTicket, recent: list[ServiceRequest], record: RunRecord
    ) -> CorrelationOutcome:
        """Classify a ticket older than 90 days with a detail lookup by customer case number (R-06)."""
        join = self._engine.join_value(ticket)  # WHY: the value to look up.
        if not join:  # WHY: an empty value cannot be looked up.
            return self._engine.classify_recent(ticket, recent)  # WHY: the same unmatched reason as before.
        record.add_requests()  # WHY: count the detail call.
        logger.info("Reading the Juniper request detail for one older ticket by case number")  # WHY: action log.
        outcome = self._session.case.get_request(case_number=join)  # WHY: one detail call.
        return self._engine.classify_detail(ticket, join, outcome, recent)  # WHY: classify the reply.

    def _fetch_details(self, outcomes: list[CorrelationOutcome], record: RunRecord) -> dict[str, RequestBundle]:
        """Fetch the detail of each distinct matched request once. Return the bundles by request number."""
        numbers: list[str] = []  # WHY: distinct request numbers in the order of the tickets.
        for outcome in outcomes:  # WHY: one pass over the outcomes.
            if outcome.status != "matched":  # WHY: only matched tickets have a request to read.
                continue  # WHY: skip the rest.
            for number in outcome.request_numbers:  # WHY: a matched ticket holds one request number.
                if number and number not in numbers:  # WHY: each request is read once.
                    numbers.append(number)  # WHY: keep the first occurrence.
        details: dict[str, RequestBundle] = {}  # WHY: the bundles by request number.
        for number in numbers:  # WHY: one detail per distinct request.
            bundle = self._fetch_bundle(number, record)  # WHY: the request with its RMAs and items.
            if bundle is not None:  # WHY: a failed read has no bundle.
                details[number] = bundle  # WHY: keep it for the export.
        return details  # WHY: the bundles for the rows.

    def _fetch_bundle(self, number: str, record: RunRecord) -> RequestBundle | None:
        """Read one request detail, then each RMA it lists. Return None when the detail is not usable."""
        logger.info("Reading the detail of one matched Juniper request")  # WHY: action log before the call.
        try:  # WHY: a transport failure leaves this request without detail.
            record.add_requests()  # WHY: count the detail call.
            outcome = self._session.case.get_request(request_number=number)  # WHY: the request detail.
        except JuniperTransportError as error:  # WHY: keep the reason.
            record.note_problem(f"A request detail call failed: {error}")  # WHY: the run is incomplete.
            return None  # WHY: no detail for this request.
        if not outcome.is_usable:  # WHY: a fault gives no detail.
            record.note_problem(f"A request detail was not returned: {ResponseStatusReader.explain(outcome)}")  # WHY.
            return None  # WHY: no detail for this request.
        request = ServiceRequest.from_detail(outcome.result)  # WHY: the parsed request.
        rmas, items = self._fetch_rmas(request, record)  # WHY: the RMA fan-out of this request.
        return RequestBundle(request=request, rmas=tuple(rmas), items=tuple(items))  # WHY: the complete bundle.

    def _fetch_rmas(self, request: ServiceRequest, record: RunRecord) -> tuple[list[RmaRecord], list[RmaItem]]:
        """Read each RMA that the request lists. A failed RMA read marks the run incomplete."""
        rmas: list[RmaRecord] = []  # WHY: the RMA records that were read.
        items: list[RmaItem] = []  # WHY: the items of those RMAs.
        for rma_number in request.rma_numbers:  # WHY: one RMA read for each RMA of the request.
            try:  # WHY: a failed RMA read must not stop the other RMAs.
                record.add_requests()  # WHY: count the RMA call.
                outcome = self._session.case.get_rma(rma_number, request.request_number, request.case_number)  # WHY.
            except JuniperTransportError as error:  # WHY: keep the reason.
                record.note_problem(f"An RMA detail call failed: {error}")  # WHY: the run is incomplete.
                continue  # WHY: the next RMA.
            if not outcome.is_usable:  # WHY: a fault gives no RMA detail.
                record.note_problem(f"An RMA detail was not returned: {ResponseStatusReader.explain(outcome)}")  # WHY.
                continue  # WHY: the next RMA.
            rmas.append(RmaRecord.from_result(outcome.result, request.request_number))  # WHY: the shipping record.
            items.extend(RmaItem.parse_all(rma_number, outcome.result))  # WHY: the item records.
        return rmas, items  # WHY: the RMA records and the items.

    def _export(
        self,
        outcomes: list[CorrelationOutcome],
        details: dict[str, RequestBundle],
        record: RunRecord,
    ) -> None:
        """Write the correlation, request, and RMA item exports through DataExporter."""
        retrieved = self._now.isoformat(timespec="seconds")  # WHY: one run time for every row.
        correlation_rows = [row for outcome in outcomes for row in outcome.to_rows(details, record.run_id)]  # WHY.
        request_rows = [ExportRowBuilder.request_row(bundle.request, retrieved) for bundle in details.values()]  # WHY.
        item_rows = self._item_rows(details, retrieved)  # WHY: item rows for every detail.
        self._write(  # WHY: the correlation links for the operator.
            "JuniperCorrelation.csv", correlation_rows, "juniperCorrelationLinks", ExportRowBuilder.CORRELATION_FIELDS
        )
        self._write(  # WHY: one row for each service request.
            "JuniperServiceRequests.csv", request_rows, "juniperQuerySrDetails", ExportRowBuilder.REQUEST_FIELDS
        )
        self._write(  # WHY: one row for each RMA item.
            "JuniperRmaItems.csv", item_rows, "juniperQueryRmaDetails", ExportRowBuilder.RMA_ITEM_FIELDS
        )

    @staticmethod
    def _item_rows(details: dict[str, RequestBundle], retrieved: str) -> list[dict[str, Any]]:
        """Return one row for each RMA item that has its RMA record."""
        rows: list[dict[str, Any]] = []  # WHY: collect the rows across the bundles.
        for bundle in details.values():  # WHY: one pass over the bundles.
            rma_by_number = {rma.rma_number: rma for rma in bundle.rmas}  # WHY: the shipping data of each RMA.
            for item in bundle.items:  # WHY: one row per item.
                rma = rma_by_number.get(item.rma_number)  # WHY: the RMA that holds the contact data.
                if rma is not None:  # WHY: an item without its RMA record has nothing to join.
                    rows.append(ExportRowBuilder.item_row(rma, item, retrieved))  # WHY: the row.
        return rows  # WHY: every item row.

    def _write(self, filename: str, rows: list[dict[str, Any]], api_name: str, fieldnames: list[str]) -> None:
        """Write one export through DataExporter. An empty output is logged, not written."""
        if not rows:  # WHY: DataExporter rejects empty data, so an empty output is logged instead.
            logger.info("No rows for %s, so no file was written", filename)  # WHY: the operator sees the reason.
            return  # WHY: nothing to write.
        logger.info("Writing %d row(s) to %s", len(rows), filename)  # WHY: action log before the write.
        cleaned = ExportRowBuilder.ascii_rows(rows)  # WHY: FR-029 ASCII-only output before the write.
        self._exporter.write_with_format_selection(  # WHY: write the rows through the shared export path.
            cleaned,
            filename,
            api_function_name=api_name,  # WHY: the operation name picks the primary key strategy.
            fieldnames=fieldnames,
        )

    def _write_run(self, record: RunRecord) -> None:
        """Write the run record. The record always holds one row."""
        self._write(
            "JuniperRunRecords.csv", [record.as_row()], "juniperRunRecords", ExportRowBuilder.RUN_FIELDS
        )  # WHY.

    @staticmethod
    def _summary(record: RunRecord) -> str:
        """Return the one-line completion message. It holds counts and the status only."""
        return (  # WHY: the contract line, with no key and no personal value.
            f"Juniper correlation complete: status={record.status} tickets={record.ticket_count} "
            f"matched={record.matched_count} ambiguous={record.ambiguous_count} "
            f"unmatched={record.unmatched_count} failed={record.failed_count} requests={record.request_count}"
        )
