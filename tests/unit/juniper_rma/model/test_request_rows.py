"""Offline tests for the Case row tables: every reply field has a column, and personal values stay in full."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

from collections import Counter  # WHY: count the record kinds of one detail.

import pytest  # WHY: parametrized checks over each nested record kind.

from src.operations.exporting.juniper_rma.model.export_rows import ExportRowBuilder  # WHY: the RMA item column list.
from src.operations.exporting.juniper_rma.model.request_rows import (  # WHY: the tables and row builders under test.
    ATTACHMENT_RECORD_SPECS,
    DETAIL_SPECS,
    ESCALATION_RECORD_SPECS,
    LIST_SPECS,
    NOTE_RECORD_SPECS,
    RECENT_NOTE_RECORD_SPECS,
    RMA_HEADER_SPECS,
    RMA_RECORD_SPECS,
    DetailRecordRows,
    NoteRows,
    RequestDetailRows,
    RequestListRows,
    RmaHeaderRows,
)
from tests.unit.juniper_rma.fixtures import read_replies as replies  # WHY: synthetic replies in the live shape.

RETRIEVED = "2026-09-07T10:00:00+00:00"  # WHY: one fixed retrieval time for every assertion.
ITEM_KEY_TO_COLUMN = {  # WHY: each item key of the live reply and the export column that holds it.
    "itemNumber": "itemNumber",
    "productID": "productID",
    "serialNumber": "serialNumber",
    "carrierDescription": "carrier",
    "dateTime": "dateTime",
    "defectiveItemStatus": "status",
    "receivedDate": "receivedDate",
    "trackingNumber": "trackingNumber",
    "defectiveItemNumber": "defectiveItemNumber",
    "deliveredDate": "deliveredDate",
    "receivedBy": "receivedBy",
    "replacementStatus": "status",
    "shipDate": "shipDate",
    "shipmentServiceLevel": "shipmentLevel",
}


def _scalar_paths(source: dict, prefix: str = "") -> set[str]:
    """Return the dotted path of each scalar value in an object. Lists are left to their own checks."""
    paths: set[str] = set()  # WHY: collect the paths in one set.
    for key, value in source.items():  # WHY: visit each key of the object.
        path = f"{prefix}{key}"  # WHY: the path of this key.
        if isinstance(value, dict):  # WHY: an object adds its keys under this path.
            paths |= _scalar_paths(value, f"{path}.")  # WHY: recurse into the object.
        elif not isinstance(value, list):  # WHY: a scalar is one field of the reply.
            paths.add(path)  # WHY: keep the path.
    return paths  # WHY: every scalar path of the object.


def _list_case() -> dict:
    """Return the one request row of the list reply."""
    return replies.list_reply()["querySRListResponse"]["cases"][0]  # WHY: the fixture row.


def test_list_table_has_a_column_for_every_scalar_field_of_the_list_row() -> None:
    """A list field with no column would be retrieved and then dropped. This test fails on that."""
    covered = {spec.path for spec in LIST_SPECS}  # WHY: the paths that the table reads.
    missing = _scalar_paths(_list_case()) - covered  # WHY: fields the table does not read.
    assert not missing, f"list fields without a column: {sorted(missing)}"  # WHY: name each missing field.


def test_detail_table_has_a_column_for_every_scalar_field_of_the_detail() -> None:
    """Every scalar field of the detail reply has a column in the summary row."""
    covered = {spec.path for spec in DETAIL_SPECS}  # WHY: the paths that the table reads.
    missing = _scalar_paths(replies.detail_reply()) - covered  # WHY: fields the table does not read.
    assert not missing, f"detail fields without a column: {sorted(missing)}"  # WHY: name each missing field.


@pytest.mark.parametrize(
    ("list_key", "specs"),
    [
        ("notes", NOTE_RECORD_SPECS),
        ("recentNotes", RECENT_NOTE_RECORD_SPECS),
        ("attachments", ATTACHMENT_RECORD_SPECS),
        ("escalate", ESCALATION_RECORD_SPECS),
        ("rma", RMA_RECORD_SPECS),
    ],
)
def test_each_nested_record_kind_has_a_column_for_every_field(list_key: str, specs: tuple) -> None:
    """Every field of each element of a nested detail list has a column in the records export."""
    elements = replies.detail_reply()[list_key]  # WHY: the nested objects of this kind.
    present: set[str] = set().union(*(_scalar_paths(item) for item in elements))  # WHY: their fields.
    missing = present - {spec.path for spec in specs}  # WHY: fields that no column reads.
    assert not missing, f"{list_key} fields without a column: {sorted(missing)}"  # WHY: name each one.


def test_rma_header_table_has_a_column_for_every_scalar_field_of_the_rma() -> None:
    """Every scalar field of the RMA reply, including the contact and address, has a header column."""
    covered = {spec.path for spec in RMA_HEADER_SPECS}  # WHY: the paths that the header reads.
    missing = _scalar_paths(replies.rma_reply()) - covered  # WHY: fields the header does not read.
    assert not missing, f"RMA fields without a column: {sorted(missing)}"  # WHY: name each missing field.


def test_rma_item_keys_all_map_to_item_columns() -> None:
    """Every key of a defective, replacement, or CE item maps to a column of the item export."""
    keys: set[str] = set()  # WHY: collect the item keys across the lists.
    for section in ("defectiveItems", "replacementItems", "ceItems"):  # WHY: each item list.
        for item in replies.rma_reply()[section]:  # WHY: each item of the list.
            keys |= set(item)  # WHY: the keys of this item.
    assert not keys - set(ITEM_KEY_TO_COLUMN), f"item keys without a mapping: {sorted(keys - set(ITEM_KEY_TO_COLUMN))}"
    columns = {ITEM_KEY_TO_COLUMN[key] for key in keys}  # WHY: the export column of each key.
    assert columns <= set(ExportRowBuilder.RMA_ITEM_FIELDS), "an item column is missing from the item export"


def test_list_row_keeps_personal_values_in_full_and_business_values() -> None:
    """Names, e-mail addresses, and free text stay in full. Account and product values stay the same."""
    row = RequestListRows.row(_list_case(), RETRIEVED)  # WHY: the row of the request.
    assert row["contactName"] == "Pat Example"  # WHY: the contact name is kept in full.
    assert row["contactEmail"] == "pat.example@example.com"  # WHY: the contact e-mail is kept in full.
    assert row["srOwnerEmailAddress"] == "owner.example@example.com"  # WHY: the owner e-mail is kept in full.
    assert row["ccEmail"] == "lee.example@example.com; ops.example@example.com"  # WHY: each CC address is kept.
    assert "pat.example@example.com" in row["problemDescription"]  # WHY: free text is kept in full.
    assert row["accountName"] == "Example Account Ltd"  # WHY: the account name is a business value.
    assert row["rmaNumbers"] == replies.RMA_NUMBER  # WHY: the RMA list is joined into one column.
    assert set(row) == set(RequestListRows.COLUMNS)  # WHY: the row has exactly the export columns.


def test_detail_row_keeps_contact_in_full_and_counts_each_nested_record() -> None:
    """The detail summary keeps the contact in full and counts the nested records that it lists."""
    row = RequestDetailRows.row(replies.detail_reply(), RETRIEVED)  # WHY: the one-row summary.
    assert row["contactName"] == "Pat Example"  # WHY: the contact name is kept in full.
    assert row["contactEmail"] == "pat.example@example.com"  # WHY: the contact e-mail is kept in full.
    assert row["preferredTelephoneNumber"] == "5550100123"  # WHY: the telephone is kept in full.
    assert row["srOwnerFullName"] == "Lee Example"  # WHY: the owner name is kept in full.
    assert "pat.example@example.com" in row["problemDescription"]  # WHY: free text is kept in full.
    counts = (row["noteCount"], row["recentNoteCount"], row["attachmentCount"], row["escalationCount"])  # WHY.
    assert counts == ("2", "2", "1", "1")  # WHY: the number of each nested list.
    assert (row["rmaCount"], row["rmaNumbers"], row["caseTypeCode"]) == ("1", replies.RMA_NUMBER, "TECH")  # WHY.
    assert set(row) == set(RequestDetailRows.COLUMNS)  # WHY: the row has exactly the export columns.


def test_detail_records_hold_one_row_per_nested_record_with_full_names() -> None:
    """Each note, attachment, escalation, RMA, and RMA item becomes one row with the full column set."""
    rows = DetailRecordRows.rows(replies.detail_reply(), RETRIEVED)  # WHY: every nested record.
    kinds = Counter(row["recordType"] for row in rows)  # WHY: count each kind.
    assert kinds == {"note": 2, "recentNote": 2, "attachment": 1, "escalation": 1, "rma": 1, "rmaItem": 1}  # WHY.
    assert all(set(row) == set(DetailRecordRows.COLUMNS) for row in rows)  # WHY: one key set for every row.
    attachment = next(row for row in rows if row["recordType"] == "attachment")  # WHY: the attachment row.
    assert attachment["uploadedBy"] == "Lee Example"  # WHY: the uploader name is kept in full.
    assert attachment["recordId"] == "1"  # WHY: the sequence number names the attachment.
    recent = next(row for row in rows if row["recordType"] == "recentNote")  # WHY: a recent note row.
    assert "pat.example@example.com" in recent["content"]  # WHY: the note content is kept in full.
    item = next(row for row in rows if row["recordType"] == "rmaItem")  # WHY: the RMA item row.
    assert (item["rmaNumber"], item["itemNumber"]) == (replies.RMA_NUMBER, "ITEM-1")  # WHY: the parent keys.


def test_note_row_keeps_the_reply_and_the_summary_and_the_content_in_full() -> None:
    """A note row holds the reply fields and the detail summary, and its content is kept in full."""
    summary = {"title": "Opened", "originator": "Pat Example", "dateTime": "2026-09-01T10:00:00.000Z"}  # WHY.
    reply = replies.note_reply(replies.NOTE_ID_ONE)  # WHY: the note reply for this identifier.
    row = NoteRows.row(replies.NOTE_ID_ONE, "recentNotes", summary, reply, RETRIEVED)  # WHY: the row of the note.
    assert set(row) == set(NoteRows.COLUMNS)  # WHY: every note column is present.
    assert row["content"] == f"Note body for {replies.NOTE_ID_ONE}, copy pat.example@example.com"  # WHY: the content.
    assert (row["noteId"], row["noteSource"], row["summaryOriginator"]) == (
        replies.NOTE_ID_ONE,
        "recentNotes",
        "Pat Example",
    )  # WHY: the identifier, the source list, and the summary name.


def test_rma_header_keeps_contact_in_full_and_counts_each_item_list() -> None:
    """The RMA header keeps the contact, the telephone, and the street in full, and counts each item list."""
    row = RmaHeaderRows.row(replies.rma_reply(), RETRIEVED)  # WHY: the RMA summary row.
    assert (row["contactName"], row["contactEmail"]) == ("Pat Example", "pat.example@example.com")  # WHY: contact.
    assert row["telephoneNumber"] == "5550100123"  # WHY: the telephone is kept in full.
    assert (row["address1"], row["address2"]) == ("1 Example Way", "")  # WHY: an empty line stays empty.
    assert row["state"] == "Example State"  # WHY: the state is a business location.
    assert (row["defectiveItemCount"], row["replacementItemCount"], row["ceItemCount"]) == ("1", "1", "0")  # WHY.
    assert set(row) == set(RmaHeaderRows.COLUMNS)  # WHY: the row has exactly the export columns.
