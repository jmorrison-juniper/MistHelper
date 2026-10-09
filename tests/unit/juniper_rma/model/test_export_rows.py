"""Tests for the export rows, the log masks, the retention purge, and the run record."""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable.

import os  # WHY: file ages for the purge test.
import time  # WHY: the clock for the purge test.

from src.operations.exporting.juniper_rma.model.export_rows import (  # WHY: the builders and the masking helpers.
    ExportRowBuilder,
    PersonalDataMasker,
    PersonalDataRetention,
)
from src.operations.exporting.juniper_rma.model.run_record import RunRecord  # WHY: the run record under test.
from src.operations.exporting.juniper_rma.model.service_request import (  # WHY: the records under test.
    RmaItem,
    RmaRecord,
)

PERSONAL_EMAIL = "jane.tester@example.com"  # WHY: a fake personal value that the export keeps in full.
PERSONAL_PHONE = "5555550199"  # WHY: a fake personal value that the export keeps in full.
PERSONAL_STREET = "1 Test Way"  # WHY: a fake personal value that the export keeps in full.


def test_masker_keeps_only_the_permitted_parts() -> None:
    """Names keep an initial, e-mail keeps the first letter and the domain, phones keep two digits."""
    assert PersonalDataMasker.name("Jane Tester") == "J*** T***"  # WHY: first letters only.
    assert PersonalDataMasker.email(PERSONAL_EMAIL) == "j***@example.com"  # WHY: domain kept.
    assert PersonalDataMasker.phone(PERSONAL_PHONE) == "********99"  # WHY: eight digits hidden, last two kept.
    assert PersonalDataMasker.street(PERSONAL_STREET) == "[masked]"  # WHY: a street is never shown.
    assert PersonalDataMasker.street("") == ""  # WHY: an empty street stays empty.


def test_log_form_masks_only_the_personal_columns() -> None:
    """The log copy masks each personal column with the same format. Business and non-text values stay."""
    assert PersonalDataMasker.for_log("contactName", "Jane Tester") == "J*** T***"  # WHY: a personal name.
    assert PersonalDataMasker.for_log("contactEmail", PERSONAL_EMAIL) == "j***@example.com"  # WHY: a personal e-mail.
    assert PersonalDataMasker.for_log("telephoneNumber", PERSONAL_PHONE) == "********99"  # WHY: a personal phone.
    assert PersonalDataMasker.for_log("address1", PERSONAL_STREET) == "[masked]"  # WHY: a street line.
    assert PersonalDataMasker.for_log("content", f"copy {PERSONAL_EMAIL}") == "copy j***@example.com"  # WHY: text.
    assert PersonalDataMasker.for_log("companyName", "Test Co") == "Test Co"  # WHY: a business name stays.
    assert PersonalDataMasker.for_log("contactName", None) is None  # WHY: a non-text value passes through.


def test_item_row_keeps_the_personal_values_in_full() -> None:
    """The export row of an RMA item keeps the personal fields in full, and business values stay the same."""
    rma = RmaRecord.from_result(  # WHY: a record with personal fields.
        {
            "rmaNumber": "RMA-1",
            "rmaContact": {
                "companyName": "Test Co",
                "contactName": "Jane Tester",
                "contactEmail": PERSONAL_EMAIL,
                "telephoneNumber": PERSONAL_PHONE,
                "address": {"address1": PERSONAL_STREET, "city": "Testville"},
            },
        },
        "REQ-1",
    )
    item = RmaItem.parse_all(  # WHY: one defective item with a receiver.
        "RMA-1", {"defectiveItems": [{"itemNumber": "D-1", "receivedBy": "Sam Receiver"}]}
    )[0]
    row = ExportRowBuilder.item_row(rma, item, "2026-10-08T12:00:00")  # WHY: the row under test.
    assert row["contactName"] == "Jane Tester"  # WHY: the contact name is kept in full.
    assert row["contactEmail"] == PERSONAL_EMAIL  # WHY: the contact e-mail is kept in full.
    assert row["telephoneNumber"] == PERSONAL_PHONE  # WHY: the telephone is kept in full.
    assert row["address1"] == PERSONAL_STREET  # WHY: the street line is kept in full.
    assert row["receivedBy"] == "Sam Receiver"  # WHY: the receiver name is kept in full.
    assert row["companyName"] == "Test Co"  # WHY: business names stay the same.


def test_retention_removes_only_expired_export_files(tmp_path) -> None:
    """A file older than the window is removed, a fresh file stays, and the count is returned."""
    old_file = tmp_path / "JuniperRmaItems.csv"  # WHY: an export older than the window.
    new_file = tmp_path / "JuniperCorrelation.csv"  # WHY: an export inside the window.
    old_file.write_text("a", encoding="utf-8")  # WHY: create the old file.
    new_file.write_text("b", encoding="utf-8")  # WHY: create the new file.
    long_ago = time.time() - 400 * 86400  # WHY: 400 days ago.
    os.utime(old_file, (long_ago, long_ago))  # WHY: age the old file.
    removed = PersonalDataRetention(180, str(tmp_path)).purge()  # WHY: purge with the 180-day window.
    assert removed == 1  # WHY: exactly one file is expired.
    assert not old_file.exists()  # WHY: the expired file is gone.
    assert new_file.exists()  # WHY: the fresh file stays.


def test_run_record_counts_outcomes_and_finishes_incomplete_with_a_reason() -> None:
    """Counts follow the outcomes, and a note makes the final status incomplete."""
    record = RunRecord("juniper_rma_correlation")  # WHY: a new run.
    record.record_outcome("matched")  # WHY: one matched ticket.
    record.record_outcome("ambiguous")  # WHY: one ambiguous ticket.
    record.record_outcome("unknown")  # WHY: an unknown status is ignored.
    record.add_requests(3)  # WHY: three Juniper calls.
    record.note_problem("A request detail call failed")  # WHY: one reason for an incomplete run.
    record.finish()  # WHY: the final status.
    row = record.as_row()  # WHY: the export row.
    assert (row["matchedCount"], row["ambiguousCount"], row["requestCount"]) == (1, 1, 3)  # WHY: the counts.
    assert row["status"] == "incomplete"  # WHY: a note means the run was not whole.
    assert row["reason"] == "A request detail call failed"  # WHY: the reason is kept.
    assert set(row) == set(ExportRowBuilder.RUN_FIELDS)  # WHY: the row matches the CSV columns.


def test_ascii_text_replaces_non_ascii_characters() -> None:
    """Each non-ASCII character becomes one question mark, and plain ASCII text is unchanged."""
    assert PersonalDataMasker.ascii_text("Caf\u00e9 ok") == "Caf? ok"  # WHY: one accented letter, one mark.
    assert PersonalDataMasker.ascii_text("plain") == "plain"  # WHY: ASCII text passes through unchanged.


def test_ascii_rows_clean_text_only_and_keep_the_input_unchanged() -> None:
    """Text is made ASCII-only, numbers and empty values pass through, and the input rows stay unchanged."""
    rows = [{"name": "Jos\u00e9", "count": 3, "empty": None}]  # WHY: text, a number, and an empty value.
    cleaned = ExportRowBuilder.ascii_rows(rows)  # WHY: the cleaning under test.
    assert cleaned == [{"name": "Jos?", "count": 3, "empty": None}]  # WHY: only the text changed.
    assert rows[0]["name"] == "Jos\u00e9"  # WHY: the caller's row keeps its original text.
