"""Deploy tasks — install-from-revision and scheduled execution (T050 + T061).

Handles the async job execution for pushing a stored config revision
back to target devices via the Mist API with saga-pattern rollback.
Also includes the scheduled job poller for due maintenance windows.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.shared.config.constants import JobStatus
from src.shared.config.settings import get_settings
from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.session import get_session_factory
from src.shared.models.config import ConfigRevision
from src.shared.models.operations import ScheduledJob
from src.worker.celeryconfig import app
from src.worker.deploy.rollback import RollbackService, RollbackState

logger = logging.getLogger(__name__)


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
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        result = _execute_install(
            db,
            job_id,
            revision_id,
            target_entity_ids,
            org_id,
        )

    engine.dispose()
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


def _push_with_rollback(
    db: Session,
    org_id: str,
    revision: ConfigRevision,
    targets: list[dict[str, str]],
) -> RollbackState:
    """Execute push with saga-pattern rollback."""
    factory = get_session_factory()  # WHY: reuse the cached session and token factory.
    api_session = factory.create_session(org_id)  # WHY: build the org-scoped Mist SDK session.
    # WHY: enforce the org API budget on every call. Fixes #1886.
    limiter = factory.create_rate_limiter(org_id)
    # WHY: wire the limiter into the shared client.
    mist = MistEndpointService(api_session, rate_limiter=limiter)

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
    status: JobStatus,
) -> None:
    """Update job status and timestamp."""
    job.status = status.value
    job.updated_at = datetime.now(UTC)
    db.commit()


# -- T061: Scheduled job execution poller --------------------------------


@app.task(name="src.worker.tasks.deploy_tasks.poll_scheduled_jobs")
def poll_scheduled_jobs() -> dict:
    """Find and execute due scheduled jobs (Beat-scheduled).

    Polls for jobs with status APPROVED and scheduled_at <= now(),
    then executes each with pre-checks, push, and post-checks.
    """
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        due_jobs = _find_due_jobs(db)
        results = {}
        for job in due_jobs:
            results[str(job.job_id)] = _execute_scheduled_job(db, job)

    engine.dispose()
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


def _execute_scheduled_job(db: Session, job: ScheduledJob) -> dict:
    """Execute a single scheduled job with pre/post checks.

    Workflow: pre-check -> push -> post-check -> rollback-on-failure.
    """
    from src.worker.tasks.check_tasks import run_post_checks, run_pre_checks

    payload = job.change_payload or {}
    org_id = str(job.org_id)
    target_ids = payload.get("target_entity_ids", [])
    revision_id = payload.get("revision_id")

    _update_job_status(db, job, JobStatus.PRE_CHECK)
    pre_result = run_pre_checks(str(job.job_id), org_id, target_ids)
    if not pre_result.get("passed", False):
        _update_job_status(db, job, JobStatus.FAILED)
        return {"status": "pre_check_failed", "details": pre_result}

    _update_job_status(db, job, JobStatus.EXECUTING)
    async_result = install_from_revision.apply(
        args=[str(job.job_id), revision_id, target_ids, org_id],
    )
    install_result = async_result.result if async_result else {}

    _update_job_status(db, job, JobStatus.POST_CHECK)
    post_result = run_post_checks(str(job.job_id), org_id, target_ids)
    if not post_result.get("passed", False):
        _update_job_status(db, job, JobStatus.ROLLED_BACK)
        return {"status": "post_check_failed_rollback", "details": post_result}

    _update_job_status(db, job, JobStatus.COMPLETED)
    return {"status": "completed", "install": install_result}


# -- T082: Rollout wave execution tasks ----------------------------------


@app.task(name="src.worker.tasks.deploy_tasks.execute_rollout_wave")
def execute_rollout_wave(plan_id: str) -> dict:
    """Execute the next pending wave of a rollout plan.

    Called after plan activation or automatic wave promotion.
    """
    from src.worker.deploy.rollout import RolloutOrchestrator

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        orchestrator = RolloutOrchestrator(db)
        result = orchestrator.execute_next_wave(UUID(plan_id))

    engine.dispose()

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

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        orchestrator = RolloutOrchestrator(db)
        result = orchestrator.promote_wave(UUID(plan_id), wave_number)

    engine.dispose()
    return result
