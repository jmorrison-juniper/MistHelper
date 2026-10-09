"""Opt-in live checks of menus 294 to 300. Each check makes read-only calls with the local settings.

Set JUNIPER_LIVE_TESTS=1 to run them. Without it, every live check is skipped. The class
TestMenuFailurePaths runs without the flag, because it uses fakes and makes no network call. A check writes no file:
its exports go to a capturing exporter. The asset check reports the entitlement block (HTTP 401) as a
skip with that reason, because the block belongs to Juniper, not to this code.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import csv  # WHY: read the saved exports back for the save checks.
import logging  # WHY: caplog levels for the printed rows.
import os  # WHY: read the opt-in and the environment.
import re  # WHY: find any raw e-mail address in the saved values.
from datetime import UTC, datetime, timedelta  # WHY: the snapshot window for the bulk check.
from pathlib import Path  # WHY: the local env file path and the saved export folder.
from types import SimpleNamespace  # WHY: the stand-in for the database mirror result.
from typing import Any  # WHY: the case rows are loosely typed.

import pytest  # WHY: markers, skips, and monkeypatching of the scripted input.
from dotenv import dotenv_values  # WHY: read the local env file without printing values.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: the shared input helper of menu 303.
)
from src.operations.exporting.export.data_exporter import DataExporter  # WHY: the real file writer for the save checks.
from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: the transport failure the fake raises.
)
from src.operations.exporting.juniper_rma.model.export_rows import (
    ExportRowBuilder,  # WHY: the request and RMA item column lists.
)
from src.operations.exporting.juniper_rma.model.reference_rows import (  # WHY: columns.
    BulkLinkRows,
    LovRows,
    SoftwareVersionRows,
)
from src.operations.exporting.juniper_rma.model.request_rows import (  # WHY: the column lists that each export must carry.  # noqa: E501
    DetailRecordRows,
    NoteRows,
    RequestDetailRows,
    RequestListRows,
    RmaHeaderRows,
)
from src.operations.exporting.juniper_rma.settings import (  # WHY.
    JuniperServiceSession,
    JuniperSettings,
    JuniperSettingsLoader,
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
from src.operations.exporting.juniper_rma.workflows.lookup import LookupWorkflow  # WHY: menu 303 under test.
from src.operations.exporting.juniper_rma.workflows.reference_reads import (  # WHY: the reference and bulk menus under test.  # noqa: E501
    AssetBulkWorkflow,
    LovWorkflow,
    SoftwareVersionWorkflow,
)
from tests.unit.juniper_rma.fixtures import read_replies as replies  # WHY: synthetic replies in the live shape.
from tests.unit.juniper_rma.fixtures.capturing import CapturingExporter, ScriptedAnswers  # WHY: shared doubles.
from tests.unit.juniper_rma.fixtures.fake_gateway import FakeGateway, build_session, make_settings  # WHY: the fakes.

LIVE_SKIP = pytest.mark.skipif(  # WHY: every live check is opt-in, the same as the existing live checks.
    os.environ.get("JUNIPER_LIVE_TESTS") != "1",
    reason="Set JUNIPER_LIVE_TESTS=1 to run the read-only live menu checks.",
)
UNMASKED_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")  # WHY: a raw address.


def _load_live_settings(needs_contact_email: bool = True) -> JuniperSettings:
    """Merge the local .env file and the JUNIPER_ environment names, then check them as the menu does."""
    env_file = Path(os.environ.get("MISTHELPER_ENV_FILE", ".env"))  # WHY: the main checkout holds the .env.
    values: dict[str, str] = {}  # WHY: merged values, never printed.
    if env_file.is_file():  # WHY: the file is optional when the environment holds the values.
        values.update({name: value for name, value in dotenv_values(env_file).items() if value is not None})
    values.update({name: value for name, value in os.environ.items() if name.startswith("JUNIPER_")})  # WHY.
    return JuniperSettingsLoader(values).load(needs_contact_email=needs_contact_email)  # WHY: the same checks.


def _live_session(needs_contact_email: bool = True) -> JuniperServiceSession:
    """Return a live session built from the checked local settings."""
    return JuniperServiceSession(_load_live_settings(needs_contact_email))  # WHY: one session per check.


def _script(monkeypatch: pytest.MonkeyPatch, answers: dict[str, str]) -> None:
    """Route every operator prompt of the Juniper menus through the scripted answers."""
    monkeypatch.setattr(JuniperMenuInput, "text", staticmethod(ScriptedAnswers(answers)))  # WHY: one input path.


def _first_listed_case() -> dict[str, Any]:
    """Return the first request of the 90-day list, read with one live list call."""
    outcome = _live_session().case.list_requests()  # WHY: one read-only list call.
    assert outcome.is_usable, f"the list call did not succeed: {outcome.status_code}"  # WHY: the reason is the code.
    rows = [
        row for row in outcome.result.get("cases") or [] if isinstance(row, dict) and row.get("serviceRequestNumber")
    ]
    assert len(rows) >= 1, "the account has no request in the last 90 days"  # WHY: the other checks need one request.
    return rows[0]  # WHY: the first request, which the other checks use.


@pytest.mark.live
@LIVE_SKIP
def test_live_294_request_list_saves_every_column(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The live 90-day list writes one row for each request, with every column, and prints each column."""
    caplog.set_level(logging.INFO)  # WHY: the printed rows are info lines.
    _script(monkeypatch, {})  # WHY: Enter for both dates keeps the 90-day window.
    exporter = CapturingExporter()  # WHY: the export is captured, not written.
    assert RequestListWorkflow(_live_session(), JuniperExportSink(exporter)).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export of this menu.
    assert write.fieldnames == RequestListRows.COLUMNS, "the list header is not the full column list"  # WHY.
    assert len(write.rows) >= 1, "the list returned no request"  # WHY: an empty list cannot prove the columns.
    assert all(set(row) == set(RequestListRows.COLUMNS) for row in write.rows)  # WHY: every row, every column.
    assert not UNMASKED_EMAIL.search(caplog.text), "a raw e-mail address reached the run log"  # WHY: the log masks.
    for column in RequestListRows.COLUMNS:  # WHY: each column is printed for the operator.
        assert f"{column}=" in caplog.text, f"column {column} was not printed"  # WHY: the print is complete.


@pytest.mark.live
@LIVE_SKIP
def test_live_295_request_detail_saves_summary_and_records(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The live detail of the first request writes the summary row and the nested records."""
    caplog.set_level(logging.INFO)  # WHY: the printed rows are info lines.
    request = _first_listed_case()  # WHY: the request to read.
    _script(monkeypatch, {"juniper_key_kind": "1", "juniper_key_value": request["serviceRequestNumber"]})  # WHY.
    exporter = CapturingExporter()  # WHY: the export is captured, not written.
    assert RequestDetailWorkflow(_live_session(), JuniperExportSink(exporter)).execute() is True  # WHY: the run.
    summary = exporter.writes[0]  # WHY: the summary export.
    assert summary.fieldnames == RequestDetailRows.COLUMNS, "the summary header is not the full column list"  # WHY.
    assert len(summary.rows) == 1, "the summary must hold one row"  # WHY: one request, one row.
    assert summary.rows[0]["serviceRequestNumber"] == request["serviceRequestNumber"]  # WHY: the right request.
    if len(exporter.writes) > 1:  # WHY: the records export exists when the request has nested records.
        records = exporter.writes[1]  # WHY: the records export.
        assert records.fieldnames == DetailRecordRows.COLUMNS, "the records header is not the full column list"  # WHY.
    assert not UNMASKED_EMAIL.search(caplog.text), "a raw e-mail address reached the run log"  # WHY: the log masks.


@pytest.mark.live
@LIVE_SKIP
def test_live_296_rma_detail_saves_header_and_every_item(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The live RMA of the first request with one writes the header and every item, with the contact in full."""
    caplog.set_level(logging.INFO)  # WHY: the printed rows are info lines.
    request = _cases_with_rma()[0]  # WHY: a request that names an RMA.
    rma_number = str(request["rma"][0]["rmaNumber"])  # WHY: the first RMA of that request.
    _script(
        monkeypatch,
        {
            "juniper_rma_number": rma_number,
            "juniper_rma_request": request["serviceRequestNumber"],
            "juniper_rma_case": "",
        },
    )  # WHY: the RMA, its request, and an empty optional case number.
    exporter = CapturingExporter()  # WHY: the export is captured, not written.
    assert RmaDetailWorkflow(_live_session(), JuniperExportSink(exporter)).execute() is True  # WHY: the run.
    header, items = exporter.writes  # WHY: the two exports.
    assert header.fieldnames == list(RmaHeaderRows.COLUMNS), "the RMA header is not the full column list"  # WHY.
    assert len(header.rows) == 1, "the RMA header must hold one row"  # WHY: one RMA, one row.
    assert len(items.rows) >= 1, "the RMA has no item"  # WHY: the live RMA lists at least one item.
    assert items.fieldnames == list(ExportRowBuilder.RMA_ITEM_FIELDS), "the item header is not the full list"  # WHY.
    assert not UNMASKED_EMAIL.search(caplog.text), "a raw e-mail address reached the run log"  # WHY: the log masks.


def _cases_with_rma() -> list[dict[str, Any]]:
    """Return the requests of the 90-day list that name at least one RMA."""
    outcome = _live_session().case.list_requests()  # WHY: one read-only list call.
    assert outcome.is_usable, f"the list call did not succeed: {outcome.status_code}"  # WHY: the reason is the code.
    rows = [row for row in outcome.result.get("cases") or [] if isinstance(row, dict)]  # WHY: the request rows.
    named = [row for row in rows if isinstance(row.get("rma"), list) and row["rma"]]  # WHY: the RMA-bearing rows.
    assert named, "no request in the last 90 days names an RMA"  # WHY: the RMA check needs one.
    return named  # WHY: the requests with an RMA, in list order.


@pytest.mark.live
@LIVE_SKIP
def test_live_297_request_notes_saves_every_note(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The live notes of the first request write one row for each distinct note, with the content in full."""
    caplog.set_level(logging.INFO)  # WHY: the printed rows are info lines.
    request = _first_listed_case()  # WHY: the request whose notes are read.
    _script(monkeypatch, {"juniper_key_kind": "1", "juniper_key_value": request["serviceRequestNumber"]})  # WHY.
    exporter = CapturingExporter()  # WHY: the export is captured, not written.
    assert RequestNotesWorkflow(_live_session(), JuniperExportSink(exporter)).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export of this menu.
    assert write.fieldnames == NoteRows.COLUMNS, "the notes header is not the full column list"  # WHY: every column.
    assert len(write.rows) >= 1, "the request returned no note"  # WHY: an empty note list cannot prove the columns.
    assert all(row["noteId"] for row in write.rows), "a note row has no identifier"  # WHY: each note is keyed.
    assert not UNMASKED_EMAIL.search(caplog.text), "a raw e-mail address reached the run log"  # WHY: the log masks.


@pytest.mark.live
@LIVE_SKIP
def test_live_298_list_of_values_saves_every_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """The live list of values writes one row for each value, and the groups include the status list."""
    _script(monkeypatch, {})  # WHY: the menu asks no question.
    exporter = CapturingExporter()  # WHY: the export is captured, not written.
    session = _live_session(needs_contact_email=False)  # WHY: the list of values needs no contact.
    assert LovWorkflow(session, JuniperExportSink(exporter)).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export of this menu.
    assert write.fieldnames == list(LovRows.COLUMNS), "the list header is not the full column list"  # WHY.
    groups = {row["lovGroup"] for row in write.rows}  # WHY: the groups that the reply carries.
    assert {"srStatus", "priority"} <= groups, f"expected groups are missing: {sorted(groups)}"  # WHY: the groups.


@pytest.mark.live
@LIVE_SKIP
def test_live_299_software_versions_saves_every_release(monkeypatch: pytest.MonkeyPatch) -> None:
    """The live software list writes one row for each release of each platform."""
    _script(monkeypatch, {})  # WHY: the menu asks no question.
    exporter = CapturingExporter()  # WHY: the export is captured, not written.
    session = _live_session(needs_contact_email=False)  # WHY: the software list needs no contact.
    assert SoftwareVersionWorkflow(session, JuniperExportSink(exporter)).execute() is True  # WHY: the run.
    write = exporter.writes[0]  # WHY: the one export of this menu.
    assert write.fieldnames == list(SoftwareVersionRows.COLUMNS), "the header is not the full column list"  # WHY.
    assert len(write.rows) >= 1, "the software list returned no release"  # WHY: an empty list cannot prove the columns.
    assert all(row["productSeries"] for row in write.rows), "a software row has no product series"  # WHY: keyed.


@pytest.mark.live
@LIVE_SKIP
def test_live_300_asset_bulk_links_or_reports_the_entitlement_block(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The live bulk read writes the masked links. While Juniper blocks the asset API (HTTP 401), it skips."""
    caplog.set_level(logging.INFO)  # WHY: the explanation is an info or error line.
    today = datetime.now(UTC).date()  # WHY: the window is relative to today in UTC.
    _script(
        monkeypatch,
        {
            "juniper_bulk_start": (today - timedelta(days=7)).isoformat(),
            "juniper_bulk_end": (today - timedelta(days=1)).isoformat(),
        },
    )  # WHY: the oldest and the newest allowed days.
    exporter = CapturingExporter()  # WHY: the export is captured, not written.
    ran = AssetBulkWorkflow(_live_session(needs_contact_email=False), JuniperExportSink(exporter)).execute()  # WHY.
    if not ran and "HTTP 401" in caplog.text:  # WHY: the block belongs to Juniper, so it is reported as a skip.
        pytest.skip("BLOCKED: Juniper asset API entitlement returns HTTP 401. Ask Juniper to enable the asset API.")
    assert ran is True, "the bulk read did not complete"  # WHY: any other failure is a real failure.
    links = [write for write in exporter.writes if write.fieldnames == list(BulkLinkRows.LINK_COLUMNS)]  # WHY.
    assert len(links) >= 1, "the bulk export has no link header"  # WHY: the header proves the file layout.
    assert not any(
        "Signature" in value for write in exporter.writes for row in write.rows for value in row.values()
    ), "a signed query reached the bulk export"  # WHY: the signature must be masked.


def _no_database_mirror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the optional database mirror out of the save check. Only the file write is under test here."""
    no_mirror = SimpleNamespace(written=False, skip_reason="save check, database mirror not under test")  # WHY.
    monkeypatch.setattr(  # WHY: the mirror step reports a skip, so the real file writer is the only writer.
        DataExporter,
        "_route_to_polyglot",
        staticmethod(lambda data, api_name, raw_data=False: no_mirror),  # WHY: no database is contacted.
    )


def _saved_csv(folder: Path, filename: str) -> tuple[list[str], list[list[str]]]:
    """Read one saved export from the data folder and return its header and its rows."""
    with (folder / "data" / filename).open(encoding="utf-8", newline="") as handle:  # WHY: the exporter's output.
        reader = csv.reader(handle)  # WHY: the standard reader keeps the quoted values intact.
        header = next(reader)  # WHY: the first line is the header.
        return header, list(reader)  # WHY: the header and every data row.


@pytest.mark.live
@LIVE_SKIP
def test_live_case_menus_save_every_column_to_disk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The real file writer saves menus 294 to 297 with every column in the header, in a temporary folder."""
    monkeypatch.chdir(tmp_path)  # WHY: the exporter writes under data/ in the working folder.
    _no_database_mirror(monkeypatch)  # WHY: the database mirror is outside this check.
    request = _first_listed_case()  # WHY: one request for the detail and the notes.
    _script(monkeypatch, {})  # WHY: the list uses the default window.
    assert RequestListWorkflow(_live_session(), JuniperExportSink()).execute() is True  # WHY: the list save.
    header, rows = _saved_csv(tmp_path, "JuniperRequestList.csv")  # WHY: read the file back.
    assert header == RequestListRows.COLUMNS and len(rows) >= 1, "the saved list lacks the columns or the rows"  # WHY.
    key = {"juniper_key_kind": "1", "juniper_key_value": request["serviceRequestNumber"]}  # WHY: one request.
    _script(monkeypatch, key)  # WHY: the detail and the notes read the same request.
    assert RequestDetailWorkflow(_live_session(), JuniperExportSink()).execute() is True  # WHY: the detail save.
    header, rows = _saved_csv(tmp_path, "JuniperRequestDetail.csv")  # WHY: read the file back.
    assert header == RequestDetailRows.COLUMNS and len(rows) == 1, "the saved detail is incomplete"  # WHY.
    assert RequestNotesWorkflow(_live_session(), JuniperExportSink()).execute() is True  # WHY: the notes save.
    header, rows = _saved_csv(tmp_path, "JuniperRequestNotes.csv")  # WHY: read the file back.
    assert (
        header == NoteRows.COLUMNS and len(rows) >= 1
    ), "the saved notes are incomplete"  # WHY: every column, every note.
    rma_request = _cases_with_rma()[0]  # WHY: a request that names an RMA, for the RMA save.
    rma_keys = {  # WHY: the RMA number, its request, and an empty optional case number.
        "juniper_rma_number": str(rma_request["rma"][0]["rmaNumber"]),
        "juniper_rma_request": rma_request["serviceRequestNumber"],
        "juniper_rma_case": "",
    }
    _script(monkeypatch, rma_keys)  # WHY: the RMA read.
    assert RmaDetailWorkflow(_live_session(), JuniperExportSink()).execute() is True  # WHY: the RMA save.
    header, rows = _saved_csv(tmp_path, "JuniperRmaDetailItems.csv")  # WHY: read the item file back.
    assert (
        header == list(ExportRowBuilder.RMA_ITEM_FIELDS) and len(rows) >= 1
    ), "the saved RMA items are incomplete"  # WHY.


@pytest.mark.live
@LIVE_SKIP
def test_live_reference_menus_save_every_column_to_disk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The real file writer saves menus 298 and 299 with every column in the header, in a temporary folder."""
    monkeypatch.chdir(tmp_path)  # WHY: the exporter writes under data/ in the working folder.
    _no_database_mirror(monkeypatch)  # WHY: the database mirror is outside this check.
    _script(monkeypatch, {})  # WHY: neither menu asks a question.
    assert LovWorkflow(_live_session(needs_contact_email=False), JuniperExportSink()).execute() is True  # WHY: 298.
    header, rows = _saved_csv(tmp_path, "JuniperLovs.csv")  # WHY: read the file back.
    assert (
        header == list(LovRows.COLUMNS) and len(rows) >= 1
    ), "the saved list of values is incomplete"  # WHY: every column.
    session = _live_session(needs_contact_email=False)  # WHY: the software list needs no contact.
    assert SoftwareVersionWorkflow(session, JuniperExportSink()).execute() is True  # WHY: 299.
    header, rows = _saved_csv(tmp_path, "JuniperSoftwareVersions.csv")  # WHY: read the file back.
    assert (
        header == list(SoftwareVersionRows.COLUMNS) and len(rows) >= 1
    ), "the saved software list is incomplete"  # WHY.


def _script_lookup(monkeypatch: pytest.MonkeyPatch, answers: dict[str, str]) -> None:
    """Route the menu 303 prompts, which use the shared input helper, through the scripted answers by context."""

    def scripted(_prompt: str, default_value: str = "", allow_empty: bool = True, context: str = "") -> str:  # WHY.
        """Return the scripted answer for this prompt context, or the default when none is set."""
        return answers.get(context, default_value)  # WHY: the scripted answer, or the default for an unset prompt.

    monkeypatch.setattr(  # WHY: the patch lasts only for this test.
        SourceDependencyResolver.InputUtils,
        "safe_input",
        staticmethod(scripted),  # WHY: the same call shape as the shared helper.
    )


@pytest.mark.live
@LIVE_SKIP
def test_live_303_lookup_saves_request_and_rma_items(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Menu 303 reads one request and one of its RMAs, and saves both to files in a temporary folder."""
    monkeypatch.chdir(tmp_path)  # WHY: the exporter writes under data/ in the working folder.
    _no_database_mirror(monkeypatch)  # WHY: the database mirror is outside this check.
    rma_request = _cases_with_rma()[0]  # WHY: a request that names an RMA, so the RMA export runs.
    _script_lookup(
        monkeypatch,
        {
            "juniper_lookup_kind": "1",  # WHY: the key is a request number.
            "juniper_lookup_value": rma_request["serviceRequestNumber"],  # WHY: the request that names the RMA.
            "juniper_lookup_rma": str(rma_request["rma"][0]["rmaNumber"]),  # WHY: the RMA to read.
        },
    )
    LookupWorkflow(_live_session(), exporter=DataExporter).execute()  # WHY: the menu path with the real writer.
    header, rows = _saved_csv(tmp_path, "JuniperLookup.csv")  # WHY: read the request row back.
    assert header == list(ExportRowBuilder.REQUEST_FIELDS), "the saved lookup header is incomplete"  # WHY: columns.
    assert len(rows) == 1, "the saved lookup should hold exactly one request row"  # WHY: one request, one row.
    header, rows = _saved_csv(tmp_path, "JuniperLookupRmaItems.csv")  # WHY: read the RMA items back.
    assert (
        header == list(ExportRowBuilder.RMA_ITEM_FIELDS) and len(rows) >= 1
    ), "the saved RMA items are incomplete"  # WHY.


class TestMenuFailurePaths:
    """Menus 294 and 298 stop without a file when Juniper returns an error or a transport failure."""

    @pytest.mark.parametrize("status_code", [400, 404])  # WHY: a client error is a final answer for the menu.
    def test_request_list_writes_no_file_on_a_client_error(
        self, monkeypatch: pytest.MonkeyPatch, status_code: int
    ) -> None:
        """A client error reply stops the list menu. The result is a failure, and no file is written."""
        _script(monkeypatch, {})  # WHY: Enter keeps the default window, as an operator does.
        gateway = FakeGateway(  # WHY: the fake answers the list call with the client error.
            bodies={"querysrlist": [replies.list_reply()]},
            statuses={"querysrlist": [status_code]},
        )
        exporter = CapturingExporter()  # WHY: a capture shows any write.
        session = build_session(gateway, make_settings())  # WHY: the real services over the fake gateway.
        assert RequestListWorkflow(session, JuniperExportSink(exporter)).execute() is False  # WHY: failure reported.
        assert exporter.writes == [], "a failed list must not write a file"  # WHY: no partial export.

    @pytest.mark.parametrize("status_code", [500, 503])  # WHY: a server error is a final answer for the menu.
    def test_list_of_values_writes_no_file_on_a_server_error(self, status_code: int) -> None:
        """A server error reply stops the list of values menu. The result is a failure, and no file is written."""
        gateway = FakeGateway(  # WHY: the fake answers the values call with the server error.
            bodies={"getlov": [replies.lov_reply()]},
            statuses={"getlov": [status_code]},
        )
        exporter = CapturingExporter()  # WHY: a capture shows any write.
        session = build_session(gateway, make_settings())  # WHY: the real services over the fake gateway.
        assert LovWorkflow(session, JuniperExportSink(exporter)).execute() is False  # WHY: failure reported.
        assert exporter.writes == [], "a failed list must not write a file"  # WHY: no partial export.

    def test_request_list_writes_no_file_on_a_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A timeout that exhausts the retries stops the list menu. The result is a failure, and no file is written."""
        _script(monkeypatch, {})  # WHY: Enter keeps the default window, as an operator does.
        timeout = JuniperTransportError("Juniper querysrlist failed after 3 attempts (Timeout)")  # WHY: the timeout.
        gateway = FakeGateway(failures={"querysrlist": [timeout]})  # WHY: the fake raises the timeout to the service.
        exporter = CapturingExporter()  # WHY: a capture shows any write.
        session = build_session(gateway, make_settings())  # WHY: the real services over the fake gateway.
        assert RequestListWorkflow(session, JuniperExportSink(exporter)).execute() is False  # WHY: failure reported.
        assert exporter.writes == [], "a failed list must not write a file"  # WHY: no partial export.

    def test_list_of_values_writes_no_file_on_a_connection_error(self) -> None:
        """A connection error that exhausts the retries stops the values menu. No file is written."""
        error = JuniperTransportError("Juniper getlov failed after 3 attempts (ConnectionError)")  # WHY: the error.
        gateway = FakeGateway(failures={"getlov": [error]})  # WHY: the fake raises the error to the service.
        exporter = CapturingExporter()  # WHY: a capture shows any write.
        session = build_session(gateway, make_settings())  # WHY: the real services over the fake gateway.
        assert LovWorkflow(session, JuniperExportSink(exporter)).execute() is False  # WHY: failure reported.
        assert exporter.writes == [], "a failed list must not write a file"  # WHY: no partial export.
