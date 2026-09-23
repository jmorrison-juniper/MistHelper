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

import re
from collections import deque
from pathlib import Path

import pytest

from src.utils import rate_limiting
from web_portal.services.operation import OperationExecutor
from web_portal.services.output_scan import (
    EXCLUDED_DIR_NAMES,
    RUNTIME_FILE_NAMES,
    OutputFileScanner,
)

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


class TestPrunedTreesStayOutOfTheWalk:
    """Issue #3140 prunes large trees. A pruned tree can never reach the panel."""

    def test_a_pruned_tree_is_not_scanned(self, tmp_path):
        """A file inside an excluded tree must not reach the result panel."""
        corpus = tmp_path / "juniper_pdf_library"
        corpus.mkdir()
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (corpus / "manual.pdf").write_bytes(b"%PDF-1.4\n")  # The corpus is reference material.
        (tmp_path / "Report.csv").write_text("a,b\n", encoding="utf-8")  # A real report.
        assert scanner.changed_files() == ["Report.csv"]

    def test_the_walk_counts_every_unpruned_file(self, tmp_path):
        """The scan must still read a nested report that no rule excludes."""
        nested = tmp_path / "exports" / "weekly"
        nested.mkdir(parents=True)
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (nested / "Inventory.csv").write_text("a\n", encoding="utf-8")
        assert scanner.changed_files() == ["exports/weekly/Inventory.csv"]

    def test_ssh_transcripts_are_never_pruned(self):
        """A per-host SSH log is operation output, so the prune list must omit it."""
        # The companion test above asserts the scanner reports this path. Naming
        # the directory here stops a future edit from pruning it by mistake.
        assert "per-host-logs" not in EXCLUDED_DIR_NAMES

    def test_the_operator_can_extend_the_prune_list(self, tmp_path, monkeypatch):
        """A site can hold a large tree that this repository cannot know about."""
        bulky = tmp_path / "site_archive"
        bulky.mkdir()
        monkeypatch.setenv("PORTAL_SCAN_EXCLUDE_DIRS", "site_archive")
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (bulky / "old.csv").write_text("a\n", encoding="utf-8")
        (tmp_path / "New.csv").write_text("a\n", encoding="utf-8")
        assert scanner.changed_files() == ["New.csv"]


# Issue #3201: the test suites write their artifacts into the data folder, and
# the live container mounts that folder. The tree reached 1,522 directories, and
# the walk of it cost 67 seconds for every operation the portal ran.
TEST_ARTIFACT_RUNS = 40  # Enough nested folders to make an unpruned walk plainly visible.


class TestTestOutputNeverSlowsTheWalk:
    """A test output tree must never reach the result panel or cost a listing."""

    def _build_test_output_tree(self, root: Path) -> None:
        """Create the nested, mostly empty tree that the upgrade portal suites leave."""
        for run in range(TEST_ARTIFACT_RUNS):  # One folder for each recorded test run.
            step = root / "test-artifacts" / "upgrade-portal" / f"run-{run}" / "screenshots"
            step.mkdir(parents=True)  # Most of the real folders hold nothing at all.

    def test_a_test_artifact_file_stays_out_of_the_result_panel(self, tmp_path):
        """A file that a test run writes is not an operation output."""
        self._build_test_output_tree(tmp_path)
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (tmp_path / "test-artifacts" / "upgrade-portal" / "run-0" / "report.json").write_text("{}", encoding="utf-8")
        (tmp_path / "SiteWlans.csv").write_text("a,b\n", encoding="utf-8")  # The real report.
        assert scanner.changed_files() == ["SiteWlans.csv"]

    def test_the_walk_refuses_a_test_output_tree_before_it_descends(self, tmp_path):
        """The walk lists the root only, because every listing costs a round trip."""
        # A filter applied after the descent would still pass the test above,
        # and it would still pay the 67 seconds. Only a count of the listed
        # folders proves that the walk never entered the tree.
        self._build_test_output_tree(tmp_path)
        scanner = OutputFileScanner(str(tmp_path))
        scanner.snapshot()
        (tmp_path / "SiteWlans.csv").write_text("a,b\n", encoding="utf-8")
        assert scanner.changed_files() == ["SiteWlans.csv"]
        assert (
            scanner.last_walk_directories == 1
        ), f"the walk listed {scanner.last_walk_directories} folders, so it entered the test output tree"

    def test_every_test_output_folder_a_test_names_is_pruned(self):
        """Each data folder that a test module names as test output must be pruned."""
        # A new suite that writes data/<test-folder> would slow every portal run
        # again. This guard reads every test module, finds each data folder
        # whose name carries the word "test", and requires the prune.
        chained = re.compile(r"""["']data["']\s*\)?\s*/\s*[fr]?["']([^"'{}]+)["']""")  # data / "name"
        literal = re.compile(r"""["'](?:\./)?data[/\\]{1,2}([A-Za-z0-9_.\-]+)""")  # "data/name"
        modules = sorted((REPOSITORY_ROOT / "tests").rglob("*.py"))
        assert len(modules) >= 500, f"the guard read only {len(modules)} test modules, so it proves too little"
        named: dict[str, str] = {}  # Map each test output folder to one module that names it.
        for module in modules:
            text = module.read_text(encoding="utf-8", errors="replace")
            for pattern in (chained, literal):
                for match in pattern.finditer(text):
                    name = match.group(1)
                    if Path(name).suffix:  # A name with a suffix is a file, not a folder.
                        continue
                    if "test" in re.split(r"[-_.]", name.lower()):  # The name marks itself as test output.
                        named.setdefault(name, module.relative_to(REPOSITORY_ROOT).as_posix())
        # Measured on 2026-09-23: three folders. The floor proves the guard still
        # finds the known writers, so a broken pattern cannot report a clean result.
        assert len(named) >= 3, f"the guard found only {sorted(named)}, so its patterns no longer match"
        unpruned = {name: module for name, module in named.items() if name not in EXCLUDED_DIR_NAMES}
        assert not unpruned, f"these test output folders are not pruned, so each run pays their walk: {unpruned}"
