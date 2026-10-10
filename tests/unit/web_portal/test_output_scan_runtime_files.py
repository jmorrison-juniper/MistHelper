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

import os
import re
import threading
from collections import deque
from pathlib import Path

import pytest

from src.foundation.support.utils import rate_limiting
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
        source = (REPOSITORY_ROOT / "src" / "foundation" / "support" / "refactors" / "main_entrypoint.py").read_text(
            encoding="utf-8"
        )
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

    def test_in_place_nested_rewrite_does_not_stat_untouched_siblings(self, tmp_path, monkeypatch):
        """An in-place rewrite must be found without statting each historical file."""
        output_dir = tmp_path / "CombinedInventory_ByWeek"  # Use the measured costly nested report folder.
        output_dir.mkdir()  # Create the folder before the scanner records the directory state.
        for index in range(25):  # Build enough siblings to prove whether the scan reads the whole folder.
            (output_dir / f"week-{index:02d}.csv").write_text("before\n", encoding="utf-8")
        target = output_dir / "week-07.csv"  # Pick one existing file to overwrite in place.
        scanner = OutputFileScanner(str(tmp_path))  # Build a scanner rooted at the temporary data directory.
        scanner.snapshot()  # Mark the run start before the operation overwrites its report.
        real_stat = Path.stat  # Keep the original method so the scanner still gets true file times.
        counted: list[str] = []  # Record which sibling CSV files the scanner asks the filesystem to stat.

        def counting_stat(path: Path, *args, **kwargs):
            """Count stats of historical report siblings before delegating."""
            if path.parent == output_dir and path.suffix == ".csv":  # Count only files in the measured hot folder.
                counted.append(path.name)  # Save the name so the failure shows the excessive scope.
            return real_stat(path, *args, **kwargs)  # Preserve the real filesystem behavior.

        monkeypatch.setattr(Path, "stat", counting_stat)  # Instrument stats after the snapshot setup finishes.
        target.write_text("after\n", encoding="utf-8")  # Rewrite an existing file without changing the folder mtime.
        assert scanner.changed_files() == ["CombinedInventory_ByWeek/week-07.csv"]
        assert len(set(counted)) <= 3, f"the scan statted too many sibling files: {sorted(set(counted))}"

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


class TestFullWalkFallback:
    """The costly full walk runs only when both fast paths find no output."""

    def _write_existing_reports(self, root: Path, count: int) -> Path:
        """Create historical reports and return one rewrite target."""
        reports = root / "reports"  # Keep the historical files in one measured folder.
        reports.mkdir()  # Create the folder before the scanner records directory marks.
        for index in range(count):  # Build enough files to show when the full walk runs.
            (reports / f"report-{index:04d}.csv").write_text("before\n", encoding="utf-8")
        return reports / "report-0007.csv"  # Return a stable existing file for rewrite tests.

    def _move_file_time_after_mark(self, path: Path) -> None:
        """Move one file timestamp after the scanner mark."""
        stamp = path.stat().st_mtime + 10  # Use seconds because os.utime accepts floats.
        os.utime(path, (stamp, stamp))  # Make the rewritten file newer on every filesystem.

    def test_tracked_write_avoids_full_walk_with_many_existing_files(self, tmp_path):
        """A tracked report must not stat every historical report."""
        self._write_existing_reports(tmp_path, 1000)  # Create historical files before the snapshot.
        scanner = OutputFileScanner(str(tmp_path))  # Scan the temporary data root.
        scanner.snapshot()  # Start write tracking after the historical files exist.
        (tmp_path / "Tracked.csv").write_text("after\n", encoding="utf-8")  # Use the tracked Path.open route.
        assert scanner.changed_files() == ["Tracked.csv"]
        assert scanner.last_scanned_files <= 3

    def test_utime_rewrite_uses_full_walk_when_fast_paths_find_nothing(self, tmp_path):
        """An untracked timestamp rewrite must still reach the result panel."""
        target = self._write_existing_reports(tmp_path, 25)  # Create an existing report before the snapshot.
        scanner = OutputFileScanner(str(tmp_path))  # Scan the temporary data root.
        scanner.snapshot()  # Record the start mark before the untracked rewrite.
        self._move_file_time_after_mark(target)  # Simulate a C writer that updates only file metadata.
        assert scanner.changed_files() == ["reports/report-0007.csv"]
        assert scanner.last_scanned_files >= 25

    def test_os_open_rewrite_uses_full_walk_when_fast_paths_find_nothing(self, tmp_path):
        """A writer that bypasses Python open must still reach the result panel."""
        target = self._write_existing_reports(tmp_path, 25)  # Create an existing report before the snapshot.
        scanner = OutputFileScanner(str(tmp_path))  # Scan the temporary data root.
        scanner.snapshot()  # Record the start mark before the low-level rewrite.
        descriptor = os.open(target, os.O_WRONLY | os.O_TRUNC)  # Bypass builtins.open and Path.open hooks.
        try:
            os.write(descriptor, b"after\n")  # Rewrite the file through the low-level descriptor.
        finally:
            os.close(descriptor)  # Close the descriptor so the timestamp is visible.
        self._move_file_time_after_mark(target)  # Make the rewrite deterministic across filesystems.
        assert scanner.changed_files() == ["reports/report-0007.csv"]
        assert scanner.last_scanned_files >= 25

    def test_replace_rewrite_uses_full_walk_when_fast_paths_find_nothing(self, tmp_path):
        """A temp-file replace onto an existing name must still reach the panel."""
        target = self._write_existing_reports(tmp_path, 25)  # Create an existing report before the snapshot.
        scanner = OutputFileScanner(str(tmp_path))  # Scan the temporary data root.
        scanner.snapshot()  # Record the start mark before the replace.
        replacement = target.with_name("report-0007.csv.replace")  # Keep the temp file inside the test root.
        replacement.write_text("after\n", encoding="utf-8")  # Create the replacement through normal Python I/O.
        os.replace(replacement, target)  # Replace the existing name through an untracked filesystem operation.
        self._move_file_time_after_mark(target)  # Make the replacement newer than the probe mark.
        assert scanner.changed_files() == ["reports/report-0007.csv"]
        assert scanner.last_scanned_files >= 25

    def test_no_output_pays_full_walk_and_returns_empty(self, tmp_path):
        """A run with no output pays the full walk and reports no false file."""
        self._write_existing_reports(tmp_path, 25)  # Create historical files before the snapshot.
        scanner = OutputFileScanner(str(tmp_path))  # Scan the temporary data root.
        scanner.snapshot()  # Record a run that writes no file.
        assert scanner.changed_files() == []
        assert scanner.last_scanned_files == 25

    def test_tracked_result_skips_untracked_rewrite_full_walk(self, tmp_path):
        """The untracked rewrite is not reported because the fast path found evidence."""
        target = self._write_existing_reports(tmp_path, 25)  # Create an existing report before the snapshot.
        scanner = OutputFileScanner(str(tmp_path))  # Scan the temporary data root.
        scanner.snapshot()  # Record the start mark before both writes.
        self._move_file_time_after_mark(target)  # Rewrite one existing file outside the tracking hook.
        (tmp_path / "Tracked.csv").write_text("after\n", encoding="utf-8")  # Add fast-path evidence.
        assert scanner.changed_files() == ["Tracked.csv"]
        assert scanner.last_scanned_files <= 3


class TestConcurrentOwnerTracking:
    """Concurrent scanners accept only unambiguous writes from their owner."""

    def test_overlapping_inventory_run_keeps_only_its_output(self, tmp_path):
        """Issue 4092: a later run must not add its output to the inventory result."""
        inventory_written = threading.Event()  # Start the second run after the inventory file exists.
        second_completed = threading.Event()  # Complete the second run before the inventory run.
        results: dict[str, list[str]] = {}  # Store both ordered overlap results for exact assertions.

        def inventory_worker() -> None:
            scanner = OutputFileScanner(str(tmp_path))  # Bind the inventory scanner to this worker.
            scanner.snapshot()  # Activate the first run before it writes its report.
            (tmp_path / "SiteInventory.csv").write_text("inventory", encoding="utf-8")  # Write owned evidence.
            inventory_written.set()  # Permit the overlapping run to start after this write.
            second_completed.wait(timeout=10)  # Keep the first scanner active until the second completes.
            results["inventory"] = scanner.changed_files()  # Collect the first result after the overlap ends.

        def other_worker() -> None:
            scanner = OutputFileScanner(str(tmp_path))  # Bind the overlapping scanner to its worker.
            scanner.snapshot()  # Activate the second run while the first scanner remains active.
            (tmp_path / "Other.csv").write_text("other", encoding="utf-8")  # Write only the second run output.
            results["other"] = scanner.changed_files()  # Complete the second scanner before the first.
            second_completed.set()  # Release the inventory scanner after the second result is final.

        inventory_thread = threading.Thread(target=inventory_worker)  # Build the first operation worker.
        inventory_thread.start()  # Start and snapshot the inventory scanner.
        assert inventory_written.wait(timeout=10), "the inventory worker did not write its report"
        other_thread = threading.Thread(target=other_worker)  # Build the later overlapping operation worker.
        other_thread.start()  # Start the second scanner before the first completes.
        other_thread.join(timeout=10)  # Require the second scanner to complete first.
        inventory_thread.join(timeout=10)  # Complete the inventory scanner after the second scanner.
        assert not other_thread.is_alive(), "the overlapping worker did not complete"
        assert not inventory_thread.is_alive(), "the inventory worker did not complete"
        assert results["inventory"] == ["SiteInventory.csv"]  # Reject the foreign Other.csv result.
        assert results["other"] == ["Other.csv"]  # Confirm the second run also keeps only its output.

    def test_distinct_owner_threads_keep_distinct_tracked_files(self, tmp_path):
        """Each scanner must report only the file its owner thread opened."""
        barrier = threading.Barrier(3)  # Hold both scanners active while each owner writes.
        release = threading.Event()  # Keep both registrations alive until both writes finish.
        results: dict[str, list[str]] = {}  # Store each owner scanner result for assertions.

        def worker(name: str) -> None:
            scanner = OutputFileScanner(str(tmp_path))  # Bind this scanner to its current worker owner.
            scanner.snapshot()  # Activate this scanner before synchronized writes.
            barrier.wait(timeout=10)  # Prove both scanners overlap.
            (tmp_path / f"{name}.csv").write_text(name, encoding="utf-8")  # Track one owner-specific file.
            release.wait(timeout=10)  # Keep the scanner active while the other owner writes.
            results[name] = scanner.changed_files()  # Stop tracking and collect approved evidence.

        threads = [threading.Thread(target=worker, args=(name,)) for name in ("alpha", "beta")]  # Build owners.
        for thread in threads:  # Start both owner threads before joining the barrier.
            thread.start()  # Activate one scanner in each thread.
        barrier.wait(timeout=10)  # Confirm both owner registrations are active.
        release.set()  # Let both scanners collect their tracked evidence.
        for thread in threads:  # Wait for deterministic cleanup.
            thread.join(timeout=10)  # Bound the test if hook cleanup fails.
        assert results == {"alpha": ["alpha.csv"], "beta": ["beta.csv"]}  # Reject cross-run paths.

    def test_shared_path_is_ambiguous_for_both_active_owners(self, tmp_path):
        """A path opened by both active owners must appear in neither result."""
        first_written = threading.Event()  # Order the two opens while both scanners remain active.
        second_written = threading.Event()  # Keep the first scanner active until ambiguity is recorded.
        results: dict[str, list[str]] = {}  # Store both scanner decisions.

        def first_worker() -> None:
            scanner = OutputFileScanner(str(tmp_path))  # Bind owner one from the current worker.
            scanner.snapshot()  # Register owner one before the shared write.
            (tmp_path / "Shared.csv").write_text("first", encoding="utf-8")  # Track the shared path first.
            first_written.set()  # Allow owner two to open the same path.
            second_written.wait(timeout=10)  # Keep owner one active through the second open.
            results["first"] = scanner.changed_files()  # Exclude the now-ambiguous path.

        def second_worker() -> None:
            first_written.wait(timeout=10)  # Wait until owner one tracks the path.
            scanner = OutputFileScanner(str(tmp_path))  # Bind owner two from the current worker.
            scanner.snapshot()  # Register owner two while owner one remains active.
            (tmp_path / "Shared.csv").write_text("second", encoding="utf-8")  # Make both owners possible.
            second_written.set()  # Release owner one after ambiguity is recorded.
            results["second"] = scanner.changed_files()  # Exclude the shared path for owner two.

        threads = [threading.Thread(target=first_worker), threading.Thread(target=second_worker)]  # Build owners.
        for thread in threads:  # Start the ordered overlap.
            thread.start()  # Run each scanner in its owner thread.
        for thread in threads:  # Wait for both ambiguity decisions.
            thread.join(timeout=10)  # Bound the test if ownership tracking deadlocks.
        assert results == {"first": [], "second": []}  # Reject the shared path from both runs.

    def test_overlap_disables_ownerless_timestamp_fallback(self, tmp_path):
        """A child-thread write during overlap must not become either run's evidence."""
        barrier = threading.Barrier(3)  # Hold two scanner owners in one overlap.
        child_done = threading.Event()  # Release scanners after the ownerless write completes.
        results: list[list[str]] = []  # Store both scanner results without assigning an owner.

        def worker() -> None:
            scanner = OutputFileScanner(str(tmp_path))  # Bind one owner from the current worker.
            scanner.snapshot()  # Register before the ownerless child starts.
            barrier.wait(timeout=10)  # Confirm both scanners are active.
            child_done.wait(timeout=10)  # Keep overlap active through the unowned write.
            results.append(scanner.changed_files())  # Timestamp fallback must remain disabled.

        threads = [threading.Thread(target=worker) for _ in range(2)]  # Build two independent owners.
        for thread in threads:  # Activate both scanners.
            thread.start()  # Start one scanner per owner thread.
        barrier.wait(timeout=10)  # Prove the scanner lifetimes overlap.
        child = threading.Thread(  # Use a thread with no active scanner registration.
            target=lambda: (tmp_path / "Ownerless.csv").write_text("foreign", encoding="utf-8")
        )
        child.start()  # Create an ownerless write while both scanners overlap.
        child.join(timeout=10)  # Ensure the file exists before either scanner stops.
        child_done.set()  # Release both scanners after the ownerless evidence exists.
        for thread in threads:  # Wait for both fallback decisions.
            thread.join(timeout=10)  # Bound the test if hook cleanup fails.
        assert results == [[], []]  # Reject ownerless timestamp evidence for both overlapping runs.

    def test_stale_owner_context_cannot_claim_the_surviving_run(self, tmp_path):
        """A late write from a finished run must not enter the sole surviving scanner."""
        first = OutputFileScanner(str(tmp_path), owner_id="first-run")  # Build the run that finishes first.
        second = OutputFileScanner(str(tmp_path), owner_id="second-run")  # Build the surviving run.
        first.snapshot()  # Activate the first owner before the overlap begins.
        second.snapshot()  # Mark both scanners as overlap-sensitive.
        first_token = OutputFileScanner.bind_owner("first-run")  # Attribute the first owned write.
        (tmp_path / "First.csv").write_text("first", encoding="utf-8")  # Track evidence for the first run.
        OutputFileScanner.reset_owner(first_token)  # Restore the test context before collection.
        assert first.changed_files() == ["First.csv"]  # Finish and unregister the first owner.
        stale_token = OutputFileScanner.bind_owner("first-run")  # Simulate late work from the finished run.
        (tmp_path / "FirstLate.csv").write_text("late", encoding="utf-8")  # Try to steal the surviving scanner.
        OutputFileScanner.reset_owner(stale_token)  # Remove the stale context after the write.
        second_token = OutputFileScanner.bind_owner("second-run")  # Attribute the surviving run's real result.
        (tmp_path / "Second.csv").write_text("second", encoding="utf-8")  # Track the surviving owner evidence.
        OutputFileScanner.reset_owner(second_token)  # Restore the test context before collection.
        assert second.changed_files() == ["Second.csv"]  # Reject the stale owner's late file.

    def test_new_run_start_during_fallback_discards_foreign_names(self, tmp_path, monkeypatch):
        """A scanner that starts during a fallback walk must not leak its file into the earlier run."""
        first = OutputFileScanner(str(tmp_path), owner_id="first-run")  # Build the scanner that finishes first.
        first.snapshot()  # Register before the later run exists.
        second: OutputFileScanner | None = None  # Hold the later scanner for cleanup and evidence collection.

        def start_second_during_walk() -> set[str]:
            """Start a second run and return the foreign name that the slow walk observed."""
            nonlocal second  # Publish the new scanner to the outer cleanup path.
            second = OutputFileScanner(str(tmp_path), owner_id="second-run")  # Start after first deregistration.
            second.snapshot()  # Increment the generation while the first fallback is still active.
            token = OutputFileScanner.bind_owner("second-run")  # Attribute the later run's file correctly.
            (tmp_path / "SecondOnly.csv").write_text("second", encoding="utf-8")  # Create foreign fallback evidence.
            OutputFileScanner.reset_owner(token)  # Restore the direct test context.
            return {"SecondOnly.csv"}  # Simulate the first directory walk observing the new file.

        monkeypatch.setattr(first, "_changed_files_by_directory_marks", start_second_during_walk)
        assert first.changed_files() == []  # Discard the foreign name after the generation changes.
        if second is None:  # A missing scanner means the injected race did not execute.
            pytest.fail("the later scanner did not start during the fallback walk")
        assert second._owner_id == "second-run"  # Prove the injected later run owns the scanner.
        assert second.changed_files() == ["SecondOnly.csv"]  # Keep the later run's owned file.


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
        # Measured after issue #3202: two folders. The floor proves that the patterns still find known writers.
        assert len(named) >= 2, f"the guard found only {sorted(named)}, so its patterns no longer match"
        unpruned = {name: module for name, module in named.items() if name not in EXCLUDED_DIR_NAMES}
        assert not unpruned, f"these test output folders are not pruned, so each run pays their walk: {unpruned}"
