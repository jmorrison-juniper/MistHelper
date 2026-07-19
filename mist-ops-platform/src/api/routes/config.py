"""Config routes — time-travel and revision endpoints (T046).

Implements the contracts/config.md API contract:
    - GET /config/revisions          — list revisions
    - GET /config/revisions/{id}     — get revision detail
    - GET /config/time-travel        — point-in-time lookup (R-04)
    - POST /config/diff              — field-level diff (US2, placeholder)
    - POST /config/install-from-revision — rollback push (US2, placeholder)
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_authenticated_user, get_db_session
from src.api.middleware.auth import CurrentUser
from src.api.schemas.common import PaginationMeta, ResponseEnvelope
from src.api.schemas.config import (
    AcceptDriftRequest,
    BaselineCreate,
    BaselineResponse,
    DiffRequest,
    DiffResponse,
    DiffChange as DiffChangeSchema,
    DiffSummary as DiffSummarySchema,
    InstallFromRevisionRequest,
    InstallJobResponse,
    RemediateRequest,
    RevisionDetailResponse,
    RevisionResponse,
    TimeTravelResponse,
    TimeTravelStatusSnapshot,
)
from src.shared.models.config import (
    Baseline,
    ConfigRevision,
    DeviceStatusSnapshot,
    DriftAlert,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


# -- GET /config/revisions -----------------------------------------------


@router.get("/revisions", summary="List config revisions")
async def list_revisions(
    org_id: UUID = Query(...),
    entity_id: UUID = Query(...),
    entity_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[RevisionResponse]]:
    """Return config revisions for an entity within an org."""
    stmt = (
        select(ConfigRevision)
        .where(
            ConfigRevision.org_id == str(org_id),
            ConfigRevision.entity_id == entity_id,
        )
        .order_by(ConfigRevision.captured_at.desc())
    )
    if entity_type:
        stmt = stmt.where(ConfigRevision.entity_type == entity_type)

    total_result = await db.execute(
        select(ConfigRevision.id).where(
            ConfigRevision.org_id == str(org_id),
            ConfigRevision.entity_id == entity_id,
        )
    )
    total = len(total_result.all())

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    data = [RevisionResponse.model_validate(row) for row in rows]
    meta = PaginationMeta(page=page, per_page=per_page, total=total)
    return ResponseEnvelope(data=data, meta=meta)


# -- GET /config/revisions/{revision_id} ----------------------------------


@router.get("/revisions/{revision_id}", summary="Get revision detail")
async def get_revision(
    revision_id: int,
    org_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[RevisionDetailResponse]:
    """Return a full config revision including its JSON payload."""
    stmt = select(ConfigRevision).where(
        ConfigRevision.org_id == str(org_id),
        ConfigRevision.revision_number == revision_id,
    )
    result = await db.execute(stmt)
    revision = result.scalar_one_or_none()

    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revision {revision_id} not found",
        )

    data = RevisionDetailResponse.model_validate(revision)
    return ResponseEnvelope(data=data)


# -- GET /config/time-travel (R-04) ---------------------------------------


@router.get("/time-travel", summary="Point-in-time config lookup")
async def time_travel(
    org_id: UUID = Query(...),
    entity_id: UUID = Query(...),
    entity_type: str = Query(...),
    timestamp: datetime = Query(...),
    include_status: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[TimeTravelResponse]:
    """Retrieve the config state at a specific point in time.

    Uses a descending-index lookup on captured_at (R-04 pattern):
    ``WHERE entity_id = ? AND captured_at <= ? ORDER BY captured_at DESC LIMIT 1``
    """
    config_result = await _find_revision_at(
        db,
        org_id,
        entity_id,
        entity_type,
        timestamp,
    )

    if config_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No config data for {entity_id} at {timestamp.isoformat()}",
        )

    response = TimeTravelResponse(
        entity_id=entity_id,
        entity_type=entity_type,
        queried_timestamp=timestamp,
        actual_timestamp=config_result.captured_at,
        config=config_result.config_blob or {},
    )

    if include_status:
        response.status = await _find_status_at(db, entity_id, timestamp)

    return ResponseEnvelope(data=response)


# -- POST /config/diff (T053) -----------------------------------------------


@router.post("/diff", summary="Compute config diff")
async def compute_diff(
    body: DiffRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[DiffResponse]:
    """Compute field-level diff between two revisions using deepdiff."""
    from src.shared.services.diff import DiffService

    old_rev = await _load_revision_by_number(db, body.org_id, body.old_revision_id)
    new_rev = await _load_revision_by_number(db, body.org_id, body.new_revision_id)

    if old_rev is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Old revision {body.old_revision_id} not found",
        )
    if new_rev is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"New revision {body.new_revision_id} not found",
        )

    service = DiffService()
    result = service.compute_diff(
        old_rev.config_blob or {},
        new_rev.config_blob or {},
    )

    changes = [
        DiffChangeSchema(
            path=change.path,
            old_value=change.old_value,
            new_value=change.new_value,
            change_type=change.change_type,
        )
        for change in result.changes
    ]
    summary = DiffSummarySchema(
        fields_changed=result.summary.fields_changed,
        fields_added=result.summary.fields_added,
        fields_removed=result.summary.fields_removed,
    )

    data = DiffResponse(
        old_revision_id=body.old_revision_id,
        new_revision_id=body.new_revision_id,
        entity_id=old_rev.entity_id,
        changes=changes,
        summary=summary,
    )
    return ResponseEnvelope(data=data)


# -- POST /config/install-from-revision (T054) ----------------------------


@router.post(
    "/install-from-revision",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Push a revision back to devices",
)
async def install_from_revision(
    body: InstallFromRevisionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[InstallJobResponse]:
    """Queue an async job to push a historical revision to target devices.

    Requires ``confirm=true`` for safety (destructive operation).
    Creates a ScheduledJob and enqueues a Celery task.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This will push revision {body.revision_id} "
                f"to {len(body.target_entity_ids)} devices. "
                "Set confirm=true to proceed."
            ),
        )

    revision = await _load_revision_by_number(db, body.org_id, body.revision_id)
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revision {body.revision_id} not found",
        )

    from uuid import uuid4

    from src.shared.config.constants import JobStatus
    from src.shared.models.operations import ScheduledJob

    job_id = uuid4()
    job = ScheduledJob(
        id=job_id,
        org_id=str(body.org_id),
        name=f"install-from-revision-{body.revision_id}",
        job_type="install_from_revision",
        status=JobStatus.PENDING.value,
        parameters={
            "revision_id": body.revision_id,
            "target_entity_ids": [str(eid) for eid in body.target_entity_ids],
            "reason": body.reason,
        },
    )
    db.add(job)
    await db.commit()

    from src.worker.tasks.deploy_tasks import install_from_revision as deploy_task

    deploy_task.delay(
        job_id=str(job_id),
        revision_id=body.revision_id,
        target_entity_ids=[str(eid) for eid in body.target_entity_ids],
        org_id=str(body.org_id),
    )

    data = InstallJobResponse(
        job_id=job_id,
        status="pending",
        target_count=len(body.target_entity_ids),
        revision_id=body.revision_id,
    )
    return ResponseEnvelope(data=data)


# -- helpers -------------------------------------------------------------


async def _load_revision_by_number(
    db: AsyncSession,
    org_id: UUID,
    revision_number: int,
) -> ConfigRevision | None:
    """Load a config revision by its sequence number within an org."""
    stmt = select(ConfigRevision).where(
        ConfigRevision.org_id == str(org_id),
        ConfigRevision.revision_number == revision_number,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_revision_at(
    db: AsyncSession,
    org_id: UUID,
    entity_id: UUID,
    entity_type: str,
    timestamp: datetime,
) -> ConfigRevision | None:
    """R-04 temporal query: latest revision at or before timestamp."""
    stmt = (
        select(ConfigRevision)
        .where(
            ConfigRevision.org_id == str(org_id),
            ConfigRevision.entity_id == entity_id,
            ConfigRevision.entity_type == entity_type,
            ConfigRevision.captured_at <= timestamp,
        )
        .order_by(ConfigRevision.captured_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_status_at(
    db: AsyncSession,
    entity_id: UUID,
    timestamp: datetime,
) -> TimeTravelStatusSnapshot | None:
    """Nearest status snapshot at or before the requested time."""
    stmt = (
        select(DeviceStatusSnapshot)
        .where(
            DeviceStatusSnapshot.device_id == entity_id,
            DeviceStatusSnapshot.captured_at <= timestamp,
        )
        .order_by(DeviceStatusSnapshot.captured_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        return None

    return TimeTravelStatusSnapshot(
        operational_state=snapshot.status,
        uptime_seconds=snapshot.uptime_seconds or 0,
        cpu_pct=snapshot.cpu_pct or 0.0,
        mem_pct=snapshot.mem_pct or 0.0,
    )


# ===================================================================
# Baseline endpoints (T093)
# ===================================================================


@router.get("/baselines")
async def list_baselines(
    org_id: UUID = Query(...),
    entity_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[BaselineResponse]]:
    """List baselines for an organization."""
    stmt = select(Baseline).where(Baseline.org_id == org_id).order_by(Baseline.updated_at.desc())
    if entity_type:
        stmt = stmt.where(Baseline.entity_type == entity_type)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    items = [BaselineResponse.model_validate(r) for r in rows]
    return ResponseEnvelope(data=items)


@router.post("/baselines", status_code=201)
async def create_baseline(
    body: BaselineCreate,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[BaselineResponse]:
    """Create or update a baseline (intended state)."""
    existing = await _find_baseline_by_scope(
        db,
        body.org_id,
        body.entity_type,
        body.entity_scope,
    )
    if existing:
        existing.config_payload = body.config_payload
        existing.updated_by = user.email
        await db.flush()
        return ResponseEnvelope(
            data=BaselineResponse.model_validate(existing),
        )

    baseline = Baseline(
        org_id=body.org_id,
        entity_type=body.entity_type,
        entity_scope=body.entity_scope,
        config_payload=body.config_payload,
        updated_by=user.email,
    )
    db.add(baseline)
    await db.flush()
    return ResponseEnvelope(data=BaselineResponse.model_validate(baseline))


@router.post("/baselines/{baseline_id}/accept-drift")
async def accept_drift(
    baseline_id: UUID,
    body: AcceptDriftRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[BaselineResponse]:
    """Accept current drift as the new baseline."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    baseline = await _load_baseline(db, baseline_id)
    alert = await _load_drift_alert(db, body.alert_id)

    actual = await _latest_revision_for_baseline(db, baseline)
    if actual and actual.config_blob:
        baseline.config_payload = actual.config_blob
        baseline.updated_by = user.email

    alert.status = "accepted"
    alert.resolved_by = user.email
    from datetime import UTC, datetime as _dt

    alert.resolved_at = _dt.now(UTC)

    await db.flush()
    return ResponseEnvelope(data=BaselineResponse.model_validate(baseline))


@router.post("/baselines/{baseline_id}/remediate")
async def remediate(
    baseline_id: UUID,
    body: RemediateRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[dict]:
    """Push baseline config back to drifted devices."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    baseline = await _load_baseline(db, baseline_id)

    for alert_id in body.alert_ids:
        alert = await _load_drift_alert(db, alert_id)
        alert.status = "remediated"
        alert.resolved_by = user.email
        from datetime import UTC, datetime as _dt

        alert.resolved_at = _dt.now(UTC)

    from src.worker.tasks.deploy_tasks import install_from_revision

    install_from_revision.delay(
        str(baseline.org_id),
        str(baseline.baseline_id),
        [str(baseline.entity_scope)],
    )
    await db.flush()
    return ResponseEnvelope(
        data={
            "baseline_id": str(baseline_id),
            "alerts_remediated": len(body.alert_ids),
            "status": "remediation_queued",
        }
    )


# -- Baseline helpers ---


async def _load_baseline(
    db: AsyncSession,
    baseline_id: UUID,
) -> Baseline:
    """Load a baseline or raise 404."""
    stmt = select(Baseline).where(Baseline.baseline_id == baseline_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return row


async def _load_drift_alert(
    db: AsyncSession,
    alert_id: UUID,
) -> DriftAlert:
    """Load a drift alert or raise 404."""
    stmt = select(DriftAlert).where(DriftAlert.alert_id == alert_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return row


async def _find_baseline_by_scope(
    db: AsyncSession,
    org_id: UUID,
    entity_type: str,
    entity_scope: UUID,
) -> Baseline | None:
    """Find baseline by unique scope constraint."""
    stmt = select(Baseline).where(
        Baseline.org_id == org_id,
        Baseline.entity_type == entity_type,
        Baseline.entity_scope == entity_scope,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _latest_revision_for_baseline(
    db: AsyncSession,
    baseline: Baseline,
) -> ConfigRevision | None:
    """Find latest revision matching baseline scope."""
    stmt = (
        select(ConfigRevision)
        .where(
            ConfigRevision.org_id == str(baseline.org_id),
            ConfigRevision.entity_type == baseline.entity_type,
            ConfigRevision.entity_id == baseline.entity_scope,
        )
        .order_by(ConfigRevision.captured_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()
