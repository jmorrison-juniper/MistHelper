"""Deploy tasks — install-from-revision and scheduled execution (T050 + T061).

Handles the async job execution for pushing a stored config revision
back to target devices via the Mist API with saga-pattern rollback.
Also includes the scheduled job poller for due maintenance windows.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.config.constants import JobStatus
from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.session import get_session_factory
from src.shared.models.config import ConfigRevision
from src.shared.models.operations import ScheduledJob
from src.shared.sync_db import sync_engine
from src.worker.celeryconfig import app
from src.worker.deploy.rollback import RollbackService, RollbackState

logger = logging.getLogger(__name__)

# The shared JobStatus enum lives in `src/shared/config/constants.py`. The root
# `.gitignore` pattern `config/` keeps that file out of git, so this module
# cannot add an enum member to it. The literal below gives the job row a
# distinct value for a restore that did not finish on every device.
ROLLBACK_FAILED_STATUS = "rollback_failed"


@app.task(
    name="src.worker.tasks.deploy_tasks.install_from_revision",
    bind=True,
    max_retries=2,
)
def install_from_revision(
    self,
    job_id: str,
    revision_id: int,
    target_entity_ids: list[str],
    org_id: str,
) -> dict:
    """Execute install-from-revision job.

    Steps:
        1. Load the revision from DB
        2. Build target ID maps from entity metadata
        3. Push via RollbackService (saga pattern)
        4. Update job status
    """
    logger.info("Installing revision %s for job %s", revision_id, job_id)
    # The scope disposes the pool on the success path and on the error path.
    with sync_engine() as engine, Session(engine) as db:
        result = _execute_install(
            db,
            job_id,
            revision_id,
            target_entity_ids,
            org_id,
        )

    logger.debug("Install for job %s returned status %s", job_id, result.get("status"))
    return result


def _execute_install(
    db: Session,
    job_id: str,
    revision_id: int,
    target_entity_ids: list[str],
    org_id: str,
) -> dict:
    """Core install logic within a DB session."""
    job = _load_job(db, job_id)
    if job is None:
        return {"error": f"Job {job_id} not found"}

    _update_job_status(db, job, JobStatus.EXECUTING)

    revision = _load_revision(db, revision_id, org_id)
    if revision is None:
        _update_job_status(db, job, JobStatus.FAILED)
        return {"error": f"Revision {revision_id} not found"}

    targets = _build_targets(revision, target_entity_ids)
    state = _push_with_rollback(db, org_id, revision, targets)

    final_status = JobStatus.COMPLETED if state.status == "completed" else JobStatus.FAILED
    _update_job_status(db, job, final_status)

    return {
        "job_id": job_id,
        "status": state.status,
        "pushed": len(state.pushed),
        "error": state.error,
    }


def _load_job(db: Session, job_id: str) -> ScheduledJob | None:
    """Retrieve the job record."""
    stmt = select(ScheduledJob).where(ScheduledJob.id == UUID(job_id))
    return db.execute(stmt).scalar_one_or_none()


def _load_revision(
    db: Session,
    revision_id: int,
    org_id: str,
) -> ConfigRevision | None:
    """Retrieve the config revision."""
    stmt = select(ConfigRevision).where(
        ConfigRevision.revision_number == revision_id,
        ConfigRevision.org_id == org_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def _build_targets(
    revision: ConfigRevision,
    target_entity_ids: list[str],
) -> list[dict[str, str]]:
    """Build ID parameter dicts for each target entity."""
    targets: list[dict[str, str]] = []
    for entity_id in target_entity_ids:
        ids: dict[str, str] = {"device_id": entity_id}
        if revision.entity_type in ("site_setting", "site_info"):
            ids = {"site_id": entity_id}
        targets.append(ids)
    return targets


def _build_mist_service(org_id: str) -> MistEndpointService:
    """Create a Mist endpoint service for one organization."""
    factory = get_session_factory()  # Reuse the cached factory to avoid a new login per call.
    api_session = factory.create_session(org_id)  # Bind the session to the caller organization.
    limiter = factory.create_rate_limiter(org_id)  # Enforce the org API budget on every call. Fixes #1886.
    return MistEndpointService(api_session, rate_limiter=limiter)  # Wrap the session in the typed facade.


def _push_with_rollback(
    db: Session,
    org_id: str,
    revision: ConfigRevision,
    targets: list[dict[str, str]],
) -> RollbackState:
    """Execute push with saga-pattern rollback."""
    mist = _build_mist_service(org_id)  # Share one Mist service builder with the restore path.

    service = RollbackService(db, mist)
    config_payload = revision.config_blob or {}
    return service.execute_with_rollback(
        revision.entity_type,
        targets,
        config_payload,
    )


def _update_job_status(
    db: Session,
    job: ScheduledJob,
    status: JobStatus | str,
) -> None:
    """Update job status and timestamp."""
    # A restore that did not finish has no enum member, so accept a plain string as well.
    job.status = status.value if isinstance(status, JobStatus) else status
    job.updated_at = datetime.now(UTC)  # Record the moment of the change for the audit trail.
    db.commit()  # Persist at once so an operator reads the true state during the job.


# -- T061: Scheduled job execution poller --------------------------------


@app.task(name="src.worker.tasks.deploy_tasks.poll_scheduled_jobs")
def poll_scheduled_jobs() -> dict:
    """Find and execute due scheduled jobs (Beat-scheduled).

    Polls for jobs with status APPROVED and scheduled_at <= now(),
    then executes each with pre-checks, push, and post-checks.
    """
    logger.info("Polling for scheduled jobs that are due")
    # The scope disposes the pool on the success path and on the error path.
    with sync_engine() as engine, Session(engine) as db:
        due_jobs = _find_due_jobs(db)  # Read the approved jobs whose time arrived.
        results = {}
        for job in due_jobs:
            results[str(job.job_id)] = _execute_scheduled_job(db, job)  # Run each job.

    logger.debug("Polled and ran %d scheduled jobs", len(results))
    return {"polled": len(results), "results": results}


def _find_due_jobs(db: Session) -> list[ScheduledJob]:
    """Load approved jobs whose scheduled time has arrived."""
    now = datetime.now(UTC)
    stmt = (
        select(ScheduledJob)
        .where(
            ScheduledJob.status == JobStatus.APPROVED.value,
            ScheduledJob.scheduled_at <= now,
        )
        .order_by(ScheduledJob.scheduled_at.asc())
        .limit(10)
    )
    return list(db.execute(stmt).scalars().all())


@dataclass
class _ConfigBackup:
    """Previous configuration of every target, read before the push."""

    entity_type: str = ""
    snapshots: list[tuple[dict[str, str], dict[str, Any]]] = field(default_factory=list)


@dataclass
class _JobPlan:
    """Everything the scheduled job workflow needs after it reads the payload."""

    org_id: str
    target_ids: list[str]
    revision_id: int | None
    auto_rollback: bool
    backup: _ConfigBackup


def _build_job_plan(job: ScheduledJob) -> _JobPlan:
    """Read the job payload into a plan the workflow steps can share."""
    payload = job.change_payload or {}  # An empty payload must not raise, so default to a dict.
    return _JobPlan(
        org_id=str(job.org_id),  # The Mist session factory needs the organization as a string.
        target_ids=payload.get("target_entity_ids", []),  # No target means no device to change.
        revision_id=payload.get("revision_id"),  # The revision holds the config to push.
        # The operator can switch off the restore. Default to true, because a live network
        # must return to the last known good state when the platform finds a fault.
        auto_rollback=bool(payload.get("auto_rollback_on_failure", True)),
        backup=_ConfigBackup(),  # Start empty. The capture step fills it before the push.
    )


def _execute_scheduled_job(db: Session, job: ScheduledJob) -> dict:
    """Execute a single scheduled job with pre/post checks.

    Workflow: pre-check -> backup -> push -> post-check -> rollback-on-failure.
    """
    plan = _build_job_plan(job)  # Parse the payload once and share it with every step.
    pre_failure = _run_pre_check_phase(db, job, plan)  # Stop before the push if a device is sick.
    if pre_failure is not None:
        return pre_failure  # No push ran, so no restore is needed.

    _capture_job_backup(db, plan)  # Read the live config first, because the push overwrites it.
    install_result = _run_install_phase(db, job, plan)
    if not _install_succeeded(install_result):
        # A failed install can leave a part of the fleet on the new config, so restore now.
        return _handle_job_failure(db, job, plan, "install_failed", install_result)

    post_result = _run_post_check_phase(db, job, plan)
    if not post_result.get("passed", False):
        # The push finished but the devices are unhealthy, so put the old config back.
        return _handle_job_failure(db, job, plan, "post_check_failed", post_result)

    _update_job_status(db, job, JobStatus.COMPLETED)  # Every step passed, so the job is done.
    return {"status": "completed", "install": install_result}


def _run_pre_check_phase(
    db: Session,
    job: ScheduledJob,
    plan: _JobPlan,
) -> dict | None:
    """Run the pre-checks. Return a failure payload, or None when they pass."""
    from src.worker.tasks.check_tasks import run_pre_checks

    logger.info("Starting pre-checks for job %s", job.job_id)  # Log before the check runs.
    _update_job_status(db, job, JobStatus.PRE_CHECK)
    result = run_pre_checks(str(job.job_id), plan.org_id, plan.target_ids)
    passed = result.get("passed", False)  # A missing verdict counts as a failure, not a pass.
    logger.debug("Pre-check result for job %s: passed=%s", job.job_id, passed)
    if passed:
        return None  # None tells the caller to continue with the push.

    _update_job_status(db, job, JobStatus.FAILED)  # Nothing changed, so FAILED is the true state.
    return {"status": "pre_check_failed", "details": result}


def _capture_job_backup(db: Session, plan: _JobPlan) -> None:
    """Read the live configuration of every target before the push."""
    revision = _load_revision(db, plan.revision_id, plan.org_id) if plan.revision_id else None
    if revision is None:
        # Without the revision the workflow cannot map a target to an endpoint.
        logger.error("No revision %s for job backup, a restore is not possible", plan.revision_id)
        return

    targets = _build_targets(revision, plan.target_ids)  # Same target map the push path builds.
    plan.backup.entity_type = revision.entity_type  # The restore needs the same entity type.
    logger.info("Capturing the previous config of %d targets", len(targets))
    plan.backup.snapshots = _read_snapshots(plan.org_id, revision.entity_type, targets)
    logger.debug("Captured %d config snapshots", len(plan.backup.snapshots))


def _read_snapshots(
    org_id: str,
    entity_type: str,
    targets: list[dict[str, str]],
) -> list[tuple[dict[str, str], dict[str, Any]]]:
    """Read the current config of each target from the Mist API."""
    mist = _build_mist_service(org_id)  # One service serves every read in this loop.
    snapshots: list[tuple[dict[str, str], dict[str, Any]]] = []
    for entity_ids in targets:
        result = mist.read_entity(entity_type=entity_type, ids=entity_ids)
        if result.success and isinstance(result.data, dict):
            snapshots.append((entity_ids, result.data))  # Keep the pair so the restore finds it.
        else:
            # A missing snapshot removes the restore option for that one device.
            logger.error("Cannot read the current config of %s", entity_ids)
    return snapshots


def _run_install_phase(
    db: Session,
    job: ScheduledJob,
    plan: _JobPlan,
) -> dict:
    """Push the revision to every target and return the install result."""
    logger.info("Starting the install for job %s", job.job_id)  # Log before the push starts.
    _update_job_status(db, job, JobStatus.EXECUTING)
    async_result = install_from_revision.apply(
        args=[str(job.job_id), plan.revision_id, plan.target_ids, plan.org_id],
    )
    install_result = async_result.result if async_result else {}
    logger.debug("Install result for job %s: %s", job.job_id, install_result)
    # A non-dict result means the task raised, so hand back an empty dict the caller can read.
    return install_result if isinstance(install_result, dict) else {}


def _install_succeeded(install_result: dict) -> bool:
    """Report whether the install pushed the revision to every target."""
    if install_result.get("error"):
        return False  # The task reported an error, so treat the install as a failure.
    # Only the exact "completed" status proves that every push finished.
    return install_result.get("status") == "completed"


def _run_post_check_phase(
    db: Session,
    job: ScheduledJob,
    plan: _JobPlan,
) -> dict:
    """Run the post-checks and return the verdict."""
    from src.worker.tasks.check_tasks import run_post_checks

    logger.info("Starting post-checks for job %s", job.job_id)  # Log before the check runs.
    _update_job_status(db, job, JobStatus.POST_CHECK)
    result = run_post_checks(str(job.job_id), plan.org_id, plan.target_ids)
    logger.debug(
        "Post-check result for job %s: passed=%s",
        job.job_id,
        result.get("passed", False),
    )
    return result


def _handle_job_failure(
    db: Session,
    job: ScheduledJob,
    plan: _JobPlan,
    reason: str,
    details: dict,
) -> dict:
    """Restore the previous config and set the status from the real outcome."""
    if not plan.auto_rollback:
        # Warning: the new configuration stays live, so an operator must repair it by hand.
        logger.warning("Auto rollback is off for job %s, the new config stays live", job.job_id)
        _update_job_status(db, job, JobStatus.FAILED)  # Never claim a restore that did not run.
        return {"status": reason, "rollback": "skipped", "details": details}

    restored = _restore_previous_config(db, plan)  # Push the captured config back to the devices.
    # ROLLED_BACK must mean that every device holds the previous config again.
    _update_job_status(db, job, JobStatus.ROLLED_BACK if restored else ROLLBACK_FAILED_STATUS)
    outcome = "restored" if restored else "failed"
    logger.warning("Job %s failed at %s, the rollback outcome is %s", job.job_id, reason, outcome)
    return {"status": reason, "rollback": outcome, "details": details}


def _restore_previous_config(db: Session, plan: _JobPlan) -> bool:
    """Push every captured snapshot back. Return True when every target restored."""
    backup = plan.backup
    if not backup.snapshots:
        # Warning: no snapshot exists, so the bad configuration stays on the devices.
        logger.error("No config snapshot for job rollback, nothing was restored")
        return False

    service = RollbackService(db, _build_mist_service(plan.org_id))
    logger.info("Restoring the previous config on %d targets", len(backup.snapshots))
    restored = 0
    for entity_ids, config in backup.snapshots:
        if _restore_one_target(service, backup.entity_type, entity_ids, config):
            restored += 1  # Count only a target that holds the previous config again.
    logger.debug("Restore finished, %d of %d targets are back", restored, len(backup.snapshots))
    return restored == len(backup.snapshots)


def _restore_one_target(
    service: RollbackService,
    entity_type: str,
    entity_ids: dict[str, str],
    config: dict[str, Any],
) -> bool:
    """Push one captured snapshot back to one target."""
    # Reuse the same saga helper the push failure branch uses, one target at a time,
    # because each target carries its own previous configuration.
    state = service.execute_with_rollback(entity_type, [entity_ids], config)
    if state.status != "completed":
        logger.error("Restore failed for %s: %s", entity_ids, state.error)
        return False
    return True


# -- T082: Rollout wave execution tasks ----------------------------------


@app.task(name="src.worker.tasks.deploy_tasks.execute_rollout_wave")
def execute_rollout_wave(plan_id: str) -> dict:
    """Execute the next pending wave of a rollout plan.

    Called after plan activation or automatic wave promotion.
    """
    from src.worker.deploy.rollout import RolloutOrchestrator

    logger.info("Executing the next wave of rollout plan %s", plan_id)
    # The scope disposes the pool on the success path and on the error path.
    with sync_engine() as engine, Session(engine) as db:
        orchestrator = RolloutOrchestrator(db)  # Own the wave state machine.
        result = orchestrator.execute_next_wave(UUID(plan_id))  # Push one wave.

    logger.debug("Wave execution for plan %s returned %s", plan_id, result)

    if result.get("auto_promote"):
        execute_rollout_wave.delay(plan_id)

    return result


@app.task(name="src.worker.tasks.deploy_tasks.promote_rollout_wave")
def promote_rollout_wave(
    plan_id: str,
    wave_number: int,
) -> dict:
    """Manually promote to the next wave."""
    from src.worker.deploy.rollout import RolloutOrchestrator

    logger.info("Promoting rollout plan %s to wave %d", plan_id, wave_number)
    # The scope disposes the pool on the success path and on the error path.
    with sync_engine() as engine, Session(engine) as db:
        orchestrator = RolloutOrchestrator(db)  # Own the wave state machine.
        result = orchestrator.promote_wave(UUID(plan_id), wave_number)  # Advance it.

    logger.debug("Promotion of plan %s returned %s", plan_id, result)
    return result
