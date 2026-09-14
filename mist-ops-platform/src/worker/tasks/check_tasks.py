"""Check tasks — pre/post deployment verification Celery tasks (T060).

Runs pre-checks before and post-checks after scheduled deployments.
Results are stored as job checkpoints for audit trail.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.session import get_session_factory
from src.shared.models.operations import JobCheckpoint, ScheduledJob
from src.shared.sync_db import sync_engine
from src.worker.celeryconfig import app

logger = logging.getLogger(__name__)


@app.task(name="src.worker.tasks.check_tasks.run_pre_checks")
def run_pre_checks(job_id: str, org_id: str, target_ids: list[str]) -> dict:
    """Execute pre-deployment checks and store results as checkpoint."""
    logger.info("Running the pre-deployment checks for job %s", job_id)
    # The scope disposes the pool on the success path and on the error path.
    with sync_engine() as engine, Session(engine) as db:
        result = _execute_pre_checks(db, job_id, org_id, target_ids)  # Run the checks.

    logger.debug("Pre-checks for job %s returned %s", job_id, result.get("status"))
    return result


@app.task(name="src.worker.tasks.check_tasks.run_post_checks")
def run_post_checks(job_id: str, org_id: str, target_ids: list[str]) -> dict:
    """Execute post-deployment checks and store results as checkpoint."""
    logger.info("Running the post-deployment checks for job %s", job_id)
    # The scope disposes the pool on the success path and on the error path.
    with sync_engine() as engine, Session(engine) as db:
        result = _execute_post_checks(db, job_id, org_id, target_ids)  # Run the checks.

    logger.debug("Post-checks for job %s returned %s", job_id, result.get("status"))
    return result


def _execute_pre_checks(
    db: Session,
    job_id: str,
    org_id: str,
    target_ids: list[str],
) -> dict:
    """Run pre-checks and save checkpoint."""
    from src.worker.checks.pre_checks import PreCheckService  # WHY: defer this task dependency.

    job = _load_job(db, job_id)  # WHY: the job stores the pre-check settings.
    check_defs = _read_check_defs(job)  # WHY: use the settings stored with the job.
    mist = _build_mist_service(org_id)  # WHY: one Mist client serves all checks.
    service = PreCheckService(db, mist)  # WHY: the service owns the safety logic.
    results = service.run_all(org_id, target_ids, check_defs)  # WHY: pass the gates.

    all_passed = all(result.passed for result in results)  # WHY: one failed check stops.
    checkpoint_data = [_checkpoint_payload(r) for r in results]  # WHY: store one shape.

    _save_checkpoints(db, job_id, "pre_check", checkpoint_data)  # WHY: persist evidence.

    return {
        "job_id": job_id,
        "phase": "pre_check",
        "passed": all_passed,
        "checks": len(results),
    }


def _execute_post_checks(
    db: Session,
    job_id: str,
    org_id: str,
    target_ids: list[str],
) -> dict:
    """Run post-checks and save checkpoint."""
    from src.worker.checks.post_checks import PostCheckService  # WHY: defer this task dependency.

    mist = _build_mist_service(org_id)  # WHY: one Mist client serves all checks.
    service = PostCheckService(db, mist)  # WHY: the service owns the health logic.
    results = service.run_all(org_id, target_ids)  # WHY: run all post-checks.

    all_passed = all(result.passed for result in results)  # WHY: one failed check stops.
    checkpoint_data = [_checkpoint_payload(r) for r in results]  # WHY: store one shape.

    _save_checkpoints(db, job_id, "post_check", checkpoint_data)  # WHY: persist evidence.

    return {
        "job_id": job_id,
        "phase": "post_check",
        "passed": all_passed,
        "checks": len(results),
    }


def _build_mist_service(org_id: str) -> MistEndpointService:
    """Create Mist API service for the given org, with rate limiting applied."""
    factory = get_session_factory()  # WHY: reuse the cached session and token factory.
    api_session = factory.create_session(org_id)  # WHY: build the org-scoped Mist SDK session.
    # WHY: enforce the org API budget on every call. Fixes #1886.
    limiter = factory.create_rate_limiter(org_id)
    # WHY: wire the limiter into the shared client.
    return MistEndpointService(api_session, rate_limiter=limiter)


def _load_job(db: Session, job_id: str) -> ScheduledJob | None:
    """Load the job row so the worker can read check settings."""
    logger.info("Loading scheduled job %s for check settings", job_id)  # WHY: log first.
    job_uuid = UUID(job_id)  # WHY: convert the request id before the query.
    stmt = select(ScheduledJob).where(ScheduledJob.job_id == job_uuid)  # WHY: target one row.
    job = db.execute(stmt).scalar_one_or_none()  # WHY: accept that the row can be gone.
    logger.debug(
        "Scheduled job %s load returned found=%s",
        job_id,
        job is not None,
    )  # WHY: summarize the read.
    return job  # WHY: the caller needs the row or a safe absence.


def _read_check_defs(job: ScheduledJob | None) -> list[dict[str, Any]]:
    """Read pre-check definitions from the job row."""
    if job is None:  # WHY: absence uses no optional gates.
        return []  # WHY: the required reachability check can still run.
    if job.pre_check_defs is None:  # WHY: a job can omit optional gates.
        return []  # WHY: no setting means no optional version check.
    return cast("list[dict[str, Any]]", job.pre_check_defs)  # WHY: JSONB stores this list.


def _checkpoint_payload(result: object) -> dict[str, Any]:
    """Build the stored payload for one check result."""
    return {
        "name": getattr(result, "name", ""),  # WHY: retain the check name for audit review.
        "passed": bool(getattr(result, "passed", False)),  # WHY: store the exact pass verdict.
        "message": getattr(result, "message", ""),  # WHY: give the operator the failure reason.
        "details": getattr(result, "details", {}),  # WHY: keep safe evidence for troubleshooting.
    }


def _save_checkpoints(
    db: Session,
    job_id: str,
    phase: str,
    data: list[dict[str, Any]],
) -> None:
    """Persist job checkpoint records."""
    logger.info(
        "Saving %d %s checkpoint rows for job %s",
        len(data),
        phase,
        job_id,
    )  # WHY: log before writes.
    for item in data:  # WHY: the schema stores one checkpoint per entity and step.
        checkpoint = _build_checkpoint(job_id, phase, item)  # WHY: convert to ORM fields.
        db.add(checkpoint)  # WHY: stage the checkpoint for one database commit.
    db.commit()  # WHY: make all checkpoint rows durable together.
    logger.debug(
        "Saved %d %s checkpoint rows for job %s",
        len(data),
        phase,
        job_id,
    )  # WHY: summarize writes.


def _build_checkpoint(job_id: str, phase: str, item: dict[str, Any]) -> JobCheckpoint:
    """Create one checkpoint row from one check result."""
    entity_text = str(item.get("name", "")).split(":", 1)[-1]  # WHY: read the target id.
    entity_id = _checkpoint_entity_id(entity_text)  # WHY: keep UUID storage.
    status = "passed" if item.get("passed") else "failed"  # WHY: make status queryable.
    return JobCheckpoint(
        job_id=UUID(job_id),
        entity_id=entity_id,
        step=phase,
        status=status,
        payload=item,
        created_at=datetime.now(UTC),
    )  # WHY: match the ORM model and the 0003 migration.


def _checkpoint_entity_id(entity_text: str) -> UUID:
    """Return a UUID for a checkpoint target."""
    try:
        return UUID(entity_text)  # WHY: production target ids already are Mist UUIDs.
    except ValueError:
        return uuid5(NAMESPACE_URL, entity_text)  # WHY: tests use stable non-UUID target ids.
