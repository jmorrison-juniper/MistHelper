"""Tests for the report exporter."""

from __future__ import annotations

import csv  # Read the written file the way a spreadsheet would.
from datetime import UTC, datetime  # The run time names the file.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from types import SimpleNamespace  # A runtime double with a fake exporter.
from unittest.mock import Mock, patch  # Record the exporter call.

import pytest  # Check the documented errors.

from src.operations.exporting.ex_hardware_inventory.report.csv_file import ReportCheckError, ReportTooLarge  # Errors.
from src.operations.exporting.ex_hardware_inventory.report.export import ReportExporter, ReportFile  # Unit.

RUN = datetime(2026, 11, 24, 23, 15, 7, tzinfo=UTC)  # An invented run time.
FIELDS = ["org_id", "device_name", "item_description"]  # A small column list.
ROWS = [
    {"org_id": "o1", "device_name": "d1", "item_description": "first"},
    {"org_id": "o1", "device_name": "d2", "item_description": "second, with a comma"},
]  # Two rows.
TARGET = "src.operations.exporting.ex_hardware_inventory.report.export.SourceDependencyResolver"  # The seam.


def runtime(write: Mock) -> SimpleNamespace:
    """Build a resolver double whose exporter is the given mock."""
    return SimpleNamespace(DataExporter=SimpleNamespace(write_with_format_selection=write))


def real_writer(path_text: str, data: list[dict[str, str]], names: list[str]) -> bool:
    """Write the file the way the standard exporter does: UTF-8, CRLF, standard quoting."""
    with open(path_text, "w", newline="", encoding="utf-8") as handle:  # The same open mode as the exporter.
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")  # The same writer class.
        writer.writeheader()  # The header row.
        writer.writerows(data)  # The data rows.
    return True


class TestWrite:
    """The exporter writes, checks, and names the file."""

    def test_calls_the_standard_exporter_with_csv_forced_and_explicit_columns(self, tmp_path: Path) -> None:
        """The call names the endpoint, the columns, and the CSV format override."""

        def write(data: list[dict[str, str]], path_text: str, **kwargs: object) -> bool:
            """Act as the exporter and write the file."""
            return real_writer(path_text, data, kwargs["fieldnames"])  # type: ignore[arg-type]

        mock = Mock(side_effect=write)  # Record the call and write the file.
        with patch(TARGET, runtime(mock)):
            result = ReportExporter(tmp_path).write(ROWS, FIELDS, RUN)
        assert result is not None and result.row_count == 2  # Two rows written.
        assert result.path == tmp_path / "ExHardwareInventory_20261124T231507Z.csv"  # The UTC stamped name.
        call = mock.call_args  # The one exporter call.
        assert call.args[0] == ROWS and call.args[1] == str(result.path)  # Rows and path.
        assert call.kwargs["api_function_name"] == "ExHardwareInventory"  # The natural-key strategy.
        assert call.kwargs["fieldnames"] == FIELDS  # The column order of the contract.
        assert call.kwargs["backend_options"].format_override == "csv"  # CSV is forced.

    def test_the_real_exporter_writes_a_file_that_passes_the_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The standard exporter and the check agree on the file format."""
        monkeypatch.setenv("MISTHELPER_STANDALONE", "true")  # No database backend in a unit test.
        monkeypatch.setenv("OUTPUT_FORMAT", "sqlite")  # The override must win over the global setting.
        result = ReportExporter(tmp_path).write(ROWS, FIELDS, RUN)  # The real DataExporter.
        assert isinstance(result, ReportFile) and result.row_count == len(ROWS)  # A file with every row was written.
        with result.path.open(newline="", encoding="utf-8") as handle:  # Read it back.
            cells = list(csv.reader(handle))
        assert cells == [FIELDS] + [[row[name] for name in FIELDS] for row in ROWS]  # Header and rows.

    def test_a_second_report_in_the_same_second_never_overwrites_the_first(self, tmp_path: Path) -> None:
        """An existing name gets the suffix _2, and the earlier file stays untouched."""
        first = tmp_path / "ExHardwareInventory_20261124T231507Z.csv"  # The name of the first choice.
        first.write_text("earlier report", encoding="utf-8")  # An earlier report.
        mock = Mock(side_effect=lambda data, path_text, **kwargs: real_writer(path_text, data, kwargs["fieldnames"]))
        with patch(TARGET, runtime(mock)):
            result = ReportExporter(tmp_path).write(ROWS, FIELDS, RUN)
        assert result is not None and result.path.name == "ExHardwareInventory_20261124T231507Z_2.csv"  # Suffix.
        assert first.read_text(encoding="utf-8") == "earlier report"  # The earlier file is untouched.

    def test_creates_the_data_folder_when_it_is_missing(self, tmp_path: Path) -> None:
        """A folder that does not exist yet is created before the write."""
        folder = tmp_path / "new" / "data"  # Two levels that do not exist.
        mock = Mock(side_effect=lambda data, path_text, **kwargs: real_writer(path_text, data, kwargs["fieldnames"]))
        with patch(TARGET, runtime(mock)):
            result = ReportExporter(folder).write(ROWS, FIELDS, RUN)
        assert result is not None and result.path.parent == folder and result.path.exists()  # Written.


class TestNoFileCases:
    """Some runs must leave no file."""

    def test_no_rows_writes_nothing_and_does_not_call_the_exporter(self, tmp_path: Path) -> None:
        """An empty run returns None and touches nothing."""
        mock = Mock()  # Must stay unused.
        with patch(TARGET, runtime(mock)):
            assert ReportExporter(tmp_path).write([], FIELDS, RUN) is None  # FR-042.
        mock.assert_not_called()  # No call.
        assert list(tmp_path.iterdir()) == []  # No file, no folder content.

    @pytest.mark.parametrize("limit_bytes", [20, 0, -1])
    def test_a_report_over_the_limit_is_refused_before_any_write(self, tmp_path: Path, limit_bytes: int) -> None:
        """A report that would pass the limit raises and writes nothing, and a limit of zero or less passes none."""
        mock = Mock()  # Must stay unused.
        exporter = ReportExporter(tmp_path)
        with patch.object(ReportExporter, "LIMIT_BYTES", limit_bytes), patch(TARGET, runtime(mock)):
            with pytest.raises(ReportTooLarge):
                exporter.write(ROWS, FIELDS, RUN)
        mock.assert_not_called()  # No call.
        assert list(tmp_path.iterdir()) == []  # No file.

    def test_the_default_limit_is_64_mebibytes(self) -> None:
        """The CLI limit matches the portal run limit."""
        assert ReportExporter.LIMIT_BYTES == 64 * 1024 * 1024  # FR-041.


class TestFileCheck:
    """A file that fails the check is removed, and the error is the documented one."""

    def test_an_exporter_that_returns_false_leaves_no_file(self, tmp_path: Path) -> None:
        """A failed write raises the check error and leaves no file."""
        mock = Mock(return_value=False)  # The exporter reports failure and writes nothing.
        with patch(TARGET, runtime(mock)):
            with pytest.raises(ReportCheckError):
                ReportExporter(tmp_path).write(ROWS, FIELDS, RUN)
        assert list(tmp_path.iterdir()) == []  # No file.

    def test_a_truncated_file_is_removed(self, tmp_path: Path) -> None:
        """A file with the header and one row of two fails the check and is removed."""

        def write(data: list[dict[str, str]], path_text: str, **kwargs: object) -> bool:
            """Write a truncated file and claim success."""
            return real_writer(path_text, data[:1], kwargs["fieldnames"])  # type: ignore[arg-type]

        with patch(TARGET, runtime(Mock(side_effect=write))):
            with pytest.raises(ReportCheckError, match="should hold 2 rows"):
                ReportExporter(tmp_path).write(ROWS, FIELDS, RUN)
        assert list(tmp_path.iterdir()) == []  # The damaged file is gone.

    def test_a_file_the_exporter_never_created_fails_the_check(self, tmp_path: Path) -> None:
        """An exporter that claims success and writes nothing raises the check error."""
        with patch(TARGET, runtime(Mock(return_value=True))):
            with pytest.raises(ReportCheckError):
                ReportExporter(tmp_path).write(ROWS, FIELDS, RUN)
        assert list(tmp_path.iterdir()) == []  # No file.

    def test_a_file_with_the_wrong_header_is_removed(self, tmp_path: Path) -> None:
        """A header that differs from the columns fails the check."""

        def write(data: list[dict[str, str]], path_text: str, **kwargs: object) -> bool:
            """Write the rows under the wrong columns and claim success."""
            return real_writer(path_text, data, ["org_id", "device_name", "other"])  # type: ignore[arg-type]

        with patch(TARGET, runtime(Mock(side_effect=write))):
            with pytest.raises(ReportCheckError, match="header"):
                ReportExporter(tmp_path).write(ROWS, FIELDS, RUN)
        assert list(tmp_path.iterdir()) == []  # The damaged file is gone.
