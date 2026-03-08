"""Check tasks — pre/post deployment verification Celery tasks (T060).

Runs pre-checks before and post-checks after scheduled deployments.
Results are stored as job checkpoints for audit trail.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.shared.config.settings import get_settings
from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.session import get_session_factory
from src.shared.models.operations import JobCheckpoint, ScheduledJob
from src.worker.celeryconfig import app

logger = logging.getLogger(__name__)


@app.task(name="src.worker.tasks.check_tasks.run_pre_checks")
def run_pre_checks(job_id: str, org_id: str, target_ids: list[str]) -> dict:
    """Execute pre-deployment checks and store results as checkpoint."""
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        result = _execute_pre_checks(db, job_id, org_id, target_ids)

    engine.dispose()
    return result


@app.task(name="src.worker.tasks.check_tasks.run_post_checks")
def run_post_checks(job_id: str, org_id: str, target_ids: list[str]) -> dict:
    """Execute post-deployment checks and store results as checkpoint."""
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        result = _execute_post_checks(db, job_id, org_id, target_ids)

    engine.dispose()
    return result


def _execute_pre_checks(
    db: Session,
    job_id: str,
    org_id: str,
    target_ids: list[str],
) -> dict:
    """Run pre-checks and save checkpoint."""
    from src.worker.checks.pre_checks import PreCheckService

    mist = _build_mist_service(org_id)
    service = PreCheckService(db, mist)
    results = service.run_all(org_id, target_ids)

    all_passed = all(result.passed for result in results)
    checkpoint_data = [
        {"name": r.name, "passed": r.passed, "message": r.message}
        for r in results
    ]

    _save_checkpoint(db, job_id, "pre_check", checkpoint_data, all_passed)

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
    from src.worker.checks.post_checks import PostCheckService

    mist = _build_mist_service(org_id)
    service = PostCheckService(db, mist)
    results = service.run_all(org_id, target_ids)

    all_passed = all(result.passed for result in results)
    checkpoint_data = [
        {"name": r.name, "passed": r.passed, "message": r.message}
        for r in results
    ]

    _save_checkpoint(db, job_id, "post_check", checkpoint_data, all_passed)

    return {
        "job_id": job_id,
        "phase": "post_check",
        "passed": all_passed,
        "checks": len(results),
    }


def _build_mist_service(org_id: str) -> MistEndpointService:
    """Create Mist API service for the given org."""
    factory = get_session_factory()
    api_session = factory.create_session(org_id)
    return MistEndpointService(api_session)


def _save_checkpoint(
    db: Session,
    job_id: str,
    phase: str,
    data: list[dict],
    passed: bool,
) -> None:
    """Persist a job checkpoint record."""
    checkpoint = JobCheckpoint(
        id=uuid4(),
        job_id=UUID(job_id),
        phase=phase,
        state_data={"checks": data, "passed": passed},
        created_at=datetime.now(UTC),
    )
    db.add(checkpoint)
    db.commit()
