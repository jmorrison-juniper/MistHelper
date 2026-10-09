"""Menus 294 to 297: the Juniper Case read menus. Each menu prints and saves every field that it reads."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log and operator messages for each read.
import re  # WHY: the note identifier rule is a whole-value pattern.
from datetime import UTC, date, datetime, timedelta  # WHY: the list window and its defaults.
from typing import Any  # WHY: the detail and note records are loosely typed.

from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: a failed call is reported, not raised.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: reply reading.
    ResponseOutcome,
    ResponseStatusReader,
)
from src.operations.exporting.juniper_rma.model.export_rows import ExportRowBuilder  # WHY: the RMA item column list.
from src.operations.exporting.juniper_rma.model.request_rows import (  # WHY: the column tables and row builders of the Case reads.  # noqa: E501
    DetailRecordRows,
    NoteRows,
    RequestDetailRows,
    RequestListRows,
    RmaHeaderRows,
    read_text,
)
from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: RMA item parsing for the items file.
    RmaItem,
    RmaRecord,
)
from src.operations.exporting.juniper_rma.settings import (
    JuniperServiceSession,  # WHY: the checked session for each menu.
)
from src.operations.exporting.juniper_rma.workflows.juniper_menu_support import (  # WHY: shared prompts, sink, and clock.  # noqa: E501
    CaseKeyPrompt,
    JuniperExportSink,
    JuniperMenuInput,
    records_of,
    utc_now_text,
)

logger = logging.getLogger(__name__)  # WHY: module logger for each Case read.


class RequestListWorkflow:
    """Menu 294: list the requests of the account in a date window, and save every field of each request."""

    MAX_WINDOW_DAYS = 90  # WHY: the Case list accepts at most 90 days (R-06).
    FILENAME = "JuniperRequestList.csv"  # WHY: the export of this menu.
    API_NAME = "juniperQuerySrList"  # WHY: the operation name recorded with the export.

    def __init__(self, session: JuniperServiceSession, sink: JuniperExportSink | None = None) -> None:
        """Store the checked session and the export sink. A test may inject a sink double."""
        self._session = session  # WHY: the Case service and the settings.
        self._sink = sink if sink is not None else JuniperExportSink()  # WHY: the shared export path.

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and run the list."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=True)  # WHY: refusal and setting checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to list.
        RequestListWorkflow(session).execute()  # WHY: the list itself.

    def execute(self) -> bool:
        """Ask for the window, read the list, print every field of each request, and write the export."""
        window = self._ask_window()  # WHY: the operator sets the dates before any call.
        if window is None:  # WHY: a rejected date stops before any call.
            return False  # WHY: nothing was sent.
        outcome = self._read(window[0], window[1])  # WHY: one list call.
        if outcome is None:  # WHY: the reason is already logged.
            return False  # WHY: nothing to export.
        retrieved = utc_now_text()  # WHY: one retrieval time for every row of this run.
        rows = [RequestListRows.row(raw, retrieved) for raw in records_of(outcome.result, "cases")]  # WHY: all fields.
        return self._sink.publish("Request list", self.FILENAME, self.API_NAME, RequestListRows.COLUMNS, rows)

    def _ask_window(self) -> tuple[date, date] | None:
        """Ask for the start and end dates. Return None when a date is invalid or the window is too wide."""
        today = datetime.now(UTC).date()  # WHY: the defaults are relative to today in UTC.
        start = JuniperMenuInput.day(  # WHY: the default start is 90 days back.
            "start date", today - timedelta(days=self.MAX_WINDOW_DAYS), "juniper_list_start"
        )
        if start is None:  # WHY: a rejected date stops the run.
            return None  # WHY: no call is made.
        end = JuniperMenuInput.day("end date", today, "juniper_list_end")  # WHY: the default end is today.
        if end is None:  # WHY: a rejected date stops the run.
            return None  # WHY: no call is made.
        if start > end or (end - start).days > self.MAX_WINDOW_DAYS:  # WHY: the window must be valid.
            logger.warning(
                "Input rejected: the menu could not run, because the start must precede the end, "
                "and the window must span 90 days or fewer"
            )
            return None  # WHY: no call is made.
        return start, end  # WHY: the checked window.

    def _read(self, start: date, end: date) -> ResponseOutcome | None:
        """Read the list. Return None when the call fails or Juniper does not accept the request."""
        logger.info("Juniper request list: window %s to %s", start.isoformat(), end.isoformat())  # WHY: action log.
        try:  # WHY: a transport failure is reported as a failed list.
            outcome = self._session.case.list_requests(from_day=start, to_day=end)  # WHY: one list call.
        except JuniperTransportError as error:  # WHY: keep the reason, never a secret.
            logger.error("Juniper request list failed to complete: %s", error)  # WHY: the operator sees the reason.
            return None  # WHY: no rows.
        if outcome.is_usable:  # WHY: a usable reply carries the list.
            return outcome  # WHY: the caller reads the rows.
        logger.error(  # WHY: the reason names what Juniper returned.
            "Juniper request list failed to complete: %s",  # The message keeps the cause.
            ResponseStatusReader.explain(outcome),  # The explanation names the next step.
        )
        return None  # WHY: no rows.


class RequestDetailWorkflow:
    """Menu 295: read one request by request number or case number, and save every field of its detail."""

    DETAIL_FILE = "JuniperRequestDetail.csv"  # WHY: one row with every scalar field of the detail.
    DETAIL_API = "juniperQuerySrDetails"  # WHY: the operation name recorded with the export.
    RECORDS_FILE = "JuniperRequestDetailRecords.csv"  # WHY: one row for each nested note, attachment, and RMA item.
    RECORDS_API = "juniperQuerySrDetailRecords"  # WHY: the operation name recorded with the export.

    def __init__(self, session: JuniperServiceSession, sink: JuniperExportSink | None = None) -> None:
        """Store the checked session and the export sink. A test may inject a sink double."""
        self._session = session  # WHY: the Case service.
        self._sink = sink if sink is not None else JuniperExportSink()  # WHY: the shared export path.

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and read one request."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=True)  # WHY: refusal and setting checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to read.
        RequestDetailWorkflow(session).execute()  # WHY: the detail read itself.

    def execute(self) -> bool:
        """Ask for the key, read the detail, print every field, and write both exports."""
        key = CaseKeyPrompt.ask()  # WHY: the key kind and value, checked before any call.
        if key is None:  # WHY: a cancelled or invalid key stops the run.
            logger.info("Juniper request detail cancelled: no valid key")  # WHY: the operator sees the reason.
            return False  # WHY: nothing was sent.
        outcome = CaseKeyPrompt.read_detail(self._session, key[0], key[1])  # WHY: one detail call.
        if outcome is None:  # WHY: the reason is already logged.
            return False  # WHY: nothing to export.
        retrieved = utc_now_text()  # WHY: one retrieval time for both exports.
        summary = [RequestDetailRows.row(outcome.result, retrieved)]  # WHY: every scalar field, one row.
        records = DetailRecordRows.rows(outcome.result, retrieved)  # WHY: every nested record, one row each.
        self._sink.publish("Request detail", self.DETAIL_FILE, self.DETAIL_API, RequestDetailRows.COLUMNS, summary)
        return self._sink.publish(  # WHY: the records export reports the result of the run.
            "Request detail records",
            self.RECORDS_FILE,
            self.RECORDS_API,
            DetailRecordRows.COLUMNS,
            records,
        )


class RmaDetailWorkflow:
    """Menu 296: read one RMA with its request, and save every field of the RMA and each of its items."""

    HEADER_FILE = "JuniperRmaDetail.csv"  # WHY: one row with every field of the RMA reply.
    HEADER_API = "juniperQueryRmaHeaders"  # WHY: the operation name recorded with the export.
    ITEMS_FILE = "JuniperRmaDetailItems.csv"  # WHY: one row for each defective, replacement, or CE item.
    ITEMS_API = "juniperQueryRmaDetails"  # WHY: the operation name recorded with the export.

    def __init__(self, session: JuniperServiceSession, sink: JuniperExportSink | None = None) -> None:
        """Store the checked session and the export sink. A test may inject a sink double."""
        self._session = session  # WHY: the Case service.
        self._sink = sink if sink is not None else JuniperExportSink()  # WHY: the shared export path.

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and read one RMA."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=True)  # WHY: refusal and setting checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to read.
        RmaDetailWorkflow(session).execute()  # WHY: the RMA read itself.

    def execute(self) -> bool:
        """Ask for the RMA, its request, and an optional case number, then read and export it."""
        values = self._ask_values()  # WHY: every input is checked before any call.
        if values is None:  # WHY: a rejected input stops the run.
            return False  # WHY: nothing was sent.
        outcome = self._read(*values)  # WHY: one RMA call.
        if outcome is None:  # WHY: the reason is already logged.
            return False  # WHY: nothing to export.
        retrieved = utc_now_text()  # WHY: one retrieval time for both exports.
        header = [RmaHeaderRows.row(outcome.result, retrieved)]  # WHY: every field of the reply.
        items = self._item_rows(values[0], values[1], outcome.result, retrieved)  # WHY: every item of the RMA.
        self._sink.publish("RMA detail", self.HEADER_FILE, self.HEADER_API, RmaHeaderRows.COLUMNS, header)
        return self._sink.publish(  # WHY: the items export reports the result of the run.
            "RMA detail items",
            self.ITEMS_FILE,
            self.ITEMS_API,
            ExportRowBuilder.RMA_ITEM_FIELDS,
            items,
        )

    @staticmethod
    def _ask_values() -> tuple[str, str, str] | None:
        """Ask for the RMA number, the request number, and an optional case number. None when one is invalid."""
        rma_number = JuniperMenuInput.identifier("RMA number", "juniper_rma_number")  # WHY: required.
        if rma_number is None:  # WHY: a missing or invalid RMA stops the run.
            return None  # WHY: no call is made.
        request_number = JuniperMenuInput.identifier("request number", "juniper_rma_request")  # WHY: required.
        if request_number is None:  # WHY: a missing or invalid request stops the run.
            return None  # WHY: no call is made.
        case_number = JuniperMenuInput.identifier(  # WHY: the case number is optional for these requests.
            "customer case number", "juniper_rma_case", required=False
        )
        if case_number is None:  # WHY: an invalid case number stops the run.
            return None  # WHY: no call is made.
        return rma_number, request_number, case_number  # WHY: the checked inputs.

    def _read(self, rma_number: str, request_number: str, case_number: str) -> ResponseOutcome | None:
        """Read the RMA. Return None when the call fails or Juniper does not accept the request."""
        logger.info("Juniper RMA detail read")  # WHY: action log before the call, no value.
        try:  # WHY: a transport failure is reported as a failed read.
            outcome = self._session.case.get_rma(rma_number, request_number, case_number)  # WHY: one RMA call.
        except JuniperTransportError as error:  # WHY: keep the reason.
            logger.error("Juniper RMA detail failed to complete: %s", error)  # WHY: the operator sees the reason.
            return None  # WHY: no export.
        if outcome.is_usable:  # WHY: a usable reply carries the RMA.
            return outcome  # WHY: the caller exports it.
        logger.error(  # WHY: the reason names what Juniper returned.
            "Juniper RMA detail failed to complete: %s",  # The message keeps the cause.
            ResponseStatusReader.explain(outcome),  # The explanation names the next step.
        )
        return None  # WHY: no export.

    @staticmethod
    def _item_rows(
        rma_number: str,
        request_number: str,
        result: dict[str, Any],
        retrieved: str,
    ) -> list[dict[str, str]]:
        """Return one row for each item of the RMA, with the RMA and request context."""
        rma = RmaRecord.from_result(result, request_number)  # WHY: the RMA context for each item row.
        items = RmaItem.parse_all(rma_number, result)  # WHY: every defective, replacement, and CE item.
        return [ExportRowBuilder.item_row(rma, item, retrieved) for item in items]  # WHY: the item rows.


class RequestNotesWorkflow:
    """Menu 297: read the notes of one request, and save every field of each note."""

    FILENAME = "JuniperRequestNotes.csv"  # WHY: one row for each note read.
    API_NAME = "juniperQuerySrNoteDetails"  # WHY: the operation name recorded with the export.
    NOTE_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,80}")  # WHY: note identifiers hold letters, digits, and - or _.

    def __init__(self, session: JuniperServiceSession, sink: JuniperExportSink | None = None) -> None:
        """Store the checked session and the export sink. A test may inject a sink double."""
        self._session = session  # WHY: the Case service.
        self._sink = sink if sink is not None else JuniperExportSink()  # WHY: the shared export path.

    @staticmethod
    def run() -> None:
        """Menu entry point. Open a checked session and read the notes of one request."""
        session = JuniperServiceSession.open_for_menu(needs_contact_email=True)  # WHY: refusal and setting checks.
        if session is None:  # WHY: the reason is already logged.
            return  # WHY: nothing to read.
        RequestNotesWorkflow(session).execute()  # WHY: the notes read itself.

    def execute(self) -> bool:
        """Read the detail for the note list, read each note, print every field, and write the export."""
        key = CaseKeyPrompt.ask()  # WHY: the request is found first, because its detail lists the notes.
        if key is None:  # WHY: a cancelled or invalid key stops the run.
            logger.info("Juniper request notes cancelled: no valid key")  # WHY: the operator sees the reason.
            return False  # WHY: nothing was sent.
        detail = CaseKeyPrompt.read_detail(self._session, key[0], key[1])  # WHY: one detail call.
        if detail is None:  # WHY: the reason is already logged.
            return False  # WHY: no notes to read.
        note_filter = self._ask_note_id()  # WHY: one note, or every note of the request.
        if note_filter is None:  # WHY: a rejected identifier stops the run.
            return False  # WHY: nothing was sent.
        targets = self._targets(detail.result, note_filter)  # WHY: the notes to read, without repeats.
        if not targets:  # WHY: nothing matches the request.
            logger.info("The request lists no note that matches the input")  # WHY: the operator sees the reason.
            return False  # WHY: nothing to export.
        return self._export(detail.result, targets)  # WHY: read each note and write the export.

    def _ask_note_id(self) -> str | None:
        """Ask for one note identifier, or a blank answer for every note. None when the identifier is invalid."""
        raw = JuniperMenuInput.text(  # WHY: the prompt explains the blank answer.
            "Enter one note identifier, or press Enter for every note of the request: ",
            "juniper_note_id",
        )
        if not raw:  # WHY: a blank answer means every note.
            return ""  # WHY: an empty filter keeps every note.
        if not self.NOTE_ID_PATTERN.fullmatch(raw):  # WHY: reject the value before any call.
            logger.warning(
                "Input rejected: the menu could not run, because the note identifier must be 1 to 80 "
                "letters, digits, hyphens, or _"
            )
            return None  # WHY: no call is made.
        return raw  # WHY: the checked identifier.

    @staticmethod
    def _targets(detail: dict[str, Any], note_filter: str) -> list[tuple[str, str, dict[str, Any]]]:
        """Return each distinct note as (identifier, source list, summary). A filter keeps one note."""
        found: list[tuple[str, str, dict[str, Any]]] = []  # WHY: the notes to read, in order.
        seen: set[str] = set()  # WHY: a note in both lists is read once.
        for source in ("notes", "recentNotes"):  # WHY: the full list first, then the recent list.
            for summary in records_of(detail, source):  # WHY: each summary object.
                note_id = read_text(summary, "id")  # WHY: the identifier that the note read needs.
                if not note_id or note_id in seen:  # WHY: skip blanks and repeats.
                    continue  # WHY: nothing to add.
                if note_filter and note_id != note_filter:  # WHY: the filter keeps one identifier.
                    continue  # WHY: another note.
                seen.add(note_id)  # WHY: remember the identifier.
                found.append((note_id, source, summary))  # WHY: keep the note and its summary.
        if note_filter and not found:  # WHY: an identifier that the list does not name is still read.
            found.append((note_filter, "", {}))  # WHY: the reply carries the note, with no summary.
        return found  # WHY: the notes to read.

    def _export(self, detail: dict[str, Any], targets: list[tuple[str, str, dict[str, Any]]]) -> bool:
        """Read each target note with the request keys, collect the rows, and publish them."""
        request_number = read_text(detail, "serviceRequestNumber")  # WHY: the note read needs the request.
        case_number = read_text(detail, "customerCaseNumber")  # WHY: the detail key, empty for these requests.
        retrieved = utc_now_text()  # WHY: one retrieval time for the run.
        rows: list[dict[str, str]] = []  # WHY: one row for each note that Juniper returns.
        for note_id, source, summary in targets:  # WHY: one read for each note.
            reply = self._read_note(note_id, request_number, case_number)  # WHY: one note call.
            if reply is not None:  # WHY: a failed note is logged and skipped.
                rows.append(NoteRows.row(note_id, source, summary, reply, retrieved))  # WHY: the row.
        return self._sink.publish("Request notes", self.FILENAME, self.API_NAME, NoteRows.COLUMNS, rows)

    def _read_note(self, note_id: str, request_number: str, case_number: str) -> dict[str, Any] | None:
        """Read one note. Return the reply result, or None when the call fails or Juniper refuses it."""
        logger.info("Juniper note read")  # WHY: action log before the call, no note value.
        try:  # WHY: a transport failure skips this note only.
            outcome = self._session.case.get_note(note_id, request_number, case_number)  # WHY: one note call.
        except JuniperTransportError as error:  # WHY: keep the reason.
            logger.error("Juniper note read failed: %s", error)  # WHY: the operator sees the reason.
            return None  # WHY: skip this note.
        if outcome.is_usable:  # WHY: a usable reply carries the note.
            return outcome.result  # WHY: the caller builds the row.
        logger.error("Juniper note read failed: %s", ResponseStatusReader.explain(outcome))  # WHY: the reason.
        return None  # WHY: skip this note.
