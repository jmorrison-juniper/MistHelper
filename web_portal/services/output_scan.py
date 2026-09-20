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
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SCAN_LIMIT = 200  # One run must not flood the result panel with names.
_SKIPPED_SUFFIXES = (".tmp", ".part", ".swp", ".lock")  # A partial write is not a report.
_SKIPPED_PREFIXES = (".", "~")  # A hidden file and an editor backup are not reports.


class OutputFileScanner:
    """Report the data-directory files that one operation created or changed."""

    def __init__(self, data_dir: str | None = None, limit: int = DEFAULT_SCAN_LIMIT) -> None:
        """Resolve the data directory the operation writes into."""
        chosen = data_dir or os.environ.get("DATA_DIR", "data")  # The portal writes every output file here.
        self._root = Path(chosen).resolve()  # An absolute root keeps the relative names stable.
        self._limit = max(1, limit)  # One name must always fit, so a zero cap cannot hide a report.
        self._before: dict[str, float] = {}  # Hold the modification time of each file before the run.

    @property
    def root(self) -> Path:
        """Return the resolved data directory under scan."""
        return self._root

    def snapshot(self) -> None:
        """Record the modification time of every file before the operation runs."""
        logger.info("Output scan records the state of %s", self._root)  # Log before the directory walk.
        self._before = self._read_state()  # Keep the pre-run picture for the later comparison.
        logger.debug("Output scan recorded %d files", len(self._before))  # Log the measured count.

    def changed_files(self) -> list[str]:
        """Return the files that appeared or changed since the snapshot."""
        logger.info("Output scan compares %s against the pre-run state", self._root)  # Log before the walk.
        after = self._read_state()  # Read the directory a second time.
        names = [name for name, stamp in after.items() if self._is_new_or_changed(name, stamp)]
        names.sort()  # A stable order keeps the result panel readable between runs.
        logger.debug("Output scan found %d changed files", len(names))  # Log the measured count.
        return names[: self._limit]  # Cap the list, so one run cannot flood the panel.

    def _is_new_or_changed(self, name: str, stamp: float) -> bool:
        """Report whether one file is absent from the snapshot or newer than it."""
        previous = self._before.get(name)  # A missing entry means the operation created the file.
        return previous is None or stamp > previous

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
        """Yield every file under the root that can hold an operation report."""
        for path in self._root.rglob("*"):
            if path.is_file() and self._is_reportable(path.name):
                yield path

    @staticmethod
    def _is_reportable(name: str) -> bool:
        """Report whether one file name can name an operation output."""
        if name.startswith(_SKIPPED_PREFIXES):  # A hidden file and a backup carry no report.
            return False
        return not name.endswith(_SKIPPED_SUFFIXES)  # A partial write is not a finished report.
