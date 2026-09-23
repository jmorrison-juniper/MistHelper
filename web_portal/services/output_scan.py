"""Find the files an operation wrote, without reading the log prose.

Why:
    The portal used to learn an output file name only from a log sentence. It
    matched three phrases and four extensions, so an operation that wrote a
    Markdown report and logged ``Mermaid report:`` reported no file at all. The
    engineer then read an empty result panel and believed the run produced
    nothing. Issue #3089 records that loss.

Method:
    This scanner reads the data directory instead. It records the modification
    time of every file before the run, then lists the files that changed or
    appeared while the operation ran. A file name therefore needs no log
    sentence to reach the portal.

Limit:
    Two operations that run at the same time share one data directory, so each
    run can report a file the other run wrote. The portal shows a superset
    rather than an empty list, because a missing report costs an engineer more
    than an extra name.

    The scanner does skip the runtime bookkeeping files that every run touches.
    Issue #3126 records the noise they created. A file that a log line names
    explicitly still reaches the panel, because the executor merges the scanned
    names into the names the log already produced.
"""

from __future__ import annotations

import builtins
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SCAN_LIMIT = 200  # One run must not flood the result panel with names.
_SKIPPED_SUFFIXES = (".tmp", ".part", ".swp", ".lock")  # A partial write is not a report.
_SKIPPED_PREFIXES = (".", "~")  # A hidden file and an editor backup are not reports.

# Issue #3140: the run-start mark dates each file the later walk finds. The
# comparison is exact, because a file an operation writes carries a
# modification time after the run started.
#
# Issue #3172: the mark used to come from the wall clock, and a file carries a
# time from the filesystem clock. The two do not agree. Measured on Windows, a
# report written right after the mark carried a time up to 194500 nanoseconds
# before it, so a strict comparison dropped the file the operation had just
# written. The scanner now takes the mark from a probe file, so one clock dates
# the mark and every report. See snapshot() for the measurement.
#
# This value only widens the window when the wall-clock fallback runs, which
# happens when the root cannot hold a probe file.
#
# Warning: a filesystem that truncates the modification time to a whole second
# could place a write before the mark and hide that report. If this scanner ever
# runs on such a mount, raise this value to the granularity of that mount rather
# than widening the window for everyone. A wider window reports a file the run
# never wrote, which the tests forbid.
_MTIME_GRANULARITY_NANOSECONDS = 0

# Issue #3140: the scanner walked every entry under the data root, and one
# operator tree held 11330 corpus PDF files across 19.7 GB. One walk with a stat
# call took 341 seconds on that mount, and the portal runs two walks for each
# operation, so every run paid about 11 minutes whatever work it did.
#
# No operation writes a report into one of these trees, so the walk skips them
# whole rather than visiting each file. Pruning needs `os.walk`, because
# `Path.rglob` offers no way to refuse a subdirectory before it descends.
#
# Warning: add a name here only when no operation writes a report into it. A
# pruned tree can never reach the result panel.
EXCLUDED_DIR_NAMES = (
    "juniper_pdf_library",  # The harvested Juniper document corpus. Read-only reference material.
    "mist_ideas_cache",  # The scraped idea cache. src/ideas writes it outside a portal run.
    "portal-test-artifacts",  # The end-to-end test reports. A test run is not an operation output.
    # Issue #3201: the upgrade portal suites write their artifacts here, and the
    # tree reached 1,522 mostly empty directories. Each listing is a round trip
    # over the bind mount, so the walk of this tree alone cost 67 seconds, and
    # every operation paid that cost. Measured in the container on 2026-09-23:
    # the whole scan fell from 56.0 seconds to 3.0 seconds with this prune.
    "test-artifacts",  # The upgrade portal test artifacts. A test run is not an operation output.
    "test-control-byte-guard",  # The markdown control-byte test workspace. A test run is not an operation output.
    "agent_logs",  # The agent telemetry directory that copilot-instructions.md names.
    "__pycache__",  # Compiled bytecode is never a report.
    ".git",  # Repository metadata is never a report.
)

# An operator can extend the prune list without a code change, because a site
# can hold a large tree that this repository cannot know about.
_EXTRA_EXCLUDES_ENV = "PORTAL_SCAN_EXCLUDE_DIRS"

# Issue #3126: the runtime writes these files on every run, and no operation
# means one as its output. The scanner would otherwise list four names for a
# run that produced one report, so the engineer must pick the report out of a
# list that changes each time.
#
# Warning: each name below must match the writer that owns it. The guard test
# `tests/unit/web_portal/test_output_scan_runtime_files.py` reads the owning
# constant and fails when a rename leaves a stale entry here.
RUNTIME_FILE_NAMES = (
    "script.log",  # The application log. src/refactors/main_entrypoint.py opens it.
    "portal_access.log",  # The Gunicorn access log. container/scripts/start.sh names it.
    "delay_metrics.json",  # The rate-limiter metric store. src/utils/rate_limiting._METRICS_FILENAME.
    "tuning_data.json",  # The rate-limiter tuning store. src/utils/rate_limiting._TUNING_FILENAME.
)


class OutputFileScanner:
    """Report the data-directory files that one operation created or changed."""

    _tracking_lock = threading.RLock()  # Guard hook installation and each scanner's candidate set.
    _active_scanners: list[OutputFileScanner] = []  # Track runs that are between snapshot() and changed_files().
    _original_open = builtins.open  # Save the process default before the scanner installs a write hook.
    _original_path_open = Path.open  # Save pathlib writes, because many exporters use Path helpers.
    _hooks_installed = False  # Record whether the process-wide hooks are active.

    def __init__(self, data_dir: str | None = None, limit: int = DEFAULT_SCAN_LIMIT) -> None:
        """Resolve the data directory the operation writes into."""
        chosen = data_dir or os.environ.get("DATA_DIR", "data")  # The portal writes every output file here.
        self._root = Path(chosen).resolve()  # An absolute root keeps the relative names stable.
        self._limit = max(1, limit)  # One name must always fit, so a zero cap cannot hide a report.
        self._before: dict[str, float] = {}  # Kept for callers that read the pre-run picture.
        self._directory_marks: dict[str, int] = {}  # Store directory mtimes for the untracked-writer fallback.
        self._directory_entries: dict[str, set[str]] = {}  # Store reportable names without paying file stats.
        self._write_candidates: set[Path] = set()  # Store paths opened for writing while this run executes.
        self._started_at: float = 0.0  # The run-start mark that dates each file found later.
        self._excluded = self._resolve_excludes()  # Name the trees the walk refuses to enter.
        # Issue #3201: the cost of a walk is the count of directories it lists,
        # not the count of files it finds. The count stays readable after each
        # walk, so a test can prove that a pruned tree was never entered.
        self.last_walk_directories = 0  # The directories the most recent walk listed.
        self.last_scanned_files = 0  # The files the most recent change check statted.

    @staticmethod
    def _resolve_excludes() -> frozenset[str]:
        """Return the directory names the walk skips, including operator additions."""
        names = set(EXCLUDED_DIR_NAMES)  # Start from the trees this repository knows are large.
        raw = os.environ.get(_EXTRA_EXCLUDES_ENV, "")  # Read the operator list, which may be absent.
        for entry in raw.split(os.pathsep):  # The separator matches the platform path convention.
            cleaned = entry.strip()  # A stray space must not create an unmatchable name.
            if cleaned:  # An empty field would prune nothing and cost a comparison.
                names.add(cleaned)
        return frozenset(names)  # A frozen set states that the list cannot change mid-run.

    @property
    def root(self) -> Path:
        """Return the resolved data directory under scan."""
        return self._root

    def snapshot(self) -> None:
        """Record the moment the run began, so a later walk can date each file.

        Issue #3140: this method used to walk the whole tree and stat every
        entry. That walk cost 32 seconds on the reporting mount even after the
        prune, and the portal pays it twice for each operation. A timestamp
        costs nothing and answers the same question, because a report the
        operation wrote carries a modification time after the run started.

        Issue #3172: the mark came from the wall clock, and a file carries a
        time from the filesystem clock. The two disagree. A report written
        right after the mark could carry a time up to 0.19 milliseconds before
        it, so the scanner dropped the file the operation had just written.

        The mark now comes from a probe file, so one clock dates the mark and
        every report. Measured over 1500 attempts of each case:

            wall clock, strict >   lost 118   reported in error 0
            wall clock, >=         lost  36   reported in error 0
            probe file, strict >   lost   0   reported in error 0
            probe file, >=         lost   0   reported in error 14
        """
        logger.info("Output scan marks the run start for %s", self._root)  # Log before the mark.
        self._started_at = self._mark_from_probe_file()  # Use the filesystem clock for later file comparisons.
        self._directory_marks, self._directory_entries = self._read_directory_snapshot()  # Snapshot folders only.
        self._start_write_tracking()  # Track file writes so in-place rewrites do not need a full folder stat.
        logger.debug("Output scan start mark: %d ns", self._started_at)  # State the recorded value.

    def _mark_from_probe_file(self) -> int:
        """Return a run-start mark taken from the filesystem clock.

        The probe carries the process id, so two runs against one root never
        pick the same name.
        """
        probe = self._root / f".portal-scan-mark-{os.getpid()}"  # A unique name per process.
        try:
            probe.write_bytes(b"")  # Create the probe, so the filesystem dates it.
            stamp = probe.stat().st_mtime_ns  # Read the mark in the clock that dates every report.
            return stamp
        except OSError as error:
            # A missing or read-only root cannot hold a probe. The wall clock
            # is the weaker mark, so name the reason an operator may see a
            # report go missing.
            logger.warning("Output scan could not write a probe in %s: %s. Using the wall clock.", self._root, error)
            return time.time_ns() - _MTIME_GRANULARITY_NANOSECONDS
        finally:
            try:
                probe.unlink()  # Remove the probe, so it never reaches the result panel.
            except OSError:
                pass  # A probe that never existed cannot be removed, and that is not an error.

    def changed_files(self) -> list[str]:
        """Return the files that appeared or changed since the run began."""
        logger.info("Output scan reads %s for files the run wrote", self._root)  # Log before the walk.
        self._stop_write_tracking()  # Stop recording before this method opens no report files.
        self.last_scanned_files = 0  # Reset the stat count so tests can prove the scan scope.
        found = self._changed_tracked_files()  # First read only files that Python opened for writing.
        found.update(self._changed_files_by_directory_marks())  # Add files from untracked directory changes.
        names = list(found)  # Convert to a list because the result panel expects ordered names.
        names.sort()  # A stable order keeps the result panel readable between runs.
        logger.debug("Output scan found %d changed files", len(names))  # Log the measured count.
        return names[: self._limit]  # Cap the list, so one run cannot flood the panel.

    def _changed_tracked_files(self) -> set[str]:
        """Return changed files from the write tracker."""
        changed: set[str] = set()  # Use a set because one file can be opened more than once.
        with self._tracking_lock:  # Copy under lock so another run cannot mutate the set during iteration.
            candidates = tuple(self._write_candidates)  # Freeze the candidate list for this check.
        for path in candidates:  # Check only files that were opened for writing during this run.
            name = self._changed_reportable_path(path)  # Return a relative name only when the timestamp qualifies.
            if name is not None:  # A qualifying name is an operation output candidate.
                changed.add(name)  # Add the name without a duplicate.
        return changed  # Return the tracked result names.

    def _changed_files_by_directory_marks(self) -> set[str]:
        """Return changed files from directories whose own mtime changed."""
        changed: set[str] = set()  # Collect fallback names without duplicates.
        current_marks, current_entries = self._read_directory_snapshot()  # Restat directories and list names only.
        for relative_name, stamp in current_marks.items():  # Compare each current directory with the snapshot mark.
            previous = self._directory_marks.get(relative_name)  # A missing mark means the directory is new.
            if previous is None or stamp > previous:  # A changed directory can hold an untracked new file.
                directory = self._root if relative_name == "." else self._root / relative_name  # Resolve the scope.
                old_names = self._directory_entries.get(relative_name, set())  # Names seen before the run.
                new_names = current_entries.get(relative_name, set()) - old_names  # Only new names need a stat.
                changed.update(self._changed_files_in_directory(directory, new_names))  # Add qualifying files.
        return changed  # Return the fallback result names.

    def _changed_files_in_directory(self, directory: Path, names: set[str]) -> set[str]:
        """Return changed reportable files in one directory."""
        changed: set[str] = set()  # Collect names from this fallback directory.
        for filename in names:  # Read only files that appeared after the snapshot.
            path = directory / filename  # Build the absolute path for timestamp validation.
            name = self._changed_reportable_path(path)  # Check timestamp and runtime-file filters.
            if name is not None:  # A qualifying file belongs in the result panel.
                changed.add(name)  # Add the relative name.
        return changed  # Return all changed files found in this directory.

    def _changed_reportable_path(self, path: Path) -> str | None:
        """Return a relative name when path is a changed reportable file."""
        try:
            if not path.is_file():  # A vanished path or directory is not an output file.
                return None
            if not self._is_reportable(path.name):  # Runtime files and partial writes do not reach the panel.
                return None
            self.last_scanned_files += 1  # Count each file stat the optimized scan still pays.
            stamp = path.stat().st_mtime_ns  # Read the file clock that the snapshot probe also used.
            if stamp <= self._started_at:  # A strict comparison excludes files the run did not touch.
                return None
            return path.relative_to(self._root).as_posix()  # Use portal-stable POSIX names.
        except OSError as error:  # A file can vanish between tracking and stat.
            logger.debug("Output scan skipped %s: %s", path, error)  # Record the skip for diagnostics.
            return None

    def _read_directory_snapshot(self) -> tuple[dict[str, int], dict[str, set[str]]]:
        """Return directory modification times and reportable names."""
        marks: dict[str, int] = {}  # Map each relative directory name to its mtime.
        entries: dict[str, set[str]] = {}  # Map each relative directory to reportable file names.
        if not self._root.is_dir():  # A missing root cannot hold output files.
            logging.warning("Output scan found no directory at %s", self._root)  # Name the missing path.
            return marks, entries
        visited_dirs = 0  # Count the directories the walk listed.
        for current, dirnames, filenames in os.walk(self._root):  # Walk allows in-place pruning.
            dirnames[:] = [name for name in dirnames if name not in self._excluded]  # Refuse costly subtrees.
            visited_dirs += 1  # Count this directory listing.
            directory = Path(current)  # Convert the current directory once for path operations.
            try:
                name = "." if directory == self._root else directory.relative_to(self._root).as_posix()  # Key it.
                marks[name] = directory.stat().st_mtime_ns  # Record the directory timestamp for fallback scans.
                entries[name] = {filename for filename in filenames if self._is_reportable(filename)}  # List names.
            except OSError as error:  # A directory can vanish during the walk.
                logger.debug("Output scan skipped directory %s: %s", directory, error)  # Keep diagnostic context.
        self.last_walk_directories = visited_dirs  # Publish the measured directory scope.
        logger.debug("Output scan entered %d directories", visited_dirs)  # State the measured scope.
        return marks, entries  # Return the directory snapshot.

    def _start_write_tracking(self) -> None:
        """Register this scanner for process-wide Python file write tracking."""
        with self._tracking_lock:  # Serialize hook installation with any concurrent run.
            self._write_candidates.clear()  # Remove stale paths if a caller reuses this scanner.
            if self not in self._active_scanners:  # Avoid duplicate records for one scanner.
                self._active_scanners.append(self)  # Activate this scanner for future writable opens.
            self._install_hooks_locked()  # Ensure writes go through the tracking wrappers.

    def _stop_write_tracking(self) -> None:
        """Unregister this scanner and remove hooks when no scan is active."""
        with self._tracking_lock:  # Serialize hook removal with concurrent open calls.
            if self in self._active_scanners:  # The scanner can be stopped more than once safely.
                self._active_scanners.remove(self)  # Stop recording candidates for this run.
            if not self._active_scanners:  # The process needs no hook when no run is active.
                self._remove_hooks_locked()  # Restore the original file open functions.

    @classmethod
    def _install_hooks_locked(cls) -> None:
        """Install process-wide file open hooks while the caller holds the lock."""
        if cls._hooks_installed:  # A prior active scanner already installed the hooks.
            return
        cls._original_open = builtins.open  # Save the current function so removal restores it exactly.
        cls._original_path_open = Path.open  # Save pathlib's current open method for restoration.
        builtins.open = cls._tracked_open  # type: ignore[assignment]
        Path.open = cls._tracked_path_open  # type: ignore[method-assign]
        cls._hooks_installed = True  # Mark the process as hooked.
        logger.debug("Output scan write tracking hooks installed")  # State that tracking is active.

    @classmethod
    def _remove_hooks_locked(cls) -> None:
        """Remove process-wide file open hooks while the caller holds the lock."""
        if not cls._hooks_installed:  # Nothing is installed, so removal has no work.
            return
        builtins.open = cls._original_open  # type: ignore[assignment]
        Path.open = cls._original_path_open  # type: ignore[method-assign]
        cls._hooks_installed = False  # Mark the process as restored.
        logger.debug("Output scan write tracking hooks removed")  # State that tracking is inactive.

    @staticmethod
    def _tracked_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any):
        """Open a file through builtins.open and record writable paths."""
        handle = OutputFileScanner._original_open(file, mode, *args, **kwargs)  # Preserve normal open behavior.
        OutputFileScanner._record_write_candidate(file, mode)  # Record only after open succeeds.
        return handle  # Return the real file object to the caller.

    @staticmethod
    def _tracked_path_open(
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ):
        """Open a file through Path.open and record writable paths."""
        handle = OutputFileScanner._original_path_open(path, mode, buffering, encoding, errors, newline)
        OutputFileScanner._record_write_candidate(path, mode)  # Record only after open succeeds.
        return handle  # Return the real file object to the caller.

    @classmethod
    def _record_write_candidate(cls, file: Any, mode: str) -> None:
        """Record file when mode can modify it and it lives under an active root."""
        if not cls._mode_can_write(mode):  # Read-only opens cannot create or update a report.
            return
        try:
            resolved = cls._resolve_candidate_path(file)  # Convert strings and Path objects to an absolute path.
        except TypeError:
            return  # File descriptors and unsupported objects have no path to report.
        with cls._tracking_lock:  # Protect active scanner iteration and candidate mutation.
            for scanner in cls._active_scanners:  # A concurrent run can report a superset, as before.
                if scanner._path_is_reportable_candidate(resolved):  # Record only paths this scanner may report.
                    scanner._write_candidates.add(resolved)  # Add the path without duplicates.

    @staticmethod
    def _mode_can_write(mode: str) -> bool:
        """Return true when an open mode can modify file content."""
        return any(flag in mode for flag in ("w", "a", "x", "+"))  # These modes can create or update a file.

    @staticmethod
    def _resolve_candidate_path(file: Any) -> Path:
        """Return an absolute path for a file-open argument."""
        if not isinstance(file, str | os.PathLike):  # File descriptors do not identify a report path.
            raise TypeError("file has no filesystem path")
        path = Path(file)  # Normalize strings and Path-like objects to a Path.
        absolute = path if path.is_absolute() else Path.cwd() / path  # Match how open resolves relative paths.
        return absolute.resolve(strict=False)  # Resolve parents without requiring the file to still exist.

    @staticmethod
    def _path_is_under_root(path: Path, root: Path) -> bool:
        """Return true when path is inside root."""
        try:
            path.relative_to(root)  # A relative path exists only when root contains path.
            return True  # The candidate belongs to this scanner.
        except ValueError:
            return False  # The file belongs to another directory.

    def _path_is_reportable_candidate(self, path: Path) -> bool:
        """Return true when path is under root and outside excluded trees."""
        try:
            relative = path.relative_to(self._root)  # Convert to root-relative parts for prune checks.
        except ValueError:
            return False  # A path outside the data root cannot be this run's output.
        return not any(part in self._excluded for part in relative.parts[:-1])  # Honor every pruned directory.

    def _read_state(self) -> dict[str, int]:
        """Return the modification time of every readable file under the root."""
        state: dict[str, int] = {}
        if not self._root.is_dir():  # A missing directory is not an error, because the run may still start.
            logging.warning("Output scan found no directory at %s", self._root)  # Name the missing path.
            return state
        for path in self._walk():
            try:
                # Read integer nanoseconds. A float rounds two close instants
                # to one value and hides a report. Issue #3172.
                state[path.relative_to(self._root).as_posix()] = path.stat().st_mtime_ns
            except OSError as error:  # A file can vanish between the walk and the stat call.
                logger.debug("Output scan skipped %s: %s", path, error)  # Record the skip for a reader.
        return state

    def _walk(self):
        """Yield every file under the root that can hold an operation report.

        The walk prunes each excluded tree in place, so it never descends into a
        large read-only corpus. `os.walk` allows that refusal. `Path.rglob` does
        not, and issue #3140 measured the cost of visiting every entry.
        """
        visited_dirs = 0  # Count the directories the walk entered, so the log can prove the scope.
        for current, dirnames, filenames in os.walk(self._root):
            # Editing dirnames in place tells os.walk which subtrees to skip.
            dirnames[:] = [name for name in dirnames if name not in self._excluded]
            visited_dirs += 1
            for name in filenames:
                if self._is_reportable(name):  # Skip a partial write, a hidden file, and bookkeeping.
                    yield Path(current) / name
        self.last_walk_directories = visited_dirs  # Publish the measured scope for a caller or a test.
        logger.debug("Output scan entered %d directories", visited_dirs)  # State the measured scope.

    @staticmethod
    def _is_reportable(name: str) -> bool:
        """Report whether one file name can name an operation output."""
        if name.startswith(_SKIPPED_PREFIXES):  # A hidden file and a backup carry no report.
            return False
        if name.endswith(_SKIPPED_SUFFIXES):  # A partial write is not a finished report.
            return False
        return not OutputFileScanner._is_runtime_file(name)  # Runtime bookkeeping is not an operation output.

    @staticmethod
    def _is_runtime_file(name: str) -> bool:
        """Report whether one name belongs to the runtime rather than to an operation."""
        for runtime_name in RUNTIME_FILE_NAMES:
            if name == runtime_name:  # The plain name matches a runtime writer.
                return True
            if name.startswith(runtime_name + "."):  # A rotated log carries a numeric suffix.
                return True
        return False
