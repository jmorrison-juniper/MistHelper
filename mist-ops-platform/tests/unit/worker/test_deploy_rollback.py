"""Tests for the rollback behavior of the scheduled job workflow (issue #1887).

The scheduled job workflow pushes a configuration change to live network
devices. A failure after the push must restore the previous configuration.
The job status must report what the restore really did.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar

import pytest

from src.worker.deploy.rollback import RollbackState
from src.worker.tasks import check_tasks, deploy_tasks

PREVIOUS_CONFIG = {"radio_config": {"band_24": {"power": 8}}}
NEW_CONFIG = {"radio_config": {"band_24": {"power": 14}}}


class FakeSession:
    """Stand-in for the SQLAlchemy session."""

    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeJob:
    """Stand-in for the ScheduledJob row."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.job_id = uuid.uuid4()
        self.org_id = uuid.uuid4()
        self.change_payload = payload
        self.status = "approved"
        self.updated_at = datetime.now(UTC)


class FakeRevision:
    """Stand-in for the ConfigRevision row."""

    entity_type = "device"
    config_blob = NEW_CONFIG


class FakeReadResult:
    """Stand-in for the Mist read result."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.success = True
        self.data = data


class FakeMist:
    """Stand-in for the Mist endpoint service."""

    def read_entity(self, entity_type: str, ids: dict[str, str]) -> FakeReadResult:
        return FakeReadResult(dict(PREVIOUS_CONFIG))


class FakeRollbackService:
    """Stand-in for RollbackService that records every restore call."""

    calls: ClassVar[list[tuple[str, list[dict[str, str]], dict[str, Any]]]] = []
    restore_status = "completed"

    def __init__(self, db: Any, mist: Any) -> None:
        self.db = db
        self.mist = mist

    def execute_with_rollback(
        self,
        entity_type: str,
        targets: list[dict[str, str]],
        new_config: dict[str, Any],
    ) -> RollbackState:
        FakeRollbackService.calls.append((entity_type, targets, new_config))
        return RollbackState(status=FakeRollbackService.restore_status, error="push denied")


class FakeAsyncResult:
    """Stand-in for the Celery async result."""

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result


class FakeInstallTask:
    """Stand-in for the install_from_revision Celery task."""

    def __init__(self, result: dict[str, Any]) -> None:
        self._result = result
        self.calls = 0

    def apply(self, args: list[Any]) -> FakeAsyncResult:
        self.calls += 1
        return FakeAsyncResult(self._result)


class CheckRecorder:
    """Record every check call and return a fixed verdict."""

    def __init__(self, passed: bool) -> None:
        self.passed = passed
        self.calls = 0

    def __call__(self, job_id: str, org_id: str, target_ids: list[str]) -> dict[str, Any]:
        self.calls += 1
        return {"passed": self.passed}


def _build_payload(auto_rollback: bool = True) -> dict[str, Any]:
    """Build a job payload with one target device."""
    return {
        "target_entity_ids": [str(uuid.uuid4())],
        "revision_id": 7,
        "auto_rollback_on_failure": auto_rollback,
    }


@pytest.fixture()
def workflow(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace every outside call of the scheduled job workflow."""
    FakeRollbackService.calls = []
    FakeRollbackService.restore_status = "completed"

    pre_check = CheckRecorder(passed=True)
    post_check = CheckRecorder(passed=True)
    install = FakeInstallTask({"status": "completed", "pushed": 1, "error": None})

    monkeypatch.setattr(check_tasks, "run_pre_checks", pre_check)
    monkeypatch.setattr(check_tasks, "run_post_checks", post_check)
    monkeypatch.setattr(deploy_tasks, "install_from_revision", install)
    monkeypatch.setattr(deploy_tasks, "RollbackService", FakeRollbackService)
    monkeypatch.setattr(deploy_tasks, "_build_mist_service", lambda org_id: FakeMist())
    monkeypatch.setattr(
        deploy_tasks,
        "_load_revision",
        lambda db, revision_id, org_id: FakeRevision(),
    )
    return {"pre_check": pre_check, "post_check": post_check, "install": install}


class TestPostCheckRollback:
    """Verify that a failure after the push restores the previous config."""

    def test_post_check_failure_runs_the_restore(
        self,
        workflow: dict[str, Any],
    ) -> None:
        """A failed post-check must push the previous config back."""
        workflow["post_check"].passed = False
        db = FakeSession()
        job = FakeJob(_build_payload())

        result = deploy_tasks._execute_scheduled_job(db, job)

        assert FakeRollbackService.calls, "The restore helper never ran"
        assert FakeRollbackService.calls[0][2] == PREVIOUS_CONFIG
        assert job.status == "rolled_back"
        assert result["rollback"] == "restored"

    def test_failed_install_skips_the_post_check_and_restores(
        self,
        workflow: dict[str, Any],
    ) -> None:
        """A failed install must stop the workflow and start the restore."""
        workflow["install"]._result = {"status": "failed", "error": "push denied"}
        db = FakeSession()
        job = FakeJob(_build_payload())

        result = deploy_tasks._execute_scheduled_job(db, job)

        assert workflow["post_check"].calls == 0, "The post-check ran after a failed install"
        assert FakeRollbackService.calls, "The restore helper never ran"
        assert job.status == "rolled_back"
        assert result["status"] == "install_failed"

    def test_auto_rollback_off_marks_the_job_failed(
        self,
        workflow: dict[str, Any],
    ) -> None:
        """A job that switches off auto rollback must report FAILED."""
        workflow["post_check"].passed = False
        db = FakeSession()
        job = FakeJob(_build_payload(auto_rollback=False))

        result = deploy_tasks._execute_scheduled_job(db, job)

        assert FakeRollbackService.calls == [], "The restore ran although the switch is off"
        assert job.status == "failed"
        assert job.status != "rolled_back"
        assert result["rollback"] == "skipped"

    def test_incomplete_restore_marks_rollback_failed(
        self,
        workflow: dict[str, Any],
    ) -> None:
        """A restore that does not finish must report ROLLBACK_FAILED."""
        workflow["post_check"].passed = False
        FakeRollbackService.restore_status = "partial_rollback"
        db = FakeSession()
        job = FakeJob(_build_payload())

        result = deploy_tasks._execute_scheduled_job(db, job)

        assert job.status == deploy_tasks.ROLLBACK_FAILED_STATUS
        assert job.status != "rolled_back"
        assert result["rollback"] == "failed"

    def test_happy_path_keeps_the_new_config(
        self,
        workflow: dict[str, Any],
    ) -> None:
        """A job that passes every check must not restore anything."""
        db = FakeSession()
        job = FakeJob(_build_payload())

        result = deploy_tasks._execute_scheduled_job(db, job)

        assert FakeRollbackService.calls == [], "The restore ran on a healthy job"
        assert job.status == "completed"
        assert result["status"] == "completed"

    def test_pre_check_failure_skips_the_install(
        self,
        workflow: dict[str, Any],
    ) -> None:
        """A failed pre-check must not push anything."""
        workflow["pre_check"].passed = False
        db = FakeSession()
        job = FakeJob(_build_payload())

        result = deploy_tasks._execute_scheduled_job(db, job)

        assert workflow["install"].calls == 0, "The install ran after a failed pre-check"
        assert FakeRollbackService.calls == [], "The restore ran without a push"
        assert job.status == "failed"
        assert result["status"] == "pre_check_failed"
