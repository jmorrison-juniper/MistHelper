"""Test the audit trail isolation of the browser test portal. Issue #3498.

Why:
    The browser test portal wrote each site lock action to the checkout trail.
    In the main checkout, that file is the production audit trail, and the
    production container mounts it. The trail held 909 test lines, and no gate
    reported the leak.

    `AuditTrailIsolation` moves the trail of the test portal into the artifact
    directory of its own run. It also counts the checkout trail before and
    after the run. These tests prove the move and the guard decision with no
    browser and no network.

    Each test passes the `monkeypatch` fixture to the move. The fixture then
    restores the directory of the lock module after the test, so no other test
    reads a moved trail.

    Issue #3512 found that the browser guard read the moved trail of the first
    test when a module started the portal inside that test. The browser guard
    now reads the checkout trail from the root guard of issue #3503. The tests
    of `TestTheSessionBuild` prove that source with the move of the root
    conftest in place.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from src.interfaces.portals.upgrade_portal.runtime import lock
from tests.support.site_lock_trail import CheckoutTrailGuard
from tests.support.upgrade_portal_e2e.records.audit import AuditTrailIsolation

logger = logging.getLogger(__name__)  # WHY: keep test log records on the module logger.

ORG_ID = "11111111-1111-1111-1111-111111111111"  # The stand-in organization of the browser suite.
SITE_ID = "34983498-3498-3498-3498-349834983498"  # The journey site of issue #3498.
OPERATOR_EMAIL = "e2e.operator@example.invalid"  # A reserved address that reaches no mail host.
TRAIL_RECORD = '{"action": "take"}\n'  # One record of the append-only trail.
CHECKOUT_ROOT = Path(__file__).resolve().parents[3]  # Issue #3512: this file sits at the depth of the lock module.


@pytest.fixture(name="isolation")
def fixture_isolation(tmp_path: Path) -> AuditTrailIsolation:
    """Build one isolation whose two trails sit inside `tmp_path`.

    Args:
        tmp_path: The directory of this test alone.

    Returns:
        The isolation of a stand-in run.
    """
    logger.info("Build an isolation inside %s", tmp_path)  # Report before the build.
    checkout_trail = tmp_path / "checkout" / "data" / lock.AUDIT_FILE_NAME  # The stand-in production trail.
    built = AuditTrailIsolation(tmp_path / "run", checkout_trail)  # The stand-in run directory.
    logger.debug("Built an isolation with the run trail %s", built.run_trail)  # Report after the build.
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
    """The move points the writer and the reader of the lock module at the run trail."""

    def test_the_move_points_the_lock_module_at_the_run_trail(
        self, isolation: AuditTrailIsolation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The path that the lock module reports MUST be the run trail after the move."""
        logger.info("Checking the path after the move")  # Report the plan.

        placed = isolation.place(monkeypatch)

        assert (placed, lock.audit_trail_path()) == (isolation.run_trail.resolve(), isolation.run_trail.resolve())

    def test_a_lock_action_after_the_move_reaches_the_run_trail_only(
        self, isolation: AuditTrailIsolation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A take and a release MUST reach the run trail and never the checkout trail."""
        logger.info("Checking where two lock actions land after the move")  # Report the plan.
        isolation.place(monkeypatch)

        lock._write_lock_action(ORG_ID, SITE_ID, lock.ACTION_TAKE, OPERATOR_EMAIL)
        lock._write_lock_action(ORG_ID, SITE_ID, lock.ACTION_RELEASE, OPERATOR_EMAIL)

        counts = (isolation.count_lines(isolation.run_trail), isolation.count_lines(isolation.checkout_trail))
        assert counts == (2, 0), f"The run trail and the checkout trail hold {counts} line(s)."

    def test_the_move_refuses_a_run_trail_that_is_the_checkout_trail(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A move to the checkout trail MUST fail and MUST leave the lock module unchanged."""
        logger.info("Checking the refusal of a move to the checkout trail")  # Report the plan.
        original = lock.AUDIT_DIRECTORY  # The directory that the refusal must keep.
        same = AuditTrailIsolation(tmp_path, tmp_path / lock.AUDIT_FILE_NAME)

        with pytest.raises(ValueError, match="is the checkout trail"):
            same.place(monkeypatch)

        assert lock.AUDIT_DIRECTORY == original

    def test_the_move_refuses_a_lock_module_that_reports_another_path(
        self, isolation: AuditTrailIsolation, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A lock module that ignores the new directory MUST stop the test portal."""
        logger.info("Checking the refusal of a lock module that ignores the move")  # Report the plan.
        elsewhere = tmp_path / "elsewhere" / lock.AUDIT_FILE_NAME  # The path of a lock module that cached its path.
        monkeypatch.setattr(lock, "audit_trail_path", lambda: elsewhere)

        with pytest.raises(RuntimeError, match="elsewhere"):
            isolation.place(monkeypatch)


class TestTheCount:
    """The count reads one trail, and a trail that the guard cannot read fails the guard."""

    def test_an_absent_trail_counts_zero(self, isolation: AuditTrailIsolation) -> None:
        """A fresh checkout holds no trail, so the count MUST be 0."""
        logger.info("Checking the count of an absent trail")  # Report the plan.

        assert isolation.count_lines(isolation.checkout_trail) == 0

    def test_each_record_counts_once(self, isolation: AuditTrailIsolation) -> None:
        """The count MUST equal the number of records in the trail."""
        logger.info("Checking the count of three records")  # Report the plan.
        write_records(isolation.checkout_trail, 3)

        assert isolation.count_lines(isolation.checkout_trail) == 3

    def test_an_unreadable_trail_fails_the_guard(self, isolation: AuditTrailIsolation) -> None:
        """A trail that the guard cannot read MUST raise, and never count as 0."""
        logger.info("Checking the count of a trail that the guard cannot read")  # Report the plan.
        isolation.checkout_trail.mkdir(parents=True)  # A directory at the trail path is not a readable file.

        with pytest.raises(OSError):
            isolation.count_lines(isolation.checkout_trail)


class TestTheGuardDecision:
    """The guard passes on equal counts, fails on a changed count, and states what it checked."""

    def test_equal_counts_pass_and_state_the_measure(self, isolation: AuditTrailIsolation) -> None:
        """Equal counts MUST pass, and the measure MUST name the path and the counts."""
        logger.info("Checking the decision on equal counts")  # Report the plan.
        write_records(isolation.checkout_trail, 2)
        before = isolation.count_lines(isolation.checkout_trail)

        isolation.require_unchanged(before, isolation.count_lines(isolation.checkout_trail))

        assert isolation.measure(before, before) == (
            f"Checkout audit trail guard (issue #3498): checked 1 trail, {isolation.checkout_trail}. "
            "It held 2 line(s) before the browser run and 2 line(s) after the run. "
            f"The trail of this run holds 0 line(s), at {isolation.run_trail}."
        )

    def test_a_line_written_between_the_counts_fails_the_guard(self, isolation: AuditTrailIsolation) -> None:
        """One record written during the run MUST fail the guard with the path, the counts, and the repair."""
        logger.info("Checking the decision on a record written during the run")  # Report the plan.
        write_records(isolation.checkout_trail, 1)
        before = isolation.count_lines(isolation.checkout_trail)
        write_records(isolation.checkout_trail, 1)  # The leak that issue #3498 found.

        with pytest.raises(AssertionError) as caught:
            isolation.require_unchanged(before, isolation.count_lines(isolation.checkout_trail))

        assert str(caught.value) == isolation.measure(1, 2) + AuditTrailIsolation.REPAIR

    def test_the_measure_counts_the_records_of_the_run_trail(
        self, isolation: AuditTrailIsolation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The measure MUST count the records that the test portal wrote to its own trail."""
        logger.info("Checking the run trail count of the measure")  # Report the plan.
        isolation.place(monkeypatch)
        lock._write_lock_action(ORG_ID, SITE_ID, lock.ACTION_TAKE, OPERATOR_EMAIL)

        measure = isolation.measure(0, 0)

        assert measure.endswith(f"The trail of this run holds 1 line(s), at {isolation.run_trail}.")


class TestTheSessionBuild:
    """The browser guard reads the checkout trail from the root guard, in each order. Issue #3512."""

    def test_a_build_with_no_checkout_trail_fails(self, tmp_path: Path) -> None:
        """A build that names no checkout trail MUST fail, so no default can read a moved trail (FR-002)."""
        logger.info("Checking a build that names no checkout trail")  # Report the plan.
        constructor: Any = AuditTrailIsolation  # Any, because this call leaves out a required argument on purpose.

        with pytest.raises(TypeError) as caught:
            constructor(tmp_path / "run")

        assert "checkout_trail" in str(caught.value)

    def test_a_late_build_names_the_trail_of_the_root_guard(
        self, tmp_path: Path, checkout_site_lock_trail_guard: CheckoutTrailGuard | None
    ) -> None:
        """A build under the move of the root conftest MUST name the trail of the root guard (FR-001, FR-005)."""
        logger.info("Checking a build that starts after the move of this test")  # Report the plan.
        moved = tmp_path / CheckoutTrailGuard.DIRECTORY_NAME / lock.AUDIT_FILE_NAME  # The trail of this test.
        assert lock.audit_trail_path() == moved, "Without the move, this test cannot show the fault of issue #3512."

        built = AuditTrailIsolation.for_session(tmp_path / "run", checkout_site_lock_trail_guard)

        expected = (CHECKOUT_ROOT / "data" / lock.AUDIT_FILE_NAME, False)  # The checkout trail, not the moved trail.
        assert (built.checkout_trail, built.checkout_trail == moved) == expected

    def test_a_build_with_no_root_guard_fails(self, tmp_path: Path) -> None:
        """A build with no root guard MUST fail and name the lock module, and never read a moved trail (FR-003)."""
        logger.info("Checking a build that has no root guard")  # Report the plan.

        with pytest.raises(RuntimeError) as caught:
            AuditTrailIsolation.for_session(tmp_path / "run", None)

        message = str(caught.value)  # The text that a maintainer reads in the failed run.
        assert (message, "checkout_site_lock_trail_guard" in message, "lock module" in message) == (
            AuditTrailIsolation.NO_ROOT_GUARD,
            True,
            True,
        )
