"""Keep the site lock trail of one browser run inside the artifact directory of that run."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each move and each count of the trail.
from pathlib import Path  # Issue #3498: name the run trail and the checkout trail.
from typing import ClassVar  # The repair text belongs to the class.

import pytest  # Issue #3498: the move uses the public patch object of pytest.

from src.upgrade_portal.runtime import lock  # Issue #3498: the module that writes the site lock trail.

logger = logging.getLogger(__name__)  # Keep the trail records tied to this module.


class AuditTrailIsolation:  # Keep the site lock trail of one browser run away from the checkout trail.
    """Move the site lock trail of one browser run, and prove that the checkout trail kept its records.

    Why:
        Issue #3498. The lock module wrote each lock action of the test portal
        to `data/upgrade_takeover_audit.jsonl` in the checkout. In the main
        checkout, that file is the production audit trail, and the production
        container mounts it. The child process moves the trail into the
        artifact directory of its run. The parent process counts the checkout
        trail before and after the run, so a write that escapes the move fails
        the run.

    Caution: the production container writes the trail of the main checkout. A
    real lock action during a browser run in the main checkout also changes the
    count, and the guard then fails. Run the browser suite in a worktree.
    """

    REPAIR: ClassVar[str] = (  # The repair that the failure message names.
        " The browser run changed the checkout trail, which is the production audit trail in the main checkout."
        " Call AuditTrailIsolation.place in the test portal before create_app."
        " If a real operator took a site during the run, run the browser suite in a worktree."
    )

    def __init__(self, artifact_directory: Path, checkout_trail: Path | None = None) -> None:
        """Bind the isolation to one run directory and one checkout trail.

        Args:
            artifact_directory: The directory of this browser run alone.
            checkout_trail: The trail that the production portal writes. No
                value reads the path that the lock module reports now, so a
                caller builds the isolation before a move.
        """
        self.artifact_directory = artifact_directory  # The run owns this directory, and no other run writes it.
        self.checkout_trail = checkout_trail or lock.audit_trail_path()  # The default path of the lock module.
        self.run_trail = artifact_directory / lock.AUDIT_FILE_NAME  # The trail of this run alone.

    def place(self, patcher: pytest.MonkeyPatch | None = None) -> Path:
        """Point the site lock trail of this process at the run directory.

        Why:
            The lock module reads `AUDIT_DIRECTORY` at call time, and it keeps
            an absolute directory as written. One change therefore moves the
            writer and the reader together. The check after the change stops
            the test portal when a later lock module ignores the directory.

        Args:
            patcher: The patch object that owns the change. A unit test passes
                its `monkeypatch` fixture, which restores the directory. No
                value keeps the change for the whole life of the process.

        Returns:
            The path that the lock module now reports.

        Raises:
            ValueError: If the run trail is the checkout trail.
            RuntimeError: If the lock module reports another path after the change.
        """
        logger.info("Move the site lock trail of this process to %s", self.run_trail)  # Log before the move.
        target = self.run_trail.resolve()  # The absolute path that the lock module must report.
        if target == self.checkout_trail.resolve():  # A move to the same file protects nothing.
            raise ValueError(f"The run trail {self.run_trail} is the checkout trail, so the move protects nothing.")
        active = patcher or pytest.MonkeyPatch()  # The child never undoes the move, so no fixture owns it.
        active.setattr(lock, "AUDIT_DIRECTORY", str(target.parent))  # An absolute directory stands as written.
        placed = lock.audit_trail_path()  # The path of every later lock write and every audit read.
        if placed != target:  # A lock module that cached its path ignores the new directory.
            raise RuntimeError(f"The lock module reports {placed} after the move, not {target}.")
        logger.debug("The site lock trail of this process is now %s", placed)  # Log after the move.
        return placed  # The caller may log or compare the path.

    @staticmethod
    def count_lines(trail: Path) -> int:
        """Count the records of one trail.

        Why:
            The trail holds one JSON record on each line. A fresh checkout
            holds no trail, so an absent file counts 0. Any other read fault
            raises, because a guard that cannot read its input must fail.

        Args:
            trail: The trail to count.

        Returns:
            The count of lines.

        Raises:
            OSError: If the trail exists and the guard cannot read it.
        """
        logger.info("Count the records of the trail %s", trail)  # Log before the read.
        if not trail.exists():  # A fresh checkout holds no trail yet.
            logger.debug("The trail %s does not exist, so it holds 0 records", trail)  # Log after the check.
            return 0  # No file means no record.
        with trail.open("rb") as handle:  # Bytes, so a damaged record still counts as one line.
            count = sum(1 for _line in handle)  # One record on each line.
        logger.debug("The trail %s holds %s record(s)", trail, count)  # Log after the read.
        return count  # The guard compares this number.

    def measure(self, before: int, after: int) -> str:
        """State what the guard checked, in one sentence for the run report.

        Args:
            before: The line count of the checkout trail before the run.
            after: The line count of the checkout trail after the run.

        Returns:
            The sentence that names the checked trail, the two counts, and the
            line count of the run trail.
        """
        run_lines = self.count_lines(self.run_trail)  # The records that the test portal wrote to its own trail.
        return (  # One sentence, so the terminal summary prints one line.
            f"Checkout audit trail guard (issue #3498): checked 1 trail, {self.checkout_trail}. "
            f"It held {before} line(s) before the browser run and {after} line(s) after the run. "
            f"The trail of this run holds {run_lines} line(s), at {self.run_trail}."
        )

    def require_unchanged(self, before: int, after: int) -> None:
        """Fail the run when the checkout trail changed.

        Args:
            before: The line count of the checkout trail before the run.
            after: The line count of the checkout trail after the run.

        Raises:
            AssertionError: If the two counts differ.
        """
        logger.info("Compare the checkout trail counts %s and %s", before, after)  # Log before the decision.
        if after == before:  # The run wrote no record to the checkout trail.
            logger.debug("The checkout trail kept its %s record(s)", before)  # Log after the decision.
            return  # The guard passes.
        raise AssertionError(self.measure(before, after) + self.REPAIR)  # The path, the counts, and the repair.
