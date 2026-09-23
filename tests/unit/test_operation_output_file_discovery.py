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

from web_portal.services.operation import PARAMETER_REGISTRY, _RunLogHandler
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

    def test_finalize_removes_a_log_name_when_the_file_does_not_exist(self, tmp_path):
        """A no-data export log line must not create a previewable phantom file."""
        from web_portal.services.operation import OperationExecutor

        run = {"run_id": "r1", "menu_number": "4", "output_files": deque(maxlen=50)}  # Build the run state.
        run["output_files"].append("OrgCurrentGuests.csv")  # Simulate the log scrape finding a no-data filename.
        executor = OperationExecutor.__new__(OperationExecutor)  # Avoid the thread pool for a focused unit guard.
        executor._finalize_output_files(run, tmp_path)  # Remove names that do not exist under the data directory.
        assert list(run["output_files"]) == []  # The results panel must not offer a missing file.

    def test_finalize_moves_site_cache_after_the_site_result(self, tmp_path):
        """A site prompt cache must not be the first preview when a result exists."""
        from web_portal.services.operation import OperationExecutor

        (tmp_path / "SiteList.csv").write_text("site\n", encoding="utf-8")  # Create the prompt cache file.
        (tmp_path / "SiteWlans_AlamoSanAntonio.csv").write_text("wlan\n", encoding="utf-8")  # Create the result.
        run = {"run_id": "r2", "menu_number": "69", "output_files": deque(maxlen=50)}  # Build a site-scoped run.
        run["output_files"].append("SiteList.csv")  # Simulate the scanner finding the cache first.
        run["output_files"].append("SiteWlans_AlamoSanAntonio.csv")  # Simulate the operation output.
        executor = OperationExecutor.__new__(OperationExecutor)  # Avoid the thread pool for a focused unit guard.
        executor._finalize_output_files(run, tmp_path)  # Reorder cache names after true operation outputs.
        expected = ["SiteWlans_AlamoSanAntonio.csv", "SiteList.csv"]  # Name the safe preview order.
        assert list(run["output_files"]) == expected  # Preview the result first.

    def test_site_parameter_rows_measure_prompt_cache_risk(self):
        """The guard must state how many rows can refresh the site cache."""
        site_menus = [  # Build the measured row list from the same metadata that builds portal controls.
            int(menu_number)  # Compare menu numbers as integers, because the registry keys are strings.
            for menu_number, entry in PARAMETER_REGISTRY.items()  # Read each portal parameter definition once.
            if any(  # Keep rows whose controls can select a site and refresh the cache.
                "site" in str(parameter.get("name", "")).lower()  # Detect site-scoped control names.
                or "site" in str(parameter.get("source", "")).lower()  # Detect site-backed selector sources.
                or str(parameter.get("type", "")).lower() in {"site", "site_select"}  # Detect site selector types.
                for parameter in entry.get("parameters", [])  # Read the controls that the portal renders.
                if isinstance(parameter, dict)  # Ignore malformed test fixtures without failing the measurement.
            )
        ]
        print(f"The site cache output guard checked {len(site_menus)} site-scoped portal rows.")  # Guard proof.
        assert len(site_menus) == 76  # Pin the measured risk set, so a future change updates the evidence.
        assert 69 in site_menus  # Menu 69 reproduced the defect and must stay in the measured set.
        assert 1 not in site_menus  # Menu 1 exports SiteList.csv directly, so it stays outside this cache-risk set.

    def test_finalize_keeps_site_list_when_menu_one_exports_it(self, tmp_path):
        """Menu 1 must keep its site list output because it is the operation result."""
        from web_portal.services.operation import OperationExecutor

        (tmp_path / "SiteList.csv").write_text("site\n", encoding="utf-8")  # Create the menu 1 result file.
        run = {"run_id": "r3", "menu_number": "1", "output_files": deque(maxlen=50)}  # Build a menu 1 run.
        run["output_files"].append("SiteList.csv")  # Simulate the scanner finding the site list export.
        executor = OperationExecutor.__new__(OperationExecutor)  # Avoid the thread pool for a focused unit guard.
        executor._finalize_output_files(run, tmp_path)  # Keep existing files even when their name is a cache elsewhere.
        assert list(run["output_files"]) == ["SiteList.csv"]  # Menu 1 must still show its result file.

    def test_finalize_drops_lonely_site_cache_when_the_run_reports_no_data(self, tmp_path):
        """A prompt cache must not hide an empty site-scoped operation result."""
        from web_portal.services.operation import OperationExecutor

        (tmp_path / "SiteList.csv").write_text("site\n", encoding="utf-8")  # Create the prompt cache file.
        run = {"run_id": "r4", "menu_number": "69", "output_files": deque(maxlen=50)}  # Build a site-scoped run.
        run["log_messages"] = [
            {"message": "No data provided for output to SiteWlans_AlamoSanAntonio.csv"}
        ]  # Mark no data.
        run["output_files"].append("SiteList.csv")  # Simulate the scanner finding only the cache refresh.
        executor = OperationExecutor.__new__(OperationExecutor)  # Avoid the thread pool for a focused unit guard.
        executor._finalize_output_files(run, tmp_path)  # Remove cache-only evidence when the run says no data.
        assert list(run["output_files"]) == []  # The completion guard must read the no-data reason instead.
