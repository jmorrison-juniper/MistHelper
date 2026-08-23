"""Deploy job CRUD and dry-run endpoints (T063, T064).

Covers:
  - GET    /deploy/jobs          — list jobs
  - POST   /deploy/jobs          — create a job
  - GET    /deploy/jobs/{id}     — job detail (with checkpoints)
  - PUT    /deploy/jobs/{id}     — update pending job
  - DELETE /deploy/jobs/{id}     — cancel pending job
  - POST   /deploy/jobs/{id}/approve  — approve a job
  - POST   /deploy/dry-run       — validate without applying
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import (
    get_authenticated_user,
    get_db_session,
    get_scoped_org_id,
)
from src.api.middleware.auth import CurrentUser
from src.api.schemas.common import ResponseEnvelope
from src.shared.config.settings import get_settings
from src.api.schemas.deploy import (
    CheckpointDetail,
    DryRunRequest,
    DryRunResponse,
    GoldenImageCreate,
    GoldenImageResponse,
    JobApproveRequest,
    JobCancelledResponse,
    JobCreate,
    JobDetail,
    JobSummary,
    JobUpdate,
    RolloutCreate,
    RolloutDetail,
    RolloutSummary,
    TargetEntity,
    TemplateCreate,
    TemplateInstantiateRequest,
    TemplateResponse,
    WaveResponse,
)
from src.shared.config.constants import JobStatus
from src.shared.models.governance import ChangeTemplate, GoldenImage
from src.shared.models.operations import (
    JobCheckpoint,
    RolloutPlan,
    RolloutWave,
    ScheduledJob,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deploy", tags=["deploy"])


# -- Helpers ---


async def _load_job(
    db: AsyncSession,
    job_id: UUID,
) -> ScheduledJob:
    """Load a job or raise 404."""
    stmt = select(ScheduledJob).where(ScheduledJob.job_id == job_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return row


def _target_count(job: ScheduledJob) -> int:
    """Extract target entity count from JSONB."""
    targets = job.target_entities
    if isinstance(targets, list):
        return len(targets)
    return 0


# -- Routes ---


@router.get("/jobs")
async def list_jobs(
    org_id: UUID = Depends(get_scoped_org_id),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[JobSummary]]:
    """List scheduled deployment jobs for an org."""
    stmt = select(ScheduledJob).where(ScheduledJob.org_id == org_id).order_by(ScheduledJob.scheduled_at.desc())
    if status:
        stmt = stmt.where(ScheduledJob.status == status)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    items = [
        JobSummary(
            job_id=r.job_id,
            status=r.status,
            scheduled_at=r.scheduled_at,
            target_count=_target_count(r),
            created_by=r.created_by,
            approved_by=r.approved_by,
            rollout_plan_id=r.rollout_plan_id,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return ResponseEnvelope(data=items)


@router.post("/jobs", status_code=201)
async def create_job(
    body: JobCreate,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[JobSummary]:
    """Create a new scheduled deployment job."""
    conflict = await _check_conflicts(db, body)
    if conflict:
        raise HTTPException(status_code=409, detail=conflict)

    job = ScheduledJob(
        org_id=body.org_id,
        target_entities=[t.model_dump() for t in body.target_entities],
        change_payload=body.change_payload,
        scheduled_at=body.scheduled_at,
        status=JobStatus.PENDING.value,
        pre_check_defs=[c.model_dump() for c in body.pre_check_defs],
        post_check_defs=[c.model_dump() for c in body.post_check_defs],
        created_by=user.email,
    )
    db.add(job)
    await db.flush()

    summary = JobSummary(
        job_id=job.job_id,
        status=job.status,
        scheduled_at=job.scheduled_at,
        target_count=len(body.target_entities),
        created_by=job.created_by,
        approved_by=None,
        rollout_plan_id=None,
        created_at=job.created_at,
    )
    return ResponseEnvelope(data=summary)


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[JobDetail]:
    """Get detailed job status with checkpoint progress."""
    job = await _load_job(db, job_id)
    checkpoints = _build_checkpoints(job)
    targets = _parse_targets(job)

    detail = JobDetail(
        job_id=job.job_id,
        status=job.status,
        scheduled_at=job.scheduled_at,
        started_at=job.started_at,
        target_entities=targets,
        change_payload=job.change_payload,
        pre_check_result=job.pre_check_result,
        post_check_result=job.post_check_result,
        checkpoints=checkpoints,
        created_by=job.created_by,
        approved_by=job.approved_by,
    )
    return ResponseEnvelope(data=detail)


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: UUID,
    body: JobUpdate,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[JobSummary]:
    """Update a pending job (reschedule or modify)."""
    job = await _load_job(db, job_id)
    if job.status != JobStatus.PENDING.value:
        raise HTTPException(
            status_code=409,
            detail="Only pending jobs can be updated",
        )

    _apply_updates(job, body)
    await db.flush()
    return ResponseEnvelope(data=_to_summary(job))


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[JobCancelledResponse]:
    """Cancel a pending job."""
    job = await _load_job(db, job_id)
    if job.status not in (JobStatus.PENDING.value, JobStatus.APPROVED.value):
        raise HTTPException(
            status_code=409,
            detail="Only pending or approved jobs can be cancelled",
        )

    job.status = JobStatus.CANCELLED.value
    now = datetime.now(UTC)
    job.completed_at = now
    await db.flush()

    return ResponseEnvelope(
        data=JobCancelledResponse(
            job_id=job.job_id,
            status="cancelled",
            cancelled_at=now,
        ),
    )


@router.post("/jobs/{job_id}/approve")
async def approve_job(
    job_id: UUID,
    body: JobApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[JobSummary]:
    """Approve a job (maker-checker FR-033)."""
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail="confirm must be true",
        )

    job = await _load_job(db, job_id)
    if job.status != JobStatus.PENDING.value:
        raise HTTPException(
            status_code=409,
            detail="Only pending jobs can be approved",
        )
    if job.created_by == user.email:
        raise HTTPException(
            status_code=403,
            detail="Approver must be different from creator",
        )

    job.status = JobStatus.APPROVED.value
    job.approved_by = user.email
    await db.flush()
    return ResponseEnvelope(data=_to_summary(job))


# -- Dry-run endpoint (T064) ---


@router.post("/dry-run")
async def dry_run(
    body: DryRunRequest,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[DryRunResponse]:
    """Validate a change without applying it (FR-036, SC-013 <10s)."""
    from src.worker.deploy.dry_run import DryRunValidator

    validator = DryRunValidator(db)
    result = await validator.validate(body)
    return ResponseEnvelope(data=result)


# -- Private helpers ---


async def _check_conflicts(
    db: AsyncSession,
    body: JobCreate,
) -> str | None:
    """Check for scheduling conflicts on the same targets."""
    entity_ids = [t.entity_id for t in body.target_entities]
    stmt = select(ScheduledJob).where(
        ScheduledJob.org_id == body.org_id,
        ScheduledJob.scheduled_at == body.scheduled_at,
        ScheduledJob.status.in_(
            [
                JobStatus.PENDING.value,
                JobStatus.APPROVED.value,
            ]
        ),
    )
    existing = (await db.execute(stmt)).scalars().all()
    for job in existing:
        targets = job.target_entities or []
        for target in targets:
            tid = target.get("entity_id")
            if tid and UUID(tid) in entity_ids:
                return f"Device {tid} has a pending job " f"at {job.scheduled_at}. " f"Conflicting job: {job.job_id}"
    return None


def _build_checkpoints(job: ScheduledJob) -> list[CheckpointDetail]:
    """Convert ORM checkpoints to schema objects."""
    return [
        CheckpointDetail(
            entity_id=cp.entity_id,
            step=cp.step,
            status=cp.status,
            detail=cp.payload,
        )
        for cp in (job.checkpoints or [])
    ]


def _parse_targets(job: ScheduledJob) -> list[TargetEntity]:
    """Parse JSONB target_entities into typed objects."""
    raw = job.target_entities or []
    return [
        TargetEntity(
            entity_type=t.get("entity_type", ""),
            entity_id=UUID(t["entity_id"]),
        )
        for t in raw
        if "entity_id" in t
    ]


def _apply_updates(job: ScheduledJob, body: JobUpdate) -> None:
    """Apply partial update fields to a job."""
    if body.scheduled_at is not None:
        job.scheduled_at = body.scheduled_at
    if body.change_payload is not None:
        job.change_payload = body.change_payload
    if body.pre_check_defs is not None:
        job.pre_check_defs = [c.model_dump() for c in body.pre_check_defs]
    if body.post_check_defs is not None:
        job.post_check_defs = [c.model_dump() for c in body.post_check_defs]


def _to_summary(job: ScheduledJob) -> JobSummary:
    """Convert ORM job to summary schema."""
    return JobSummary(
        job_id=job.job_id,
        status=job.status,
        scheduled_at=job.scheduled_at,
        target_count=_target_count(job),
        created_by=job.created_by,
        approved_by=job.approved_by,
        rollout_plan_id=job.rollout_plan_id,
        created_at=job.created_at,
    )


# ===================================================================
# Rollout endpoints (T084)
# ===================================================================


@router.get("/rollouts")
async def list_rollouts(
    org_id: UUID = Depends(get_scoped_org_id),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[RolloutSummary]]:
    """List rollout plans for an org."""
    stmt = select(RolloutPlan).where(RolloutPlan.org_id == org_id).order_by(RolloutPlan.created_at.desc())
    if status:
        stmt = stmt.where(RolloutPlan.status == status)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    items = [_plan_to_summary(r) for r in rows]
    return ResponseEnvelope(data=items)


@router.post("/rollouts", status_code=201)
async def create_rollout(
    body: RolloutCreate,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[RolloutSummary]:
    """Create a multi-wave rollout plan."""
    plan = RolloutPlan(
        org_id=body.org_id,
        name=body.name,
        promotion_mode=body.promotion_mode,
        health_gate_criteria=body.health_gate_criteria.model_dump(),
        status="draft",
        created_by=user.email,
    )
    db.add(plan)
    await db.flush()

    for wave_def in body.waves:
        wave = RolloutWave(
            plan_id=plan.plan_id,
            wave_number=wave_def.wave_number,
            target_entities=[t.model_dump() for t in wave_def.target_entities],
            status="pending",
        )
        db.add(wave)
    await db.flush()

    return ResponseEnvelope(data=_plan_to_summary(plan, body.waves))


@router.post("/rollouts/{plan_id}/activate")
async def activate_rollout(
    plan_id: UUID,
    body: JobApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[dict]:
    """Activate a rollout (draft -> active, starts first wave)."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    plan = await _load_plan(db, plan_id)
    if plan.status != "draft":
        raise HTTPException(status_code=409, detail="Plan must be draft")

    plan.status = "active"
    await db.flush()

    from src.worker.tasks.deploy_tasks import execute_rollout_wave

    execute_rollout_wave.delay(str(plan_id))

    return ResponseEnvelope(data={"plan_id": str(plan_id), "status": "active"})


@router.post("/rollouts/{plan_id}/pause")
async def pause_rollout(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[dict]:
    """Pause an active rollout."""
    plan = await _load_plan(db, plan_id)
    if plan.status != "active":
        raise HTTPException(status_code=409, detail="Plan must be active")
    plan.status = "paused"
    await db.flush()
    return ResponseEnvelope(data={"plan_id": str(plan_id), "status": "paused"})


@router.post("/rollouts/{plan_id}/resume")
async def resume_rollout(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[dict]:
    """Resume a paused rollout."""
    plan = await _load_plan(db, plan_id)
    if plan.status != "paused":
        raise HTTPException(status_code=409, detail="Plan must be paused")
    plan.status = "active"
    await db.flush()

    from src.worker.tasks.deploy_tasks import execute_rollout_wave

    execute_rollout_wave.delay(str(plan_id))

    return ResponseEnvelope(data={"plan_id": str(plan_id), "status": "active"})


@router.post("/rollouts/{plan_id}/waves/{wave_number}/promote")
async def promote_wave(
    plan_id: UUID,
    wave_number: int,
    body: JobApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[dict]:
    """Manually promote to the next wave."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    from src.worker.tasks.deploy_tasks import promote_rollout_wave

    promote_rollout_wave.delay(str(plan_id), wave_number)

    return ResponseEnvelope(
        data={"plan_id": str(plan_id), "promoted_from": wave_number},
    )


@router.post("/rollouts/{plan_id}/waves/{wave_number}/rollback")
async def rollback_wave(
    plan_id: UUID,
    wave_number: int,
    body: JobApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[dict]:
    """Roll back a specific wave."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    from src.worker.deploy.rollout import RolloutOrchestrator
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.orm import Session as _Sess

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = _ce(sync_url)
    with _Sess(engine) as sync_db:
        orch = RolloutOrchestrator(sync_db)
        result = orch.rollback_wave(plan_id, wave_number, body.comment)
    engine.dispose()

    return ResponseEnvelope(data=result)


# ===================================================================
# Golden image endpoints (T085)
# ===================================================================


@router.get("/golden-images")
async def list_golden_images(
    org_id: UUID = Depends(get_scoped_org_id),
    image_type: str | None = Query(None),
    device_model: str | None = Query(None),
    lifecycle_state: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[GoldenImageResponse]]:
    """List golden images for an org."""
    stmt = select(GoldenImage).where(GoldenImage.org_id == org_id).order_by(GoldenImage.created_at.desc())
    if image_type:
        stmt = stmt.where(GoldenImage.image_type == image_type)
    if device_model:
        stmt = stmt.where(GoldenImage.device_model == device_model)
    if lifecycle_state:
        stmt = stmt.where(GoldenImage.lifecycle_state == lifecycle_state)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    items = [GoldenImageResponse.model_validate(r) for r in rows]
    return ResponseEnvelope(data=items)


@router.post("/golden-images", status_code=201)
async def create_golden_image(
    body: GoldenImageCreate,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[GoldenImageResponse]:
    """Register a new golden image."""
    image = GoldenImage(
        org_id=body.org_id,
        image_type=body.image_type,
        device_model=body.device_model,
        version=body.version,
        content_hash=body.content_hash,
        artifact_url=body.artifact_url,
        lifecycle_state="draft",
        created_by=user.email,
    )
    db.add(image)
    await db.flush()
    return ResponseEnvelope(data=GoldenImageResponse.model_validate(image))


@router.post("/golden-images/{image_id}/approve")
async def approve_golden_image(
    image_id: UUID,
    body: JobApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[GoldenImageResponse]:
    """Approve a golden image (draft -> approved, FR-033)."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    image = await _load_golden_image(db, image_id)
    if image.lifecycle_state != "draft":
        raise HTTPException(status_code=409, detail="Image must be draft")
    if image.created_by == user.email:
        raise HTTPException(
            status_code=403,
            detail="Approver must differ from creator",
        )

    image.lifecycle_state = "approved"
    image.approved_by = user.email
    image.approved_at = datetime.now(UTC)
    await db.flush()
    return ResponseEnvelope(data=GoldenImageResponse.model_validate(image))


@router.post("/golden-images/{image_id}/retire")
async def retire_golden_image(
    image_id: UUID,
    body: JobApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[GoldenImageResponse]:
    """Retire a golden image (approved -> retired)."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    image = await _load_golden_image(db, image_id)
    if image.lifecycle_state != "approved":
        raise HTTPException(status_code=409, detail="Image must be approved")

    image.lifecycle_state = "retired"
    await db.flush()
    return ResponseEnvelope(data=GoldenImageResponse.model_validate(image))


# -- Rollout/golden image helpers ---


async def _load_plan(db: AsyncSession, plan_id: UUID) -> RolloutPlan:
    """Load a rollout plan or raise 404."""
    stmt = select(RolloutPlan).where(RolloutPlan.plan_id == plan_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return row


async def _load_golden_image(
    db: AsyncSession,
    image_id: UUID,
) -> GoldenImage:
    """Load a golden image or raise 404."""
    stmt = select(GoldenImage).where(GoldenImage.image_id == image_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return row


def _plan_to_summary(
    plan: RolloutPlan,
    waves: list | None = None,
) -> RolloutSummary:
    """Convert plan to summary, counting waves and targets."""
    plan_waves = waves or getattr(plan, "waves", []) or []
    total = sum(
        len(w.target_entities) if hasattr(w, "target_entities") and isinstance(w.target_entities, list) else 0
        for w in plan_waves
    )
    return RolloutSummary(
        plan_id=plan.plan_id,
        name=plan.name,
        status=plan.status,
        promotion_mode=plan.promotion_mode,
        wave_count=len(plan_waves),
        total_targets=total,
        created_at=plan.created_at,
    )


# ===================================================================
# Change template endpoints (T097)
# ===================================================================


@router.get("/templates")
async def list_templates(
    org_id: UUID = Depends(get_scoped_org_id),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[TemplateResponse]]:
    """List change templates (FR-031)."""
    stmt = select(ChangeTemplate).where(ChangeTemplate.org_id == org_id).order_by(ChangeTemplate.name)
    if category:
        stmt = stmt.where(ChangeTemplate.category == category)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    items = [TemplateResponse.model_validate(r) for r in rows]
    return ResponseEnvelope(data=items)


@router.post("/templates", status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[TemplateResponse]:
    """Create a reusable change template."""
    tmpl = ChangeTemplate(
        org_id=body.org_id,
        name=body.name,
        category=body.category,
        target_entity_type=body.target_entity_type,
        parameter_schema=body.parameter_schema,
        config_template=body.config_template,
        approval_required=body.approval_required,
        author=user.email,
    )
    db.add(tmpl)
    await db.flush()
    return ResponseEnvelope(data=TemplateResponse.model_validate(tmpl))


@router.post("/templates/{template_id}/instantiate")
async def instantiate_template(
    template_id: UUID,
    body: TemplateInstantiateRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[JobSummary]:
    """Instantiate a template to create a deployment job."""
    tmpl = await _load_template(db, template_id)

    from src.shared.services.template import TemplateService
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.orm import Session as _Sess

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = _ce(sync_url)
    with _Sess(engine) as sync_db:
        svc = TemplateService(sync_db)
        payload = svc.instantiate(tmpl, body.parameters)
    engine.dispose()

    job = ScheduledJob(
        org_id=body.org_id,
        change_payload={
            "entity_type": tmpl.target_entity_type,
            "entity_id": str(body.target_entity_id),
            "config": payload,
        },
        target_entities=[
            {
                "entity_type": tmpl.target_entity_type,
                "entity_id": str(body.target_entity_id),
            }
        ],
        status=JobStatus.PENDING.value,
        scheduled_at=body.scheduled_at,
        created_by=user.email,
        approval_required=tmpl.approval_required,
    )
    db.add(job)
    await db.flush()
    return ResponseEnvelope(data=_to_summary(job))


async def _load_template(
    db: AsyncSession,
    template_id: UUID,
) -> ChangeTemplate:
    """Load a change template or raise 404."""
    stmt = select(ChangeTemplate).where(
        ChangeTemplate.template_id == template_id,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return row
