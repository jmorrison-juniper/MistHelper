"""Prove CSV suffix preservation through the actual local writer."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import pytest

from src.export.data_exporter import DataExporter
from src.utils.file_path_utils import FilePathUtils


class TestCsvSuffixNames:
    """Keep the supplied name when its final ASCII suffix is CSV."""

    @pytest.mark.parametrize("suffix", [".csv", ".csV", ".cSv", ".cSV", ".Csv", ".CsV", ".CSv", ".CSV"])
    def test_actual_writer_preserves_final_suffix(self, tmp_path: Path, suffix: str) -> None:
        """Write one real file for each of the eight suffix cases."""
        supplied = f"SiteWiFiClients{suffix}"
        assert DataExporter._write_csv_format([{"id": "client-1"}], supplied) is True
        destination = tmp_path / FilePathUtils.get_csv_path(supplied)
        assert sorted(path.name for path in destination.parent.iterdir()) == [supplied]
        with destination.open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["id"], ["client-1"]]
        print("Checked 1 filename and 1 CSV record:", supplied)

    @pytest.mark.parametrize(
        ("supplied", "expected"),
        [
            ("BareReport", "BareReport.csv"),
            ("Report.csv.backup", "Report.csv.backup.csv"),
            ("Report.CSV.old", "Report.CSV.old.csv"),
            ("Report.csvx", "Report.csvx.csv"),
            ("Report.json", "Report.json.csv"),
            ("Report.csv.", "Report.csv..csv"),
            ("Report.c\u017fv", "Report.c\u017fv.csv"),
            ("", ".csv"),
        ],
    )
    def test_actual_writer_appends_only_a_missing_final_suffix(
        self, tmp_path: Path, supplied: str, expected: str
    ) -> None:
        """An internal CSV segment or a different suffix does not prevent extension."""
        assert DataExporter._write_csv_format([{"id": "client-1"}], supplied) is True
        destination = tmp_path / "data" / expected
        assert sorted(path.name for path in destination.parent.iterdir()) == [expected]
        with destination.open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["id"], ["client-1"]]
        print("Checked 1 filename and 1 CSV record:", ascii(expected))

    @pytest.mark.parametrize("directory", ["Archive.csv", "Archive.CSV", "R\u00e9sultats.csv"])
    @pytest.mark.parametrize("supplied", ["MixedStem.CSV", "MixedStem"])
    def test_actual_writer_preserves_an_explicit_directory(self, tmp_path: Path, directory: str, supplied: str) -> None:
        """A directory suffix must not affect recognition of the final filename."""
        parent = tmp_path / directory
        parent.mkdir()
        target = str(parent / supplied)
        expected = supplied if supplied.endswith(".CSV") else f"{supplied}.csv"
        assert FilePathUtils.get_csv_path(target) == target
        assert DataExporter._write_csv_format([{"id": "client-1"}], target) is True
        assert sorted(path.name for path in parent.iterdir()) == [expected]
        with (parent / expected).open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["id"], ["client-1"]]
        assert list((tmp_path / "data").iterdir()) == []

    @pytest.mark.parametrize("supplied", ["R\u00e9seau_\u6771\u4eac.CSV", "R\u00e9seau_\u6771\u4eac", "MiXeDStem.CsV"])
    def test_actual_writer_preserves_unicode_and_stem_case(self, tmp_path: Path, supplied: str) -> None:
        """Comparison must not change Unicode content or the original stem."""
        expected = supplied if "." in supplied else f"{supplied}.csv"
        assert FilePathUtils.get_csv_path(supplied) == str(Path("data") / supplied)
        assert DataExporter._write_csv_format([{"name": "Caf\u00e9 \u6771\u4eac"}], supplied) is True
        destination = tmp_path / "data" / expected
        assert sorted(path.name for path in destination.parent.iterdir()) == [expected]
        with destination.open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["name"], ["Caf\u00e9 \u6771\u4eac"]]


class TestCsvSuffixRecords:
    """Preserve the writer's existing record and overwrite behavior."""

    def test_actual_writer_preserves_explicit_field_order_and_escaping(self, tmp_path: Path) -> None:
        """The suffix decision must not change CSV quoting or string processing."""
        data: list[dict[str, Any]] = [{"id": 7, "text": 'first\nsecond\r,"quoted"', "items": ["one", "two"]}]
        assert DataExporter._write_csv_format(data, "Records.CSV", ["text", "items", "id"]) is True
        with (tmp_path / "data" / "Records.CSV").open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [
                ["text", "items", "id"],
                ['first\\nsecond,"quoted"', "one,two", "7"],
            ]
        assert sorted(path.name for path in (tmp_path / "data").iterdir()) == ["Records.CSV"]

    def test_actual_writer_keeps_derived_field_order(self, tmp_path: Path) -> None:
        """The default header remains the sorted union of record keys."""
        data: list[dict[str, Any]] = [{"z": "last", "a": 1}, {"b": 2, "a": 3}]
        assert DataExporter._write_csv_format(data, "Records.CSV") is True
        with (tmp_path / "data" / "Records.CSV").open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["a", "b", "z"], ["1", "", "last"], ["3", "2", ""]]

    def test_repeat_write_truncates_the_same_file(self, tmp_path: Path) -> None:
        """A second write replaces prior rows without creating another name."""
        first = [{"id": "a-long-first-record"}, {"id": "a-long-second-record"}]
        assert DataExporter._write_csv_format(first, "Records.CSV") is True
        destination = tmp_path / "data" / "Records.CSV"
        first_size = destination.stat().st_size
        assert DataExporter._write_csv_format([{"id": "new"}], "Records.CSV") is True
        assert destination.stat().st_size < first_size
        assert sorted(path.name for path in destination.parent.iterdir()) == ["Records.CSV"]
        with destination.open(encoding="utf-8", newline="") as stream:
            assert list(csv.reader(stream)) == [["id"], ["new"]]
        print("Checked 2 writes, 1 filename, and 1 final CSV record.")


class TestCsvSuffixRefusals:
    """Keep the existing refusal and writer error boundaries."""

    @pytest.mark.parametrize("target", [None, 64, b"Records.CSV", Path("Records.CSV"), ["Records.CSV"]])
    def test_non_string_target_keeps_dispatch_refusal(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, target: Any
    ) -> None:
        """An invalid runtime target must not become a valid generated filename."""
        with caplog.at_level(logging.ERROR):
            result = DataExporter._dispatch_format_write([{"id": "client-1"}], target, "csv", None, "listOrgSites")
        assert result is False
        assert "Failed to write data to" in caplog.text
        assert list(tmp_path.rglob("*.csv")) == []
        assert list(tmp_path.rglob("*.CSV")) == []

    def test_actual_open_failure_still_propagates(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """A directory in place of a file must retain the real writer's OS error."""
        destination = tmp_path / "data" / "Blocked.CSV"
        destination.mkdir(parents=True)
        with caplog.at_level(logging.ERROR), pytest.raises(OSError):
            DataExporter._write_csv_format([{"id": "client-1"}], "Blocked.CSV")
        assert destination.is_dir()
        assert sorted(path.name for path in destination.parent.iterdir()) == ["Blocked.CSV"]
        assert "Blocked.CSV" in caplog.text
        assert any(record.levelno == logging.ERROR for record in caplog.records)
