"""Guard the runtime files the results panel must not name as output.

Issue #3126: the scanner reported every file that changed during a run, so a
run that wrote one report listed four names.

```text
files : ['AllGatewayTestResults.csv', 'delay_metrics.json', 'script.log', 'tuning_data.json']
```

Three of those belong to the runtime. The engineer had to pick the report out
of a list that changed on every run.

These tests hold two contracts. The scanner must omit each runtime file, and
each name in the skip list must still match the writer that owns it. The
second contract matters because a rename would otherwise leave a stale entry
that silently stops skipping.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from src.utils import rate_limiting
from web_portal.services.operation import OperationExecutor
from web_portal.services.output_scan import RUNTIME_FILE_NAMES, OutputFileScanner

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class TestRuntimeFilesStayOutOfTheResultPanel:
    """A file the runtime writes on every run is not an operation output."""

    @pytest.mark.parametrize("runtime_name", RUNTIME_FILE_NAMES)
    def test_scanner_omits_each_runtime_file(self, tmp_path, runtime_name):
        """Each runtime file must stay out of the list, whatever the run wrote."""
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()  # Record the empty directory before the run writes.
        (tmp_path / runtime_name).write_text("runtime", encoding="utf-8")
        assert scanner.changed_files() == []

    def test_scanner_keeps_the_report_beside_the_runtime_files(self, tmp_path):
        """The report must survive while every runtime file drops out."""
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        for runtime_name in RUNTIME_FILE_NAMES:
            (tmp_path / runtime_name).write_text("runtime", encoding="utf-8")
        (tmp_path / "AllGatewayTestResults.csv").write_text("a,b\n", encoding="utf-8")
        assert scanner.changed_files() == ["AllGatewayTestResults.csv"]

    def test_scanner_omits_a_rotated_log(self, tmp_path):
        """A rotated log carries a numeric suffix, and it is still runtime bookkeeping."""
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (tmp_path / "script.log.1").write_text("rotated", encoding="utf-8")
        (tmp_path / "script.log.12").write_text("rotated", encoding="utf-8")
        assert scanner.changed_files() == []

    def test_scanner_keeps_a_report_whose_name_starts_like_a_runtime_file(self, tmp_path):
        """A report is not runtime bookkeeping because its name shares a prefix."""
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (tmp_path / "script_log_summary.csv").write_text("a,b\n", encoding="utf-8")
        assert scanner.changed_files() == ["script_log_summary.csv"]

    def test_scanner_keeps_an_ssh_host_log(self, tmp_path):
        """A per-host SSH log is real operation output, so it must reach the panel."""
        nested = tmp_path / "per-host-logs"
        nested.mkdir()
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (nested / "switch1.log").write_text("ok", encoding="utf-8")
        assert scanner.changed_files() == ["per-host-logs/switch1.log"]


class TestALogLineStillWins:
    """An operation that names a runtime file keeps that name in the panel."""

    def test_named_runtime_file_survives_the_merge(self, tmp_path):
        """The merge adds scanned names, so a prose-matched name is never removed."""
        run = {"run_id": "r1", "output_files": deque(maxlen=50)}
        run["output_files"].append("script.log")  # An operation claimed this file in its log.
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (tmp_path / "script.log").write_text("runtime", encoding="utf-8")
        (tmp_path / "Report.csv").write_text("a,b\n", encoding="utf-8")
        OperationExecutor._record_scanned_files(OperationExecutor.__new__(OperationExecutor), run, scanner)
        assert list(run["output_files"]) == ["script.log", "Report.csv"]


class TestSkipListMatchesItsWriters:
    """A rename must not leave a stale entry that stops skipping."""

    def test_rate_limiter_names_match_their_constants(self):
        """The two rate-limiter names must equal the constants that module defines."""
        assert rate_limiting._METRICS_FILENAME in RUNTIME_FILE_NAMES
        assert rate_limiting._TUNING_FILENAME in RUNTIME_FILE_NAMES

    def test_application_log_name_is_still_live(self):
        """The application log name must still appear in the module that opens it."""
        source = (REPOSITORY_ROOT / "src" / "refactors" / "main_entrypoint.py").read_text(encoding="utf-8")
        assert "script.log" in source
        assert "script.log" in RUNTIME_FILE_NAMES

    def test_access_log_name_is_still_live(self):
        """The Gunicorn access log name must still appear in the start script."""
        source = (REPOSITORY_ROOT / "container" / "scripts" / "start.sh").read_text(encoding="utf-8")
        assert "portal_access.log" in source
        assert "portal_access.log" in RUNTIME_FILE_NAMES

    def test_skip_list_holds_every_reported_name(self):
        """The list must hold the four names the reported run showed."""
        assert set(RUNTIME_FILE_NAMES) == {
            "script.log",
            "portal_access.log",
            "delay_metrics.json",
            "tuning_data.json",
        }
