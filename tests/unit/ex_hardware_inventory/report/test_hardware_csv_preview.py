"""Tests for the page reader of the combined CSV report (issue #4931)."""

from __future__ import annotations

import pytest  # Check the documented errors and the failure paths.

from src.operations.exporting.ex_hardware_inventory.report.csv_file import (
    CsvPreviewer,
    CsvRenderer,
    ReportCheckError,
)  # Units.

FIELDS = ["org_name", "device_name", "item_description"]  # A small column list for the tests.


def make_report(rows: list[dict[str, str]] | None = None) -> bytes:
    """Render a report with the real renderer, so the tests read the bytes that a run publishes."""
    default = [
        {"org_name": "Alpha", "device_name": f"ex-{index:02d}", "item_description": f"Part {index}"}
        for index in range(1, 6)
    ]
    return CsvRenderer.render(default if rows is None else rows, FIELDS, 10_000_000)  # Five rows unless told otherwise.


class TestPaging:
    """The page holds the columns, the rows from the offset, and the true totals."""

    def test_the_first_page_has_the_columns_the_rows_and_the_totals(self) -> None:
        """Two rows of five, with the column names and the counts of the whole file."""
        page = CsvPreviewer.page(make_report(), 0, 2)
        assert page["columns"] == FIELDS and page["total"] == 5 and page["matched"] == 5
        assert page["rows"] == [["Alpha", "ex-01", "Part 1"], ["Alpha", "ex-02", "Part 2"]]
        assert page["offset"] == 0 and page["limit"] == 2 and page["cut_cells"] == 0

    def test_a_later_page_starts_at_the_offset(self) -> None:
        """The offset skips whole rows, in the order of the file."""
        page = CsvPreviewer.page(make_report(), 2, 2)
        assert [row[1] for row in page["rows"]] == ["ex-03", "ex-04"]

    def test_the_last_page_can_be_short(self) -> None:
        """A page that reaches the end holds only the rows that remain."""
        page = CsvPreviewer.page(make_report(), 4, 3)
        assert [row[1] for row in page["rows"]] == ["ex-05"] and page["total"] == 5

    def test_a_page_past_the_end_is_empty_and_keeps_the_totals(self) -> None:
        """No row is a legal answer, and the counts still describe the file."""
        page = CsvPreviewer.page(make_report(), 10, 2)
        assert page["rows"] == [] and page["total"] == 5 and page["matched"] == 5

    def test_a_limit_above_the_row_count_returns_every_row(self) -> None:
        """The reader does not need the rows to fill a page."""
        assert len(CsvPreviewer.page(make_report(), 0, 1000)["rows"]) == 5

    def test_a_header_only_file_has_no_rows(self) -> None:
        """A report with no row is the header alone. The page holds the columns and zero rows."""
        page = CsvPreviewer.page(make_report([]), 0, 10)
        assert page["columns"] == FIELDS and page["rows"] == [] and page["total"] == 0 and page["matched"] == 0

    @pytest.mark.parametrize("offset, limit", [(-1, 10), (0, 0), (0, -1), (-5, -5)])
    def test_a_bad_position_is_refused_and_no_file_is_read(self, offset: int, limit: int) -> None:
        """A negative offset would slice from the end, and a limit below 1 reads nothing, so both are refused."""
        with pytest.raises(ValueError, match="page offset must be 0 or more"):
            CsvPreviewer.page(b"not even read", offset, limit)  # The check runs before the parse.


class TestFilter:
    """The filter is a plain text search over the whole report."""

    @staticmethod
    def rows() -> bytes:
        """Return 250 rows where only the last page holds the word that the tests search."""
        rows = [
            {"org_name": "Alpha", "device_name": f"ex-{index:03d}", "item_description": "Fan"} for index in range(250)
        ]
        rows[240]["item_description"] = "Needle Module"
        return make_report(rows)

    def test_the_filter_covers_the_whole_report_and_not_only_the_page(self) -> None:
        """The only match is at row 240, and a first page of 10 rows still finds it."""
        page = CsvPreviewer.page(self.rows(), 0, 10, "needle")
        assert [row[1] for row in page["rows"]] == ["ex-240"]
        assert page["matched"] == 1 and page["total"] == 250

    def test_the_filter_matches_any_cell_and_ignores_case(self) -> None:
        """A word in the organization column matches the same way as a word in the part column."""
        report = make_report(
            [
                {"org_name": "Beta Org", "device_name": "sw-1", "item_description": "Fan"},
                {"org_name": "Alpha", "device_name": "sw-2", "item_description": "BETA Module"},
                {"org_name": "Alpha", "device_name": "sw-3", "item_description": "Fan"},
            ]
        )
        page = CsvPreviewer.page(report, 0, 10, "bEtA")
        assert [row[1] for row in page["rows"]] == ["sw-1", "sw-2"] and page["matched"] == 2

    def test_the_filter_pages_the_matching_rows_only(self) -> None:
        """The offset counts matching rows, so page two of the matches starts at the second match."""
        report = make_report(
            [{"org_name": "Alpha", "device_name": f"ex-{i}", "item_description": "Fan"} for i in range(6)]
        )
        page = CsvPreviewer.page(report, 2, 2, "fan")
        assert [row[1] for row in page["rows"]] == ["ex-2", "ex-3"] and page["matched"] == 6

    def test_the_filter_is_plain_text_and_never_a_pattern(self) -> None:
        """A dot is a dot, and a bracket that would break a pattern is only text."""
        report = make_report(
            [
                {"org_name": "o", "device_name": "ex.01", "item_description": "x"},
                {"org_name": "o", "device_name": "ex-02", "item_description": "x"},
            ]
        )
        assert [row[1] for row in CsvPreviewer.page(report, 0, 10, ".")["rows"]] == ["ex.01"]
        assert CsvPreviewer.page(report, 0, 10, "(")["matched"] == 0  # A pattern engine would raise here.

    @pytest.mark.parametrize("text", ["", "   ", "\t"])
    def test_a_blank_filter_matches_every_row(self, text: str) -> None:
        """Empty text and white space give the same answer as no filter."""
        assert CsvPreviewer.page(make_report(), 0, 10, text)["matched"] == 5

    def test_a_filter_with_no_match_gives_an_empty_page_and_the_total(self) -> None:
        """No match is a legal answer."""
        page = CsvPreviewer.page(make_report(), 0, 10, "absent")
        assert page["rows"] == [] and page["matched"] == 0 and page["total"] == 5


class TestCells:
    """A cell keeps its text, and a very long cell is cut."""

    @pytest.mark.parametrize("length, cut", [(999, 0), (1000, 0), (1001, 1), (5000, 1)])
    def test_a_cell_over_the_limit_is_cut_and_counted(self, length: int, cut: int) -> None:
        """The limit is the most characters that a cell keeps, so a cell of that size stays whole."""
        report = make_report([{"org_name": "Alpha", "device_name": "ex-01", "item_description": "x" * length}])
        page = CsvPreviewer.page(report, 0, 10)
        assert len(page["rows"][0][2]) == min(length, CsvPreviewer.CELL_LIMIT) and page["cut_cells"] == cut

    def test_commas_quotes_and_line_breaks_round_trip(self) -> None:
        """Standard quoting keeps an awkward value intact."""
        value = 'a,"b"\nc'
        page = CsvPreviewer.page(make_report([{"org_name": value, "device_name": "d", "item_description": "x"}]), 0, 5)
        assert page["rows"][0][0] == value

    def test_markup_in_a_cell_comes_back_unchanged(self) -> None:
        """The reader never edits text. The page sets cells as plain text, so markup cannot run."""
        value = "<img src=x onerror=alert(1)>"
        page = CsvPreviewer.page(make_report([{"org_name": value, "device_name": "d", "item_description": "x"}]), 0, 5)
        assert page["rows"][0][0] == value

    def test_a_cell_that_the_report_guard_prefixed_keeps_its_apostrophe(self) -> None:
        """The table shows the file as it is, so the guard apostrophe stays visible."""
        page = CsvPreviewer.page(
            make_report([{"org_name": "'=SUM(A1)", "device_name": "d", "item_description": "x"}]), 0, 5
        )
        assert page["rows"][0][0] == "'=SUM(A1)"


class TestDamagedFiles:
    """A file that is not a report gets one documented error."""

    def test_bytes_that_are_not_utf8_are_refused(self) -> None:
        """A byte that UTF-8 cannot decode is a damaged file."""
        with pytest.raises(ReportCheckError, match="not valid UTF-8 CSV"):
            CsvPreviewer.page(b"org_name\r\n\xff\xfe\r\n", 0, 10)

    def test_an_empty_file_is_refused(self) -> None:
        """A file with no header is not a report."""
        with pytest.raises(ReportCheckError, match="empty"):
            CsvPreviewer.page(b"", 0, 10)

    def test_a_ragged_row_is_refused(self) -> None:
        """A row with the wrong number of cells would make a crooked table."""
        with pytest.raises(ReportCheckError, match="wrong number of cells"):
            CsvPreviewer.page(b"a,b\r\n1\r\n", 0, 10)

    def test_a_cell_over_the_csv_reader_limit_is_refused(self) -> None:
        """The standard reader stops at 131072 characters in one field, and the error is the documented one."""
        huge = CsvRenderer.render([{"a": "x" * 200_000}], ["a"], 10_000_000)
        with pytest.raises(ReportCheckError, match="not valid UTF-8 CSV"):
            CsvPreviewer.page(huge, 0, 10)
