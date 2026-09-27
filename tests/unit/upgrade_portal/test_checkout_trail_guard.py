"""Test the site lock trail move and the checkout trail guard of the root conftest. Issue #3503.

Why:
    The unit, contract, and integration tests of the upgrade portal wrote each
    site lock action to the checkout trail. In the main checkout, that file is
    the production audit trail. One run of those suites wrote 150 lines to the
    trail of a fresh worktree, and no gate reported the leak.

    The root conftest now moves the trail of each test into the temporary
    directory of that test. A session guard counts the checkout trail before the
    first test and after the last test. These tests prove the move, the count,
    the guard decision, and the skip text with no network and no production
    file.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.upgrade_portal.runtime import lock
from tests.support.site_lock_trail import CheckoutTrailGuard

logger = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.

ORG_ID = "35033503-3503-3503-3503-350335033503"  # The stand-in organization of issue #3503.
SITE_ID = "35033503-3503-3503-3503-3503350335aa"  # The stand-in site of issue #3503.
OPERATOR_EMAIL = "unit.operator@example.invalid"  # A reserved address that reaches no mail host.
TRAIL_RECORD = '{"action": "take"}\n'  # One record of the append-only trail.
CHECKOUT_ROOT = Path(__file__).resolve().parents[3]  # This file sits at the same depth as the lock module.


@pytest.fixture(name="guard")
def fixture_guard(tmp_path: Path) -> CheckoutTrailGuard:
    """Build one guard whose checkout trail is a stand-in inside `tmp_path`.

    Args:
        tmp_path: The directory of this test alone.

    Returns:
        The guard of a stand-in checkout.
    """
    logger.info("Build a guard inside %s", tmp_path)  # Report before the build.
    built = CheckoutTrailGuard(tmp_path / "checkout" / "data" / lock.AUDIT_FILE_NAME)  # The stand-in trail.
    logger.debug("Built a guard for the stand-in trail %s", built.checkout_trail)  # Report after the build.
    return built


def write_records(trail: Path, count: int) -> None:
    """Append records to one trail, and create its directory first.

    Args:
        trail: The trail to write.
        count: The number of records to append.
    """
    trail.parent.mkdir(parents=True, exist_ok=True)  # A fresh stand-in checkout holds no data directory.
    with trail.open("a", encoding="utf-8") as handle:  # Append, as the lock module does.
        handle.write(TRAIL_RECORD * count)  # One record on each line.


class TestTheMove:
    """The root conftest points the site lock trail of each test inside the directory of that test."""

    def test_the_lock_module_reports_a_trail_inside_the_test_directory(self, tmp_path: Path) -> None:
        """The trail path MUST sit inside the temporary directory of this test."""
        logger.info("Checking the trail path under the move")  # Report the plan.

        path = lock.audit_trail_path()

        assert path == tmp_path / CheckoutTrailGuard.DIRECTORY_NAME / lock.AUDIT_FILE_NAME

    def test_a_lock_action_reaches_the_trail_of_the_test(self, tmp_path: Path) -> None:
        """A take and a release MUST reach the trail of this test."""
        logger.info("Checking where two lock actions land under the move")  # Report the plan.
        test_trail = tmp_path / CheckoutTrailGuard.DIRECTORY_NAME / lock.AUDIT_FILE_NAME
        assert lock.audit_trail_path() == test_trail, "Without the move, the two writes reach the checkout trail."

        lock._write_lock_action(ORG_ID, SITE_ID, lock.ACTION_TAKE, OPERATOR_EMAIL)
        lock._write_lock_action(ORG_ID, SITE_ID, lock.ACTION_RELEASE, OPERATOR_EMAIL)

        assert CheckoutTrailGuard.count_lines(test_trail) == 2

    def test_the_move_creates_no_folder_before_the_first_write(self, tmp_path: Path) -> None:
        """The move MUST NOT create the trail folder, so a test with no lock action finds no new folder."""
        logger.info("Checking that the move leaves the test directory unchanged")  # Report the plan.

        folder = tmp_path / CheckoutTrailGuard.DIRECTORY_NAME

        assert not folder.exists()

    def test_a_test_that_sets_its_own_directory_keeps_it(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A directory that a test sets MUST win over the move (FR-003)."""
        logger.info("Checking that the directory of a test wins over the move")  # Report the plan.
        own_directory = tmp_path / "own"
        monkeypatch.setattr(lock, "AUDIT_DIRECTORY", str(own_directory))

        path = lock.audit_trail_path()

        assert path == own_directory / lock.AUDIT_FILE_NAME


class TestTheSessionGuard:
    """The session guard counts the checkout trail, and never the moved trail of a test."""

    def test_the_session_guard_counts_the_checkout_trail(
        self, checkout_site_lock_trail_guard: CheckoutTrailGuard | None
    ) -> None:
        """The session guard MUST count the trail that the production portal writes."""
        logger.info("Checking the trail that the session guard counts")  # Report the plan.

        counted = getattr(checkout_site_lock_trail_guard, "checkout_trail", None)  # None when the guard skipped.

        assert (counted, counted == lock.audit_trail_path()) == (CHECKOUT_ROOT / "data" / lock.AUDIT_FILE_NAME, False)


class TestTheCount:
    """The count reads one trail, and a trail that the guard cannot read fails the guard."""

    def test_an_absent_trail_counts_zero(self, guard: CheckoutTrailGuard) -> None:
        """A fresh checkout holds no trail, so the count MUST be 0."""
        logger.info("Checking the count of an absent trail")  # Report the plan.

        assert guard.count_lines(guard.checkout_trail) == 0

    def test_each_record_counts_once(self, guard: CheckoutTrailGuard) -> None:
        """The count MUST equal the number of records in the trail."""
        logger.info("Checking the count of three records")  # Report the plan.
        write_records(guard.checkout_trail, 3)

        assert guard.count_lines(guard.checkout_trail) == 3

    def test_an_unreadable_trail_fails_the_guard(self, guard: CheckoutTrailGuard) -> None:
        """A trail that the guard cannot read MUST raise, and never count as 0."""
        logger.info("Checking the count of a trail that the guard cannot read")  # Report the plan.
        guard.checkout_trail.mkdir(parents=True)  # A directory at the trail path is not a readable file.

        with pytest.raises(OSError):
            guard.count_lines(guard.checkout_trail)


class TestTheGuardDecision:
    """The guard passes on equal counts, fails on a changed count, and states what it checked."""

    def test_equal_counts_pass_and_state_the_measure(self, guard: CheckoutTrailGuard) -> None:
        """Equal counts MUST pass, and the measure MUST name the path and the two counts."""
        logger.info("Checking the decision on equal counts")  # Report the plan.
        write_records(guard.checkout_trail, 2)
        before = guard.count_lines(guard.checkout_trail)

        guard.require_unchanged(before, guard.count_lines(guard.checkout_trail))

        assert guard.measure(before, before) == (
            f"Checkout site lock trail guard (issue #3503): checked 1 trail, {guard.checkout_trail}. "
            "It held 2 line(s) before the first test and 2 line(s) after the last test."
        )

    def test_a_line_written_between_the_counts_fails_the_guard(self, guard: CheckoutTrailGuard) -> None:
        """One record written during the session MUST fail the guard with the measure and the repair."""
        logger.info("Checking the decision on a record written during the session")  # Report the plan.
        write_records(guard.checkout_trail, 1)
        before = guard.count_lines(guard.checkout_trail)
        write_records(guard.checkout_trail, 1)  # The leak that issue #3503 found.

        with pytest.raises(AssertionError) as caught:
            guard.require_unchanged(before, guard.count_lines(guard.checkout_trail))

        assert str(caught.value) == guard.measure(1, 2) + CheckoutTrailGuard.REPAIR

    def test_the_repair_names_the_move_and_the_production_container(self) -> None:
        """The repair MUST name the move fixture and the production container as a second cause (FR-007)."""
        logger.info("Checking the two causes that the repair names")  # Report the plan.

        named = ("isolate_site_lock_trail" in CheckoutTrailGuard.REPAIR, "production" in CheckoutTrailGuard.REPAIR)

        assert named == (True, True)


class TestTheSkip:
    """A lock module that cannot import skips the guard, and the skip names the reason."""

    def test_the_skip_names_the_missing_capability(self) -> None:
        """The skip text MUST name the error of the import and the capability that the session lacks."""
        logger.info("Checking the skip text for a lock module that cannot import")  # Report the plan.

        measure = CheckoutTrailGuard.skip_measure(ModuleNotFoundError("No module named 'flask'"))

        assert measure == (
            "Checkout site lock trail guard (issue #3503): skipped, because the lock module cannot import "
            "(ModuleNotFoundError: No module named 'flask'). "
            "Without that module, no test can write a site lock action."
        )
