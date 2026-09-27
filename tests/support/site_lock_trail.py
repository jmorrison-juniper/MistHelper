"""Count the checkout site lock trail around one test session. Issue #3503.

Why:
    The unit, contract, and integration tests of the upgrade portal wrote each
    site lock action to `data/upgrade_takeover_audit.jsonl` in the checkout. In
    the main checkout, that file is the production audit trail. The root
    conftest now moves the trail of each test into the temporary directory of
    that test, and this class proves that the checkout trail kept its records.

    The module imports the standard library only. The root conftest loads it
    for each test session, and the lock module pulls in the web framework of
    the portal. The fixtures import the lock module late, so the environment
    guard of the root conftest runs first.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record each count and each decision of the guard.
from pathlib import Path  # Name the checkout trail.
from typing import ClassVar  # The folder name and the repair text belong to the class.

logger = logging.getLogger(__name__)  # Keep the guard records tied to this module.


class CheckoutTrailGuard:  # Prove that no test of one session wrote to the checkout trail.
    """Count the checkout site lock trail before the first test and after the last test.

    Why:
        Issue #3503. The move of the root conftest keeps each lock action of a
        test inside the temporary directory of that test. A write that escapes
        the move reaches the checkout trail. This guard counts the lines of
        that trail at the start and at the end of the session, so an escaped
        write fails the run.

    Caution: the production container writes the trail of the main checkout. A
    real lock action during a test session in the main checkout also changes
    the count, and the guard then fails. Run the tests in a worktree.
    """

    DIRECTORY_NAME: ClassVar[str] = "site-lock-trail"  # The trail folder inside the temporary directory of a test.
    REPAIR: ClassVar[str] = (  # The repair that the failure message names.
        " A test changed the checkout trail, which is the production audit trail in the main checkout."
        " The fixture isolate_site_lock_trail in tests/conftest.py moves the trail of each test."
        " A fixture with module scope or session scope runs before that move."
        " A thread that outlives its test writes after the move ends."
        " Move each such lock action into the body of a test."
        " If a real operator took a site during the session, the production container wrote the line."
        " In that case, run the tests in a worktree."
    )

    def __init__(self, checkout_trail: Path) -> None:
        """Bind the guard to one checkout trail.

        Args:
            checkout_trail: The trail that the production portal writes. The
                root conftest reads it from the lock module before the first
                move of the session.
        """
        self.checkout_trail = checkout_trail  # The trail that must keep its line count.

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
            before: The line count of the checkout trail before the first test.
            after: The line count of the checkout trail after the last test.

        Returns:
            The sentence that names the checked trail and the two counts.
        """
        return (  # One sentence, so the terminal summary prints one line.
            f"Checkout site lock trail guard (issue #3503): checked 1 trail, {self.checkout_trail}. "
            f"It held {before} line(s) before the first test and {after} line(s) after the last test."
        )

    @staticmethod
    def skip_measure(fault: ImportError) -> str:
        """State why the guard did not run, in one sentence for the run report.

        Why:
            A guard that skips for a reason in the environment must print the
            reason and name the missing capability. If the lock module cannot
            import, no test can write a site lock action, so the skip is safe.

        Args:
            fault: The error that the import of the lock module raised.

        Returns:
            The sentence that names the error and the missing capability.
        """
        return (  # One sentence, so the terminal summary prints one line.
            "Checkout site lock trail guard (issue #3503): skipped, because the lock module cannot import "
            f"({type(fault).__name__}: {fault}). "
            "Without that module, no test can write a site lock action."
        )

    def require_unchanged(self, before: int, after: int) -> None:
        """Fail the run when the checkout trail changed.

        Args:
            before: The line count of the checkout trail before the first test.
            after: The line count of the checkout trail after the last test.

        Raises:
            AssertionError: If the two counts differ.
        """
        logger.info("Compare the checkout trail counts %s and %s", before, after)  # Log before the decision.
        if after == before:  # No test wrote a record to the checkout trail.
            logger.debug("The checkout trail kept its %s record(s)", before)  # Log after the decision.
            return  # The guard passes.
        raise AssertionError(self.measure(before, after) + self.REPAIR)  # The path, the counts, and the repair.
