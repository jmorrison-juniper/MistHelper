"""Tests for the CSV renderer and the file check."""

from __future__ import annotations

import csv  # Read the rendered bytes the way a spreadsheet would.
import io  # Wrap the rendered text for the CSV reader.

import pytest  # Check the documented errors.

from src.operations.exporting.ex_hardware_inventory.report.csv_file import (
    CsvRenderer,
    CsvVerifier,
    ReportCheckError,
    ReportTooLarge,
)  # Units.

FIELDS = ["org_id", "device_name", "item_description"]  # A small column list for the tests.


def read_back(data: bytes) -> list[list[str]]:
    """Parse rendered bytes with the standard CSV reader."""
    return list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))  # Rows of cells.


class TestCsvRenderer:
    """The renderer writes UTF-8 text with one header row."""

    def test_header_then_rows_in_column_order(self) -> None:
        """The first line holds the column names, then one line for each row."""
        rows = [{"org_id": "o1", "device_name": "d1", "item_description": "x"}]  # One row.
        data = CsvRenderer.render(rows, FIELDS, 1_000_000)  # Render.
        assert read_back(data) == [FIELDS, ["o1", "d1", "x"]]  # Header and row.

    def test_line_end_is_crlf_and_text_is_utf8_without_a_byte_order_mark(self) -> None:
        """The file uses CRLF and no byte order mark."""
        data = CsvRenderer.render([{"org_id": "café"}], ["org_id"], 1_000_000)  # A non-ASCII value.
        assert data.startswith(b"org_id\r\n")  # Header with CRLF and no mark.
        assert "café".encode() in data  # UTF-8 text.

    def test_commas_quotes_and_line_breaks_round_trip(self) -> None:
        """Standard quoting keeps awkward values intact."""
        value = 'a,"b"\nc'  # A comma, a quote, and a line break.
        data = CsvRenderer.render([{"org_id": value}], ["org_id"], 1_000_000)  # Render.
        assert read_back(data)[1] == [value]  # The same value after a round trip.

    def test_missing_keys_become_empty_cells(self) -> None:
        """A row that lacks a column gets an empty cell."""
        data = CsvRenderer.render([{"org_id": "o1"}], FIELDS, 1_000_000)  # A short row.
        assert read_back(data)[1] == ["o1", "", ""]  # Empty cells fill the gap.

    def test_report_over_the_limit_raises(self) -> None:
        """A report that would pass the byte limit is refused and returns no bytes."""
        rows = [{"org_id": "x" * 100}] * 10  # About a thousand bytes.
        with pytest.raises(ReportTooLarge):  # The documented error.
            CsvRenderer.render(rows, ["org_id"], 500)  # A limit below the size.

    @pytest.mark.parametrize("limit_bytes", [0, -1])
    def test_a_limit_of_zero_or_less_refuses_every_report(self, limit_bytes: int) -> None:
        """The header alone has bytes, so no limit at or below zero can hold a report."""
        with pytest.raises(ReportTooLarge, match=f"The limit is {limit_bytes} bytes"):  # The message names the limit.
            CsvRenderer.render([], ["org_id"], limit_bytes)  # Even an empty report has a header.

    def test_a_limit_equal_to_the_size_passes(self) -> None:
        """The limit is the most bytes that the file may hold, so a file of that size is allowed."""
        size = len(CsvRenderer.render([{"org_id": "o1"}], ["org_id"], 1_000_000))  # The exact size of the file.
        assert len(CsvRenderer.render([{"org_id": "o1"}], ["org_id"], size)) == size  # Allowed at the limit.
        with pytest.raises(ReportTooLarge):  # One byte less is refused.
            CsvRenderer.render([{"org_id": "o1"}], ["org_id"], size - 1)


class TestCsvVerifier:
    """The check proves that a written file matches its rows."""

    def test_matching_file_passes(self) -> None:
        """The right header and the right row count pass, and the check returns nothing."""
        data = CsvRenderer.render([{"org_id": "o1"}, {"org_id": "o2"}], ["org_id"], 1_000_000)  # Two rows.
        assert CsvVerifier.verify(data, ["org_id"], 2) is None  # The check raises on a mismatch, so a pass is None.

    def test_a_value_with_a_line_break_counts_as_one_row(self) -> None:
        """The check counts parsed rows, not physical lines."""
        data = CsvRenderer.render([{"org_id": "a\nb"}], ["org_id"], 1_000_000)  # One row over two lines.
        assert CsvVerifier.verify(data, ["org_id"], 1) is None  # One row, as the parser reads it.

    def test_a_header_only_file_matches_zero_rows(self) -> None:
        """A report with no row is the header alone, and zero rows pass."""
        data = CsvRenderer.render([], ["org_id"], 1_000_000)  # No row.
        assert CsvVerifier.verify(data, ["org_id"], 0) is None  # Zero rows is a legal count.

    def test_a_negative_row_count_never_matches(self) -> None:
        """No file can hold a negative number of rows."""
        data = CsvRenderer.render([], ["org_id"], 1_000_000)  # No row.
        with pytest.raises(ReportCheckError, match="should hold -1 rows"):  # The message names the count.
            CsvVerifier.verify(data, ["org_id"], -1)  # A count below zero.

    def test_wrong_header_fails(self) -> None:
        """A header that differs from the expected columns fails."""
        data = CsvRenderer.render([{"org_id": "o1"}], ["org_id"], 1_000_000)  # One row.
        with pytest.raises(ReportCheckError):  # The documented error.
            CsvVerifier.verify(data, ["other"], 1)  # A different header.

    def test_wrong_row_count_fails(self) -> None:
        """A file with fewer rows than expected fails."""
        data = CsvRenderer.render([{"org_id": "o1"}], ["org_id"], 1_000_000)  # One row.
        with pytest.raises(ReportCheckError):  # The documented error.
            CsvVerifier.verify(data, ["org_id"], 2)  # Two rows expected.

    def test_ragged_row_fails(self) -> None:
        """A row with the wrong number of cells fails."""
        with pytest.raises(ReportCheckError):  # The documented error.
            CsvVerifier.verify(b"org_id,device_name\r\no1\r\n", ["org_id", "device_name"], 1)  # A short row.

    def test_empty_file_fails(self) -> None:
        """A file with no header fails."""
        with pytest.raises(ReportCheckError):  # The documented error.
            CsvVerifier.verify(b"", ["org_id"], 0)  # No bytes at all.
