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

import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SCAN_LIMIT = 200  # One run must not flood the result panel with names.
_SKIPPED_SUFFIXES = (".tmp", ".part", ".swp", ".lock")  # A partial write is not a report.
_SKIPPED_PREFIXES = (".", "~")  # A hidden file and an editor backup are not reports.

# Some filesystems record a modification time with one second of granularity, so
# the run-start mark steps back by this much. A wider window can name one extra
# file. A narrower window could lose a report, which costs an engineer more.
_MTIME_GRANULARITY_SECONDS = 1.0

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

    def __init__(self, data_dir: str | None = None, limit: int = DEFAULT_SCAN_LIMIT) -> None:
        """Resolve the data directory the operation writes into."""
        chosen = data_dir or os.environ.get("DATA_DIR", "data")  # The portal writes every output file here.
        self._root = Path(chosen).resolve()  # An absolute root keeps the relative names stable.
        self._limit = max(1, limit)  # One name must always fit, so a zero cap cannot hide a report.
        self._before: dict[str, float] = {}  # Kept for callers that read the pre-run picture.
        self._started_at: float = 0.0  # The run-start mark that dates each file found later.
        self._excluded = self._resolve_excludes()  # Name the trees the walk refuses to enter.

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

        The mark steps back one second, because some filesystems record a
        modification time with one second of granularity. A file written in the
        same second as the start would otherwise miss the comparison. The module
        already prefers a superset over an empty list, so the wider window
        matches the stated behavior.
        """
        self._started_at = time.time() - _MTIME_GRANULARITY_SECONDS
        logger.info("Output scan marks the run start for %s", self._root)  # Log before the run.
        logger.debug("Output scan start mark: %.3f", self._started_at)  # State the recorded value.

    def changed_files(self) -> list[str]:
        """Return the files that appeared or changed since the run began."""
        logger.info("Output scan reads %s for files the run wrote", self._root)  # Log before the walk.
        names = [name for name, stamp in self._read_state().items() if stamp >= self._started_at]
        names.sort()  # A stable order keeps the result panel readable between runs.
        logger.debug("Output scan found %d changed files", len(names))  # Log the measured count.
        return names[: self._limit]  # Cap the list, so one run cannot flood the panel.

    def _read_state(self) -> dict[str, float]:
        """Return the modification time of every readable file under the root."""
        state: dict[str, float] = {}
        if not self._root.is_dir():  # A missing directory is not an error, because the run may still start.
            logging.warning("Output scan found no directory at %s", self._root)  # Name the missing path.
            return state
        for path in self._walk():
            try:
                state[path.relative_to(self._root).as_posix()] = path.stat().st_mtime
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
