"""Tests for the report hook of the portal finish step."""

from __future__ import annotations

import csv  # Read the compiled bytes the way a spreadsheet would.
import io  # Wrap the bytes for the CSV reader.
import logging  # Prove that no log line holds a file name.
from collections.abc import Mapping  # The reader double returns text by name.

import pytest  # Parametrize and check errors.

from src.operations.exporting.ex_hardware_inventory.report.csv_file import ReportTooLarge  # The size error.
from src.operations.exporting.ex_hardware_inventory.run.publisher import ReportHook  # Unit.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import Batches  # Identities.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies  # Invented replies.

ORG = Batches.ORG  # An invented organization.
OTHER = "22222222-2222-4222-8222-222222222222"  # A second invented organization.


def outcome(index: int, state: str = "completed", reason: str | None = None, files: list[str] | None = None) -> dict:
    """Build one manifest outcome for a switch."""
    names = files if files is not None else ([f"hardware/ex-{index:02d}.xml"] if state == "completed" else [])
    return {"target": Batches.identity(index, with_key=False), "state": state, "reason_code": reason, "files": names}


def reader(replies: Mapping[str, str]):
    """Build a reply reader over a mapping. A missing name raises OSError."""

    def read(name: str) -> str:
        """Return the text of one saved reply."""
        if name not in replies:
            raise FileNotFoundError(name)
        return replies[name]

    return read


def rows_of(data: bytes) -> list[dict[str, str]]:
    """Parse compiled bytes into dictionaries."""
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))


class TestCompile:
    """The hook builds one CSV from the outcomes and the saved replies."""

    def test_a_collected_switch_gives_a_row_for_each_hardware_item(self) -> None:
        """Each hardware item is one row, with the organization name from the scope."""
        replies = {"hardware/ex-01.xml": HardwareReplies.single_switch("SW1")}
        scope = {"mode": "organization", "organizations": {ORG: "Alpha Org"}}
        rows = rows_of(ReportHook(reader(replies), scope).compile([outcome(1)], 1_000_000))
        assert len(rows) > 3 and {row["record_type"] for row in rows} == {"hardware_item"}
        assert {row["org_name"] for row in rows} == {"Alpha Org"} and {row["scope"] for row in rows} == {"organization"}
        assert "SW1-CH" in {row["item_serial_number"] for row in rows}  # The chassis serial of the reply.

    def test_each_missing_reply_is_an_outcome_row_with_a_plain_detail(self) -> None:
        """A failed, a skipped, a stopped, and a completed switch with a missing file each give one row."""
        outcomes = [
            outcome(1, "failed", "completion_unproven"),
            outcome(2, "skipped", "offline"),
            outcome(3, "stopped", "cancelled"),
            outcome(4),  # Completed, but its file is not readable.
        ]
        rows = rows_of(ReportHook(reader({}), {"organizations": {ORG: "Alpha Org"}}).compile(outcomes, 1_000_000))
        by_name = {row["device_name"]: row for row in rows}
        assert [row["record_type"] for row in rows] == ["device_outcome"] * 4
        assert by_name["ex-01"]["collection_detail"] == "The shell did not show a stable prompt."
        assert by_name["ex-02"]["collection_status"] == "skipped"
        assert by_name["ex-03"]["collection_status"] == "cancelled"
        assert by_name["ex-04"]["collection_status"] == "failed"
        assert by_name["ex-04"]["collection_detail"] == "The reply file is missing."

    def test_an_unreadable_file_name_is_logged_without_the_name(self, caplog: pytest.LogCaptureFixture) -> None:
        """A file that cannot be read adds a warning that holds no file name."""
        caplog.set_level(logging.DEBUG)
        ReportHook(reader({}), None).compile([outcome(1)], 1_000_000)
        assert "A saved reply could not be read" in caplog.text  # The warning exists.
        assert "hardware/ex-01.xml" not in caplog.text

    @pytest.mark.parametrize(
        "error", [OSError("gone"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad"), ValueError("unsafe")]
    )
    def test_every_read_error_becomes_a_missing_reply(self, error: Exception) -> None:
        """OSError, a decode error, and ValueError from the reader all give the missing-reply row."""

        def read(name: str) -> str:
            """Raise the planned error."""
            raise error

        rows = rows_of(ReportHook(read, None).compile([outcome(1)], 1_000_000))
        assert [row["collection_detail"] for row in rows] == ["The reply file is missing."]

    def test_a_failed_save_is_not_called_an_invalid_reply(self) -> None:
        """The target code is format_failed for both causes, and the XML entry tells them apart."""
        saved = {"xml": {"state": "failed", "reason_code": "output_failed"}}  # The run folder refused the file.
        invalid = {"xml": {"state": "failed", "reason_code": "invalid_output"}}  # The reply did not decode.
        outcomes = [
            {**outcome(1, "failed", "format_failed"), "formats": saved},
            {**outcome(2, "failed", "format_failed"), "formats": invalid},
        ]
        rows = rows_of(ReportHook(reader({}), None).compile(outcomes, 1_000_000))
        details = {row["device_name"]: row["collection_detail"] for row in rows}
        assert details == {
            "ex-01": "The reply could not be saved.",
            "ex-02": "The reply was not a valid chassis inventory.",
        }

    def test_an_organization_that_could_not_be_read_is_one_outcome_row(self) -> None:
        """The scope lists a failed organization, and the report has one row for it."""
        scope = {
            "mode": "msp",
            "organizations": {ORG: "Alpha Org", OTHER: "Beta Org"},
            "failed": {OTHER: "discovery_failed"},
        }
        replies = {"hardware/ex-01.xml": HardwareReplies.minimal()}
        rows = rows_of(ReportHook(reader(replies), scope).compile([outcome(1)], 1_000_000))
        failed = [row for row in rows if row["org_name"] == "Beta Org"]
        assert len(failed) == 1 and failed[0]["org_id"] == OTHER and failed[0]["device_id"] == ""
        assert failed[0]["collection_detail"] == "Mist could not list the switches of this organization."
        assert {row["scope"] for row in rows} == {"msp"}

    @pytest.mark.parametrize("scope", [None, {}, {"organizations": "text"}, {"failed": ["x"]}, {"mode": None}])
    def test_a_missing_or_bad_scope_is_an_organization_run(self, scope: object) -> None:
        """A bad scope shape never fails the report. The organization name falls back to the identifier."""
        replies = {"hardware/ex-01.xml": HardwareReplies.minimal()}
        rows = rows_of(ReportHook(reader(replies), scope).compile([outcome(1)], 1_000_000))  # type: ignore[arg-type]
        assert {row["scope"] for row in rows} == {"organization"} and {row["org_name"] for row in rows} == {ORG}

    def test_a_bad_outcome_shape_is_a_failed_row_and_not_a_crash(self) -> None:
        """An outcome with no identity and no state still gives one failed row."""
        rows = rows_of(ReportHook(reader({}), None).compile([{}, {"target": "text", "files": "x"}], 1_000_000))
        assert [row["collection_status"] for row in rows] == ["failed", "failed"]

    def test_a_report_over_the_limit_raises_and_returns_nothing(self) -> None:
        """The size limit is the remaining quota of the run folder."""
        replies = {"hardware/ex-01.xml": HardwareReplies.single_switch("SW1")}
        with pytest.raises(ReportTooLarge):
            ReportHook(reader(replies), None).compile([outcome(1)], 100)

    def test_the_run_time_is_one_utc_value_on_every_row(self) -> None:
        """Every row carries the same run time in ISO 8601 form with a Z."""
        replies = {"hardware/ex-01.xml": HardwareReplies.single_switch("SW1")}
        rows = rows_of(ReportHook(reader(replies), None).compile([outcome(1)], 1_000_000))
        stamps = {row["report_run_utc"] for row in rows}
        assert len(stamps) == 1 and next(iter(stamps)).endswith("Z") and "T" in next(iter(stamps))

    def test_a_formula_cell_is_neutralized(self) -> None:
        """A reply that holds a formula in a text field gets the apostrophe guard."""
        xml = HardwareReplies.minimal(description="=HYPERLINK(1)")
        rows = rows_of(ReportHook(reader({"hardware/ex-01.xml": xml}), None).compile([outcome(1)], 1_000_000))
        assert rows[0]["item_description"] == "'=HYPERLINK(1)"
