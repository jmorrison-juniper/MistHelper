"""Tests for pre-check target safety."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock
from uuid import uuid4

from src.worker.checks.pre_checks import CheckResult, PreCheckService
from src.worker.tasks import check_tasks

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest

EXPECTED_MIXED_CHECKS = 2  # WHY: the mixed case must keep both target results.


def _run_pre_check_task(
    monkeypatch: pytest.MonkeyPatch,
    results: Sequence[object],
    targets: list[str],
) -> dict[str, Any]:
    """Run the pre-check task with controlled service results."""
    job_id = str(uuid4())  # WHY: the task converts the job id to a UUID for checkpoint rows.
    save_checkpoints = MagicMock()  # WHY: the test reads the task result, not the database write.
    monkeypatch.setattr(
        check_tasks,
        "_load_job",
        lambda _db, _job_id: None,
    )  # WHY: no job row is needed for aggregation.
    monkeypatch.setattr(
        check_tasks,
        "_build_mist_service",
        lambda _org_id: MagicMock(),
    )  # WHY: no API call is needed.
    monkeypatch.setattr(
        check_tasks,
        "_save_checkpoints",
        save_checkpoints,
    )  # WHY: keep the test hermetic.
    monkeypatch.setattr(
        PreCheckService,
        "run_all",
        lambda _service, _org_id, _targets, _defs=None: list(results),
    )  # WHY: isolate task aggregation from the service implementation.
    return check_tasks._execute_pre_checks(
        MagicMock(),
        job_id,
        "org-1",
        targets,
    )  # WHY: exercise the scheduled task path.


def test_pre_check_task_fails_closed_with_zero_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A scheduled pre-check with no targets must not pass."""
    result = _run_pre_check_task(
        monkeypatch,
        [CheckResult("target_selection", False)],
        [],
    )  # WHY: reproduce issue #2657 with an explicit empty-target failure.

    assert result["passed"] is False  # WHY: a safety gate that checked no target must fail closed.
    assert result["checks"] == 1  # WHY: the task must record that a failure was evaluated.


def test_pre_check_task_passes_with_one_passing_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A scheduled pre-check passes when one target passes."""
    result = _run_pre_check_task(
        monkeypatch,
        [CheckResult("reachability:dev-a", True)],
        ["dev-a"],
    )  # WHY: one evaluated target proves the safety gate ran.

    assert result["passed"] is True  # WHY: all evaluated checks passed.
    assert result["checks"] == 1  # WHY: one target produced one result.


def test_pre_check_task_fails_with_one_failing_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A scheduled pre-check fails when one target fails."""
    result = _run_pre_check_task(
        monkeypatch,
        [CheckResult("reachability:dev-a", False)],
        ["dev-a"],
    )  # WHY: one failed target must block the action.

    assert result["passed"] is False  # WHY: one failed check must fail the task.
    assert result["checks"] == 1  # WHY: the failed target still counts as evaluated.


def test_pre_check_task_fails_with_mixed_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A scheduled pre-check fails when one target fails."""
    result = _run_pre_check_task(
        monkeypatch,
        [CheckResult("reachability:dev-a", True), CheckResult("reachability:dev-b", False)],
        ["dev-a", "dev-b"],
    )  # WHY: a mixed set must not hide the failed target.

    assert result["passed"] is False  # WHY: one failed check blocks the pass report.
    assert result["checks"] == EXPECTED_MIXED_CHECKS  # WHY: both target results must count.


def test_pre_check_task_fails_when_a_result_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A scheduled pre-check fails when one target returns no result."""
    result = _run_pre_check_task(
        monkeypatch,
        [None],
        ["dev-a"],
    )  # WHY: an absent result cannot prove that the target is safe.

    assert result["passed"] is False  # WHY: missing evidence must fail closed.
    assert result["checks"] == 1  # WHY: the task must not drop the missing result.
