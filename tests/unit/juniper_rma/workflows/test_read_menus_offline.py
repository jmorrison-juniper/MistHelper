"""Offline tests for menus 294 to 300 and for the RMA item export of menu 303.

The operator answers come from a scripted input. The exports go to a capturing exporter, so no file is written.
Every reply comes from the synthetic fixtures, and the gateway is a fake that never opens a connection.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import logging  # WHY: caplog levels for the operator messages.
from datetime import UTC, datetime, timedelta  # WHY: the default and the rejected snapshot windows.
from typing import Any  # WHY: the captured rows are loosely typed.

import pytest  # WHY: fixtures and monkeypatching of the scripted input.

from src.operations.exporting.juniper_rma.api.gateway import JuniperTransportError  # WHY: the error the fake can raise.
from src.operations.exporting.juniper_rma.model.export_rows import ExportRowBuilder  # WHY: the RMA item column list.
from src.operations.exporting.juniper_rma.model.reference_rows import (  # WHY: columns.
    BulkLinkRows,
    LovRows,
    SoftwareVersionRows,
)
from src.operations.exporting.juniper_rma.model.request_rows import (  # WHY.
    DetailRecordRows,
    RequestDetailRows,
    RequestListRows,
)
from src.operations.exporting.juniper_rma.workflows.case_reads import (  # WHY: the Case menus under test.
    RequestDetailWorkflow,
    RequestListWorkflow,
    RequestNotesWorkflow,
    RmaDetailWorkflow,
)
from src.operations.exporting.juniper_rma.workflows.juniper_menu_support import (  # WHY: input.
    JuniperExportSink,
    JuniperMenuInput,
)
from src.operations.exporting.juniper_rma.workflows.lookup import (
    LookupWorkflow,  # WHY: menu 303, changed by this feature.
)
from src.operations.exporting.juniper_rma.workflows.reference_reads import (  # WHY: the reference and bulk menus under test.  # noqa: E501
    AssetBulkWorkflow,
    LovWorkflow,
    SoftwareVersionWorkflow,
)
from tests.unit.juniper_rma.fixtures import read_replies as replies  # WHY: synthetic replies in the live shape.
from tests.unit.juniper_rma.fixtures.capturing import CapturingExporter, ScriptedAnswers  # WHY: shared doubles.
from tests.unit.juniper_rma.fixtures.fake_gateway import FakeGateway, build_session, make_settings  # WHY: fakes.


def _script(monkeypatch: pytest.MonkeyPatch, answers: dict[str, str]) -> None:
    """Route every operator prompt of the Juniper menus through the scripted answers."""
    monkeypatch.setattr(JuniperMenuInput, "text", staticmethod(ScriptedAnswers(answers)))  # WHY: one input path.


def _sink() -> tuple[JuniperExportSink, CapturingExporter]:
    """Return a sink that writes through a capturing exporter, and the exporter for assertions."""
    exporter = CapturingExporter()  # WHY: the recorder that stands in for the file writer.
    return JuniperExportSink(exporter), exporter  # WHY: the real sink, so the printing and cleaning run.


def _every_value_is_ascii(rows: list[dict[str, Any]]) -> bool:
    """Return True when every text value in the rows is ASCII only."""
    for row in rows:  # WHY: check each row.
        for value in row.values():  # WHY: check each value.
            if isinstance(value, str) and not value.isascii():  # WHY: the output is ASCII only.
                return False  # WHY: a non-ASCII value reached the output.
    return True  # WHY: every value is ASCII.


def test_294_lists_every_field_keeps_personal_values_and_exports_every_column(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The default window is the last 90 days, the row keeps every column, and each column is printed."""
    caplog.set_level(logging.INFO)  # WHY: the printed rows are info lines.
    _script(monkeypatch, {})  # WHY: Enter for both dates, which keeps the defaults.
    gateway = FakeGateway(bodies={"querysrlist": [replies.list_reply()]})  # WHY: one usable list reply.
    sink, exporter = _sink()  # WHY: capture the export.
    assert RequestListWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export of this menu.
    assert (write.filename, write.api) == ("JuniperRequestList.csv", "juniperQuerySrList")  # WHY: the file and key.
    assert write.fieldnames == RequestListRows.COLUMNS  # WHY: the header is the full column list.
    assert len(write.rows) == 1 and set(write.rows[0]) == set(RequestListRows.COLUMNS)  # WHY: every field, once.
    assert write.rows[0]["contactEmail"] == "pat.example@example.com"  # WHY: the e-mail is kept in full.
    assert _every_value_is_ascii(write.rows)  # WHY: no non-ASCII text.
    for column in RequestListRows.COLUMNS:  # WHY: each column appears in the printed row.
        assert f"{column}=" in caplog.text, f"column {column} was not printed"  # WHY: the operator sees it.
    window = gateway.calls_for("querysrlist")[0].body["querySRListRequest"]["caseInformation"]  # WHY: the call.
    assert window["fromDate"] < window["toDate"]  # WHY: the default window spans days.


def test_294_rejects_a_window_wider_than_90_days_before_any_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """A window of more than 90 days is refused, and no request is sent."""
    today = datetime.now(UTC).date()  # WHY: the window is relative to today.
    _script(monkeypatch, {"juniper_list_start": (today - timedelta(days=120)).isoformat()})  # WHY: too wide.
    gateway = FakeGateway()  # WHY: any call would be recorded.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert RequestListWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: refused.
    assert gateway.calls == [] and exporter.writes == []  # WHY: no call and no export.


def test_294_a_transport_failure_is_reported_and_nothing_is_written(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A transport failure after the retries stops the menu, and the reason is logged."""
    caplog.set_level(logging.ERROR)  # WHY: the failure is an error line.
    _script(monkeypatch, {})  # WHY: default window.
    failure = JuniperTransportError("Juniper querysrlist failed after 3 attempts (ConnectionError)")  # WHY.
    gateway = FakeGateway(failures={"querysrlist": [failure]})  # WHY: the call fails.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert RequestListWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: stopped.
    assert exporter.writes == [] and "failed after 3 attempts" in caplog.text  # WHY: no export, reason logged.


def test_295_reads_the_detail_by_request_number_and_exports_summary_and_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The request-number key reads the detail, the summary row keeps every field, and the records are exported."""
    _script(monkeypatch, {"juniper_key_kind": "1", "juniper_key_value": replies.SR_NUMBER})  # WHY: the key.
    gateway = FakeGateway(bodies={"querysrdetails": [replies.detail_reply()]})  # WHY: one detail reply.
    sink, exporter = _sink()  # WHY: capture both exports.
    assert RequestDetailWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    summary, records = exporter.writes  # WHY: the two exports, in order.
    assert [summary.filename, records.filename] == ["JuniperRequestDetail.csv", "JuniperRequestDetailRecords.csv"]
    assert summary.fieldnames == RequestDetailRows.COLUMNS  # WHY: the summary header.
    assert records.fieldnames == DetailRecordRows.COLUMNS  # WHY: the records header.
    assert len(summary.rows) == 1 and len(records.rows) == 8  # WHY: 2 notes, 2 recent, 1 file, 1 escalation, 2 RMA.
    assert summary.rows[0]["contactEmail"] == "pat.example@example.com"  # WHY: the contact e-mail is kept in full.
    assert _every_value_is_ascii(summary.rows + records.rows)  # WHY: no non-ASCII text in either export.
    body = gateway.calls_for("querysrdetails")[0].body["querySRRequest"]["caseInformation"]  # WHY: the key sent.
    assert (body["serviceRequestNumber"], body["customerCaseNumber"]) == (replies.SR_NUMBER, "")  # WHY.


def test_295_reads_the_detail_by_customer_case_number(monkeypatch: pytest.MonkeyPatch) -> None:
    """The case-number key sends the case number, and the request number stays empty."""
    _script(monkeypatch, {"juniper_key_kind": "2", "juniper_key_value": replies.CASE_NUMBER})  # WHY: the key.
    gateway = FakeGateway(bodies={"querysrdetails": [replies.detail_reply()]})  # WHY: one detail reply.
    sink, _exporter = _sink()  # WHY: the export is not checked here.
    assert RequestDetailWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    body = gateway.calls_for("querysrdetails")[0].body["querySRRequest"]["caseInformation"]  # WHY: the key sent.
    assert (body["customerCaseNumber"], body["serviceRequestNumber"]) == (replies.CASE_NUMBER, "")  # WHY: the case key.


def test_295_a_request_that_is_not_found_writes_nothing_and_says_so(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Fault 756 means no request matches for the account. The menu says so and writes nothing."""
    caplog.set_level(logging.INFO)  # WHY: the not-found message is an info line.
    _script(monkeypatch, {"juniper_key_kind": "1", "juniper_key_value": replies.SR_NUMBER})  # WHY: the key.
    fault = replies.fault_reply("756", "customerCaseNumber is not linked to the account")  # WHY: the fault body.
    gateway = FakeGateway(bodies={"querysrdetails": [fault]}, statuses={"querysrdetails": [400]})  # WHY: 400 body.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert RequestDetailWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: stopped.
    assert exporter.writes == [] and "No Juniper request matches" in caplog.text  # WHY: no export, clear message.


def test_295_an_invalid_key_kind_stops_before_any_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the choices 1 and 2 are valid. Any other answer cancels the menu before a call."""
    _script(monkeypatch, {"juniper_key_kind": "3"})  # WHY: an invalid choice.
    gateway = FakeGateway()  # WHY: any call would be recorded.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert RequestDetailWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: cancelled.
    assert gateway.calls == [] and exporter.writes == []  # WHY: no call and no export.


def test_296_exports_the_rma_header_and_every_item(monkeypatch: pytest.MonkeyPatch) -> None:
    """The RMA menu writes one header row and one row for each item, with the contact values in full."""
    _script(
        monkeypatch,
        {"juniper_rma_number": replies.RMA_NUMBER, "juniper_rma_request": replies.SR_NUMBER, "juniper_rma_case": ""},
    )  # WHY: the RMA, the request, and an empty optional case.
    gateway = FakeGateway(bodies={"queryrmadetails": [replies.rma_reply()]})  # WHY: one RMA reply.
    sink, exporter = _sink()  # WHY: capture both exports.
    assert RmaDetailWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    header, items = exporter.writes  # WHY: the two exports, in order.
    assert (header.filename, header.api) == ("JuniperRmaDetail.csv", "juniperQueryRmaHeaders")  # WHY: header key.
    assert (items.filename, items.api) == ("JuniperRmaDetailItems.csv", "juniperQueryRmaDetails")  # WHY: items key.
    assert len(header.rows) == 1 and len(items.rows) == 2  # WHY: one RMA and two items.
    assert items.fieldnames == ExportRowBuilder.RMA_ITEM_FIELDS  # WHY: the full item column list.
    assert items.rows[1]["receivedBy"] == "Dana Example"  # WHY: the receiver name is kept in full.
    assert _every_value_is_ascii(header.rows + items.rows)  # WHY: no non-ASCII text in either export.


def test_296_without_an_rma_number_nothing_is_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    """The RMA number is required. A blank answer cancels the menu before any call."""
    _script(monkeypatch, {"juniper_rma_request": replies.SR_NUMBER})  # WHY: the RMA is left blank.
    gateway = FakeGateway()  # WHY: any call would be recorded.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert RmaDetailWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: cancelled.
    assert gateway.calls == [] and exporter.writes == []  # WHY: no call and no export.


def test_297_reads_each_distinct_note_once_and_exports_full_content(monkeypatch: pytest.MonkeyPatch) -> None:
    """Notes from both lists are read once each. Content is kept in full, and every row has the full columns."""
    _script(monkeypatch, {"juniper_key_kind": "1", "juniper_key_value": replies.SR_NUMBER})  # WHY: every note.
    gateway = FakeGateway(
        bodies={
            "querysrdetails": [replies.detail_reply()],
            "querysrnotedetails": [
                replies.note_reply(replies.NOTE_ID_ONE),
                replies.note_reply(replies.NOTE_ID_TWO),
                replies.note_reply(replies.NOTE_ID_THREE),
            ],
        }
    )  # WHY: three distinct notes across the two lists.
    sink, exporter = _sink()  # WHY: capture the notes export.
    assert RequestNotesWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export of this menu.
    assert (write.filename, write.api) == ("JuniperRequestNotes.csv", "juniperQuerySrNoteDetails")  # WHY: the key.
    sent = [call.body["querySRNoteRequest"]["noteId"] for call in gateway.calls_for("querysrnotedetails")]  # WHY.
    assert sent == [replies.NOTE_ID_ONE, replies.NOTE_ID_TWO, replies.NOTE_ID_THREE]  # WHY: each note once.
    assert len(write.rows) == 3 and _every_value_is_ascii(write.rows)  # WHY: the rows and the ASCII text.


def test_297_one_named_note_reads_only_that_note(monkeypatch: pytest.MonkeyPatch) -> None:
    """A note identifier in the answer limits the read to that note."""
    _script(
        monkeypatch,
        {"juniper_key_kind": "1", "juniper_key_value": replies.SR_NUMBER, "juniper_note_id": replies.NOTE_ID_TWO},
    )  # WHY: one identifier.
    gateway = FakeGateway(
        bodies={
            "querysrdetails": [replies.detail_reply()],
            "querysrnotedetails": [replies.note_reply(replies.NOTE_ID_TWO)],
        }
    )  # WHY: one note reply.
    sink, exporter = _sink()  # WHY: capture the export.
    assert RequestNotesWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    assert [call.body["querySRNoteRequest"]["noteId"] for call in gateway.calls_for("querysrnotedetails")] == [
        replies.NOTE_ID_TWO
    ]  # WHY: only the named note is read.
    assert len(exporter.writes[0].rows) == 1  # WHY: one row for the one note.


def test_297_an_invalid_note_identifier_is_rejected_before_any_note_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """A note identifier with a space or a symbol is refused before a note read."""
    _script(
        monkeypatch,
        {"juniper_key_kind": "1", "juniper_key_value": replies.SR_NUMBER, "juniper_note_id": "bad id!"},
    )  # WHY: an invalid identifier.
    gateway = FakeGateway(bodies={"querysrdetails": [replies.detail_reply()]})  # WHY: only the detail is read.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert RequestNotesWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: refused.
    assert gateway.calls_for("querysrnotedetails") == [] and exporter.writes == []  # WHY: no note call.


def test_298_exports_every_lov_value_with_its_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The list of values writes one row for each scalar value, and the request carries the appid parameter."""
    _script(monkeypatch, {})  # WHY: the menu asks no question.
    gateway = FakeGateway(bodies={"getlov": [replies.lov_reply()]})  # WHY: one list reply.
    sink, exporter = _sink()  # WHY: capture the export.
    assert LovWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export.
    assert (write.filename, write.api) == ("JuniperLovs.csv", "juniperGetLov")  # WHY: the file and key.
    assert write.fieldnames == list(LovRows.COLUMNS) and len(write.rows) == 7  # WHY: seven scalar values.
    assert gateway.calls_for("getlov")[0].query == {"appid": make_settings().app_id}  # WHY: the GET parameter.


def test_299_exports_every_release_of_every_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """The software list writes one row for each release, and a platform with no release keeps one row."""
    _script(monkeypatch, {})  # WHY: the menu asks no question.
    gateway = FakeGateway(bodies={"getSoftwareEosLov": [replies.eos_reply()]})  # WHY: one software reply.
    sink, exporter = _sink()  # WHY: capture the export.
    assert SoftwareVersionWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export.
    assert (write.filename, write.api) == ("JuniperSoftwareVersions.csv", "juniperGetSoftwareEosLov")  # WHY: keys.
    assert (
        write.fieldnames == list(SoftwareVersionRows.COLUMNS) and len(write.rows) == 3
    )  # WHY: two releases and one empty.


def test_300_exports_masked_links_and_the_no_data_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid snapshot window writes the masked links and the no-data dates, and no signature leaves the menu."""
    today = datetime.now(UTC).date()  # WHY: the window is relative to today.
    _script(
        monkeypatch,
        {
            "juniper_bulk_start": (today - timedelta(days=7)).isoformat(),
            "juniper_bulk_end": (today - timedelta(days=1)).isoformat(),
        },
    )  # WHY: the oldest and the newest allowed days.
    gateway = FakeGateway(bodies={"queryAssetsBulkData": [replies.bulk_reply()]})  # WHY: one bulk reply.
    sink, exporter = _sink()  # WHY: capture both exports.
    assert AssetBulkWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    links, no_data = exporter.writes  # WHY: the two exports, in order.
    assert (links.filename, links.api) == ("JuniperAssetBulkLinks.csv", "juniperQueryAssetsBulkData")  # WHY: keys.
    assert links.fieldnames == list(BulkLinkRows.LINK_COLUMNS) and len(links.rows) == 1  # WHY: one link.
    assert links.rows[0]["urlMasked"].endswith("?[masked]")  # WHY: the query is replaced by the mask.
    assert no_data.fieldnames == list(BulkLinkRows.NO_DATA_COLUMNS) and len(no_data.rows) == 1  # WHY: one no-data date.
    assert not any("SECRET123" in value for row in links.rows for value in row.values())  # WHY: no signature leaks.


def test_300_a_window_outside_the_retention_rule_is_refused_before_any_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """A window that starts more than seven days back is refused, and no bulk request is sent."""
    today = datetime.now(UTC).date()  # WHY: the window is relative to today.
    _script(monkeypatch, {"juniper_bulk_start": (today - timedelta(days=10)).isoformat()})  # WHY: too old.
    gateway = FakeGateway()  # WHY: any call would be recorded.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert AssetBulkWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: refused.
    assert gateway.calls == [] and exporter.writes == []  # WHY: no call and no export.


def test_300_an_entitlement_rejection_writes_nothing_and_names_the_401_cause(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """HTTP 401 from the asset gateway is named as an entitlement problem, and no export is written."""
    caplog.set_level(logging.ERROR)  # WHY: the rejection is an error line.
    today = datetime.now(UTC).date()  # WHY: the window is relative to today.
    _script(
        monkeypatch,
        {
            "juniper_bulk_start": (today - timedelta(days=7)).isoformat(),
            "juniper_bulk_end": (today - timedelta(days=1)).isoformat(),
        },
    )  # WHY: a valid window, so the rejection comes from Juniper.
    gateway = FakeGateway(bodies={"queryAssetsBulkData": [{}]}, statuses={"queryAssetsBulkData": [401]})  # WHY.
    sink, exporter = _sink()  # WHY: nothing should be written.
    assert AssetBulkWorkflow(build_session(gateway, make_settings()), sink).execute() is False  # WHY: stopped.
    assert exporter.writes == [] and "HTTP 401" in caplog.text  # WHY: no export, and the status is named.


def test_303_lookup_saves_each_rma_item_as_well_as_printing_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """Menu 303 writes the request row and, when an RMA is asked for, one row for each RMA item."""
    monkeypatch.setattr(LookupWorkflow, "_ask_kind", lambda self: "1")  # WHY: a request-number lookup.
    monkeypatch.setattr(LookupWorkflow, "_ask_value", lambda self, kind: replies.SR_NUMBER)  # WHY: the request.
    monkeypatch.setattr(LookupWorkflow, "_ask_rma", lambda self: replies.RMA_NUMBER)  # WHY: one RMA to show.
    gateway = FakeGateway(bodies={"querysrdetails": [replies.detail_reply()], "queryrmadetails": [replies.rma_reply()]})
    sink_exporter = CapturingExporter()  # WHY: the lookup takes the exporter directly.
    LookupWorkflow(build_session(gateway, make_settings()), sink_exporter).execute()  # WHY: the lookup run.
    names = [write.filename for write in sink_exporter.writes]  # WHY: the files written.
    assert names == ["JuniperLookup.csv", "JuniperLookupRmaItems.csv"]  # WHY: the request and the items.
    items = sink_exporter.writes[1]  # WHY: the item export.
    assert len(items.rows) == 2 and items.fieldnames == ExportRowBuilder.RMA_ITEM_FIELDS  # WHY: every item, all fields.
    assert _every_value_is_ascii(items.rows)  # WHY: the items are ASCII only.


def test_the_run_log_masks_personal_values_while_the_export_keeps_them(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The printed run log masks each personal value. The export keeps the same note content in full."""
    caplog.set_level(logging.INFO)  # WHY: the printed rows are info lines.
    _script(monkeypatch, {"juniper_key_kind": "1", "juniper_key_value": replies.SR_NUMBER})  # WHY: every note.
    gateway = FakeGateway(
        bodies={
            "querysrdetails": [replies.detail_reply()],
            "querysrnotedetails": [
                replies.note_reply(replies.NOTE_ID_ONE),
                replies.note_reply(replies.NOTE_ID_TWO),
                replies.note_reply(replies.NOTE_ID_THREE),
            ],
        }
    )  # WHY: the three distinct notes of the request.
    sink, exporter = _sink()  # WHY: capture the export and the printed rows.
    assert RequestNotesWorkflow(build_session(gateway, make_settings()), sink).execute() is True  # WHY: the run.
    first_note = exporter.writes[0].rows[0]  # WHY: the first note row, which holds an address.
    assert first_note["content"].endswith("pat.example@example.com")  # WHY: the export keeps the address.
    assert "pat.example@example.com" not in caplog.text  # WHY: the run log never shows the raw address.
    assert "p***@example.com" in caplog.text  # WHY: the run log shows the masked address.
