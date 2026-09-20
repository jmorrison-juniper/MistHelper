"""Guard the portal report of the files an operation wrote.

Issue #3089: menu 25 wrote ``OrgAuditAnalysis.md`` and ``OrgAuditAnalysis.html``
and announced them with the sentence ``Mermaid report: data/...``. The portal
listed zero files, because the scraper accepted three phrases and four
extensions. An engineer then read an empty result panel and believed the run
produced nothing.

These tests hold both repairs. The regular expression must read the real
sentence menu 25 logs, and the directory scanner must find a file that no log
line names at all.
"""

from __future__ import annotations

import os
from collections import deque

import pytest

from web_portal.services.operation import _RunLogHandler
from web_portal.services.output_scan import OutputFileScanner


def _extract(message: str) -> list[str]:
    """Return every file name the portal scraper reads from one log sentence."""
    return _RunLogHandler._OUTPUT_FILE_RE.findall(message)


class TestOutputFileRegex:
    """The scraper must read the sentences the operations really log."""

    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("Mermaid report: data/OrgAuditAnalysis.md", "OrgAuditAnalysis.md"),
            ("HTML report: data/OrgAuditAnalysis.html", "OrgAuditAnalysis.html"),
            ("Wrote 42 rows to data/Sites.csv", "Sites.csv"),
            ("Results written to data/Devices.json", "Devices.json"),
            ("Capture saved to data/session.pcap", "session.pcap"),
            ("Exported to data/summary.xlsx", "summary.xlsx"),
        ],
    )
    def test_reads_the_real_sentences(self, message, expected):
        """Every sentence an operation logs must yield its file name."""
        assert expected in _extract(message)  # The panel needs this name to show the report.

    def test_markdown_report_was_the_reported_loss(self):
        """The exact menu 25 line must produce a name, because it produced none before."""
        assert _extract("Mermaid report: data/OrgAuditAnalysis.md") == ["OrgAuditAnalysis.md"]

    def test_ignores_a_sentence_that_names_no_file(self):
        """A progress line must not add a phantom name to the result panel."""
        assert _extract("Audit complete. 12 sites reviewed.") == []


class TestOutputFileScanner:
    """The scanner must find a report that no log sentence names."""

    def test_finds_a_file_created_during_the_run(self, tmp_path):
        """A file that appears after the snapshot must reach the result list."""
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()  # Record the empty directory before the operation writes.
        (tmp_path / "OrgAuditAnalysis.md").write_text("# report", encoding="utf-8")
        assert scanner.changed_files() == ["OrgAuditAnalysis.md"]

    def test_ignores_a_file_that_existed_before_the_run(self, tmp_path):
        """An untouched file must not appear, because this run did not write it."""
        (tmp_path / "older.csv").write_text("a,b\n", encoding="utf-8")
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()  # The file already exists at this moment.
        assert scanner.changed_files() == []

    def test_finds_a_file_the_run_rewrote(self, tmp_path):
        """A rewritten file must appear, because the run refreshed its content."""
        target = tmp_path / "Sites.csv"
        target.write_text("a,b\n", encoding="utf-8")
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        os.utime(target, (target.stat().st_atime, target.stat().st_mtime + 10))  # Advance the modification time.
        assert scanner.changed_files() == ["Sites.csv"]

    def test_reports_a_file_in_a_subdirectory(self, tmp_path):
        """A report under a subdirectory must reach the list with its relative path."""
        nested = tmp_path / "per-host-logs"
        nested.mkdir()
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (nested / "switch1.log").write_text("ok", encoding="utf-8")
        assert scanner.changed_files() == ["per-host-logs/switch1.log"]

    def test_skips_a_partial_write(self, tmp_path):
        """A temporary file is not a finished report, so it must stay out of the list."""
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (tmp_path / "export.csv.tmp").write_text("x", encoding="utf-8")
        assert scanner.changed_files() == []

    def test_missing_directory_returns_no_name(self, tmp_path):
        """A missing data directory must yield an empty list instead of raising."""
        scanner = OutputFileScanner(str(tmp_path / "absent"))
        scanner.snapshot()
        assert scanner.changed_files() == []

    def test_cap_limits_the_reported_names(self, tmp_path):
        """A run that writes many files must not flood the result panel."""
        scanner = OutputFileScanner(str(tmp_path), limit=3)
        scanner.snapshot()
        for index in range(10):
            (tmp_path / f"report{index}.csv").write_text("x", encoding="utf-8")
        assert len(scanner.changed_files()) == 3


class TestRunRecordMerge:
    """The executor must merge the scanned names without a duplicate."""

    def test_merge_adds_only_the_unknown_name(self, tmp_path):
        """A name the log already produced must not appear twice in the panel."""
        from web_portal.services.operation import OperationExecutor

        run = {"run_id": "r1", "output_files": deque(maxlen=50)}
        run["output_files"].append("Sites.csv")  # The log scrape already found this report.
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (tmp_path / "Sites.csv").write_text("a,b\n", encoding="utf-8")
        (tmp_path / "Extra.md").write_text("# x", encoding="utf-8")
        OperationExecutor._record_scanned_files(OperationExecutor.__new__(OperationExecutor), run, scanner)
        assert list(run["output_files"]) == ["Sites.csv", "Extra.md"]
