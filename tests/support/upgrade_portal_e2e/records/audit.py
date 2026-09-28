"""Keep the site lock trail of one browser run inside its artifact directory, and replay the trail after the run.

Why:
    Issue #3498 moved the trail of each browser run away from the checkout
    trail. Issue #3508 found two browser tests that left a site lock after the
    test ended, and the run still passed. `TrailHoldCheck` replays the trail of
    the run after the test portal stops. `TrailLine` reads each line strictly,
    and `TrailHoldResult` holds the counts, the measure, and the decision.
    Issue #3512 made the parent read the checkout trail from the root guard.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Issue #3508: read each line of the run trail.
import logging  # Record each move and each count of the trail.
from dataclasses import dataclass  # Issue #3508: describe the result of one replay.
from pathlib import Path  # Issue #3498: name the run trail and the checkout trail.
from typing import Any, ClassVar  # A trail row holds values of mixed types, and each rule text belongs to a class.

import pytest  # Issue #3498: the move uses the public patch object of pytest.

from src.upgrade_portal.compare import lock_audit  # Issue #3508: the expiry rule of the audit log of the portal.
from src.upgrade_portal.runtime import lock  # Issue #3498: the module that writes the site lock trail.
from tests.support.site_lock_trail import CheckoutTrailGuard  # Issue #3512: the root guard names the checkout trail.

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

        Issue #3512. The root conftest moves the trail of each test, and a
        module can start the portal inside its first test. A read of the lock
        module in the parent then names the moved trail of that test. So the
        parent reads the checkout trail from the root guard through
        `for_session`, and each caller names its checkout trail.

    Caution: the production container writes the trail of the main checkout. A
    real lock action during a browser run in the main checkout also changes the
    count, and the guard then fails. Run the browser suite in a worktree.
    """

    REPAIR: ClassVar[str] = (  # The repair that the failure message names.
        " The browser run changed the checkout trail, which is the production audit trail in the main checkout."
        " Call AuditTrailIsolation.place in the test portal before create_app."
        " If a real operator took a site during the run, run the browser suite in a worktree."
    )
    NO_ROOT_GUARD: ClassVar[str] = (  # Issue #3512: the message of a build that has no root guard.
        "The root guard checkout_site_lock_trail_guard gave None, because the lock module cannot import."
        " The browser guard of issue #3498 needs the checkout trail that the root guard reads before the first move."
    )

    def __init__(self, artifact_directory: Path, checkout_trail: Path) -> None:
        """Bind the isolation to one run directory and one checkout trail.

        Args:
            artifact_directory: The directory of this browser run alone.
            checkout_trail: The trail that the production portal writes. The
                parent process reads it from the root guard through
                `for_session`. The child process runs no pytest fixture, so it
                reads the path of the lock module before its move. Issue #3512
                removed the default, because a read after a move names the
                moved trail.
        """
        self.artifact_directory = artifact_directory  # The run owns this directory, and no other run writes it.
        self.checkout_trail = checkout_trail  # Issue #3512: the caller names the trail, so no move can change it.
        self.run_trail = artifact_directory / lock.AUDIT_FILE_NAME  # The trail of this run alone.

    @classmethod
    def for_session(cls, artifact_directory: Path, root_guard: CheckoutTrailGuard | None) -> AuditTrailIsolation:
        """Build the isolation of the parent process from the root guard of the session.

        Why:
            Issue #3512. The root fixture `isolate_site_lock_trail` moves the
            trail of each test. A module that starts the portal inside its
            first test starts the browser guard after that move. The root guard
            read the checkout trail before the first move, so this build reads
            that value, in each order.

        Args:
            artifact_directory: The directory of this browser run alone.
            root_guard: The root guard `checkout_site_lock_trail_guard`. None
                means that the lock module cannot import.

        Returns:
            The isolation that counts the checkout trail.

        Raises:
            RuntimeError: If the root guard is None.
        """
        logger.info("Build the browser trail guard of %s from the root guard", artifact_directory)  # Log first.
        if root_guard is None:  # The root guard skipped, so it holds no checkout trail.
            raise RuntimeError(cls.NO_ROOT_GUARD)  # Never read the lock module here, because a move can apply.
        built = cls(artifact_directory, root_guard.checkout_trail)  # The trail that the root guard read first.
        logger.debug("The browser trail guard counts %s", built.checkout_trail)  # Log after the build.
        return built  # The fixture counts this trail before and after the run.

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


class TrailLine:  # Read one line of the run trail, or fail with its line number.
    """Read one line of the run trail strictly.

    Why:
        Issue #3508. The shipped reader `lock_audit.read_trail_lines` skips a
        damaged line, and that rule suits a page. A guard must fail when it
        cannot read its input, so this reader fails on each line that it cannot
        read. The message names the line number, so the reader of the report
        finds the line.
    """

    KNOWN_ACTIONS: ClassVar[frozenset[str]] = frozenset(  # The four actions that the lock module writes.
        {lock.ACTION_TAKE, lock.ACTION_RELEASE, lock.ACTION_TAKEOVER, lock.ACTION_EXPIRE}
    )

    @classmethod
    def read(cls, trail: Path, number: int, raw: bytes) -> dict[str, Any] | None:
        """Return the record of one line, or no record for a blank line.

        Args:
            trail: The trail that holds the line, which each message names.
            number: The line number, counted from 1.
            raw: The bytes of the line.

        Returns:
            The record, or None when the line is blank.

        Raises:
            AssertionError: The line is not UTF-8 text, is not a JSON object,
                names no site, or names an unknown action.
        """
        where = f"Line {number} of {trail}"  # Each message leads with the place of the fault.
        try:  # The writer writes UTF-8 text, so other bytes mean a damaged line.
            text = raw.decode("utf-8").strip()  # The line text without its line end.
        except UnicodeDecodeError as failure:  # A damaged write or a file of another kind.
            raise AssertionError(f"{where} is not UTF-8 text.") from failure
        if not text:  # A blank line holds no record.
            return None  # The caller skips the line.
        record = cls._parse(where, text)  # A line of another shape fails here.
        cls._require_fields(where, text, record)  # A row with no site or an unknown action fails here.
        return record  # The caller replays the record.

    @staticmethod
    def _parse(where: str, text: str) -> dict[str, Any]:
        """Return the JSON object of one line, or fail with the place of the line."""
        try:  # The parser raises its own error for text that is not JSON.
            record = json.loads(text)  # The writer writes one JSON object on each line.
        except json.JSONDecodeError as failure:  # A partial write or a line of another kind.
            raise AssertionError(f"{where} is not JSON. The line reads: {text!r}") from failure
        if not isinstance(record, dict):  # A list, a number, a string, or null names no site.
            raise AssertionError(f"{where} is not a JSON object. The line reads: {text!r}")
        return record  # The caller checks the fields.

    @classmethod
    def _require_fields(cls, where: str, text: str, record: dict[str, Any]) -> None:
        """Fail when one record names no site or names an unknown action."""
        site = record.get("site_id")  # The site of the action.
        if not isinstance(site, str) or not site.strip():  # A row with no site belongs to no hold.
            raise AssertionError(f"{where} names no site. The line reads: {text!r}")
        action = record.get("action")  # A row from before issue #2221 holds no action.
        if action not in (None, "") and action not in cls.KNOWN_ACTIONS:  # A new action needs a new rule.
            raise AssertionError(f"{where} names the unknown action {action!r}. The line reads: {text!r}")


@dataclass(frozen=True)
class TrailHoldResult:  # The counts and the leaked holds of one replay of the run trail.
    """Hold the counts and the leaked holds of one replay, and make the decision.

    Why:
        Issue #3508. A guard must state what it checked. The measure names the
        trail, the count of records, the count of sites, and the count of
        leaked holds. The fixture stores the measure before the decision, so
        the terminal summary prints it when the check fails.
    """

    trail: Path  # The trail that the check read.
    records: int  # The count of records, with no blank line.
    sites: int  # The count of sites that the records name.
    leaks: tuple[str, ...]  # One sentence for each hold that no release closed.

    REPAIR: ClassVar[str] = (  # The repair that the failure message names.
        " A browser test took a site lock and did not release it."
        " A test that failed before its release step can also leave its lock."
        " Release each lock in the test that took it, or in the teardown of its fixture."
    )

    @property
    def measure(self) -> str:
        """Return one sentence that names what the check read and what it found."""
        return (  # One sentence, so the terminal summary prints one line.
            f"Run trail hold check (issue #3508): read {self.records} record(s) of {self.sites} site(s) "
            f"in {self.trail}. It found {len(self.leaks)} leaked hold(s)."
        )

    def require_no_leak(self) -> None:
        """Fail the run when a hold has no release.

        Raises:
            AssertionError: One or more holds have no release. The message names each hold.
        """
        logger.info("Decide the run trail hold check")  # Log before the decision.
        if not self.leaks:  # Each hold closed with a release.
            logger.debug("The run trail holds no leaked hold")  # Log after the decision.
            return  # The check passes.
        raise AssertionError(self.measure + " " + " ".join(self.leaks) + self.REPAIR)  # Each hold and the repair.


class TrailHoldCheck:  # Replay the site lock trail of one browser run after the test portal stops.
    """Replay the site lock trail of one browser run, and find each hold that no release closed.

    Why:
        Issue #3508. The full browser run of issue #3497 ended with two site
        locks held, and the run still passed. The check reads the trail after
        the portal stops, so no write can follow the read. It uses the shipped
        rule `lock_audit.mark_expiries`, so the check and the audit log of the
        portal agree on each expired hold. It then counts each hold that is
        open at the end of the trail.

    Note: the run trail holds the stand-in addresses of the browser fixtures
    only. The message names the operator, because the address names the fixture
    that took the lock.
    """

    def __init__(self, trail: Path) -> None:
        """Bind the check to one run trail.

        Args:
            trail: The site lock trail of one browser run.
        """
        self.trail = trail  # The run owns this file, and no other run writes it.

    def evaluate(self) -> TrailHoldResult:
        """Read the trail, and return the counts and each leaked hold.

        Returns:
            The result of the replay.

        Raises:
            AssertionError: A line of the trail cannot be read.
            OSError: The trail exists and the check cannot open it.
        """
        logger.info("Replay the site lock trail %s", self.trail)  # Log before the read.
        rows = self._rows()  # Each record of the trail, oldest first.
        leaks = self._leaks(rows)  # One sentence for each hold that no release closed.
        sites = len({str(row["site_id"]) for row in rows})  # Each record names one site.
        logger.debug("The trail holds %s record(s) and %s leaked hold(s)", len(rows), len(leaks))  # Log after.
        return TrailHoldResult(self.trail, len(rows), sites, leaks)  # The fixture stores the measure first.

    def _rows(self) -> list[dict[str, Any]]:
        """Return each record of the trail, oldest first, or no record when no trail exists."""
        if not self.trail.exists():  # A run that took no lock wrote no trail.
            logger.debug("The trail %s does not exist, so it holds 0 records", self.trail)  # Log the absent file.
            return []  # No file means no record.
        rows: list[dict[str, Any]] = []  # The records in the order of the trail.
        with self.trail.open("rb") as handle:  # Bytes, so a damaged line names its own line number.
            for number, raw in enumerate(handle, start=1):  # The line number counts from 1.
                row = TrailLine.read(self.trail, number, raw)  # A bad line fails here.
                if row is not None:  # A blank line holds no record.
                    rows.append(row)  # Keep the order, because each hold closes in order.
        return rows  # The caller replays the records.

    @staticmethod
    def _leaks(rows: list[dict[str, Any]]) -> tuple[str, ...]:
        """Return one sentence for each hold that no release closed."""
        leaks: list[str] = []  # The sentences in the order of the trail.
        open_holds: dict[str, dict[str, Any]] = {}  # The open hold of each site.
        for row in lock_audit.mark_expiries(rows):  # The shipped rule adds one row for each expired hold.
            site = str(row.get("site_id") or "")  # The site of the action.
            if row.get("inferred"):  # A take found an open hold of the same site.
                leaks.append(
                    f"A take of the site {site} at {row.get('occurred_at')} found a lock of "
                    f"{row.get('actor_email')} that no release closed."
                )
            if str(row.get("action") or lock_audit.LEGACY_ACTION) in lock_audit.OPENING_ACTIONS:  # A new hold.
                open_holds[site] = row  # The site now holds an open hold.
            else:  # A release or an expiry closes the hold of the site.
                open_holds.pop(site, None)  # The site is free.
        leaks += [  # Each hold that is open at the end of the trail.
            f"The site {site} still holds a lock that {row.get('actor_email')} took at {row.get('occurred_at')}."
            for site, row in open_holds.items()
        ]
        return tuple(leaks)  # A tuple keeps the result fixed.
